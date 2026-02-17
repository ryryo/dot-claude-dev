# Task Breakdown 手順書

リーダー（Claude Code）が直接実行するタスク分解手順。Step 4 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{story_analysis}` | story-analysis.json の内容 | `{plan_dir}/story-analysis.json` |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Step 1 で取得） |

## タスクスキーマ契約

### REQUIRED フィールド（全タスクに必須。1つでも欠けたら不合格）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | string | 一意識別子。`"task-{wave}-{seq}"` 形式（例: `"task-1-1"`） |
| `name` | string | タスク名。短く具体的に |
| `role` | string | 担当ロール名（`role-catalog.md` のロール） |
| `description` | string | タスクの目的・背景の説明 |
| `needsPriorContext` | boolean | 前Waveの成果物を参照するか。Wave 1は原則 `false` |
| `inputs` | string[] | 入力ファイルパス。なければ空配列 `[]` |
| `outputs` | string[] | 出力ファイルパス。なければ空配列 `[]` |
| `taskPrompt` | string | Teammate に渡す**具体的な実装指示**。ファイルパス・操作内容・期待結果を含む |

### FORBIDDEN フィールド（これらが存在したら不合格）

| フィールド | 理由 |
|-----------|------|
| `title` | `name` と重複。`name` を使う |
| `acceptanceCriteria` | `taskPrompt` に含める |
| `context`（タスクレベル） | トップレベル `context` のみ使用 |
| `deliverables` | `outputs` と重複。`outputs` を使う |

### Wave 構造

```json
{
  "waves": [
    {
      "id": 1,
      "tasks": [
        { "id": "task-1-1", "role": "designer", ... },
        { "id": "task-1-2", "role": "frontend-developer", ... }
      ]
    }
  ]
}
```

- `waves[].tasks[]` フラット配列 + 各タスクの `role` フィールドでロールを指定
- 旧 `roles.{roleName}` 形式は使わない

## 実行手順

### Step 1: コードベース探索

story-analysis.json の内容に基づき、具体的なファイルパスと実装状況を把握する:

1. **Glob** で対象ファイルを特定（`src/components/**/*.tsx`, `src/styles/**/*.css` 等）
2. **Grep** で関連するコード・パターンを検索
3. **Read** で以下を確認:
   - 対象ファイルの現在の実装内容
   - デザインシステムのパターン（CSS変数、クラス命名規則）
   - DESIGN.md やデザイントークン定義がある場合はその内容
   - 既存のテスト・ドキュメント
4. 探索結果から `context` セクション（targetFiles, relatedModules, technicalNotes, designSystemRefs）の情報を収集

### Step 2: タスク分解

story-analysis.json のチーム設計（ロール・Wave構造）に基づき、具体的なタスクに分解する:

**story-analysis.json**: {story_analysis}

各タスクは以下を満たすこと:
- 8つの必須フィールドのみ（FORBIDDEN フィールドを含めない）
- `taskPrompt` は具体的な実装指示（ファイルパス・操作内容・期待結果を含む）
- `taskPrompt` は曖昧でない（「機能を実装」「バグを修正」のような指示でない）
- reviewer/tester ロールの `taskPrompt` は `"IMPORTANT: Do NOT modify any files. This is a review-only task. Report findings only."` で始め、`"コードの修正は行わないでください。"` で終える

### Step 3: task-list.json の出力

Write ツールで `{plan_dir}/task-list.json` を出力する。

## 出力スキーマ

```json
{
  "context": {
    "description": "...",
    "targetFiles": {},
    "relatedModules": {},
    "technicalNotes": {},
    "designSystemRefs": {}
  },
  "waves": [
    {
      "id": 1,
      "tasks": [
        {
          "id": "task-1-1",
          "name": "CSS変数定義の追加",
          "role": "designer",
          "description": "新規コンポーネントに必要なCSS変数をデザイントークンファイルに追加する",
          "needsPriorContext": false,
          "inputs": ["src/styles/tokens.css"],
          "outputs": ["src/styles/tokens.css"],
          "taskPrompt": "src/styles/tokens.css を開き、:root ブロックに以下のCSS変数を追加してください:\n--color-card-bg: #ffffff\n--color-card-border: #e5e7eb\n--spacing-card: 1.5rem\n既存の変数と命名規則を揃えてください。"
        }
      ]
    },
    {
      "id": 2,
      "tasks": [
        {
          "id": "task-2-1",
          "name": "Cardコンポーネント実装",
          "role": "frontend-developer",
          "description": "Wave 1で定義されたCSS変数を使ってCardコンポーネントを新規作成する",
          "needsPriorContext": true,
          "inputs": ["src/styles/tokens.css"],
          "outputs": ["src/components/Card/Card.tsx", "src/components/Card/index.ts"],
          "taskPrompt": "src/components/Card/Card.tsx を新規作成してください。\nPropsは { title: string; children: React.ReactNode } です。\nsrc/styles/tokens.css のCSS変数 --color-card-bg, --color-card-border, --spacing-card を使い、Tailwind v4 の変数ショートハンド構文 bg-(--color-card-bg) 形式でスタイリングしてください。\nindex.ts でnamed exportしてください。"
        }
      ]
    },
    {
      "id": 3,
      "tasks": [
        {
          "id": "task-3-1",
          "name": "実装レビュー",
          "role": "reviewer",
          "description": "Wave 1-2の実装をレビューし、改善候補を報告する",
          "needsPriorContext": true,
          "inputs": ["src/styles/tokens.css", "src/components/Card/Card.tsx"],
          "outputs": [],
          "taskPrompt": "IMPORTANT: Do NOT modify any files. This is a review-only task. Report findings only.\n\n以下のファイルをレビューしてください:\n1. src/styles/tokens.css - CSS変数の命名規則・値の妥当性\n2. src/components/Card/Card.tsx - コンポーネント設計・アクセシビリティ・Tailwind記法\n\n改善候補を重要度(高/中/低)付きで報告してください。コードの修正は行わないでください。"
        }
      ]
    }
  ],
  "metadata": {
    "totalTasks": 3,
    "totalWaves": 3,
    "roles": ["designer", "frontend-developer", "reviewer"],
    "ocModel": ""
  }
}
```
