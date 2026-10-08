# ブラウザなしの成果採用

## PRの独立照合とDevin Review

`gh pr view`、`gh pr diff`、GitHub API、read-only fetchを使い、対象repo・base/head・本文・変更範囲・checksを照合する。共有checkoutを切り替えず必要なコードを読める。PR作成後は現在のチャットへ`attach_artifact`する。

難しい変更でDevin Reviewを使う場合、[公式のPRコメント起動](https://docs.devin.ai/work-with-devin/devin-review#triggering-a-review-from-a-pr-comment)を使える。これは本スキルを使ってレビューまで依頼された対象PRについてのDevinへの起動指示である。相談・スキル説明だけではコメントを投稿しない。

```sh
gh pr comment PR_URL --body '/devin review'
```

組織のGitHub App対象repo、Open PR、投稿者のwrite/admin権限、GitHubアカウントとDevinのlinkが前提。Reviewのためにrepo全体のauto-reviewやauto-fixを有効化する必要はない。別の`/devin`文言は通常セッションを起動し得るため、この指示を曖昧に言い換えない。対象headと投稿済みコメントを記録し、応答が遅いだけで同じheadに重複投稿しない。

GitHubのPR会話・review comments・checksと、関連Devinセッションのmessages/events/attachmentsから、対象head、分析完了、取得できる指摘を確認する。返却がReview画面へのリンクだけなら、全指摘を取得済み、指摘ゼロ、分析完了とは言わない。Devin作者PRでは指摘が先に作者セッションへ渡る場合もあるため、GitHubのコメント不在だけでゼロ判定しない。

指摘の全文・対象headをAPI/CLIで取得できない場合、通常のコードレビューをDevin Review実行済みの代わりに記録しない。Codexの独立レビューは続ける。Devin Reviewが採用条件なら、その未確認を残して採用を保留する。ブラウザを開いて満たしたことにしない。契約上必須でないなら、独立レビューと必要な検証で採否を決め、Reviewの確認限界を明記する。

指摘は実コード・契約と照合し、有効なものを同じ実装セッションへ返す。更新headが分析対象と違う場合は、修正の影響に応じて再確認する。Devin Reviewの成功や指摘ゼロだけで採用しない。

## Headを照合したマージ

マージまで許可され、重要な指摘が解決し、必要な検証・repoの条件を満たせば、`gh pr merge`等で採用する。直前に実headを再取得し、レビューしたSHAとの一致を確認する。利用するCLIが対応していれば`--match-head-commit`へそのSHAを指定し、repoで認められたmerge方式を選ぶ。`--admin`や強制で必須条件を迂回しない。

操作後はGitHubの`state=MERGED`とmerge commitを取得する。auto-mergeの設定受領、process成功、Devinの返答だけをマージ済みとしない。結果不明なら同じPRを読み直してから扱う。

## 環境提案とCLI

[公式CLIのDRS](https://docs.devin.ai/cli/reference/commands#devin-cloud-drs)にはblueprint-list、blueprint-write、build-start、build-logs等がある。これは任意のUI提案カードの「承認」APIではない。提案の保存とsnapshot有効化を同一操作として仮定しない。

環境採用が今回の許可に含まれる場合、対象repo・既存blueprint・提案の全文とscript・実状態を取得し、固定依存、公式配布、試験state分離、資格情報と公開範囲を確認する。CLIの`--help`と現在の対象範囲を確認し、今回のrepoに必要な変更だけを行う。`blueprint-write`は内容の置換なので他者の既存設定を保持する。組織全体をbuildする操作を対象repoだけのbuildと推測しない。

既に成功・適用済みなら再buildしない。必要なら開始IDを保持してbuildの成功・失敗と適用対象を実際に照合し、資格情報を含み得るraw logsを無差別に出力・保存しない。CLIで適用済み状態やUI提案との対応が確認できなければ、その工程を未確認として残す。製品接続や実機検収の成功には読み替えない。
