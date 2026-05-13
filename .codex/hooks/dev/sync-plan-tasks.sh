#!/bin/bash
# Codex Stop hook helper: sync spec.md generated sections for changed PLAN tasks.

set -euo pipefail

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SYNC_SCRIPT="$ROOT/.codex/skills/dev/spec-codex-run/scripts/sync.sh"

if [ ! -f "$SYNC_SCRIPT" ]; then
  exit 0
fi

changed_tasks=$(
  {
    git -C "$ROOT" diff --name-only -- docs/PLAN 2>/dev/null || true
    git -C "$ROOT" diff --cached --name-only -- docs/PLAN 2>/dev/null || true
    git -C "$ROOT" ls-files --others --exclude-standard -- docs/PLAN 2>/dev/null || true
  } | awk -F/ '$1 == "docs" && $2 == "PLAN" && NF == 4 && $4 == "tasks.json" { print }' | sort -u
)

if [ -z "$changed_tasks" ]; then
  exit 0
fi

while IFS= read -r tasks_path; do
  [ -n "$tasks_path" ] || continue
  plan_id=$(basename "$(dirname "$tasks_path")")
  echo "Syncing PLAN generated section: $plan_id" >&2
  bash "$SYNC_SCRIPT" "$plan_id" >&2
done <<< "$changed_tasks"
