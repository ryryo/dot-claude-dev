---
name: dev:story
description: |
  ストーリーからTDD/E2E/TASK分岐付きタスクリスト（TODO.md）を生成。
  ストーリー駆動開発の起点となるスキル。
  「タスクを作成」「/dev:story」で起動。

  Trigger:
  タスクを作成, ストーリーからタスク, /dev:story, story to tasks
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# ストーリー → タスク生成（dev:story）

## 概要

ユーザーストーリーから実装可能なタスクリスト（TODO.md）を生成する。
各タスクにはTDD/E2E/TASKラベルを自動付与し、Worktree内での独立した開発を支援する。

## 3分類の定義

| カテゴリ | 対象 | ワークフロー | ステップ数 |
|----------|------|--------------|------------|
| **TDD** | ロジック、バリデーション、計算 | RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT | 6 |
| **E2E** | UIコンポーネント、レイアウト | IMPL→AUTO→CHECK→COMMIT | 4 |
| **TASK** | 設定、セットアップ、インフラ、ドキュメント | EXEC→VERIFY→COMMIT | 3 |

## 入力

- ユーザーからの会話（ストーリー説明）
- または docs/USER_STORIES.md
- feature-slug, story-slug（AskUserQuestionで確定）

## 出力 【3ファイル必須】

**⚠️ 以下の3ファイルは必ずWriteツールで保存すること**

`docs/features/{feature-slug}/{story-slug}/` に保存:

| ファイル | 内容 | 保存タイミング |
|----------|------|---------------|
| `story-analysis.json` | ストーリー分析結果 | Phase 1完了時 |
| `task-list.json` | タスクリスト（分類前） | Phase 2完了時 |
| `TODO.md` | TDD/E2E/TASKラベル付きタスク | Phase 3完了時 |

---

## ワークフロー

```
Phase 1: ストーリー理解・slug確定
    → agents/analyze-story.md [opus]
    → AskUserQuestionでslug確定 ※必須
    → 【Write】story-analysis.json 保存
        ↓
Phase 2: タスク分解
    → agents/decompose-tasks.md [sonnet]
    → AskUserQuestionで不明点確認（技術選定・方針等） ※必要に応じて
    → 【Write】task-list.json 保存
        ↓
Phase 3: TDD/E2E/TASK分類
    → agents/assign-workflow.md [haiku]
    → 【Write】TODO.md 保存
        ↓
Phase 4: ユーザー確認
    → AskUserQuestion で確認・承認
```

---

## Phase 1: ストーリー理解・slug確定

### 1.1 ストーリー取得

ユーザーからストーリーを聞き取る、または既存ファイルを読み込む。

```javascript
// USER_STORIES.md が存在すれば読み込み
Read({ file_path: "docs/USER_STORIES.md" })
```

### 1.2 ストーリー分析

```javascript
Task({
  description: "ストーリー分析",
  prompt: `ストーリーを分析し、以下を抽出してください:
- 目的・ゴール
- スコープ（対象範囲）
- 受入条件
- feature-slug候補（3つ）
- story-slug候補（3つ）

出力形式: JSON
`,
  subagent_type: "general-purpose",
  model: "opus"
})
```

→ 詳細: [agents/analyze-story.md](.claude/skills/dev/story/agents/analyze-story.md)

### 1.3 slug確定

AskUserQuestionでslug候補を提示し、ユーザーに選択してもらう:

```javascript
AskUserQuestion({
  questions: [
    {
      question: "feature-slugを選択してください",
      header: "Feature",
      options: [
        // analyze-story.mdの出力から動的に生成
        { label: "user-auth", description: "ユーザー認証機能" },
        { label: "dashboard", description: "ダッシュボード機能" },
        { label: "settings", description: "設定機能" }
      ],
      multiSelect: false
    },
    {
      question: "story-slugを選択してください",
      header: "Story",
      options: [
        // analyze-story.mdの出力から動的に生成
        { label: "login-form", description: "ログインフォーム実装" },
        { label: "validation", description: "バリデーション追加" },
        { label: "error-handling", description: "エラーハンドリング" }
      ],
      multiSelect: false
    }
  ]
})
```

**ポイント**:
- 既存のfeature-slugがあれば優先的に提示
- 「その他」で自由入力も可能

### 1.4 出力ディレクトリ作成

```bash
mkdir -p docs/features/{feature-slug}/{story-slug}
```

### 1.5 story-analysis.json 保存 【必須】

**⚠️ 必ずWriteツールで保存すること**

```javascript
Write({
  file_path: "docs/features/{feature-slug}/{story-slug}/story-analysis.json",
  content: JSON.stringify({
    goal: "目的",
    scope: "スコープ",
    acceptanceCriteria: ["受入条件1", "受入条件2"],
    featureSlug: "feature-slug",
    storySlug: "story-slug"
  }, null, 2)
})
```

**チェックポイント**: ファイルが存在することを確認してから次のPhaseへ進む。

---

## Phase 2: タスク分解

```javascript
Task({
  description: "タスク分解",
  prompt: `story-analysis.jsonを読み込み、ストーリーを実装可能なタスクに分解してください。

【必須】タスク分解の前に、対象ファイルをGlob/Read等で探索し、
現在のコード構造（シグネチャ、型、関連モジュール、既存テスト）を把握すること。

出力のtask-list.jsonには以下を含める:
- context: 対象ファイルパス、現在のシグネチャ、関連モジュール、既存テスト（必須）
- tasks: 各タスク（名前、説明、filesフィールド（パスと操作）、入出力、依存関係）

出力形式: JSON
`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

→ 詳細: [agents/decompose-tasks.md](.claude/skills/dev/story/agents/decompose-tasks.md)

### 2.2 タスク作成前の確認 【必須】

タスク分解エージェントの結果を保存する前に、タスクを作成するうえで判断が必要な事項をAskUserQuestionで確認する。

**確認すべき事項の例**:
- 使用するライブラリ・フレームワークの選定
- アーキテクチャや設計方針
- スコープの境界（どこまで含めるか）
- 既存コードとの整合性や制約

```javascript
AskUserQuestion({
  questions: [
    // ストーリー分析から判断が必要な事項を動的に生成
    // 例:
    {
      question: "バリデーションにはどのライブラリを使いますか？",
      header: "技術選定",
      options: [
        { label: "Zod", description: "TypeScriptファーストのスキーマバリデーション" },
        { label: "Yup", description: "既存プロジェクトで使用中" }
      ],
      multiSelect: false
    }
  ]
})
```

**ポイント**:
- 確認不要（自明）な場合はスキップしてよい
- 回答を踏まえてタスク分解を調整する

### 出力: task-list.json 【必須】

**⚠️ 必ずWriteツールで保存すること**

**⚠️ contextセクション必須**: 後続エージェント（dev:developing）がこのファイルだけで作業開始できるよう、対象ファイルパス・現在のシグネチャ・関連モジュール・既存テスト情報を含めること。

```javascript
Write({
  file_path: "docs/features/{feature-slug}/{story-slug}/task-list.json",
  content: JSON.stringify({
    context: {
      description: "ストーリーの技術的説明",
      targetFiles: { "src/path/to/file.ts": "現状と変更内容" },
      existingTests: { "src/path/to/file.test.ts": "更新要否" },
      relatedModules: { "storeName": "役割と関係" },
      currentSignatures: { "functionName": "現在のシグネチャ" }
    },
    tasks: [
      { id: 1, name: "タスク名", description: "何をするかの説明", files: { "src/path/to/file.ts": "new or edit" }, dependencies: [] }
    ]
  }, null, 2)
})
```

---

## Phase 3: TDD/E2E/TASK分類

```javascript
Task({
  description: "TDD/E2E/TASK分類",
  prompt: `task-list.jsonを読み込み、各タスクをTDD/E2E/TASKに分類してください。

判定基準:
- TDD: 入出力が明確、アサーションで検証可能、ロジック層
- E2E: 視覚的確認が必要、UX判断、プレゼンテーション層
- TASK: テスト不要、UI検証不要、セットアップ/設定タスク

出力形式: Markdown（TODO.md形式）
`,
  subagent_type: "general-purpose",
  model: "haiku"
})
```

→ 詳細: [agents/assign-workflow.md](.claude/skills/dev/story/agents/assign-workflow.md)
→ 判定基準: [references/tdd-criteria.md](.claude/skills/dev/story/references/tdd-criteria.md) | [references/e2e-criteria.md](.claude/skills/dev/story/references/e2e-criteria.md) | [references/task-criteria.md](.claude/skills/dev/story/references/task-criteria.md)

### 出力: TODO.md 【必須】

**⚠️ 必ずWriteツールで保存すること**

```javascript
Write({
  file_path: "docs/features/{feature-slug}/{story-slug}/TODO.md",
  content: `# TODO

## フェーズ1: 環境セットアップ

### TASKタスク
- [ ] [TASK][EXEC] TypeScript環境構築
- [ ] [TASK][VERIFY] ビルド確認

## フェーズ2: ユーザー認証機能

### TDDタスク
- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング

### E2Eタスク
- [ ] [E2E][IMPL] LoginForm UIコンポーネント
- [ ] [E2E][AUTO] agent-browser検証

### 共通
- [ ] [CHECK] lint/format/build
`
})
```

**チェックポイント**: 3ファイルすべてが保存されていることを確認。

---

## Phase 4: ユーザー確認

```javascript
AskUserQuestion({
  questions: [{
    question: "タスクリストを確認してください。問題なければ実装を開始しますか？",
    header: "確認",
    options: [
      { label: "実装開始", description: "dev:developingで実装を開始" },
      { label: "修正が必要", description: "タスクを調整" }
    ],
    multiSelect: false
  }]
})
```

**「実装開始」を選択された場合**:
- dev:developingスキルを呼び出し

**「修正が必要」を選択された場合**:
- ユーザーの指示に従ってTODO.mdを修正
- 再度確認

---

## 完了条件

### 必須出力ファイル（3点セット）

以下のファイルがすべて `docs/features/{feature-slug}/{story-slug}/` に保存されていること：

| ファイル | 内容 | Phase |
|----------|------|-------|
| `story-analysis.json` | ストーリー分析結果（目的、スコープ、受入条件） | Phase 1 |
| `task-list.json` | タスクリスト（分類前） | Phase 2 |
| `TODO.md` | TDD/E2E/TASKラベル付きタスクリスト | Phase 3 |

### チェックリスト

- [ ] story-analysis.json がWriteツールで保存された
- [ ] task-list.json がWriteツールで保存された
- [ ] TODO.md がWriteツールで保存された
- [ ] 各タスクにTDD/E2E/TASKラベルが付与された
- [ ] ユーザーが承認した

## 関連スキル

- **dev:developing**: TDD/E2E/TASKタスクの実装
- **dev:feedback**: 実装後のフィードバック

## 参照ルール

実装時は `.claude/rules/workflow/workflow-branching.md` が自動適用される（TDD/E2E/TASK分岐判定）。
