# Audit Catalog

初回監査の前に、対象scopeへ適用する独立観点を選ぶためのcatalogである。全項目を機械的に適用せず、現在のcontract、到達可能なsurface、変更経路に結び付く観点だけを選ぶ。選んだ観点は深い探索前に固定し、一件目のfindingで探索を止めない。

各観点には次を記す。

- 判定質問
- 守るcontract
- origin、mechanism、observationを結ぶ因果経路
- 探索を止める境界
- 反例または直接証拠のprobe

## Architecture

| 観点 | 主な判定質問 | 代表的な反例 |
| --- | --- | --- |
| 責務と境界 | module、service、componentが複数の変更理由を抱えていないか。公開境界は利用側の語彙になっているか。 | UI変更がstorageやschedulerへ波及する、同じ規則が複数ownerにある |
| 依存方向 | domainからadapter、上位から下位への依存が一方向か。循環や裏口importがないか。 | leafがrouteやglobal singletonを知る、barrel経由で循環する |
| state ownership | canonical、derived、local、history stateが区別され、書込ownerが一つか。 | derived stateの二重保持、複数writer、stale closureによる巻き戻り |
| asyncとresource lifecycle | 作成、開始、cancel、cleanup、retry、replaceのownerと順序が明確か。古い処理が無害になり現在処理が前進できるか。 | timer/listener/worker/object URLのleak、古いpromiseが新しいstateを上書きする |
| 外部I/Oと非決定性 | storage、network、cache、time、random、filesystemなどの境界が見えるか。 | module load時のI/O、失敗やtimeoutを注入できない、cache keyがtenantを跨ぐ |
| 公開contract | API、serialization、error、event順、auth、client分離が内部変更から保護されるか。 | 内部renameが保存形式を変える、errorを握りつぶす、別clientのstateを共有する |
| test seam | 公開挙動を観測でき、危険な失敗条件を局所再現できるか。 | private関数のmockだけで成功する、resource ownerやevent順を検証できない |
| runtime lifecycle | route、provider、singleton、SSR、shutdownを跨ぐ所有権が明確か。 | navigation後もlistenerが残る、SSRでbrowser globalへ触れる |
| dead codeとcompatibility | 現在のentryから到達可能性を証明できない旧経路や不要compatibilityが、現行contractを曖昧にしていないか。 | 利用側検索だけで消す、dynamic entryや保存済みdataからの到達を見落とす |

## Front-end

| 観点 | 主な判定質問 | 代表的な反例 |
| --- | --- | --- |
| component/API | componentの責務、props、composition boundaryが利用側の関心と一致するか。 | boolean propsの組合せが無効状態を作る、巨大componentがdomain処理を所有する |
| hook/composableと共有logic | hookやcomposableがframework lifecycleだけを扱い、純粋なdomain logicを隠していないか。 | framework外で使えない計算、effectやwatcherが複数外部作用を束ねる |
| context/provide/state/selectors | provider範囲、selector粒度、更新ownerが明確か。 | context値の毎回再生成、全画面rerender、複数provider間の同期 |
| render/hot path | render、canvas、list、timelineの更新量が入力変化に比例しているか。 | 全item再計算、不安定key、layout thrashing、不要なserialization |
| data/cache/loading | request identity、cancel、stale response、loading/error/emptyが一貫するか。 | 前画面のresponseが反映される、cacheがauth/client境界を跨ぐ |
| accessibility | role、name、state、keyboard、focus、selectionがrefactor前後で同じか。 | visual wrapper変更でaccessible nameやfocus順が変わる |
| SSR/hydration | serverとclientの初期結果が一致し、browser-only処理が適切なphaseにあるか。 | hydration mismatch、module scopeでwindow参照 |
| bundle/lazy/third-party | dependencyとlazy boundaryが必要な経路だけへ読み込まれるか。 | editor初期表示で未使用SDKを同期loadする、分割でerror boundaryを失う |
| rendering/loading strategy | CSR、SSR、static、streaming、lazy、preloadの現在方針を維持し、refactorが取得順や対話可能時点を変えないか。 | hydration前の操作を失う、prefetchがauth境界を越える、loading順が逆転する |

compound component、container/presentational、render props、provider、command、observerなどのpattern名を先にgoalにしない。現在のroot causeとcontractを固定した後、既存codebaseの規約に合う最小構造だけを選ぶ。新しいframework、state library、data fetching library、build pluginはrefactorの解決策にしない。

## Test Portfolio

テスト数、行数、実行時間の削減自体をgoalにしない。整理候補は次に限定する。

- 同じ公開入口、同じ観測結果、同じ失敗の根本原因を重ねて守る。
- 現在の製品経路から到達不能になった旧routeまたは旧contractを守る。
- private名、file配置、class、静的HTML、style、文言だけを固定する。
- 同じ分岐と根本原因を、細かな入力値だけ増やして重ねる。

次はsetupが似ていても独立したoracleとして残す。

- 異なるstate transition、failure、retry、cleanup
- event順、serialization、resource ownership、concurrency
- auth、leave、client分離、no-upload、cache isolation
- protocol、error code、保存形式、role、name、stateなど値自体がcontractのもの
- 過去の別root causeを再発防止するもの

削除または統合の前に、守るcontractまたは再発条件と、削除後に残すbehavior oracleを対応付ける。残るoracleがなければ先にcharacterization testへ置き換える。競合、resource lifecycle、event順など高リスクな候補は、可能なら故障注入または失敗条件の一時復元で、残すテストだけがfailureを検出することを確認する。

`skip`、`todo`、retryの追加、timeout緩和、coverage除外、弱いsnapshotへの置換を整理として扱わない。test count、line count、runtimeは前後差を説明する情報であり、合否条件ではない。

## Performance

性能を独立観点にするのは、性能改善を主張する場合、またはrender、canvas、large list、scheduler、queue、serialization、resource lifecycleなどhot pathを変更する場合である。

- 同じhost、data、操作、build mode、sample条件でbefore／afterを測る。
- warm-up、中央値、分布または幅を残す。
- profiler、browser trace、counterなど、因果経路へ届く計測を選ぶ。
- 測定変動内の差を改善と主張しない。
- 計測用code、flag、artifactをproductionへ残さない。

## Integration and Cross-boundary

変更が複数境界へ届く場合は、個別moduleの正しさだけでなく次を確認する。

- producerとconsumerが同じcontractを解釈する。
- route、provider、cache、storageを跨いでもstate ownerが増えない。
- 古い処理が無害になり、現在の処理が前進できる。
- auth、tenant/client、共有状態、外部作用が混ざらない。
- error、cancel、retry、cleanupが正常系と同じownerへ戻る。

## 候補をfindingへ昇格しない条件

次のいずれかならP3または`non_applicable`とする。

- 現在の導線から到達できない。
- 破られる現在contractを示せない。
- 観測可能な悪化、失敗条件または保守コストを示せない。
- 最小修正境界が製品成果の変更を必要とする。
- 一般論、好み、命名統一、将来の推測だけである。

contract、対象surface、因果経路または観点集合を変えないと調べられない候補は、現在runへ追加しない。GateをHOLDし、新しいscopeとして再判断する。
