# Requirements

These requirements were reverse-engineered from the current implementation
(`core.py`, `cli.py`, `mcp_server.py`) as of v0.1.0. Acceptance criteria are
written in EARS notation (WHEN/THEN, IF/THEN).

## 1. List projects with session history

**User story:** As a user, I want to list which projects on this machine
have Claude Code session transcripts, so that I can find the right
project before listing or exporting its sessions.

- **1.1** WHEN the user runs `list-projects` THEN the system SHALL list
  every directory directly under `~/.claude/projects` that contains at
  least one `*.jsonl` file.
- **1.2** WHEN a directory under `~/.claude/projects` contains no
  `*.jsonl` files THEN the system SHALL exclude it from the listing.
- **1.3** WHEN a project is listed THEN the system SHALL show its slug
  name and the count of session files found for it.
- **1.4** IF `~/.claude/projects` does not exist THEN the system SHALL
  report that no projects directory was found rather than raising an
  unhandled error.
- **1.5** IF no project directories contain sessions THEN the system
  SHALL report that no projects were found.

## 2. List sessions within a project

**User story:** As a user, I want to list the sessions within a project,
most recently active first, with an id, timestamp, and preview, so that I
can identify which session to export without opening the raw JSONL files.

- **2.1** WHEN the user runs `list-sessions` without `--project` THEN the
  system SHALL resolve the project from the current working directory.
- **2.2** WHEN the user runs `list-sessions --project <value>` THEN the
  system SHALL resolve `<value>` as either a project slug or a
  working-directory path (see Requirement 8).
- **2.3** WHEN sessions are listed THEN the system SHALL order them by
  file last-modified time, most recent first.
- **2.4** WHEN a session is listed THEN the system SHALL display, at
  minimum, its session id, its earliest available message timestamp, its
  message count, and up to 80 characters of its first user message.
- **2.5** IF the resolved project has no session files THEN the system
  SHALL report that no sessions were found rather than raising an error.
- **2.6** IF the given `--project` value does not resolve to an existing
  project directory (directly or via slug conversion) THEN the system
  SHALL raise an error identifying the value that could not be resolved.

## 3. Export a single session to text

**User story:** As a user, I want to export one session to a readable
text file by id, index, or "latest", so that I can review, archive, or
share a past conversation outside of Claude Code.

- **3.1** WHEN the user runs `export <session>` THEN the system SHALL
  accept `<session>` as the literal token `latest`, a 1-based index, or a
  full or partial session id.
- **3.2** WHEN `<session>` is `latest` THEN the system SHALL select the
  most recently modified session for the resolved project.
- **3.3** WHEN `<session>` is numeric THEN the system SHALL treat it as a
  1-based index into the most-recent-first session ordering defined in
  Requirement 2.3.
- **3.4** IF a numeric `<session>` index is outside the range of
  available sessions THEN the system SHALL raise an "out of range" error.
- **3.5** WHEN `<session>` exactly matches one session id, or uniquely
  prefix-matches exactly one session id, THEN the system SHALL export
  that session.
- **3.6** IF `<session>` prefix-matches more than one session id THEN the
  system SHALL raise an error listing the ambiguous matches instead of
  selecting one.
- **3.7** IF `<session>` matches no session id THEN the system SHALL
  raise a "not found" error.
- **3.8** WHEN no `-o/--output` is given THEN the system SHALL write the
  export to a filename generated from the session id in the current
  working directory.
- **3.9** WHEN `-o/--output` names an existing directory THEN the system
  SHALL write the export to a generated filename inside that directory.
- **3.10** WHEN `-o/--output` names a non-directory path THEN the system
  SHALL write the export to exactly that path, overwriting it if it
  already exists.
- **3.11** WHEN a session export completes THEN the system SHALL print
  the path that was written.

## 4. Truncate large tool content by default

**User story:** As a user, I want long tool inputs and outputs truncated
by default when exporting, so that exported transcripts stay readable,
while retaining the option to see everything.

- **4.1** WHEN a `tool_use` block's JSON-encoded input exceeds 800
  characters and `--full` was not given THEN the system SHALL truncate it
  to 800 characters and append a truncation marker.
- **4.2** WHEN a `tool_result` block's content exceeds 1500 characters and
  `--full` was not given THEN the system SHALL truncate it to 1500
  characters and append a truncation marker.
- **4.3** WHEN `--full` is given (CLI) or `full=True` is passed (MCP)
  THEN the system SHALL NOT truncate `tool_use` or `tool_result` content.

## 5. Export every session in a project

**User story:** As a user, I want to export every session in a project at
once, so that I can archive a project's full conversation history in a
single command.

- **5.1** WHEN the user runs `export --all` THEN the system SHALL export
  every session found for the resolved project (per Requirement 2).
- **5.2** WHEN `export --all` runs without `-o/--output` THEN the system
  SHALL write each session's export into the current working directory.
- **5.3** WHEN `export --all` runs with `-o/--output <dir>` THEN the
  system SHALL create `<dir>` if it does not already exist and write each
  session's export inside it.
- **5.4** WHEN each individual session finishes exporting under
  `--all` THEN the system SHALL print the path written for that session.
- **5.5** IF the resolved project has no sessions THEN `export --all`
  SHALL report that no sessions were found and SHALL NOT create an output
  directory.

## 6. Render a transcript as self-explanatory text

**User story:** As someone reading an exported transcript, I want each
turn labeled with its role and timestamp, and non-text content rendered
as labeled blocks, so that the exported text is understandable without
referring back to the original JSON.

- **6.1** WHEN a transcript line has `type` `user` or `assistant` and
  contains a non-empty rendered message THEN the system SHALL render it
  as a labeled turn (`--- USER ---` or `--- ASSISTANT ---`), including its
  ISO-8601 timestamp when the line provides one.
- **6.2** WHEN a transcript line has any `type` other than `user` or
  `assistant` (e.g. `queue-operation`, `summary`) THEN the system SHALL
  exclude it from the rendered output.
- **6.3** IF a message turn renders to empty or whitespace-only text
  after block formatting and truncation THEN the system SHALL omit that
  turn from the output entirely.
- **6.4** WHEN a content block has `type` `thinking` THEN the system
  SHALL render it prefixed with `[thinking]`.
- **6.5** WHEN a content block has `type` `tool_use` THEN the system
  SHALL render it prefixed with `[tool_use: <tool name>]` followed by its
  JSON-encoded input (subject to Requirement 4.1).
- **6.6** WHEN a content block has `type` `tool_result` THEN the system
  SHALL render it prefixed with `[tool_result]` followed by its content
  (subject to Requirement 4.2), flattening list-of-block content into
  plain text first.
- **6.7** WHEN a content block has `type` `image` THEN the system SHALL
  render it as the literal placeholder `[image]`.
- **6.8** WHEN a content block has any other `type` THEN the system SHALL
  render it as `[<type>]`.

## 7. Expose the same operations as MCP tools

**User story:** As a Claude Code session, I want to list and export
Claude Code sessions (my own project's or another project's) through MCP
tools, so that I can act on session history on the user's behalf without
shelling out to the CLI.

- **7.1** WHEN the MCP server (`mcp_server.py`) is started THEN the
  system SHALL expose exactly three tools: `list_projects`,
  `list_project_sessions`, and `export_session_to_file`.
- **7.2** WHEN `list_projects` is called THEN the system SHALL return the
  same project/session-count information as Requirement 1, as structured
  data rather than printed text.
- **7.3** WHEN `list_project_sessions` is called with a `project`
  argument THEN the system SHALL return the same session listing as
  Requirement 2, as structured data including a 1-based `index` per
  session (usable as the `session` argument to `export_session_to_file`).
- **7.4** THE `list_project_sessions` and `export_session_to_file` tools
  SHALL require an explicit `project` argument and SHALL NOT default it
  to the MCP server process's own working directory, since that directory
  has no relationship to the calling session's project.
- **7.5** WHEN `export_session_to_file` is called THEN the system SHALL
  write the rendered transcript to `output_path` and SHALL return that
  path together with the resulting file's size in bytes, rather than
  returning the transcript content inline in the tool result.

## 8. Resolve a project from either a path or a slug

**User story:** As a caller of this tool (a user or an MCP client), I
want to identify a project by either its working-directory path or its
already-known Claude Code slug, so that I don't need to know or compute
the slug format myself.

- **8.1** WHEN a `project` value contains no path-separator character
  (`\`, `/`) and no `:` THEN the system SHALL first check whether it
  matches a directory name directly under `~/.claude/projects`.
- **8.2** WHEN a `project` value is a filesystem path THEN the system
  SHALL derive its slug by replacing every `\`, `/`, and `:` character
  with `-`, and SHALL resolve against the resulting directory name under
  `~/.claude/projects`.
- **8.3** IF neither the literal `project` value nor its derived slug
  matches an existing directory under `~/.claude/projects` THEN the
  system SHALL raise a `FileNotFoundError` naming both paths that were
  attempted.
- **8.4** WHEN no `project` value is given to a CLI command THEN the
  system SHALL use the current working directory as the `project` value.
