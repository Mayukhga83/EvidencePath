"""Server-side configuration and a best-effort local API quota.

A local sqlite quota is suitable for a single Streamlit process; not robust
against multi-replica deployments, server resets or adversarial abuse. Public
high-scale services should place a durable authenticated quota at a gateway.
No uploaded document, API key, IP address or client content is persisted here.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import tempfile

DAILY_SERVER_CALL_LIMIT = int(os.getenv("EP_DAILY_SERVER_CALL_LIMIT", "75"))
PER_SESSION_CALL_LIMIT = int(os.getenv("EP_PER_SESSION_CALL_LIMIT", "8"))
MAX_AGENT_STEPS = 10
MODEL_DEFAULT = os.getenv("EP_OPENAI_MODEL", "gpt-4.1-mini")


def server_key(secret_mapping=None) -> str:
    """Only read server-owned environment or Streamlit secrets, never visitor input."""
    val = (os.getenv("OPENAI_API_KEY") or "").strip()
    if val: return val
    if secret_mapping is None: return ""
    try:
        return str(secret_mapping.get("OPENAI_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError, OSError):
        return ""


def reserve_live_call(session_calls: int, db_path: str | Path | None=None, daily_cap: int | None=None) -> int:
    """Reserve one call BEFORE invoking the model, conservatively charging failures.

    Returns updated visitor session call count. sqlite transaction protects
    against simultaneous requests in the same shared filesystem.
    """
    if session_calls >= PER_SESSION_CALL_LIMIT:
        raise RuntimeError("This visitor session reached its live-analysis limit; switch to offline mode.")
    cap = DAILY_SERVER_CALL_LIMIT if daily_cap is None else daily_cap
    path=Path(db_path) if db_path is not None else Path(tempfile.gettempdir())/'evidencepath-v3-quota.sqlite3'
    day=datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(path,timeout=4,isolation_level=None) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS quota (day TEXT PRIMARY KEY, count INTEGER NOT NULL)")
        db.execute("INSERT OR IGNORE INTO quota VALUES (?,0)",(day,))
        n=db.execute("SELECT count FROM quota WHERE day=?",(day,)).fetchone()[0]
        if n >= cap:
            db.execute("ROLLBACK")
            raise RuntimeError("Server's daily demo budget is exhausted; use the offline examples.")
        db.execute("UPDATE quota SET count=count+1 WHERE day=?",(day,))
        db.execute("COMMIT")
    return session_calls + 1
