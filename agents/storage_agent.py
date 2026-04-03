"""
Storage Agent
-------------
Persists meeting data entirely in SQLite — no files written to disk.
All transcript text and summary JSON are stored as TEXT columns.

Pipeline context keys consumed: all context keys
Pipeline context keys produced: "meeting_id" (confirmed)
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import DB_PATH

logger = get_logger("StorageAgent")


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS meetings (
    id               TEXT PRIMARY KEY,
    filename         TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    duration_secs    REAL DEFAULT 0,
    summary_style    TEXT DEFAULT 'executive',
    status           TEXT DEFAULT 'completed',
    overview         TEXT DEFAULT '',
    sentiment        TEXT DEFAULT 'neutral',
    action_items     TEXT DEFAULT '[]',
    raw_transcript   TEXT DEFAULT '',
    clean_transcript TEXT DEFAULT '',
    summary_json     TEXT DEFAULT '{}'
)
"""

_MIGRATE_COLS = [
    ("raw_transcript",   "TEXT DEFAULT ''"),
    ("clean_transcript", "TEXT DEFAULT ''"),
    ("summary_json",     "TEXT DEFAULT '{}'"),
]


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db(conn: sqlite3.Connection):
    conn.execute(_CREATE_TABLE)
    # Safe migrations: add new columns to existing DBs
    existing = {row[1] for row in conn.execute("PRAGMA table_info(meetings)")}
    for col, col_def in _MIGRATE_COLS:
        if col not in existing:
            conn.execute(f"ALTER TABLE meetings ADD COLUMN {col} {col_def}")
    conn.commit()


class StorageAgent:
    """Saves pipeline results to SQLite only. Nothing written to the filesystem."""

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        meeting_id  = context.get("meeting_id") or str(uuid.uuid4())[:8]
        context["meeting_id"] = meeting_id
        file_path   = Path(context.get("file_path", "unknown"))
        summary     = context.get("summary", {})
        ai_items    = json.dumps(summary.get("action_items", []))
        overview    = (summary.get("meeting_overview") or "")[:800]
        sentiment   = summary.get("sentiment", "neutral")
        summary_json = json.dumps(summary, ensure_ascii=False)

        row = (
            meeting_id,
            file_path.name,
            datetime.now().isoformat(),
            context.get("duration_seconds", 0),
            context.get("summary_style", "executive"),
            "completed",
            overview,
            sentiment,
            ai_items,
            context.get("raw_transcript", ""),
            context.get("clean_transcript", ""),
            summary_json,
        )

        with _get_conn() as conn:
            _init_db(conn)
            conn.execute("""
                INSERT OR REPLACE INTO meetings
                    (id, filename, created_at, duration_secs, summary_style,
                     status, overview, sentiment, action_items,
                     raw_transcript, clean_transcript, summary_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, row)
            conn.commit()

        logger.info(f"Stored meeting {meeting_id} ({file_path.name}) in SQLite")
        return context

    # ── Query helpers ────────────────────────────────────────────────────────

    @staticmethod
    def list_meetings(limit: int = 100) -> list[dict]:
        if not DB_PATH.exists():
            return []
        with _get_conn() as conn:
            _init_db(conn)
            rows = conn.execute(
                "SELECT id, filename, created_at, duration_secs, summary_style, "
                "status, overview, sentiment, action_items "
                "FROM meetings ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_meeting(meeting_id: str) -> dict | None:
        if not DB_PATH.exists():
            return None
        with _get_conn() as conn:
            _init_db(conn)
            row = conn.execute(
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        # Parse summary JSON
        try:
            record["summary"] = json.loads(record.get("summary_json") or "{}")
        except Exception:
            record["summary"] = {}
        return record

    @staticmethod
    def delete_meeting(meeting_id: str):
        if not DB_PATH.exists():
            return
        with _get_conn() as conn:
            conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
