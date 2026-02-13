---
name: dev:team-opencode-plan
description: |
  opencode活用のチーム実装計画を作成。ストーリー分析→タスク分解→レビュー→ユーザー承認。
  計画は docs/features/team-opencode/{YYMMDD}_{slug}/ に永続化され、複数保持可能。

  Trigger:
  dev:team-opencode-plan, /dev:team-opencode-plan, dev:team-opencode, チーム計画, team plan
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# チーム実行計画の作成（dev:team-opencode-plan）

## 概要

ストーリーまたは直接指示を受け取り、opencode を活用して計画フェーズ（ストーリー分析・タスク分解・レビュー）を実行する。リーダーはコンテキスト収集と検証・修正を担当する。計画は `docs/features/team-opencode/{YYMMDD}_{slug}/` に永続化され、複数の計画を保持できる。

承認済み計画の実行は `dev:team-opencode-exec` で行う。

## 必須リソース

| リソース                               | 読み込みタイミング            | 用途                 |
| -------------------------------------- | ----------------------------- | -------------------- |
| `references/role-catalog.md`           | Phase 0-2（ロール設計時）     | ロール定義の参照     |
| `references/prompts/story-analysis.md` | Phase 0-2（ストーリー分析時） | opencode用プロンプト |
| `references/prompts/task-breakdown.md` | Phase 0-3（タスク分解時）     | opencode用プロンプト |
| `references/prompts/task-review.md`    | Phase 0-4（タスクレビュー時） | opencode用プロンプト |
| `references/templates/*.json`          | Phase 0-0（初期化時）         | テンプレート雛形     |

## 計画出力先

```
docs/features/team-opencode/{YYMMDD}_{slug}/
├── story-analysis.json    # ストーリー分析（ゴール、スコープ、受入条件、チーム設計）
├── task-list.json         # ロールごとのタスク定義（Wave構造 + ロール割当、承認済み）
└── prompts/               # 各ロールの opencode 実行プロンプト（自動生成）
```

命名規則: `{YYMMDD}_{slug}`（YYMMDD: 作成日、slug: kebab-case 英数字+ハイフン、最大40文字）

---

## Phase 0: 計画（リーダー + opencode 協調）

### 0-0: ワークスペース初期化

1. ユーザーにストーリー/指示を聞く
2. ストーリータイトルから slug 候補を2-3個生成（kebab-case、英語、最大40文字）
3. AskUserQuestion で候補を提示し、ユーザーが選択（カスタム入力も可）
4. 選択された slug で初期化スクリプトを実行:

```bash
PLAN_DIR=$(bash .claude/skills/dev/team-opencode-plan/scripts/init-team-workspace.sh {slug})
```

`$PLAN_DIR` を以降のすべてのステップでファイルパスとして使用する。

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

### 0-2: ストーリー分析 → story-analysis.json（opencode実行）

1. ユーザーのストーリー/指示を整理する
2. `references/role-catalog.md` を Read で読み込む
3. `references/prompts/story-analysis.md` を Read で読み込み、変数を置換して opencode run を実行:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{user_story}` | ユーザー入力 |
| `{role_catalog}` | `references/role-catalog.md` の内容 |
| `{plan_dir}` | `$PLAN_DIR`（0-0 で取得） |

```bash
opencode run -m $OC_MODEL "{story-analysis.md の変数置換済みプロンプト}"
```

4. 出力された `$PLAN_DIR/story-analysis.json` を Read で読み込み、構造を検証する
5. 不備があればリーダーが修正する

**ルール**:

- 最終Waveには必ず `reviewer` ロールを配置する
- Wave間の `blockedBy` で直列依存を明示する
- 同一Wave内のロールは並行実行される

### 0-3: コード探索＆タスク分解 → task-list.json（opencode実行）

1. リーダーが対象コードベースを探索（Glob, Grep, Read）し、コンテキスト情報を収集する
2. `references/prompts/task-breakdown.md` を Read で読み込み、変数を置換して opencode run を実行:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{story_analysis}` | `$PLAN_DIR/story-analysis.json` の内容 |
| `{codebase_context}` | リーダーが収集したコンテキスト情報 |
| `{plan_dir}` | `$PLAN_DIR`（0-0 で取得） |

```bash
opencode run -m $OC_MODEL "{task-breakdown.md の変数置換済みプロンプト}"
```

3. 出力された `$PLAN_DIR/task-list.json` を Read で読み込み、構造とタスク粒度を検証する
4. 不備があればリーダーが修正する

### 0-4: opencode でタスクレビュー

タスク分解の品質を opencode で検証する。`references/prompts/task-review.md` を Read で読み込み、変数を置換して実行。**モデルは `openai/gpt-5.3-codex` 固定**（`$OC_MODEL` ではない）:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{story_analysis}` | `$PLAN_DIR/story-analysis.json` の内容 |
| `{task_list}` | `$PLAN_DIR/task-list.json` の内容 |

```bash
opencode run -m openai/gpt-5.3-codex "{task-review.md の変数置換済みプロンプト}"
```

**判定**:

- `APPROVED` → 0-5 へ
- `NEEDS_REVISION` → task-list.json を修正 → 再レビュー（最大3回）
- 3回失敗 → 現状のままユーザーに提示し判断を仰ぐ

**注意**: codex の提案をそのまま適用するのではなく、リーダーが妥当性を判断してから適用する。

### 0-5: ユーザー承認

1. `$PLAN_DIR/task-list.json` の metadata に `ocModel` を記録する:

```json
{
  "metadata": {
    "totalTasks": 5,
    "totalWaves": 3,
    "roles": ["frontend-developer", "reviewer"],
    "ocModel": "{$OC_MODEL}"
  }
}
```

2. task-list.json を整形し、AskUserQuestion でユーザーに提示:

```
Q: 以下の計画でAgent Teamsを実行します。承認しますか？

【計画パス】 {$PLAN_DIR}
【チーム構成】 {ロール一覧}
【Wave構造】 {Wave 1}: {並行ロール} → {Wave 2}: {並行ロール} → ...
【タスク数】 {totalTasks}タスク / {totalWaves} Wave
【モデル】 {$OC_MODEL}

選択肢:
- 承認（dev:team-opencode-exec で実行可能）
- 修正が必要（Phase 0-2 に戻る）
```

**ゲート**: ユーザー承認後、「`dev:team-opencode-exec` を実行して計画を実行してください」と案内する。

---

## 重要な注意事項

1. **opencode コマンドは決め打ち**: プロンプトテンプレートのコマンドをリーダーが改変しない
2. **フォールバック禁止**: opencode 失敗時に直接実装しない。リトライのみ（最大3回）
3. **計画もopencode活用**: Phase 0 のストーリー分析（0-2）、タスク分解（0-3）、レビュー（0-4）は opencode で実行。リーダーはコンテキスト収集・検証・修正を担当
4. **リーダーは実装しない**: リーダーの役割は計画・調整。実装はエージェント（opencode）が担当
5. **Phase順序は絶対**: Phase 0-0→0-1→0-2→0-3→0-4→0-5 の順序を飛ばさない
