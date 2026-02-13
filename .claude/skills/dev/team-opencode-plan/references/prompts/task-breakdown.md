# Task Breakdown Prompt

opencode run で使用するタスク分解プロンプト。Phase 0-3 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{story_analysis}` | story-analysis.json の内容 | `{plan_dir}/story-analysis.json` |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Phase 0-0 で取得） |
| `{designSystemRefs}` | design system 参照情報 | DESIGN.md または design token 定義 |

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
| `opencodePrompt` | string | opencode に渡す**具体的な実装指示**。ファイルパス・操作内容・期待結果を含む |

### FORBIDDEN フィールド（これらが存在したら不合格）

| フィールド | 理由 |
|-----------|------|
| `title` | `name` と重複。`name` を使う |
| `acceptanceCriteria` | `opencodePrompt` に含める |
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

## プロンプト

```
Based on the story analysis, perform the following:

1. **Explore the codebase** to identify:
   - Target files (components, pages, utilities related to the story)
   - Current implementation status and issues
   - Design system patterns (CSS variables, class naming conventions from {designSystemRefs})
   - Existing tests and documentation

2. **Break down into detailed tasks** following this STRICT schema:

   Each task MUST have exactly these 8 fields (no more, no less):
   - id: "task-{wave}-{seq}" format (e.g. "task-1-1")
   - name: short descriptive name
   - role: role name from story-analysis.json
   - description: purpose and background
   - needsPriorContext: boolean (Wave 1 tasks should be false)
   - inputs: array of input file paths ([] if none)
   - outputs: array of output file paths ([] if none)
   - opencodePrompt: CONCRETE implementation instruction with specific file paths, operations, and expected results

   FORBIDDEN fields (do NOT include): title, acceptanceCriteria, context, deliverables

   opencodePrompt requirements:
   - Must reference specific file paths
   - Must describe the exact changes to make
   - Must be executable as a single opencode call
   - Must NOT be vague like "implement the feature" or "fix the bug"

3. **Output** the file {plan_dir}/task-list.json

## Story Analysis
{story_analysis}

## Design System References
{designSystemRefs}

## Output Format
Write the file {plan_dir}/task-list.json with this structure:
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
          "opencodePrompt": "src/styles/tokens.css を開き、:root ブロックに以下のCSS変数を追加してください:\n--color-card-bg: #ffffff\n--color-card-border: #e5e7eb\n--spacing-card: 1.5rem\n既存の変数と命名規則を揃えてください。"
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
          "opencodePrompt": "src/components/Card/Card.tsx を新規作成してください。\nPropsは { title: string; children: React.ReactNode } です。\nsrc/styles/tokens.css のCSS変数 --color-card-bg, --color-card-border, --spacing-card を使い、Tailwind v4 の変数ショートハンド構文 bg-(--color-card-bg) 形式でスタイリングしてください。\nindex.ts でnamed exportしてください。"
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
          "opencodePrompt": "以下のファイルをレビューしてください:\n1. src/styles/tokens.css - CSS変数の命名規則・値の妥当性\n2. src/components/Card/Card.tsx - コンポーネント設計・アクセシビリティ・Tailwind記法\n\n改善候補を重要度(高/中/低)付きで報告してください。"
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
