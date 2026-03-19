from __future__ import annotations

from pathlib import Path

from opencode_log.cache import CacheManager
from opencode_log.models import Message, Session, SessionDiffItem, SessionInfo, TodoItem


def test_cache_roundtrip_with_todo_and_diff(tmp_path: Path) -> None:
    cache = CacheManager(tmp_path / "cache")
    session = Session(
        info=SessionInfo(
            id="ses_1",
            project_id="proj_1",
            directory="/tmp/work",
            title="s",
            slug=None,
            version="1",
            created_ms=1,
            updated_ms=2,
        ),
        messages=[
            Message(
                id="msg_1",
                session_id="ses_1",
                role="user",
                created_ms=1,
                completed_ms=1,
                model=None,
                provider=None,
                mode=None,
                agent=None,
                parts=[{"type": "text", "text": "hello"}],
            )
        ],
        todos=[TodoItem(id="1", content="todo", status="completed", priority="high")],
        diffs=[
            SessionDiffItem(file="a.py", status="modified", additions=3, deletions=1)
        ],
    )
    cache.set_session(session)
    cache.save()

    loaded = cache.get_session("ses_1", 2)
    assert loaded is not None
    assert len(loaded.todos) == 1
    assert len(loaded.diffs) == 1
    assert loaded.messages[0].parts[0]["type"] == "text"
