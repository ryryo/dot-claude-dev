# 架空のAPI改名案

内部field `filing_or_form4` を `event_source` に変える。新しい呼び出し元がanalyst noteも送るため。

TypeScriptがJSON成果へ書き、Pythonがoffline評価で読む。外部dashboardも読む可能性があるが契約の証拠はない。提案は新fieldを加えて旧fieldを無期限の互換aliasとして残す。呼び出し元一覧、保存形式のfixture、影響するテストの対応は未提示。
