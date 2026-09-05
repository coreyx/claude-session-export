#!/usr/bin/env bash
# Installs and registers the claude-session-export MCP server with
# Claude Code (macOS/Linux).
#
# Resolves the python3 interpreter's absolute path, installs the `mcp`
# package for it, then runs `claude mcp add --scope user` pointing at
# this clone's mcp_server.py using that absolute path (an absolute path
# is required for reliable subprocess spawning -- see spec/tech.md).
# Safe to re-run: if the server is already registered, it's removed and
# re-added so its paths stay current (e.g. after moving the repo or
# reinstalling Python).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_PATH="$REPO_ROOT/mcp_server.py"
REQUIREMENTS_PATH="$REPO_ROOT/requirements.txt"

if [ ! -f "$SERVER_PATH" ]; then
    echo "error: could not find mcp_server.py at $SERVER_PATH -- run this script from its original location inside the repo." >&2
    exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
    echo "error: the 'claude' CLI was not found on PATH. Install Claude Code first, then re-run this script." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 was not found on PATH. Install Python 3.12+, then re-run this script." >&2
    exit 1
fi

echo "Resolving the python3 interpreter..."
PYTHON_EXE="$(python3 -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
if [ -z "$PYTHON_EXE" ] || [ ! -x "$PYTHON_EXE" ]; then
    echo "error: could not resolve a working python3 interpreter via 'python3 -c ...'." >&2
    echo "  Make sure 'python3' on PATH is a real Python 3.12+ install, then re-run this script." >&2
    exit 1
fi
echo "  $PYTHON_EXE"

echo "Installing the 'mcp' package for that interpreter..."
if ! "$PYTHON_EXE" -m pip install -r "$REQUIREMENTS_PATH"; then
    echo "error: pip install failed. If it mentions an 'externally managed environment'," >&2
    echo "  retry with: \"$PYTHON_EXE\" -m pip install --user -r \"$REQUIREMENTS_PATH\"" >&2
    echo "  or install into a virtualenv and point this script's PYTHON_EXE at it instead." >&2
    exit 1
fi

SERVER_NAME="claude-session-export"
if claude mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    echo "'$SERVER_NAME' is already registered -- removing it so it can be re-added with current paths..."
    claude mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
fi

echo "Registering '$SERVER_NAME' with Claude Code (user scope, available in every project)..."
claude mcp add --scope user "$SERVER_NAME" -- "$PYTHON_EXE" "$SERVER_PATH"

echo
echo "Verifying registration:"
claude mcp get "$SERVER_NAME"

echo
echo "Done. MCP servers are only loaded when a Claude Code session starts,"
echo "so start a new session (or restart your current one) to see the new tools."
