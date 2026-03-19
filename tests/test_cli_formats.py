from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from opencode_log.cli import main


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _storage(root: Path) -> Path:
    storage = root / "storage"
    project_id = "proj_1"
    session_id = "ses_1"
    message_id = "msg_1"

    _write_json(
        storage / "project" / f"{project_id}.json",
        {
            "id": project_id,
            "worktree": "/tmp/work",
            "time": {"created": 1, "updated": 2},
        },
    )
    _write_json(
        storage / "session" / project_id / f"{session_id}.json",
        {
            "id": session_id,
            "projectID": project_id,
            "title": "s",
            "directory": "/tmp/work",
            "version": "1",
            "time": {"created": 10, "updated": 20},
            "summary": {"additions": 0, "deletions": 0, "files": 0},
        },
    )
    _write_json(
        storage / "message" / session_id / f"{message_id}.json",
        {
            "id": message_id,
            "sessionID": session_id,
            "role": "user",
            "time": {"created": 12, "completed": 13},
        },
    )
    _write_json(
        storage / "part" / message_id / "prt_1.json",
        {
            "id": "prt_1",
            "type": "text",
            "text": "hello",
            "time": {"start": 12, "end": 13},
        },
    )
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
