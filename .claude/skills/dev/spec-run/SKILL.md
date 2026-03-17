---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  IMPL → VERIFY の2層で Todo を実行する。
  ラベル（[TDD], [PARALLEL]）に応じてロールと実行方式を切り替える。
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

## 実行パラメータテーブル

Todo のラベルと Gate のタグに応じて、ロール・モデル・isolation を決定する。

| ラベル / タグ       | Step   | Role              | Model  | Isolation |
|---------------------|--------|-------------------|--------|-----------|
| (default)           | IMPL   | implementer       | opus   | -         |
| (default)           | VERIFY | reviewer          | sonnet | -         |
| [TDD]               | IMPL   | tdd-developer     | opus   | -         |
| [TDD]               | VERIFY | reviewer          | sonnet | -         |
| [PARALLEL]          | IMPL   | implementer       | opus   | worktree  |
| [PARALLEL]          | VERIFY | reviewer          | sonnet | -         |
| [PARALLEL] + [TDD]  | IMPL   | tdd-developer     | opus   | worktree  |
| [PARALLEL] + [TDD]  | VERIFY | reviewer          | sonnet | -         |
| (統合レビュー)      | VERIFY | reviewer          | sonnet | -         |

- **Role** の参照先: `references/agents/{role}.md`
- **[TDD]** は Todo 単位のラベル。同一 Gate 内で混在可
- **[PARALLEL]** は Gate 単位のタグ
- **統合レビュー**: [PARALLEL] Gate のマージ後に実行

## Todo 実行の手順

Gate のタグに応じて実行プロトコルを切り替える。**該当するリファレンスを Read してから実行すること。**

| Gate のタグ | 実行方式 | 参照ファイル |
|-------------|----------|-------------|
| タグなし | 逐次実行 | `references/sequential-execution.md` |
| `[PARALLEL]` | 並列 worktree 実行 | `references/parallel-execution.md` |

## VERIFY の実行方法

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
2. **VERIFY 結果記入欄にレビュー結果が記入済み**であること（空欄は不可）
3. **全 VERIFY の総合判定が PASS** であること

VERIFY 結果記入欄が空の Todo がある状態で Gate 通過としてはならない。

## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

## 参照

- `references/sequential-execution.md` — 逐次実行プロトコル（CONTEXT→IMPL→VERIFY→FIX→UPDATE）
- `references/parallel-execution.md` — 並列実行プロトコル（worktree 内 IMPL→VERIFY→FIX + マージ + 統合レビュー）
- `references/agents/implementer.md` — 汎用実装ロール定義
- `references/agents/tdd-developer.md` — TDD 実装ロール定義
- `agents/reviewer.md` — レビューエージェント定義（model/tools フロントマター付き）
- `references/worktree-setup-guide.md` — WorktreeCreate hook セットアップガイド
- `scripts/setup-worktree.sh` — WorktreeCreate hook 用汎用セットアップスクリプト
