# エラー履歴の調査

Issue、event、release、replay、profile、コメントから失敗と修正の時期を調べる。

1. `find_organizations`、`find_projects` 等でorgとprojectを確認する。
2. `search_issues` 等で例外名、関数・クラス、エラー文字列、パスを探す。
3. `search_issue_events`、`get_issue_tag_values` 等でrelease、期間、環境、trace、tagを絞る。最初・最後の発生、影響版、頻度の推移を確認する。
4. `get_sentry_resource` 等で全文を開き、stackが対象を通るか、breadcrumbが条件に合うか読む。
5. `find_releases` 等でcommit・PRの日付と照合する。
6. `analyze_issue_with_seer` 等のAI分析は仮説作成に限り、実event、stack、日時を一次証拠にする。

grouping変更で別IDへ移った可能性、同releaseの別修正、上流の変化、手動のresolved、samplingを確認する。resolvedを修正の証明にしない。

ID・題名、project・org、最初・最後の日時、件数と分かるsampling率、影響release、関連stackの短い抜粋、採用日の相関、URL、作者のコメントを返す。
