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

## エージェント委譲ルール

**⚠️ 分析・分解・分類は必ずTaskエージェントに委譲する。自分で実行しない。**

呼び出しパターン（全ステップ共通）:
```
agentContent = Read(".claude/skills/dev/story/agents/{agent}.md")
Task({ prompt: agentContent + 追加コンテキスト, subagent_type: "general-purpose", model: {指定モデル} })
```

| Step | agent | model | 追加コンテキスト |
|------|-------|-------|-----------------|
| 1a | analyze-story.md | opus | ユーザーのストーリー |
| 1b | resolve-slug.md | haiku | story-analysis.json + 既存slug一覧 |
| 2 | decompose-tasks.md | sonnet | story-analysis.jsonのパス |
| 3 | plan-review.md | sonnet | story-analysis.json + task-list.json（OpenCode CLI使用） |

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
     c. 選択された story 情報を手順2の analyze-story のコンテキストとして渡す
     d. story-slug は plan.json の slug を使用 → 手順3の resolve-slug の story 部分もスキップ可
   - plan.json が存在しない場合 → 従来通り手順1から実行
1. ユーザーからストーリーを聞き取る
2. → **エージェント委譲**（analyze-story.md / opus）
3. → **エージェント委譲**（resolve-slug.md / haiku）— 既存slugとの類似判定・候補整理
4. **AskUserQuestion** で feature-slug / story-slug を確定（resolve-slugの推奨順で選択肢提示）
5. ワークスペース初期化スクリプトを実行（`YYMMDD` 日付付きディレクトリが作成される）:
   ```bash
   bash .claude/skills/dev/story/scripts/init-story-workspace.sh {feature-slug} {story-slug}
   ```
   出力の `docs/FEATURES/{feature-slug}/{YYMMDD}_{story-slug}` を以降のパスとして使用する。
6. **Write** で `story-analysis.json` を保存

**ゲート**: `story-analysis.json` が存在しなければ次に進まない。

### Step 2: タスク分解 + ワークフロー分類 → task-list.json

1. → **エージェント委譲**（decompose-tasks.md / sonnet）
   - エージェント内でGlob/Readによるコード探索・context作成を行う
   - 各タスクに `workflow` フィールド（tdd/e2e/task）を付与
2. 技術選定・方針に判断が必要ならAskUserQuestionで確認（自明ならスキップ可）
3. **Write** で `task-list.json` を保存

**ゲート**: `task-list.json` が存在しなければ次に進まない。

### Step 3: 計画レビュー（OpenCode）

1. → **エージェント委譲**（plan-review.md / sonnet）
   - OpenCode CLIを使用してtask-list.jsonのタスク分解をレビュー
   - タスク粒度、依存関係、ワークフロー分類、漏れ、リスクを検証
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

- agents/: analyze-story.md, decompose-tasks.md, plan-review.md
- references/: tdd-criteria.md, e2e-criteria.md, task-criteria.md
- ルール: `.claude/rules/workflow/workflow-branching.md`（自動適用）
