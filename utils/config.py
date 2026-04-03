"""
Configuration management for Meeting Summarizer.
Loads settings from environment variables or .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
RECORDINGS_DIR = BASE_DIR / "recordings"
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for _dir in [RECORDINGS_DIR, OUTPUTS_DIR, LOGS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# LLM Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Auto-detect LLM provider if not explicitly set
_llm_provider_env = os.getenv("LLM_PROVIDER", "")
if _llm_provider_env:
    LLM_PROVIDER = _llm_provider_env
elif OPENAI_API_KEY and not ANTHROPIC_API_KEY.startswith("sk-ant-api"):
    LLM_PROVIDER = "openai"
else:
    LLM_PROVIDER = "anthropic"

# Transcription Configuration
# "local"      = OpenAI Whisper running locally (requires ffmpeg installed)
# "openai_api" = OpenAI Whisper via API (uses OPENAI_API_KEY, no local setup)
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "openai_api")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium, large
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")           # "cpu" or "cuda"
WHISPER_MAX_RETRIES = int(os.getenv("WHISPER_MAX_RETRIES", "3"))

# Database
DB_PATH = OUTPUTS_DIR / "meetings.sqlite"

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Supported audio/video extensions
SUPPORTED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a", ".webm", ".ogg", ".mkv", ".avi", ".mov"}

# Summary styles
SUMMARY_STYLES = ["executive", "detailed"]
DEFAULT_SUMMARY_STYLE = "executive"
