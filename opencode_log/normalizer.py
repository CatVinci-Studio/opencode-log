from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Message

KNOWN_PART_TYPES = {
    "text",
    "reasoning",
    "tool",
    "step-start",
    "step-finish",
    "compaction",
    "agent",
    "patch",
    "file",
    "subtask",
    "snapshot",
    "retry",
}


def normalize_part(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)
    part_type = str(data.get("type", "unknown"))
    if part_type not in KNOWN_PART_TYPES:
        data["raw_type"] = part_type
        part_type = "unknown"
    data["type"] = part_type

    if part_type in {"text", "reasoning"}:
        data["text"] = str(data.get("text", ""))
    if part_type == "tool":
        tool = data.get("tool")
        data["tool"] = str(tool if tool is not None else "tool")
        state = data.get("state")
        data["state"] = state if isinstance(state, dict) else {}
    return data


def normalize_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        result.append(normalize_part(part))
    return result


def normalize_error_text(raw_error: Any) -> str | None:
    if not isinstance(raw_error, dict):
        return None
    name = str(raw_error.get("name", "Error"))
    payload = raw_error.get("data")
    message = ""
    if isinstance(payload, dict):
        message = str(payload.get("message", ""))
    text = f"{name}: {message}".strip(": ")
    return text or None


def normalize_message(
    raw: dict[str, Any],
    session_id: str,
    parts: list[dict[str, Any]],
) -> Message:
    t = raw.get("time")
    time_data = t if isinstance(t, dict) else {}
    tok = raw.get("tokens")
    token_data = tok if isinstance(tok, dict) else {}
    cache = token_data.get("cache")
    cache_data = cache if isinstance(cache, dict) else {}

    model = raw.get("model")
    model_data = model if isinstance(model, dict) else {}

    return Message(
        id=str(raw.get("id", "")),
        session_id=str(raw.get("sessionID", session_id)),
        role=str(raw.get("role", "unknown")),
        created_ms=time_data.get("created"),
        completed_ms=time_data.get("completed"),
        model=str(raw.get("modelID") or model_data.get("modelID") or "") or None,
        provider=str(raw.get("providerID") or model_data.get("providerID") or "")
        or None,
        mode=str(raw.get("mode", "")) or None,
        agent=str(raw.get("agent", "")) or None,
        cost=float(raw.get("cost", 0) or 0),
        tokens_input=int(token_data.get("input", 0) or 0),
        tokens_output=int(token_data.get("output", 0) or 0),
        tokens_reasoning=int(token_data.get("reasoning", 0) or 0),
        tokens_cache_read=int(cache_data.get("read", 0) or 0),
        tokens_cache_write=int(cache_data.get("write", 0) or 0),
        finish=str(raw.get("finish", "")) or None,
        error=normalize_error_text(raw.get("error")),
        parts=normalize_parts(parts),
    )


def inspect_storage_schema(storage_dir: Path) -> list[str]:
    warnings: list[str] = []
    required = ["project", "session", "message", "part"]
    for name in required:
        if not (storage_dir / name).exists():
            warnings.append(f"missing storage directory: {name}")

    # Lightweight shape checks
    project_dir = storage_dir / "project"
    sample_project = (
        next(project_dir.glob("*.json"), None) if project_dir.exists() else None
    )
    if sample_project is None:
        warnings.append("no project json files found")

    session_dir = storage_dir / "session"
    if session_dir.exists():
        versions: set[str] = set()
        checked = 0
        for project_path in session_dir.iterdir():
            if not project_path.is_dir():
                continue
            for session_file in project_path.glob("ses_*.json"):
                checked += 1
                if checked > 20:
                    break
                try:
                    import json

                    payload = json.loads(session_file.read_text(encoding="utf-8"))
                except Exception:
                    warnings.append(f"unreadable session file: {session_file.name}")
                    continue
                if isinstance(payload, dict):
                    version = payload.get("version")
                    if version is not None:
                        versions.add(str(version))
                if checked > 20:
                    break
            if checked > 20:
                break
        if len(versions) > 1:
            joined = ", ".join(sorted(versions))
            warnings.append(f"multiple session schema versions detected: {joined}")

    return warnings
