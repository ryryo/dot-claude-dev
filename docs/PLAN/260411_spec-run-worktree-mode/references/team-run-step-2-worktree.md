# Step 2: Git Worktree セットアップ

## 前提

- `$PLAN_DIR` が Step 1 で確定済み

## DO

1. `git status --porcelain` で未コミット変更を確認（変更あり → AskUserQuestion で対応選択）
2. `git push && git pull --rebase` でリモート同期（コンフリクト → ユーザーに報告 → AskUserQuestion で対応選択）
3. `bash .claude/skills/dev/team-run/scripts/setup-worktree.sh {slug}` で Worktree 作成
4. `$WORKTREE_PATH` を取得（スクリプトの stdout）

## ゲート

`$WORKTREE_PATH` が有効 + `git -C $WORKTREE_PATH branch --show-current` が `feature/{slug}`

## 出力変数

- `$WORKTREE_PATH`: Worktree のパス
