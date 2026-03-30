---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  IMPL → VERIFY の2層で Todo を実行する。
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

Todo のラベルに応じて、ロール・モデルを決定する。

### 従来モード

| ラベル    | Step   | Role              | Model  |
|-----------|--------|-------------------|--------|
| (default) | IMPL   | implementer       | opus   |
| (default) | VERIFY | 3体並列レビュー   | sonnet |
| [TDD]     | IMPL   | tdd-developer     | opus   |
| [TDD]     | VERIFY | 3体並列レビュー   | sonnet |

### Codex モード

| ラベル    | Step     | Role / 実行方法            | Model / Tool   |
|-----------|----------|---------------------------|----------------|
| (default) | IMPL     | implementer (Claude)      | opus           |
| (default) | VERIFY   | 3体並列レビュー           | sonnet         |
| [TDD]     | IMPL     | codex-tdd-developer       | codex exec     |
| [TDD]     | VERIFY-a | codex review（差分バグ）   | codex review   |
| [TDD]     | VERIFY-b | 3体並列レビュー           | sonnet         |

## Todo 実行の手順

実行モードに応じて参照ファイルを切り替える。**該当するリファレンスを Read してから実行すること。**

| 実行モード | 参照ファイル |
|------------|-------------|
| 従来モード | `references/execution.md` |
| Codex モード | `references/codex-execution.md` |

## VERIFY の実行方法

`agents/` 内の3体のレビューエージェントを Agent（sonnet）で **並列** 起動する。各エージェントは信頼度スコア（0-100）で評価し、80以上の指摘のみ報告する。仕様書のパス + 対象 Review ID を渡す。

Codex モードの [TDD] タスクでは、sonnet 3体の前に `codex review` を先行実行する。詳細は `references/codex-execution.md` を参照。

### 結果の記録

```markdown
- [x] **Step 2 — Review A1** ✅ PASSED
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

- `references/execution.md` — 実行プロトコル（CONTEXT→IMPL→VERIFY→FIX→UPDATE）
- `references/agents/implementer.md` — 汎用実装ロール定義
- `references/agents/tdd-developer.md` — TDD 実装ロール定義

### Codex モード

- `references/codex-execution.md` — Codex 実行プロトコル
- `references/agents/codex-tdd-developer.md` — Codex TDD 実装プロンプトテンプレート
- `references/codex-review-instructions.md` — codex review 用レビュー指示テンプレート

### 共通

- `agents/reviewer-quality.md` — 品質・設計レビュワー
- `agents/reviewer-correctness.md` — 正確性・仕様適合レビュワー
- `agents/reviewer-conventions.md` — プロジェクト慣例レビュワー
