# GitHub履歴の調査

GitHub接続または認証済み `gh` を使う。`gh auth status` で確認し、認証情報を出力しない。使用中のschemaとCLI helpで引数を確かめ、tokenをコマンドや検証記録へ書かない。

## 検索

確認したlogin、repo、日付で置き換え、shell引数を適切にquoteする。

```sh
gh api 'users/LOGIN'
gh repo view OWNER/REPO --json nameWithOwner,visibility,defaultBranchRef
gh search prs --repo OWNER/REPO --author LOGIN --updated '>=YYYY-MM-DD' --limit 100
gh search prs --repo OWNER/REPO --reviewed-by LOGIN --updated '>=YYYY-MM-DD' --limit 100
gh search issues --repo OWNER/REPO --involves LOGIN --updated '>=YYYY-MM-DD' --limit 100
gh pr view NUMBER --repo OWNER/REPO --json author,body,commits,files,reviews,url
gh pr diff NUMBER --repo OWNER/REPO
gh api --paginate 'repos/OWNER/REPO/pulls/NUMBER/reviews'
gh api --paginate 'repos/OWNER/REPO/pulls/NUMBER/comments'
gh api --paginate 'repos/OWNER/REPO/issues/NUMBER/comments'
gh api --paginate 'repos/OWNER/REPO/issues/NUMBER/events'
```

組織ならアクセスできるrepoと調べた範囲を記す。全体検索なら返ったrepoと上限を記す。Discussionは対応する接続やGraphQLがなければ未調査とする。保持期間の短いactivity feedを一年分の履歴に代用しない。

`updated` はPR・Issueの更新であり本人の貢献時刻ではない。レビュー、コメント、コミットの実時刻と正確なloginで絞る。`involves` はmentionや割当でも一致する。URL・IDで重複を除く。

詳細をページングし、検索上限が残るなら期間を分ける。件数と欠落を資料種別ごとに記録し、取得上限やアクセス失敗があれば網羅したと宣言しない。

## コードとレビュー

パッチと周辺を読む。PR作者を全行の作者にしない。コミットと協作者を確認し、Gitのauthor文字列だけでGitHub本人を断定しない。不明な帰属は不明のままにする。

レビューの `commit_id`、行コメントの `original_commit_id`、パス、位置、hunkを確認し、その版を読む。現在のdiffには修正後の変更が含まれ得る。過去のdiffを復元できなければ判定比較から除外する。返信と解決経緯を読み、要求が必須かを決める。マージだけで本人の承認を推測しない。

## 記録

アカウント、repo、公開範囲、URL・ID、日付、レビュー対象commit、資料種別、観察、規則候補、反例を保存する。保留した評価用PRは学習材料の収集前に指定し、会話全体を収集対象から外す。

収集日、実際の締切、範囲、アクセス不能repoを記す。引用を移す前に元と保存先の公開範囲を確認する。既存の出力スキルと利用側を読んでから旧名を移行する。
