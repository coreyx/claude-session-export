"""CLI for listing and exporting Claude Code session transcripts.

Usage:
    python cli.py list-sessions [--project PATH_OR_SLUG]
    python cli.py list-projects
    python cli.py export <session> [--project PATH_OR_SLUG] [-o OUTPUT] [--full]
    python cli.py export --all [--project PATH_OR_SLUG] [-o OUTPUT_DIR]

<session> may be 'latest', a 1-based index from list-sessions, or a
full/partial session id.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core import (
    claude_projects_root,
    export_session,
    list_sessions,
)


def cmd_list_projects(args: argparse.Namespace) -> None:
    root = claude_projects_root()
    if not root.is_dir():
        print(f"No Claude projects directory found at {root}")
        return
    rows = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        n = len(list(d.glob("*.jsonl")))
        if n:
            rows.append((d.name, n))
    if not rows:
        print("No projects with sessions found.")
        return
    width = max(len(name) for name, _ in rows)
    for name, n in rows:
        print(f"{name.ljust(width)}  {n} session(s)")


def cmd_list_sessions(args: argparse.Namespace) -> None:
    sessions = list_sessions(args.project)
    if not sessions:
        print("No sessions found.")
        return
    for i, s in enumerate(sessions, start=1):
        preview = s.first_user_message.replace("\n", " ")[:80]
        started = s.started_at or "?"
        print(f"[{i}] {s.session_id}  {started}  ({s.message_count} msgs)")
        if preview:
            print(f"      {preview}")


def cmd_export(args: argparse.Namespace) -> None:
    output = Path(args.output) if args.output else None
    max_tool_input = -1 if args.full else 800
    max_tool_result = -1 if args.full else 1500

    if args.all:
        sessions = list_sessions(args.project)
        if not sessions:
            print("No sessions found.")
            return
        out_dir = output or Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)
        for s in sessions:
            out_path = export_session(
                s.session_id,
                project=args.project,
                output=out_dir,
                max_tool_input=max_tool_input,
                max_tool_result=max_tool_result,
            )
            print(f"Wrote {out_path}")
        return

    if not args.session:
        print("error: SESSION is required unless --all is given", file=sys.stderr)
        sys.exit(2)

    out_path = export_session(
        args.session,
        project=args.project,
        output=output,
        max_tool_input=max_tool_input,
        max_tool_result=max_tool_result,
    )
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Claude Code session transcripts to text.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list_projects = sub.add_parser("list-projects", help="List projects that have Claude Code sessions")
    p_list_projects.set_defaults(func=cmd_list_projects)

    p_list_sessions = sub.add_parser("list-sessions", help="List sessions for a project")
    p_list_sessions.add_argument("--project", default=None, help="Working-dir path or project slug (default: cwd)")
    p_list_sessions.set_defaults(func=cmd_list_sessions)

    p_export = sub.add_parser("export", help="Export one or all sessions to text")
    p_export.add_argument("session", nargs="?", default=None, help="'latest', an index, or a session id")
    p_export.add_argument("--all", action="store_true", help="Export every session for the project")
    p_export.add_argument("--project", default=None, help="Working-dir path or project slug (default: cwd)")
    p_export.add_argument("-o", "--output", default=None, help="Output file (single) or directory (--all)")
    p_export.add_argument("--full", action="store_true", help="Do not truncate tool inputs/outputs")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, IndexError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
