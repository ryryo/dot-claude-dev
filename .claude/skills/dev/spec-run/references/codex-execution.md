# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 基本原則

**デフォルトで Codex に委任する。** Claude が保持するのは、チェックリストで明確に該当する場合のみ。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      チェックリストで委任判断 → Codex or Claude
Step 2 — VERIFY    adversarial-review（複雑さに応じて1回 or 3回並列）
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 1 — IMPL

### 委任判断チェックリスト（必須）

各 Todo の IMPL 前に、以下の 3 項目を確認する。

| # | チェック項目 | 「はい」の場合 |
|---|-------------|---------------|
| 1 | この Todo は**前の Todo の実装結果**を見て設計判断を変える必要があるか？ | Claude 保持 |
| 2 | 仕様が曖昧で**ユーザーに確認**しないと実装方針が決まらないか？ | Claude 保持 |
| 3 | この Todo は**他の Todo と同じファイル**を同時に変更する必要があるか？ | Claude 保持 |

- **3項目すべて「いいえ」→ Codex に委任する**（例外なし）
- **1項目でも「はい」→ Claude が保持する。理由を記録する**

「確実性」「複雑さ」「Claude の方が得意」のような主観的理由での保持は禁止。

### Codex に委任する場合

#### 1. タスク分割

Todo 内に**独立したファイル**が複数含まれる場合、ファイルごとに別々の task で**並列実行**する。

| 条件 | 実行方法 |
|------|----------|
| 1ファイルの変更 | task 1回 |
| 複数ファイルだが相互依存あり | task 1回（まとめて渡す） |
| 複数ファイルで独立 | ファイルごとに task を `--background` で**並列実行** |

#### 2. テンプレート選択

- [TDD] ラベルあり、またはテスト先行が適切 → `roles/codex-tdd-developer.md`
- それ以外 → `roles/codex-developer.md`

#### 3. 実行

テンプレートの変数を埋めてプロジェクト内の `.tmp/` に書き出し、実行する（`.tmp/` が未作成なら `mkdir -p .tmp` で作成）:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --prompt-file .tmp/codex-prompt.md
```

並列実行時:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --background --prompt-file .tmp/codex-prompt-1.md
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --background --prompt-file .tmp/codex-prompt-2.md
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" status --wait
```

#### 4. 結果確認

- 成功 → Claude がコミット
- 失敗 → `--resume-last` でコンテキストを保持してリトライ（最大3回）
- 3回失敗 → Claude が直接実装（フォールバック）

### Claude が直接実装する場合

チェックリストで「はい」が 1 つ以上あった場合のみ。
仕様に忠実に実装する。[TDD] ラベルがある場合は `roles/tdd-developer.md` を参照。
実装完了後、変更をコミットする。

## Step 2 — VERIFY

### 複雑さ判断

Claude が Todo の内容を以下の観点で総合判断し、レビューモードを決定する:

| 判断要素 | シンプル寄り | 複雑寄り |
|----------|------------|---------|
| 変更ファイル数 | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | 局所的 | 複数モジュール横断 |
| リスク | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

### シンプルモード — adversarial-review 1回

`references/codex-review-instructions.md` の**統合版テンプレート**を使用。

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review --wait {統合版 focus テキスト}
```

### 複雑モード — adversarial-review 3回並列

`references/codex-review-instructions.md` の **quality / correctness / conventions** 各テンプレートを使用。

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review --background {quality-focus}
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review --background {correctness-focus}
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review --background {conventions-focus}
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" status --wait
```

各 focus テンプレートの `{変数}` は仕様書の情報で埋める。

### 結果の判定

adversarial-review は構造化 JSON（verdict, findings, severity）を返す。

- **verdict が "approve"** → PASS
- **verdict が "needs-attention"**:
  - severity が critical/high → FAIL
  - severity が medium 以下のみ → Claude が精査して PASS/FAIL 判定
- **複雑モード**: 3観点すべて PASS → 全体 PASS、いずれかが FAIL → 全体 FAIL

## Step 3 — FIX

FAIL がある場合のみ。最大3ラウンド。

### Codex 委任タスクの修正

adversarial-review の findings を含めて `task --write --resume-last` で修正を委任:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --resume-last --prompt-file .tmp/codex-fix-prompt.md
```

修正後、再度 VERIFY を実行する。

### Claude 実装タスクの修正

Claude が直接修正し、再度 VERIFY を実行する。

## Step 4 — UPDATE

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。
