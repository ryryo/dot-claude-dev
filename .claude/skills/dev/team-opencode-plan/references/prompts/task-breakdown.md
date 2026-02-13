# Task Breakdown Prompt

opencode run で使用するタスク分解プロンプト。Phase 0-3 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{story_analysis}` | story-analysis.json の内容 | `{plan_dir}/story-analysis.json` |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Phase 0-0 で取得） |
| `{designSystemRefs}` | design system 参照情報 | DESIGN.md または design token 定義 |

## プロンプト

```
Based on the story analysis, perform the following:

1. **Explore the codebase** to identify:
   - Target files (components, pages, utilities related to the story)
   - Current implementation status and issues
   - Design system patterns (CSS variables, class naming conventions from {designSystemRefs})
   - Existing tests and documentation

2. **Break down into detailed tasks** by role:
   - Each task MUST be completable in a single opencode call
   - Include specific file paths in inputs/outputs
   - opencodePrompt should be a concrete, actionable instruction

3. **Output** the file {plan_dir}/task-list.json with this structure:

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
    "roles": [],
    "ocModel": ""
  }
}
```
