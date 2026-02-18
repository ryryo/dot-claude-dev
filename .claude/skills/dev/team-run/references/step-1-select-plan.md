# Step 1: 計画選択 + Pre-flight

## DO

1. `docs/features/team/` 以下の `task-list.json` を Glob で列挙
2. `metadata.status` が `"completed"` のものを除外し、AskUserQuestion で選択
3. 選択した計画のパスを `$PLAN_DIR` として保持
4. Pre-flight 検証（全タスクに対して）:
   - 8必須フィールド: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `taskPrompt`
   - Wave構造: `waves[].tasks[]` フラット配列 + `role` フィールド
   - `taskPrompt` が具体的（ファイルパス・操作内容が明記）
   - `story-analysis.json` の `fileOwnership` が存在

## ゲート

Pre-flight 全合格。1つでも不合格 → **即停止** + 不合格タスク ID・欠損フィールドを報告 + `dev:team-plan` での修正を案内

## 出力変数

- `$PLAN_DIR`: 選択した計画ディレクトリのパス
