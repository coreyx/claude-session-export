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
stdio, so a Claude Code session can list and export sessions (its own, or
another project's) on your behalf instead of you running the CLI by hand:

| Tool | Purpose |
|---|---|
| `list_projects` | List every project on this machine that has session transcripts |
| `list_project_sessions` | List a project's sessions, most recent first |
| `export_session_to_file` | Render one session to a `.txt` file and return its path |

### 1. Install and register the server

```powershell
./scripts/install-mcp-server.ps1
```

This resolves the `python.exe` behind your `py -3` launcher, installs the
`mcp` package for it, and runs `claude mcp add --scope user` pointing at
this clone's `mcp_server.py` — the three manual steps below, done for
you. It's safe to re-run any time (e.g. after moving the repo or
reinstalling Python): if the server is already registered, it removes
and re-adds it so its paths stay current. It ends by printing
`claude mcp get claude-session-export` so you can see the result — look
for `Status: ✔ Connected`.

<details>
<summary>Doing it by hand instead</summary>

```powershell
# 1. Install the server's dependency
py -3 -m pip install -r requirements.txt

# 2. Find the absolute path to your python.exe (registration needs an
#    absolute path, not the `py` launcher -- see spec/tech.md for why)
(Get-Command python).Source        # PowerShell
which python                       # bash

# 3. Register the server (user scope: available in every project)
claude mcp add --scope user claude-session-export -- "<path from step 2>" "<absolute path to mcp_server.py>"
```

For example, on a machine where step 2 printed
`C:\Users\me\AppData\Local\Programs\Python\Python312\python.exe` and this
repo is cloned to `C:\Users\me\source\repos\claude-session-export`:

```
claude mcp add --scope user claude-session-export -- "C:\Users\me\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\me\source\repos\claude-session-export\mcp_server.py"
```

</details>

### 2. Verify it's connected

```
claude mcp list
```

should include a line like:

```
claude-session-export: C:\...\python.exe C:\...\mcp_server.py - ✔ Connected
```

If it instead shows a failure, run `claude mcp get claude-session-export`
for details, or re-run `./scripts/install-mcp-server.ps1` and read its
output — whatever error it prints (e.g. from `pip install` or
`claude mcp add`) is what Claude Code is hitting.

### 3. Start a new Claude Code session

A session only loads its MCP tools at startup, so a session that was
already running before you registered the server won't see it — start a
new one (or restart the current one).

### 4. Use it

Once registered, just ask in plain language and Claude will call the
tools itself, e.g.:

- "What Claude Code sessions exist for this project?"
- "Export my last session in this repo to a text file."
- "Export every session for `C:\Users\me\other-project` to `exports/`."

Because the server is a separate long-lived process, it has no way to
infer which project a given tool call is "for" — every call needs an
explicit `project` (a working-directory path, or a `project_slug` from
`list_projects`). A Claude Code session calling these tools about itself
passes its own working directory automatically; you don't need to supply
it yourself when asking in chat.

If you want to see the raw tool calls rather than just asking in chat,
they look like this:

```
list_project_sessions(project="C:\Users\me\my-repo")
→ [
    {"index": 1, "session_id": "9f1c2a...", "started_at": "2026-09-04T16:52:41Z",
     "message_count": 63, "first_user_message": "Can you help me..."},
    {"index": 2, "session_id": "02eb73...", "started_at": "2026-09-02T06:17:31Z",
     "message_count": 2343, "first_user_message": "I believe there is a bug..."}
  ]

export_session_to_file(session="1", project="C:\Users\me\my-repo", output_path="C:\Users\me\my-repo\transcript.txt")
→ {"output_path": "C:\\Users\\me\\my-repo\\transcript.txt", "size_bytes": 21694}
```

The transcript text itself is never returned inline (sessions can run to
many megabytes) — read the file at `output_path` if you need its content.

### Updating or removing the server

If the repo moves, or you reinstall Python at a different path, just
re-run `./scripts/install-mcp-server.ps1` — it removes and re-adds the
registration with current paths. To remove it entirely instead:

```
claude mcp remove claude-session-export
```

### Troubleshooting

- **Tools don't show up in a session.** MCP tools load at session start
  — start a new session or restart the current one (step 3).
- **`claude mcp list` shows a failure, or the install script errors.**
  The script's output shows exactly which step failed (`pip install` or
  `claude mcp add`) and the real error — usually a wrong/missing Python
  install, or the `claude` CLI not being on `PATH`.
- **A tool call fails with a `FileNotFoundError` about the project.**
  The `project` argument didn't resolve to a real
  `~/.claude/projects/<slug>` directory. Double check the working
  directory you passed, or call `list_projects` first to get an exact
  `project_slug`.

## Project layout

- `core.py` — project/session resolution and transcript rendering (no I/O
  beyond reading transcripts and writing an export file)
- `cli.py` — argparse CLI over `core.py`
- `mcp_server.py` — FastMCP stdio server over `core.py`
- `scripts/install-shim.ps1` — optional installer that writes a
  `claude-export` shim (for cmd.exe/PowerShell and POSIX shells) into
  `~/.local/bin`
- `scripts/install-mcp-server.ps1` — installs the `mcp` dependency and
  registers `mcp_server.py` with Claude Code
- `spec/tech.md`, `spec/design.md`, `spec/requirements.md` — tech stack,
  architecture, and requirements documentation

See [spec/design.md](spec/design.md) for the architecture and
[spec/requirements.md](spec/requirements.md) for the full requirements and
acceptance criteria.
