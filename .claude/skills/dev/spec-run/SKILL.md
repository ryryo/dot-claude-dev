---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  IMPL → VERIFY の2層で Todo を実行する。
  ラベル（[TDD], [PARALLEL]）に応じてロールと実行方式を切り替える。
  起動時に Codex モードを選択すると、[TDD] タスクを codex exec に委任し、
  VERIFY は codex review + sonnet 3体のハイブリッドで実行する。
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

Gate 0 通過条件（参照すべきファイルの読み込み等）を実行し、次のステップへ進む。

### ステップ 3: 実行モード選択

AskUserQuestion で実行モードを選択する:

- **従来モード** — Claude Code が全 Todo を直接実行（既存の動作）
- **Codex モード** — [TDD] ラベル付き Todo の IMPL を `codex exec` に委任。VERIFY は `codex review` + sonnet 3体のハイブリッド

選択結果を以降の全 Gate・全 Todo に適用する。

---

## 実行パラメータテーブル

Todo のラベルと Gate のタグに応じて、ロール・モデル・isolation を決定する。

### 従来モード

| ラベル / タグ       | Step   | Role              | Model  | Isolation |
|---------------------|--------|-------------------|--------|-----------|
| (default)           | IMPL   | implementer       | opus   | -         |
| (default)           | VERIFY | 3体並列レビュー   | sonnet | -         |
| [TDD]               | IMPL   | tdd-developer     | opus   | -         |
| [TDD]               | VERIFY | 3体並列レビュー   | sonnet | -         |
| [PARALLEL]          | IMPL   | implementer       | opus   | worktree  |
| [PARALLEL]          | VERIFY | 3体並列レビュー   | sonnet | -         |
| [PARALLEL] + [TDD]  | IMPL   | tdd-developer     | opus   | worktree  |
| [PARALLEL] + [TDD]  | VERIFY | 3体並列レビュー   | sonnet | -         |
| (統合レビュー)      | VERIFY | 3体並列レビュー   | sonnet | -         |

### Codex モード

| ラベル / タグ       | Step     | Role / 実行方法            | Model / Tool   | Isolation |
|---------------------|----------|---------------------------|----------------|-----------|
| (default)           | IMPL     | implementer (Claude)      | opus           | -         |
| (default)           | VERIFY   | 3体並列レビュー           | sonnet         | -         |
| [TDD]               | IMPL     | codex-tdd-developer       | codex exec     | -         |
| [TDD]               | VERIFY-a | codex review（差分バグ）   | codex review   | -         |
| [TDD]               | VERIFY-b | 3体並列レビュー           | sonnet         | -         |
| [PARALLEL]          | IMPL     | implementer (Claude)      | opus           | worktree  |
| [PARALLEL]          | VERIFY   | 3体並列レビュー           | sonnet         | -         |
| [PARALLEL] + [TDD]  | IMPL     | codex-tdd-developer       | codex exec     | worktree  |
| [PARALLEL] + [TDD]  | VERIFY-a | codex review（差分バグ）   | codex review   | -         |
| [PARALLEL] + [TDD]  | VERIFY-b | 3体並列レビュー           | sonnet         | -         |
| (統合レビュー)      | VERIFY   | 3体並列レビュー           | sonnet         | -         |

### 共通ルール

- **IMPL Role** の参照先: `references/agents/{role}.md`
- **3体並列レビュー**: `agents/reviewer-quality.md`, `agents/reviewer-correctness.md`, `agents/reviewer-conventions.md` を並列実行
- **[TDD]** は Todo 単位のラベル。同一 Gate 内で混在可
- **[PARALLEL]** は Gate 単位のタグ
- **統合レビュー**: [PARALLEL] Gate のマージ後に実行（同じ3体並列構成）
- **Codex モード固有**:
  - `codex-tdd-developer` の参照先: `references/agents/codex-tdd-developer.md`
  - `codex review` の指示テンプレート: `references/codex-review-instructions.md`
  - 非 [TDD] タスクは従来モードと同じ動作（Claude が直接 IMPL）
  - VERIFY-a（codex review）→ FIX → VERIFY-b（sonnet 3体）の順で実行

## Todo 実行の手順

Gate のタグと実行モードに応じて参照ファイルを切り替える。**該当するリファレンスを Read してから実行すること。**

### 従来モード

| Gate のタグ | 実行方式 | 参照ファイル |
|-------------|----------|-------------|
| タグなし | 逐次実行 | `references/sequential-execution.md` |
| `[PARALLEL]` | 並列 worktree 実行 | `references/parallel-execution.md` |

### Codex モード

| Gate のタグ | 実行方式 | 参照ファイル |
|-------------|----------|-------------|
| タグなし | Codex 逐次実行 | `references/codex-sequential-execution.md` |
| `[PARALLEL]` | Codex 並列 worktree 実行 | `references/codex-parallel-execution.md` |

## VERIFY の実行方法

VERIFY の詳細手順は各実行プロトコルの参照ファイルに記載されている。
以下は両モード共通の概要。

### 3体並列レビュー（両モード共通）

以下の3体を Agent（sonnet）で **並列** 起動する。各エージェントは信頼度スコア（0-100）で評価し、80以上の指摘のみ報告する。

1. `agents/reviewer-quality.md` — 品質・設計（ベストプラクティス、保守性・可読性）
2. `agents/reviewer-correctness.md` — 正確性・仕様適合（ストーリー適合性、API・SDK準拠、リスク・前提の検証、セキュリティ）
3. `agents/reviewer-conventions.md` — プロジェクト慣例（CLAUDE.md準拠、既存パターン、命名規則）

各エージェントには仕様書のパス + 対象 Review ID（例: Review A1）を渡す。

### モード別の違い

- **従来モード**: sonnet 3体並列のみ
- **Codex モード（[TDD] タスク）**: `codex review` → FIX → sonnet 3体の 2段階。詳細は `references/codex-sequential-execution.md` または `references/codex-parallel-execution.md` を参照
- **Codex モード（非 [TDD] タスク）**: 従来モードと同じ（sonnet 3体のみ）

### 総合判定

- **全体 PASS**: すべてのレビューが PASS
- **全体 FAIL**: 1体でも FAIL があれば全体 FAIL → FIX ラウンドへ

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

### 従来モード

- `references/sequential-execution.md` — 逐次実行プロトコル
- `references/parallel-execution.md` — 並列実行プロトコル
- `references/agents/implementer.md` — 汎用実装ロール定義
- `references/agents/tdd-developer.md` — TDD 実装ロール定義

### Codex モード

- `references/codex-sequential-execution.md` — Codex 逐次実行プロトコル
- `references/codex-parallel-execution.md` — Codex 並列実行プロトコル
- `references/agents/codex-tdd-developer.md` — Codex TDD 実装プロンプトテンプレート
- `references/codex-review-instructions.md` — codex review 用レビュー指示テンプレート

### 共通

- `agents/reviewer-quality.md` — 品質・設計レビュワー
- `agents/reviewer-correctness.md` — 正確性・仕様適合レビュワー
- `agents/reviewer-conventions.md` — プロジェクト慣例レビュワー
- `references/worktree-setup-guide.md` — WorktreeCreate hook セットアップガイド
- `scripts/setup-worktree.sh` — WorktreeCreate hook 用汎用セットアップスクリプト
