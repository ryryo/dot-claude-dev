# 検索例と制約

必要な例だけ使う。以下は macOS の zsh/bash、WSL の bash で使える。外部 `jq`、GNU 固有コマンド、検索用スクリプトは不要。語句・作者・件数は今回の目的に合わせて変える。数値は品質基準ではない。

## 実行前

```sh
gh --version
gh search repos --help
gh repo view --help
gh api --help
```

利用環境の help と下記公式文書で利用する引数・フィールドを確認する。認証が必要なら通常の認証手順を案内し、トークンを出力しない。認証・ネットワーク・レート制限で失敗したら連続再試行せず、公開 Web・コネクター・ブラウザへ切り替えるか、確認できた範囲を報告する。

## 定番起点と README の補完

```sh
gh search repos 'sqlite in:name,description' \
  --visibility public --sort stars --limit 10 \
  --json fullName,url,description,stargazersCount,pushedAt,isArchived,license,visibility

gh search repos 'libxev in:readme' \
  --visibility public --limit 10 \
  --json fullName,url,description,stargazersCount,visibility
```

- Repository search の既定の語句対象は名前・説明・topics。`in:readme` で README も探せるが、任意のソース本文は検索しない。関数名・ファイル内容は別のコード検索で扱い、必要時にその構文と制約を確認する。
- `--topic sqlite`、`--language Go` などで絞れるが、topic 未設定や別言語の参考実装も考慮する。`in:topics` はクエリで指定できる一方、`--match` の選択肢は `name,description,readme`。
- `--sort stars` は発見順の一つ。たとえば `--stars '>=100'` を使っても、その閾値を全経路へ流用しない。候補不足なら閾値・語句・技術条件を緩める。
- `--archived=false` や `'pushed:>=2026-01-01'` は現役の依存候補に絞る場合の例。通常の参考実装探しでは固定せず、古い・archived な候補を残せる検索も使う。`createdAt` は開発開始日や初回公開日とは限らず、`pushedAt`/`updatedAt` も人による機能開発・保守の証拠とは限らない。
- fork は既定では除外される。派生実装が重要なら `--include-forks true` を使い、元との関係を確認する。

## 作者起点

まず関連 OSS の作者・主要貢献者、作者サイト、発表・紹介記事から専門分野の実績を辿る。記事の同姓同名や古い所属を避け、プロフィールからの相互リンクや OSS のクレジット等で同一人物か確認する。Users 検索は作者を見つける補助経路として使う。

```sh
gh api --method GET search/users \
  -f q='type:user language:go followers:>1000' \
  -f sort=followers -f order=desc -F per_page=5 \
  --jq '.items[] | {login,html_url,type}'

gh api --method GET users/mitchellh \
  --jq '{login,html_url,bio,blog,followers}'

gh search repos --owner mitchellh --visibility public --limit 10 \
  --json fullName,url,description,stargazersCount,visibility
```

この作者名は動作する例であり、毎回の推薦リストではない。`--owner` に分野の実績を確認した作者・組織を指定し、star 下限を設けず、用途に関係するプロジェクトを探す。公開リポジトリが多ければ機能語・README 検索を足し、star 順の上位だけで探索を終えない。既存 OSS への主要貢献は所有 repo の一覧だけでは判断できないので、必要な範囲で公開のクレジットや貢献を示す資料を開く。

- **Users** の `followers:` はユーザーの follower 数。**Repositories** の `followers:` / `gh search repos --followers` はリポジトリを follow するユーザー数であり、owner の人気を絞るものではない。
- Users の `language:` は所有リポジトリの言語の手掛かりであり、今回の専門性の証明ではない。followers の小さい作者も関連 OSS や記事から拾う。
- `owner reputation`、投入時間・労力・実装品質を直接絞る repository qualifier はない。Users の人気から作者を特定して `--owner` へ渡す二段階と、関連分野の実績の確認を組み合わせる。
- `gh api` は `-f` / `-F` を足すと既定が POST になるため、検索例は `--method GET` を明示する。`per_page` と `--limit` は取得件数であり、網羅性を保証しない。

## 候補の軽い確認

検索で public を確認した候補を明示する。

```sh
gh repo view mitchellh/libxev \
  --json nameWithOwner,url,description,stargazerCount,pushedAt,isArchived,licenseInfo,visibility

gh repo view mitchellh/libxev
```

2つ目は説明と README を読む。`visibility` が public 以外なら内容確認を進めない。検索の `stargazersCount` と詳細の `stargazerCount`、`license` と `licenseInfo`、`fullName` と `nameWithOwner` は別名なので混ぜない。コネクター等でも対象が公開であることを確認する。

ライセンスの許容範囲が決まっていれば `--license mit` や `--license apache-2.0` 等で検索を分けられる。MIT・Apache・BSD 系を固定の許容リストにせず、BSD の種類や複数ライセンスも含めてユーザーの条件に合わせる。検索表示は暫定情報であり、欠落・独自条件があれば未確認とする。

採用段階で実ファイルを読む例:

```sh
gh api --method GET repos/mitchellh/libxev/license \
  -H 'Accept: application/vnd.github.raw+json'
```

これは既定ブランチの検出された LICENSE を読む例。採用する tag/commit の LICENSE、NOTICE、対象ファイル・同梱物に別条件がないかも確認する。404 や検出不能なら「自由に使える」と解釈しない。

## 公式資料

- [Repository search の検索対象・qualifier](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)
- [Users search の qualifier](https://docs.github.com/en/search-github/searching-on-github/searching-users)
- [gh search repos の引数・JSON](https://cli.github.com/manual/gh_search_repos)
- [gh repo view の引数・JSON](https://cli.github.com/manual/gh_repo_view)
- [gh api の GET・field・jq](https://cli.github.com/manual/gh_api)
- [REST Search users の引数・応答](https://docs.github.com/en/rest/search/search#search-users)
- [実 LICENSE の取得・raw 応答](https://docs.github.com/en/rest/licenses/licenses#get-the-license-for-a-repository)

2026-10-16 に gh 2.73.0 の help と公式文書を照合し、上記の代表コマンドを小さい件数で公開情報に対して実行確認した。star 数・候補・API 仕様は固定値として扱わず、使用時に確認する。
