# Review Checklist

Main Codex must validate every worker result before accepting it.

## Before delegation

Run and record:

```bash
git status --short
git branch --show-current
```

Treat existing uncommitted changes as user or prior-worker work. Do not revert them.

## After delegation

Run:

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

Check:

- Changed files are inside the allowed write scope.
- The worker did not modify docs/PLAN, tasks.json, progress files, commits, branches, remotes, or package lockfiles unless explicitly allowed.
- Existing uncommitted changes were not reverted.
- The worker's final report matches the actual diff, reasoning, and verification output.
- The requested behavior is complete against the original goal.
- Verification commands ran and passed, or the failure reason is precise and acceptable.
- For CLI transport, the log includes the expected session/model metadata when available.
- For mac IDE AppleScript transport, report that model selection came from Cursor IDE state and was not programmatically verified.
- For Codex subagents, inspect the returned summary, changed files, and rationale before integrating.

## Scope drift

If files outside scope changed:

1. Inspect the log and diff before taking action.
2. If the out-of-scope change is clearly worker-created and safe to remove, main Codex may correct it.
3. If the change may belong to the user or another agent, ask the user before altering it.
4. Do not use broad destructive commands.

## Acceptance

Accept the result only after the diff, scope, report, and verification all line up. Planning/progress updates, final PASS判定, commits, and PRs remain main Codex responsibilities.
