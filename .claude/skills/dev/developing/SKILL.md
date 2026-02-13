---
name: dev:developing
description: |
  task-list.jsonのタスクを実行。workflowフィールド（tdd/e2e/task）に応じたワークフローで実装。

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
hooks:
  PostToolUse:
    - matcher: "Task"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/hooks/dev/commit-check.sh"
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

### TDDワークフロー（workflow: tdd）

| Step | agent | model | type | 備考 |
|------|-------|-------|------|------|
| 1 CYCLE | tdd-cycle.md | opus | general-purpose | RED→テストcommit→GREEN→REFACTOR(+OpenCode) |
| 2 REVIEW | tdd-review.md | sonnet | general-purpose | 過剰適合・抜け道(+OpenCode) + テスト資産管理。問題→Step 1へ |
| 3 CHECK | quality-check.md | haiku | general-purpose | lint/format/build |
| 4 SPOT | spot-review.md | sonnet | general-purpose | commit後の即時レビュー(+OpenCode) |
| 4b FIX | spot-fix.md | opus | general-purpose | SPOT FAIL時のみ: 修正→CHECK→再SPOT（最大3回） |

### E2Eワークフロー（workflow: e2e）

| Step | agent | model | type | 備考 |
|------|-------|-------|------|------|
| 1 CYCLE | e2e-cycle.md | sonnet | general-purpose | UI実装 → agent-browser検証ループ |
| 2 CHECK | quality-check.md | haiku | general-purpose | lint/format/build |
| 3 SPOT | spot-review.md | sonnet | general-purpose | commit後の即時レビュー(+OpenCode) |
| 3b FIX | spot-fix.md | opus | general-purpose | SPOT FAIL時のみ: 修正→CHECK→再SPOT（最大3回） |

### TASKワークフロー（workflow: task）

**SPOT/FIX以外はサブエージェント呼び出しなし。エージェントが直接実行。**

| Step | agent | model | type | 備考 |
|------|-------|-------|------|------|
| 1 EXEC | - | - | - | エージェントが直接実行（設定ファイル作成、コマンド実行など） |
| 2 VERIFY | - | - | - | 検証（ファイル存在確認、ビルド確認など） |
| 3 SPOT | spot-review.md | sonnet | general-purpose | commit後の即時レビュー(+OpenCode) |
| 3b FIX | spot-fix.md | opus | general-purpose | SPOT FAIL時のみ: 修正→再SPOT（最大3回） |

---

## 実行プロセス

### Phase 0: 計画選択（エージェント実装）

#### 0.1 task-list.json 検索

```bash
files=$(Glob "docs/features/**/task-list.json")
if [ -z "$files" ]; then
  echo "先に /dev:story を実行してタスクリストを作成してください。"
  exit 0
fi
```

#### 0.2 タスク統計を取得

各 task-list.json を Read して統計を計算:
- `totalTasks`: タスク数の合計
- `tddCount`, `e2eCount`, `taskCount`: workflow別タスク数

JSON形式例:
```json
{
  "path": "docs/features/auth/task-list.json",
  "totalTasks": 5,
  "tddCount": 2,
  "e2eCount": 2,
  "taskCount": 1
}
```

#### 0.3 件数別分岐

**0件**: エラーメッセージ表示して終了

**1件**: AskUserQuestion で確認（自動選択しない）
```
Q: 以下の計画を実行しますか?

【パス】docs/features/auth/task-list.json
【タスク数】5 (TDD: 2 / E2E: 2 / TASK: 1)

選択肢: はい / いいえ (パスを直接指定)
```

**2件以上**: AskUserQuestion でリスト選択
```
Q: 実行する計画を選択してください。

1. docs/features/auth/task-list.json
   (5タスク: TDD 2 / E2E 2 / TASK 1)

2. docs/features/profile/task-list.json
   (3タスク: TDD 1 / E2E 1 / TASK 1)

選択肢: 1 / 2 / パスを直接指定
```

#### 0.4 選択結果を環境変数に設定

選択されたパスを `$TASK_LIST` として後続フェーズで使用:
```bash
export TASK_LIST="docs/features/auth/task-list.json"
```

### Phase 1: タスク登録

1. `$TASK_LIST` を読み込み、全タスクを **TaskCreate** で登録
2. 依存関係があれば **TaskUpdate(addBlockedBy)** で設定
3. **TaskList** で登録確認

**ゲート**: タスクが登録されなければ次に進まない。

### Phase 2: タスク実行（workflow別ワークフロー）

1. **実行順序**: workflow: task のタスクを最初に実行（環境構築が必要なため）
2. 各タスクの `workflow` フィールドに応じて上記ワークフローを適用
3. 各タスク完了時に **TaskUpdate(completed)**

**ゲート**: 全タスクが完了しなければ次に進まない。

---

## 完了条件

- [ ] すべてのtaskワークフローが完了（EXEC→VERIFY→SPOT）
- [ ] すべてのtddワークフローが完了（CYCLE→REVIEW→CHECK→SPOT）
- [ ] すべてのe2eワークフローが完了（CYCLE→CHECK→SPOT）
- [ ] 全テストが成功
- [ ] 品質チェックが通過
- [ ] spot-reviewがパス（または3回失敗でエスカレーション）

## 参照

- agents/: tdd-cycle.md, tdd-review.md, e2e-cycle.md, quality-check.md, simple-add-dev.md, spot-review.md, spot-fix.md
- rules/: workflow/tdd-workflow.md, workflow/e2e-cycle.md, workflow/workflow-branching.md
