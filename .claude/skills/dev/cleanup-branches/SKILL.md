# cleanup-branches

不要なローカル・リモートブランチとworktreeを一括削除するスキル。
master/developにマージ済みのブランチを検出し、ユーザー確認後に削除する。

## トリガー

`/cleanup-branches` または「ブランチ整理」「不要ブランチ削除」

## 実行フロー

### Step 1: 現状調査

以下を**並列実行**する:

```bash
git branch -a
git branch -a --merged master
git worktree list
```

### Step 2: 削除候補リストアップ

以下の分類でテーブル表示する:

**ローカルブランチ:**

| ブランチ | masterにマージ済み | 削除候補 | 備考 |
|---|---|---|---|

**リモートブランチ:**

| ブランチ | masterにマージ済み | 削除候補 | 備考 |
|---|---|---|---|

メインブランチの特定:
```bash
git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
```
失敗した場合は `master` または `main` のうち存在する方を使用する。

分類ルール:
- メインブランチ（master/main）は常に**保持**
- `develop` は常に**保持**
- リモートのメインブランチ・developも常に**保持**
- メインブランチにマージ済みのブランチは**削除候補**
- 未マージでも明らかに古い試行ブランチは**削除候補**（備考に理由を記載）
- worktree使用中のブランチは備考に `worktree使用中(+)` と記載

### Step 3: ユーザー確認

AskUserQuestion で削除を確認する。

### Step 4: 削除実行

以下の順序で実行:

1. **Worktree削除**（ブランチに紐づくworktreeがある場合）
```bash
git worktree remove --force <path>
```

2. **ローカルブランチ削除**
```bash
git branch -d <branch1> <branch2> ...
```

3. **リモートブランチ削除**
```bash
git push origin --delete <branch1> <branch2> ...
```

### Step 5: 完了確認

```bash
git branch -a
```

削除結果のサマリーを表示:
- Worktree: X個削除
- ローカルブランチ: X本削除
- リモートブランチ: X本削除
- 残りのブランチ一覧
