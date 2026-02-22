# Step 5: レビュー・フィードバックループ

## 前提

- Step 4 のゲート通過済み（全 Wave 完了）

## DO

1. Reviewer 報告の改善候補を集約
2. AskUserQuestion で重要度付きリストをユーザーに提示（対応する項目を選択 / 対応不要）
3. 対応不要 → Step 6 へ
4. 対応あり → fix タスク生成 + TaskCreate + Teammate スポーン（`Read("references/teammate-spawn-protocol.md")` に従う）
5. fix 完了後 → AskUserQuestion で再レビュー要否を確認

## ゲート

ユーザー承認 or 3ラウンド超過 → Step 6 へ
