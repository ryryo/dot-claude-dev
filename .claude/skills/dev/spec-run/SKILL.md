---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  IMPL → VERIFY の2層で Todo を実行する。
  起動時に Codex モードを選択すると、デフォルトで全タスクを Codex プラグイン（task）に委任し、
  VERIFY は codex review（複雑さに応じて1回 or 3回直列）で実行する。
  仕様書の Gate 0 で参照される。

  Trigger: 仕様書を実行, /dev:spec-run, 計画書の実行
---

# 仕様書実行プロトコル（dev:spec-run）

仕様書（`docs/PLAN/*.md` または `docs/PLAN/*/spec.md`）に基づいて作業するエージェント向けの実行プロトコル。

## 起動フロー

### ステップ 1: 仕様書の特定

#### A. コンテキストから特定できる場合

会話の文脈や Gate 0 からの参照で対象が明確。そのままステップ 1.5 へ進む。

#### B. `/dev:spec-run` が単独で実行された場合

1. `docs/PLAN/*.md` と `docs/PLAN/*/spec.md` を Glob で検索し、更新日順でソートする
2. 上位 5 件を AskUserQuestion で提示する（最新を推奨マーク付き）
3. ユーザーが選択した仕様書を対象とする

### ステップ 1.5: 入力形式判定

仕様書と同じディレクトリに `tasks.json` が存在するか確認する:

| 条件 | モード | 動作 |
|------|--------|------|
| `tasks.json` が存在する | **ディレクトリモード** | tasks.json から Todo を部分読み込みして実行 |
| `tasks.json` が存在しない | **従来モード** | 単一 MD をそのまま処理 |

判定結果を以降の全ステップに引き継ぐ。

### ステップ 2: 実行準備(必須)

- **従来モード**: Gate 0 通過条件（参照すべきファイルの読み込み等）を実行
- **ディレクトリモード**: spec.md の「参照すべきファイル」を Read + tasks.json を Read して全体構造（gates, todo IDs）を把握。各 Todo の `impl` はこの時点では読まない

次のステップへ進む。

### ステップ 3: 実行モード選択

AskUserQuestion で実行モードを選択する:

- **従来モード** — Claude Code が全 Todo を直接実行
- **Codex モード** — デフォルトで全タスクを Codex プラグイン（`task --write`）に委任（例外のみ Claude が保持）。VERIFY は `codex review`（複雑さに応じて1回 or 3回直列）

選択結果を以降の全 Gate・全 Todo に適用する。

### ステップ 4: 実行プロトコルの読み込み

選択したモードの参照ファイルを Read し、その手順に従って Todo を実行する。

| 実行モード | 参照ファイル |
|------------|-------------|
| 従来モード | `references/execution.md` |
| Codex モード | `references/codex-execution.md` |

---

## Gate 通過条件

Gate 内の全 Todo について:

1. **IMPL が完了**していること
2. **VERIFY 結果記入欄にレビュー結果が記入済み**であること（空欄は不可）
3. **全 VERIFY の総合判定が PASS** であること

### 結果の記録

**従来モード**: 仕様書の該当 Todo のチェックボックスと Review 記入欄を更新
**ディレクトリモード**: spec.md のチェックボックスと Review blockquote を更新

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
- [x] **Todo A2**: フォーカスインジケーター
  > **Review A2**: ✅ PASSED (FIX 1回)
  > - stdin の null チェックを追加
```

## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

## 参照

### 従来モード

- `references/execution.md` — 実行プロトコル
- `roles/implementer.md` — 汎用実装ロール定義
- `roles/tdd-developer.md` — TDD 実装ロール定義

### Codex モード

- `references/codex-execution.md` — Codex 実行プロトコル
- `roles/codex-developer.md` — Codex 汎用実装プロンプトテンプレート（XML ブロック構造）
- `roles/codex-tdd-developer.md` — Codex TDD 実装プロンプトテンプレート（XML ブロック構造）
- `references/codex-review-instructions.md` — codex review 用 focus テンプレート（統合版 + 3観点版）

### 共通

- `agents/reviewer-quality.md` — 品質・設計レビュワー
- `agents/reviewer-correctness.md` — 正確性・仕様適合レビュワー
- `agents/reviewer-conventions.md` — プロジェクト慣例レビュワー
