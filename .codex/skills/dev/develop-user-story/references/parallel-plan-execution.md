# 並列実行可能なPLAN設計

対象scopeが複数の独立成果へ分かれ、直列・並列の実行graphが必要な場合だけ読む。USは利用者契約、PLANは成果と実行内容の契約、進行PLANは依存graphの正本として分離する。実行主体や実行環境の識別子は計画外の管理情報とし、PLANへ記録しない。

## 1. 分割可否を先に判定する

実行PLANへ分ける候補は、次をすべて満たす場合だけ採用する。

1. 先行Gateと必要な開始状態を明示すれば、別の実行主体が追加の製品判断なしに開始できる。
2. 排他的write scopeを持ち、同じsource、generated file、lockfile、台帳、EVIDENCE、外部状態を別laneと同時変更しない。
3. 変更path、固定した公開interface、検証結果、外部操作結果など、統合ownerへ渡す成果が明確である。
4. focused test、typecheck、build、dry-runなど、handoff前にlocalで再現できる強いoracleがある。
5. merge、shared glue、生成物再生成、上位test、Journey、台帳更新を所有する統合先が一つに決まる。
6. 調整、merge、reviewの追加費用を上回る並行化または責務分離の実益がある。

条件数、技術layer、画面数、US境界だけで分割しない。同じstateやcommand/historyを連続変更する、同じfileを往復する、統合前に合否を判定できない候補は一つの実行PLANのPhaseにまとめる。

## 2. plan setを一度に作る

複数PLANが必要なら、一回の計画操作で次を揃える。

- 実行PLAN: 一つのmerge可能な成果をhandoffする契約。
- integration PLAN: 複数candidateのmerge、shared glue、生成物、上位検証、実装後review、Journey、台帳更新に実作業がある場合の実行PLAN。
- external PLAN: deploy、課金、外部データ変更など、別承認と単一ownerが必要な操作を分ける場合の実行PLAN。
- 進行PLAN: 上記PLANの依存、状態、割当、統合順を管理するindex。実装は所有しない。

integrationやexternalの作業が小さく独立成果を要しない場合は、別PLANを増やさず、既存の統合実行PLANへ含める。既存PLANを再編する場合は、検証済みの履歴を失わない。新しい実行入口を進行PLANへ一本化し、旧PLANを残すならarchive／supersededと明示して二重の正本を作らない。

実行PLAN名はUS IDや実行方式ではなく安定した成果名を使う。例: `YYMMDD_editor-shell.md`。成果名をfileのidentityとし、実行主体や実行環境はPLANの外で管理する。

## 3. 実行PLANの必須契約

repositoryのPLAN templateを使い、少なくとも次を固定する。

- role: `candidate`、`integration`、`external`のいずれか
- 対象USと条件ID。partial実装と最終確認のownerを区別する
- 開始Gateと必要な状態
- read scope、排他的write scope、write禁止
- Goalとhandoff先
- handoff成果: 変更path、公開interface、検証結果、未解決事項
- integration ownerへ残す作業: merge、shared glue、generated file、lockfile、上位test、Journey、台帳／EVIDENCE更新
- focused検証とhandoff Gate
- 契約変更、owner競合、外部承認不足に対する停止条件
- 複数candidateの開始、merge、外部handoff、最終Joinを所有するintegration PLANでは、本文と同じGate名を使ったMermaid実行DAG。開始Gate、hard dependency、並行lane、merge point、条件付きfallback、external lane、最終Joinを省略しない

candidateは、自分の変更pathとlocal oracleが成立した時点でhandoffする。統合後Gate、実Journey、USの`implemented`／`verified`、台帳、共有進行PLANを更新しない。integrationまたはexternal ownerだけが、review済みcontractへ統合した実結果から最終状態を更新する。

integration PLANとは別に進行PLANやREADMEがある場合も、integration ownerが自PLANだけで実行順とhandoffを判断できるよう、実行DAGをintegration PLANへ置く。進行PLANの全台帳や個別taskは複製せず、そのintegration PLANが所有・接続するedgeとGateだけを自己完結して示す。

## 4. 進行PLANの必須契約

進行PLAN名は`YYMMDD_{scope}_execution.md`を既定とし、次だけを持つ。

1. 対象scope、開始Gate、全体完了条件、coordination owner。
2. Mermaid DAG。直列edge、並列lane、統合point、条件付きfallback、外部停止Gate、最終Joinを区別する。文章、一覧表、別fileへのlinkだけでは代替しない。
3. 次の列を持つPLAN台帳。

| lane | PLAN | role | 対象条件 | depends on | handoff先 | 状態 |
| --- | --- | --- | --- | --- | --- | --- |
| `<stable-id>` | `<path>` | `candidate/integration/external` | `<US-XX-NN>` | `<Gateまたはなし>` | `<lane>` | `planned/ready/active/handoff/merged/verified/blocked` |

4. source、generated file、lockfile、PLAN、台帳、EVIDENCE、外部状態のowner表。
5. candidateのmerge順、生成物再生成、上位検証、review、Journey、deployの順序。
6. 現在のready lane、停止理由、再開条件。依存が変わったときだけ更新する。

並行実行時は、進行管理側がwrite scope、port、Wrangler state、生成物、外部状態を衝突させない実行contextを計画外で選ぶ。PLANには実行contextの方式や識別子を書かない。

個別PLANのPhase、command、詳細task、受け入れ条件本文を複製しない。条件IDとlinkで参照する。進行PLANの状態更新はcoordination／integration ownerだけが行い、candidate ownerはhandoff結果を返すだけにする。

## 5. plan set review

4.1の独立レビューは、進行PLANと全実行PLANを一つのartifactとして行う。通常はreviewer一名・Gate一回でよい。次を反証する。

- 全条件IDに実装ownerと最終確認ownerがあり、重複・空白・未確認の完了扱いがない。
- graphに閉路、不要な直列待ち、未記載のmerge pointがない。
- Mermaidがrender可能で、図のedge、Gate名、fallback、外部lane、最終Joinが各PLAN本文と一致し、文章側だけ・図側だけに存在する依存がない。
- 並行laneのwrite scopeと外部状態ownerが排他的である。
- candidateが単独でUS完了を主張せず、review済みcontractへ統合した状態で上位test、review、Journeyが再実行される。
- 実行PLAN単体を新しい実行主体へ渡しても、開始条件、成果、禁止範囲、handoff先を推測せず実行できる。
- PLANの分割費用に見合う並行化利益があり、同じcodeを複数laneで二度実装しない。

意味変更を反映した場合は、影響する実行PLANだけでなく、依存、owner、条件追跡が変わる進行PLANも同じreviewerへ再確認させる。

## 6. 計画に置かない識別子

PLAN、進行PLAN、handoff、review metadataにはversion controlや実行環境の識別子、content digestを書かない。これらは実行時の管理情報とし、計画の開始条件、完了条件、再review条件にはしない。外部sourceの版・license provenanceが必要な場合はREFERENCE、EVIDENCE、noticeまたはdependency管理へ置き、PLANはそのpathを参照する。
