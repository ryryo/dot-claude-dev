# setup-project のディレクトリポータビリティ改善

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

`dot-claude-dev` を複数ホスト / 複数 OS（Mac・WSL・Remote Claude Code 等）の間で git 共有する際、各ホストごとに配置パスが異なりうる（`$HOME/dot-claude-dev` / `$HOME/dev/dot-claude-dev` / `$HOME/.dot-claude-dev` 等）。パス解決の齟齬で発生する `setup-project` 実行時エラーと、symlink 経由で hook が動作しない問題（旧 spec 継承）をまとめて解消する。

**原則**: OS（Mac / WSL / Linux / Remote）と配置（$HOME 直下 / サブディレクトリ / 隠しディレクトリ）は独立に扱う。どの OS でもどの配置でも動作することを目指す。

## 背景

### 実害

- **サブディレクトリ配置での破綻**: `CLAUDE_SHARED_DIR` が未設定で `$HOME/dot-claude-dev` 以外（例: `$HOME/dev/dot-claude-dev`）に clone した場合、他プロジェクトに `/setup-project` 実行すると `setup-claude.sh` のデフォルト `$HOME/dot-claude-dev` が存在せず `Shared directory not found` で停止する。現状は Mac で顕在化しているが、OS を問わず発生しうる問題。
- **symlink 経由の hook 動作不良（旧 spec 継承）**: `sync-spec-md.mjs` の `isDirectRun` 判定が `process.argv[1]`（symlink path）と `import.meta.url`（realpath resolved URL）の不一致によりサイレント終了。`ablog` のようにリンク先プロジェクトから呼ばれたときに `main()` が実行されない。

### 旧 spec の継承

旧 spec `260414_sync-spec-md-hook-fix` を本 spec に吸収する。旧 spec では A1（診断ログ仕込み）完了、A2 STEP 1（dot-claude-dev 直）で仮説 Z（symlink バグ）を確定。A2 STEP 2（ablog）は Mac 環境から `/home/ryryo/ablog/` アクセス不可のためスキップし、コード解析 + 外部調査で確定済み。

### 運用実績のある配置例（OS と配置は独立、組み合わせ自由）

| 例 | dot-claude-dev のパス | `CLAUDE_SHARED_DIR` 設定状況 |
|------|----------------------|--------------------------------|
| `$HOME` 直下（最も標準的） | `$HOME/dot-claude-dev` | 未設定でも動作（既定と一致） |
| `dev/` サブディレクトリ | `$HOME/dev/dot-claude-dev` | 未設定の場合ありえる（本 spec で改善） |
| Remote Claude Code | `$HOME/.dot-claude-dev`（隠しディレクトリ） | `setup-claude-remote.sh` が実行時注入済み（維持） |
| その他のカスタム配置 | 任意（例: `$HOME/repos/dot-claude-dev` など） | `CLAUDE_SHARED_DIR` を明示設定で対応 |

**重要**: 上記 3 パターンは OS を問わず発生しうる。現在の実運用では Mac が `$HOME/dev/dot-claude-dev`、WSL が `$HOME/dot-claude-dev` を使っているが、将来 Mac で `$HOME/dot-claude-dev` を使ったり WSL で `$HOME/dev/...` に配置する可能性もある。本 spec の探索順は OS を問わず同じ候補をチェックするため、OS と配置の組み合わせが増えても追加修正不要。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|---------|------|------|
| 1 | パス解決の単一起点 | `CLAUDE_SHARED_DIR` 環境変数を single source of truth | シンプル・全環境対応・既存コードとの親和性 |
| 2 | 未設定検出方針 | `setup-claude.sh` が `CLAUDE_SHARED_DIR` 未設定を検出 → 自動探索 → shell rc 自動追記 | Mac で未設定運用があるため自動化が必要 |
| 3 | 探索順序 | `$HOME/dot-claude-dev` → `$HOME/dev/dot-claude-dev` → `$HOME/.dot-claude-dev` | デプロイ実績順。OS 非依存（Mac / WSL / Linux / Remote 共通） |
| 4 | 複数候補 tie-break | 先頭優先 + env var による明示的オーバーライド | シンプル |
| 4b | カスタム配置の扱い | 探索 3 候補に該当しない配置（例: `$HOME/repos/...`）は `CLAUDE_SHARED_DIR` env var で明示指定する運用 | 3 候補以外を自動探索すると誤検出リスク大。明示指定は確実 |
| 5 | clone 時挙動 | 手動 `/setup-project` 継続。SessionStart での自動修復はしない | ユーザー選択（/dev:dig Round 2） |
| 6 | isDirectRun 修正方針 | `import.meta.main`（Node 22.18+）を第一判定、`pathToFileURL(realpathSync(argv[1]))` フォールバックを第二判定 | Node 22.18 で `import.meta.main` が追加済み、symlink 問題を構造的に解消 |
| 7 | Remote 環境の扱い | `setup-claude-remote.sh` が `CLAUDE_SHARED_DIR` を実行時注入する既存仕組みを維持 | `.zshrc` が使えない Remote 環境への配慮 |
| 8 | 回帰検証の方針 | ablog 回帰確認は WSL 側で人間が実施（Mac から不可） | Mac から `/home/ryryo/ablog/` にアクセス不可のため |

## アーキテクチャ詳細

### パス解決フロー（新 setup-claude.sh）

```
$ bash setup-claude.sh
  │
  ├── CLAUDE_SHARED_DIR 設定済み？
  │    ├── YES → SHARED_DIR=$CLAUDE_SHARED_DIR
  │    └── NO  → 探索モード
  │              ├── $HOME/dot-claude-dev 存在？      → YES: 採用
  │              ├── $HOME/dev/dot-claude-dev 存在？   → YES: 採用
  │              ├── $HOME/.dot-claude-dev 存在？      → YES: 採用
  │              └── いずれもなし                      → エラー終了
  │
  ├── 探索で見つけた場合 or env var と既定が異なる場合
  │    └── shell rc（.zshrc / .bashrc / .profile）に export を追記
  │         (既に CLAUDE_SHARED_DIR 行があれば何もしない)
  │
  ├── SHARED_DIR 存在確認
  │
  └── symlink 作成（ln -sfn）
```

### isDirectRun 判定（新 sync-spec-md.mjs）

```js
import { realpathSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

// Node 22.18+ の import.meta.main を第一判定
// フォールバック: argv[1] を realpath 解決 → file:// URL と比較
const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
);

if (isDirectRun) {
  main();
}
```

**重要**: 旧実装の `file://${process.argv[1]}` は symlink path を URL 化しただけで realpath 化されないため、`import.meta.url`（realpath 解決済み）と不一致になる。`realpathSync` で symlink を解決することで両者が一致する。

### sync-spec-md-hook.sh の ERR_LOG 追加（恒常機構）

現状: `node "$SYNC_SCRIPT" "$FILE_PATH" 2>&1 | tee -a "$DEBUG_LOG" >&2`（tee は Gate A1 の診断用、恒常機構なし）

新規: 失敗時のみ `/tmp/sync-spec-md-hook.log` に追記する恒常機構を追加。

```bash
# Gate E3 で A1 の診断ログを除去した後、以下が残る
ERR_LOG="/tmp/sync-spec-md-hook.log"
if ! node "$SYNC_SCRIPT" "$FILE_PATH" 2> /tmp/.sync-spec-md.err; then
  {
    echo "=== $(date -Iseconds) | PID $$ ==="
    echo "FILE_PATH=$FILE_PATH"
    cat /tmp/.sync-spec-md.err
  } >> "$ERR_LOG"
fi
rm -f /tmp/.sync-spec-md.err
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|----------|----------|------|
| `scripts/setup-claude.sh` | `CLAUDE_SHARED_DIR` 未設定検出 + 自動探索 + shell rc 自動追記 | Mac 環境で `/setup-project` が成功するようになる |
| `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | `isDirectRun` 判定を `import.meta.main` + `pathToFileURL(realpathSync(...))` に変更 | symlink 経由の hook 実行で `main()` が呼ばれるようになる |
| `.claude/skills/dev/spec-run/scripts/__tests__/sync-spec-md.test.mjs` | symlink 経由 subprocess テストを追加 | isDirectRun 修正の回帰防止 |
| `.claude/hooks/dev/sync-spec-md-hook.sh` | 失敗時に `/tmp/sync-spec-md-hook.log` へ記録する ERR_LOG 機構を追加。Gate A1 の診断ログを除去 | hook 失敗時の可観測性向上 |
| `package.json` | `"engines": { "node": ">=22.18.0" }` を追加 | `import.meta.main` が必須である旨を明示 |
| `docs/setup-guide.md` | `CLAUDE_SHARED_DIR` を前提とした記述へ一斉更新 | 3 環境運用を正式にドキュメント化 |
| `.claude/launch.json` | `runtimeExecutable` のハードコードパス（`/Users/ryryo/.anyenv/...`）を削除し `npm` に変更 | Mac 以外でも使えるようになる |
| `.claude/skills/setup-project/scripts/check-claude-setup.sh` | 「リンク先が別パスの dot-claude-dev」の場合に `CLAUDE_SHARED_DIR` 設定を案内する指針を追加 | 診断出力の有益性向上 |

### 新規作成ファイル

なし。既存ファイルの修正のみ。

### 変更しないファイル

| ファイル | 理由 |
|----------|------|
| `.claude/skills/setup-project/scripts/setup-claude-remote.sh` | Remote 環境で既に `CLAUDE_SHARED_DIR` を実行時注入しており修正不要 |
| `.claude/settings.json` (hook 配線) | 本 spec で変更する必要なし |
| `.claude/skills/setup-project/SKILL.md` | setup-claude.sh 改善が反映されれば SKILL.md は現状のままで OK |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
|----------|------|
| `scripts/setup-claude.sh` | 既存ロジック（特に line 6 の SHARED_DIR 既定値、line 15-34 の永続化ロジック）の現状把握 |
| `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | isDirectRun 周辺（line 148-155）の現状把握 |
| `.claude/skills/dev/spec-run/scripts/__tests__/sync-spec-md.test.mjs` | 既存テスト構造の把握（symlink テスト追加の参考） |
| `.claude/hooks/dev/sync-spec-md-hook.sh` | 診断ログ（line 10-17, 20, 33, 54, 77-80）位置と ERR_LOG 追加位置 |
| `.claude/skills/setup-project/scripts/setup-claude-remote.sh` | Remote 環境が `CLAUDE_SHARED_DIR` をどう注入しているかを理解（変更しないが前提） |
| `docs/setup-guide.md` | 現行記述の確認（特に line 75-90 の CLAUDE_SHARED_DIR 説明） |
| `/tmp/sync-spec-md-hook-debug.log` | Gate A1 診断ログの現状出力確認（hook 動作ログ） |

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 核心バグ修正 [TDD]
Gate B: セットアップ自動化（Gate A 完了後）
Gate C: 可視化と要件明示（Gate A 完了後）
Gate D: オプション改善（Gate B, C 完了後）
Gate E: 検証と最終化（Gate D 完了後）
```

### Gate A: 核心バグ修正 [TDD]

> symlink 経由で hook の main() が呼ばれない問題を最優先で倒す

- [ ] **A1**: [TDD] sync-spec-md.mjs の isDirectRun バグ修正（symlink 対応）
  > **Review A1**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: セットアップ自動化

> Mac サブディレクトリ配置でも setup-claude.sh が自動で動くようにする

- [ ] **B1**: setup-claude.sh に CLAUDE_SHARED_DIR 未設定検出 + 探索 + shell rc 自動追記を実装
  > **Review B1**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: 可視化と要件明示

> hook 失敗の恒常観測と Node バージョン要件の明示

- [ ] **C1**: [SIMPLE] sync-spec-md-hook.sh に失敗時 ERR_LOG 記録を追加
  > **Review C1**: _未記入_
- [ ] **C2**: [SIMPLE] package.json に engines.node >= 22.18.0 を明記
  > **Review C2**: _未記入_

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: オプション改善

> ドキュメントと開発環境設定を CLAUDE_SHARED_DIR 前提に統一

- [ ] **D1**: [SIMPLE] docs/setup-guide.md を CLAUDE_SHARED_DIR 前提の記述に一斉更新
  > **Review D1**: _未記入_
- [ ] **D2**: [SIMPLE] .claude/launch.json の npm shim ハードコードを削除
  > **Review D2**: _未記入_
- [ ] **D3**: check-claude-setup.sh に別パス dot-claude-dev 発見時の指針表示を追加
  > **Review D3**: _未記入_

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate E: 検証と最終化

> 全テスト通過確認と診断ログ除去

- [ ] **E1**: npm test 全通過確認 + dot-claude-dev 内 self-test 実施
  > **Review E1**: _未記入_
- [ ] **E2**: Gate A1（旧 spec）由来の診断ログを sync-spec-md-hook.sh から除去（ERR_LOG は残す）
  > **Review E2**: _未記入_

**Gate E 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認（WSL 環境で ablog 回帰 + Remote 環境で `CLAUDE_CODE_REMOTE=true` 実行時の `setup-claude-remote.sh` → 新 `setup-claude.sh` チェーンを目視確認）

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| `import.meta.main` が Node < 22.18 で undefined になり全環境で false 判定のみになる | hook が動かない環境が残る | package.json の `engines.node >= 22.18.0` で明示。フォールバックで `pathToFileURL(realpathSync)` を追加したため `import.meta.main` が false でも動作 |
| `setup-claude.sh` が複数候補を検出した時のユーザー混乱 | 意図しないディレクトリを採用 | 探索順序を固定（先頭優先）+ stderr に採用先を明示表示 + env var 明示で上書き可能 |
| `.zshrc` 自動追記でユーザーの dotfiles を破壊 | セットアップが毎回 rc に追記する | `grep -q "CLAUDE_SHARED_DIR"` で既存行を検出して重複追記を防止（現行ロジック維持） |
| Remote 環境で本修正と既存の `setup-claude-remote.sh` が競合 | Remote セッション起動失敗 | Remote は既に `CLAUDE_SHARED_DIR` を実行時注入するため本修正の「未設定検出」パスに入らず影響なし |
| ablog 側の symlink チェーンが本修正で逆に壊れる可能性 | ablog で hook が動作しない | WSL 環境で人間が実行時検証（本 spec のレビューステータスで明記） |
| `.claude/launch.json` の npm shim 削除で Mac の nodenv ユーザーが dashboard デバッグできなくなる | launch デバッグのみ影響、本番動作は無関係 | `npm` のまま PATH 解決に委ねる。nodenv が PATH に含まれていない場合は各自の IDE 設定で追記 |
