# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 基本原則

**デフォルトで Codex に委任する。** Claude が保持するのは、チェックリストで明確に該当する場合のみ。

## 実行ステップ

```
Step 0 — CONTEXT      仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Preflight フェーズ     Preflight セクション該当時のみ、Claude main session が順次実行（スキップ条件あり）
Step 1 — IMPL         チェックリストで委任判断 → Codex or Claude
Step 2 — VERIFY       codex review（複雑さに応じて1回 or 3回並列）
Step 3 — FIX          FAIL がある場合のみ修正（最大3ラウンド）
Step 4 — UPDATE       モードに応じて tasks.json または spec.md を更新する
```

## Step 0 — CONTEXT

最初の Todo 着手前に1回だけ実行する。

### 0-1. codex-companion.mjs のパス解決

```bash
CODEX_COMPANION="$(bash .claude/skills/dev/spec-run/scripts/resolve-codex-plugin.sh)"
```

失敗した場合は codex プラグインが未インストール。Claudeモードにフォールバックする。

### 0-2. 仕様書の読み込み

#### シングルモード

仕様書の「参照すべきファイル」を全て Read する。

#### ディレクトリモード（v1 / v2 共通）

1. spec.md の「参照すべきファイル」を全て Read する
2. tasks.json を Read して全体構造（`gates`, Todo の `id`/`gate`/`title`/`dependencies`）を把握する
3. 各 Todo の `impl` フィールドは**この時点では読まない**（部分読み込みで後述）

**v2 モードでの差分**: tasks.json の `steps[]` / `status` / `progress` フィールドも把握する。これらは Step 4 UPDATE で更新する対象になる。

## Preflight フェーズ（該当時のみ）

> **Codex の `workspace-write` sandbox はネットワーク完全ブロック（DNS 解決不可）+ ワークスペース外書き込み禁止 + 対話不可。** Preflight 項目はこの制約を回避するため Claude main session が実行する。

仕様書に `## Preflight` セクション（通常モード）または `tasks.json` の `preflight` 配列（ディレクトリモード）が存在し、項目が 1 件以上ある場合のみ実行する。該当が無ければ何もせず Step 1 へ進む。

### 実行手順

1. Preflight 項目を記載順に処理する（依存関係はないため順序通り）
2. 各項目を判定する:
   - `manual: false`（自動実行可能）→ Bash ツールで `command` を実行
   - `manual: true`（ユーザー手動操作必須）→ AskUserQuestion で操作内容と完了確認を提示し、完了報告を待つ
3. 実行成功 → 仕様書の該当チェックボックスを `[x]` に更新する
4. 全 Preflight 完了後、Step 1 へ進む

### Preflight 失敗時

Claude main session での実行が失敗した場合:

1. sandbox 起因ではないため diagnose スクリプトは不要
2. エラー内容をユーザーに直接報告する
3. AskUserQuestion で以下を選択させる:
   - 1. 手動で対応後リトライ
   - 2. この Preflight 項目をスキップして残りの Gate 実行を継続（リスク警告付き）
   - 3. 作業中断

### 注意

- Preflight は Gate/Todo とは独立して実行する（Gate 冒頭ではなく spec-run 起動直後に1回だけ）
- **Preflight セクションが無い場合は完全にスキップ**（既存仕様書との後方互換のため警告なし）
- Claudeモードと Codex モードで Preflight フェーズの動作は完全に同一

## Step 1 — IMPL

### 委任判断チェックリスト（必須）

各 Todo の IMPL 前に、以下の手順で委任先を決定する。

#### 0. [SIMPLE] ラベルの早期確認

Todo の title に `[SIMPLE]` プレフィックスがある場合、以下のチェックリストを**評価せずスキップ**して Claude が直接実装する。理由の記録は不要。

#### 1. 3項目チェックリスト

`[SIMPLE]` ラベルがない場合のみ、以下の 3 項目を確認する。

| # | チェック項目 | 「はい」の場合 |
|---|-------------|---------------|
| 1 | この Todo は**前の Todo の実装結果**を見て設計判断を変える必要があるか？ | Claude 保持 |
| 2 | 仕様が曖昧で**ユーザーに確認**しないと実装方針が決まらないか？ | Claude 保持 |
| 3 | この Todo は**他の Todo と同じファイル**を同時に変更する必要があるか？ | Claude 保持 |

- **3項目すべて「いいえ」→ Codex に委任する**（例外は `[SIMPLE]` ラベルのみ）
- **1項目でも「はい」→ Claude が保持する。理由を記録する**

「確実性」「複雑さ」「Claude の方が得意」のような主観的理由での保持は禁止（spec-run 実行時の判定に限る。ただし spec 作成時に付与された `[SIMPLE]` ラベルは例外で、spec-run での override は禁止）。

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

以下の2系統のいずれかに該当する場合に Claude が直接実装する:

1. **`[SIMPLE]` ラベルあり** — チェックリスト評価をスキップして Claude が実装。VERIFY は SKIPPED（Step 2 参照）
2. **チェックリストで「はい」が 1 つ以上** — 従来ルート。理由を記録して Claude が実装

いずれの場合も仕様に忠実に実装する。`[TDD]` ラベルがある場合は `roles/tdd-developer.md` を参照。
実装完了後、変更をコミットする。

## Step 2 — VERIFY

### [SIMPLE] ラベルの早期 SKIP

Todo の title に `[SIMPLE]` プレフィックスがある場合、複雑さ判断もドキュメント判定も行わず無条件で VERIFY をスキップする。

記録形式: `> **Review XX**: ⏭️ SKIPPED ([SIMPLE])`

Step 3（FIX）は不要。そのまま Step 4（UPDATE）へ進む。

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

> **重要**: VERIFY は **native `codex review` CLI** を使う。`node "$CODEX_COMPANION" review` は使わない（companion v1.0.2 からフォーカステキスト廃止。フォーカス付きは `adversarial-review` に移行したが、VERIFY には native CLI を継続使用する）。
> **CLI 制約**: `--commit` と `[PROMPT]` は排他的引数で併用不可。IMPL 直後の VERIFY では HEAD が対象コミットなので `[PROMPT]` 方式（`origin/main..HEAD` 自動検出）で十分。

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

### v2 ディレクトリモード

Codex が tasks.json を Edit で更新する。**spec.md は直接編集しない。**

更新対象フィールド:

1. **該当 Todo の `steps[]`**:
   - `steps[0].checked` (impl step): `true`
   - `steps[1].checked` (review step): `true`
   - `steps[1].review`: `{ "result": "PASSED"|"FAILED"|..., "fixCount": n, "summary": "..." }`
   - **`[SIMPLE]` ラベルの場合**: `steps[1].review` は `{ "result": "SKIPPED", "fixCount": 0, "summary": "[SIMPLE]" }` を格納する
   - `steps[]` は `[SIMPLE]` でも**必ず2要素**（impl + review）を維持する。review step を削除するのではなく `result: "SKIPPED"` で埋めることでスキーマ互換を保つ

2. **トップレベル `status` と `progress`**（再計算）:
   - `total = sum of all todos[].steps[].length`（固定値、todos 数 × 2）
   - `completed = count of all steps where checked == true`
   - `status`: `completed == 0` → `not-started`、`0 < completed < total` → `in-progress`、`completed == total && !reviewChecked` → `in-review`、`completed == total && reviewChecked` → `completed`

**Codex 完了後の spec.md 同期**: PostToolUse hook は Claude Code のツール呼び出しに対して発火するため、Codex 内部の編集には反応しない。Codex 完了後、main session の Claude が手動で sync-spec-md を実行する:

```bash
node "${CLAUDE_PROJECT_DIR}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs" "${tasks_json_path}"
```

### v1 ディレクトリモード

spec.md のチェックボックスを `[x]` に更新し、Review 結果を blockquote に記入する:

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
```

### シングルモード

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。

---

## worktree モード（オプション）

SKILL.md の Step 4 で worktree 使用を選択した場合、本 codex-execution プロトコルは **worktree 内の cwd** で実行される。差分は以下の通り。

### 前提

- `cd $WORKTREE_PATH` が `worktree-setup.md` フェーズ 2 末尾で実行済み
- Bash tool の cwd は worktree 内
- Codex プラグイン（`resolve-codex-plugin.sh`）は **worktree cwd でも動作する前提**（Gate D Todo D1 で検証済みであること）

### 各 Step の差分

| Step | 差分 |
|------|------|
| Step 0-1 `resolve-codex-plugin.sh` | worktree 内から実行。パス解決が成功することを確認 |
| Step 0-2 仕様書読み込み | worktree 内のパスで Read（worktree は master から派生なので同じファイル構造） |
| Preflight フェーズ | worktree 内で実行 |
| Step 1 IMPL（Codex 委任） | `node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-prompt.md` を worktree cwd で実行。`.tmp/` は worktree 内に作成される（`mkdir -p .tmp` も worktree 側） |
| Step 1 IMPL（Claude 保持） | worktree 内のファイルを直接編集、worktree 内でコミット |
| Step 2 VERIFY | `codex review - < .tmp/codex-review-focus.md` を worktree cwd で実行。差分検出は `origin/master..HEAD` が worktree の feature/{slug} に対して自然に動作する |
| Step 3 FIX | `task --write --resume-last` を worktree cwd で実行 |
| Step 4 UPDATE | v2: worktree 内の tasks.json を更新 → Codex 完了後に main session が `sync-spec-md.mjs` を手動実行 / v1/single: worktree 内の spec.md を更新 |

### .tmp/ 配置に関する注意

- `.tmp/` は `.gitignore` に登録済みなので worktree 側でも自動的に git 管理外
- worktree ごとに独立した `.tmp/` を持つため、並行実行時にプロンプトファイル名の衝突は発生しない
- 完了処理での `rm -f .tmp/codex-*.md` は:
  - worktree 側: cleanup-worktree.sh で worktree ごと削除されるため不要
  - master 側: cwd を master に戻した後、念のため削除（非 worktree モードと同じ処理）

### Codex プラグインのパス解決

`resolve-codex-plugin.sh` が worktree cwd で動作しない場合（Gate D 検証で判明した場合）、以下の対処を取る:

- **対処 A**: master 側で `resolve-codex-plugin.sh` を実行して `$CODEX_COMPANION` を取得 → worktree に cd してから使う（パスは絶対パスなので worktree からも参照可能なはず）
- **対処 B**: 動作しない場合は worktree モードと Codex モードの併用を禁止する旨を SKILL.md に記載（Gate D の検証結果次第）

### 仕様書に記載されるエラー診断

既存の「Codex エラー診断」セクションはそのまま適用される。worktree 内で実行した結果のエラーも同じ診断スクリプト・分類表・ユーザー報告テンプレートを使う。

### worktree モードの詳細なライフサイクル

worktree セットアップ手順は `references/worktree-setup.md`、完了時の merge / cleanup は `references/worktree-teardown.md` を参照。
