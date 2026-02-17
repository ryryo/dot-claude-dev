# Task Review Prompt

opencode run で使用するタスクレビュープロンプト。Phase 0-4 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{story_analysis}` | story-analysis.json の内容 | `{plan_dir}/story-analysis.json` |
| `{task_list}` | task-list.json の内容 | `{plan_dir}/task-list.json` |

## プロンプト

```
Review this team task breakdown:

## Story Analysis
{story_analysis}

## Task List
{task_list}

Analyze:
1. Task granularity - Each task should be completable in a single opencode call
2. Wave dependencies - inputs/outputs consistent across waves?
3. Role assignment - Does each task match its assigned role?
4. Missing tasks - Setup, error handling, edge cases?
5. Risk - External dependencies, technical unknowns?
6. Schema compliance - All 8 required fields present? No forbidden fields?
7. opencodePrompt quality - Concrete instructions with file paths and operations?
8. Reviewer constraint - reviewer/tester tasks' opencodePrompt MUST start with "IMPORTANT: Do NOT modify any files." and their outputs MUST be empty []

Respond with:
- APPROVED or NEEDS_REVISION
- Top 3-5 recommendations (if NEEDS_REVISION)
- Suggested modifications as JSON patches to task-list.json
```
