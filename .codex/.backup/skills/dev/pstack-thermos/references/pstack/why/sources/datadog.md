# 稼働状況の調査

metrics、monitor、dashboard、APM、log、incident、notebookから、変更当時に起きていたことを調べる。計測の存在は関心の証拠であり、特定コードの動機そのものとは限らない。

利用可能な接続で次を行う。名前はDatadog MCPの例であり、実際のschemaを確認する。

1. `search_datadog_services` と `search_datadog_service_dependencies` で対象と依存を確認する。
2. `search_datadog_dashboards`、`search_datadog_monitors` で機能・サービス・シンボルを探し、クエリと閾値を読む。
3. `search_datadog_metrics`、`get_datadog_metric_context`、`get_datadog_metric` で単位、tag、時系列を読む。
4. `search_datadog_logs` はservice、tag、期間で絞り、必要なら `use_log_patterns=true`。数は `analyze_datadog_logs` で集約し、生logを大量に流さない。変更前後の30日程度を出発点にする。
5. `aggregate_spans`、`search_datadog_spans`、`get_datadog_trace` でtimeout・retry・サービス間の経路を追う。
6. 防御的なコードなら `search_datadog_incidents`、`get_datadog_incident` で時系列と対応策を読む。

変更前の急増と変更後の安定は相関であり、同時期の別PRも照合する。図の題名、metricの存在だけで因果を断定しない。削除・改名・保持期限をゼロ件と混同しない。

各項目の種類、名称、リンク・ID、作者と日時、関係する条件・クエリ・引用、対象コードとの関係と証拠の強さを返す。
