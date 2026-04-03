"""
Transcription Agent
-------------------
Converts audio/video files to text.

Strategy (in order):
  1. OpenAI Whisper API  (if TRANSCRIPTION_PROVIDER=openai_api and key has quota)
  2. Auto-fallback to local Whisper if API returns quota/auth errors
  3. Local Whisper        (if TRANSCRIPTION_PROVIDER=local)

Handles files > 25 MB by:
  1. Extracting audio with system ffmpeg   (fastest)
  2. Fallback: PyAV decode→encode           (pure Python)
  3. Splits into ≤24 MB chunks if audio is still too large
"""
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import (
    TRANSCRIPTION_PROVIDER, OPENAI_API_KEY,
    WHISPER_MODEL_SIZE, WHISPER_DEVICE, WHISPER_MAX_RETRIES,
)

logger = get_logger("TranscriptionAgent")

OPENAI_MAX_BYTES = 24 * 1024 * 1024   # 24 MB (API hard limit is 25 MB)
CHUNK_MINUTES    = 8                   # split long recordings into 8-min pieces


# ─── Audio extraction helpers ─────────────────────────────────────────────────

def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _extract_with_ffmpeg(file_path: Path, start_sec: float = 0,
                          end_sec: float = None) -> Path | None:
    """Extract mono 16kHz MP3 audio using system ffmpeg."""
    if not _ffmpeg_available():
        return None

    out = Path(tempfile.mktemp(suffix=".mp3"))
    cmd = [
        "ffmpeg", "-y",
        "-i", str(file_path),
        "-vn",                     # drop video stream
        "-ac", "1",                # mono
        "-ar", "16000",            # 16 kHz
        "-b:a", "32k",             # 32 kbps
    ]
    if start_sec > 0:
        cmd += ["-ss", str(start_sec)]
    if end_sec is not None:
        cmd += ["-t", str(end_sec - start_sec)]
    cmd.append(str(out))

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        if result.returncode == 0 and out.exists() and out.stat().st_size > 512:
            mb = out.stat().st_size / 1024 / 1024
            logger.info(f"ffmpeg extracted audio: {mb:.1f} MB")
            return out
        logger.warning(f"ffmpeg failed (rc={result.returncode}): "
                       f"{result.stderr.decode(errors='ignore')[-200:]}")
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg timed out")
    except Exception as e:
        logger.warning(f"ffmpeg error: {e}")

    out.unlink(missing_ok=True)
    return None


def _extract_with_pyav(file_path: Path, start_sec: float = 0,
                        end_sec: float = None) -> Path:
    """
    Decode audio frames from video and re-encode using PyAV.
    Does NOT use add_stream(template=…) — works with any PyAV version.
    """
    try:
        import av
    except ImportError:
        raise RuntimeError(
            "Neither ffmpeg nor PyAV is available.\n"
            "Install ffmpeg:  brew install ffmpeg   (macOS)\n"
            "  OR  pip install av"
        )

    # Probe available encoders
    CANDIDATES = [
        ("libmp3lame", "mp3", ".mp3"),
        ("libopus",    "ogg", ".ogg"),
        ("aac",        "adts", ".aac"),
        ("pcm_s16le",  "wav",  ".wav"),
    ]
    chosen_codec = chosen_format = chosen_ext = None

    for codec, fmt, ext in CANDIDATES:
        probe_tmp = Path(tempfile.mktemp(suffix=ext))
        try:
            with av.open(str(probe_tmp), "w", format=fmt) as c:
                c.add_stream(codec, rate=16000)
            chosen_codec, chosen_format, chosen_ext = codec, fmt, ext
            break
        except Exception:
            pass
        finally:
            probe_tmp.unlink(missing_ok=True)

    if chosen_codec is None:
        raise RuntimeError("PyAV: no suitable audio encoder found")

    out = Path(tempfile.mktemp(suffix=chosen_ext))

    with av.open(str(file_path)) as in_f:
        audio_streams = [s for s in in_f.streams if s.type == "audio"]
        if not audio_streams:
            raise ValueError("No audio stream found in the file")
        audio_in = audio_streams[0]

        if start_sec > 0:
            in_f.seek(int(start_sec * 1_000_000))

        with av.open(str(out), "w", format=chosen_format) as out_f:
            out_stream = out_f.add_stream(chosen_codec, rate=16000)
            if chosen_codec != "pcm_s16le":
                out_stream.codec_context.bit_rate = 32_000

            resampler = None
            try:
                from av.audio.resampler import AudioResampler
                resampler = AudioResampler(format="fltp", layout="mono", rate=16000)
            except Exception as e:
                logger.debug(f"AudioResampler unavailable ({e}), encoding as-is")

            for frame in in_f.decode(audio_in):
                if end_sec is not None and frame.pts is not None:
                    pts_s = float(frame.pts) * float(frame.time_base)
                    if pts_s >= end_sec:
                        break

                frames = [frame]
                if resampler:
                    try:
                        r = resampler.resample(frame)
                        frames = r if isinstance(r, list) else ([r] if r is not None else [])
                    except Exception:
                        frames = [frame]

                for f in frames:
                    f.pts = None
                    for pkt in out_stream.encode(f):
                        out_f.mux(pkt)

            for pkt in out_stream.encode(None):
                out_f.mux(pkt)

    mb = out.stat().st_size / 1024 / 1024
    logger.info(f"PyAV ({chosen_codec}) extracted audio: {mb:.1f} MB")
    return out


def _get_duration_seconds(file_path: Path) -> float:
    """Get media duration via ffprobe or PyAV."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
            capture_output=True, timeout=30
        )
        return float(r.stdout.decode().strip())
    except Exception:
        pass
    try:
        import av
        with av.open(str(file_path)) as c:
            if c.duration:
                return float(c.duration) / 1_000_000
    except Exception:
        pass
    return 0.0


def _prepare_chunks(file_path: Path) -> list[Path]:
    """
    Returns a list of audio file paths ready for transcription.
    Small files go straight through; large ones get extracted & split.
    """
    if file_path.stat().st_size <= OPENAI_MAX_BYTES:
        logger.info(f"File {file_path.stat().st_size/1024/1024:.1f} MB — sending directly")
        return [file_path]

    logger.info(f"File {file_path.stat().st_size/1024/1024:.1f} MB > 24 MB — extracting audio…")

    full_audio = (_extract_with_ffmpeg(file_path) or _extract_with_pyav(file_path))
    audio_size = full_audio.stat().st_size

    if audio_size <= OPENAI_MAX_BYTES:
        return [full_audio]

    # Still too large — split by duration
    duration  = _get_duration_seconds(file_path)
    chunk_sec = CHUNK_MINUTES * 60
    n_chunks  = max(1, int(duration / chunk_sec) + 1)
    logger.info(
        f"Audio {audio_size/1024/1024:.1f} MB / {duration:.0f}s "
        f"— splitting into {n_chunks}×{CHUNK_MINUTES}-min chunks"
    )
    full_audio.unlink(missing_ok=True)

    chunks = []
    start  = 0.0
    while start < duration:
        end   = min(start + chunk_sec, duration)
        chunk = (_extract_with_ffmpeg(file_path, start_sec=start, end_sec=end)
                 or _extract_with_pyav(file_path, start_sec=start, end_sec=end))
        chunks.append(chunk)
        start = end

    return chunks


# ─── Quota / auth error detection ─────────────────────────────────────────────

class QuotaExceededError(Exception):
    """Raised when OpenAI API returns a quota/billing error."""
    pass


def _is_quota_error(exc: Exception) -> bool:
    """Check if an exception is an OpenAI quota/billing error."""
    exc_str = str(exc).lower()
    return any(kw in exc_str for kw in [
        "insufficient_quota", "exceeded your current quota",
        "billing", "rate_limit", "429",
    ])


# ─── OpenAI API transcription ────────────────────────────────────────────────

def _transcribe_chunk_openai(audio_path: Path) -> tuple[str, float]:
    """Send one ≤24 MB audio file to OpenAI Whisper API."""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )
    text     = getattr(resp, "text", "") or ""
    duration = float(getattr(resp, "duration", 0) or 0)
    return text.strip(), duration


def _transcribe_openai_api(file_path: Path) -> dict:
    """Transcribe via OpenAI Whisper API. Raises QuotaExceededError on billing issues."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set.\n"
            "Add it to your .env file: OPENAI_API_KEY=sk-proj-..."
        )

    chunks    = _prepare_chunks(file_path)
    tmp_files = [c for c in chunks if c != file_path]
    texts, total_dur = [], 0.0

    try:
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Transcribing chunk {i}/{len(chunks)}: {chunk.name}")
            try:
                text, dur = _transcribe_chunk_openai(chunk)
            except Exception as api_err:
                if _is_quota_error(api_err):
                    raise QuotaExceededError(
                        f"OpenAI API quota exceeded. Your API key has run out of credits.\n"
                        f"Original error: {api_err}"
                    ) from api_err
                raise  # re-raise non-quota errors
            texts.append(text)
            total_dur += dur
            logger.info(f"  Chunk {i} done — {len(text)} chars, {dur:.0f}s")
    finally:
        for f in tmp_files:
            f.unlink(missing_ok=True)

    return {"text": " ".join(texts), "duration": total_dur, "segments": []}


# ─── Local Whisper ────────────────────────────────────────────────────────────

def _local_whisper_available() -> bool:
    """Check if local whisper is installed."""
    try:
        import whisper
        return True
    except ImportError:
        return False


def _transcribe_local(file_path: Path) -> dict:
    """Transcribe using local Whisper model."""
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "Local Whisper is not installed. To enable local transcription:\n"
            "  pip install openai-whisper torch\n"
            "  brew install ffmpeg   (required by local whisper on macOS)"
        )

    # Extract audio first if the file is a large video
    audio_path = file_path
    tmp_audio = None
    if file_path.stat().st_size > OPENAI_MAX_BYTES:
        logger.info("Extracting audio for local Whisper…")
        tmp_audio = (_extract_with_ffmpeg(file_path) or _extract_with_pyav(file_path))
        audio_path = tmp_audio

    try:
        model_attr = "_whisper_model"
        if not hasattr(_transcribe_local, model_attr):
            logger.info(f"Loading local Whisper model '{WHISPER_MODEL_SIZE}' on {WHISPER_DEVICE}…")
            setattr(_transcribe_local, model_attr,
                    whisper.load_model(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE))
        model  = getattr(_transcribe_local, model_attr)
        result = model.transcribe(str(audio_path), fp16=False, verbose=False)
        return result
    finally:
        if tmp_audio:
            tmp_audio.unlink(missing_ok=True)


# ─── Agent ────────────────────────────────────────────────────────────────────

class TranscriptionAgent:
    """Transcribes meeting recordings. Auto-falls back to local Whisper on API quota errors."""

    def __init__(self):
        self.max_retries = WHISPER_MAX_RETRIES
        self.provider    = TRANSCRIPTION_PROVIDER
        ffmpeg_status    = "available" if _ffmpeg_available() else "not found (will use PyAV)"
        local_whisper    = "available" if _local_whisper_available() else "not installed"
        logger.info(
            f"TranscriptionAgent ready — provider: '{self.provider}', "
            f"ffmpeg: {ffmpeg_status}, local_whisper: {local_whisper}"
        )

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        file_path = Path(context["file_path"])
        if not file_path.exists():
            raise FileNotFoundError(f"Recording not found: {file_path}")

        mb = file_path.stat().st_size / 1024 / 1024
        logger.info(f"Transcribing: {file_path.name} ({mb:.1f} MB) via '{self.provider}'")

        last_exc = None
        tried_local_fallback = False

        for attempt in range(1, self.max_retries + 1):
            if not file_path.exists():
                raise FileNotFoundError(
                    f"File was removed before transcription completed: {file_path}"
                )
            try:
                if self.provider == "openai_api":
                    result = _transcribe_openai_api(file_path)
                else:
                    result = _transcribe_local(file_path)

                text = result.get("text", "").strip()
                if not text:
                    raise ValueError("Whisper returned empty transcript — check the audio file")

                context["raw_transcript"]   = text
                context["duration_seconds"] = float(result.get("duration") or 0)
                context["segments"]         = result.get("segments", [])
                logger.info(
                    f"Transcription done — {len(text)} chars, "
                    f"{context['duration_seconds']:.0f}s (attempt {attempt})"
                )
                return context

            except QuotaExceededError as qe:
                logger.warning(f"OpenAI API quota exceeded: {qe}")

                # Auto-fallback to local Whisper
                if not tried_local_fallback and _local_whisper_available():
                    tried_local_fallback = True
                    logger.info("Auto-falling back to local Whisper transcription…")
                    try:
                        result = _transcribe_local(file_path)
                        text = result.get("text", "").strip()
                        if text:
                            context["raw_transcript"]   = text
                            context["duration_seconds"] = float(result.get("duration") or 0)
                            context["segments"]         = result.get("segments", [])
                            logger.info(
                                f"Local Whisper fallback succeeded — {len(text)} chars"
                            )
                            return context
                    except Exception as local_err:
                        logger.warning(f"Local Whisper fallback also failed: {local_err}")

                # No fallback available — raise clear error
                raise RuntimeError(
                    "OPENAI API QUOTA EXCEEDED — Your API key has run out of credits.\n\n"
                    "To fix this, do ONE of the following:\n"
                    "  1. Add credits at https://platform.openai.com/settings/organization/billing\n"
                    "  2. Use a different API key (update OPENAI_API_KEY in .env)\n"
                    "  3. Switch to local transcription:\n"
                    "     pip install openai-whisper torch\n"
                    "     Then set TRANSCRIPTION_PROVIDER=local in .env"
                ) from qe

            except Exception as exc:
                last_exc = exc
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {exc}")
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.info(f"Retrying in {wait}s…")
                    time.sleep(wait)

        # All attempts exhausted
        ffmpeg_tip = (
            "" if _ffmpeg_available()
            else "\n\nTip: install ffmpeg for reliable large-file support:\n  brew install ffmpeg"
        )
        raise RuntimeError(
            f"Transcription failed after {self.max_retries} attempts.\n"
            f"Last error: {last_exc}{ffmpeg_tip}"
        ) from last_exc
