# Step 3b: タスク登録（Teammate 委譲用）

## 前提

- Step 3a のゲート通過済み（TeamCreate 成功）

## DO

1. `$PLAN_DIR/task-list.json` の全タスクを TaskCreate でチームタスクリストに登録（wave, role, requirePlanApproval をメタデータ付与）
   **⚠️ これらは Step 4 で Teammate に割り当てるための登録。Lead が実行するタスクではない。**
2. Wave 間の blockedBy を TaskUpdate で設定
3. TaskList で登録を確認

## ゲート

1. 全タスク登録済み（task-list.json のタスク数 = TaskList のタスク数）
2. **全タスクの owner が空**（Lead に割り当てられていないこと）。owner が付いているタスクがあれば TaskUpdate で owner を空にリセット
3. 以降 **Delegate mode: Lead はコードを書かない（F1）**
