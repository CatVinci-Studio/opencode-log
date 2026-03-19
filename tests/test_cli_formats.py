from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from click.testing import CliRunner

from opencode_log.cli import main


def _storage(root: Path) -> Path:
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
            (project_id, "/tmp/work", "git", 1, 2),
        )
        conn.execute(
            """
            INSERT INTO session (
                id, project_id, slug, directory, title, version,
                summary_additions, summary_deletions, summary_files,
                time_created, time_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, project_id, "s", "/tmp/work", "s", "1", 0, 0, 0, 10, 20),
        )
        conn.execute(
            "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
            (
                message_id,
                session_id,
                12,
                13,
                json.dumps(
                    {
                        "id": message_id,
                        "sessionID": session_id,
                        "role": "user",
                        "time": {"created": 12, "completed": 13},
                    }
                ),
            ),
        )
        conn.execute(
            "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "prt_1",
                message_id,
                session_id,
                12,
                13,
                json.dumps({"id": "prt_1", "type": "text", "text": "hello"}),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return storage


def test_cli_markdown_format_outputs_md_files(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    out = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--storage-dir",
            str(storage),
            "--output",
            str(out),
            "--all-projects",
            "--format",
            "markdown",
        ],
    )
    assert result.exit_code == 0
    assert (out / "index.md").exists()
    assert not (out / "index.html").exists()


def test_cli_html_format_renders_combined_sessions_content(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    out = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--storage-dir",
            str(storage),
            "--output",
            str(out),
            "--all-projects",
            "--format",
            "html",
            "--no-open-browser",
        ],
    )
    assert result.exit_code == 0

    combined_pages = list(out.glob("projects/*/combined_transcripts.html"))
    assert len(combined_pages) == 1

    combined_html = combined_pages[0].read_text(encoding="utf-8")
    assert "Search & Filter" in combined_html
    assert '<article class="message' in combined_html
    assert "hello" in combined_html
    assert "cost $$" not in combined_html
