# dev:spec-run に worktree モードを追加する

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

なお、本仕様書の実装対象そのものが `/dev:spec-run` スキルであるため、本仕様書を実行する際は**現行の spec-run**（worktree モード未実装版）で実行する。worktree 使用の選択肢は本仕様書の実装完了後に初めて出現する。

---

## 概要

`dev:spec-run` スキルにオプションで「worktree モード」を追加する。ユーザーは Step 4 の実行モード選択時に worktree 使用可否を選べるようになり、worktree を使う場合は `.worktrees/{slug}/` に作業用 worktree と `feature/{slug}` ブランチを作成、その中で全 Gate を実行し、人間レビュー完了後に master へ `--no-ff` マージ → worktree / feature ブランチを自動 cleanup する。デフォルトは「worktree を使わない」（現行動作維持）。

## 背景

### 現状の課題

`dev:spec-run` は常に現 cwd（通常 master）で直接作業するため:

- 実装中に他の作業で master を触れない（実装と別件作業の並行ができない）
- 途中で中断したとき、どこまで進んだかを master のワーキングツリー上の変更として見ざるを得ない
- 複数の spec を並行実行できない

### なぜ worktree か

git worktree はリポジトリの別ブランチを別ディレクトリに同時チェックアウトできる機能で、以下を実現する:

- 実装を feature ブランチに分離 → master は常にクリーン
- 1 リポジトリで複数の spec を並行実行可能
- `.worktrees/` は既に `.gitignore` 済み（行 37）なので追加設定不要

### なぜ team-run のスクリプトを流用するか

`.claude/.backup/skills/dev/team-run/scripts/` に既に実績のある setup/cleanup スクリプトがあり、**冪等性**（reuse 時に branch/worktree 再利用）が実装済みで本要件の「中断 → 次回 reuse」にそのまま使える。team-run はPR経由のフローだったが、spec-run 用途に合わせて cleanup の責任範囲を調整し（PR → ローカル `--no-ff` マージ）、5 点の改修を加える。

### なぜデフォルトは「使わない」か

現行ユーザーの使用感を壊さない。worktree は高度な機能であり、ユーザーが明示的に選んだときのみ有効化する。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1 | マージ戦略 | ローカル `git merge --no-ff` でデフォルトブランチ（master/main 自動検出）にマージ | PR/CI不要、spec-run 単体で完結。`--no-ff` でマージコミットを残し worktree 使用の履歴が追える |
| 2 | クリーニング範囲 | worktree ディレクトリ + feature ブランチ（ローカルのみ）削除 | リモートブランチは作成していないので触らない。push はしない |
| 3 | 中断時の扱い | worktree と feature ブランチをそのまま残し、次回 reuse | setup-worktree.sh の冪等性を活用。作業ログが消えない |
| 4 | reuse 時 spec 同期 | worktree 内で `git merge {base}` を実行して最新 spec を取り込む | git 標準フローで進捗チェックボックスも自動保持。特殊処理不要 |
| 5 | マージコンフリクト | Claude が精査 → 単純な機械的コンフリクト（import順・フォーマット）は自動解決 → 仕様影響のありそうなコンフリクトは AskUserQuestion でエスカレーション | 深掘り決定事項。仕様外改変リスクを避ける |
| 6 | slug 決定 | 仕様書ファイル名（拡張子除く）をそのまま使う | 例: `260411_dashboard-table-view.md` → `feature/260411_dashboard-table-view`。追加の問いかけ不要 |
| 7 | 問いかけ位置 | Step 4 実行モード選択と**同一** AskUserQuestion で聞く（1 tool call で 2 質問） | ユーザーへの問いかけ回数を増やさない |
| 8 | デフォルト推奨 | 「worktree を使わない」がデフォルト推奨 | 現行動作との後方互換。worktree 使用側に `(Recommended)` を付けない |
| 9 | master dirty 時 | 警告 → AskUserQuestion で「コミット / stash / 中断」を選択 | 未保存作業を守る |
| 10 | Codex モード連携 | cwd=worktree のまま Codex を実行、`.tmp/` も worktree 内 | `.gitignore` で `.tmp/` は全 worktree で除外される。完了時削除は worktree 側で行う |
| 11 | Preflight 実行場所 | worktree 内で実行（cwd=worktree のまま） | `node_modules` / `.env` が worktree 側に揃う |
| 12 | 人間レビュー統合 | 人間レビュー**OK** → worktree/ブランチ cleanup → cwd を master に戻す。**NG** → worktree を残したまま修正ループ | 本 SKILL.md に既存の「人間レビュー確認フロー」と整合 |
| 13 | base ブランチ検出 | `git symbolic-ref refs/remotes/origin/HEAD` で自動検出、失敗時は `master` → `main` の順で試す | cleanup-branches スキルと同じ慣例 |
| 14 | スクリプト配置 | `.claude/skills/dev/spec-run/scripts/setup-worktree.sh` / `cleanup-worktree.sh` | 既存 `diagnose-codex.sh` / `resolve-codex-plugin.sh` と同じ場所 |
| 15 | worktree 配置 | `.worktrees/{slug}/` | team-run 慣例を踏襲、`.gitignore` に登録済み |

## アーキテクチャ詳細

### 起動フロー全体図（worktree モード選択時）

```
Step 1 仕様書特定              [cwd: master]
Step 2 入力形式判定             [cwd: master]
Step 3 実行準備（参照ファイルRead）[cwd: master]
Step 4 実行モード + worktree 選択 [cwd: master]
       │
       │ ユーザーが「worktree 使う」を選択
       ▼
Step 4.5 master dirty チェック   [cwd: master]
       │ dirty なら: コミット/stash/中断 を選択
       ▼
Step 4.6 setup-worktree.sh 実行  [cwd: master → worktree]
       │ 新規: feature/{slug} + .worktrees/{slug}/ 作成
       │ reuse: 既存 worktree に git merge {base} で最新 spec 取り込み
       │       （コンフリクトは Claude 精査 → 自動解決 or エスカレーション）
       ▼
Step 5 プロトコル読込 + Preflight + Gate 実行 [cwd: worktree]
       │ 全 Gate 通過まで IMPL / VERIFY / FIX / UPDATE をループ
       ▼
全 Gate 通過後の完了処理
       │
       │ 人間レビューセクションあり
       ▼
人間レビュー確認 (AskUserQuestion)
       │
       ├─ OK    ─┐
       │         ▼
       │    Step C1: worktree 内で最終状態確認（未コミット 0, 全 commit 済み）
       │    Step C2: cwd を master リポジトリルートに戻す
       │    Step C3: git checkout {base} （必要なら git pull）
       │    Step C4: git merge --no-ff feature/{slug}
       │             （コンフリクトは Claude 精査 → 自動解決 or エスカレーション）
       │    Step C5: cleanup-worktree.sh 実行
       │             （worktree 削除 + feature ブランチ削除）
       │    Step C6: .tmp/codex-*.md 削除（Codex モードのみ、完了処理に移行）
       │    Step C7: 完了報告
       │
       └─ NG    ─┐
                 ▼
            worktree を残したまま修正ループ
            （cwd は worktree のまま、Gate 再実行 or 部分修正）
```

### worktree 未選択時のフロー

**現行の動作を一切変更しない。** `Step 4.5` / `4.6` / `C1-C6` は全てスキップし、完了処理の `.tmp/codex-*.md` 削除は master の cwd で実行する。

### setup-worktree.sh の契約

| 項目 | 値 |
|---|---|
| パス | `.claude/skills/dev/spec-run/scripts/setup-worktree.sh` |
| 呼び出し | `bash .claude/skills/dev/spec-run/scripts/setup-worktree.sh <slug>` |
| stdout | worktree の絶対パス（成功時のみ 1 行） |
| stderr | ログメッセージ（全イベント） |
| 終了コード | 0: 成功 / 1: slug 検証失敗 / 2: base ブランチ検出失敗 / 3: git 操作失敗 |
| 副作用 | `feature/{slug}` ブランチ作成（既存なら再利用）+ `.worktrees/{slug}/` 作成（既存なら再利用） |

### setup-worktree.sh の改修ポイント（team-run 版からの差分）

team-run 版（`references/team-run-setup-worktree.sh`）に対して以下 5 点を追加する:

1. **起点ブランチ明示** — `git branch feature/{slug} {base}` の形で明示。team-run 版は `git branch feature/{slug}` だけで暗黙に現 HEAD を使っていた
2. **SLUG サニタイズ** — 正規表現 `^[a-zA-Z0-9][a-zA-Z0-9_.-]*$` でチェック、失敗時 exit 1
3. **base 自動検出** — `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'` → 失敗時は `master` / `main` の順で試す
4. **リモート同期確認** — `git fetch origin --quiet` を冒頭で実行（失敗は warning のみ、exit しない）
5. **既存ブランチ reuse 時の警告** — ブランチが既に存在する場合、`git merge-base --is-ancestor origin/{base} feature/{slug}` で base の最新を含んでいるか確認し、遅れていたら stderr に警告を出す（自動マージは**しない**。マージは SKILL.md プロトコル側で `git merge {base}` として実行する）

### cleanup-worktree.sh の契約

| 項目 | 値 |
|---|---|
| パス | `.claude/skills/dev/spec-run/scripts/cleanup-worktree.sh` |
| 呼び出し | `bash .claude/skills/dev/spec-run/scripts/cleanup-worktree.sh <slug>` |
| stdout | 削除したリソースのサマリー |
| stderr | エラー詳細 |
| 終了コード | 0: 成功 / 1: slug 検証失敗 / 2: worktree 削除失敗 / 3: ブランチ削除失敗 |
| 副作用 | `.worktrees/{slug}/` 削除 + `feature/{slug}` ブランチ削除 + `git worktree prune` |

### cleanup-worktree.sh の改修ポイント（team-run 版からの差分）

team-run 版（`references/team-run-cleanup-worktree.sh`）はworktreeだけ消してfeatureブランチを残していた。spec-run 用に以下 3 点を改修:

1. **feature ブランチ削除を追加** — worktree 削除後に `git branch -d feature/{slug}`（未マージなら exit 3 で報告。強制削除 `-D` は**しない**）
2. **`|| true` のエラー握りつぶしを撤廃** — `git worktree remove --force` が失敗したら exit 2 で報告
3. **未コミット変更検知** — worktree を削除する前に `git -C .worktrees/{slug} status --porcelain` を確認、変更があれば exit 2 で報告（`--force` で破棄しない）

### worktree-protocol.md（新規）の構成

```markdown
# worktree ライフサイクル（spec-run 用）

## フェーズ
1. 起動時チェック（dirty 検知）
2. setup (新規 or reuse)
3. reuse 時の spec 同期（git merge {base}）
4. Gate 実行（cwd=worktree）
5. 完了時 merge (git merge --no-ff)
6. cleanup (worktree 削除 + feature ブランチ削除)
7. エラーリカバリ（コンフリクト対応 / dirty 残留対応）

## コンフリクト自動解決のガイドライン
（どのパターンが Claude の自動判断 OK で、どのパターンが AskUserQuestion に上げるか）

## cwd 管理
（Bash tool の cwd 永続性を前提に、どのステップで cd するか）
```

### SKILL.md 更新箇所

#### Step 4（実行モード選択）

現行:

```markdown
### ステップ 4: 実行モード選択

AskUserQuestion で実行モードを選択する:

- **Claudeモード** — Claude Code が全 Todo を直接実行
- **Codex モード** — デフォルトで全タスクを Codex プラグイン（`task --write`）に委任
```

更新後:

```markdown
### ステップ 4: 実行モード + worktree 選択

AskUserQuestion で**2 つの質問を同時に**聞く:

**質問 1: 実行モード**
- **Claudeモード** — Claude Code が全 Todo を直接実行
- **Codex モード** — デフォルトで全タスクを Codex プラグインに委任

**質問 2: worktree 使用**
- **使わない（Recommended）** — 現 cwd（master）で直接作業する（現行動作）
- **使う** — feature/{slug} の worktree 内で作業し、完了後にローカル --no-ff マージ + cleanup を自動実行

「使う」を選択した場合は `references/worktree-protocol.md` を Read してそのライフサイクルに従う。
```

#### Step 4.5（新規: dirty チェック）

```markdown
### ステップ 4.5: master dirty チェック（worktree 選択時のみ）

`git status --porcelain` で master の未コミット変更を確認。変更がある場合 AskUserQuestion で以下を選ばせる:

- コミット → `/dev:simple-add` で先にコミット
- stash → `git stash push -m "spec-run worktree setup: {slug}"`
- 中断 → spec-run を停止してユーザーに対応を任せる
```

#### Step 4.6（新規: worktree setup）

```markdown
### ステップ 4.6: worktree setup（worktree 選択時のみ）

1. `bash .claude/skills/dev/spec-run/scripts/setup-worktree.sh {slug}` を実行
2. stdout の絶対パスを `$WORKTREE_PATH` として記憶
3. 以降の Bash コマンドは `cd $WORKTREE_PATH` で cwd を切り替える（Bash tool の cwd は永続するため最初の1回で十分）
4. 既存 worktree を reuse した場合: `git merge {base}` を worktree 内で実行（base は setup-worktree.sh と同じ自動検出ロジック）
5. reuse 時のマージコンフリクトが発生した場合:
   - Claude が diff 内容を精査
   - 仕様影響なしの機械的コンフリクト（import順・フォーマットのみ）→ 自動解決
   - 仕様影響ありの可能性 → AskUserQuestion で「手動解決 / 中断 / 特定ファイルの片側採用」を提示
```

#### 完了処理（既存を更新）

```markdown
## 全 Gate 通過後の完了処理

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

未コミットの変更がある場合はコミットする。

### 人間レビュー確認フロー
（既存のロジック）

### worktree 終了処理（worktree 選択時のみ）

人間レビューが **OK** の場合のみ以下を実行:

1. `cd $WORKTREE_PATH && git status --porcelain` が空を確認
2. master リポジトリルートに cwd を戻す: `cd "$MASTER_ROOT"`（`$MASTER_ROOT` は Step 4.6 の `setup-worktree.sh` 呼び出し前に `MASTER_ROOT="$(pwd)"` で事前保存したパス。`git rev-parse --show-toplevel` は worktree 内から実行すると worktree 側のルートを返すため使用しない）
3. `git checkout {base}`（base は setup と同じ自動検出）
4. `git merge --no-ff feature/{slug} -m "Merge feature/{slug} via spec-run"`
5. コンフリクトが発生した場合は Step 4.6 の reuse 時と同じ方針で対応
6. `bash .claude/skills/dev/spec-run/scripts/cleanup-worktree.sh {slug}` を実行
7. Codex モードの場合、**master 側の** `.tmp/codex-*.md` を削除（worktree 側は cleanup で消えている）

人間レビューが **NG** の場合:
- worktree を残したまま修正ループに入る（cwd は worktree のまま）
```

### cwd 管理方針

- Bash tool の cwd は永続する前提
- `cd $WORKTREE_PATH` は Step 4.6 で 1 回だけ実行
- 以降の全 Bash コマンドは worktree 内で実行される
- Read / Edit / Write は絶対パスを使うので cwd に影響されない（仕様書読込時は master 側のパスでも worktree 側のパスでもよいが、worktree 内のファイルが最新なので **worktree 内のパス** を使う）
- 完了処理で master ルートに戻る（`cd "$MASTER_ROOT"` — `MASTER_ROOT="$(pwd)"` を Step 4.6 の worktree setup 前に保存しておく）

### コンフリクト自動解決ガイドライン

Claude が自動解決してよい条件（worktree-protocol.md に詳記）:

| パターン | 自動解決可 | 理由 |
|---|---|---|
| import 文の順序のみの差異 | ✅ | 機能影響なし |
| コメント・空白のみの差異 | ✅ | 機能影響なし |
| 片側が完全な superset（新機能追加のみ） | ✅ | 既存動作を壊さない |
| 同じ関数のロジック変更が両側にある | ❌ | AskUserQuestion |
| spec.md 内のチェックボックス変更 | ✅ | どちらも `[x]` なら `[x]` を採用、片側 `[x]` なら `[x]` を優先 |
| spec.md 内の Review blockquote 変更 | ❌ | 両方の記述を保持して手動確認 |
| 設定ファイル（package.json 等）の両側変更 | ❌ | AskUserQuestion |

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `.claude/skills/dev/spec-run/SKILL.md` | Step 4 に worktree 選択肢追加、Step 4.5 / 4.6 追加、完了処理に worktree 終了処理を追加 | worktree モードが有効になる。デフォルト挙動は現行と同一 |
| `.claude/skills/dev/spec-run/references/execution.md` | Claudeモードでの worktree 動作説明を追加（cwd は worktree 前提で各 Step を記述、差分のみ） | Claude モードで worktree 使用時の挙動が明確化 |
| `.claude/skills/dev/spec-run/references/codex-execution.md` | Codex モードでの worktree 動作説明を追加（Codex cwd / .tmp/ 配置） | Codex モードで worktree 使用時の挙動が明確化 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `.claude/skills/dev/spec-run/scripts/setup-worktree.sh` | team-run 版を流用 + 5 点改修（起点明示 / サニタイズ / base検出 / fetch / reuse警告） |
| `.claude/skills/dev/spec-run/scripts/cleanup-worktree.sh` | team-run 版を流用 + 3 点改修（feature削除追加 / エラー握りつぶし撤廃 / 未コミット検知） |
| `.claude/skills/dev/spec-run/references/worktree-protocol.md` | worktree ライフサイクル詳細（7 フェーズ + コンフリクトガイドライン + cwd 管理） |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `.gitignore` | `.worktrees/` と `.tmp/` は既に登録済み（行 37, 24） |
| `.claude/skills/dev/spec-run/roles/*.md` | ロール定義は cwd に非依存。worktree 内でも現行ロール定義で実装可能 |
| `.claude/skills/dev/spec-run/agents/*.md` | レビュワー定義も cwd 非依存 |
| `.claude/skills/dev/spec-run/references/codex-review-instructions.md` | focus テンプレートは `[PROMPT]` 方式で差分検出、worktree 内でも `origin/master..HEAD` が自然に動作 |
| `.claude/.backup/skills/dev/team-run/scripts/*.sh` | 流用元。本仕様では新規ファイルを spec-run/scripts/ に作成し、team-run バックアップは改変しない |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `.claude/skills/dev/spec-run/SKILL.md` | 更新対象本体。現行 Step 構造を把握 |
| `.claude/skills/dev/spec-run/references/execution.md` | Claude モード実行プロトコル（更新対象） |
| `.claude/skills/dev/spec-run/references/codex-execution.md` | Codex モード実行プロトコル（更新対象） |
| `.claude/skills/dev/spec-run/scripts/diagnose-codex.sh` | 既存スクリプトのコーディング慣例（set -euo pipefail / エラーハンドリング） |
| `.claude/skills/dev/spec-run/scripts/resolve-codex-plugin.sh` | 同上 |
| `.claude/skills/dev/cleanup-branches/SKILL.md` | worktree 削除手順の既存慣例（`git worktree remove --force`） |
| `.gitignore` | `.worktrees/` / `.tmp/` が既に登録済みであることを確認 |

### 参照資料（references/ にコピー済み）

| ファイル | 目的 |
| -------- | ---- |
| `references/team-run-setup-worktree.sh` | 流用元 setup スクリプト。改修後は spec-run/scripts/ に置く |
| `references/team-run-cleanup-worktree.sh` | 流用元 cleanup スクリプト。改修後は spec-run/scripts/ に置く |
| `references/team-run-step-2-worktree.md` | team-run での worktree セットアップ呼び出し手順（参考） |
| `references/team-run-step-6-pr-cleanup.md` | team-run での PR / cleanup フロー（spec-run ではローカルマージに置き換える参考情報） |

## タスクリスト

> **実装詳細は `tasks.json` を参照。** このセクションは進捗管理と Review 記録用。

### 依存関係図

```
Gate A: スクリプト層（独立、並列可）
├── Todo A1: setup-worktree.sh 作成
└── Todo A2: cleanup-worktree.sh 作成

Gate B: プロトコル文書層（Gate A 完了後）
├── Todo B1: worktree-protocol.md 新規作成（B2/B3 の前提）
├── Todo B2: execution.md 更新（Claudeモード worktree 対応、B1 完了後）
└── Todo B3: codex-execution.md 更新（Codexモード worktree 対応、B1 完了後）

Gate C: SKILL.md 本体更新（Gate B 完了後）
├── Todo C1: Step 4 に worktree 選択肢追加
├── Todo C2: Step 4.5 / 4.6 追加（dirty check + worktree setup）
└── Todo C3: 完了処理に worktree 終了処理追加

Gate D: 検証（Gate C 完了後）
├── Todo D1: シェルスクリプト構文検証 + 冪等性動作確認
└── Todo D2: ドキュメント参照整合性確認
```

### Gate A: スクリプト層

- [x] **Todo A1**: setup-worktree.sh を spec-run/scripts/ に作成（team-run 版を流用 + 5 点改修）
  > **Review A1**: ✅ PASSED (シンプルモード / correctness reviewer 1体)
  >
  > 5 点改修（起点明示 / SLUG サニタイズ / base 自動検出 / fetch / reuse 警告）すべて確認。契約（stdout=絶対パス / stderr=ログ / exit 0-3）遵守。bash -n 構文検証 PASS、実行権限付与済み。

- [x] **Todo A2**: cleanup-worktree.sh を spec-run/scripts/ に作成（team-run 版を流用 + 3 点改修）
  > **Review A2**: ✅ PASSED (シンプルモード / correctness reviewer 1体)
  >
  > 3 点改修（feature ブランチ削除追加 / `|| true` 撤廃 / 未コミット検知）すべて確認。`-d` フラグで未マージ保護、SLUG サニタイズ、exit コード契約（0/1/2/3）遵守。bash -n PASS。

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: プロトコル文書層

- [x] **Todo B1**: references/worktree-protocol.md を新規作成
  > **Review B1**: ⏭️ SKIPPED (docs only)

- [x] **Todo B2**: references/execution.md に worktree 対応セクション追加
  > **Review B2**: ⏭️ SKIPPED (docs only)

- [x] **Todo B3**: references/codex-execution.md に worktree 対応セクション追加
  > **Review B3**: ⏭️ SKIPPED (docs only)

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: SKILL.md 本体更新

- [x] **Todo C1**: SKILL.md の Step 4 を「実行モード + worktree 選択」に書き換える
  > **Review C1**: ⏭️ SKIPPED (docs only)

- [x] **Todo C2**: SKILL.md に Step 4.5（dirty check）と Step 4.6（worktree setup）を追加
  > **Review C2**: ⏭️ SKIPPED (docs only)

- [x] **Todo C3**: SKILL.md の完了処理に worktree 終了処理（merge + cleanup）を追加
  > **Review C3**: ⏭️ SKIPPED (docs only)

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: 検証

- [x] **Todo D1**: 両シェルスクリプトの構文検証（`bash -n`）+ SLUG バリデーション・冪等性・Codex plugin 互換性の動作確認（master 履歴を汚染しないよう一時ブランチ `test/validate-worktree-cleanup` を使用）
  > **Review D1**: ✅ PASSED
  >
  > - 構文検証: `bash -n` 両方とも 0 exit
  > - SLUG バリデーション: 'bad slug' / '/etc' / 空文字 すべて exit 1
  > - 新規作成: `.worktrees/test-worktree-validation/` + `feature/test-worktree-validation` 作成確認
  > - 冪等性: 再実行で "already exists, reusing" メッセージ確認、exit 0
  > - Codex plugin 互換性: worktree cwd から `resolve-codex-plugin.sh` 実行で `/Users/ryryo/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs` 取得成功 → **Codex モード × worktree モード併用可能**
  > - cleanup 未マージケース: `git branch -d` 失敗で exit 3、worktree は先に削除される挙動を確認
  > - cleanup 正常ケース: 一時ブランチ `test/validate-worktree-cleanup` で `--no-ff` マージ後に cleanup 実行、exit 0、worktree + feature ブランチ削除確認
  > - 後始末: master HEAD は `0501eaf` のまま不変、一時ブランチも `-D` で削除済み

- [x] **Todo D2**: SKILL.md ↔ worktree-protocol.md ↔ execution.md / codex-execution.md の相互参照が壊れていないか確認
  > **Review D2**: ✅ PASSED
  >
  > - 全 3 ファイル（setup-worktree.sh / cleanup-worktree.sh / worktree-protocol.md）存在確認
  > - SKILL.md → worktree-protocol.md: 6 箇所参照（Step 4 / Step 4.5 / Step 4.6×2 / 完了処理×2）
  > - execution.md → worktree-protocol.md: 1 箇所（line 167）
  > - codex-execution.md → worktree-protocol.md: 1 箇所（line 343）
  > - worktree-protocol.md → scripts: setup/cleanup 両方正しいパス
  > - 用語統一: `$WORKTREE_PATH` / `$MASTER_ROOT` / `feature/{slug}` / `.worktrees/{slug}` 全ファイル一致
  > - Step 番号連続性: 1→2→3→4→4.5→4.6→5 確認
  > - Codex × worktree 併用: D1 で検証成功、codex-execution.md の「動作する前提」記述と整合

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認（実装後、実際に spec-run を worktree モードで起動して一連の流れが動くかを手動確認）

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| マージコンフリクトの自動解決で Claude が仕様に影響する改変をしてしまう | 高 | worktree-protocol.md の「コンフリクト自動解決ガイドライン」で許可パターンを厳格に限定。迷ったら AskUserQuestion で必ずエスカレーション |
| cwd が worktree に入ったまま完了処理で戻し忘れる | 中 | 完了処理の最初に `git rev-parse --show-toplevel` で明示的に master ルートへ cd。cleanup-worktree.sh 実行前に cwd を master に戻すことを SKILL.md に明記 |
| reuse 時の `git merge {base}` で worktree 内の進捗 spec.md が破壊される | 中 | 設計決定 #4 の通り git merge の標準動作で保持される（両側編集行以外は維持）。ただし同じ行を両側編集した場合はエスカレーション |
| base ブランチ検出失敗 | 低 | setup-worktree.sh で `symbolic-ref` → `master` → `main` の順にフォールバック。全て失敗なら exit 2 で明示エラー |
| `.tmp/` が worktree ごとに独立することでディスク使用量増 | 低 | 完了処理 + cleanup で自動削除。残留しても `.gitignore` 対象 |
| team-run の backup スクリプトを作業エージェントがうっかり直接編集してしまう | 低 | 仕様書の「変更しないファイル」セクションで明記。references/ にコピー済みなので backup を触る必要なし |
| Codex プラグイン側のパス解決（`resolve-codex-plugin.sh`）が worktree cwd で動作しない可能性 | 中 | Todo D1 の動作確認で worktree cwd でも `resolve-codex-plugin.sh` が成功することを検証する手順を含める |
