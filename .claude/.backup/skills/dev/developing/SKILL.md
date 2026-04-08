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

## 実行方法

ワークフロー別の実行方法:
- **TDD**: 各ステップは Task エージェントに委譲する（実装・テスト・レビューは独立性が高い）
- **E2E/TASK**: メインで直接実行し、CHECK/SPOT/FIX のみ Task エージェントに委譲する

### エージェント呼び出しパターン

`scripts/build-prompt.sh` でプロンプトを自動構築する。agent本文 + 追加コンテキスト + LEARNINGS_FOOTER が一括で組み立てられる。

```
prompt = Bash("bash scripts/build-prompt.sh {agent} $LEARNINGS_PATH \"タスク: {name}\n{description}\"")
Task({ prompt, subagent_type: "general-purpose", model: {指定モデル} })
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

**CHECK/SPOT/FIX以外はサブエージェント呼び出しなし。メインが直接実行。**

| Step    | agent          | model  | type            | 備考                                          |
| ------- | -------------- | ------ | --------------- | --------------------------------------------- |
| 1 IMPL  | -              | -      | -               | メインが直接UI実装                             |
| 2 AUTO  | -              | -      | -               | メインが agent-browser CLI で直接検証          |
| 2b FIX  | -              | -      | -               | AUTO NG時: メインが直接修正（最大3回）         |
| 3 CHECK | quality-check.md | haiku | general-purpose | lint/format/build                             |
| 4 SPOT  | spot-review.md | sonnet | general-purpose | commit後の即時レビュー(+OpenCode)             |
| 4b FIX  | spot-fix.md    | opus   | general-purpose | SPOT FAIL時のみ: 修正→CHECK→再SPOT（最大3回） |

**IMPL→AUTO→FIX ループ実行手順:**

```
# Step 1 IMPL（メイン直接実行）
# メインが直接 Read/Write/Edit でUI実装する

# Step 2 AUTO + FIX ループ（メイン直接実行）
fix_count = 0
loop:
  # agent-browser CLI で直接検証
  Bash("agent-browser open <対象URL>")
  Bash("agent-browser snapshot -i")        # 対話要素確認
  Bash("agent-browser screenshot <path>")  # スクリーンショット取得
  # 操作・検証を実行し、結果を評価
  Bash("agent-browser close")

  if 検証OK → break
  fix_count += 1
  if fix_count >= 3 → エスカレーション → break

  # Step 2b FIX（メイン直接実行）
  # 検証で見つかった問題をメインが直接修正
  goto loop

# Step 3 CHECK, 4 SPOT/FIX は共通フロー（Task委譲、テーブル通り）
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

1. ユーザーが直接ディレクトリパスを渡している場合:
   - そのディレクトリ内の `task-list.json` と `story-analysis.json` を読み込む
   - Read で存在確認し、直接 Phase 1 へ
2. `Glob("docs/FEATURES/**/task-list.json")` で検索
3. 0件 → 「先に /dev:story を実行してタスクリストを作成してください。」と案内して終了
4. 各ファイルを Read し、`metadata.status` が `"completed"` のものを除外（未定義は `"pending"` 扱い）
5. 残った候補を **AskUserQuestion** でユーザーに選択させる:
   - 1件: 確認（「この計画を実行しますか？」）
   - 2件以上: リスト選択（タスク数・TDD/E2E/TASK内訳を表示）
6. 選択されたディレクトリを `$STORY_DIR` として確定。`$STORY_DIR/task-list.json` を `$TASK_LIST` とする

**ゲート**: `$TASK_LIST` が確定していなければ次に進まない。

### Phase 1: タスク登録 + コンテキスト読み込み + LEARNINGS.md 作成

1. `$TASK_LIST` を読み込み、全タスクを **TaskCreate** で登録
2. 依存関係があれば **TaskUpdate(addBlockedBy)** で設定
3. **TaskList** で登録確認
4. **story-analysis.json の読み込み**: `$STORY_DIR/story-analysis.json` を Read し、`$STORY_ANALYSIS` として保持する
   - `goal`: ストーリーの達成目標
   - `scope.included` / `scope.excluded`: スコープ境界（実装時のスコープクリープ防止に使用）
   - story-analysis.json が存在しない場合はスキップ（下位互換）
5. `LEARNINGS.md` を作成:
   ```bash
   bash scripts/init-learnings.sh <ストーリーディレクトリ>
   ```
6. `$LEARNINGS_PATH` を作成した LEARNINGS.md の絶対パスに設定

**ゲート**: タスクが登録され、`LEARNINGS.md` が作成されていなければ次に進まない。

### Phase 2: タスク実行（workflow別ワークフロー）

**planPath 参照**: task-list.json の `context.planPath` が存在する場合:
1. Phase 2 開始時に planPath を Read し、当該ストーリーの設計情報（acceptanceCriteria, technicalNotes 等）を `$PLAN_CONTEXT` として保持する
2. サブエージェント呼び出し時、タスクの実装にストーリー全体の設計情報が必要な場合は build-prompt.sh の追加コンテキストに `$PLAN_CONTEXT` を含める。その際、用途を明示するヘッダーを付けること:
   ```
   prompt = Bash("bash scripts/build-prompt.sh {agent} $LEARNINGS_PATH \"タスク: {name}\n{description}\" \"## 全体計画（設計判断・スコープ確認に参照）\n$PLAN_CONTEXT\"")
   ```
3. メイン自身も実装方針やスコープ判断に迷った際に planPath を参照する

**story-analysis.json 参照**: `$STORY_ANALYSIS` が存在する場合:
- `scope.excluded` をスコープクリープ防止のガードレールとして使用。タスク実装中に scope 外の変更を行おうとしていないか確認する
- `goal` をタスクの実装判断（方針に迷った際の判断基準）に使用する
- サブエージェントへの追加コンテキストとしては通常不要（task-list.json の context で十分）。ただし、スコープの判断が難しいタスクでは `scope` 情報を追加コンテキストに含めてよい

#### E2E環境セットアップ（E2Eタスクが存在する場合、Phase 2開始前に1回実行）

```bash
bash ".claude/skills/dev/agent-browser/setup-agent-browser.sh"
```

- `SUCCESS:<prefix>` → agent-browser CLI 使用可能
- `FAIL:<reason>` → AskUserQuestion で `<reason>` を報告して中断

#### タスク実行

1. 各タスクの `workflow` フィールドに応じて上記「ワークフロー別ステップ・委譲先」を適用
2. **build-prompt.sh を使って LEARNINGS_FOOTER を全 Task 呼び出しに自動付与する**
3. 各タスク完了時に **TaskUpdate(completed)**

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

- agents/: tdd-cycle.md, tdd-review.md, quality-check.md, spot-review.md, spot-fix.md
- scripts/: build-prompt.sh, init-learnings.sh
- references/: learnings-footer.md
- rules/: workflow/workflow-branching.md
