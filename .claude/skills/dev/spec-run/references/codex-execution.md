# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 基本原則

**デフォルトで Codex に委任する。** Claude が保持するのは、チェックリストで明確に該当する場合のみ。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）

【各 Gate 冒頭で実行】
Step P — PREFLIGHT その Gate の環境構築系 Todo を Claude main session でまとめて先行実行
Step 1 — IMPL      チェックリストで委任判断 → Codex or Claude
Step 2 — VERIFY    codex review（複雑さに応じて1回 or 3回並列）
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 0 — CONTEXT

最初の Todo 着手前に1回だけ実行する。

### 0-1. codex-companion.mjs のパス解決

```bash
CODEX_COMPANION="$(bash .claude/skills/dev/spec-run/scripts/resolve-codex-plugin.sh)"
```

失敗した場合は codex プラグインが未インストール。従来モードにフォールバックする。

### 0-2. 仕様書の読み込み

#### 従来モード

仕様書の「参照すべきファイル」を全て Read する。

#### ディレクトリモード

1. spec.md の「参照すべきファイル」を全て Read する
2. tasks.json を Read して全体構造（`gates`, Todo の `id`/`gate`/`title`/`dependencies`）を把握する
3. 各 Todo の `impl` フィールドは**この時点では読まない**（部分読み込みで後述）

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

#### 1.5. Todo 情報の取得（ディレクトリモードのみ）

tasks.json から**現在の Todo の `impl` フィールドだけ**を取得する。
Codex プロンプトテンプレートの仕様部分にこの `impl` 内容を埋め込む。

#### 2. テンプレート選択

- [TDD] ラベルあり / `tdd: true`、またはテスト先行が適切 → `roles/codex-tdd-developer.md`
- それ以外 → `roles/codex-developer.md`

#### 3. 実行

テンプレートの変数を埋めてプロジェクト内の `.tmp/` に書き出し、実行する（`.tmp/` が未作成なら `mkdir -p .tmp` で作成）:

```bash
node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-prompt.md
```

並列実行時:

```bash
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-1.md
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-2.md
node "$CODEX_COMPANION" status --wait
```

#### 4. 結果確認

- 成功 → Claude がコミット
- 失敗 → **エラー診断** を実行してからリトライ判断

### Codex エラー診断（task / review 共通）

Codex コマンドが失敗した場合、**黙ってフォールバックせず**、以下の手順で原因を特定してユーザーに報告する。

#### 4-1. 診断スクリプトの実行

```bash
bash .claude/skills/dev/spec-run/scripts/diagnose-codex.sh "$CODEX_COMPANION"
```

#### 4-2. エラー分類と対処

診断結果をもとに、以下の表で分類する:

| エラーメッセージ | 原因 | 自動対処 | ユーザー報告 |
|----------------|------|---------|-------------|
| `Invalid request` | プロジェクト未信頼 / API 仕様変更 / モデル非対応 | 不可 | **必須** — 診断結果をそのまま提示し、対処法を案内 |
| `401` / `Unauthorized` | トークン期限切れ | 不可 | **必須** — `codex auth` での再認証を案内 |
| `429` / `rate_limit` | レートリミット | 30秒待ってリトライ（最大2回） | リトライ後も失敗なら報告 |
| `timeout` / `ETIMEDOUT` | ネットワーク / 応答遅延 | 1回リトライ | リトライ後も失敗なら報告 |
| `ECONNREFUSED` | broker ソケット切断 | 不可 | **必須** — Claude Code 再起動を案内 |
| その他 | 不明 | 不可 | **必須** — エラーメッセージ + ログファイルパスを提示 |

#### 4-3. ユーザーへの報告テンプレート

```
⚠️ Codex {task|review} が失敗しました。

エラー: {errorMessage}
原因:  {診断結果からの原因}
ジョブ: {job ID}
ログ:  {logFile パス}

推奨対処:
- {対処法}

選択肢:
1. 対処後にリトライ
2. Claude が直接{実装|レビュー}（フォールバック）
3. 作業を中断
```

AskUserQuestion で上記3択を提示する。**暗黙のフォールバックは禁止**。

#### 4-4. リトライポリシー

| 種別 | 自動リトライ | `--resume-last` | 最大回数 |
|------|------------|----------------|---------|
| レートリミット（429） | 30秒待ちで自動 | 不要 | 2回 |
| タイムアウト | 即時 | 使用 | 1回 |
| その他（Invalid request 等） | **しない** | — | — |

### Claude が直接実装する場合

チェックリストで「はい」が 1 つ以上あった場合のみ。
仕様に忠実に実装する。[TDD] ラベルがある場合は `roles/tdd-developer.md` を参照。
実装完了後、変更をコミットする。

## Step 2 — VERIFY

### 複雑さ判断

Claude が Todo の内容を以下の観点で総合判断し、レビューモードを決定する:

| 判断要素 | SKIP（レビュー不要） | シンプル寄り | 複雑寄り |
|----------|---------------------|------------|---------|
| 変更内容 | ドキュメント・設定・コメントのみ | コード変更あり（軽微） | コード変更あり（重要） |
| 変更ファイル数 | — | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | — | 局所的 | 複数モジュール横断 |
| リスク | なし（実行パスに影響しない） | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | ロジック変更なし | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

### SKIP — レビュー不要

変更がドキュメント（`.md`）、コメント、設定ファイルのみでロジックを含まない場合、VERIFY をスキップして自動 PASS とする。

記録形式: `> **Review XX**: ⏭️ SKIPPED (docs only)`

Step 3（FIX）も不要。そのまま Step 4（UPDATE）へ進む。

### シンプルモード — codex review 1回

`references/codex-review-instructions.md` の**統合版テンプレート**を使用。
focus テキストを `.tmp/codex-review-focus.md` に書き出し、stdin で渡す。

> **CLI 制約（v0.118.0）**: `--commit` と `[PROMPT]` は排他的引数で併用不可。
> IMPL 直後の VERIFY では HEAD が対象コミットなので `[PROMPT]` 方式（`origin/main..HEAD` 自動検出）で十分。

```bash
codex review - < .tmp/codex-review-focus.md
```

未コミットの変更をレビューする場合は `codex review --uncommitted` を使用。

### 複雑モード — codex review 3回並列

`references/codex-review-instructions.md` の **quality / correctness / conventions** 各テンプレートを使用。
3観点を並列実行し、すべての完了を待つ。

```bash
codex review - < .tmp/codex-review-quality.md &
codex review - < .tmp/codex-review-correctness.md &
codex review - < .tmp/codex-review-conventions.md &
wait
```

各 focus テンプレートの `{変数}` は仕様書の情報で埋める。

### review 失敗時

`codex review` / `adversarial-review` が失敗した場合も、上記「Codex エラー診断」の手順に従う。
review はコード変更を伴わないため、フォールバック選択肢は以下になる:

1. 対処後にリトライ
2. Claude が直接レビュー（Agent sonnet でレビュー実行）
3. テスト通過のみで PASS 判定（テスト全パス + 変更が軽微な場合のみ）

### 結果の判定

`codex review` は優先度付きテキストコメントを返す（`[P1]` critical, `[P2]` important, `[P3]` minor）。

- **コメントなし / P3 のみ** → PASS
- **P2 あり** → Claude が内容を精査し、仕様の設計決定に基づく意図的な動作かを判断して PASS/FAIL 決定
- **P1 あり** → FAIL
- **複雑モード**: 3観点すべて PASS → 全体 PASS、いずれかが FAIL → 全体 FAIL

## Step 3 — FIX

FAIL がある場合のみ。最大3ラウンド。

### Codex 委任タスクの修正

`codex review` の指摘内容を含めて `task --write --resume-last` で修正を委任:

```bash
node "$CODEX_COMPANION" task --write --resume-last --prompt-file .tmp/codex-fix-prompt.md
```

修正後、再度 VERIFY を実行する。

### Claude 実装タスクの修正

Claude が直接修正し、再度 VERIFY を実行する。

## Step 4 — UPDATE

### 従来モード

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。

### ディレクトリモード

spec.md のチェックボックスを `[x]` に更新し、Review 結果を blockquote に記入する:

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
```
