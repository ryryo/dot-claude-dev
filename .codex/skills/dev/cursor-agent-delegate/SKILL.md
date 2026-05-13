---
name: dev:cursor-agent-delegate
description: |
  Cursor CLI の headless agent を使い、Composer 2 Fast に低〜中複雑度の実装・調査・テスト作業を委任し、
  Codex 側で差分・検証結果・範囲逸脱を確認する。
  依頼内容・参照資料・既存コードを読み込み、write scope を絞ったプロンプトで cursor-agent を実行する。
  完了後は main Codex がレビュー・検収を担う。

  Trigger:
  cursor-agent-delegate, Cursor CLI 委任, Cursor Agent 委任, Composer 2 Fast に作業依頼,
  composer-2-fast 実行, Cursor Agent で実装, 並列エージェント実行
user-invocable: true
---

# cursor-agent-delegate

Cursor CLI の headless mode で `composer-2-fast` に作業を投げ、返ってきた差分を main Codex が検収する。

**役割分担:**

| 役割 | 担当 |
|------|------|
| orchestrator / reviewer | main Codex |
| worker（実装・調査・テスト） | Cursor Agent |
| 最終統合・進捗ファイル更新・commit / push | main Codex（ユーザーが明示しない限り） |

---

## 前提

- CLI コマンド名は `cursor-agent`（または `agent`）。実在するコマンドを確認し、以後 `CURSOR_AGENT_BIN` として扱う。
- headless 実行は `-p / --print` フラグを使う。
- 編集ありの実行は `--force`、read-only の調査・レビューは `--mode ask` または `--mode plan`（`--force` 不要）。
- `--mode ask` は既存コードの確認・要約・レビュー観点の洗い出しに使う。`--mode plan` は実装方針や手順案を作らせるが、まだ編集させない場合に使う。
- モデルは原則 `--model composer-2-fast` を明示。毎回 `models` で存在確認し、なければユーザーに報告して代替を確認する。
- `--workspace <path>` は必ず指定する。暗黙の cwd に依存しない。
- headless 実行中に workspace 信頼確認で止まらないよう、編集ありの実行では `--trust` を付ける。

---

## Step 1: CLI と環境を確認する

```bash
command -v cursor-agent || command -v agent
"$CURSOR_AGENT_BIN" --version
"$CURSOR_AGENT_BIN" status
"$CURSOR_AGENT_BIN" models | rg '^composer-2-fast\b'
git status --short
```

- `status` が未ログインなら実行せず、`cursor-agent login` または `CURSOR_API_KEY` が必要だと報告する。
- `composer-2-fast` が存在しない場合も実行しない。
- 開始時の `git status --short` と対象ブランチを記録する。既存の未コミット変更はユーザーまたは他 agent の作業として扱い、巻き戻さない。

**ゲート**: `composer-2-fast` が確認できなければ次に進まない。

---

## Step 2: 対象タスクを選ぶ

Cursor Agent に投げてよいのは、write scope と検証条件を明確にできる作業だけ。

**Cursor Agent に向いている作業:**
- 純粋関数・helper・schema・validator・adapter・単体テスト
- 新規小ディレクトリに閉じる実装
- 依存関係が薄く、単独で完了条件を検証できる低〜中複雑度タスク
- 既存 UI / state / routing への接続が薄い小さな修正
- 調査・既存実装の要約・テスト観点の洗い出し

**main Codex に残す作業:**
- 共通 state・editor / canvas・export pipeline・routing・認可・DB migration など影響範囲が広い変更
- 複数領域にまたがる最終統合
- 進捗・状態ファイルの更新、完了判定、生成ドキュメントの同期
- commit / push / PR
- 仕様が曖昧で、期待する振る舞いを agent に渡せない作業

**ゲート**: write scope と検証条件を言語化できなければ次に進まない。

---

## Step 3: 実行範囲を決める

単発の read-only 調査は現在の workspace でよい。

編集を伴う場合:
- `git status --short` で既存変更を把握してから実行する。
- write scope をファイルまたはディレクトリ単位で明示する。
- 既存の未コミット変更と衝突しそうな作業は Cursor Agent に投げず、main Codex 側で扱うかユーザーに確認する。
- `--workspace` で対象 workspace を必ず渡す。

**ゲート**: write scope のリストアップが完了してから次に進む。

---

## Step 4: worker プロンプトを作る

プロンプトには結論ではなく契約を渡す。以下をすべて含める。

```text
You are a worker agent running inside this repository.

Workspace:
<絶対パス>

Goal:
<具体的なタスク 1 件>

Read first:
- <絶対パス>
- <絶対パス>

Write scope:
- You may edit only: <パス>
- Do not edit: <パス>
- Do not update progress/state files, generated planning docs, commits, branches, remotes, or package lockfiles unless explicitly listed in write scope.
- Do not revert existing uncommitted changes or files outside your scope.

Implementation constraints:
- <制約>

Verification:
- Run: <コマンド>
- If the command cannot run, explain the exact reason.

Final report:
- Files changed
- Summary of behavior changed
- Verification commands and results
- Anything intentionally left for main Codex
```

長いプロンプトは一時ファイルに書き出し、`PROMPT="$(< "$PROMPT_FILE")"` で読み込んで渡す。
（`-f` は Cursor CLI では `--force` の短縮形なので、プロンプトファイル指定には使わない。）

**ゲート**: プロンプトに上記の必須項目がすべて含まれていることを確認してから実行する。

---

## Step 5: Cursor Agent を実行する

**read-only 調査:**

```bash
"$CURSOR_AGENT_BIN" -p \
  --mode ask \
  --output-format text \
  --workspace "$WORKSPACE" \
  --model composer-2-fast \
  "$PROMPT"
```

**編集あり:**

```bash
"$CURSOR_AGENT_BIN" -p \
  --force \
  --trust \
  --output-format stream-json \
  --stream-partial-output \
  --workspace "$WORKSPACE" \
  --model composer-2-fast \
  "$PROMPT" | tee "$LOG"
```

並列実行は 2〜4 件を上限とし、write scope が重ならないものだけ同時に投げる。
各 agent ごとに workspace・log path・allowed write scope を記録する。

---

## Step 6: 結果を検収する

Cursor Agent 終了後、main Codex が必ず確認する。

```bash
git status --short
git diff --name-only
git diff --stat
```

**確認観点:**
- 変更ファイルが write scope に収まっている
- 既存の未コミット変更を巻き戻していない
- agent の報告と実際の diff が一致している
- 依頼内容・完了条件・検証条件に対して不足がない
- 検証コマンドが成功している、または失敗理由が妥当

範囲外の変更がある場合は、agent の log と diff を確認してから判断する。
ユーザーや他 agent の既存変更と混ざっている可能性があるため、安易に revert しない。
Cursor Agent が作った範囲外変更だけを特定できる場合に限り main Codex が修正し、特定できなければユーザーに判断を仰ぐ。

**ゲート**: すべての確認観点をパスしてから次に進む。

---

## Step 7: 報告する

計画ファイル・進捗管理ファイルがある場合:
- Cursor Agent の報告だけで完了状態にしない。
- main Codex が完了条件を再検証してから状態を更新する。
- 同期スクリプトや生成手順がある場合は、プロジェクト規定の手順に従う。

最終報告に含める内容:
- 実行した Cursor CLI コマンドの要約
- 使用モデル（通常 `composer-2-fast`）
- Cursor Agent が変更したファイル
- main Codex が実施した検証
- 採用した差分・棄却した差分・残課題

---

## 参照

- [Cursor CLI overview](https://cursor.com/docs/cli/overview)
- [Cursor Headless CLI](https://cursor.com/docs/cli/headless)
- [Cursor CLI parameters](https://cursor.com/docs/cli/reference/parameters)
