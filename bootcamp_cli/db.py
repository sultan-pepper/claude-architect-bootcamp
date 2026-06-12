"""SQLite database for progress, check runs, hints, and mentor messages."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import os


def get_db_path() -> Path:
    """Get database path from env or use default."""
    db_path = os.environ.get("BOOTCAMP_DB", "./data/bootcamp.db")
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize database with schema if needed."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            module_id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'locked',
            assisted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS check_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            passed INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            report_json TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hint_unlocks (
            module_id TEXT NOT NULL,
            level INTEGER NOT NULL,
            ts TEXT NOT NULL,
            PRIMARY KEY (module_id, level)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mentor_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def get_module_state(conn: sqlite3.Connection, module_id: str) -> str:
    """Get current state of a module (locked/available/in_progress/passed)."""
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM progress WHERE module_id = ?", (module_id,))
    row = cursor.fetchone()
    return row["state"] if row else "locked"


def set_module_state(
    conn: sqlite3.Connection, module_id: str, state: str, assisted: bool = False
) -> None:
    """Set module state and optionally assisted flag."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"

    cursor.execute(
        "SELECT state FROM progress WHERE module_id = ?",
        (module_id,)
    )
    exists = cursor.fetchone() is not None

    if exists:
        cursor.execute(
            """UPDATE progress SET state = ?, assisted = ?, updated_at = ?
               WHERE module_id = ?""",
            (state, int(assisted), now, module_id)
        )
    else:
        cursor.execute(
            """INSERT INTO progress (module_id, state, assisted, updated_at)
               VALUES (?, ?, ?, ?)""",
            (module_id, state, int(assisted), now)
        )
    conn.commit()


def get_module_assisted(conn: sqlite3.Connection, module_id: str) -> bool:
    """Check if module has assisted flag set."""
    cursor = conn.cursor()
    cursor.execute("SELECT assisted FROM progress WHERE module_id = ?", (module_id,))
    row = cursor.fetchone()
    return bool(row["assisted"]) if row else False


def record_check_run(
    conn: sqlite3.Connection,
    module_id: str,
    passed: int,
    failed: int,
    report_json: str
) -> None:
    """Record a check run result."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"

    cursor.execute(
        """INSERT INTO check_runs (module_id, ts, passed, failed, report_json)
           VALUES (?, ?, ?, ?, ?)""",
        (module_id, now, passed, failed, report_json)
    )
    conn.commit()


def get_last_check_run(
    conn: sqlite3.Connection, module_id: str
) -> Optional[dict]:
    """Get the most recent check run for a module."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, module_id, ts, passed, failed, report_json
           FROM check_runs WHERE module_id = ? ORDER BY ts DESC LIMIT 1""",
        (module_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def count_failed_check_runs(
    conn: sqlite3.Connection, module_id: str, after_ts: Optional[str] = None
) -> int:
    """Count failed check runs, optionally after a timestamp."""
    cursor = conn.cursor()
    if after_ts:
        cursor.execute(
            """SELECT COUNT(*) as cnt FROM check_runs
               WHERE module_id = ? AND failed > 0 AND ts > ?""",
            (module_id, after_ts)
        )
    else:
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM check_runs WHERE module_id = ? AND failed > 0",
            (module_id,)
        )
    return cursor.fetchone()["cnt"]


def get_hint_unlock_ts(
    conn: sqlite3.Connection, module_id: str, level: int
) -> Optional[str]:
    """Get timestamp when a hint level was unlocked."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ts FROM hint_unlocks WHERE module_id = ? AND level = ?",
        (module_id, level)
    )
    row = cursor.fetchone()
    return row["ts"] if row else None


def set_hint_unlock(
    conn: sqlite3.Connection, module_id: str, level: int
) -> None:
    """Record when a hint level was unlocked."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"

    cursor.execute(
        """INSERT OR REPLACE INTO hint_unlocks (module_id, level, ts)
           VALUES (?, ?, ?)""",
        (module_id, level, now)
    )
    conn.commit()


def add_mentor_message(
    conn: sqlite3.Connection, module_id: str, role: str, content: str
) -> None:
    """Store a mentor message."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"

    cursor.execute(
        """INSERT INTO mentor_messages (module_id, role, content, ts)
           VALUES (?, ?, ?, ?)""",
        (module_id, role, content, now)
    )
    conn.commit()


def get_mentor_messages(
    conn: sqlite3.Connection, module_id: str
) -> list[dict]:
    """Get all mentor messages for a module, oldest first."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT role, content FROM mentor_messages
           WHERE module_id = ? ORDER BY ts ASC""",
        (module_id,)
    )
    return [dict(row) for row in cursor.fetchall()]
