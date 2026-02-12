---
name: dev:team-opencode
description: |
  Agent Teamsでタスクを並行実行。計画フェーズでロール分業・Wave構造を設計し、
  各エージェント(haiku)がopencode runで外部モデルに実装を委譲する。
  レビュー・フィードバックループで品質を担保する。

  Trigger:
  dev:team-opencode, /dev:team-opencode, チームで実装, team opencode, swarm実装
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
  - TeamCreate
  - TeamDelete
  - SendMessage
---

# Agent Teams + opencode 並行実装（dev:team-opencode）

## 概要

ストーリーまたは直接指示を受け取り、計画フェーズでロール分業・Wave構造を設計した上で、Agent Teamsで並行実装する。各エージェント（haiku）は `opencode run` で外部モデルに実装を委譲し、結果をコミットする。最終Waveにはレビュワーを必ず配置し、品質ゲートとフィードバックループで品質を担保する。

## 必須リソース

| リソース                              | 読み込みタイミング                  | 用途                       |
| ------------------------------------- | ----------------------------------- | -------------------------- |
| `references/agent-prompt-template.md` | Phase 1-3（エージェントスポーン前） | 統一エージェントプロンプト |
| `references/role-catalog.md`          | Phase 0-2（ロール設計時）           | ロール定義の参照           |
| `references/templates/*.json`         | Phase 0-0（初期化時）               | テンプレート雛形           |

**⚠️ エージェントスポーン時、必ず `agent-prompt-template.md` を Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

## 一時計画フォルダ

```
docs/features/team-opencode/
├── story-analysis.json    # ストーリー分析（ゴール、スコープ、受入条件、チーム設計）
├── task-list.json         # ロールごとのタスク定義（Wave構造 + ロール割当）
└── prompts/               # 各ロールの opencode 実行プロンプト（自動生成）
```

---

## Phase 0: 計画（Claude Code が実行）

### 0-0: クリーンアップ＆テンプレート初期化

```bash
bash .claude/skills/dev/team-opencode/scripts/init-team-workspace.sh
```

### 0-1: opencode モデル選択

AskUserQuestion で使用するopencode モデルを確認:

```
Q: opencode run で使用するモデルは？
選択肢:
- openai/gpt-5.3-codex
- zai-coding-plan/glm-5
- zai-coding-plan/glm-4.7
```

選択されたモデルを `$OC_MODEL` として以降のすべてのコマンドに使用する。

### 0-2: ストーリー分析 → story-analysis.json

1. ユーザーのストーリー/指示を分析
2. `references/role-catalog.md` を Read で読み込み、必要なロールを選定
3. `docs/features/team-opencode/story-analysis.json` を以下の構造で埋める:

```json
{
  "story": { "title": "...", "description": "..." },
  "goal": "...",
  "scope": { "included": [...], "excluded": [...] },
  "acceptanceCriteria": [...],
  "teamDesign": {
    "roles": [
      {
        "name": "ロール名",
        "catalogRef": "role-catalog.mdのキー",
        "customDirective": "タスク固有の追加指示（不要ならnull）",
        "outputs": ["期待する出力ファイル"]
      }
    ],
    "waves": [
      {
        "id": 1,
        "parallel": ["ロール名1", "ロール名2"],
        "description": "Wave説明"
      },
      {
        "id": 2,
        "parallel": ["ロール名3"],
        "blockedBy": [1],
        "description": "Wave説明"
      }
    ],
    "qualityGates": ["最終Waveにレビュワー配置"]
  }
}
```

**ルール**:

- 最終Waveには必ず `reviewer` ロールを配置する
- Wave間の `blockedBy` で直列依存を明示する
- 同一Wave内のロールは並行実行される

### 0-3: コード探索＆タスク分解 → task-list.json

1. 対象コードベースを探索（Glob, Grep, Read）
2. 各ロールのタスクを **1つのopencode呼び出しで完結する粒度** に分解
3. `docs/features/team-opencode/task-list.json` を以下の構造で埋める:

```json
{
  "context": {
    "description": "...",
    "targetFiles": {},
    "relatedModules": {},
    "technicalNotes": {}
  },
  "waves": [
    {
      "id": 1,
      "roles": {
        "ロール名": [
          {
            "id": "task-1-1",
            "name": "タスク名",
            "description": "タスク説明",
            "needsPriorContext": false,
            "inputs": [],
            "outputs": ["出力ファイルパス"],
            "opencodePrompt": "opencode に渡す具体的な実装指示"
          }
        ]
      }
    }
  ],
  "metadata": {
    "totalTasks": 0,
    "totalWaves": 0,
    "roles": []
  }
}
```

### 0-4: opencode でタスクレビュー

タスク分解の品質を opencode の codex モデルで検証する。モデルは必ず「openai/gpt-5.3-codex」指定。

```bash
opencode run -m openai/gpt-5.3-codex "
Review this team task breakdown:

## Story Analysis
{story-analysis.json の内容}

## Task List
{task-list.json の内容}

Analyze:
1. Task granularity - Each task should be completable in a single opencode call
2. Wave dependencies - inputs/outputs consistent across waves?
3. Role assignment - Does each task match its assigned role?
4. Missing tasks - Setup, error handling, edge cases?
5. Risk - External dependencies, technical unknowns?

Respond with:
- APPROVED or NEEDS_REVISION
- Top 3-5 recommendations (if NEEDS_REVISION)
- Suggested modifications as JSON patches to task-list.json
" 2>&1
```

**判定**:

- `APPROVED` → 0-5 へ
- `NEEDS_REVISION` → task-list.json を修正 → 再レビュー（最大3回）
- 3回失敗 → 現状のままユーザーに提示し判断を仰ぐ

**注意**: codex の提案をそのまま適用するのではなく、リーダーが妥当性を判断してから適用する。

### 0-5: ユーザー承認

task-list.json を整形し、AskUserQuestion でユーザーに提示:

```
Q: 以下の計画でAgent Teamsを実行します。承認しますか？

【チーム構成】 {ロール一覧}
【Wave構造】 {Wave 1}: {並行ロール} → {Wave 2}: {並行ロール} → ...
【タスク数】 {totalTasks}タスク / {totalWaves} Wave
【モデル】 {$OC_MODEL}

選択肢:
- 承認して実行
- タスク一覧を詳しく見たい（task-list.json の全タスクを展開表示）
- 修正が必要（Phase 0-2 に戻る）
```

**ゲート**: ユーザー承認なしに Phase 1 に進まない。

---

## Phase 1: チーム実行（Wave式）

### 1-1: チーム作成

```
TeamCreate({ team_name: "team-opencode-{timestamp}", description: "opencode並行実装" })
```

### 1-2: タスク登録

task-list.json の全タスクを TaskCreate で登録する。Wave間の `blockedBy` も設定。

### 1-3: Wave N のエージェントスポーン

現在のWaveに属するロールごとに1エージェントをスポーン。

**全エージェント共通設定**:

- `model`: haiku
- `subagent_type`: general-purpose
- `run_in_background`: true

**プロンプト構築手順**:

1. `references/agent-prompt-template.md` を Read で読み込む
2. `references/role-catalog.md` から該当ロールの `role_directive` を取得
3. `story-analysis.json` から該当ロールの `customDirective` を取得
4. task-list.json からタスクの `description`, `inputs`, `outputs`, `opencodePrompt` を取得
5. テンプレートの変数を置換してエージェントプロンプトとして使用
6. task-list.json の `needsPriorContext` を確認し、テンプレートの `{prior_context_step}` を置換
7. task-list.json の `name` を `{task_name}` として置換

⚠️ **必須**: テンプレートの文言を改変・省略・要約しない。変数（`{...}`）のみ置換する。

### 1-4: 完了待機

TaskList を定期的に確認し、現在のWaveの全タスク完了を待つ。

**タイムアウト**: エージェントが5分以上 in_progress のまま変化がない場合、「エージェント遅延・失敗時のエスカレーション手順」に従う。

**⚠️ 禁止:**

- エージェント遅延を理由に、リーダーがユーザー承認なしで作業を代行する
- 1つのエージェントの遅延を理由に、他のエージェントをシャットダウンする
- Wave未完了のまま次のWaveに進む

### 1-5: 次Wave スポーン

現在のWaveが完了したら、「Wave完了ゲート」のチェックリストを確認し、次のWaveのエージェントをスポーンする（1-3 に戻る）。全Waveが完了するまで繰り返す。

**⚠️ 必須**: 最終Wave（reviewer含む）の完了まで、このループを続ける。Waveを省略しない。

---

## Phase 2: レビュー・フィードバックループ

### 2-1: レビュワー報告の受信

最終Waveのレビュワーが改善候補を SendMessage で報告する。

レビュワーの `customDirective` には以下を含めること:

```
レビュー完了後、改善候補を以下の形式で報告してください:
1. [重要度: 高/中/低] 改善内容の簡潔な説明
2. [重要度: 高/中/低] ...

改善候補がない場合は「改善候補なし」と報告してください。
```

### 2-2: ユーザーへの提示

AskUserQuestion でレビュー結果をユーザーに提示:

```
Q: レビュワーから以下の改善候補が挙がりました。対応しますか？
- 候補1: {改善内容}
- 候補2: {改善内容}
- 対応不要（完了へ進む）
```

### 2-3: フィードバック分岐

- **対応あり** → Phase 0-2 に戻る（story-analysis.json / task-list.json を更新し、新Waveのエージェントをスポーン）
- **対応なし** → Phase 3 へ

**ループ制限**: 最大3ラウンド。超過時はユーザーに継続可否を確認。

---

## Phase 3: クリーンアップ

### 3-1: 結果集約

全タスク完了後、各エージェントからの報告を集約してユーザーに提示:

```
## 実行結果

| タスク | ロール | 状態 | 概要 |
|--------|--------|------|------|
| {タスク1} | {ロール} | ✅ / ❌ | {概要} |
```

### 3-2: シャットダウン

全エージェントに shutdown_request を送信。

### 3-3: TeamDelete

```
TeamDelete()
```

---

## エラーハンドリング

| 状況                      | 対応                                 |
| ------------------------- | ------------------------------------ |
| opencode run エラー       | 同じコマンドを最大3回リトライ        |
| エージェント無応答（5分） | SendMessage で状況確認               |
| 状況確認後も無応答（5分） | エージェントを再スポーン（下記参照） |
| 3回リトライ失敗           | ユーザーに報告、指示を仰ぐ           |
| opencode モデル利用不可   | ユーザーに報告、別モデル選択を促す   |

### エージェント遅延・失敗時のエスカレーション手順

エージェントが期待通りに動かない場合、以下の手順を**順番に**実行する。手順を飛ばさない。

```
1. SendMessage で状況確認（5分無応答後）
     ↓ 5分待っても応答なし
2. 当該エージェントのみ shutdown_request → 同じタスクで新エージェントを再スポーン
     ↓ 再スポーンも失敗（3回）
3. AskUserQuestion でユーザーに報告し、指示を仰ぐ
   選択肢:
   - リーダーが当該タスクのみ代行（他のWave・タスクはスキップしない）
   - タスクをスキップして次へ進む
   - 中止する
```

**⚠️ 禁止事項:**

- リーダーが**ユーザー承認なしに**エージェントの作業を代行しない
- 1つのエージェントが遅延しても、**他のエージェントをシャットダウンしない**
- エージェント代行時も、**後続Waveのスキップは禁止**（代行完了後、次Waveを通常通りスポーンする）

---

## Wave完了ゲート（厳守）

各Waveの完了時に以下のチェックリストを**すべて満たしてから**次のWaveに進む。

### Wave N → Wave N+1 移行チェックリスト

- [ ] 当該Waveの**全タスク**が TaskList で `completed` になっている
- [ ] 各タスクの成果物（outputs）が**ファイルとして実際に存在する**ことを確認（`ls` / `Glob`）
- [ ] 次のWaveが存在する場合、**次Waveのエージェントをスポーンする**（Phase 1-3 に戻る）

### 最終Wave完了 → Phase 2 移行チェックリスト

- [ ] 最終Waveの reviewer タスクが `completed` になっている
- [ ] reviewer からの改善候補報告を受信している
- [ ] Phase 2-2 でユーザーに改善候補を提示する

**⚠️ 以下の行為は禁止:**

- Wave完了前に次Waveのエージェントをスポーンする
- 最終Wave（reviewer）をスキップして Phase 3 に進む
- タスクを実行せずに `completed` にする

---

## タスク完了の定義

TaskUpdate で `completed` にする条件:

1. **エージェントが実行した場合**: opencode結果を適用し、dev:simple-add でコミット済み
2. **リーダーが代行した場合**: ユーザー承認を得た上で代行し、dev:simple-add でコミット済み
3. **いずれの場合も**: 成果物ファイルが存在し、コミットされていることを確認済み

**⚠️ 禁止**: 上記条件を満たさずにタスクを `completed` にする

---

## 重要な注意事項

1. **opencode コマンドは決め打ち**: プロンプトテンプレートのコマンドをエージェントに改変させない
2. **フォールバック禁止**: opencode 失敗時に直接実装しない。リトライのみ
3. **モデル固定**: 選択されたモデルを全エージェントで統一
4. **CC側はhaiku**: コスト最小化。実装はopencode側が担当
5. **越境防止**: 各エージェントは自分のタスク以外に手を出さない
6. **計画はリーダーが実行**: Phase 0 はリーダー（Claude Code）が自ら実行。opencode に委譲するのはタスク実行のみ
7. **リーダーは実装しない**: リーダーの役割は計画・調整・監視。実装はエージェント（opencode）が担当。リーダーが直接コードを書くのはユーザー承認後の代行時のみ
8. **Phase順序は絶対**: Phase 0→1→2→3 の順序を飛ばさない。Wave内のステップ（1-1→1-2→1-3→1-4→1-5）も飛ばさない
9. **全Wave完走が必須**: 最終Waveのreviewerを含め、task-list.jsonで定義した全Waveをスポーン・完了させる。「効率化」のためにWaveを省略しない
