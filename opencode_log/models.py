from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def ms_to_datetime(ms: int | None) -> datetime | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


def format_local_time(ms: int | None) -> str:
    dt = ms_to_datetime(ms)
    if dt is None:
        return "-"
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Project:
    id: str
    worktree: str
    vcs: str | None = None
    created_ms: int | None = None
    updated_ms: int | None = None

    @property
    def display_name(self) -> str:
        path = Path(self.worktree)
        if path.name:
            return path.name
        return self.worktree


@dataclass
class SessionInfo:
    id: str
    project_id: str
    directory: str
    title: str
    slug: str | None
    version: str | None
    created_ms: int | None
    updated_ms: int | None
    additions: int = 0
    deletions: int = 0
    files: int = 0


@dataclass
class Message:
    id: str
    session_id: str
    role: str
    created_ms: int | None
    completed_ms: int | None
    model: str | None
    provider: str | None
    mode: str | None
    agent: str | None
    cost: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_reasoning: int = 0
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    finish: str | None = None
    error: str | None = None
    parts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TodoItem:
    id: str
    content: str
    status: str
    priority: str


@dataclass
class SessionDiffItem:
    file: str
    status: str
    additions: int
    deletions: int


@dataclass
class Session:
    info: SessionInfo
    messages: list[Message]
    todos: list[TodoItem] = field(default_factory=list)
    diffs: list[SessionDiffItem] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def total_cost(self) -> float:
        return sum(m.cost for m in self.messages)

    @property
    def total_input_tokens(self) -> int:
        return sum(m.tokens_input for m in self.messages)

    @property
    def total_output_tokens(self) -> int:
        return sum(m.tokens_output for m in self.messages)

    @property
    def total_reasoning_tokens(self) -> int:
        return sum(m.tokens_reasoning for m in self.messages)

    @property
    def total_cache_read_tokens(self) -> int:
        return sum(m.tokens_cache_read for m in self.messages)

    @property
    def total_cache_write_tokens(self) -> int:
        return sum(m.tokens_cache_write for m in self.messages)

    @property
    def tool_call_count(self) -> int:
        count = 0
        for message in self.messages:
            count += sum(1 for part in message.parts if part.get("type") == "tool")
        return count
