from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, TYPE_CHECKING

import dateparser

from .models import Message, Project, Session, SessionDiffItem, SessionInfo, TodoItem
from .normalizer import normalize_message

if TYPE_CHECKING:
    from .cache import CacheManager


def _parse_json_text(value: Any) -> Any | None:
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _resolve_db_path(storage_dir: Path) -> Path | None:
    if storage_dir.is_file() and storage_dir.name.endswith(".db"):
        return storage_dir

    candidates = [storage_dir / "opencode.db"]
    if storage_dir.name == "storage":
        candidates.append(storage_dir.parent / "opencode.db")

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _connect_db(storage_dir: Path) -> sqlite3.Connection | None:
    db_path = _resolve_db_path(storage_dir)
    if db_path is None:
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


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
    projects: list[Project] = []
    conn = _connect_db(storage_dir)
    if conn is None:
        return projects

    try:
        rows = conn.execute(
            """
            SELECT id, worktree, vcs, time_created, time_updated
            FROM project
            ORDER BY time_updated DESC, id ASC
            """
        ).fetchall()
        for row in rows:
            projects.append(
                Project(
                    id=str(row["id"] or ""),
                    worktree=str(row["worktree"] or ""),
                    vcs=row["vcs"],
                    created_ms=row["time_created"],
                    updated_ms=row["time_updated"],
                )
            )
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    return projects


def _load_project_sessions(
    conn: sqlite3.Connection, project_id: str
) -> list[SessionInfo]:
    infos: list[SessionInfo] = []
    rows = conn.execute(
        """
        SELECT
            id,
            project_id,
            directory,
            title,
            slug,
            version,
            summary_additions,
            summary_deletions,
            summary_files,
            time_created,
            time_updated
        FROM session
        WHERE project_id = ?
        ORDER BY time_updated DESC, id ASC
        """,
        (project_id,),
    ).fetchall()

    for row in rows:
        infos.append(
            SessionInfo(
                id=str(row["id"] or ""),
                project_id=str(row["project_id"] or project_id),
                directory=str(row["directory"] or ""),
                title=str(row["title"] or "Untitled Session"),
                slug=row["slug"],
                version=row["version"],
                created_ms=row["time_created"],
                updated_ms=row["time_updated"],
                additions=int(row["summary_additions"] or 0),
                deletions=int(row["summary_deletions"] or 0),
                files=int(row["summary_files"] or 0),
            )
        )
    return infos


def _load_parts_by_message(
    conn: sqlite3.Connection, session_id: str
) -> dict[str, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT id, message_id, time_created, time_updated, data
        FROM part
        WHERE session_id = ?
        ORDER BY time_created ASC, time_updated ASC, id ASC
        """,
        (session_id,),
    ).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        raw = _parse_json_text(row["data"])
        if not isinstance(raw, dict):
            continue
        payload = dict(raw)
        payload.setdefault("id", row["id"])
        time_data = payload.get("time")
        if not isinstance(time_data, dict):
            time_data = {}
        time_data.setdefault("start", row["time_created"])
        time_data.setdefault("end", row["time_updated"])
        payload["time"] = time_data
        message_id = str(row["message_id"] or "")
        grouped.setdefault(message_id, []).append(payload)
    return grouped


def _parse_session_diffs(raw_diffs: Any) -> list[SessionDiffItem]:
    if not isinstance(raw_diffs, list):
        return []

    parsed: list[SessionDiffItem] = []
    for row in raw_diffs:
        if not isinstance(row, dict):
            continue
        parsed.append(
            SessionDiffItem(
                file=str(row.get("file", "")),
                status=str(row.get("status", "modified")),
                additions=int(row.get("additions", 0) or 0),
                deletions=int(row.get("deletions", 0) or 0),
            )
        )
    return parsed


def _fallback_session_diffs_from_patch_parts(
    messages: list[Message],
) -> list[SessionDiffItem]:
    files: list[str] = []
    seen: set[str] = set()
    for message in messages:
        for part in message.parts:
            if part.get("type") != "patch":
                continue
            part_files = part.get("files")
            if not isinstance(part_files, list):
                continue
            for path in part_files:
                text = str(path)
                if not text or text in seen:
                    continue
                seen.add(text)
                files.append(text)
    return [
        SessionDiffItem(file=path, status="modified", additions=0, deletions=0)
        for path in files
    ]


def _load_messages_and_diffs(
    conn: sqlite3.Connection,
    session_id: str,
    parts_by_message: dict[str, list[dict[str, Any]]],
) -> tuple[list[Message], list[SessionDiffItem]]:
    messages: list[Message] = []
    latest_diffs: list[SessionDiffItem] = []

    rows = conn.execute(
        """
        SELECT id, session_id, time_created, time_updated, data
        FROM message
        WHERE session_id = ?
        ORDER BY time_created ASC, id ASC
        """,
        (session_id,),
    ).fetchall()

    for row in rows:
        data = _parse_json_text(row["data"])
        if not isinstance(data, dict):
            continue
        data = dict(data)
        data.setdefault("id", row["id"])
        data.setdefault("sessionID", row["session_id"])
        time_data = data.get("time")
        if not isinstance(time_data, dict):
            time_data = {}
        time_data.setdefault("created", row["time_created"])
        time_data.setdefault("completed", row["time_updated"])
        data["time"] = time_data

        summary = data.get("summary")
        if isinstance(summary, dict):
            parsed = _parse_session_diffs(summary.get("diffs"))
            if parsed:
                latest_diffs = parsed

        m = normalize_message(
            raw=data,
            session_id=session_id,
            parts=parts_by_message.get(str(row["id"] or ""), []),
        )
        messages.append(m)

    messages.sort(key=lambda x: ((x.created_ms or 0), x.id))
    if not latest_diffs:
        latest_diffs = _fallback_session_diffs_from_patch_parts(messages)
    return messages, latest_diffs


def _load_todos(conn: sqlite3.Connection, session_id: str) -> list[TodoItem]:
    rows = conn.execute(
        """
        SELECT session_id, content, status, priority, position
        FROM todo
        WHERE session_id = ?
        ORDER BY position ASC
        """,
        (session_id,),
    ).fetchall()

    items: list[TodoItem] = []
    for row in rows:
        item_id = f"{row['session_id']}:{int(row['position'] or 0)}"
        items.append(
            TodoItem(
                id=item_id,
                content=str(row["content"] or ""),
                status=str(row["status"] or "pending"),
                priority=str(row["priority"] or "medium"),
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
    conn = _connect_db(storage_dir)
    if conn is None:
        return []

    result: list[Session] = []
    infos = _load_project_sessions(conn, project_id)
    infos.sort(key=lambda x: ((x.updated_ms or x.created_ms or 0), x.id), reverse=True)

    try:
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
                parts_by_message = _load_parts_by_message(conn, info.id)
                messages, diffs = _load_messages_and_diffs(
                    conn, info.id, parts_by_message
                )
                session_loaded = Session(
                    info=info,
                    messages=messages,
                    todos=_load_todos(conn, info.id),
                    diffs=diffs,
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
    finally:
        conn.close()

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
    db_path = _resolve_db_path(storage_dir)
    if db_path is None:
        return ["opencode.db not found (expected in data directory)"]

    warnings: list[str] = []
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        available = {str(row[0]) for row in rows}
        required = {"project", "session", "message", "part", "todo"}
        missing = sorted(required - available)
        for table in missing:
            warnings.append(f"missing database table: {table}")

        if "session" in available:
            versions = {
                str(row[0])
                for row in conn.execute(
                    "SELECT DISTINCT version FROM session WHERE version IS NOT NULL AND version != '' LIMIT 20"
                ).fetchall()
            }
            if len(versions) > 1:
                warnings.append(
                    "multiple session schema versions detected: "
                    + ", ".join(sorted(versions))
                )
    except sqlite3.Error as exc:
        warnings.append(f"database error: {exc}")
    finally:
        if conn is not None:
            conn.close()

    return warnings
