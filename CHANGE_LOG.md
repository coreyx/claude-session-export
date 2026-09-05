# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `scripts/install-shim.ps1`: optional installer that writes a
  `claude-export` shim (`claude-export.cmd` for cmd.exe/PowerShell,
  `claude-export` for POSIX shells) into `~/.local/bin`, hardcoded to
  invoke this clone's `cli.py` via the `py -3` launcher. Reuses a bin
  directory already commonly on `PATH` instead of adding a new,
  per-tool, per-clone `PATH` entry; never modifies `PATH` itself.

### Changed

- Replaced an earlier approach (a `bin/` directory inside the repo,
  added directly to the user's `PATH`) with the installer above, after
  reconsidering the per-tool `PATH` growth it implied.

## [0.1.0] - 2026-09-04

### Added

- `core.py`: resolve a Claude Code project directory from either a
  working-directory path or a project slug, list a project's sessions
  (most recently active first), and render a session transcript to
  readable plain text.
- `cli.py`: `list-projects`, `list-sessions`, and `export` (single session
  or `--all`) subcommands over `core.py`.
- `mcp_server.py`: MCP stdio server exposing `list_projects`,
  `list_project_sessions`, and `export_session_to_file` tools over the
  same core logic; registered with Claude Code at user scope.
- Default truncation of large `tool_use` inputs and `tool_result` content
  in rendered exports, with a `--full` / `full=True` opt-out.
- `spec/tech.md`, `spec/design.md`, `spec/requirements.md`,
  `README.md`, `RELEASE_NOTES.md`.

### Fixed

- Project resolution incorrectly used `root / project` for an absolute
  `project` path, which silently discarded the `~/.claude/projects` root
  (an absolute right-hand operand replaces the left side in `pathlib`
  joins) and resolved to the raw working directory instead of the
  project's slug directory. Fixed by only attempting a direct slug match
  when `project` has no path separators.
