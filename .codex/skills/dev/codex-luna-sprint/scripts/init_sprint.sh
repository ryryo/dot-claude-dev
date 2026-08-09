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

mkdir -p "$luna_sprint_dir/prompts" "$luna_sprint_dir/reviews"

python3 - "$luna_sprint_dir" "$luna_workspace" "$luna_skill_dir" <<'PY'
from pathlib import Path
import shlex
import sys

sprint = Path(sys.argv[1])
workspace = sys.argv[2]
skill_dir = sys.argv[3]

(sprint / "product-frame.md").write_text("""# Product frame

## Status

- State: draft
- Confirmed by main: no

## Source precedence

| Source | Path or evidence | Authority and conflicts |
| --- | --- | --- |
| Latest user intent | <record> | <decision> |
| Foundational workflow | <path and section> | <decision> |
| User stories / UX | <path and section> | <decision> |
| Existing plan | <path and section> | <decision> |
| Lab / prototype / fixture | <path and classification> | <constraint scope> |

## User and outcome

- User:
- Starting state:
- Desired outcome:
- Completion evidence:

## Journeys

### Normal

- <upstream inputs -> user decisions -> result>

### Optional / fallback

- <secondary paths that must not dominate the normal CTA>

### Failure / reload recovery

- <preserved state and recovery action>

## Input provenance

| Value | Inherited from | User may override | Must not be re-entered |
| --- | --- | --- | --- |
| <value> | <source> | <when> | <invariant> |

## UX invariants

- Upstream confirmed values are inherited rather than re-entered.
- Upload and internal settings do not outrank upstream artifact selection.
- Lab or fixture limits do not become production domain limits.
- Import or generation success does not auto-approve human decisions.
- Exceptional controls do not appear as equal-strength normal controls.

## Path classification

| Capability | normal | optional | fallback | technical substrate | Lab-only |
| --- | --- | --- | --- | --- | --- |
| <capability> |  |  |  |  |  |

## Unresolved product decisions

- <must be empty before confirmation>
""", encoding="utf-8")

(sprint / "implementation-plan.md").write_text("""# Implementation plan

## Status

- State: draft
- Product frame prerequisite: not-confirmed

Do not design architecture until product-frame.md is confirmed.

## Story-to-implementation trace

| Story / invariant | Architecture / UI | API / schema | Acceptance |
| --- | --- | --- | --- |
| <source> | <decision> | <contract> | <evidence> |

## Data and state

- <data flow, state transitions, migration, failure, security>

## Technical substrate boundaries

- <what is useful infrastructure but not a finished user journey>

## Verification

- <behavior tests, integration, browser acceptance>

## Unresolved implementation decisions

- <must be empty before task routing>
""", encoding="utf-8")

(sprint / "tasks.md").write_text("""# Sprint tasks

## Prerequisites

- Product frame: draft
- Implementation plan: draft
- Luna routing allowed: no

## Rule

- Register every task as main-codex first.
- User stories, UX, UI composition, user-facing wording, accessibility, domain/API contracts, and state transitions always remain main-codex.
- Move only fully specified pure logic, parsers/serializers, fixtures, table tests, mechanical codemods, or exact adapters after both prerequisite reviews are confirmed.
- A small UI leaf is not a Luna leaf. Fixed API adapters qualify only after main fixes method/path, request/response mapping, validation/coercion, auth/authorization/ownership (or explicit N/A), success status, error algebra/body, idempotency, and mutation/side effects.

## Routing registry

- <copy task fields from references/task-contract.md>

## Dependency order and conflicts

- <main story/UX/contracts -> optional mechanical Luna leaf -> main diff review/integration/journey review>
""", encoding="utf-8")

(sprint / "reviews" / "product-frame.md").write_text("""# Product frame review

- Decision: draft | confirmed | rework
- Source conflicts:
- Normal journey findings:
- Optional / fallback findings:
- Recovery findings:
- Reviewer evidence:
- Main decision:
""", encoding="utf-8")

(sprint / "reviews" / "implementation-plan.md").write_text("""# Implementation plan review

- Decision: draft | confirmed | plan-reopened
- Story / UX trace findings:
- Shadow state or Lab leakage findings:
- Contract and migration findings:
- Main decision:
""", encoding="utf-8")

(sprint / "review.md").write_text("""# Main review

## Product and plan reviews

- Product frame: <reviews/product-frame.md>
- Implementation plan: <reviews/implementation-plan.md>

## Task decisions

- <reviews/Txx.md: accepted, corrected-by-main, rejected, or blocked>

## Whole-user-journey verification

- Normal journey evidence:
- Exception / recovery evidence:
- Regression evidence:

## Final decision

- accepted | rework | plan-reopened
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
