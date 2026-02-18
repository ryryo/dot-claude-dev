# Step 6: PR作成 + クリーンアップ

## 前提

- Step 5 のゲート通過済み（レビュー完了 or スキップ）

## DO

1. `git -C $WORKTREE_PATH status --porcelain` で全コミット済み確認
2. `git -C $WORKTREE_PATH push -u origin feature/{slug}`
3. `gh pr create --title "feat: {slug}" --body "{Summary + Changes + Review Notes}"`
4. `bash .claude/skills/dev/team-run/scripts/cleanup-worktree.sh {slug}`

## ゲート

PR URL を取得
