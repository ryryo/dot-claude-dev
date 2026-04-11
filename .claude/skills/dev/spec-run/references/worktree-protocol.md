# worktree ライフサイクル（spec-run 用）

SKILL.md の Step 4 で worktree 使用を選択した場合のみ適用される拡張プロトコル。未選択時は本ファイルを Read する必要はない。

## 前提

- `.worktrees/` と `.tmp/` は `.gitignore` 登録済み（dot-claude-dev 側で確認済み）
- setup-worktree.sh / cleanup-worktree.sh は `.claude/skills/dev/spec-run/scripts/` に配置済み
- Bash tool の cwd は永続する前提で設計

## フェーズ一覧

| # | フェーズ | 実行タイミング | cwd |
|---|---------|---------------|-----|
| 1 | dirty チェック | Step 4 直後 | master |
| 2 | setup | Step 4.5 の後 | master → worktree |
| 3 | reuse 時 spec 同期 | setup 直後、既存 worktree 検出時 | worktree |
| 4 | Gate 実行 | Step 5 | worktree |
| 5 | 完了時 merge | 人間レビュー OK 後 | worktree → master |
| 6 | cleanup | merge 直後 | master |
| 7 | エラーリカバリ | 各フェーズで失敗時 | - |

---

## フェーズ 1: dirty チェック

### 目的
master の未コミット変更が worktree 作成後のマージ時にコンフリクトを生まないようにする。

### 手順

1. `git status --porcelain` を実行
2. 出力が空なら → フェーズ 2 へ
3. 出力に行があれば AskUserQuestion で以下を選択:
   - **コミット**: `/dev:simple-add` スキルを呼び出してコミット（ユーザーに内容確認を任せる）
   - **stash**: `git stash push -m "spec-run worktree setup: {slug}"` を実行（完了時の pop はユーザー責任。spec-run は pop しない）
   - **中断**: spec-run を停止、ユーザーに対応を任せる

---

## フェーズ 2: setup

### 目的
`.worktrees/{slug}/` と `feature/{slug}` ブランチを作成する（既存なら reuse）。

### 手順

1. slug を決定: 仕様書ファイル名から拡張子を除いたもの（例: `260411_dashboard-table-view.md` → `260411_dashboard-table-view`）
2. `bash .claude/skills/dev/spec-run/scripts/setup-worktree.sh {slug}` を実行
3. stdout の 1 行を `$WORKTREE_PATH` として記憶
4. stderr を確認し、"already exists, reusing" を検出したら **reuse フラグ** を立てる
5. **Bash tool の cwd を worktree に切り替え**: `cd "$WORKTREE_PATH"` を実行（以降の全 Bash コマンドは worktree 内で動作）

### 失敗時

| 終了コード | 意味 | 対処 |
|-----------|------|------|
| 1 | slug 無効 | spec-run を停止、仕様書ファイル名をユーザーに確認 |
| 2 | base ブランチ検出失敗 | master/main どちらも存在しないリポジトリ。ユーザーに報告して停止 |
| 3 | git 操作失敗 | stderr の内容をユーザーに報告して停止 |

---

## フェーズ 3: reuse 時 spec 同期

### 目的
前回中断後に放置された worktree に、master 側で加えられた最新仕様を取り込む。進捗チェックボックスは git merge の標準動作で保持される。

### 実行条件
フェーズ 2 で **reuse フラグが立った場合のみ**。新規作成時はスキップ。

### 手順

1. cwd は worktree 内（フェーズ 2 末尾で切り替え済み）
2. base ブランチを検出: `git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`（フォールバックは master → main）
3. `git merge {base} --no-edit -m "Sync {base} into feature/{slug}"` を実行
4. 終了コードで分岐:
   - 0: 成功（または already up-to-date）→ フェーズ 4 へ
   - 非 0: コンフリクト → 「コンフリクト自動解決」セクションへ

### コンフリクト自動解決

Claude が `git status --porcelain` で conflict ファイル一覧を取得し、各ファイルに対して以下を判断する:

#### 自動解決 OK

| パターン | 判定方法 | 解決 |
|---------|---------|------|
| import 文の順序のみの差異 | diff が import 系の行のみに限定 | 両方の import を union、重複除去 |
| コメント・空白のみの差異 | diff が `//` / `#` / 空白のみ | 両方残す（実害なし） |
| 片側が完全な superset（片側は機能追加のみ） | 一方の変更が他方を完全に含む | superset 側を採用 |
| spec.md の同一チェックボックス行、両側 `[x]` | `- [x]` が両側 | `[x]` を採用 |
| spec.md の同一チェックボックス行、片側のみ `[x]` | 片側 `[x]`、片側 `[ ]` | `[x]` を採用（進捗優先） |

#### AskUserQuestion でエスカレーション

- 同じ関数のロジックが両側で変更
- spec.md の Review blockquote 内容が両側変更
- package.json / tsconfig.json 等の設定ファイル両側変更
- .env 系のファイル
- 上記パターンに当てはまらない全てのコンフリクト

エスカレーション時の選択肢:
1. ユーザーが手動解決 → 解決後に「完了」報告を待つ
2. 特定ファイルを master 側で上書き（`git checkout --theirs <file>`）
3. 特定ファイルを worktree 側で上書き（`git checkout --ours <file>`）
4. merge を abort（`git merge --abort`）して spec-run を停止

自動解決後は `git add <files> && git commit --no-edit` でマージを完了させる。

---

## フェーズ 4: Gate 実行

### 目的
通常の Gate 実行を worktree 内の cwd で行う。

### 変更点（非 worktree モードとの差分）

- cwd は worktree 内（変更なし、フェーズ 2 で切り替え済み）
- Preflight は worktree 内で実行（`.env` / `node_modules` は worktree 側に揃える）
- Codex モードでは `.tmp/codex-*.md` が worktree 側の `.tmp/` に書かれる
- Codex プラグインのパス解決（`resolve-codex-plugin.sh`）は worktree cwd でも動作する前提（Gate A/D で検証）
- ファイル編集（Read/Edit/Write）は worktree 内の絶対パスを使う
- 仕様書 spec.md の更新も worktree 内のパスで行う（master 側には cleanup 後の merge で反映される）

### 注意

- Codex プラグイン側の `task --write` が cwd=worktree で想定通り動作することを Gate D の Todo D1 で検証する
- 万一動作しない場合は spec-run を停止してユーザーに報告（フォールバックで master 側に勝手に切り替えない）

---

## フェーズ 5: 完了時 merge

### 目的
人間レビュー OK 後、worktree の全変更をローカル master にマージする。

### 実行条件

- 全 Gate 通過済み
- 「人間レビュー確認フロー」で OK を受領済み
- worktree 内に未コミット変更がない

### 手順

1. `git -C "$WORKTREE_PATH" status --porcelain` が空であることを確認（非空なら「全 Gate 通過後の完了処理」セクションでコミット済みのはずだが念のため）
2. **master ルートに cwd を戻す**: `cd "$MASTER_ROOT"`（`$MASTER_ROOT` は setup フェーズ前に `MASTER_ROOT="$(pwd)"` で事前保存しておく。`git rev-parse --show-toplevel` は worktree 内から実行すると worktree 側のルートを返すため使用しない）
3. base ブランチを検出（フェーズ 3 と同じロジック）
4. `git checkout {base}`
5. `git pull --ff-only` を試行（失敗したら警告して続行。ローカルマージを妨げない）
6. `git merge --no-ff feature/{slug} -m "Merge feature/{slug} via spec-run ({spec title})"` を実行
7. 終了コードで分岐:
   - 0: 成功 → フェーズ 6 へ
   - 非 0: コンフリクト → フェーズ 3 の「コンフリクト自動解決」ロジックを適用

---

## フェーズ 6: cleanup

### 目的
worktree と feature ブランチを削除する。

### 手順

1. cwd は master リポジトリルート（フェーズ 5 で切り替え済み）
2. `bash .claude/skills/dev/spec-run/scripts/cleanup-worktree.sh {slug}` を実行
3. 終了コードで分岐:
   - 0: 成功 → 完了処理の残りへ
   - 2: worktree 削除失敗（未コミット変更残留、または git worktree remove 失敗）→ stderr の内容をユーザーに報告して中断
   - 3: feature ブランチ削除失敗（未マージ）→ ユーザーに状況確認を依頼。merge が実際に成功していたか再確認（merge commit が存在するか確認）

### Codex モード特有

- worktree 内の `.tmp/codex-*.md` は cleanup-worktree.sh で worktree ごと消える
- master 側に `.tmp/codex-*.md` が残っていれば削除する（非 worktree モードと同様）

---

## フェーズ 7: エラーリカバリ

### dirty チェック失敗（フェーズ 1）
- ユーザーが「中断」を選んだ場合、spec-run 自体を停止

### setup 失敗（フェーズ 2）
- setup-worktree.sh の exit code に応じてユーザーに報告
- 自動リトライは行わない

### reuse 時マージ失敗（フェーズ 3）
- Claude 自動解決で解決できなかった場合、AskUserQuestion でエスカレーション
- ユーザーが「abort」を選んだ場合: `git merge --abort` → spec-run 停止。worktree は残る（次回再起動時に再 reuse が可能）

### Gate 実行失敗（フェーズ 4）
- 既存 spec-run の FIX ループに従う（worktree 特有の処理なし）
- 3 ラウンド超過したら既存プロトコル通りユーザーに判断を仰ぐ
- spec-run 中断時は worktree を残して終了（ユーザー選択の「次回 reuse」のため）

### 完了時マージ失敗（フェーズ 5）
- フェーズ 3 と同じコンフリクト自動解決ロジック
- 解決不能な場合は spec-run を停止、worktree と feature ブランチは残す（次回 reuse の選択肢をユーザーに残す）
- この時点で cwd は master にいるので、ユーザーは手動で `git merge --abort` や `git reset` で状態を戻せる

### cleanup 失敗（フェーズ 6）
- exit 2 / 3 の内容をユーザーに報告
- 自動リトライは行わない（状態破壊を避けるため）
- ユーザーは `.claude/skills/dev/cleanup-branches/` スキルを使って手動整理可能

---

## cwd 管理まとめ

| ステップ | cwd | 切替コマンド |
|---------|-----|-------------|
| Step 1-4 | master | （初期値） |
| Step 4.5 (dirty check) | master | （変更なし） |
| Step 4.6 setup-worktree.sh 呼び出し | master | （スクリプト内で cd するが戻る、stdout=絶対パス） |
| Step 4.6 末尾 | **worktree** | `cd "$WORKTREE_PATH"` |
| Step 5 以降 Gate 実行 | worktree | （変更なし） |
| 完了処理フェーズ 5 冒頭 | **master** | `cd "$MASTER_ROOT"`（setup 前に `MASTER_ROOT="$(pwd)"` で事前保存したパスを使う。`git rev-parse --show-toplevel` は worktree 内では worktree 側のルートを返すため不可） |
| cleanup 後 | master | （変更なし） |

**推奨**: setup-worktree.sh 呼び出し前に `MASTER_ROOT="$(pwd)"` で master ルートを保存しておき、フェーズ 5 冒頭で `cd "$MASTER_ROOT"` で確実に戻す。
