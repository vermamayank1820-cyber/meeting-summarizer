"""
FastAPI Backend — Meeting Summarizer
--------------------------------------
Endpoints:
  POST /upload                    Upload recording → background pipeline
  GET  /meetings                  List processed meetings
  GET  /meetings/{id}             Full meeting data from SQLite
  GET  /status/{id}               Job status
  POST /meetings/{id}/chat        Streaming Q&A chatbot over the transcript
  DELETE /meetings/{id}           Remove meeting record
  GET  /health                    Health check

Design:
  - Uploaded files are deleted from disk immediately after the pipeline completes
  - All data lives in SQLite only — no transcript/summary files on disk
  - WatcherAgent runs in the background watching /recordings
"""
import asyncio
import shutil
import tempfile
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.watcher_agent import WatcherAgent
from agents.storage_agent import StorageAgent
from orchestrator import Orchestrator, PipelineError
from utils.logger import get_logger

from utils.config import (
    RECORDINGS_DIR, SUPPORTED_EXTENSIONS, SUMMARY_STYLES,
    DEFAULT_SUMMARY_STYLE, OPENAI_API_KEY, OPENAI_MODEL, LLM_PROVIDER,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
)

# Uploads land here — a TEMP dir OUTSIDE /recordings so WatcherAgent never
# double-processes API uploads.  Files are deleted after the pipeline runs.
_UPLOAD_TMP_DIR = Path(tempfile.gettempdir()) / "meeting_summarizer_uploads"
_UPLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("API")

# ── In-memory job tracker ────────────────────────────────────────────────────
_job_status: dict[str, str] = {}


def _run_pipeline(file_path: Path, summary_style: str, meeting_id: str,
                  delete_after: bool = True):
    """
    Run the full agent pipeline in a background thread.
    delete_after=True  → remove the file once done (API uploads from tmp dir)
    delete_after=False → leave the file alone (WatcherAgent files in /recordings)
    """
    _job_status[meeting_id] = "processing"
    orchestrator = Orchestrator()
    try:
        result = orchestrator.process(file_path, summary_style)
        _job_status[meeting_id] = "completed"
        _job_status[result.get("meeting_id", meeting_id)] = "completed"
        logger.info(f"Job {meeting_id} completed successfully")
    except PipelineError as exc:
        logger.error(f"Pipeline error [{meeting_id}]: {exc}")
        _job_status[meeting_id] = f"failed: {exc.stage}"
    except Exception as exc:
        logger.error(f"Unexpected error [{meeting_id}]: {exc}", exc_info=True)
        _job_status[meeting_id] = "failed: unexpected error"
    finally:
        if delete_after and file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted temp upload: {file_path.name}")
            except Exception as e:
                logger.warning(f"Could not delete {file_path.name}: {e}")


# ── Lifespan ─────────────────────────────────────────────────────────────────
watcher: Optional[WatcherAgent] = None


def _on_new_recording(path: Path):
    mid = str(uuid.uuid4())[:8]
    logger.info(f"WatcherAgent → pipeline for {path.name} (job: {mid})")
    # delete_after=False: user manually dropped this file, leave it in /recordings
    threading.Thread(
        target=_run_pipeline,
        args=(path, DEFAULT_SUMMARY_STYLE, mid, False),
        daemon=True,
    ).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global watcher
    watcher = WatcherAgent(on_new_file=_on_new_recording)
    watcher.start()
    logger.info("API started — WatcherAgent running")
    yield
    if watcher:
        watcher.stop()
    logger.info("API shut down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meeting Summarizer API",
    version="2.0.0",
    description="Agentic AI meeting transcription and summarization",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "watcher": "running" if watcher else "stopped",
        "llm_provider": LLM_PROVIDER,
    }


@app.post("/upload", summary="Upload a recording and start processing")
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    summary_style: str = Form(default=DEFAULT_SUMMARY_STYLE),
):
    if summary_style not in SUMMARY_STYLES:
        raise HTTPException(400, f"summary_style must be one of {SUMMARY_STYLES}")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{suffix}'")

    meeting_id = str(uuid.uuid4())[:8]

    # ⚠️  Save to a TEMP directory — NOT to /recordings.
    # /recordings is watched by WatcherAgent; saving there would trigger a
    # second pipeline for the same file, causing a race condition.
    save_path = _UPLOAD_TMP_DIR / f"{meeting_id}_{Path(file.filename).name}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = save_path.stat().st_size
    logger.info(f"Uploaded: {file.filename} ({file_size/1024/1024:.1f} MB) → tmp job {meeting_id}")
    _job_status[meeting_id] = "queued"

    # delete_after=True → remove the temp file once pipeline finishes
    background_tasks.add_task(_run_pipeline, save_path, summary_style, meeting_id, True)

    # Estimate processing time
    mb = file_size / 1024 / 1024
    if mb < 10:
        eta = "~1-2 minutes"
    elif mb < 25:
        eta = "~2-4 minutes"
    elif mb < 100:
        eta = "~4-7 minutes"
    else:
        eta = "~7-12 minutes"

    return JSONResponse({
        "meeting_id": meeting_id,
        "filename": file.filename,
        "file_size_mb": round(mb, 1),
        "status": "queued",
        "estimated_time": eta,
        "message": f"Processing started. Estimated completion: {eta}",
    }, status_code=202)


@app.get("/status/{meeting_id}")
def get_status(meeting_id: str):
    status = _job_status.get(meeting_id)
    if status is None:
        record = StorageAgent.get_meeting(meeting_id)
        if record:
            return {"meeting_id": meeting_id, "status": record["status"]}
        raise HTTPException(404, f"Job '{meeting_id}' not found")
    return {"meeting_id": meeting_id, "status": status}


@app.get("/meetings")
def list_meetings(limit: int = 100):
    meetings = StorageAgent.list_meetings(limit=limit)
    return {"count": len(meetings), "meetings": meetings}


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    record = StorageAgent.get_meeting(meeting_id)
    if not record:
        raise HTTPException(404, f"Meeting '{meeting_id}' not found")
    return record


@app.post("/meetings/{meeting_id}/chat", summary="Ask a question about a meeting (streaming)")
async def chat_about_meeting(
    meeting_id: str,
    question: str = Form(...),
):
    """
    Streaming chatbot endpoint.
    Retrieves the transcript from SQLite and answers the question via GPT-4o / Claude.
    Returns a text/event-stream so the UI can display tokens as they arrive.
    """
    record = StorageAgent.get_meeting(meeting_id)
    if not record:
        raise HTTPException(404, f"Meeting '{meeting_id}' not found")

    transcript = record.get("clean_transcript") or record.get("raw_transcript") or ""
    summary    = record.get("summary", {})

    if not transcript:
        raise HTTPException(422, "Transcript not available for this meeting yet")

    # Trim transcript to avoid token overflow (~6000 tokens ≈ 24000 chars)
    MAX_TRANSCRIPT_CHARS = 24_000
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n[transcript truncated…]"

    summary_text = (
        f"Overview: {summary.get('meeting_overview','')}\n"
        f"Decisions: {'; '.join(str(d) for d in summary.get('decisions_taken',[]))}\n"
        f"Action Items: {'; '.join(str(a.get('task','') if isinstance(a,dict) else a) for a in summary.get('action_items',[]))}"
    )

    system_prompt = f"""You are an expert meeting analyst and assistant.
The user attended a meeting and wants to ask questions about it.
Answer based ONLY on the meeting content provided below.
Be concise, professional, and specific. If the answer is not in the transcript, say so clearly.

=== MEETING SUMMARY ===
{summary_text}

=== FULL TRANSCRIPT ===
{transcript}
"""

    async def _stream_openai():
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": question},
            ],
            stream=True,
            temperature=0.3,
            max_tokens=1024,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def _stream_anthropic():
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        async with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    generator = _stream_openai() if LLM_PROVIDER == "openai" else _stream_anthropic()
    return StreamingResponse(generator, media_type="text/plain")


@app.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: str):
    StorageAgent.delete_meeting(meeting_id)
    _job_status.pop(meeting_id, None)
    return {"message": f"Meeting {meeting_id} deleted"}
