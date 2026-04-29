# Worktree Teardown

Use only when worktree mode was selected and the user is ready to merge.

## Merge

1. Ensure the worktree has no uncommitted changes:

   ```bash
   git -C "$WORKTREE_PATH" status --porcelain
   ```

2. Return to the base repository root:

   ```bash
   BASE_ROOT="$(git worktree list | head -1 | awk '{print $1}')"
   cd "$BASE_ROOT"
   ```

3. Detect the base branch:

   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
   ```

   If that fails, use `master` if present, otherwise `main`.

4. Merge:

   ```bash
   git checkout {base}
   git pull --ff-only 2>/dev/null || echo "pull skipped"
   git merge --no-ff feature/{slug} -m "Merge feature/{slug} via spec-agent-run"
   ```

If conflicts occur, resolve only obvious non-semantic conflicts automatically. Ask the user before choosing sides for code logic, config, `.env`, package metadata, or non-obvious conflicts.

## Cleanup

After a successful merge:

```bash
bash .codex/skills/dev/spec-agent-run/scripts/cleanup-worktree.sh {slug}
```

If cleanup fails because the branch is not merged or the worktree is dirty, stop and report the exact stderr. Do not force-remove automatically.
