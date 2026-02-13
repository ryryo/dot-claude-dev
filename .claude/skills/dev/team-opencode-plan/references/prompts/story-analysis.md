# Story Analysis Prompt

opencode run で使用するストーリー分析プロンプト。Phase 0-2 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{user_story}` | ユーザーのストーリー/指示 | ユーザー入力 |
| `{role_catalog}` | role-catalog.md の内容 | `references/role-catalog.md` |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Phase 0-0 で取得） |

## プロンプト

```
Analyze the following story/instructions and produce a story-analysis.json.

## User Story
{user_story}

## Available Roles
{role_catalog}

## Output Format
Write the file {plan_dir}/story-analysis.json with this structure:
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

## Rules
- The final wave MUST include a reviewer role
- Use blockedBy to express sequential dependencies between waves
- Roles within the same wave run in parallel
```
