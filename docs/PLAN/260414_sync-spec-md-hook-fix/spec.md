# sync-spec-md hook 動作不良の網羅的診断・修正

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

`PostToolUse` hook (`.claude/hooks/dev/sync-spec-md-hook.sh` → `sync-spec-md.mjs`) が `tasks.json` 編集時に `spec.md` の generated 領域を自動更新する仕組みが、ablog プロジェクトの実測で動作していないことが判明した。既存プラン `260413_hook-verification` は「検証済み」となっているが、**hook 発火 / スクリプト実行 / main() 呼び出し / 置換処理のどの層で止まっているかは未確定**。まず dot-claude-dev 本体（symlink なし直参照）と ablog 側（symlink 経由）の両方で実証的に切り分け、確定した原因を恒久修正する。

## 背景

### 発端

ablog プロジェクト（`/home/ryryo/ablog/docs/PLAN/260414_tweet-post/` で `/dev:spec-run` 実行中）で、`tasks.json` を `Edit` しても `spec.md` の generated 領域 (`<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 診断層
Gate B: 修正層（Gate A 完了後）
Gate C: 動作確認層（Gate B 完了後）
```

### Gate A: 診断層

> hook 発火の 6 層を実証的に切り分ける

- [x] **A1**: sync-spec-md-hook.sh に診断用 debug log を一時的に仕込む
  > **Review A1**: ✅ PASSED — 全6層ロギング確認済み。手動 hook 呼び出しで expected 7行全通過。spec.md 自動更新も確認
- [ ] **A2**: tasks.json を実 Edit して hook 発火パスをログ検証
  > **Review A2**: _未記入_
- [ ] **A3**: sync-spec-md.mjs の isDirectRun バグを単体で再現（A2 で仮説 Z が有力な場合のみ）
  > **Review A3**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: 修正層

> direct-run 判定恒久化 + エラー可視化 + engines 明記

- [ ] **B1**: [TDD] sync-spec-md.mjs の direct-run 判定を import.meta.main + realpath フォールバックに修正（仮説 Z 確定時のみ）
  > **Review B1**: _未記入_
- [ ] **B2**: sync-spec-md-hook.sh に恒常的なエラー可視化機構を追加
  > **Review B2**: _未記入_
- [ ] **B3**: package.json の engines.node を 22.18+ に明記
  > **Review B3**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: 動作確認層

> テスト通過 + self-test + ablog 回帰 + 診断ログ除去

- [ ] **C1**: dot-claude-dev の vitest 全通過確認
  > **Review C1**: _未記入_
- [ ] **C2**: dot-claude-dev 内で tasks.json Edit → spec.md 自動更新の self-test
  > **Review C2**: _未記入_
- [ ] **C3**: ablog 側 tweet-post で tasks.json Edit → spec.md 自動更新の回帰確認
  > **Review C3**: _未記入_
- [ ] **C4**: A1 で追加した診断用 debug log を除去（恒常エラー可視化は残す）
  > **Review C4**: _未記入_

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->`) が更新されないことが発覚。tasks.json 側では A1 Todo が `checked: true` + Review `SKIPPED` になっているのに、spec.md 側は `[ ]` / `_未記入_` のまま。

### 既存の `260413_hook-verification` が不十分だった理由

- `hook-verify.txt` の新規作成 1 件だけで「検証完了」としており、tasks.json 編集による発火パスを実証していない
- pure 関数（`generateTaskListSection` / `replaceGeneratedSection`）のユニットテストはあるが、`main()` 呼び出し判定（`isDirectRun`）の回路は検証されていない
- シンボリックリンク配下（他プロジェクトへの `.claude/skills/dev` 配布経路）での動作確認がない

### 原因についての仮説（Gate A で実証確認するまでは未確定）

現時点では「どこで止まっているか」の仮説が複数あり、**いずれも実環境では未検証**。順に潰す必要がある:

仮説 X: hook 自体が発火していない（Claude Code の PostToolUse 設定または matcher の問題）
仮説 Y: hook は発火しているが filter（tool_name / file_path）で脱落している
仮説 Z: hook は sync-spec-md.mjs を呼んでいるが node スクリプトの isDirectRun 判定で main() が呼ばれない

仮説 Z の裏付け（理論計算）:

```js
const isDirectRun = process.argv[1] && (
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url === `file://${resolve(process.argv[1])}`
);
```
- Node 22.20 では `import.meta.url` は **realpath 解決済み**の URL を返す（symlink 解決）
- `process.argv[1]` / `resolve(argv[1])` はどちらも **realpath 解決しない**
- したがって symlink 経由で呼ばれた場合、両者は必ず不一致 → `main()` が呼ばれずサイレント終了（exit 0）
- ただし **symlink なし直参照（dot-claude-dev 本体）で動いているかは未確認**。もし direct 呼び出しでも動いていない場合、仮説 X/Y のどこかに別の原因がある。

### 実証順序

Gate A では以下の順で切り分ける:

1. **dot-claude-dev 本体（symlink なし）で hook + sync が動くか** — 仮説 X/Y を排除できる最初のゲート
2. dot-claude-dev で動き ablog で動かない場合 → 仮説 Z（symlink 問題）が確定
3. dot-claude-dev でも動かない場合 → hook 発火 / 設定の問題が優先課題になり、設計決定を見直す

この切り分けを済ませてから Gate B の修正に入る。

### 未検証の周辺事項

| # | 層 | 検証状態 |
|---|----|----------|
| 1 | Claude Code が Edit/Write/MultiEdit で PostToolUse hook を発火させているか | 未検証 |
| 2 | hook スクリプトが正しい stdin payload を受け取るか | 未検証 |
| 3 | hook スクリプトが tool_name / file_path フィルタを通過するか | 未検証 |
| 4 | hook スクリプトが sync-spec-md.mjs を正しい引数で呼んでいるか | 未検証 |
| 5 | sync-spec-md.mjs の `main()` が呼ばれているか | **理論的には NG**（isDirectRun 判定）、**実測未確認**（direct 実行では動く可能性あり） |
| 6 | `main()` の各処理段階が想定通りか（parse → read → replace → write） | 未検証 |

Gate A では dot-claude-dev 本体（symlink なし）を最初に検証し、1〜6 のどの層で失敗するかを実証する。仮説 Z が確定した場合のみ Gate B で symlink 対応修正、それ以外は別設計で対処する。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1 | 診断手法 | hook スクリプトに一時 debug log を仕込み実 Edit で層別確認 | 推測ではなく実証。silent failure の可能性を排除できる |
| 1a | 診断の最初の対象 | **dot-claude-dev 本体（symlink なし直参照）** で hook + sync が動くかを最初に検証 | symlink 問題と hook 問題を最短で切り分けるため。ここで動けば仮説 Z（symlink 問題）に絞れる |
| 2 | ログ出力先 | `/tmp/sync-spec-md-hook-debug.log` に append | 環境変数不要、複数セッション串刺し可、diagnose 後すぐ削除 |
| 3 | direct-run 判定の恒久修正（仮説 Z 確定時のみ） | `import.meta.main` を第一、`realpathSync(argv[1]) + pathToFileURL` を第二フォールバック | Node 22.18+ native API（2025-07 リリース、22.20 でバックポート済）。symlink / Windows / percent-encoding のすべてに強い。ただし仮説 Z が未確定なら Gate B の設計自体を見直す |
| 4 | 文字列結合 `file://${path}` の廃止 | `pathToFileURL()` に統一 | ドライブレター / percent-encoding で string 結合版は脆弱。Node 公式推奨 |
| 5 | engines 要件 | dot-claude-dev の `package.json` に `engines.node >= 22.18.0` を明記 | `import.meta.main` の導入バージョン。現在の CI/ローカルとも 22.20 で条件を満たす |
| 6 | hook 側のエラー可視化 | `sync-spec-md.mjs` の exit / stderr を常に `/tmp/sync-spec-md-hook.log`（診断用ではなく恒常的）にティーで残す | 今回のような silent failure を次回以降即検知できる。容量はローテートなしで十分軽量 |
| 7 | 修正対象ファイルの権威 | ロジック本体は `dot-claude-dev` 側のみ（ablog 等は symlink 経由） | 配信構造を維持。各プロジェクトでの重複修正を避ける |
| 8 | TDD 対象 | `sync-spec-md.mjs` の main 呼び出し判定は subprocess テストで検証 | `import.meta.main` の動作を unit ではなく実コマンドで確認しないと意味がない |
| 9 | 診断ログの始末 | Gate C 最終 Todo で debug log 行を **必ず除去** | 本番環境に `/tmp` 書き込みが残るのは好ましくない。恒常エラー可視化（#6）は残す |
| 10 | 260413_hook-verification の扱い | 触らず、本 spec の背景で補足するのみ | 過去仕様書を書き換えると履歴が壊れる。完了扱いのまま残す |
| 11 | 他プロジェクトへの展開 | dot-claude-dev 側の修正のみで symlink 経由の全プロジェクトに自動反映 | setup-project の create-settings-json.sh テンプレート（commit e9c0504）はそのままで良い |
| 12 | Windows 対応 | `pathToFileURL` を使うことで実質的に対応（ユーザー環境は WSL2 Linux だが副作用で他環境でも動く） | 文字列結合 `file://` は Windows 互換性なし。`pathToFileURL` に統一で広く対応 |

## アーキテクチャ詳細

### 修正後の direct-run 判定

`dot-claude-dev/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` 末尾:

```js
import { realpathSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

// Node 22.18+ の import.meta.main を優先、古い環境には realpath 両側正規化でフォールバック
const isDirectRun = typeof import.meta.main === 'boolean'
  ? import.meta.main
  : (
      process.argv[1]
        ? import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
        : false
    );
if (isDirectRun) {
  main();
}
```

### 診断ログのフォーマット（Gate A で仕込み / Gate C で除去）

`sync-spec-md-hook.sh` 冒頭（`set -e` の次、`INPUT=$(cat)` の前）に挿入:

```bash
DEBUG_LOG="/tmp/sync-spec-md-hook-debug.log"
{
  echo "=== $(date -Iseconds) | PID $$ ==="
  echo "CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-<unset>}"
  echo "PWD=$(pwd)"
} >> "$DEBUG_LOG"
```

各段階の通過前に `echo "step: tool_name ok ($TOOL_NAME)" >> "$DEBUG_LOG"` のような行を加え、6 層（hook 起動 / INPUT 読み取り / tool_name フィルタ / file_path 取得 / tasks.json フィルタ / sync-spec-md.mjs 呼び出し前後）を段階的にロギングする。

### 恒常エラー可視化（Gate B で追加 / Gate C で残置）

`sync-spec-md-hook.sh` の `node` 呼び出し部を以下に差し替え:

```bash
ERR_LOG="/tmp/sync-spec-md-hook.log"
if ! node "$SYNC_SCRIPT" "$FILE_PATH" 2>>"$ERR_LOG"; then
  {
    echo "=== $(date -Iseconds) | sync-spec-md.mjs failed ==="
    echo "script=$SYNC_SCRIPT"
    echo "tasks_json=$FILE_PATH"
  } >> "$ERR_LOG"
fi
```

診断用 `DEBUG_LOG` と異なり、**恒常的に残す**。次回以降の silent failure 即検知用。

### 層別診断マトリクス

Gate A の実 Edit 後、`/tmp/sync-spec-md-hook-debug.log` を見て以下を判定する:

| ログに出る行 | 意味 | 次の対処 |
|--------------|------|---------|
| そもそも何も出ない | 層 1 (hook 未発火) | settings.json / Claude Code 側の問題。AskUserQuestion でユーザー確認 |
| `=== ...===` のみ | 層 2 (INPUT 読み取り前に死亡) | set -e / bash 設定確認 |
| `tool_name ok` なし | 層 3 (フィルタで脱落) | matcher 定義確認 |
| `file_path ok` なし | 層 3 (file_path 不正) | tool_input 構造確認 |
| `tasks.json filter ok` なし | 層 3 | ファイル名ルール確認 |
| `calling node` あり & `node returned` なし | 層 4/5 (node 実行失敗) | node 側で確認 |
| `node returned` あり & spec.md 未更新 | 層 5/6 (main 未呼出 or 置換失敗) | sync-spec-md.mjs 側で確認（一次原因の想定） |

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `/home/ryryo/dot-claude-dev/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | direct-run 判定を `import.meta.main` + fallback に修正、`realpathSync` / `pathToFileURL` import 追加 | symlink 経由で配信されている全プロジェクトの hook 動作が正常化 |
| `/home/ryryo/dot-claude-dev/.claude/hooks/dev/sync-spec-md-hook.sh` | Gate A で診断用 debug log を追加 → Gate C で除去。恒常エラー可視化（ERR_LOG）を追加して残す | hook 動作は変わらず、可観測性のみ向上 |
| `/home/ryryo/dot-claude-dev/.claude/skills/dev/spec-run/scripts/__tests__/sync-spec-md.test.mjs` | subprocess 経由で `main()` が symlink 経由でも呼ばれることを検証するテストを追加 | 既存テストは継続パス、新規テストで回帰防止 |
| `/home/ryryo/dot-claude-dev/package.json` | `engines.node >= 22.18.0` を明記 | 明示要件化のみ。現行環境 22.20 は条件を満たす |

### 新規作成ファイル

なし（一時的な `/tmp/sync-spec-md-hook-debug.log` は Gate C で除去、`/tmp/sync-spec-md-hook.log` はランタイム生成物で git 管理外）

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `docs/PLAN/260413_hook-verification/` | 完了扱いの履歴を保全。本 spec の背景で補足済み |
| 各プロジェクトの `.claude/settings.json` | hook 配線はテンプレート（commit e9c0504）通りで問題なし。Node スクリプト側の修正のみで解決 |
| `setup-project` スキル | テンプレート内の hook 配線は正しい |
| 既存の `generateTaskListSection` / `replaceGeneratedSection` 実装 | 仕様不変。テストは継続パス |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `/home/ryryo/dot-claude-dev/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | 修正対象本体 |
| `/home/ryryo/dot-claude-dev/.claude/hooks/dev/sync-spec-md-hook.sh` | hook スクリプト本体 |
| `/home/ryryo/dot-claude-dev/.claude/skills/dev/spec-run/scripts/__tests__/sync-spec-md.test.mjs` | 既存テスト。新規テスト追加先 |
| `/home/ryryo/dot-claude-dev/.claude/settings.json` | hook 配線確認（matcher が Edit/Write/MultiEdit か） |
| `/home/ryryo/dot-claude-dev/docs/PLAN/260412_spec-dashboard-format-v2/spec.md` | hook 導入の設計元。決定 #4 / #6 / #8 が根拠 |
| `/home/ryryo/dot-claude-dev/docs/PLAN/260413_hook-verification/spec.md` | 先行検証仕様（不十分だった先例） |
| `/home/ryryo/ablog/docs/PLAN/260414_tweet-post/spec.md` | Gate C 回帰テストの対象 |
| `/home/ryryo/ablog/docs/PLAN/260414_tweet-post/tasks.json` | Gate C 回帰テストの対象 |

### 参照資料（references/ にコピー済み）

なし（外部パス参照は発生しない。すべて dot-claude-dev / ablog 内で完結）

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 診断層
Gate B: 修正層（Gate A 完了後）
Gate C: 動作確認層（Gate B 完了後）
```

### Gate A: 診断層

> hook 発火の 6 層を実証的に切り分ける

- [ ] **A1**: sync-spec-md-hook.sh に診断用 debug log を一時的に仕込む
  > **Review A1**: _未記入_

- [ ] **A2**: tasks.json を実 Edit して hook 発火パスをログ検証
  > **Review A2**: _未記入_

- [ ] **A3**: sync-spec-md.mjs の isDirectRun バグを単体で再現（A2 で仮説 Z が有力な場合のみ）
  > **Review A3**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: 修正層

> direct-run 判定恒久化 + エラー可視化 + engines 明記

- [ ] **B1**: [TDD] sync-spec-md.mjs の direct-run 判定を import.meta.main + realpath フォールバックに修正（仮説 Z 確定時のみ）
  > **Review B1**: _未記入_

- [ ] **B2**: sync-spec-md-hook.sh に恒常的なエラー可視化機構を追加
  > **Review B2**: _未記入_

- [ ] **B3**: package.json の engines.node を 22.18+ に明記
  > **Review B3**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: 動作確認層

> テスト通過 + self-test + ablog 回帰 + 診断ログ除去

- [ ] **C1**: dot-claude-dev の vitest 全通過確認
  > **Review C1**: _未記入_

- [ ] **C2**: dot-claude-dev 内で tasks.json Edit → spec.md 自動更新の self-test
  > **Review C2**: _未記入_

- [ ] **C3**: ablog 側 tweet-post で tasks.json Edit → spec.md 自動更新の回帰確認
  > **Review C3**: _未記入_

- [ ] **C4**: A1 で追加した診断用 debug log を除去（恒常エラー可視化は残す）
  > **Review C4**: _未記入_

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| A2 で仮説 X/Y が判明した場合 Gate B の現行計画が無効になる | B1（direct-run 判定修正）の前提が失われる | A2 の STEP 1（dot-claude-dev 直参照）結果を見て分岐。仮説 X/Y の場合は A2 内で AskUserQuestion を実施し、以降の Gate を再計画する。その場合 **B1 は pending のまま保留**（別仕様書へ移す判断をユーザーに委ねる）、**B2/B3 は B1 と独立して実施可能**（dependencies は A2 のみ）。C2 は impl 内「ケース B」の分岐で SKIPPED 扱いになる |
| 診断用 debug log の削除忘れ | `/tmp` に持続的な書き込みが発生 | Gate C4 を独立 Todo として設置。C1-C3 通過後 100% 除去 |
| Node 22.18 未満環境での挙動 | `import.meta.main` が undefined → フォールバック分岐に入る | フォールバックは `realpathSync(argv[1])` で両側正規化済み。22.18 未満でも symlink 耐性あり。さらに package.json engines で 22.18+ を明示 |
| 他プロジェクトの既存 settings.json が古いテンプレートで作られている | そもそも hook が発火しない（Gate A1 の診断で検出） | Gate A2 のログで即判明。検出された場合は setup-project 側の問題として切り分け別仕様で対応 |
| 環境変数 `$CLAUDE_PROJECT_DIR` が symlink を含む | hook 内の `CLAUDE_PROJECT_DIR` 参照で不整合 | hook の `SYNC_SCRIPT` パス解決は symlink 経由でも動作確認済み。sync-spec-md.mjs 修正後は両側対応 |
| Windows (非 WSL) 互換性 | `file://` 文字列結合の残存 | 設計決定 #4 で `pathToFileURL` に統一済み。該当箇所は sync-spec-md.mjs のみ |
| ablog 側 tweet-post の途中状態を壊す | 回帰テストで tasks.json を一時編集する | C3 IMPL で編集後に元に戻す（ないし diff=0 で commit 不要）ことを明記 |
| テストが subprocess spawn を含むため CI で遅い | `npm test` 実行時間増加 | 追加テストは 1 件のみ、subprocess 起動 1 回で済む（影響軽微） |
