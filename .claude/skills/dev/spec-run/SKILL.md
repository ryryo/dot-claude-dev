---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  Todo の実行手順（IMPL → REVIEW → FIX）、Gate 通過条件、Review 実行方法を定義する。
  [PARALLEL] タグ付き Gate の Todo は Agent(isolation: worktree) で並列実行する。
  仕様書の Gate 0 で参照される。

  Trigger: 仕様書を実行, /dev:spec-run, 計画書の実行
---

# 仕様書実行プロトコル（dev:spec-run）

仕様書（`docs/PLAN/*.md`）に基づいて作業するエージェント向けの実行プロトコル。

## 起動フロー

### ステップ 1: 仕様書の特定

#### A. コンテキストから特定できる場合

会話の文脈や Gate 0 からの参照で対象が明確。そのままステップ 2 へ進む。

#### B. `/dev:spec-run` が単独で実行された場合

1. `docs/PLAN/*.md` を Glob で検索し、更新日順でソートする
2. 上位 5 件を AskUserQuestion で提示する（最新を推奨マーク付き）
3. ユーザーが選択した仕様書を対象とする

### ステップ 2: 実行準備(必須)

Gate 0 通過条件（参照すべきファイルの読み込み等）を実行し、Todo 実行に進む。

---

## Todo 実行の手順

Gate の `[PARALLEL]` タグに応じて実行プロトコルを切り替える。**該当するリファレンスを Read してから実行すること。**

| Gate のタグ | 実行方式 | 参照ファイル |
|-------------|----------|-------------|
| タグなし | 逐次実行 | `references/sequential-execution.md` |
| `[PARALLEL]` | 並列 worktree 実行 | `references/parallel-execution.md` |

## REVIEW の実行方法

`agents/reviewer.md` を Read し、その手順に従って実行する。引数は仕様書のパス + 対象 Review ID（例: Review A1）。

### 結果の記録

仕様書の Step 2 記入欄には **判定結果のみ** を簡潔に記録する。

```markdown
- [x] **Step 2 — Review A1** ✅ PASSED
```

FIX で修正した場合は変更内容をメモする:

```markdown
- [x] **Step 2 — Review A1** ✅ PASSED (FIX 1回)
  > - stdin の null チェックを追加
```

## Gate 通過条件

Gate 内の全 Todo について:

1. **IMPL が完了**していること
2. **REVIEW 結果記入欄にレビュー結果テーブルが記入済み**であること（空欄は不可）
3. **全 REVIEW の総合判定が PASS** であること

REVIEW 結果記入欄が空の Todo がある状態で Gate 通過としてはならない。

## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

## 参照

- `references/sequential-execution.md` — 逐次実行プロトコル（CONTEXT→IMPL→REVIEW→FIX→UPDATE）
- `references/parallel-execution.md` — 並列実行プロトコル（Agent(isolation: worktree) + マージ）
- `agents/reviewer.md` — 個別 Todo のレビューエージェント指示書
- `agents/tdd-developer.md` — TDD ワークフロー用実装エージェント
- `agents/frontend-developer.md` — E2E ワークフロー用実装エージェント
- `references/worktree-setup-guide.md` — WorktreeCreate hook セットアップガイド
- `scripts/setup-worktree.sh` — WorktreeCreate hook 用汎用セットアップスクリプト
