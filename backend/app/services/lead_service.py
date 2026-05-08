"""
Lead capture service — stores prospect info in SQLite.
Simple enough for demos; swap for Postgres later.
"""
import asyncio
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jamiiz.leads")

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "leads.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            email       TEXT NOT NULL,
            business    TEXT,
            pain_point  TEXT,
            hours_saved TEXT,
            assistant   TEXT,
            session_id  TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT,
            assistant     TEXT,
            question      TEXT,
            answer        TEXT,
            created_at    TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Lead database initialised at %s", DB_PATH)


def save_lead(
    email: str,
    name: str | None = None,
    business: str | None = None,
    pain_point: str | None = None,
    hours_saved: str | None = None,
    assistant: str | None = None,
    session_id: str | None = None,
) -> int:
    """Insert a lead and return its ID."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO leads (name, email, business, pain_point, hours_saved, assistant, session_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, business, pain_point, hours_saved, assistant, session_id,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    logger.info("Lead saved: id=%d email=%s assistant=%s", lead_id, email, assistant)
    return lead_id


def log_question(
    question: str,
    answer: str,
    assistant: str,
    session_id: str | None = None,
) -> None:
    """Log every Q&A pair — product intelligence for free."""
    conn = _get_connection()
    conn.execute(
        """
        INSERT INTO questions_log (session_id, assistant, question, answer, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, assistant, question, answer, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_leads(limit: int = 100) -> list[dict]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
