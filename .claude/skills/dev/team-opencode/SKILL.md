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

| リソース | 読み込みタイミング | 用途 |
|----------|-------------------|------|
| `references/agent-prompt-template.md` | Phase 1-3（エージェントスポーン前） | 統一エージェントプロンプト |
| `references/role-catalog.md` | Phase 0-2（ロール設計時） | ロール定義の参照 |
| `references/templates/*.json, *.md` | Phase 0-0（初期化時） | テンプレート雛形 |

**⚠️ エージェントスポーン時、必ず `agent-prompt-template.md` を Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

## 一時計画フォルダ

```
docs/features/team-opencode/
├── story-analysis.json    # ストーリー分析（ゴール、スコープ、受入条件、チーム設計）
├── task-list.json         # ロールごとのタスク定義（Wave構造 + ロール割当）
├── TODO.md                # 実行順序（Wave + ロール + ステップ）
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

### 0-4: TODO.md 生成

task-list.json から `docs/features/team-opencode/TODO.md` を生成:

```markdown
# TODO: {タスクタイトル}

## Wave 1: {Wave説明}

### {ロール名}

- [ ] [TEAM][EXEC] task-1-1: {タスク名}
- [ ] [TEAM][VERIFY] 成果物確認: {出力ファイル}

## Wave 2: {Wave説明}（Wave 1 完了後）

### {ロール名}

- [ ] [TEAM][EXEC] task-2-1: {タスク名}
- [ ] [TEAM][VERIFY] 成果物確認: {出力ファイル}
```

### 0-5: opencode codex でタスクレビュー

タスク分解の品質を opencode の codex モデルで検証する。

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
- `APPROVED` → 0-6 へ
- `NEEDS_REVISION` → task-list.json / TODO.md を修正 → 再レビュー（最大3回）
- 3回失敗 → 現状のままユーザーに提示し判断を仰ぐ

**注意**: codex の提案をそのまま適用するのではなく、リーダーが妥当性を判断してから適用する。

### 0-6: ユーザー承認

計画をユーザーに提示:

```
以下の計画でAgent Teamsを実行します:

## チーム構成
{ロール一覧}

## Wave構造
{Wave 1}: {並行ロール} → {Wave 2}: {並行ロール} → ...

## タスク一覧
{TODO.md の内容}

モデル: {$OC_MODEL}

実行してよいですか？
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

⚠️ **必須**: テンプレートの文言を改変・省略・要約しない。変数（`{...}`）のみ置換する。

### 1-4: 完了待機

TaskList を定期的に確認し、現在のWaveの全タスク完了を待つ。

**タイムアウト**: エージェントが5分以上 in_progress のまま変化がない場合、SendMessage で状況確認する。

### 1-5: 次Wave スポーン

現在のWaveが完了したら、次のWaveのエージェントをスポーンする（1-3 に戻る）。全Waveが完了するまで繰り返す。

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

- **対応あり** → Phase 0-2 に戻る（story-analysis.json / task-list.json / TODO.md を更新し、新Waveのエージェントをスポーン）
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

| 状況 | 対応 |
|------|------|
| opencode run エラー | 同じコマンドを最大3回リトライ |
| エージェント無応答（5分） | SendMessage で状況確認 |
| 3回リトライ失敗 | ユーザーに報告、指示を仰ぐ |
| opencode モデル利用不可 | ユーザーに報告、別モデル選択を促す |

## 重要な注意事項

1. **opencode コマンドは決め打ち**: プロンプトテンプレートのコマンドをエージェントに改変させない
2. **フォールバック禁止**: opencode 失敗時に直接実装しない。リトライのみ
3. **モデル固定**: 選択されたモデルを全エージェントで統一
4. **CC側はhaiku**: コスト最小化。実装はopencode側が担当
5. **越境防止**: 各エージェントは自分のタスク以外に手を出さない
6. **計画はリーダーが実行**: Phase 0 はリーダー（Claude Code）が自ら実行。opencode に委譲するのはタスク実行のみ
