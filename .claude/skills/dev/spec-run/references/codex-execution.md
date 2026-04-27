# 実行プロトコル（Codex モード, v3）

各 Gate を順番に実行する。**Gate 契約（Goal/Constraints/AC）を Codex に丸ごと渡し、AC が成立する状態まで自律的に実装させる。**

## 基本原則

**デフォルトで Codex に Gate 単位で委任する。** Claude が保持するのは、チェックリストで明確に該当する場合のみ。

## 実行ステップ

```
Step 0 — CONTEXT      仕様書の「参照すべきファイル」を全て Read（最初の Gate 着手前に1回だけ）
Preflight フェーズ     Preflight 該当時のみ、Claude main session が順次実行
Step 1 — IMPL         チェックリストで委任判断 → Codex or Claude（Gate 単位）
Step 2 — VERIFY       codex review（複雑さに応じて 1 回 or 3 回並列）+ AC 検証
Step 3 — FIX          FAIL がある場合のみ修正（最大 3 ラウンド）
Step 4 — UPDATE       tasks.json を更新（gate.passed / acceptanceCriteria / review / progress / status）
```

## Step 0 — CONTEXT

最初の Gate 着手前に 1 回だけ実行する。

### 0-1. codex-companion.mjs のパス解決

```bash
CODEX_COMPANION="$(bash .claude/skills/dev/spec-run/scripts/resolve-codex-plugin.sh)"
```

失敗した場合は codex プラグインが未インストール。Claudeモードにフォールバックする。

### 0-2. 仕様書の読み込み

1. spec.md の「参照すべきファイル」を全て Read
2. tasks.json を Read して以下を把握:
   - 全 `gates[]`（id / title / dependencies / goal / constraints / acceptanceCriteria / todos）
   - `preflight[]`
   - `progress` / `status`

## Preflight フェーズ（該当時のみ）

> **Codex の `workspace-write` sandbox はネットワーク完全ブロック + ワークスペース外書き込み禁止 + 対話不可。** Preflight 項目はこの制約を回避するため Claude main session が実行する。

`tasks.json.preflight[]` が 1 件以上あるときのみ実行する。

1. 各項目を記載順に処理
2. `manual: false` → Bash で `command` を実行 / `manual: true` → AskUserQuestion で操作確認
3. 各 Preflight の `ac` が成立しているか検証
4. 成立 → tasks.json の `preflight[].checked = true` を書き込む
5. 全 Preflight 完了後、Step 1 へ

### Preflight 失敗時

Claude モードと同じ手順（エラー報告 + 3 択フォールバック）。

## Step 1 — IMPL

各 Gate の IMPL 前に、以下の手順で委任先を決定する。

### 1-0. Gate 内の [SIMPLE] Todo の早期分離

Gate 内の Todo のうち title に `[SIMPLE]` プレフィックスがあるものは、チェックリスト評価をスキップして **Claude main session が直接実装** する。`[SIMPLE]` 以外の Todo の集合に対して以下のチェックリストを評価する。

### 1-1. 委任判断チェックリスト

`[SIMPLE]` を除いた残りの Todo について、以下 3 項目を確認する:

| # | チェック項目 | 「はい」の場合 |
|---|--------------|---------------|
| 1 | この Gate は **前の Gate の実装結果** を見て設計判断を変える必要があるか？ | Claude 保持 |
| 2 | 仕様が曖昧で **ユーザーに確認** しないと実装方針が決まらないか？ | Claude 保持 |
| 3 | この Gate は **他の Gate と同じファイル** を同時に変更する必要があるか？ | Claude 保持 |

- **3 項目すべて「いいえ」** → Codex に委任する
- **1 項目でも「はい」** → Claude が保持する。理由を記録する

「確実性」「複雑さ」「Claude の方が得意」のような主観的理由での保持は禁止。

### 1-2. Codex に委任する場合

#### 1-2-A. 並列実行判断

| 条件 | 実行方法 |
|------|----------|
| Gate が 1 つのまとまり | task 1 回 |
| Gate 内に独立した Todo グループが複数（dependencies が完全分離） | グループごとに task を `--background` で並列 |

#### 1-2-B. テンプレート選択

- Gate 内に `tdd: true` の Todo を含む → `roles/codex-tdd-developer.md`
- それ以外 → `roles/codex-developer.md`

#### 1-2-C. Gate 契約の組み立てと実行

tasks.json から現在の Gate のフィールドを抽出し、テンプレートに埋める:

- `goal.what` / `goal.why`
- `constraints.must` / `constraints.mustNot`
- `acceptanceCriteria[]`
- `todos[]`

完成したプロンプトを `.tmp/codex-prompt-{gate-id}.md` に書き出して実行（`.tmp/` 不在なら `mkdir -p .tmp`）:

```bash
node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-prompt-A.md
```

並列時:

```bash
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-A-1.md
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-A-2.md
node "$CODEX_COMPANION" status --wait
```

#### 1-2-D. 結果確認

- 成功 → Claude がコミット
- 失敗 → **エラー診断** を実行してからリトライ判断

### 1-3. Claude が直接実装する場合

以下のいずれかに該当する場合:

1. **`[SIMPLE]` ラベル付き Todo の集合** — チェックリスト評価をスキップ。VERIFY も SKIPPED
2. **チェックリストで「はい」が 1 つ以上** — 理由を記録して Claude が実装

ロール選択:

- Gate 内に `tdd: true` Todo を含む → `roles/tdd-developer.md`
- それ以外 → `roles/implementer.md`

実装完了後、コミット。

### Codex エラー診断（task / review 共通）

Codex コマンドが失敗した場合、**黙ってフォールバックせず**、以下の手順で原因を特定してユーザーに報告する。

#### 診断スクリプトの実行

```bash
bash .claude/skills/dev/spec-run/scripts/diagnose-codex.sh "$CODEX_COMPANION"
```

#### エラー分類と対処

| エラーメッセージ | 原因 | 自動対処 | ユーザー報告 |
|----------------|------|---------|-------------|
| `Invalid request` | プロジェクト未信頼 / API 仕様変更 / モデル非対応 | 不可 | **必須** |
| `401` / `Unauthorized` | トークン期限切れ | 不可 | **必須** — `codex auth` 案内 |
| `429` / `rate_limit` | レートリミット | 30 秒待ってリトライ（最大 2 回） | リトライ後失敗なら報告 |
| `timeout` / `ETIMEDOUT` | ネットワーク / 応答遅延 | 1 回リトライ | リトライ後失敗なら報告 |
| `ECONNREFUSED` | broker ソケット切断 | 不可 | **必須** — Claude Code 再起動を案内 |
| その他 | 不明 | 不可 | **必須** |

#### ユーザーへの報告テンプレート

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

AskUserQuestion で 3 択を提示する。**暗黙のフォールバックは禁止**。

#### リトライポリシー

| 種別 | 自動リトライ | `--resume-last` | 最大回数 |
|------|------------|----------------|---------|
| レートリミット（429） | 30 秒待ち | 不要 | 2 回 |
| タイムアウト | 即時 | 使用 | 1 回 |
| その他（Invalid request 等） | しない | — | — |

## Step 2 — VERIFY

### `[SIMPLE]` 専用 Gate の早期 SKIP

Gate に含まれる Todo がすべて `[SIMPLE]` の場合、複雑さ判断をスキップして VERIFY を SKIPPED にする。

`gates[].review = { result: "SKIPPED", fixCount: 0, summary: "[SIMPLE]" }` を書き込み Step 4 へ。

### 複雑さ判断

通常の Gate は以下で判定:

| 判断要素 | SKIP | シンプル寄り | 複雑寄り |
|----------|------|--------------|----------|
| 変更内容 | docs / config / コメントのみ | コード変更（軽微） | コード変更（重要） |
| 変更ファイル数 | — | 1-2 | 3+ |
| 影響範囲 | — | 局所的 | 複数モジュール横断 |
| リスク | なし | 低 | 高（認証 / データ / API） |
| ロジック複雑度 | なし | 単純 | 条件分岐 / 状態 / 非同期 |

**迷ったら複雑モード。**

### SKIP — レビュー不要

`gates[].review = { result: "SKIPPED", fixCount: 0, summary: "docs only" }` を書き込み Step 4 へ。

### シンプルモード — codex review 1 回

`references/codex-review-instructions.md` の **統合版テンプレート** を使用。focus テキストを `.tmp/codex-review-focus.md` に書き出し stdin で渡す。

> **重要**: VERIFY は **native `codex review` CLI** を使う。`node "$CODEX_COMPANION" review` は使わない。
> **CLI 制約**: `--commit` と `[PROMPT]` は排他。IMPL 直後の VERIFY では `[PROMPT]` 方式（`origin/main..HEAD` 自動検出）。

```bash
codex review - < .tmp/codex-review-focus.md
```

未コミット差分は `codex review --uncommitted`。

### 複雑モード — codex review 3 回並列

`references/codex-review-instructions.md` の **quality / correctness / conventions** 各テンプレートを使用。

```bash
codex review - < .tmp/codex-review-quality.md &
codex review - < .tmp/codex-review-correctness.md &
codex review - < .tmp/codex-review-conventions.md &
wait
```

### AC 検証

レビューと並行し、各 AC の検証手段（コマンド / テスト / HTTP / 手動）を実行し、`gates[].acceptanceCriteria[].checked` が全て `true` になっているか確認する。Codex が書き漏らした AC があれば main session が補完する。

### review 失敗時

「Codex エラー診断」のフローに従う。review はコード変更を伴わないため、フォールバック選択肢は:

1. 対処後にリトライ
2. Claude が直接レビュー（Agent sonnet）
3. テスト通過のみで PASS（変更が軽微 + テスト全パスの場合のみ）

### 結果の判定

`codex review` は優先度付きコメントを返す（`[P1]` critical, `[P2]` important, `[P3]` minor）。

- コメントなし / P3 のみ → PASS
- P2 あり → Claude が精査して PASS / FAIL 判断
- P1 あり → FAIL
- 複雑モード: 3 観点すべて PASS → 全体 PASS、いずれか FAIL → 全体 FAIL
- AC が未 checked のまま残っている → FAIL（実装エージェントが AC 未達のまま完了報告した）

## Step 3 — FIX

FAIL の場合のみ。最大 3 ラウンド。

### Codex 委任タスクの修正

`codex review` の指摘内容と未達 AC を含めて `task --write --resume-last` で修正委任:

```bash
node "$CODEX_COMPANION" task --write --resume-last --prompt-file .tmp/codex-fix-prompt.md
```

### Claude 実装タスクの修正

main session または対応するロールエージェントが直接修正し、再度 VERIFY。

## Step 4 — UPDATE

Codex 完了後 / Claude 実装後に tasks.json を Edit する。**spec.md は直接編集しない。**

### 更新対象フィールド

1. **該当 Gate の `acceptanceCriteria[].checked`**: 全 AC を `true` に
2. **該当 Gate の `review`**: `{ result, fixCount, summary }`
   - `[SIMPLE]` 専用 Gate の場合: `{ result: "SKIPPED", fixCount: 0, summary: "[SIMPLE]" }`
3. **該当 Gate の `passed`**: 全 AC checked + `review.result` が PASSED / SKIPPED なら `true`
4. **トップレベル `progress` / `status`**: Claudeモードと同じ算出ルールで再計算

### Codex 完了後の spec.md 同期

PostToolUse hook は Claude Code のツール呼び出しに対して発火するため、Codex 内部の編集には反応しない。Codex 完了後、main session の Claude が手動で sync-spec-md を実行する:

```bash
node "${CLAUDE_PROJECT_DIR}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs" "${tasks_json_path}"
```

---

## worktree モード（オプション）

SKILL.md ステップ 4 で worktree 使用を選択した場合、本プロトコルは worktree 内 cwd で実行される。

### 前提

- `cd $WORKTREE_PATH` 実行済み
- Codex プラグイン（`resolve-codex-plugin.sh`）が worktree cwd で動作することを前提

### 各 Step の差分

| Step | 差分 |
|------|------|
| Step 0-1 `resolve-codex-plugin.sh` | worktree 内から実行 |
| Step 0-2 仕様書読み込み | worktree 内のパスで Read |
| Preflight | worktree 内で実行 |
| Step 1 IMPL（Codex 委任） | `task --write --prompt-file` を worktree cwd で実行。`.tmp/` は worktree 内 |
| Step 1 IMPL（Claude 保持） | worktree 内で編集・コミット |
| Step 2 VERIFY | `codex review` を worktree cwd で実行（`origin/master..HEAD` が feature/{slug} 対象） |
| Step 3 FIX | `task --write --resume-last` を worktree cwd で実行 |
| Step 4 UPDATE | worktree 内の tasks.json を更新 → main session が sync-spec-md.mjs を手動実行 |

### .tmp/ 配置

- `.tmp/` は `.gitignore` 登録済み。worktree 側でも自動的に git 管理外
- worktree ごとに独立した `.tmp/` を持つため並行実行時の衝突なし
- 完了処理での `rm -f .tmp/codex-*.md`:
  - worktree 側: cleanup-worktree.sh で worktree ごと削除されるため不要
  - base 側: cwd を base に戻した後、念のため削除

### Codex プラグインのパス解決失敗時

- **対処 A**: base 側で `resolve-codex-plugin.sh` を実行 → 絶対パスを取得 → worktree に cd してから使う
- **対処 B**: 動作しない場合は worktree モードと Codex モードの併用を禁止

### worktree のライフサイクル

セットアップは `references/worktree-setup.md`、merge / cleanup は `references/worktree-teardown.md` を参照。
