---
name: dev:spec-run
description: 仕様書（docs/PLAN/*.md）の実行プロトコル。IMPL → VERIFY の2層で Todo を実行。Trigger: 仕様書を実行, /dev:spec-run, 計画書の実行
---

## 起動フロー

### ステップ 1: 仕様書の特定

対象が会話の文脈や Gate 0 から明確な場合はステップ 2 へ進む。それ以外は:

1. `docs/PLAN/*.md` と `docs/PLAN/*/spec.md` を Glob で検索し、更新日順でソートする
2. 上位 5 件を AskUserQuestion で提示する（最新を推奨マーク付き）
3. ユーザーが選択した仕様書を対象とする

### ステップ 2: 入力形式判定

- `tasks.json` あり → **ディレクトリモード**（tasks.json から Todo を部分読み込みして実行）
- `tasks.json` なし → **シングルモード**（単一 MD をそのまま処理）

### ステップ 3: 実行準備

- **シングルモード**: Gate 0 通過条件（参照すべきファイルの読み込み等）を実行
- **ディレクトリモード**: spec.md の「参照すべきファイル」と tasks.json を並列 Read し、全体構造（gates, todo IDs, descriptions）を把握。各 Todo の `impl` はこの時点では読まない

### ステップ 4: 実行モード + worktree 選択

AskUserQuestion で**2 つの質問を同時に**聞く（1 tool call）:

**質問 1: 実行モード**

- **Claudeモード** — Claude Code が全 Todo を直接実行
- **Codex モード** — デフォルトで全タスクを Codex プラグイン（`task --write`）に委任（例外のみ Claude が保持）。VERIFY は `codex review`（複雑さに応じてスキップ or 1回 or 3回並列）

**質問 2: worktree 使用**

- **使わない（Recommended）** — 現 cwd（通常 master）で直接作業する（現行動作）
- **使う** — `feature/{slug}` の worktree 内で作業し、全 Gate 通過後にローカル `--no-ff` マージ + cleanup を自動実行

「使う」を選択した場合は `references/worktree-setup.md` を Read し、フェーズ 1（dirty チェック）→ フェーズ 2（setup）→ フェーズ 3（reuse 時 spec 同期）の順に実行してから Step 5 へ進む。「使わない」を選択した場合は Step 5 へ直行。

### ステップ 5: 実行プロトコルの読み込みと実行

選択したモードの参照ファイルを Read し、その手順に従って Todo を実行する（Preflight フェーズを含む）。

---

## Gate 通過条件

Gate 内の全 Todo について:

1. **IMPL が完了**していること
2. **VERIFY 結果記入欄にレビュー結果が記入済み**であること（空欄は不可）
3. **全 VERIFY の総合判定が PASS** であること

### 結果の記録

**Preflight 完了時**:

```markdown
- [x] **P1**: パッケージインストール — `pnpm install`
- [x] **P2**: **[手動]** `.env.local` に `API_KEY` を設定
```

**シングルモード**: 仕様書の該当 Todo のチェックボックスと Review 記入欄を更新
**ディレクトリモード**: spec.md のチェックボックスと Review blockquote を更新

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
- [x] **Todo A2**: フォーカスインジケーター
  > **Review A2**: ✅ PASSED (FIX 1回)
  >
  > - stdin の null チェックを追加
```

## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

**Codex モードの場合**: 一時プロンプトファイルを削除する。

```bash
rm -f .tmp/codex-*.md
```

### 人間レビュー確認フロー

仕様書に `## レビューステータス` セクションが存在し、未チェックの `- [ ] **レビュー完了**` 行がある場合、以下を実行する。

1. AskUserQuestion でブラウザ動作確認を促す（実装内容に応じた確認ポイントを添える）
2. ユーザーが「OK / 確認済み」を選択した場合:
   - 仕様書の `- [ ] **レビュー完了**` を `- [x] **レビュー完了**` に更新する
   - 変更をコミットする
3. ユーザーが「NG / 修正が必要」を選択した場合:
   - 問題内容を確認し、必要な修正を実施してから再度確認する

`## レビューステータス` セクションが存在しない場合はスキップ。

### worktree 終了処理（Step 4 で worktree を選択した場合のみ）

Step 4 で「worktree を使う」を選択した場合のみ実行。`references/worktree-teardown.md` を Read し、フェーズ 5（完了時 merge）→ フェーズ 6（cleanup）→ フェーズ 7（エラーリカバリ）に従う。人間レビューが NG の場合は worktree を残したまま修正ループに入り、OK になったら merge + cleanup を実行する。

## 参照

### Claudeモード

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
