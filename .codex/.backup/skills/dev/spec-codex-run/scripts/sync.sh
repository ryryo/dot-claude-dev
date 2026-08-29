#!/usr/bin/env bash
# Usage: bash .codex/skills/dev/spec-codex-run/scripts/sync.sh {YYMMDD}_{slug}
# Example: bash .codex/skills/dev/spec-codex-run/scripts/sync.sh 260513_user-auth
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: sync.sh {YYMMDD}_{slug}" >&2
  exit 1
fi

PLAN_ID="$1"
TASKS_JSON="docs/PLAN/${PLAN_ID}/tasks.json"

if [ ! -f "$TASKS_JSON" ]; then
  echo "ERROR: ${TASKS_JSON} not found" >&2
  exit 1
fi

node "$(dirname "$0")/sync-spec-md.mjs" "$TASKS_JSON"
echo "Synced: ${TASKS_JSON} -> docs/PLAN/${PLAN_ID}/spec.md"
