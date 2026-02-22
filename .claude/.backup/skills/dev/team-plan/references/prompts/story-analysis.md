# Story Analysis 手順書

リーダー（Claude Code）が直接実行するストーリー分析手順。Phase 0-2 で使用。

## 変数

| 変数 | 説明 | 値の取得元 |
|------|------|-----------|
| `{user_story}` | ユーザーのストーリー/指示 | ユーザー入力 |
| `{role_catalog}` | role-catalog.md の内容 | `references/role-catalog.md` |
| `{plan_dir}` | 計画ディレクトリパス | `$PLAN_DIR`（Phase 0-0 で取得） |
| `{template}` | 選択されたチーム構成テンプレート | `references/team-templates/*.json`（Phase 0-1 で選択、カスタムの場合は空） |

## 実行手順

### Step 1: コードベース探索

ストーリーに関連するコードベースの構造を把握する:

1. **Glob** でプロジェクト構造を確認（`src/**/*.{ts,tsx}`, `app/**/*.php` 等）
2. **Grep** でストーリーに関連するキーワードを検索
3. **Read** で関連ファイルの内容を確認
4. 既存の DESIGN.md があれば Read で読み込む

### Step 2: ストーリー分析

以下の観点でユーザーのストーリー/指示を分析する:

**ユーザーストーリー**: {user_story}

**利用可能なロール**: {role_catalog}

**テンプレート（選択済みの場合）**: {template}

分析観点:
1. **ゴール**: ストーリーが達成しようとしていること
2. **スコープ**: 含まれるもの / 含まれないもの
3. **受入条件**: 完了の定義
4. **チーム設計**: テンプレートをベースに、ストーリーに合わせてロールとWave構造を決定

### Step 3: story-analysis.json の出力

Write ツールで `{plan_dir}/story-analysis.json` を出力する。

## 出力スキーマ

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
    "qualityGates": ["最終Waveにレビュワー配置"],
    "fileOwnership": {}
  }
}
```

## ルール

- 最終Waveには必ず `reviewer` ロールを配置する
- Wave間の `blockedBy` で直列依存を明示する
- 同一Wave内のロールは並行実行される
- テンプレートが選択されている場合、そのロール構成・Wave構造・fileOwnership をベースに調整する
- テンプレートは強制ではなく推奨デフォルト。ストーリーに合わせて自由に変更可能
