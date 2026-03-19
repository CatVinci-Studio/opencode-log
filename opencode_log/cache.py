from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Message, Session, SessionDiffItem, SessionInfo, TodoItem

CACHE_VERSION = 2


def _session_to_dict(session: Session) -> dict[str, Any]:
    info = session.info
    return {
        "info": {
            "id": info.id,
            "project_id": info.project_id,
            "directory": info.directory,
            "title": info.title,
            "slug": info.slug,
            "version": info.version,
            "created_ms": info.created_ms,
            "updated_ms": info.updated_ms,
            "additions": info.additions,
            "deletions": info.deletions,
            "files": info.files,
        },
        "messages": [
            {
                "id": m.id,
                "session_id": m.session_id,
                "role": m.role,
                "created_ms": m.created_ms,
                "completed_ms": m.completed_ms,
                "model": m.model,
                "provider": m.provider,
                "mode": m.mode,
                "agent": m.agent,
                "cost": m.cost,
                "tokens_input": m.tokens_input,
                "tokens_output": m.tokens_output,
                "tokens_reasoning": m.tokens_reasoning,
                "tokens_cache_read": m.tokens_cache_read,
                "tokens_cache_write": m.tokens_cache_write,
                "finish": m.finish,
                "error": m.error,
                "parts": m.parts,
            }
            for m in session.messages
        ],
        "todos": [
            {
                "id": item.id,
                "content": item.content,
                "status": item.status,
                "priority": item.priority,
            }
            for item in session.todos
        ],
        "diffs": [
            {
                "file": item.file,
                "status": item.status,
                "additions": item.additions,
                "deletions": item.deletions,
            }
            for item in session.diffs
        ],
    }


def _session_from_dict(data: dict[str, Any]) -> Session | None:
    info_data = data.get("info")
    if not isinstance(info_data, dict):
        return None

    info = SessionInfo(
        id=str(info_data.get("id", "")),
        project_id=str(info_data.get("project_id", "")),
        directory=str(info_data.get("directory", "")),
        title=str(info_data.get("title", "Untitled Session")),
        slug=info_data.get("slug"),
        version=info_data.get("version"),
        created_ms=info_data.get("created_ms"),
        updated_ms=info_data.get("updated_ms"),
        additions=int(info_data.get("additions", 0) or 0),
        deletions=int(info_data.get("deletions", 0) or 0),
        files=int(info_data.get("files", 0) or 0),
    )

    raw_messages = data.get("messages")
    if not isinstance(raw_messages, list):
        return Session(info=info, messages=[])

    messages: list[Message] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        raw_parts = item.get("parts")
        parts = raw_parts if isinstance(raw_parts, list) else []
        messages.append(
            Message(
                id=str(item.get("id", "")),
                session_id=str(item.get("session_id", info.id)),
                role=str(item.get("role", "unknown")),
                created_ms=item.get("created_ms"),
                completed_ms=item.get("completed_ms"),
                model=item.get("model"),
                provider=item.get("provider"),
                mode=item.get("mode"),
                agent=item.get("agent"),
                cost=float(item.get("cost", 0.0) or 0.0),
                tokens_input=int(item.get("tokens_input", 0) or 0),
                tokens_output=int(item.get("tokens_output", 0) or 0),
                tokens_reasoning=int(item.get("tokens_reasoning", 0) or 0),
                tokens_cache_read=int(item.get("tokens_cache_read", 0) or 0),
                tokens_cache_write=int(item.get("tokens_cache_write", 0) or 0),
                finish=item.get("finish"),
                error=item.get("error"),
                parts=parts,
            )
        )
    todos: list[TodoItem] = []
    for item in data.get("todos", []):
        if not isinstance(item, dict):
            continue
        todos.append(
            TodoItem(
                id=str(item.get("id", "")),
                content=str(item.get("content", "")),
                status=str(item.get("status", "pending")),
                priority=str(item.get("priority", "medium")),
            )
        )

    diffs: list[SessionDiffItem] = []
    for item in data.get("diffs", []):
        if not isinstance(item, dict):
            continue
        diffs.append(
            SessionDiffItem(
                file=str(item.get("file", "")),
                status=str(item.get("status", "modified")),
                additions=int(item.get("additions", 0) or 0),
                deletions=int(item.get("deletions", 0) or 0),
            )
        )

    return Session(info=info, messages=messages, todos=todos, diffs=diffs)


class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.sessions_dir = cache_dir / "sessions"
        self.state_path = cache_dir / "state.json"
        self.data: dict[str, Any] = {
            "version": CACHE_VERSION,
            "session_cache": {},
            "render_cache": {},
        }
        self._load()

    def _load(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and payload.get("version") == CACHE_VERSION:
                self.data = payload
        except Exception:
            self.data = {
                "version": CACHE_VERSION,
                "session_cache": {},
                "render_cache": {},
            }

    def save(self) -> None:
        self.state_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        self.data = {
            "version": CACHE_VERSION,
            "session_cache": {},
            "render_cache": {},
        }
        self.save()

    def get_session(self, session_id: str, updated_ms: int | None) -> Session | None:
        entries = self.data.get("session_cache")
        if not isinstance(entries, dict):
            return None
        entry = entries.get(session_id)
        if not isinstance(entry, dict):
            return None
        if entry.get("updated_ms") != updated_ms:
            return None
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return None
            return _session_from_dict(raw)
        except Exception:
            return None

    def set_session(self, session: Session) -> None:
        path = self.sessions_dir / f"{session.info.id}.json"
        path.write_text(
            json.dumps(_session_to_dict(session), ensure_ascii=False),
            encoding="utf-8",
        )
        entries = self.data.setdefault("session_cache", {})
        if isinstance(entries, dict):
            entries[session.info.id] = {
                "updated_ms": session.info.updated_ms,
            }

    def should_render(self, key: str, signature: str, out_path: Path) -> bool:
        cache = self.data.get("render_cache")
        if not isinstance(cache, dict):
            return True
        existing = cache.get(key)
        if not out_path.exists():
            return True
        if not isinstance(existing, dict):
            return True
        return existing.get("signature") != signature

    def mark_rendered(self, key: str, signature: str) -> None:
        cache = self.data.setdefault("render_cache", {})
        if isinstance(cache, dict):
            cache[key] = {"signature": signature}
