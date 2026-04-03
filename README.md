# 🎙️ Meeting Summarizer — AI Meeting Workspace

> Automatically transcribes meeting recordings and generates consulting-grade summaries with a modern React workspace for uploads, results, and action tracking.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEETING SUMMARIZER SYSTEM                     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────────────────────────┐   │
│  │  /recordings │───▶│         ORCHESTRATOR                 │   │
│  │   (folder)   │    │   (pipeline coordinator)             │   │
│  └──────────────┘    └──────────────┬───────────────────────┘   │
│         ▲                           │                            │
│  ┌──────┴──────┐    ┌──────────────▼───────────────────────┐   │
│  │   WATCHER   │    │  [1] Transcription Agent (Whisper)   │   │
│  │    AGENT    │    │  [2] Cleaning Agent   (Claude API)   │   │
│  └─────────────┘    │  [3] Summarization Agent (Claude)    │   │
│                      │  [4] Storage Agent   (JSON+SQLite)   │   │
│  ┌─────────────┐    └──────────────┬───────────────────────┘   │
│  │ Manual Upload│───▶              │                            │
│  │  (FastAPI)   │    ┌─────────────▼──────────────┐            │
│  └─────────────┘    │        /outputs              │            │
│                      │  + SQLite database           │            │
│                      └─────────────┬───────────────┘            │
│                      ┌─────────────▼──────────────┐            │
│                      │   React UI      :5173        │            │
│                      │   FastAPI Docs  :8000/docs   │            │
│                      └─────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Meeting Summarizer/
├── agents/
│   ├── watcher_agent.py        # Monitors /recordings for new files
│   ├── transcription_agent.py  # Whisper audio → text
│   ├── cleaning_agent.py       # Remove fillers, fix grammar
│   ├── summarization_agent.py  # LLM structured summary
│   └── storage_agent.py        # Save transcripts + summaries in SQLite
├── api/
│   └── main.py                 # FastAPI server
├── frontend/                   # React + Tailwind SaaS UI
│   ├── src/
│   └── package.json
├── ui/
│   └── app.py                  # Legacy Streamlit UI
├── utils/
│   ├── config.py               # Config from .env
│   └── logger.py               # Centralized logging
├── tests/
│   └── test_example.py         # Example test (no audio needed)
├── recordings/                 # Drop recordings here (auto-watched)
├── outputs/                    # SQLite database and generated app data
├── logs/                       # Daily log files
├── orchestrator.py             # Pipeline coordinator
├── requirements.txt
├── .env.example
└── start.sh
```

---

## Product Experience

The frontend is now structured like a focused SaaS workspace instead of a utility dashboard.

- **Dashboard / Home**: AI-first landing experience with a large prompt surface, recent meetings, and action-item visibility
- **Upload / Ingestion**: Dedicated recording upload flow with clear summary-style selection and one primary CTA
- **Processing State**: Stable skeleton-based loading layout instead of spinner-only feedback
- **Results**: Summary, key discussion points, decisions, transcript preview, and action items in a single workspace
- **Action Items**: Collapsible meeting-based task groups with assignees, due dates, and status pills

---

## Setup

### 1. Install dependencies

```bash
cd "Meeting Summarizer"
python3 -m pip install -r requirements.txt
cd frontend && npm install
```

> **Note on PyTorch / Whisper:** If you're on macOS Apple Silicon, install:
> `pip install torch torchvision torchaudio` (no extra index URL needed)

### 2. Configure API key

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
WHISPER_MODEL_SIZE=base      # "tiny" is fastest; "medium" is best quality
```

Get your Claude API key at: https://console.anthropic.com

### 3. Start the system

```bash
bash start.sh
```

Or start services individually:

```bash
# Terminal 1 — Backend + WatcherAgent
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — React UI
cd frontend && npm run dev
```

---

## Usage

### Automatic (Folder Watch)
1. Record your meeting in Teams / Google Meet / Zoom
2. Save/export the recording to `./recordings/`
3. The WatcherAgent detects it and runs the full pipeline automatically
4. Open [http://localhost:5173](http://localhost:5173) to review the summary workspace

### Manual Upload
1. Open [http://localhost:5173](http://localhost:5173)
2. Go to **Ingestion**
3. Drag & drop your recording
4. Choose summary style: **Executive** (concise) or **Detailed**
5. Click **Process Recording**
6. Wait on the skeleton processing screen, then review the generated result and action items

### CLI (single file)
```bash
python3 orchestrator.py recordings/my_meeting.mp4 executive
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload recording |
| GET | `/meetings` | List all meetings |
| GET | `/meetings/{id}` | Full meeting data |
| GET | `/status/{id}` | Processing status |

Interactive docs: http://localhost:8000/docs

---

## Testing (without audio)

```bash
python3 tests/test_example.py
```

This runs the full stack (cleaning → summarization → storage) using a synthetic transcript. Whisper is skipped, so no audio file needed. Requires a valid API key for the LLM test.

---

## Data Model

Meetings are stored in SQLite at `outputs/meetings.sqlite`.
The backend persists transcripts and structured summaries in the database, and the React frontend reads them through the API.

Example summary payload:
```json
{
  "meeting_id": "a1b2c3d4",
  "filename": "meeting.mp4",
  "processed_at": "2026-04-03T14:30:00",
  "raw_transcript": "...",
  "clean_transcript": "...",
  "summary": {
    "meeting_overview": "...",
    "key_discussion_points": [...],
    "decisions_taken": [...],
    "action_items": [
      {"task": "...", "owner": "...", "deadline": "..."}
    ],
    "risks_and_blockers": [...],
    "next_steps": [...],
    "sentiment": "positive"
  }
}
```

The main frontend screens use these fields:

- `overview` / `summary.meeting_overview` for the executive result card
- `summary.key_discussion_points` and `summary.decisions_taken` for the results screen
- `action_items` and `summary.action_items` for the action dashboard
- `clean_transcript` / `raw_transcript` for transcript preview
- `status` for processing and completion states

---

## Frontend Stack

- React 18 + Vite
- Tailwind CSS
- Component-based UI in `frontend/src/components`
- FastAPI backend integration via `frontend/src/lib/api.js`

Key frontend entrypoints:

- `frontend/src/App.jsx`
- `frontend/src/components/UploadDropzone.jsx`
- `frontend/src/components/ResultsView.jsx`
- `frontend/src/components/ActionItemsBoard.jsx`

---

## Whisper Model Guide

| Model | Size | Speed | Quality | Best for |
|-------|------|-------|---------|----------|
| `tiny` | 75MB | ★★★★★ | ★★☆ | Quick tests |
| `base` | 145MB | ★★★★☆ | ★★★ | Default (balanced) |
| `small` | 460MB | ★★★☆☆ | ★★★★ | Better accuracy |
| `medium` | 1.5GB | ★★☆☆☆ | ★★★★★ | Production quality |

Set via `WHISPER_MODEL_SIZE` in `.env`.

---

## Troubleshooting

**Whisper model download slow?**
First run downloads the model. Subsequent runs use the cached version.

**LLM API error?**
Check your API key in `.env`. Verify your quota at console.anthropic.com.

**Transcription fails after upload?**
Check the backend logs in `logs/`. Common causes are OpenAI transcription quota exhaustion, missing `ffmpeg`, or local Whisper model download/SSL failures.

**File not detected by WatcherAgent?**
Ensure the file extension is in the supported list (.mp4, .mp3, .wav, .m4a, .webm, .ogg, .mkv, .mov).

**UI can't connect to API?**
Make sure the FastAPI server is running on port 8000 (`python -m uvicorn api.main:app`).

**Frontend not starting?**
Install the UI dependencies first:
`cd frontend && npm install`

**React dev server starts but the page is blank?**
Confirm the frontend is running on port 5173 and that the backend is reachable at `http://localhost:8000`. Override the API URL with `VITE_API_BASE_URL` if needed.
