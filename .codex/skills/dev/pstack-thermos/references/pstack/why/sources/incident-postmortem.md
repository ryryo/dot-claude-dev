# 障害履歴を重ねる観点

独立した資料種別ではなく、防御的なコードへ各資料の中で加える観点である。null、retry、timeout、rate limit、feature flag、egress、OOM等なら次を探す。

- 設計資料の障害分析と対応項目。
- チケットの `incident`、`sev-*`、`postmortem-action-item`、`reliability`。
- 会話の `#sev-*`、`#incident-*` と追加時期。
- Gitの障害対応、ガード追加、revertと再適用。
- Datadogのincident、作成されたmonitor・dashboard。
- Sentryの初回・最終発生と対象stack。
- 利用データのエラー、retry、失敗イベントの増減。

障害リンクがあれば分析全文と対応項目を読む。複数資料が同じID、PR、時系列を支持するか照合する。別資料の発見は担当へ渡し、重複調査しない。防御的でないコードには無理に適用しない。
