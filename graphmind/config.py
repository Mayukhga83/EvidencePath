from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st

        return str(st.secrets.get(name, os.getenv(name, default)))
    except Exception:
        return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = _secret("OPENAI_API_KEY")
    openai_model: str = _secret("OPENAI_MODEL", "gpt-5.4-mini")
    embedding_model: str = _secret("EMBEDDING_MODEL", "text-embedding-3-small")
    backend_mode: str = _secret("BACKEND_MODE", "local").lower()
    supabase_url: str = _secret("SUPABASE_URL")
    supabase_key: str = _secret("SUPABASE_KEY")
    local_store_path: Path = Path(_secret("LOCAL_STORE_PATH", "data/local_store.json"))
    auto_memory_threshold: float = float(_secret("AUTO_MEMORY_THRESHOLD", "0.80"))
    conversation_context_turns: int = int(_secret("CONVERSATION_CONTEXT_TURNS", "6"))

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


settings = Settings()
