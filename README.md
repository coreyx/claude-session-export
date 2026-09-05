# claude-session-export

Export Claude Code session transcripts to readable plain text — as a
standalone CLI, and as an MCP server so a Claude Code session can list and
export sessions (including its own history, or another project's) on your
behalf.

Claude Code stores every session as a JSONL file under
`~/.claude/projects/<slug>/`, where `<slug>` is the session's working
directory with `\`, `/`, and `:` replaced by `-`. This tool reads those
files directly and renders them as a readable transcript: one `--- USER ---`
/ `--- ASSISTANT ---` block per turn, with tool calls, tool results, and
thinking blocks rendered as labeled sections.

## Requirements

- Python 3.12+
- The `mcp` package (only required for the MCP server, not the CLI) — see
  `requirements.txt`

Install dependencies with:

```
py -3 -m pip install -r requirements.txt
```

## Installing the `claude-export` command (optional)

Rather than adding this repo to `PATH` directly, the installer drops a
shim into `~/.local/bin` — a directory many dev setups (including this
one) already keep on `PATH` — so adding this tool doesn't grow `PATH`
with another per-tool, per-clone entry:

```powershell
./scripts/install-shim.ps1
```

This writes `claude-export.cmd` (cmd.exe/PowerShell) and `claude-export`
(Git Bash/other POSIX shells) into `~/.local/bin`, each hardcoded to
invoke this clone's `cli.py`. It's safe to re-run (it overwrites any
existing shim there), and it never modifies `PATH` itself — if
`~/.local/bin` isn't already on your `PATH`, the script prints the exact
command to add it and stops short of running it for you. Once installed,
every example below also works as `claude-export <subcommand> ...`
instead of `py -3 cli.py <subcommand> ...`. This step is entirely
optional — the CLI works via `py -3 cli.py ...` with or without it.

## CLI usage

Run `cli.py` with the system Python (or `claude-export`, once installed
per above). All commands default to the project for your current working
directory unless `--project` is given.

```
py -3 cli.py list-projects
py -3 cli.py list-sessions [--project PATH_OR_SLUG]
py -3 cli.py export latest|<index>|<session-id> [-o OUTPUT] [--full]
py -3 cli.py export --all [--project PATH_OR_SLUG] [-o OUTPUT_DIR]
```

- `<session>` may be the literal `latest`, a 1-based index from
  `list-sessions` output, or a full or unambiguous partial session id.
- `--project` accepts either a working-directory path (e.g.
  `C:\Users\me\repo`) or an already-known project slug.
- `-o/--output` is a file path for a single export, or a directory for
  `--all`. If omitted, a filename is generated from the session id and
  written to the current directory.
- `--full` disables truncation of large tool inputs/outputs (see
  [spec/requirements.md](spec/requirements.md), requirement 4, for the
  default truncation behavior).

### Examples

```
py -3 cli.py list-sessions
py -3 cli.py export latest -o transcript.txt
py -3 cli.py export --all -o exports/
```

## MCP server usage

`mcp_server.py` exposes the same functionality as three MCP tools over
stdio: `list_projects`, `list_project_sessions`, `export_session_to_file`.

Register it with Claude Code (user scope, so it's available in every
project):

```
claude mcp add --scope user claude-session-export -- "<path to python.exe>" "<path to mcp_server.py>"
```

Use an absolute path to `python.exe` rather than the `py` launcher — it's
more reliable when Claude Code spawns the server as a subprocess.

Because the server runs as its own long-lived process, it has no way to
infer which project a given tool call is "for" — callers must always pass
`project` explicitly (their own working directory, or a slug from
`list_projects`).

## Project layout

- `core.py` — project/session resolution and transcript rendering (no I/O
  beyond reading transcripts and writing an export file)
- `cli.py` — argparse CLI over `core.py`
- `mcp_server.py` — FastMCP stdio server over `core.py`
- `scripts/install-shim.ps1` — optional installer that writes a
  `claude-export` shim (for cmd.exe/PowerShell and POSIX shells) into
  `~/.local/bin`
- `spec/tech.md`, `spec/design.md`, `spec/requirements.md` — tech stack,
  architecture, and requirements documentation

See [spec/design.md](spec/design.md) for the architecture and
[spec/requirements.md](spec/requirements.md) for the full requirements and
acceptance criteria.
