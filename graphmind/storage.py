from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from graphmind.config import settings
from graphmind.models import AgentTrace, MemoryItem, Message, now_iso
from graphmind.scenarios import SCENARIOS


class Store(Protocol):
    def clone_scenario(self, scenario_name: str, workspace_id: str, reset: bool = False) -> str: ...
    def get_workspace(self, workspace_id: str) -> dict | None: ...
    def list_memories(self, workspace_id: str) -> list[dict]: ...
    def upsert_memory(self, memory: MemoryItem) -> None: ...
    def update_memory_status(self, memory_id: str, status: str) -> None: ...
    def add_message(self, message: Message) -> None: ...
    def list_messages(self, workspace_id: str) -> list[dict]: ...
    def add_trace(self, trace: AgentTrace) -> None: ...
    def list_traces(self, workspace_id: str) -> list[dict]: ...


class LocalStore:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.local_store_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"workspaces": [], "messages": [], "memories": [], "traces": []})

    def _empty(self) -> dict:
        return {"workspaces": [], "messages": [], "memories": [], "traces": []}

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for key in self._empty():
                data.setdefault(key, [])
            return data
        except Exception:
            return self._empty()

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _clear_workspace(self, data: dict, workspace_id: str) -> None:
        data["workspaces"] = [w for w in data["workspaces"] if w["id"] != workspace_id]
        data["messages"] = [m for m in data["messages"] if m["workspace_id"] != workspace_id]
        data["memories"] = [m for m in data["memories"] if m["workspace_id"] != workspace_id]
        data["traces"] = [t for t in data["traces"] if t["workspace_id"] != workspace_id]

    def clone_scenario(self, scenario_name: str, workspace_id: str, reset: bool = False) -> str:
        scenario = SCENARIOS[scenario_name]
        data = self._read()
        if reset:
            self._clear_workspace(data, workspace_id)

        workspace = dict(scenario["workspace"])
        workspace.update(
            {
                "id": workspace_id,
                "name": f"{scenario_name} · Session",
                "source_scenario": scenario_name,
                "parent_workspace_id": scenario["workspace"]["id"],
                "created_at": now_iso(),
            }
        )
        if not any(w["id"] == workspace_id for w in data["workspaces"]):
            data["workspaces"].append(workspace)

        keys = {
            (m["workspace_id"], m["subject"].lower(), m["relation"], m["object"].lower())
            for m in data["memories"]
        }
        for raw in scenario["memories"]:
            key = (workspace_id, raw["subject"].lower(), raw["relation"], raw["object"].lower())
            if key not in keys:
                data["memories"].append(MemoryItem(workspace_id=workspace_id, **raw).model_dump())
        self._write(data)
        return workspace_id

    def get_workspace(self, workspace_id: str) -> dict | None:
        return next((w for w in self._read()["workspaces"] if w["id"] == workspace_id), None)

    def list_memories(self, workspace_id: str) -> list[dict]:
        return [m for m in self._read()["memories"] if m["workspace_id"] == workspace_id]

    def upsert_memory(self, memory: MemoryItem) -> None:
        data = self._read()
        row = memory.model_dump()
        for index, existing in enumerate(data["memories"]):
            if existing["id"] == memory.id:
                data["memories"][index] = row
                self._write(data)
                return
        data["memories"].append(row)
        self._write(data)

    def update_memory_status(self, memory_id: str, status: str) -> None:
        data = self._read()
        for memory in data["memories"]:
            if memory["id"] == memory_id:
                memory["status"] = status
                memory["last_seen_at"] = now_iso()
        self._write(data)

    def add_message(self, message: Message) -> None:
        data = self._read()
        data["messages"].append(message.model_dump())
        self._write(data)

    def list_messages(self, workspace_id: str) -> list[dict]:
        rows = [m for m in self._read()["messages"] if m["workspace_id"] == workspace_id]
        return sorted(rows, key=lambda row: row.get("created_at", ""))

    def add_trace(self, trace: AgentTrace) -> None:
        data = self._read()
        data["traces"].append(trace.model_dump())
        self._write(data)

    def list_traces(self, workspace_id: str) -> list[dict]:
        rows = [t for t in self._read()["traces"] if t["workspace_id"] == workspace_id]
        return sorted(rows, key=lambda row: row.get("created_at", ""))


class SupabaseStore:
    def __init__(self):
        from supabase import create_client

        if not settings.has_supabase:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required for Supabase mode.")
        self.client = create_client(settings.supabase_url, settings.supabase_key)

    def _clear_workspace(self, workspace_id: str) -> None:
        for table in ["traces", "messages", "memories"]:
            self.client.table(table).delete().eq("workspace_id", workspace_id).execute()
        self.client.table("workspaces").delete().eq("id", workspace_id).execute()

    def clone_scenario(self, scenario_name: str, workspace_id: str, reset: bool = False) -> str:
        scenario = SCENARIOS[scenario_name]
        if reset:
            self._clear_workspace(workspace_id)

        workspace = dict(scenario["workspace"])
        workspace.update(
            {
                "id": workspace_id,
                "name": f"{scenario_name} · Session",
                "source_scenario": scenario_name,
                "parent_workspace_id": scenario["workspace"]["id"],
            }
        )
        try:
            self.client.table("workspaces").upsert(workspace).execute()
        except Exception as exc:
            print("SUPABASE WORKSPACE UPSERT ERROR:")
            print(repr(exc))
            print("WORKSPACE PAYLOAD:")
            print(workspace)
            raise

        existing = self.list_memories(workspace_id)
        keys = {(m["subject"].lower(), m["relation"], m["object"].lower()) for m in existing}
        rows = []
        for raw in scenario["memories"]:
            key = (raw["subject"].lower(), raw["relation"], raw["object"].lower())
            if key not in keys:
                rows.append(MemoryItem(workspace_id=workspace_id, **raw).model_dump(exclude={"embedding"}))
        if rows:
            self.client.table("memories").insert(rows).execute()
        return workspace_id

    def get_workspace(self, workspace_id: str) -> dict | None:
        rows = self.client.table("workspaces").select("*").eq("id", workspace_id).limit(1).execute().data or []
        return rows[0] if rows else None

    def list_memories(self, workspace_id: str) -> list[dict]:
        return self.client.table("memories").select("*").eq("workspace_id", workspace_id).execute().data or []

    def upsert_memory(self, memory: MemoryItem) -> None:
        payload = memory.model_dump()
        if payload.get("embedding") is None:
            payload.pop("embedding", None)
        self.client.table("memories").upsert(payload).execute()

    def update_memory_status(self, memory_id: str, status: str) -> None:
        self.client.table("memories").update(
            {"status": status, "last_seen_at": now_iso()}
        ).eq("id", memory_id).execute()

    def add_message(self, message: Message) -> None:
        self.client.table("messages").insert(message.model_dump()).execute()

    def list_messages(self, workspace_id: str) -> list[dict]:
        return (
            self.client.table("messages")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at")
            .execute()
            .data
            or []
        )

    def add_trace(self, trace: AgentTrace) -> None:
        self.client.table("traces").insert(
            {
                "id": trace.id,
                "workspace_id": trace.workspace_id,
                "query": trace.query,
                "payload": trace.model_dump(),
                "created_at": trace.created_at,
            }
        ).execute()

    def list_traces(self, workspace_id: str) -> list[dict]:
        rows = (
            self.client.table("traces")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at")
            .execute()
            .data
            or []
        )
        return [row.get("payload", row) for row in rows]


def get_store() -> Store:
    if settings.backend_mode == "supabase":
        if not settings.has_supabase:
            raise RuntimeError(
                "BACKEND_MODE is set to 'supabase', but SUPABASE_URL "
                "or SUPABASE_KEY is missing."
            )

        return SupabaseStore()

    return LocalStore()
