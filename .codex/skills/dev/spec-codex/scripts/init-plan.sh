#!/usr/bin/env bash
# Usage: bash .codex/skills/dev/spec-codex/scripts/init-plan.sh {YYMMDD}_{slug}
# Example: bash .codex/skills/dev/spec-codex/scripts/init-plan.sh 260513_user-auth
set -euo pipefail

PLAN_ID="${1:?Usage: init-plan.sh {YYMMDD}_{slug}}"
PLAN_DIR="docs/PLAN/${PLAN_ID}"
SKILL_DIR=".codex/skills/dev/spec-codex"

if [ -d "$PLAN_DIR" ]; then
  echo "ERROR: ${PLAN_DIR} already exists" >&2
  exit 1
fi

mkdir -p "${PLAN_DIR}/references"

cp "${SKILL_DIR}/references/templates/context-template.md"  "${PLAN_DIR}/references/context.md"
cp "${SKILL_DIR}/references/templates/tasks.template.json"  "${PLAN_DIR}/tasks.json"

echo "Created: ${PLAN_DIR}/"
echo "  references/context.md  (from context-template.md)"
echo "  tasks.json             (from tasks.template.json)"
echo ""
echo "Next: edit context.md and tasks.json, then write spec.md"
