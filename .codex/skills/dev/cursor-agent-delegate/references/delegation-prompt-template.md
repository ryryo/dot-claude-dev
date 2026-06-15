# Delegation Prompt Template

Cursor Agent または Codex subagent に渡す prompt は、実装方針を過剰に誘導せず、期待成果・制約・検証条件を明示する。

```text
You are a worker agent running inside this repository.

Worker type:
<codex-subagent or cursor-agent>

Workspace:
<absolute workspace path>

Goal:
<one concrete task>

Read first:
- <absolute path>
- <absolute path>

Write scope:
- You may edit only:
  - <path>
  - <path>
- Do not edit:
  - <path>
  - docs/PLAN/**
  - progress/state/generated planning files
- Do not update commits, branches, remotes, package lockfiles, or generated planning docs unless explicitly listed in the allowed write scope.
- Do not revert existing uncommitted changes or files outside your scope.
- Other workers or the user may have active changes. Accommodate them and do not overwrite unrelated work.

Implementation constraints:
- <constraint>
- <constraint>

Verification:
- Run: <command>
- If the command cannot run, explain the exact reason and what you checked instead.

Final report:
- Files changed
- Summary of behavior changed
- Verification commands and results
- Anything intentionally left for main Codex
```

Rules:

- Use absolute paths for workspace and read-first files.
- Pass exactly one task per worker prompt.
- Keep write scope non-overlapping across parallel workers.
- Do not assign final integration, Gate PASS判定, commit, push, PR, or progress-file updates.
- Include a verification command that main Codex can rerun.
- For Codex subagents, include explicit ownership and whether the task is implementation, design, review, or test-strategy work.
