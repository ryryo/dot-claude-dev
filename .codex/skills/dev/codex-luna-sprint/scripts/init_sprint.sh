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

luna_workspace="$(cd "$luna_workspace" && pwd -P)"
luna_skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
luna_date_prefix="$(date +%y%m%d)"
luna_sprint_dir="$luna_workspace/.codex/tmp/${luna_date_prefix}_${luna_slug}"

if [[ -e "$luna_sprint_dir" || -L "$luna_sprint_dir" ]]; then
  printf 'Sprint directory already exists: %s\n' "$luna_sprint_dir" >&2
  exit 1
fi

mkdir -p "$luna_workspace/.codex/tmp"
# Do not merge into a directory created by another initializer after the check.
mkdir "$luna_sprint_dir"
mkdir "$luna_sprint_dir/prompts" "$luna_sprint_dir/reviews"

python3 - "$luna_sprint_dir" "$luna_workspace" "$luna_skill_dir" <<'PY'
from pathlib import Path
import shlex
import sys

sprint = Path(sys.argv[1])
workspace = sys.argv[2]
skill_dir = Path(sys.argv[3])
split_dir = skill_dir.parent / "tasks/codex-task-split"
work_contract = split_dir / "references/worker-work-contract.md"

(sprint / "tasks.md").write_text("""# Sprint tasks

## Context

- Original request or existing Story / PLAN path and section:
- Authoritative progress record, if one already exists:
- Source chat ID / host:
- Shared workspace: {workspace}

Inherit the outcome, acceptance and required gates from the original request or
existing sources. Do not rewrite them for delegation or fill gaps with a new
implementation design. Luna owns investigation, local design and test selection.

## Ownership and chat mapping

Use [{task_contract}]({task_contract}); record only assigned work.

| Task ID / request reference | Owner / exclusive write scope / dependencies | Luna chat ID / host / returned title | Round / state | Prompt / report / review reference |
| --- | --- | --- | --- | --- |

Keep task-specific context in its request, not a second copy here. Add an ownership
or dependency decision only when needed. Pending chat IDs are not send targets.

Do not edit the same files or responsibility concurrently, including shared
lockfiles and test environments. Start dependent tasks after prerequisites pass.
Pass [{work_contract}]({work_contract}) to Luna. Save a prompt only when delegating.
Luna review_ready means pending source acceptance, not overall completion.
""".format(
    workspace=workspace,
    task_contract=split_dir / "references/task-contract.md",
    work_contract=work_contract,
), encoding="utf-8")

(sprint / "review.md").write_text("""# Sprint acceptance

Use [{main_review}]({main_review}). Check the actual diff against the original
request or source criteria. Reuse evidence tied to the current change and
environment; add checks only for gaps, integration and material risks.

## Task decisions

Record task ID / round / chat, decision, supporting evidence and any correction.
Use accepted | rework | corrected-by-main | rejected | blocked as needed.
Link to the report and evidence rather than copying logs or design narratives.
Use reviews/<task-id>.md only when a separate detailed record is useful.

## Integration and overall decision

Record the overall accepted | rework | blocked decision with needed integration
checks, remaining risks and references to required gates or progress updates.
Do not repeat task checks already supported by current evidence.

For the first real use, briefly note outcome quality, source preparation/design,
decision returns, review/correction effort and per-model usage only if available.
Do not infer token savings from unavailable usage. Keep completed task chats.
""".format(main_review=split_dir / "references/main-review.md"), encoding="utf-8")

(sprint / "sprint-env.sh").write_text(
    "\n".join([
        f"export LUNA_WORKSPACE={shlex.quote(workspace)}",
        f"export LUNA_SKILL_DIR={shlex.quote(str(skill_dir))}",
        f"export SPRINT_DIR={shlex.quote(str(sprint))}",
        "",
    ]),
    encoding="utf-8",
)
PY

printf 'codex_luna_sprint.workspace=%s\n' "$luna_workspace"
printf 'codex_luna_sprint.skill_dir=%s\n' "$luna_skill_dir"
printf 'codex_luna_sprint.sprint_dir=%s\n' "$luna_sprint_dir"
