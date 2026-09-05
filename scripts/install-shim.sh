#!/usr/bin/env bash
# Installs the optional `claude-export` command shim (macOS/Linux).
#
# Writes a `claude-export` script into ~/.local/bin, hardcoded to invoke
# this clone's cli.py via `python3`. ~/.local/bin is a directory many
# dev setups already keep on PATH, so this avoids adding a new PATH
# entry per tool/clone. Safe to re-run: it overwrites any existing shim
# at that location. Not required for the CLI to work -- `python3 cli.py
# <args>` always works regardless of whether this has been run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI_PATH="$REPO_ROOT/cli.py"
if [ ! -f "$CLI_PATH" ]; then
    echo "error: could not find cli.py at $CLI_PATH -- run this script from its original location inside the repo." >&2
    exit 1
fi

TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

SHIM_PATH="$TARGET_DIR/claude-export"
cat > "$SHIM_PATH" <<EOF
#!/usr/bin/env bash
exec python3 "$CLI_PATH" "\$@"
EOF
chmod +x "$SHIM_PATH"

echo "Installed claude-export shim to $SHIM_PATH"

case ":$PATH:" in
    *":$TARGET_DIR:"*)
        echo "$TARGET_DIR is already on PATH -- 'claude-export' should work in new shells now."
        ;;
    *)
        echo "warning: $TARGET_DIR is not on PATH. Add a line like this to your shell profile (~/.bashrc, ~/.zshrc, etc.), then open a new shell:"
        echo "  export PATH=\"$TARGET_DIR:\$PATH\""
        ;;
esac
