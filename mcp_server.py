"""MCP server exposing Claude Code session listing/export as tools.

Run directly (stdio transport), or register it with Claude Code via
scripts/install-mcp-server.ps1 (Windows) or scripts/install-mcp-server.sh
(macOS/Linux) -- see README.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from core import claude_projects_root, export_session, list_sessions

mcp = FastMCP("claude-session-export")


@mcp.tool()
def list_projects() -> list[dict]:
    """List Claude Code projects on this machine that have session transcripts.

    Each entry's "project_slug" identifies the project and doubles as the
    `project` argument to the other tools here."""
    root = claude_projects_root()
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir():
            n = len(list(d.glob("*.jsonl")))
            if n:
                out.append({"project_slug": d.name, "session_count": n})
    return out


@mcp.tool()
def list_project_sessions(project: str) -> list[dict]:
    """List sessions for a project, most recently active first.

    `project` is a working-directory path (e.g. "C:\\Users\\me\\repo") or a
    project_slug from list_projects. Callers should pass their own current
    working directory when listing their own project's sessions, since this
    server has no way to infer it."""
    sessions = list_sessions(project)
    return [
        {
            "index": i + 1,
            "session_id": s.session_id,
            "started_at": s.started_at,
            "message_count": s.message_count,
            "first_user_message": s.first_user_message[:200],
        }
        for i, s in enumerate(sessions)
    ]


@mcp.tool()
def export_session_to_file(
    session: str,
    output_path: str,
    project: str,
    full: bool = False,
) -> dict:
    """Export one Claude Code session transcript to a readable .txt file.

    session: 'latest', a 1-based index from list_project_sessions, or a
        full/partial session id.
    output_path: absolute path to write the .txt file to (or a directory).
    project: working-directory path or project_slug (see list_projects).
    full: if true, do not truncate large tool inputs/outputs.

    Returns the path written to and its size; the transcript content is
    NOT returned inline since sessions can be many megabytes -- read the
    file if you need its content.
    """
    max_len = -1 if full else 800
    max_result_len = -1 if full else 1500
    out = export_session(
        session,
        project=project,
        output=Path(output_path),
        max_tool_input=max_len,
        max_tool_result=max_result_len,
    )
    return {"output_path": str(out), "size_bytes": out.stat().st_size}


if __name__ == "__main__":
    mcp.run()
