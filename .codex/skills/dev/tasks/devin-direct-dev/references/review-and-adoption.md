# 成果のレビューと採用

## PRの独立照合とDevin Review

`gh pr view`、`gh pr diff`、GitHub API、コードを読むためのfetchを使う。対象リポジトリ・base/head・本文・変更範囲・checksを照合する。共有作業ツリーのcheckoutを切り替えず、必要なコードを読む。PR作成後は`attach_artifact`で現在のチャットへ添付する。

難しい変更でDevin Reviewを使う場合、[公式のPRコメント起動](https://docs.devin.ai/work-with-devin/devin-review#triggering-a-review-from-a-pr-comment)を使える。これは本スキルを使ってレビューまで依頼された対象PRについてのDevinへの起動指示である。相談・スキル説明だけではコメントを投稿しない。

```sh
gh pr comment PR_URL --body '/devin review'
```

対象リポジトリが組織のGitHub Appに含まれ、PRがOpenであることを確認する。投稿者にはwrite/admin権限と、GitHubアカウントのDevinへの連携が必要である。Reviewのためにリポジトリ全体のauto-reviewやauto-fixを有効化する必要はない。別の`/devin`文言は通常セッションを起動し得るため、この指示を曖昧に言い換えない。対象headと投稿済みコメントを記録し、応答が遅いだけで同じheadに重複投稿しない。

GitHubのPR会話・review comments・checksと、関連するDevinセッションのmessages/events/attachmentsを読む。対象head、分析が完了したか、取得できる指摘を確認する。Review画面へのリンクだけが返された場合は、全指摘を取得した、指摘がなかった、分析が完了したとは扱わない。Devinが作成したPRでは、指摘が先に作者セッションへ渡る場合もある。GitHubにコメントがないことだけで、指摘がないと判断しない。

指摘の全文や対象headをAPI/CLIで取得できない場合も、Codexのレビューは続ける。通常のコードレビューを行っただけで、Devin Reviewを実行済みと記録しない。Devin Reviewが採用条件なら、未確認の項目を記録して採用を保留する。ブラウザを開いて条件を満たしたことにしない。作業条件で必須とされていなければ、Codexのレビューと必要な検証で採否を決め、Reviewで確認できなかった範囲を明記する。

指摘は実コード・契約と照合し、有効なものを同じ実装セッションへ返す。更新headが分析対象と違う場合は、修正の影響に応じて再確認する。Devin Reviewの成功や指摘ゼロだけで採用しない。

## Headを照合したマージ

マージまで許可され、重要な指摘が解決し、必要な検証・repoの条件を満たせば、`gh pr merge`等で採用する。直前に実headを再取得し、レビューしたSHAとの一致を確認する。利用するCLIが対応していれば`--match-head-commit`へそのSHAを指定し、repoで認められたmerge方式を選ぶ。`--admin`や強制で必須条件を迂回しない。

操作後はGitHubの`state=MERGED`とmerge commitを取得する。auto-merge設定の受領、プロセスの成功、Devinの返答だけで、マージ済みと判断しない。結果が不明なら、同じPRの状態を取得して確認する。

## 環境提案とCLI

[公式CLIのDRS](https://docs.devin.ai/cli/reference/commands#devin-cloud-drs)にはblueprint-list、blueprint-write、build-start、build-logs等がある。これは任意のUI提案カードの「承認」APIではない。提案の保存とsnapshot有効化を同一操作として仮定しない。

今回の依頼で環境の採用が許可されている場合、対象リポジトリ、既存blueprint、提案の全文とスクリプト、実際の状態を取得する。固定された依存、公式の配布元、試験データの分離、資格情報と公開範囲を確認する。CLIの`--help`と操作の対象範囲を読み、今回のリポジトリに必要な変更だけを行う。`blueprint-write`は内容を置換するため、他者の既存設定を保持する。組織全体をbuildする操作を、対象リポジトリだけのbuildと推測しない。

既に成功・適用済みなら、再buildしない。buildが必要なら開始時のIDを保持し、成功・失敗と適用対象を実際に確認する。資格情報を含む可能性があるログを、無差別に出力・保存しない。CLIで適用済みの状態や画面上の提案との対応を確認できなければ、その工程を未確認として残す。環境の準備が成功しても、製品の接続や実機での検収が成功したとは扱わない。
