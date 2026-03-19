from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Message, Project, Session, format_local_time
from .render import RENDER_VERSION, session_render_signature
from .storage import safe_slug


def _code_block(value: str, language: str = "") -> str:
    lang = language.strip()
    return f"```{lang}\n{value}\n```"


def _json_block(data: Any) -> str:
    return _code_block(json.dumps(data, ensure_ascii=False, indent=2), "json")


def _message_to_markdown(message: Message) -> str:
    lines: list[str] = []
    lines.append(
        f"### {message.role.capitalize()} - {format_local_time(message.created_ms)}"
    )
    lines.append("")

    tags: list[str] = []
    if message.agent:
        tags.append(f"agent: `{message.agent}`")
    if message.mode:
        tags.append(f"mode: `{message.mode}`")
    if message.provider or message.model:
        tags.append(f"model: `{message.provider or '-'} / {message.model or '-'}`")
    if message.finish:
        tags.append(f"finish: `{message.finish}`")
    if tags:
        lines.append("- " + " | ".join(tags))
    lines.append(
        f"- tokens: in `{message.tokens_input}` / out `{message.tokens_output}` / reasoning `{message.tokens_reasoning}`"
    )
    lines.append(f"- cost: `${message.cost:.6f}`")
    if message.error:
        lines.append(f"- error: `{message.error}`")
    lines.append("")

    for part in message.parts:
        part_type = str(part.get("type", "unknown"))
        if part_type == "text":
            lines.append(str(part.get("text", "")))
            lines.append("")
            continue
        if part_type == "reasoning":
            lines.append("<details><summary>Reasoning</summary>")
            lines.append("")
            lines.append(str(part.get("text", "")))
            lines.append("")
            lines.append("</details>")
            lines.append("")
            continue
        if part_type == "tool":
            lines.append("<details><summary>Tool</summary>")
            lines.append("")
            lines.append(f"- name: `{part.get('tool', 'tool')}`")
            state = part.get("state") if isinstance(part.get("state"), dict) else {}
            status = state.get("status")
            if status:
                lines.append(f"- status: `{status}`")
            lines.append("")
            lines.append(_json_block(state))
            lines.append("")
            lines.append("</details>")
            lines.append("")
            continue

        lines.append(f"<details><summary>{part_type}</summary>")
        lines.append("")
        lines.append(_json_block(part))
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_session_markdown(
    session: Session,
    out_file: Path,
    project_name: str,
    session_links: list[dict[str, str]],
) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# {session.info.title}")
    lines.append("")
    lines.append(f"- project: `{project_name}`")
    lines.append(f"- session id: `{session.info.id}`")
    lines.append(f"- directory: `{session.info.directory}`")
    lines.append(
        f"- tokens: in `{session.total_input_tokens}` / out `{session.total_output_tokens}`"
    )
    lines.append(f"- cost: `${session.total_cost:.6f}`")
    lines.append("")

    if session.todos:
        lines.append("## Todo")
        lines.append("")
        for item in session.todos:
            lines.append(
                f"- [{item.status}] ({item.priority}) {item.content} (`{item.id}`)"
            )
        lines.append("")

    if session.diffs:
        lines.append("## Session Diff")
        lines.append("")
        for item in session.diffs:
            lines.append(
                f"- `{item.file}` [{item.status}] +{item.additions} / -{item.deletions}"
            )
        lines.append("")

    lines.append("## Messages")
    lines.append("")
    for message in session.messages:
        lines.append(_message_to_markdown(message))

    if session_links:
        lines.append("## Other Sessions")
        lines.append("")
        for item in session_links:
            lines.append(f"- [{item['title']}]({item['file'].replace('.html', '.md')})")

    out_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def render_combined_markdown(
    project: Project, sessions: list[Session], out_file: Path
) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# {project.display_name} - Combined Transcripts")
    lines.append("")
    lines.append(f"- project path: `{project.worktree}`")
    lines.append(f"- sessions: `{len(sessions)}`")
    lines.append("")
    lines.append("## Sessions")
    lines.append("")
    for session in sessions:
        lines.append(
            f"- [{session.info.title}](session-{session.info.id}.md) | messages `{session.message_count}` | tools `{session.tool_call_count}`"
        )
    lines.append("")

    for session in sessions:
        lines.append(f"---\n\n## {session.info.title}\n")
        lines.append(
            f"_session: [{session.info.id}](session-{session.info.id}.md) | updated {format_local_time(session.info.updated_ms)}_\n"
        )
        for message in session.messages:
            lines.append(_message_to_markdown(message))

    out_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def render_index_markdown(
    output_root: Path,
    projects: list[Project],
    sessions_by_project: dict[str, list[Session]],
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    out_file = output_root / "index.md"
    lines: list[str] = ["# OpenCode Log Index", ""]
    for project in projects:
        sessions = sessions_by_project.get(project.id, [])
        if not sessions:
            continue
        project_slug = f"{safe_slug(project.display_name)}-{project.id[:8]}"
        lines.append(f"## {project.display_name}")
        lines.append("")
        lines.append(f"- path: `{project.worktree}`")
        lines.append(
            f"- combined: [combined_transcripts.md](projects/{project_slug}/combined_transcripts.md)"
        )
        lines.append("")
        for session in sessions:
            lines.append(
                f"- [{session.info.title}](projects/{project_slug}/session-{session.info.id}.md)"
            )
        lines.append("")

    out_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return out_file


def markdown_render_signature(session: Session) -> str:
    return f"md-{RENDER_VERSION}|{session_render_signature(session)}"
