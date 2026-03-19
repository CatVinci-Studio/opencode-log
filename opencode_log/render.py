from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Message, Project, Session, format_local_time
from .storage import safe_slug

RENDER_VERSION = "0.4"


@dataclass
class RenderedPart:
    kind: str
    html: str
    css_class: str


@dataclass
class RenderedMessage:
    id: str
    role: str
    role_label: str
    css_class: str
    created_text: str
    created_ms: int
    mode: str | None
    agent: str | None
    model: str | None
    provider: str | None
    finish: str | None
    error: str | None
    token_text: str
    cost_text: str
    has_tool: bool
    has_reasoning: bool
    search_blob: str
    parts: list[RenderedPart]


def _env() -> Environment:
    template_dir = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _json_code_block(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return f"<pre>{html.escape(text)}</pre>"


def _render_part(part: dict[str, Any]) -> RenderedPart:
    part_type = str(part.get("type", "unknown"))

    if part_type == "text":
        text = part.get("text", "")
        return RenderedPart(
            kind="text",
            css_class="part-text",
            html=f"<pre>{html.escape(str(text))}</pre>",
        )

    if part_type == "reasoning":
        text = part.get("text", "")
        content = "<details class='collapsible-details'><summary>Reasoning</summary><pre>{}</pre></details>".format(
            html.escape(str(text))
        )
        return RenderedPart(kind="reasoning", css_class="part-reasoning", html=content)

    if part_type == "tool":
        tool_name = str(part.get("tool", "tool"))
        state = part.get("state") or {}
        status = state.get("status", "unknown")
        blocks = [
            f"<details class='collapsible-details part-tool-block'><summary>Tool: {html.escape(tool_name)} ({html.escape(str(status))})</summary>"
        ]
        for key in ("title", "metadata", "input", "output", "error"):
            value = state.get(key)
            if value in (None, "", {}, []):
                continue
            blocks.append(
                f"<div><strong>{html.escape(key)}</strong>{_json_code_block(value)}</div>"
            )
        blocks.append("</details>")
        return RenderedPart(kind="tool", css_class="part-tool", html="".join(blocks))

    if part_type in {
        "step-start",
        "step-finish",
        "compaction",
        "agent",
        "patch",
        "file",
        "subtask",
        "snapshot",
        "retry",
    }:
        return RenderedPart(
            kind=part_type,
            css_class=f"part-{part_type}",
            html=(
                f"<details class='collapsible-details'><summary>{html.escape(part_type)}</summary>"
                f"{_json_code_block(part)}</details>"
            ),
        )

    return RenderedPart(
        kind=part_type,
        css_class="part-unknown",
        html=f"<details class='collapsible-details'><summary>{html.escape(part_type)}</summary>{_json_code_block(part)}</details>",
    )


def _token_text(message: Message) -> str:
    parts = [
        f"in {message.tokens_input:,}",
        f"out {message.tokens_output:,}",
    ]
    if message.tokens_reasoning:
        parts.append(f"reason {message.tokens_reasoning:,}")
    if message.tokens_cache_read:
        parts.append(f"cache r {message.tokens_cache_read:,}")
    if message.tokens_cache_write:
        parts.append(f"cache w {message.tokens_cache_write:,}")
    return " | ".join(parts)


def _build_search_blob(message: Message) -> str:
    chunks: list[str] = [
        message.role,
        message.mode or "",
        message.agent or "",
        message.model or "",
        message.provider or "",
    ]
    for part in message.parts:
        part_type = str(part.get("type", ""))
        chunks.append(part_type)
        if part_type in {"text", "reasoning"}:
            chunks.append(str(part.get("text", "")))
        if part_type == "tool":
            chunks.append(str(part.get("tool", "")))
            state = part.get("state") or {}
            if isinstance(state, dict):
                for key in ("title", "status"):
                    chunks.append(str(state.get(key, "")))
    return " ".join(chunks).lower()


def _render_message(message: Message) -> RenderedMessage:
    role = message.role
    role_label = role.capitalize()
    css_class = role if role in {"user", "assistant"} else "unknown"

    rendered_parts = [_render_part(p) for p in message.parts]
    kinds = {p.kind for p in rendered_parts}
    created_ms = int(message.created_ms or 0)

    return RenderedMessage(
        id=message.id,
        role=role,
        role_label=role_label,
        css_class=css_class,
        created_text=format_local_time(message.created_ms),
        created_ms=created_ms,
        mode=message.mode,
        agent=message.agent,
        model=message.model,
        provider=message.provider,
        finish=message.finish,
        error=message.error,
        token_text=_token_text(message),
        cost_text=f"{message.cost:.6f}",
        has_tool="tool" in kinds,
        has_reasoning="reasoning" in kinds,
        search_blob=_build_search_blob(message),
        parts=rendered_parts,
    )


def session_render_signature(session: Session) -> str:
    return "|".join(
        [
            RENDER_VERSION,
            session.info.id,
            str(session.info.updated_ms or 0),
            str(session.message_count),
            str(len(session.todos)),
            str(len(session.diffs)),
            str(session.total_input_tokens),
            str(session.total_output_tokens),
            f"{session.total_cost:.6f}",
        ]
    )


def combined_render_signature(project: Project, sessions: list[Session]) -> str:
    session_sig = ",".join(session_render_signature(s) for s in sessions)
    return f"{RENDER_VERSION}|combined|{project.id}|{session_sig}"


def index_render_signature(
    projects: list[Project], sessions_by_project: dict[str, list[Session]]
) -> str:
    blocks: list[str] = [RENDER_VERSION, "index"]
    for project in sorted(projects, key=lambda p: p.id):
        sessions = sessions_by_project.get(project.id, [])
        if not sessions:
            continue
        blocks.append(project.id)
        blocks.extend(session_render_signature(s) for s in sessions)
    return "|".join(blocks)


def render_session_page(
    session: Session,
    out_file: Path,
    project_name: str,
    back_link: str,
    session_links: list[dict[str, str]],
) -> None:
    env = _env()
    template = env.get_template("transcript.html")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    html_content = template.render(
        title=session.info.title,
        project_name=project_name,
        session=session,
        session_created_text=format_local_time(session.info.created_ms),
        session_updated_text=format_local_time(session.info.updated_ms),
        rendered_messages=[_render_message(m) for m in session.messages],
        session_links=session_links,
        back_link=back_link,
    )
    out_file.write_text(html_content, encoding="utf-8")


def render_combined_page(
    project: Project,
    sessions: list[Session],
    out_file: Path,
    back_link: str,
) -> None:
    env = _env()
    template = env.get_template("combined.html")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    rendered_sessions: list[dict[str, Any]] = []
    session_links: list[dict[str, str]] = []
    for session in sessions:
        anchor = f"ses-{session.info.id}"
        session_links.append(
            {
                "id": session.info.id,
                "title": session.info.title,
                "anchor": anchor,
                "file": f"session-{session.info.id}.html",
            }
        )
        rendered_sessions.append(
            {
                "info": session.info,
                "anchor": anchor,
                "created_text": format_local_time(session.info.created_ms),
                "updated_text": format_local_time(session.info.updated_ms),
                "rendered_messages": [_render_message(m) for m in session.messages],
                "message_count": session.message_count,
                "tool_call_count": session.tool_call_count,
                "total_input_tokens": session.total_input_tokens,
                "total_output_tokens": session.total_output_tokens,
                "total_reasoning_tokens": session.total_reasoning_tokens,
                "total_cost": session.total_cost,
            }
        )

    html_content = template.render(
        title=f"{project.display_name} - Combined Transcripts",
        project=project,
        sessions=rendered_sessions,
        session_links=session_links,
        back_link=back_link,
    )
    out_file.write_text(html_content, encoding="utf-8")


def render_index_page(
    output_root: Path,
    projects: list[Project],
    sessions_by_project: dict[str, list[Session]],
) -> Path:
    env = _env()
    template = env.get_template("index.html")

    project_cards: list[dict[str, Any]] = []
    total_sessions = 0
    total_messages = 0
    total_cost = 0.0
    total_in_tokens = 0
    total_out_tokens = 0

    for project in projects:
        sessions = sessions_by_project.get(project.id, [])
        if not sessions:
            continue
        total_sessions += len(sessions)

        project_slug = f"{safe_slug(project.display_name)}-{project.id[:8]}"
        base = f"projects/{project_slug}"
        summary = {
            "id": project.id,
            "name": project.display_name,
            "worktree": project.worktree,
            "session_count": len(sessions),
            "combined_link": f"{base}/combined_transcripts.html",
            "sessions": [],
        }

        for s in sessions:
            total_messages += s.message_count
            total_cost += s.total_cost
            total_in_tokens += s.total_input_tokens
            total_out_tokens += s.total_output_tokens
            summary["sessions"].append(
                {
                    "id": s.info.id,
                    "title": s.info.title,
                    "updated": format_local_time(s.info.updated_ms),
                    "updated_ms": int(s.info.updated_ms or 0),
                    "message_count": s.message_count,
                    "tool_count": s.tool_call_count,
                    "cost": f"${s.total_cost:.6f}",
                    "token_summary": f"in {s.total_input_tokens:,} / out {s.total_output_tokens:,}",
                    "link": f"{base}/session-{s.info.id}.html",
                }
            )
        project_cards.append(summary)

    output_root.mkdir(parents=True, exist_ok=True)
    index_path = output_root / "index.html"
    html_content = template.render(
        title="OpenCode Log Index",
        projects=project_cards,
        total_projects=len(project_cards),
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_cost=f"${total_cost:.6f}",
        total_token_summary=f"in {total_in_tokens:,} / out {total_out_tokens:,}",
    )
    index_path.write_text(html_content, encoding="utf-8")
    return index_path
