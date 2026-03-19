from __future__ import annotations

import json
from pathlib import Path

from opencode_log.storage import (
    get_storage_schema_warnings,
    load_project_sessions,
    load_projects,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _build_minimal_storage(root: Path) -> Path:
    storage = root / "storage"
    project_id = "proj_1"
    session_id = "ses_1"
    message_id = "msg_1"

    _write_json(
        storage / "project" / f"{project_id}.json",
        {
            "id": project_id,
            "worktree": "/tmp/work",
            "time": {"created": 1000, "updated": 2000},
        },
    )
    _write_json(
        storage / "session" / project_id / f"{session_id}.json",
        {
            "id": session_id,
            "projectID": project_id,
            "title": "Test Session",
            "directory": "/tmp/work",
            "version": "1",
            "time": {"created": 1100, "updated": 2200},
            "summary": {"additions": 1, "deletions": 1, "files": 1},
        },
    )
    _write_json(
        storage / "message" / session_id / f"{message_id}.json",
        {
            "id": message_id,
            "sessionID": session_id,
            "role": "assistant",
            "time": {"created": 1200, "completed": 1250},
            "tokens": {
                "input": 3,
                "output": 7,
                "reasoning": 2,
                "cache": {"read": 1, "write": 1},
            },
            "cost": 0.123,
            "finish": "stop",
        },
    )
    _write_json(
        storage / "part" / message_id / "prt_1.json",
        {
            "id": "prt_1",
            "type": "text",
            "text": "hello",
            "time": {"start": 1200, "end": 1201},
        },
    )
    _write_json(
        storage / "part" / message_id / "prt_2.json",
        {
            "id": "prt_2",
            "type": "new-future-type",
            "value": "x",
            "time": {"start": 1202, "end": 1203},
        },
    )
    _write_json(
        storage / "todo" / f"{session_id}.json",
        [{"id": "1", "content": "item", "status": "completed", "priority": "high"}],
    )
    _write_json(
        storage / "session_diff" / f"{session_id}.json",
        [{"file": "a.py", "status": "modified", "additions": 10, "deletions": 2}],
    )
    return storage


def test_load_project_sessions_normalizes_unknown_parts(tmp_path: Path) -> None:
    storage = _build_minimal_storage(tmp_path)
    projects = load_projects(storage)
    assert len(projects) == 1

    sessions = load_project_sessions(storage, project_id="proj_1")
    assert len(sessions) == 1
    session = sessions[0]
    assert len(session.todos) == 1
    assert len(session.diffs) == 1

    parts = session.messages[0].parts
    assert len(parts) == 2
    assert parts[0]["type"] == "text"
    assert parts[1]["type"] == "unknown"
    assert parts[1]["raw_type"] == "new-future-type"


def test_schema_warning_when_missing_directories(tmp_path: Path) -> None:
    storage = tmp_path / "storage"
    storage.mkdir(parents=True)
    warnings = get_storage_schema_warnings(storage)
    assert any("missing storage directory" in msg for msg in warnings)
