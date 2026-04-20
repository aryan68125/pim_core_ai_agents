from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Database file lives next to the running process (ai_agent_microservice/).
# A relative path keeps tests and the real server both working without config.
_DB_PATH = Path("pim_core/db/agent_models.db")


def _connect() -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure the schema exists."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_models (
            agent_name TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def load_all() -> dict[str, str]:
    """Load all agent → model rows from the database.

    Returns an empty dict when the database does not yet exist.
    """
    with _connect() as conn:
        rows = conn.execute("SELECT agent_name, model_name FROM agent_models").fetchall()
    return {row["agent_name"]: row["model_name"] for row in rows}


def upsert(agent_name: str, model_name: str) -> None:
    """Insert or update the model assignment for an agent."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_models (agent_name, model_name, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(agent_name) DO UPDATE SET
                model_name = excluded.model_name,
                updated_at = excluded.updated_at
            """,
            (agent_name, model_name, now),
        )
        conn.commit()


def delete(agent_name: str) -> None:
    """Remove the model assignment row for an agent."""
    with _connect() as conn:
        conn.execute("DELETE FROM agent_models WHERE agent_name = ?", (agent_name,))
        conn.commit()
