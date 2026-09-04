# Tech Stack

## Language & runtime

- **Python 3.12** (developed and tested against the Windows install at
  `C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe`,
  invoked either directly or via the `py -3` launcher).
- No minimum-version guard is enforced in code; 3.12 is what was used to
  build and test this project. The code has no syntax that requires a
  version newer than 3.10 (`X | None` unions, `list[T]` generics,
  dataclasses), so earlier 3.10+ interpreters would likely work but are
  untested.

## Core library (`core.py`)

Standard library only — deliberately kept dependency-free so the CLI can
run with nothing beyond a bare Python install:

- `json` — parsing each line of a session's `.jsonl` transcript, and
  encoding `tool_use` inputs back to text for rendering.
- `re` — converting a filesystem path into Claude Code's project slug
  (`[\\/:]` → `-`).
- `pathlib.Path` — all filesystem paths and traversal (`Path.home()`,
  `Path.glob`, `Path.stat`).
- `dataclasses.dataclass` — the `SessionInfo` record returned by
  `list_sessions`/`find_session`.
- `typing.Optional` — parameter typing (project targets 3.12, but avoids
  `X | None` in a couple of spots for readability with `Optional`).

## CLI (`cli.py`)

- `argparse` — subcommands (`list-projects`, `list-sessions`, `export`)
  and their flags, entirely standard library.
- `sys` — error output to stderr and process exit codes.

No third-party dependency is required to use the CLI; `requirements.txt`
only exists for the MCP server.

## MCP server (`mcp_server.py`)

- **`mcp`** (the official Model Context Protocol Python SDK), specifically
  `mcp.server.fastmcp.FastMCP` — decorator-based tool registration
  (`@mcp.tool()`) and the stdio server loop (`mcp.run()`).
- Transitive dependencies pulled in by `mcp` (not used directly by this
  project, but present in the environment): `pydantic`/`pydantic-settings`
  for schema validation of tool arguments, `starlette` + `uvicorn` +
  `sse-starlette` (HTTP/SSE transport support inside the SDK, unused here
  since this server runs over stdio), `httpx`, `anyio`.
- **Transport: stdio.** Claude Code spawns the server as a subprocess and
  talks to it over stdin/stdout; no network port is opened. This is the
  simplest transport for a purely local, single-user tool and matches how
  Claude Code registers stdio MCP servers via `claude mcp add`.

## Data source

- Claude Code's own session transcripts: newline-delimited JSON (JSONL)
  files at `~/.claude/projects/<slug>/*.jsonl`, one JSON object per line.
  Object `type`s observed include `user`, `assistant`, `queue-operation`,
  and `summary`; only `user` and `assistant` lines (each with a
  `message.content` of either a string or a list of content blocks —
  `text`, `thinking`, `tool_use`, `tool_result`, `image`) are rendered.
- This format and the `<slug>` naming scheme are reverse-engineered from
  observed files on disk, not from published Anthropic documentation —
  see the "Known limitations" section of `RELEASE_NOTES.md`.

## Packaging & distribution

- None yet. There is no `pyproject.toml`/`setup.py`, no virtual
  environment committed to the repo, and no console-script entry point.
  The CLI is invoked as `py -3 cli.py ...` from the repo directory; the
  MCP server is registered with an absolute path to `python.exe` and to
  `mcp_server.py` (see `README.md`).
- `requirements.txt` pins only `mcp>=1.0.0`; its transitive dependencies
  were already present in the target Python environment at the time this
  was built.

## Platform

- Developed and tested on **Windows 11 / PowerShell**. All path handling
  goes through `pathlib`/`os.sep` rather than hardcoded `\` or `/`
  separators, so the CLI and core logic are expected to run unmodified on
  macOS/Linux — this has not been verified.

## Version control

- **git**, initialized for this project alongside this documentation.
