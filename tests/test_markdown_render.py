from __future__ import annotations

from pathlib import Path

from opencode_log.markdown import render_session_markdown
from opencode_log.models import Message, Session, SessionInfo, TodoItem


def test_render_session_markdown_contains_core_sections(tmp_path: Path) -> None:
    session = Session(
        info=SessionInfo(
            id="ses_1",
            project_id="proj_1",
            directory="/tmp/work",
            title="My Session",
            slug=None,
            version="1",
            created_ms=1000,
            updated_ms=2000,
        ),
        messages=[
            Message(
                id="msg_1",
                session_id="ses_1",
                role="assistant",
                created_ms=1200,
                completed_ms=1300,
                model="m",
                provider="p",
                mode="normal",
                agent="build",
                parts=[{"type": "text", "text": "hello"}],
            )
        ],
        todos=[TodoItem(id="1", content="todo", status="completed", priority="high")],
    )

    out = tmp_path / "session-ses_1.md"
    render_session_markdown(
        session=session,
        out_file=out,
        project_name="proj",
        session_links=[
            {"id": "ses_1", "title": "My Session", "file": "session-ses_1.html"}
        ],
    )
    text = out.read_text(encoding="utf-8")
    assert "# My Session" in text
    assert "## Todo" in text
    assert "## Messages" in text
    assert "hello" in text
