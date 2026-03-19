from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

import dateparser

from .models import Message, Project, Session, SessionDiffItem, SessionInfo, TodoItem
from .normalizer import inspect_storage_schema, normalize_message

if TYPE_CHECKING:
    from .cache import CacheManager


def _read_json_file(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def parse_date_to_ms(text: str | None, end_of_day: bool = False) -> int | None:
    if not text:
        return None
    dt = dateparser.parse(
        text,
        settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    if dt is None:
        return None
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
    else:
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(dt.timestamp() * 1000)


def load_projects(storage_dir: Path) -> list[Project]:
    project_dir = storage_dir / "project"
    projects: list[Project] = []
    if not project_dir.exists():
        return projects

    for file in sorted(project_dir.glob("*.json")):
        data = _read_json_file(file)
        if not isinstance(data, dict):
            continue
        time_data = data.get("time") or {}
        projects.append(
            Project(
                id=str(data.get("id", "")),
                worktree=str(data.get("worktree", "")),
                vcs=data.get("vcs"),
                created_ms=time_data.get("created"),
                updated_ms=time_data.get("updated"),
            )
        )
    return projects


def _load_project_sessions(storage_dir: Path, project_id: str) -> list[SessionInfo]:
    session_root = storage_dir / "session" / project_id
    infos: list[SessionInfo] = []
    if not session_root.exists():
        return infos

    for file in sorted(session_root.glob("ses_*.json")):
        data = _read_json_file(file)
        if not isinstance(data, dict):
            continue
        t = data.get("time") or {}
        s = data.get("summary") or {}
        infos.append(
            SessionInfo(
                id=str(data.get("id", "")),
                project_id=str(data.get("projectID", project_id)),
                directory=str(data.get("directory", "")),
                title=str(data.get("title", "Untitled Session")),
                slug=data.get("slug"),
                version=data.get("version"),
                created_ms=t.get("created"),
                updated_ms=t.get("updated"),
                additions=int(s.get("additions", 0) or 0),
                deletions=int(s.get("deletions", 0) or 0),
                files=int(s.get("files", 0) or 0),
            )
        )
    return infos


def _part_sort_key(part: dict[str, Any]) -> tuple[int, int, str]:
    time_data = part.get("time") or {}
    start = int(time_data.get("start", 0) or 0)
    end = int(time_data.get("end", 0) or 0)
    return (start, end, str(part.get("id", "")))


def _load_parts_for_message(storage_dir: Path, message_id: str) -> list[dict[str, Any]]:
    part_dir = storage_dir / "part" / message_id
    if not part_dir.exists():
        return []

    items: list[dict[str, Any]] = []
    for file in sorted(part_dir.glob("prt_*.json")):
        part = _read_json_file(file)
        if isinstance(part, dict):
            items.append(part)
    items.sort(key=_part_sort_key)
    return items


def _load_messages(storage_dir: Path, session_id: str) -> list[Message]:
    message_dir = storage_dir / "message" / session_id
    if not message_dir.exists():
        return []

    messages: list[Message] = []
    for file in sorted(message_dir.glob("msg_*.json")):
        data = _read_json_file(file)
        if not isinstance(data, dict):
            continue
        m = normalize_message(
            raw=data,
            session_id=session_id,
            parts=_load_parts_for_message(storage_dir, str(data.get("id", ""))),
        )
        messages.append(m)

    messages.sort(key=lambda x: ((x.created_ms or 0), x.id))
    return messages


def _load_todos(storage_dir: Path, session_id: str) -> list[TodoItem]:
    todo_path = storage_dir / "todo" / f"{session_id}.json"
    data = _read_json_file(todo_path)
    if not isinstance(data, list):
        return []

    items: list[TodoItem] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        items.append(
            TodoItem(
                id=str(row.get("id", "")),
                content=str(row.get("content", "")),
                status=str(row.get("status", "pending")),
                priority=str(row.get("priority", "medium")),
            )
        )
    return items


def _load_session_diffs(storage_dir: Path, session_id: str) -> list[SessionDiffItem]:
    diff_path = storage_dir / "session_diff" / f"{session_id}.json"
    data = _read_json_file(diff_path)
    if not isinstance(data, list):
        return []

    items: list[SessionDiffItem] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        items.append(
            SessionDiffItem(
                file=str(row.get("file", "")),
                status=str(row.get("status", "modified")),
                additions=int(row.get("additions", 0) or 0),
                deletions=int(row.get("deletions", 0) or 0),
            )
        )
    return items


def _session_in_range(
    session: SessionInfo,
    from_ms: int | None,
    to_ms: int | None,
) -> bool:
    if from_ms is None and to_ms is None:
        return True
    updated = session.updated_ms or session.created_ms or 0
    if from_ms is not None and updated < from_ms:
        return False
    if to_ms is not None and updated > to_ms:
        return False
    return True


def _message_in_range(message: Message, from_ms: int | None, to_ms: int | None) -> bool:
    if from_ms is None and to_ms is None:
        return True
    ts = message.created_ms or 0
    if from_ms is not None and ts < from_ms:
        return False
    if to_ms is not None and ts > to_ms:
        return False
    return True


def load_project_sessions(
    storage_dir: Path,
    project_id: str,
    from_ms: int | None = None,
    to_ms: int | None = None,
    max_sessions: int | None = None,
    cache_manager: "CacheManager | None" = None,
    include_todos: bool = True,
    include_diffs: bool = True,
) -> list[Session]:
    result: list[Session] = []
    infos = _load_project_sessions(storage_dir, project_id)
    infos.sort(key=lambda x: ((x.updated_ms or x.created_ms or 0), x.id), reverse=True)

    for info in infos:
        if not _session_in_range(info, from_ms, to_ms):
            continue
        cached = (
            cache_manager.get_session(info.id, info.updated_ms)
            if cache_manager
            else None
        )
        if cached is not None:
            session_loaded = cached
        else:
            session_loaded = Session(
                info=info,
                messages=_load_messages(storage_dir, info.id),
                todos=_load_todos(storage_dir, info.id),
                diffs=_load_session_diffs(storage_dir, info.id),
            )
            if cache_manager:
                cache_manager.set_session(session_loaded)

        messages = session_loaded.messages
        if from_ms is not None or to_ms is not None:
            messages = [m for m in messages if _message_in_range(m, from_ms, to_ms)]
        if not messages:
            continue
        result.append(
            Session(
                info=info,
                messages=messages,
                todos=session_loaded.todos if include_todos else [],
                diffs=session_loaded.diffs if include_diffs else [],
            )
        )
        if max_sessions is not None and len(result) >= max_sessions:
            break

    result.sort(
        key=lambda s: (s.info.updated_ms or s.info.created_ms or 0, s.info.id),
        reverse=True,
    )
    return result


def safe_slug(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "project"


def get_storage_schema_warnings(storage_dir: Path) -> list[str]:
    return inspect_storage_schema(storage_dir)
