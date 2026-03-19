from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from opencode_log.storage import (
    get_storage_schema_warnings,
    load_project_sessions,
    load_projects,
)


def _build_minimal_storage(root: Path) -> Path:
    storage = root / "opencode"
    storage.mkdir(parents=True, exist_ok=True)
    db_path = storage / "opencode.db"

    project_id = "proj_1"
    session_id = "ses_1"
    message_id = "msg_1"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE project (
                id TEXT PRIMARY KEY,
                worktree TEXT,
                vcs TEXT,
                time_created INTEGER,
                time_updated INTEGER
            );
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                parent_id TEXT,
                slug TEXT NOT NULL,
                directory TEXT NOT NULL,
                title TEXT NOT NULL,
                version TEXT NOT NULL,
                share_url TEXT,
                summary_additions INTEGER,
                summary_deletions INTEGER,
                summary_files INTEGER,
                summary_diffs TEXT,
                revert TEXT,
                permission TEXT,
                time_created INTEGER NOT NULL,
                time_updated INTEGER NOT NULL,
                time_compacting INTEGER,
                time_archived INTEGER,
                workspace_id TEXT
            );
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                time_created INTEGER NOT NULL,
                time_updated INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            CREATE TABLE part (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                time_created INTEGER NOT NULL,
                time_updated INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            CREATE TABLE todo (
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                position INTEGER NOT NULL,
                time_created INTEGER NOT NULL,
                time_updated INTEGER NOT NULL,
                PRIMARY KEY (session_id, position)
            );
            """
        )

        conn.execute(
            "INSERT INTO project (id, worktree, vcs, time_created, time_updated) VALUES (?, ?, ?, ?, ?)",
            (project_id, "/tmp/work", "git", 1000, 2000),
        )
        conn.execute(
            """
            INSERT INTO session (
                id, project_id, slug, directory, title, version,
                summary_additions, summary_deletions, summary_files,
                time_created, time_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                project_id,
                "test-session",
                "/tmp/work",
                "Test Session",
                "1",
                1,
                1,
                1,
                1100,
                2200,
            ),
        )
        message_payload = {
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
            "summary": {
                "diffs": [
                    {
                        "file": "a.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 2,
                    }
                ]
            },
        }
        conn.execute(
            "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, 1200, 1250, json.dumps(message_payload)),
        )
        conn.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "prt_1",
                message_id,
                session_id,
                1200,
                1201,
                json.dumps({"id": "prt_1", "type": "text", "text": "hello"}),
            ),
        )
        conn.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "prt_2",
                message_id,
                session_id,
                1202,
                1203,
                json.dumps({"id": "prt_2", "type": "new-future-type", "value": "x"}),
            ),
        )
        conn.execute(
            "INSERT INTO todo (session_id, content, status, priority, position, time_created, time_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, "item", "completed", "high", 0, 1230, 1230),
        )
        conn.commit()
    finally:
        conn.close()

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
    assert any("opencode.db not found" in msg for msg in warnings)
