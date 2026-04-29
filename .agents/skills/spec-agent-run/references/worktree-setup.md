# Worktree Setup

Use only when the user chooses worktree mode.

## Dirty Check

Run:

```bash
git status --porcelain
```

If output is empty, continue. If not, ask the user how to proceed:

- commit the current changes
- stash them with `git stash push -m "spec-agent-run worktree setup: {slug}"`
- stop and let the user handle the working tree

Do not discard changes.

## Setup

Derive `{slug}` from the plan directory name, for example:

```text
docs/PLAN/260411_dashboard-table-view/tasks.json -> 260411_dashboard-table-view
```

Run:

```bash
bash .agents/skills/spec-agent-run/scripts/setup-worktree.sh {slug}
```

The script prints the absolute worktree path to stdout. Remember it as `WORKTREE_PATH` and run future commands in that directory.

## Reuse

If the script reports an existing branch or worktree, reuse it. After entering the worktree, merge the base branch into it before continuing:

```bash
git merge {base} --no-edit -m "Sync {base} into feature/{slug}"
```

If conflicts occur, resolve only obvious non-semantic conflicts automatically. Ask the user before choosing sides for code logic, config, `.env`, package metadata, or non-obvious conflicts.
