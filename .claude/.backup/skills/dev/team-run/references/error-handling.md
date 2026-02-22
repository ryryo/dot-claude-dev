# エラーハンドリング・エスカレーション

このファイルは SKILL.md のエラー発生時に `Read()` して使用する。

---

## エラーパターンテーブル

| 状況 | 対応 | エスカレーション基準 |
|------|------|---------------------|
| Teammate 無応答（5分） | SendMessage で状況確認 | — |
| 状況確認後も無応答（5分） | shutdown_request → 同タスクで再スポーン | 3回失敗 → ユーザーに報告 |
| Worktree セットアップ失敗 | エラー内容をユーザーに報告 | 即座にエスカレーション |
| Plan Approval 3回拒否 | 自動承認 + リスクをユーザーに報告 | — |
| lint/build 失敗（hook） | Teammate に修正を指示 | 3回失敗 → ユーザーに報告 |
| タスク完了 outputs 不在 | Teammate に不足事項を通知し継続指示 | 3回失敗 → ユーザーに報告 |

---

## Teammate 遅延・失敗時のエスカレーション手順

```
1. SendMessage で状況確認（5分無応答後）
     ↓ 5分待っても応答なし
2. 当該 Teammate のみ shutdown_request → 同じタスクで新 Teammate を再スポーン
     ↓ 再スポーンも失敗（3回）
3. AskUserQuestion でユーザーに報告し、指示を仰ぐ
   選択肢:
   - タスクをスキップして次へ進む
   - 中止する
```

**⛔ 禁止:**
- Lead がユーザー承認なしに Teammate の作業を代行しない（Delegate mode 厳守）
- 1つの Teammate が遅延しても、他の Teammate をシャットダウンしない

---

## hooks 検証内容

### TeammateIdle hook

Teammate が待機状態に入る前に検証:
- [ ] 担当タスクの outputs に記載されたファイルが実際に存在する
- [ ] コミットされている（`git status` でクリーン）
- [ ] 同一 Wave 内に Self-claim 可能なタスクがない

品質未達 → SendMessage で不足事項を通知し、作業を継続させる

### TaskCompleted hook

タスク完了前に検証:
- [ ] outputs ファイルが存在する
- [ ] lint/format エラーがない（プロジェクトに lint 設定がある場合）
- [ ] コミットされている

検証失敗 → TaskUpdate で completed にせず、Teammate に修正を指示

---

## Wave 完了判定チェックリスト

- [ ] 当該 Wave の**全タスク**が TaskList で `completed` になっている
- [ ] 各タスクの成果物（outputs）が**ファイルとして実際に存在する**ことを確認
- [ ] worktree にコミットがある（`git log` で確認）
