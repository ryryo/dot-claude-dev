# Task Breakdown Prompt

opencode run で使用するタスク分解プロンプト。Phase 0-3 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{story_analysis}` | story-analysis.json の内容 | `{plan_dir}/story-analysis.json` |
| `{codebase_context}` | リーダーが収集したコンテキスト情報 | Glob/Grep/Read で収集 |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Phase 0-0 で取得） |

## プロンプト

```
Break down the following story into tasks for team execution.

## Story Analysis
{story_analysis}

## Codebase Context
{codebase_context}

## Rules
- Each task MUST be completable in a single opencode call
- Include specific file paths in inputs/outputs
- opencodePrompt should be a concrete, actionable instruction

## Output Format
Write the file {plan_dir}/task-list.json with this structure:
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
    "roles": [],
    "ocModel": ""
  }
}
```
