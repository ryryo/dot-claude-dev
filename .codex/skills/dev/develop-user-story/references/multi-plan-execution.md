# 複数worktree向けPLAN設計

対象scopeが複数の独立成果へ分かれ、別worktree／sessionで直列・並列に進める場合だけ読む。USは利用者契約、PLANは実行契約、進行PLANは実行graphの正本として分離する。

## 1. 分割可否を先に判定する

実行PLANへ分ける候補は、次をすべて満たす場合だけ採用する。

1. 先行Gateまたはbaselineを明示すれば、別sessionが追加の製品判断なしに開始できる。
2. 排他的write scopeを持ち、同じsource、generated file、lockfile、台帳、EVIDENCE、外部状態を別laneと同時変更しない。
3. candidate commit、固定した公開interface、検証結果、外部操作結果など、統合ownerへ渡す成果が明確である。
4. focused test、typecheck、build、dry-runなど、handoff前にlocalで再現できる強いoracleがある。
5. merge、shared glue、生成物再生成、上位test、Journey、台帳更新を所有する統合先が一つに決まる。
6. worktree作成、merge、reviewの追加費用を上回る並行化または責務分離の実益がある。

条件数、技術layer、画面数、US境界だけで分割しない。同じstateやcommand/historyを連続変更する、同じfileを往復する、統合前に合否を判定できない候補は一つの実行PLANのPhaseにまとめる。

## 2. plan setを一度に作る

複数PLANが必要なら、一回の計画操作で次を揃える。

- 実行PLAN: 一つのmerge可能な成果を、一つのworktree／sessionでhandoffする契約。
- integration PLAN: 複数candidateのmerge、shared glue、生成物、上位検証、実装後review、Journey、台帳更新に実作業がある場合の実行PLAN。
- external PLAN: deploy、課金、外部データ変更など、別承認と単一ownerが必要な操作を独立sessionへ分ける場合の実行PLAN。
- 進行PLAN: 上記PLANの依存、状態、割当、統合順を管理するindex。実装は所有しない。

integrationやexternalの作業が小さく独立sessionを要しない場合は、別PLANを増やさず、既存の統合実行PLANへ含める。既存PLANを再編する場合は、検証済みの履歴を失わない。新しい実行入口を進行PLANへ一本化し、旧PLANを残すならarchive／supersededと明示して二重の正本を作らない。

実行PLAN名はUS IDではなく安定した成果名を使う。例: `YYMMDD_wt-editor-shell.md`。worktree名やbranchは実行時に変わり得るため、成果名をfileのidentityとし、実際の割当は進行PLANへ記録する。

## 3. 実行PLANの必須契約

repositoryのPLAN templateを使い、少なくとも次を固定する。

- role: `candidate`、`integration`、`external`のいずれか
- 対象USと条件ID。partial実装と最終確認のownerを区別する
- 開始baselineと先行Gate
- read scope、排他的write scope、write禁止
- Goalとhandoff先
- handoff成果: commit、公開interface、検証結果、未解決事項
- integration ownerへ残す作業: merge、shared glue、generated file、lockfile、上位test、Journey、台帳／EVIDENCE更新
- focused検証とhandoff Gate
- 契約変更、owner競合、外部承認不足に対する停止条件

candidateは、自分のcommitとlocal oracleが成立した時点でhandoffする。merge後Gate、実Journey、USの`implemented`／`verified`、台帳、共有進行PLANを更新しない。integrationまたはexternal ownerだけが、同じ統合baselineの実結果から最終状態を更新する。

## 4. 進行PLANの必須契約

進行PLAN名は`YYMMDD_{scope}_execution.md`を既定とし、次だけを持つ。

1. 対象scope、開始baseline、全体完了条件、coordination owner。
2. Mermaid DAGまたは同等の依存graph。直列edge、並列lane、merge point、外部停止Gateを区別する。
3. 次の列を持つPLAN台帳。

| lane | PLAN | role | 対象条件 | depends on | handoff先 | worktree／session | 状態 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<stable-id>` | `<path>` | `candidate/integration/external` | `<US-XX-NN>` | `<Gateまたはなし>` | `<lane>` | `<未割当または実値>` | `planned/ready/active/handoff/merged/verified/blocked` |

4. source、generated file、lockfile、PLAN、台帳、EVIDENCE、外部状態のowner表。
5. candidateのmerge順、生成物再生成、上位検証、review、Journey、deployの順序。
6. 現在のready lane、停止理由、再開条件。依存が変わったときだけ更新する。

個別PLANのPhase、command、詳細task、受け入れ条件本文を複製しない。条件IDとlinkで参照する。進行PLANの状態更新はcoordination／integration ownerだけが行い、candidate sessionはhandoff結果を返すだけにする。

## 5. plan set review

4.1の独立レビューは、進行PLANと全実行PLANを一つのartifactとして行う。通常はreviewer一名・Gate一回でよい。次を反証する。

- 全条件IDに実装ownerと最終確認ownerがあり、重複・空白・未確認の完了扱いがない。
- graphに閉路、不要な直列待ち、未記載のmerge pointがない。
- 並行laneのwrite scopeと外部状態ownerが排他的である。
- candidateが単独でUS完了を主張せず、統合baselineで上位test、review、Journeyが再実行される。
- 実行PLAN単体を新規sessionへ渡しても、開始条件、成果、禁止範囲、handoff先を推測せず実行できる。
- PLANの分割費用に見合う並行化利益があり、同じcodeを複数laneで二度実装しない。

意味変更を反映した場合は、影響する実行PLANだけでなく、依存、owner、条件追跡が変わる進行PLANも同じreviewerへ再確認させる。
