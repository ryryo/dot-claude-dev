#!/usr/bin/env bash
# installed_plugins.json から codex@openai-codex の installPath を動的に取得し、
# codex-companion.mjs のフルパスを stdout に出力する。
set -euo pipefail

PLUGINS_JSON="$HOME/.claude/plugins/installed_plugins.json"

if [[ ! -f "$PLUGINS_JSON" ]]; then
  echo "Error: $PLUGINS_JSON not found. Is Claude Code installed?" >&2
  exit 1
fi

INSTALL_PATH=$(node -e "
  const data = require('$PLUGINS_JSON');
  const entries = data.plugins['codex@openai-codex'];
  if (!entries || entries.length === 0) {
    process.stderr.write('Error: codex@openai-codex plugin is not installed.\n');
    process.exit(1);
  }
  process.stdout.write(entries[0].installPath);
")

COMPANION="$INSTALL_PATH/scripts/codex-companion.mjs"

if [[ ! -f "$COMPANION" ]]; then
  echo "Error: codex-companion.mjs not found at $COMPANION" >&2
  exit 1
fi

echo "$COMPANION"
