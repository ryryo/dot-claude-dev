# Step 7: 結果集約 + TeamDelete

## 前提

- Step 6 のゲート通過済み（PR URL 取得済み）

## DO

1. 結果テーブルをユーザーに提示（タスク / ロール / Wave / 状態 / 概要）
2. `$PLAN_DIR/task-list.json` の `metadata.status` を `"completed"` に更新
3. 全 Teammate に `SendMessage("全タスク完了。シャットダウンしてください。")` → 待機
4. `TeamDelete()`
