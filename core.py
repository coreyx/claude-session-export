"""Core logic for listing and exporting Claude Code session transcripts.

Claude Code stores each project's sessions as JSONL files under
``~/.claude/projects/<slug>/``, where ``<slug>`` is the project's working
directory with path separators and ``:`` replaced by ``-`` (e.g.
``C:\\Users\\me\\repo`` becomes ``C--Users-me-repo``). This module reads
those transcripts and renders them as plain, readable text.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def claude_projects_root() -> Path:
    return Path.home() / ".claude" / "projects"


def project_slug_for_path(cwd: str) -> str:
    """Convert an absolute filesystem path into the slug Claude Code uses
    for its per-project session directory."""
    return re.sub(r"[\\/:]", "-", str(cwd))


def resolve_project_dir(project: Optional[str]) -> Path:
    """Resolve a project argument to a directory under ~/.claude/projects.

    ``project`` may be:
      - None: use the current working directory
      - a working-directory path (converted to its slug)
      - a project slug that already matches a directory name
    """
    import os

    root = claude_projects_root()
    if project is None:
        project = os.getcwd()

    # Only treat `project` as a literal slug (a single path component under
    # root) when it has no path separators -- `root / project` silently
    # discards `root` if `project` is itself an absolute path.
    if os.sep not in project and (os.altsep is None or os.altsep not in project) and ":" not in project:
        candidate = root / project
        if candidate.is_dir():
            return candidate

    slug = project_slug_for_path(project)
    candidate = root / slug
    if candidate.is_dir():
        return candidate

    raise FileNotFoundError(
        f"No Claude project directory found for {project!r} "
        f"(looked for {root / project} and {candidate})"
    )


@dataclass
class SessionInfo:
    session_id: str
    path: Path
    started_at: Optional[str]
    last_modified: float
    message_count: int
    first_user_message: str


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text"):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def list_sessions(project: Optional[str] = None) -> list[SessionInfo]:
    """List sessions for a project, most recently modified first."""
    project_dir = resolve_project_dir(project)
    sessions = []
    for jsonl_path in project_dir.glob("*.jsonl"):
        started_at = None
        first_user_message = ""
        message_count = 0
        for obj in _iter_jsonl(jsonl_path):
            if obj.get("type") not in ("user", "assistant"):
                continue
            message_count += 1
            ts = obj.get("timestamp")
            if started_at is None and ts:
                started_at = ts
            if not first_user_message and obj.get("type") == "user":
                text = _text_of(obj.get("message", {}).get("content"))
                if text.strip():
                    first_user_message = text.strip()
        sessions.append(
            SessionInfo(
                session_id=jsonl_path.stem,
                path=jsonl_path,
                started_at=started_at,
                last_modified=jsonl_path.stat().st_mtime,
                message_count=message_count,
                first_user_message=first_user_message,
            )
        )
    sessions.sort(key=lambda s: s.last_modified, reverse=True)
    return sessions


def find_session(token: str, project: Optional[str] = None) -> SessionInfo:
    """Resolve a session token to a SessionInfo.

    ``token`` may be 'latest', a 1-based index into list_sessions() output,
    or a full/partial session id.
    """
    sessions = list_sessions(project)
    if not sessions:
        raise FileNotFoundError("No sessions found for that project")

    if token == "latest":
        return sessions[0]

    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(sessions):
            return sessions[idx]
        raise IndexError(f"Session index {token} out of range (1-{len(sessions)})")

    matches = [s for s in sessions if s.session_id == token]
    if not matches:
        matches = [s for s in sessions if s.session_id.startswith(token)]
    if not matches:
        raise FileNotFoundError(f"No session matching {token!r}")
    if len(matches) > 1:
        ids = ", ".join(m.session_id for m in matches)
        raise ValueError(f"Ambiguous session id {token!r}, matches: {ids}")
    return matches[0]


def _block_to_text(block: dict, max_tool_input: int, max_tool_result: int) -> str:
    btype = block.get("type")
    if btype == "text":
        return block.get("text", "")
    if btype == "thinking":
        return f"[thinking]\n{block.get('thinking', '')}"
    if btype == "tool_use":
        try:
            payload = json.dumps(block.get("input"))
        except (TypeError, ValueError):
            payload = str(block.get("input"))
        if max_tool_input >= 0 and len(payload) > max_tool_input:
            payload = payload[:max_tool_input] + "... [truncated]"
        return f"[tool_use: {block.get('name')}]\n{payload}"
    if btype == "tool_result":
        content = block.get("content")
        if isinstance(content, list):
            content = "\n".join(
                c.get("text", f"[{c.get('type')}]") if isinstance(c, dict) else str(c)
                for c in content
            )
        if not isinstance(content, str):
            content = json.dumps(content)
        if max_tool_result >= 0 and len(content) > max_tool_result:
            content = content[:max_tool_result] + "... [truncated]"
        return f"[tool_result]\n{content}"
    if btype == "image":
        return "[image]"
    return f"[{btype}]"


def _content_to_text(content, max_tool_input: int, max_tool_result: int) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [_block_to_text(b, max_tool_input, max_tool_result) for b in content if isinstance(b, dict)]
        return "\n\n".join(p for p in parts if p)
    return ""


def render_session_text(
    session: SessionInfo,
    max_tool_input: int = 800,
    max_tool_result: int = 1500,
) -> str:
    """Render a session transcript as readable plain text."""
    out = [
        "Claude Code session export",
        f"Session: {session.session_id}",
        f"Source:  {session.path}",
        "=" * 75,
        "",
    ]
    for obj in _iter_jsonl(session.path):
        otype = obj.get("type")
        if otype not in ("user", "assistant"):
            continue
        message = obj.get("message")
        if not message:
            continue
        text = _content_to_text(message.get("content"), max_tool_input, max_tool_result)
        if not text.strip():
            continue
        ts = obj.get("timestamp", "")
        label = "USER" if otype == "user" else "ASSISTANT"
        out.append(f"--- {label}{' (' + ts + ')' if ts else ''} ---")
        out.append(text.strip())
        out.append("")
    return "\n".join(out)


def export_session(
    token: str,
    project: Optional[str] = None,
    output: Optional[Path] = None,
    max_tool_input: int = 800,
    max_tool_result: int = 1500,
) -> Path:
    """Resolve, render, and write a session transcript to a text file.

    Returns the path written to. If ``output`` is a directory (or None),
    a filename is generated from the session id.
    """
    session = find_session(token, project)
    text = render_session_text(session, max_tool_input, max_tool_result)

    if output is None:
        output = Path.cwd() / f"conversation-{session.session_id[:8]}.txt"
    elif output.is_dir():
        output = output / f"conversation-{session.session_id[:8]}.txt"

    output.write_text(text, encoding="utf-8")
    return output
