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

| Step     | agent            | model  | type            | 備考                                                        |
| -------- | ---------------- | ------ | --------------- | ----------------------------------------------------------- |
| 1 CYCLE  | tdd-cycle.md     | opus   | general-purpose | RED→テストcommit→GREEN→REFACTOR(+OpenCode)                  |
| 2 REVIEW | tdd-review.md    | sonnet | general-purpose | 過剰適合・抜け道(+OpenCode) + テスト資産管理。問題→Step 1へ |
| 3 CHECK  | quality-check.md | haiku  | general-purpose | lint/format/build                                           |
| 4 SPOT   | spot-review.md   | sonnet | general-purpose | commit後の即時レビュー(+OpenCode)                           |
| 4b FIX   | spot-fix.md      | opus   | general-purpose | SPOT FAIL時のみ: 修正→CHECK→再SPOT（最大3回）               |

### E2Eワークフロー（workflow: e2e）

| Step    | agent                                           | model  | type            | 備考                                          |
| ------- | ----------------------------------------------- | ------ | --------------- | --------------------------------------------- |
| 1 IMPL  | e2e-impl.md                                     | opus   | general-purpose | UI実装                                        |
| 2 AUTO  | (cross-skill: agent-browser/subagent-prompt.md) | haiku  | general-purpose | agent-browser CLI検証                         |
| 2b FIX  | e2e-impl.md                                     | sonnet | general-purpose | AUTO NG時: 検証レポートで修正（最大3回）      |
| 3 CHECK | quality-check.md                                | haiku  | general-purpose | lint/format/build                             |
| 4 SPOT  | spot-review.md                                  | sonnet | general-purpose | commit後の即時レビュー(+OpenCode)             |
| 4b FIX  | spot-fix.md                                     | opus   | general-purpose | SPOT FAIL時のみ: 修正→CHECK→再SPOT（最大3回） |

**IMPL→AUTO→FIX ループ実行手順:**

```
# Step 1 IMPL
implAgent = Read("agents/e2e-impl.md")
Task(prompt: implAgent + タスク情報, model: opus)

# Step 2 AUTO + FIX ループ
fix_count = 0
loop:
  format = select_report_format(task)  # interaction(デフォルト) / ui-layout / responsive / api-integration
  formatContent = Read(".claude/skills/dev/agent-browser/references/formats/{format}.md")
  template = Read(".claude/skills/dev/agent-browser/references/subagent-prompt.md")
  prompt = template に {PREFIX}, {ユーザーの指示}, {SCREENSHOT_DIR}, {レポートフォーマット} を置換
  autoResult = Task(prompt: prompt, model: haiku)

  if autoResult == OK → break
  fix_count += 1
  if fix_count >= 3 → エスカレーション → break

  # Step 2b FIX
  fixAgent = Read("agents/e2e-impl.md")
  Task(prompt: fixAgent + タスク情報 + autoResult(検証レポート), model: opus)
  goto loop

# Step 3 CHECK, 4 SPOT/FIX は共通フロー（テーブル通り）
```

### TASKワークフロー（workflow: task）

**SPOT/FIX以外はサブエージェント呼び出しなし。エージェントが直接実行。**

| Step     | agent          | model  | type            | 備考                                                         |
| -------- | -------------- | ------ | --------------- | ------------------------------------------------------------ |
| 1 EXEC   | -              | -      | -               | エージェントが直接実行（設定ファイル作成、コマンド実行など） |
| 2 VERIFY | -              | -      | -               | 検証（ファイル存在確認、ビルド確認など）                     |
| 3 SPOT   | spot-review.md | sonnet | general-purpose | commit後の即時レビュー(+OpenCode)                            |
| 3b FIX   | spot-fix.md    | opus   | general-purpose | SPOT FAIL時のみ: 修正→再SPOT（最大3回）                      |

---

## 実行プロセス

### Phase 0: 計画選択

`agents/phase0-plan-selection.md` に従って実行。`$TASK_LIST` を確定する。

### Phase 1: タスク登録 + LEARNINGS.md 作成

1. `$TASK_LIST` を読み込み、全タスクを **TaskCreate** で登録
2. 依存関係があれば **TaskUpdate(addBlockedBy)** で設定
3. **TaskList** で登録確認
4. `LEARNINGS.md` を作成:
   ```bash
   ~/.claude/hooks/dev/init-learnings.sh <ストーリーディレクトリ>
   ```

**ゲート**: タスクが登録されなければ次に進まない。

### Phase 2: タスク実行（workflow別ワークフロー）

#### E2E環境セットアップ（E2Eタスクが存在する場合、Phase 2開始前に1回実行）

1. `which agent-browser` → 未インストールなら AskUserQuestion で案内
2. `agent-browser open 'data:text/html,<h1>OK</h1>'` → 失敗なら Playwright 修復を案内
3. `mkdir -p /tmp/agent-browser/$(date +%Y%m%d)-{slug}` → SCREENSHOT_DIR 確定

#### タスク実行

1. 各タスクの `workflow` フィールドに応じて上記「ワークフロー別ステップ・委譲先」を適用
2. 各タスク完了時に **TaskUpdate(completed)**
3. **学びの記録**: タスク完了直後に、そのタスクの実行中に以下に該当する事項があれば `LEARNINGS.md` に追記する。何もなければスキップしてよい

**追記すべき事項**:
- 🔍 **発見**: 想定外の挙動、フレームワーク・ライブラリの罠
- 🔄 **計画変更**: 当初計画からの逸脱とその理由
- 💡 **パターン**: 再利用できるノウハウ・実装パターン
- ⚠️ **注意**: 将来ハマりそうな落とし穴

**追記フォーマット**:
```markdown
## {タスク名}（{タスクID}）

- 🔍 ○○が△△な挙動をしていた。□□で回避した
- 🔄 当初は××で実装予定だったが、◇◇の理由で▽▽に変更
```

**ゲート**: 全タスクが完了しなければ次に進まない。

### Phase 3: 計画ステータス更新

全タスク完了後、`$TASK_LIST` の `metadata.status` を `"completed"` に更新して Write で保存する。
これにより次回の計画選択時に候補から除外される。

---

## 完了条件

- [ ] すべてのtaskワークフローが完了（EXEC→VERIFY→SPOT）
- [ ] すべてのtddワークフローが完了（CYCLE→REVIEW→CHECK→SPOT）
- [ ] すべてのe2eワークフローが完了（IMPL→AUTO→CHECK→SPOT）
- [ ] 全テストが成功
- [ ] 品質チェックが通過
- [ ] spot-reviewがパス（または3回失敗でエスカレーション）
- [ ] LEARNINGS.md がストーリーディレクトリに存在する

## 参照

- agents/: tdd-cycle.md, tdd-review.md, e2e-impl.md, quality-check.md, simple-add-dev.md, spot-review.md, spot-fix.md
- cross-skill: .claude/skills/dev/agent-browser/references/subagent-prompt.md, .claude/skills/dev/agent-browser/references/formats/
- rules/: workflow/tdd-workflow.md, workflow/e2e-cycle.md, workflow/workflow-branching.md
