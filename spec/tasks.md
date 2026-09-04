# Tasks

Reverse-engineered record of the work performed to build v0.1.0, in the
order it happened. Every task is complete; this file exists for posterity,
not as a live plan. Each task cites the requirement/acceptance-criteria
subsections (from [`requirements.md`](requirements.md)) it implements or
verifies.

- [x] **Task 1: Clarify scope and implement project & session resolution in `core.py`**
  - Clarified open decisions with the user via a short question set: where
    the tool should live (a new global tools folder, not this repo or
    `~/.claude/`), whether to build and register the MCP server
    immediately, and how the CLI should be invoked (direct `python`
    invocation rather than a `PATH` shim)
  - Created the project directory at `~/source/repos/claude-session-export`
  - Verified the Python toolchain (`py -3 --version` → Python 3.12.0) and
    located the absolute path to `python.exe` for later use
  - Implemented `claude_projects_root()`, `project_slug_for_path()`
    (regex-replacing `\`, `/`, `:` with `-`), and `resolve_project_dir()`
    in `core.py`
  - Implemented the `SessionInfo` dataclass and `list_sessions()`
    (globbing `*.jsonl`, sorting most-recently-modified first) and
    `find_session()` (resolving `latest`, a numeric index, or an
    exact/unique-prefix session id, raising on ambiguous or missing
    matches)
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.1, 8.2, 8.4_

- [x] **Task 2: Implement transcript rendering and file export in `core.py`**
  - Implemented `_iter_jsonl()` and `_text_of()` helpers for reading a
    session's JSONL lines
  - Implemented `_block_to_text()`/`_content_to_text()` to render `text`,
    `thinking`, `tool_use`, `tool_result`, and `image` content blocks as
    labeled sections, and `render_session_text()` to assemble a full
    transcript, skipping non-`user`/`assistant` lines and empty turns
  - Set default truncation limits of 800 characters (`tool_use` input)
    and 1500 characters (`tool_result` content), each overridable via a
    `-1` "no limit" sentinel
  - Implemented `export_session()` to resolve a session, render it, and
    write it to a generated filename (from the session id) or a given
    file/directory path
  - _Requirements: 2.4, 3.8, 3.9, 3.10, 4.1, 4.2, 4.3, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] **Task 3: Build the CLI (`cli.py`)**
  - Implemented `argparse` subcommands `list-projects`, `list-sessions`,
    and `export` (with `--all`, `-o/--output`, `--full`, and a positional
    `session` token), each mapping directly onto the corresponding
    `core.py` function
  - Implemented `list-projects` output by iterating
    `claude_projects_root()` directly and counting each directory's
    `*.jsonl` files
  - Implemented the `--all` export path: iterate every session for the
    resolved project, create the output directory if needed, and print
    each file written
  - Added a top-level `try/except` in `main()` to catch
    `FileNotFoundError`/`IndexError`/`ValueError` from `core.py`, print
    `error: <message>` to stderr, and exit with status 1
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.1, 2.2, 2.4, 2.5, 2.6, 3.1, 3.8, 3.9, 3.10, 3.11, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] **Task 4: Smoke-test the CLI against real session data and fix a project-resolution bug**
  - Ran `list-sessions` from the `obsidian-icloud-windows-sync` project
    directory and got an unexpected "No sessions found"
  - Diagnosed the cause with a quick `python -c` reproduction of
    `resolve_project_dir(None)`: `root / project` in `pathlib` silently
    discards `root` whenever `project` is itself an absolute path, so the
    lookup was resolving to the raw working directory instead of the
    `~/.claude/projects` slug directory
  - Fixed `resolve_project_dir()` to only attempt a direct slug match
    when `project` contains no path separator or `:`, falling through to
    slug conversion otherwise
  - Re-ran `list-sessions`, `list-projects`, and `export latest -o <file>`
    against the real project data and confirmed correct results (both
    sessions listed with correct ids/timestamps/previews; export produced
    a non-empty, correctly formatted file)
  - _Requirements: 1.1, 2.1, 2.3, 2.4, 3.2, 3.8, 8.1, 8.2, 8.3_

- [x] **Task 5: Build the MCP server (`mcp_server.py`)**
  - Implemented `list_projects`, `list_project_sessions`, and
    `export_session_to_file` as `@mcp.tool()`-decorated functions over
    `core.py`, using `mcp.server.fastmcp.FastMCP`
  - Made `project` a required argument on `list_project_sessions` and
    `export_session_to_file` (no working-directory default), and
    documented in each docstring why the server can't infer a caller's
    project
  - Made `export_session_to_file` return `{output_path, size_bytes}`
    rather than the rendered transcript text inline
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] **Task 6: Install dependencies and verify the MCP server loads**
  - Added `requirements.txt` pinning `mcp>=1.0.0`
  - Ran `py -3 -m pip install -r requirements.txt` (already satisfied in
    the target environment)
  - Verified `mcp_server.py` imports cleanly and exposes the three
    expected tool functions via a quick `python -c "import mcp_server"`
    check
  - _Requirements: 7.1_

- [x] **Task 7: Register the MCP server with Claude Code**
  - Located the absolute path to `python.exe` (rather than the `py`
    launcher) for reliability when Claude Code spawns the server as a
    subprocess
  - Ran `claude mcp add --scope user claude-session-export -- <python.exe> <mcp_server.py>`
    to register the server at user scope (available to every project)
  - Verified the registration with `claude mcp list`, confirming the
    server shows as Connected
  - Removed the temporary export file created while smoke-testing the
    CLI in Task 4
  - _Requirements: 7.1_

- [x] **Task 8: Author project documentation and specs**
  - Wrote `README.md` (overview, install, CLI usage/examples, MCP
    registration and usage, project layout)
  - Wrote `CHANGE_LOG.md` (Keep a Changelog format, v0.1.0 entry
    including the Task 4 bug fix) and `RELEASE_NOTES.md` (narrative
    v0.1.0 notes and known limitations)
  - Wrote `spec/tech.md`, documenting the language, core-library and
    interface-layer dependencies, data source format, packaging state,
    and platform
  - Wrote `spec/design.md`, documenting the core/interface-layer
    architecture (with a Mermaid diagram) and the design decisions behind
    it, referencing `spec/tech.md`
  - Wrote `spec/requirements.md`, reverse-engineering the behavior built
    in Tasks 1-7 into 8 numbered requirements (user stories) with
    EARS-notation acceptance criteria, numbered as subsections (1.1,
    1.2, ... 8.4)
  - _Requirements: documents 1.1-8.4 in full; not itself an implementation of any acceptance criterion_

- [x] **Task 9: Initialize version control and commit**
  - Added `.gitignore` excluding `__pycache__/` and `*.pyc`
  - Ran `git init` in the project directory
  - Staged all project files and created the initial commit
    (`c121115`, "feat: initial claude-session-export tool (CLI + MCP
    server)")
  - _Requirements: none directly; a process/versioning task covering the artifacts from Tasks 1-8_
