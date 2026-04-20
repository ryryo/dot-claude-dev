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

仕様書の形式を以下の 3 種類で判定する:

1. `tasks.json` が存在する場合、先頭 1 行を読んで `schemaVersion` を確認
   - `schemaVersion >= 2` → **v2 ディレクトリモード**（sync-spec-md により spec.md は自動管理される。spec-run は tasks.json のみ更新）
   - `schemaVersion` が未定義 or < 2 → **v1 ディレクトリモード**（従来どおり spec.md のチェックボックスと tasks.json の両方を更新）
2. `tasks.json` が存在しない場合 → **シングルモード**（単一 MD をそのまま処理、既存 PLAN の互換パス）

### ステップ 3: 実行準備

- **v2 ディレクトリモード**: spec.md の「参照すべきファイル」と tasks.json を並列 Read し、全体構造（gates, todo IDs, descriptions, steps, progress）を把握。各 Todo の `impl` はこの時点では読まない
- **v1 ディレクトリモード**: 現状どおり spec.md + tasks.json を並列 Read。steps[] がないため Step 状態は spec.md のチェックボックスから推論
- **シングルモード**: Gate 0 通過条件（参照すべきファイルの読み込み等）を実行

### ステップ 4: 実行モード + worktree 選択

AskUserQuestion で**2 つの質問を同時に**聞く（1 tool call）:

**質問 1: 実行モード**

- **Claudeモード** — Claude Code が全 Todo を直接実行
- **Codex モード** — デフォルトで全タスクを Codex プラグイン（`task --write`）に委任（例外のみ Claude が保持）。VERIFY は native `codex review` CLI（複雑さに応じてスキップ or 1回 or 3回並列）

**質問 2: worktree 使用**

- **使わない（Recommended）** — 現 cwd（通常 base ブランチ）で直接作業する（現行動作）
- **使う** — `feature/{slug}` の worktree 内で作業し、全 Gate 通過後にローカル `--no-ff` マージ + cleanup を自動実行

「使わない」を選択した場合は Step 5 へ直行。

#### worktree を「使う」を選択した場合のみ:

`references/worktree-setup.md` を **今すぐ Read ツールで読み込み**、記載された手順を完了させてから Step 5 へ進む。

### ステップ 5: 実行プロトコルの読み込みと実行

選択したモードの参照ファイルを Read し、その手順に従って Todo を実行する。
Preflight フェーズを含む場合は、必ずPreflightの内容はClaudeのメインセッションで実行する。

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

**v2 ディレクトリモード**: `tasks.json` のみ更新。spec.md は PostToolUse hook（`.claude/settings.json` に登録済み）で自動再生成される。hook が未発火の環境では `node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs <tasks.json-path>` を明示的に実行して同期する

```json
{
  "todos": [
    {
      "id": "A1",
      "steps": [
        { "kind": "impl",   "checked": true },
        { "kind": "review", "checked": true, "review": { "result": "PASSED", "fixCount": 0, "summary": "OK" } }
      ]
    }
  ],
  "status": "in-progress",
  "progress": { "completed": 2, "total": 16 }
}
```

**重要**: `status` と `progress` も同時に再計算して書き込む（下の算出ルール参照）。

**v1 ディレクトリモード**: 現状のまま spec.md のチェックボックスと Review blockquote を更新（PostToolUse hook は v1 tasks.json に対しては no-op でスキップ）

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
- [x] **Todo A2**: フォーカスインジケーター
  > **Review A2**: ✅ PASSED (FIX 1回)
  >
  > - stdin の null チェックを追加
```

**シングルモード**: 仕様書の該当 Todo のチェックボックスと Review 記入欄を更新

#### status / progress の算出ルール（v2 のみ）

```
total     = sum of all todos[].steps[].length
completed = count of all steps where checked == true
progress  = { completed, total }

status:
  - completed == 0                               → "not-started"
  - 0 < completed < total                        → "in-progress"
  - completed == total && reviewChecked == false → "in-review"
  - completed == total && reviewChecked == true  → "completed"
```

## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

**Codex モードの場合**: 一時プロンプトファイルを削除する。

```bash
rm -f .tmp/codex-*.md
```

### worktree 運用の確認（Step 4 で worktree を選択した場合のみ）

Step 4 で worktree を使っていない場合はスキップし、そのまま「人間レビュー確認フロー」へ進む。

AskUserQuestion で**マージと人間レビューの順序**を聞く:

- **先にマージ（Recommended）** — 人間レビューを後回しにして、すぐに worktree をマージ + cleanup する。レビューで問題が見つかった場合は base ブランチで fix-forward 対応
- **レビュー後にマージ** — 人間レビューで OK を得てから worktree をマージ + cleanup する（NG なら worktree に留まって修正ループ）

#### 「先にマージ」を選択した場合

1. `references/worktree-teardown.md` を **今すぐ Read ツールで読み込み**、記載された手順を完了させる（マージ + cleanup）
2. その後「人間レビュー確認フロー」に進む
3. レビューが NG になった場合は、base ブランチ上で修正コミットを追加して fix-forward 対応する（worktree は既に cleanup 済み）

#### 「レビュー後にマージ」を選択した場合

1. 「人間レビュー確認フロー」を実行する
2. レビュー OK になったら `references/worktree-teardown.md` を **今すぐ Read ツールで読み込み**、記載された手順を完了させる
3. レビュー NG の場合は worktree を残したまま修正ループに入る（OK になるまでマージしない）

### 人間レビュー確認フロー

仕様書に `## レビューステータス` セクションが存在し、未チェックの `- [ ] **レビュー完了**` 行がある場合、以下を実行する。

**v2 モード**: `## レビューステータス` セクションは generated 領域の外（人間編集領域）なので、従来どおり spec.md のチェックボックスを `[x]` に更新。同時に `tasks.json` のトップレベル `reviewChecked` を `true` に更新し、`status` を再計算する。

**v1 / シングルモード**: 従来どおり spec.md のチェックボックスのみ更新。

1. AskUserQuestion でブラウザ動作確認を促す（実装内容に応じた確認ポイントを添える）
2. ユーザーが「OK / 確認済み」を選択した場合:
   - 仕様書の `- [ ] **レビュー完了**` を `- [x] **レビュー完了**` に更新する
   - （v2 のみ）tasks.json の `reviewChecked: true` + `status: "completed"` に更新する
   - 変更をコミットする
3. ユーザーが「NG / 修正が必要」を選択した場合:
   - worktree が未 cleanup（「レビュー後にマージ」を選んでいる）ならその中で修正ループ
   - worktree が cleanup 済み（「先にマージ」を選んでいる）なら base ブランチで fix-forward

`## レビューステータス` セクションが存在しない場合はスキップ。

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
