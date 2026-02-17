---
name: dev:team-plan
description: |
  チーム実装計画を作成。ストーリー分析→タスク分解→レビュー（opencode）。
  計画は docs/features/team/{YYMMDD}_{slug}/ に永続化され、複数保持可能。

  Trigger:
  dev:team-plan, /dev:team-plan, チーム計画, team plan
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# チーム実行計画の作成（dev:team-plan）

## 概要

ユーザーストーリーまたは直接指示を受け取り、計画フェーズ（ストーリー分析・タスク分解）を実行し、レビューのみ opencode を活用する。計画は `docs/features/team/{YYMMDD}_{slug}/` に永続化され、複数の計画を保持できる。

承認済み計画の実行は `dev:team-opencode-exec` で行う。

## 必須リソース

| リソース                               | 読み込みタイミング          | 用途                           |
| -------------------------------------- | --------------------------- | ------------------------------ |
| `references/role-catalog.md`           | Step 3（ロール設計時）      | ロール定義の参照               |
| `references/prompts/story-analysis.md` | Step 3（ストーリー分析時）  | ストーリー分析の手順書         |
| `references/prompts/task-breakdown.md` | Step 4（タスク分解時）      | タスク分解の手順書             |
| `references/prompts/task-review.md`    | Step 5（タスクレビュー時）  | opencode 用プロンプト          |
| `references/team-templates/*.json`     | Step 2（テンプレート選択時）| チーム構成テンプレート         |
| `references/templates/*.json`          | Step 1（初期化時）          | テンプレート雛形               |

## 計画出力先

```
docs/features/team/{YYMMDD}_{slug}/
├── story-analysis.json    # ストーリー分析（ゴール、スコープ、受入条件、チーム設計）
└── task-list.json         # ロールごとのタスク定義（Wave構造 + ロール割当、各タスクに opencodePrompt 含む）
```

命名規則: `{YYMMDD}_{slug}`（YYMMDD: 作成日、slug: kebab-case 英数字+ハイフン、最大40文字）

---

## ステップ

### Step 1: ワークスペース初期化

1. ユーザーにストーリー/指示を聞く
2. ストーリータイトルから slug 候補を2-3個生成（kebab-case、英語、最大40文字）
3. AskUserQuestion で候補を提示し、ユーザーが選択（カスタム入力も可）
4. 選択された slug で初期化スクリプトを実行:

```bash
PLAN_DIR=$(bash .claude/skills/dev/team-plan/scripts/init-team-workspace.sh {slug})
```

`$PLAN_DIR` を以降のすべてのステップでファイルパスとして使用する。

### Step 2: テンプレート選択

AskUserQuestion でチーム構成テンプレートを選択:

```
Q: チーム構成テンプレートを選択してください。
選択肢（※ストーリーの内容に応じて最適なテンプレートを推奨すること）:
- feature-dev: 設計→実装→レビューの3Wave構成
- refactor: 設計→実装→テストの3Wave構成
- investigation: researcher×3の競合仮説調査
- tdd-focused: TDD開発→レビュー
- frontend-only: デザイン→フロント実装→レビュー
- カスタム: テンプレートなしでゼロから設計
```

- テンプレート選択時: `references/team-templates/{name}.json` を Read で読み込み、そのロール構成・Wave構造・ファイル所有権をストーリー分析のヒントとして使用する。テンプレートは強制ではなく推奨デフォルト
- カスタム選択時: 従来通りゼロからチーム構成を設計

### Step 3: ストーリー分析 → story-analysis.json

リーダー（Claude Code）が Glob/Grep/Read/Write を使って直接実行する。

1. ユーザーのストーリー/指示を整理する
2. `references/role-catalog.md` を Read で読み込む
3. `references/prompts/story-analysis.md` を Read で読み込み、手順書に従って実行:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{user_story}` | ユーザー入力 |
| `{role_catalog}` | `references/role-catalog.md` の内容 |
| `{plan_dir}` | `$PLAN_DIR`（Step 1 で取得） |
| `{template}` | Step 2 で選択したテンプレートの内容（カスタムの場合は空） |

**実行手順**:

1. コードベースを Glob/Grep/Read で探索し、ストーリーに関連するファイル・構造を把握する
2. ストーリーを分析し、ゴール・スコープ・受入条件・チーム設計を決定する
3. Write ツールで `$PLAN_DIR/story-analysis.json` を出力する
4. 出力した story-analysis.json を Read で読み込み、構造を検証する
5. 不備があればリーダーが修正する

**ルール**:

- 最終Waveには必ず `reviewer` ロールを配置する
- Wave間の `blockedBy` で直列依存を明示する
- 同一Wave内のロールは並行実行される

### Step 4: タスク分解 → task-list.json

リーダー（Claude Code）が Glob/Grep/Read/Write を使って直接実行する。

1. `references/prompts/task-breakdown.md` を Read で読み込み、手順書に従って実行:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{story_analysis}` | `$PLAN_DIR/story-analysis.json` の内容 |
| `{plan_dir}` | `$PLAN_DIR`（Step 1 で取得） |

**実行手順**:

1. コードベースを Glob/Grep/Read で探索し、対象ファイル・実装状況・デザインシステムパターンを把握する
2. story-analysis.json のチーム設計に基づき、具体的なタスクに分解する
3. Write ツールで `$PLAN_DIR/task-list.json` を出力する

4. 出力された `$PLAN_DIR/task-list.json` を Read で読み込み、以下のスキーマ検証を実施する:

**スキーマ検証チェックリスト（全タスクに対して実施）**:

- [ ] 8必須フィールドが存在する: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `opencodePrompt`
- [ ] 禁止フィールドが存在しない: `title`, `acceptanceCriteria`, `context`（タスクレベル）, `deliverables`
- [ ] Wave構造が `waves[].tasks[]` フラット配列 + `role` フィールド形式である（旧 `roles.{roleName}` 形式でない）
- [ ] `opencodePrompt` が具体的な実装指示を含む（ファイルパス・操作内容・期待結果）
- [ ] `opencodePrompt` が曖昧でない（「機能を実装」「バグを修正」のような指示でない）

5. 不備があればリーダーが修正する。特に `opencodePrompt` の欠損・曖昧さは必ず修正する

### Step 5: opencode でタスクレビュー

タスク分解の品質を opencode で検証する。`references/prompts/task-review.md` を Read で読み込み、変数を置換して実行。**モデルは `openai/gpt-5.3-codex` 固定**:

**変数置換テーブル**:

| 変数 | 値の取得元 |
|------|-----------|
| `{story_analysis}` | `$PLAN_DIR/story-analysis.json` の内容 |
| `{task_list}` | `$PLAN_DIR/task-list.json` の内容 |

```bash
opencode run -m openai/gpt-5.3-codex "{task-review.md の変数置換済みプロンプト}"
```

**判定**:

- `APPROVED` → 完了
- `NEEDS_REVISION` → task-list.json を修正 → 再レビュー（最大3回）
- 3回失敗 → 現状のままユーザーに提示し判断を仰ぐ

**注意**: codex の提案をそのまま適用するのではなく、リーダーが妥当性を判断してから適用する。

## 重要な注意事項

1. **レビューのみ opencode 活用**: Step 3（ストーリー分析）、Step 4（タスク分解）はリーダーが直接実行。Step 5（レビュー）のみ opencode で実行
2. **opencode コマンドは決め打ち**: Step 5 のプロンプトテンプレートのコマンドをリーダーが改変しない
3. **フォールバック禁止**: Step 5 の opencode 失敗時に直接レビューしない。リトライのみ（最大3回）
4. **リーダーは実装しない**: リーダーの役割は計画・調整。実装は exec フェーズのエージェントが担当
5. **Step順序は絶対**: Step 1→2→3→4→5 の順序を飛ばさない
