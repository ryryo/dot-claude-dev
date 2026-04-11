# worktree セットアップ（spec-run 用）

Step 4 で worktree 使用を選択した場合のみ適用。セッション開始時に1回だけ実行する。

## 前提

- `.worktrees/` と `.tmp/` は `.gitignore` 登録済み
- setup-worktree.sh は `.claude/skills/dev/spec-run/scripts/` に配置済み
- Bash tool の cwd は永続する前提で設計

---

## フェーズ 1: dirty チェック

master の未コミット変更が worktree 作成後のマージ時にコンフリクトを生まないようにする。

1. `git status --porcelain` を実行
2. 出力が空なら → フェーズ 2 へ
3. 出力に行があれば AskUserQuestion で以下を選択:
   - **コミット**: `/dev:simple-add` スキルを呼び出してコミット（ユーザーに内容確認を任せる）
   - **stash**: `git stash push -m "spec-run worktree setup: {slug}"` を実行（完了時の pop はユーザー責任。spec-run は pop しない）
   - **中断**: spec-run を停止、ユーザーに対応を任せる

---

## フェーズ 2: setup

`.worktrees/{slug}/` と `feature/{slug}` ブランチを作成する（既存なら reuse）。

1. `MASTER_ROOT="$(pwd)"` で master ルートを記憶（完了処理で戻るために必須。`git rev-parse --show-toplevel` は worktree 内では worktree 側ルートを返すため使用不可）
2. slug を決定: 仕様書ファイル名から拡張子を除いたもの（例: `260411_dashboard-table-view.md` → `260411_dashboard-table-view`）
3. `bash .claude/skills/dev/spec-run/scripts/setup-worktree.sh {slug}` を実行
4. stdout の 1 行を `$WORKTREE_PATH` として記憶
5. stderr を確認し、"already exists, reusing" を検出したら **reuse フラグ** を立てる
6. `cd "$WORKTREE_PATH"` で cwd を worktree に切り替え（以降の全 Bash コマンドは worktree 内で動作）

### 失敗時

| 終了コード | 意味 | 対処 |
|-----------|------|------|
| 1 | slug 無効 | spec-run を停止、仕様書ファイル名をユーザーに確認 |
| 2 | base ブランチ検出失敗 | master/main どちらも存在しないリポジトリ。ユーザーに報告して停止 |
| 3 | git 操作失敗 | stderr の内容をユーザーに報告して停止 |

---

## フェーズ 3: reuse 時 spec 同期

**実行条件**: フェーズ 2 で reuse フラグが立った場合のみ。新規作成時はスキップ。

前回中断後に放置された worktree に、master 側で加えられた最新仕様を取り込む。

1. cwd は worktree 内（フェーズ 2 末尾で切り替え済み）
2. base ブランチを検出: `git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`（フォールバックは master → main）
3. `git merge {base} --no-edit -m "Sync {base} into feature/{slug}"` を実行
4. 終了コードで分岐:
   - 0: 成功（または already up-to-date）→ Step 5 へ
   - 非 0: コンフリクト → 「コンフリクト自動解決」セクションへ

### コンフリクト自動解決

Claude が `git status --porcelain` で conflict ファイル一覧を取得し、各ファイルに対して以下を判断する:

#### 自動解決 OK

| パターン | 判定方法 | 解決 |
|---------|---------|------|
| import 文の順序のみの差異 | diff が import 系の行のみに限定 | 両方の import を union、重複除去 |
| コメント・空白のみの差異 | diff が `//` / `#` / 空白のみ | 両方残す（実害なし） |
| 片側が完全な superset | 一方の変更が他方を完全に含む | superset 側を採用 |
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

## cwd 管理まとめ

| ステップ | cwd | 切替コマンド |
|---------|-----|-------------|
| Step 1-4 | master | （初期値） |
| フェーズ 1 dirty check | master | （変更なし） |
| フェーズ 2 setup-worktree.sh 呼び出し | master | （スクリプト内で cd するが戻る、stdout=絶対パス） |
| フェーズ 2 末尾 | **worktree** | `cd "$WORKTREE_PATH"` |
| Step 5 以降 Gate 実行 | worktree | （変更なし） |
