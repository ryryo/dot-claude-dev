# 製品の利用データとシステム表

稼働の記録に対し、製品イベント、利用・料金、実験・flag、dbtの依存から利用者とデータの背景を調べる。会社固有の表をあるものと仮定しない。

`execute_sql_read_only` 等を使う。`statement_id` が返れば `poll_sql_result` 等で待ち、クエリを再実行しない。

```sql
SHOW TABLES IN <your_analytics_db>.<schema> LIKE '*<keyword>*';
DESCRIBE TABLE <your_analytics_db>.<schema>.stg_<event>;
```

期間を `_timestamp` または `system.query.history` の `start_time` で絞る。変更前後30日程度を起点とし、無制限に走査しない。typedで重複除去されたdbtモデルを優先し、rawの `your_warehouse.events.analytics_track_event`、`usage_event`、`raw_model_event` はモデル未作成または更新遅れの確認に使う。直近rawは `_id` で重複を除く。

モデル名の例は `stg_<source>_<event_name_with_underscores>`。`app`、`backend`、`website`、`cli` 等のsourceと実名を確認する。標準列の例は `_timestamp`、`_id`、`_auth_id`、`_request_id`、`event_name`。属性は `properties_<name>`、contextは `context_team_id`、`context_client_version`、`context_country`、`context_client_os`。

- 関連イベントの日別件数を採用前後で見る。増減が計測の追加・変更でないか照合する。
- 閾値の由来なら変更前14日の中央値・p99・最大を確認する。
- 実験表は `SHOW TABLES ... LIKE '*experiment*'` 等で見つけ、flagの露出と結果を読む。
- `system.query.history` の `statement_text` と狭い期間で対象を絞り、`total_duration_ms`、`SUM(read_bytes)`、`COUNT(*)` 等を見る。
- `system.compute.warehouses`、`system.billing.*`、`system.access.audit` は実在と権限を確認して使う。dbtの履歴はGit担当へ手がかりを渡す。

イベントの存在をコードの因果にしない。属性schemaの変化、dbt更新遅れ、保持期限を欠落として記す。SQL接続でnotebookを読めない場合は未調査とする。

種類、完全修飾表名、正確なクエリ、期間、件数・分位点・初回最終時刻の短い集約、採用日との関係、直接・間接・弱い証拠の別を返す。raw行を大量に流さない。
