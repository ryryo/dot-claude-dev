---
name: dev:story
description: |
  ストーリーからTDD/E2E/TASK分岐付きタスクリスト（task-list.json）を生成。
  ストーリー駆動開発の起点となるスキル。
  「タスクを作成」「/dev:story」で起動。

  Trigger:
  タスクを作成, ストーリーからタスク, /dev:story, story to tasks
context: fork
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

# ストーリー → タスク生成（dev:story）

## 出力先

`docs/FEATURES/{feature-slug}/{YYMMDD}_{story-slug}/` に2ファイルを**順次**保存する。

---

## ★ 実行手順（必ずこの順序で実行）

### Step 1: ストーリー分析 → story-analysis.json

0. **plan.json チェック**（dev:epic 連携）:
   - ユーザーが feature-slug を指定 or 引数で渡している場合 → `docs/FEATURES/{feature-slug}/plan.json` を Read
   - plan.json が存在する場合:
     a. feature-slug は確定済み → 手順3の resolve-slug の feature 部分をスキップ
     b. plan.json の stories 配列から `executionType: "developing"` かつ未完了のストーリーを phase 順で AskUserQuestion に選択肢提示
     c. 選択された story のフィールド（description, acceptanceCriteria, affectedFiles, testImpact, technicalNotes, referenceImplementation）を `$STORY_PLAN` として保持し、手順2の分析のコンテキストとして使う
     d. story-slug は plan.json の slug を使用 → 手順3の resolve-slug の story 部分もスキップ可
   - plan.json が存在しない場合 → 従来通り手順1から実行
1. ユーザーからストーリーを聞き取る
2. references/analyze-story.md を参照し、ストーリーを分析して story-analysis.json の内容を構成する
3. → **Task（haiku）** に委譲（agents/resolve-slug.md）— 既存slugとの類似判定・候補整理
4. **AskUserQuestion** で feature-slug / story-slug を確定（resolve-slugの推奨順で選択肢提示）
5. ワークスペース初期化スクリプトを実行（`YYMMDD` 日付付きディレクトリが作成される）:
   ```bash
   bash .claude/skills/dev/story/scripts/init-story-workspace.sh {feature-slug} {story-slug}
   ```
   出力の `docs/FEATURES/{feature-slug}/{YYMMDD}_{story-slug}` を以降のパスとして使用する。
6. **Write** で `story-analysis.json` を保存

**ゲート**: `story-analysis.json` が存在しなければ次に進まない。

### Step 2a: タスク分解（decomposition プロセス）

`.claude/commands/dev/decomposition.md` を Read し、以下のプロセスに従ってタスク分解する:

- **ステップ1（コードベース探索）**: story-analysis.json のスコープ、`$STORY_PLAN` の affectedFiles を起点に探索
- **ステップ3（不明点インタビュー）**: AskUserQuestion で技術選定・方針を確認
- **ステップ4-5（詳細Todo作成）**: 各タスクが単独で実行可能な情報量を持つことを保証

### Step 2b: task-list.json 変換 + ワークフロー分類

references/decompose-tasks.md を参照し、Step 2a の分解結果を task-list.json に変換する:

1. 各タスクに `workflow`（tdd/e2e/task）を付与
2. `context` セクションにコード探索結果を記録
3. **planPath 設定**: plan.json が存在する場合（dev:epic 連携時）、`context.planPath` に `docs/FEATURES/{feature-slug}/PLAN.md` のパスを設定する
4. **Write** で `task-list.json` を保存

**ゲート**: `task-list.json` が存在しなければ次に進まない。

### Step 3: 計画レビュー（OpenCode）

1. → **Task（sonnet）** に委譲（agents/plan-review.md）
   - OpenCode CLIを使用してtask-list.jsonのタスク分解をレビュー
   - タスク粒度、依存関係、ワークフロー分類、漏れ、リスクを検証
   - `$STORY_PLAN` が存在する場合、plan-review のプロンプトに追加コンテキストとして渡す（acceptanceCriteria との整合性チェックに使用）
2. レビュー結果をユーザーに提示
3. 修正が必要なら Step 2 に戻る

**ゲート**: OpenCodeレビューが完了しなければ次に進まない。

### Step 4: ユーザー確認

- **実装開始** → dev:developing を呼び出し
- **修正が必要** → ユーザー指示に従いtask-list.jsonを修正 → Step 3から再実行

---

## 完了条件

以下2ファイルがすべて保存されていること:

| ファイル | Phase |
|----------|-------|
| `story-analysis.json` | Step 1 |
| `task-list.json` | Step 2 |

- 各タスクに `workflow` フィールド（tdd/e2e/task）が付与されている
- ユーザーが承認済み

## 参照

- agents/: resolve-slug.md, plan-review.md
- references/: analyze-story.md, decompose-tasks.md, tdd-criteria.md, e2e-criteria.md, task-criteria.md
- ルール: `.claude/rules/workflow/workflow-branching.md`（自動適用）
