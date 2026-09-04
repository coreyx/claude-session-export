# Release Notes

## v0.1.0 — 2026-09-04

Initial release.

### What this is

A small tool for turning Claude Code's on-disk session transcripts
(`~/.claude/projects/<slug>/*.jsonl`) into readable plain text — usable
either by hand from a terminal, or by a Claude Code session itself through
an MCP server.

It grew out of a one-off script written to answer a single request
("export my previous conversations in this project as text"); this release
turns that into a reusable, project-independent tool.

### What's included

- A CLI (`cli.py`) for listing projects and sessions, and exporting one
  session, or every session in a project, to text files.
- An MCP server (`mcp_server.py`) exposing the same operations as tools
  (`list_projects`, `list_project_sessions`, `export_session_to_file`),
  registered with Claude Code at user scope so it's available in any
  project.
- Exported transcripts render each turn as a labeled `USER`/`ASSISTANT`
  block with a timestamp, and render thinking, tool-call, and tool-result
  content as labeled sub-blocks; large tool inputs/outputs are truncated
  by default (`--full` to see everything).

### Known limitations

- The `~/.claude/projects/<slug>` naming scheme this tool relies on is
  reverse-engineered from observed directory names, not from published
  documentation, and could change in a future Claude Code release.
- Developed and tested on Windows 11 / PowerShell only. The code uses
  `pathlib`/`os.sep` rather than hardcoded separators, so it should run
  unmodified on macOS/Linux, but that hasn't been verified.
- No packaging yet — run directly with `py -3 cli.py ...`; there is no
  `claude-export` command on `PATH` and no PyPI/console-script install.
- The MCP server cannot infer a caller's working directory, so every MCP
  tool call must pass `project` explicitly.
