# Step 3a: チーム作成

## 前提

- `$WORKTREE_PATH` が Step 2 で確定済み

## DO

1. 既存チーム確認 → 残っていれば TeamDelete でクリーンアップ
2. `TeamCreate({ team_name: "team-run-{slug}" })`

## ゲート

TeamCreate 成功（team_name を含む応答を確認）。

失敗 → **即停止**。**TaskCreate に進んではならない（F6）**
