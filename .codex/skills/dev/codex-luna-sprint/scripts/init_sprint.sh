#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'Usage: init_sprint.sh --slug SLUG [--workspace PATH]' \
    '' \
    '  --workspace PATH  repository workspace (default: current directory)' \
    '  --slug SLUG        2-49 lowercase letters, digits, underscore, or hyphen'
}

luna_workspace="$PWD"
luna_slug=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) luna_workspace="${2:?}"; shift 2 ;;
    --slug) luna_slug="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! "$luna_slug" =~ ^[a-z0-9][a-z0-9_-]{1,48}$ ]]; then
  printf 'Invalid --slug: %s\n' "$luna_slug" >&2
  exit 2
fi

luna_workspace="$(cd "$luna_workspace" && pwd)"
luna_skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
luna_date_prefix="$(date +%y%m%d)"
luna_sprint_dir="$luna_workspace/.codex/tmp/${luna_date_prefix}_${luna_slug}"

if [[ -e "$luna_sprint_dir" ]]; then
  printf 'Sprint directory already exists: %s\n' "$luna_sprint_dir" >&2
  exit 1
fi

mkdir -p "$luna_sprint_dir/prompts"

python3 - "$luna_sprint_dir" "$luna_workspace" "$luna_skill_dir" <<'PY'
from pathlib import Path
import shlex
import sys

sprint = Path(sys.argv[1])
workspace = sys.argv[2]
skill_dir = sys.argv[3]

(sprint / "brief.md").write_text("""# Sprint brief

## Goal

- <one bounded outcome>

## Repository context

- <relevant entrypoints, contracts, tests>

## Constraints

- Luna handles only fixed or bounded leaf tasks.
- main Codex owns shared decisions, integration, and final acceptance.

## Minimum verification

- <focused behavior test>
""", encoding="utf-8")

(sprint / "tasks.md").write_text("""# Sprint tasks

## Dependency order

- <main contract> -> <Luna leaf> -> <main integration>

## Tasks

- <copy the task contract from references/task-contract.md>

## Conflicts

- <exclusive write scopes>
""", encoding="utf-8")

(sprint / "review.md").write_text("""# Main review

## Diff review

- <allowed scope and worker report comparison>

## Verification

- <commands and results>

## Decision

- <accepted, corrected, or rejected>
""", encoding="utf-8")

(sprint / "sprint-env.sh").write_text(
    "\n".join([
        f"export LUNA_WORKSPACE={shlex.quote(workspace)}",
        f"export LUNA_SKILL_DIR={shlex.quote(skill_dir)}",
        f"export SPRINT_DIR={shlex.quote(str(sprint))}",
        "",
    ]),
    encoding="utf-8",
)
PY

printf 'codex_luna_sprint.workspace=%s\n' "$luna_workspace"
printf 'codex_luna_sprint.skill_dir=%s\n' "$luna_skill_dir"
printf 'codex_luna_sprint.sprint_dir=%s\n' "$luna_sprint_dir"
