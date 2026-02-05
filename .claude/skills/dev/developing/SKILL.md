---
name: dev:developing
description: |
  TODO.mdのタスクを実行。TDD/E2E/TASKラベルに応じたワークフローで実装。

  Trigger:
  dev:developing, /dev:developing, 実装, 開発, implementing, develop
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - TaskCreate
  - TaskList
  - TaskGet
  - TaskUpdate
---

# 実装（dev:developing）

## エージェント委譲ルール

**各ステップの実行は必ずTaskエージェントに委譲する。自分で実装・テスト・レビューしない。**

呼び出しパターン（全ステップ共通）:
```
agentContent = Read(".claude/skills/dev/developing/agents/{agent}.md")
Task({ prompt: agentContent + 追加コンテキスト, subagent_type: {type}, model: {指定モデル} })
```

## エラーハンドリング

エージェントが❌（FAILED）を返した場合:
1. エラー内容を確認
2. 修正可能なら前のステップに戻って再実行（例: CHECK失敗 → CYCLE に戻る）
3. 同じステップが合計3回失敗 → ユーザーに状況を報告し、指示を仰ぐ

**エスカレーション報告形式**:
「{タスク名}の{ステップ名}が3回失敗しました。{エラー要約}。どう対応しますか？」

## ワークフロー別ステップ・委譲先

### TDDワークフロー（[TDD]ラベル）

| Step | agent | model | type | 備考 |
|------|-------|-------|------|------|
| 1 CYCLE | tdd-cycle.md | sonnet | general-purpose | RED→テストcommit→GREEN→REFACTOR |
| 2 REVIEW | tdd-review.md | opus | general-purpose | 過剰適合・抜け道 + テスト資産管理。問題→Step 1へ |
| 3 CHECK | quality-check.md | haiku | general-purpose | lint/format/build |
| 4 COMMIT | simple-add-dev.md | haiku | simple-add | 実装+テスト整理結果をコミット |

### E2Eワークフロー（[E2E]ラベル）

| Step | agent | model | type | 備考 |
|------|-------|-------|------|------|
| 1 CYCLE | e2e-cycle.md | sonnet | general-purpose | UI実装 → agent-browser検証ループ |
| 2 CHECK | quality-check.md | haiku | general-purpose | lint/format/build |
| 3 COMMIT | simple-add-dev.md | haiku | simple-add | コミット |

### TASKワークフロー（[TASK]ラベル）

**サブエージェント呼び出しなし。エージェントが直接実行。**

```
1. TaskUpdate(in_progress)
2. 実行（設定ファイル作成、コマンド実行など）
3. 検証（ファイル存在確認、ビルド確認など）
4. TaskUpdate(completed) + TODO.md更新（- [ ] → - [x]）
5. /simple-add でコミット
```

---

## 実行手順（必ずこの順序で実行）

### Phase 1: タスク登録

1. TODO.mdを読み込み、未完了タスク（`- [ ]`）を **TaskCreate** で登録
2. 依存関係があれば **TaskUpdate(addBlockedBy)** で設定
3. **TaskList** で登録確認

**ゲート**: タスクが登録されなければ次に進まない。

### Phase 2: タスク実行（ラベル別ワークフロー）

1. **実行順序**: TASKタスクを最初に実行（環境構築が必要なため）
2. 各タスクのラベルに応じて上記ワークフローを適用
3. 各タスク完了時に **TaskUpdate(completed)** + TODO.md更新（`- [ ]` → `- [x]`）

**ゲート**: 全タスクが完了しなければ次に進まない。

---

## 完了条件

- [ ] すべてのTASKタスクが完了
- [ ] すべてのTDDタスクが完了（CYCLE→REVIEW→CHECK→COMMIT）
- [ ] すべてのE2Eタスクが完了（CYCLE→CHECK→COMMIT）
- [ ] 全テストが成功
- [ ] 品質チェックが通過
- [ ] TODO.mdが全て完了マーク

## 参照

- agents/: tdd-cycle.md, tdd-review.md, e2e-cycle.md, quality-check.md, simple-add-dev.md
- rules/: workflow/tdd-workflow.md, workflow/e2e-cycle.md, workflow/workflow-branching.md
