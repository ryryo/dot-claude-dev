# 歴史的資料の調べ方

利用できる資料の種類ごとに調べる。委譲が許可されていれば一種類一担当にし、許可がなければ主担当が区分を分けて順に調べる。以下のMCP名は例であり、実際に利用できる接続のschemaへ合わせる。

| 種類 | 手順 | 例 |
|---|---|---|
| ソースの履歴 | [code-archaeology](sources/code-archaeology.md) | Git、gh |
| チケット | [linear](sources/linear.md) | Linear、Jira、GitHub Issues |
| 長い資料 | [notion](sources/notion.md) | Notion、Confluence、Google Docs |
| 会話 | [slack](sources/slack.md) | Slack、Teams、Discord |
| 稼働記録 | [datadog](sources/datadog.md) | Datadog、New Relic、Grafana |
| エラー | [sentry](sources/sentry.md) | Sentry、Rollbar、Bugsnag |
| 製品の利用データ | [databricks](sources/databricks.md) | Databricks、BigQuery、Snowflake |

null検査、retry、timeout、rate limit、feature flag、egress guard、OOM処理など防御的なコードには [障害履歴の観点](sources/incident-postmortem.md)も加える。
