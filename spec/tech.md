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

- No formal Python packaging yet — there is no `pyproject.toml`/
  `setup.py`, no virtual environment committed to the repo, and no
  `pip`-installed console-script entry point.
- The installer scripts below are described in their Windows/PowerShell
  form; see the "Platform" section for the parallel `.sh` scripts that
  provide the same behavior on macOS/Linux.
- `scripts/install-shim.ps1` is an optional installer, not a packaging
  mechanism: it writes `claude-export.cmd` (cmd.exe/PowerShell) and
  `claude-export` (POSIX shells, e.g. Git Bash) into `~/.local/bin` —
  chosen over adding this repo's own directory to `PATH` because
  `~/.local/bin` is a directory many dev setups (this one included)
  already keep on `PATH`, so installing this tool costs zero new `PATH`
  entries rather than one per tool/clone. The tradeoff: unlike a shim
  living inside the repo, these hardcode an absolute path to this
  clone's `cli.py` at install time and need re-running if the repo
  moves. Both shims invoke `cli.py` via the `py -3` launcher — used here
  (rather than an absolute `python.exe` path, as the MCP registration
  uses) because these run interactively from a real shell, where `py`
  reliably resolves to the right interpreter, unlike the MCP server,
  which Claude Code spawns directly as a subprocess. The installer marks
  the POSIX shim executable via Git for Windows' own `bash.exe` (found
  by checking `Program Files\Git\bin` directly rather than trusting
  `bash` on `PATH`, which on Windows commonly resolves to a WSL launcher
  stub in `System32` instead).
- The MCP server is registered with an absolute path to `python.exe` and
  to `mcp_server.py` (see `README.md`), independent of the shims above.
- `scripts/install-mcp-server.ps1` automates that registration: it
  resolves the `python.exe` behind `py -3` via
  `python -c "import sys; print(sys.executable)"` (rather than
  `Get-Command python`, which can resolve to a different interpreter
  than the one `py -3` would pick), installs `mcp` for it, and calls
  `claude mcp add --scope user`. It shells out to the `claude` CLI
  itself (`claude mcp get`/`remove`/`add`) rather than editing
  `~/.claude.json` directly, so it stays correct across whatever
  internal format that file uses. It is idempotent: `claude mcp add`
  errors if a server with the same name is already registered, so the
  script checks with `claude mcp get` first and removes any existing
  registration before re-adding.
- `requirements.txt` pins only `mcp>=1.0.0`; its transitive dependencies
  were already present in the target Python environment at the time this
  was built.

## Platform

- **Windows, macOS, and Linux are all supported.** `core.py`, `cli.py`,
  and `mcp_server.py` are pure `pathlib`/`os`-based Python with no
  platform-specific branches, and are the same code on every OS.
- Development and testing happened on **Windows 11 / PowerShell**, with
  the macOS/Linux path exercised through the `.sh` installer scripts
  (see below) — the underlying Python has not been run on an actual
  macOS/Linux machine, only reasoned about and partially simulated (a
  wrapper interpreter standing in for `python3`) on Windows.
- Only the two optional installer scripts differ per platform, because
  installers are inherently about OS-specific concerns (finding the
  right interpreter, registering a shim in a shell-specific way):
  `scripts/install-shim.ps1` / `scripts/install-mcp-server.ps1` for
  Windows (PowerShell), and `scripts/install-shim.sh` /
  `scripts/install-mcp-server.sh` for macOS/Linux (POSIX shell). Each
  pair implements the same behavior for its platform's idioms: `py -3`
  vs. `python3` as the interpreter; `$PSScriptRoot`-based vs.
  `BASH_SOURCE`-based self-location (used by the installer scripts to
  find the repo root relative to themselves, not by the shims they
  generate, which hardcode an absolute path); and a `.cmd` plus a POSIX
  shim vs. a POSIX shim only.

## Version control

- **git**, initialized for this project alongside this documentation.
