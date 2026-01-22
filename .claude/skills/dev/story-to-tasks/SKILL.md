---
name: dev:story-to-tasks
description: |
  ストーリーからTDD/E2E分岐付きタスクリスト（TODO.md）を生成。
  Worktree作成後、最初に実行するスキル。
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

# ストーリー → タスク生成（dev:story-to-tasks）

## 概要

ユーザーストーリーから実装可能なタスクリスト（TODO.md）を生成する。
各タスクにはTDD/E2Eラベルを自動付与し、Worktree内での独立した開発を支援する。

## 入力

- ユーザーからの会話（ストーリー説明）
- または docs/USER_STORIES.md
- feature-slug, story-slug（AskUserQuestionで確定）

## 出力

`docs/features/{feature-slug}/stories/{story-slug}/` に以下を保存:
- `story-analysis.json` - ストーリー分析結果
- `task-list.json` - タスクリスト
- `TODO.md` - TDD/E2Eラベル付きタスク

---

## ワークフロー

```
Phase 1: ストーリー理解・slug確定
    → agents/analyze-story.md [opus]
    → AskUserQuestionでslug確定
    → story-analysis.json 出力
        ↓
Phase 2: タスク分解
    → agents/decompose-tasks.md [sonnet]
    → task-list.json 出力
        ↓
Phase 3: TDD/E2E分類
    → agents/classify-tdd-e2e.md [haiku]
    → TODO.md 出力
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

→ 詳細: [agents/analyze-story.md](.claude/skills/dev/story-to-tasks/agents/analyze-story.md)

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
mkdir -p docs/features/{feature-slug}/stories/{story-slug}
```

### 1.5 story-analysis.json 保存

```javascript
Write({
  file_path: "docs/features/{feature-slug}/stories/{story-slug}/story-analysis.json",
  content: JSON.stringify(analysisResult, null, 2)
})
```

---

## Phase 2: タスク分解

```javascript
Task({
  description: "タスク分解",
  prompt: `story-analysis.jsonを読み込み、ストーリーを実装可能なタスクに分解してください。

各タスクには以下を含める:
- タスク名
- 説明
- 入出力（明確な場合）
- 依存関係

出力形式: JSON
`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

→ 詳細: [agents/decompose-tasks.md](.claude/skills/dev/story-to-tasks/agents/decompose-tasks.md)

### 出力: task-list.json

```javascript
Write({
  file_path: "docs/features/{feature-slug}/stories/{story-slug}/task-list.json",
  content: JSON.stringify(taskList, null, 2)
})
```

---

## Phase 3: TDD/E2E分類

```javascript
Task({
  description: "TDD/E2E分類",
  prompt: `task-list.jsonを読み込み、各タスクをTDD/E2Eに分類してください。

判定基準:
- TDD: 入出力が明確、アサーションで検証可能、ロジック層
- E2E: 視覚的確認が必要、UX判断、プレゼンテーション層

出力形式: Markdown（TODO.md形式）
`,
  subagent_type: "general-purpose",
  model: "haiku"
})
```

→ 詳細: [agents/classify-tdd-e2e.md](.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md)
→ 判定基準: [references/tdd-criteria.md](.claude/skills/dev/story-to-tasks/references/tdd-criteria.md) | [references/e2e-criteria.md](.claude/skills/dev/story-to-tasks/references/e2e-criteria.md)

### 出力: TODO.md

```markdown
# TODO

## フェーズ1: ユーザー認証機能

### TDDタスク
- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング

### E2Eタスク
- [ ] [E2E][IMPL] LoginForm UIコンポーネント
- [ ] [E2E][AUTO] agent-browser検証

### 共通
- [ ] [CHECK] lint/format/build
```

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

- [ ] story-analysis.jsonが生成された
- [ ] task-list.jsonが生成された
- [ ] TODO.mdが生成された
- [ ] 各タスクにTDD/E2Eラベルが付与された
- [ ] ユーザーが承認した

## 関連スキル

- **dev:developing**: TDD/E2Eタスクの実装
- **dev:feedback**: 実装後のフィードバック

## 参照ルール

実装時は `.claude/rules/workflow/tdd-e2e-branching.md` が自動適用される。
