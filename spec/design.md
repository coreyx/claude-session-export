# Architecture

See [`tech.md`](tech.md) for the technology choices referenced below.

## Overview

The project is a thin, two-interface shell around a single dependency-free
core library. All domain logic — finding a project, listing its sessions,
and rendering a transcript to text — lives in `core.py`; `cli.py` and
`mcp_server.py` are both stateless adapters that call into it and format
its results for their respective audience (a terminal user, or an MCP
client such as a Claude Code session).

```mermaid
flowchart LR
    subgraph fs [Data source]
        FS["~/.claude/projects/&lt;slug&gt;/*.jsonl
        (Claude Code session transcripts)"]
    end

    subgraph lib [Core library]
        Core["core.py
        project resolution
        session listing
        transcript rendering"]
    end

    subgraph iface [Interfaces]
        CLI["cli.py
        argparse CLI"]
        MCP["mcp_server.py
        FastMCP stdio server"]
    end

    subgraph consumers [Consumers]
        User["Terminal user"]
        Agent["Claude Code session
        (MCP tool calls)"]
    end

    FS --> Core
    Core --> CLI
    Core --> MCP
    CLI --> User
    MCP --> Agent
```

## Core library (`core.py`)

Four responsibilities, each a small pure function or generator over the
filesystem — no interface-specific concerns (argument parsing, tool
schemas, error formatting) leak into this module:

1. **Project resolution** — `project_slug_for_path()` reproduces Claude
   Code's slug algorithm (`[\\/:]` → `-`); `resolve_project_dir()` accepts
   either a raw slug or a working-directory path and returns the matching
   directory under `~/.claude/projects`. A literal-slug match is only
   attempted when the input has no path separators, specifically to avoid
   `pathlib`'s "an absolute right-hand path replaces the left side" join
   behavior silently defeating the lookup (see `CHANGE_LOG.md`, Fixed).

2. **Session discovery** — `list_sessions()` globs a project directory for
   `*.jsonl`, scanning each file just far enough to collect a
   `SessionInfo` (id, start timestamp, message count, first user message,
   mtime) without holding the whole transcript in memory, then sorts by
   mtime descending. `find_session()` layers token resolution on top —
   `latest`, a 1-based index into that same ordering, or an exact/partial
   session-id match (raising on zero or multiple matches rather than
   guessing).

3. **Transcript rendering** — `render_session_text()` walks a transcript
   line by line, keeps only `user`/`assistant` entries, and turns each
   content block into a labeled section (`_block_to_text`): plain text
   passes through, `thinking`/`tool_use`/`tool_result`/`image` blocks get
   a `[label]` prefix, and `tool_use`/`tool_result` payloads are
   length-truncated by default. Turns that render to empty text (after
   truncation/formatting) are dropped rather than emitted as empty
   sections.

4. **Export** — `export_session()` composes the three functions above and
   writes the result to disk, generating a filename from the session id
   when the caller passes no output path or a directory.

Everything above raises plain stdlib exceptions
(`FileNotFoundError`/`IndexError`/`ValueError`) on failure; neither
interface layer wraps these in custom exception types, they just decide
how to present them.

## CLI (`cli.py`)

A conventional `argparse` subcommand tree (`list-projects`,
`list-sessions`, `export`) that maps flags directly onto `core.py`
parameters (`--project`, `-o/--output`, `--full`). The one piece of
interface-specific logic is the top-level `try/except` in `main()`, which
catches the core library's exceptions, prints `error: <message>` to
stderr, and exits `1` — everything else is a direct call-through.

## MCP server (`mcp_server.py`)

Uses `FastMCP` to declare three tools as thin wrappers:
`list_projects`, `list_project_sessions`, `export_session_to_file`. Two
design points follow directly from how MCP servers run, not from any
property of `core.py`:

- **`project` is a required argument on every tool**, not optional. The
  server is a long-lived subprocess with its own working directory, which
  has no relationship to the working directory of whatever Claude Code
  session is calling it — so unlike the CLI (where "default to `cwd`" is
  meaningful because the CLI *is* invoked from the relevant directory),
  the MCP layer cannot safely default `project` and instead documents in
  each tool's docstring that callers must pass their own working
  directory or a known slug.
- **`export_session_to_file` returns a path and size, not the transcript
  text.** Session transcripts can run to many megabytes; returning that
  inline as a tool result would flood the calling session's context for
  no benefit over just reading the file it already wrote.

Errors surface as whatever `FastMCP` does by default with an uncaught
Python exception from a tool function (an MCP tool-call error result) —
there is no bespoke error handling in this layer, mirroring the "let
`core.py`'s exceptions speak for themselves" approach used in the CLI.

## Why one core, two interfaces

The CLI and MCP server serve different callers with different framing
needs (human-readable list output vs. structured dicts; stderr+exit-code
errors vs. MCP error results; implicit cwd default vs. mandatory
`project`), but the underlying operations — resolve a project, list its
sessions, render one to text — are identical. Keeping that logic in
`core.py` and importing it from both interfaces means a change to, say,
the slug algorithm or the truncation limits, only has to happen once.
