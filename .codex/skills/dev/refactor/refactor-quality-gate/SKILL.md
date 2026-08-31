---
name: refactor-quality-gate
description: "コードベースまたは指定範囲を、製品挙動を変えずにarchitecture、front-end、test portfolioの観点で一括監査し、goal freeze、依存順の実装、全観点の独立review、必要な一括修正、変更影響だけの再reviewまで進める。複数責務、状態・副作用、描画、性能、テスト構成を横断する中〜大規模refactorで使う。単一bug修正、機能追加、review-only、根拠のない一般的hardeningには使わない。"
---

# Refactor Quality Gate

指定範囲のarchitecture、front-end、test portfolioを一つの品質Gateとして扱う。全適用観点を最初に一巡してからgoalを凍結し、実装後の独立reviewでも全候補を一度に分類する。修正後は変更影響だけを再reviewし、同じ固定範囲の全面監査を反復しない。

標準進行は次で固定する。

`scope固定 → 初回一括監査 → goal freeze → 依存順の実装batch → 初回一括review → 必要なら全指摘の一括修正 → 変更影響だけの再review`

ここでいう「一括」は、候補を全適用観点の一巡後に根本原因単位でまとめる意味である。複数goalを危険な巨大差分へ統合する意味ではない。

## 適用境界

次をすべて満たす場合に使う。

- 製品挙動を維持するrefactorである。
- 複数module、state owner、副作用、resource lifecycle、React境界、性能、test portfolioのうち複数観点を横断する。
- 現在のcontract、対象surface、検証oracle、write禁止範囲を固定できる。
- 採用findingを根本原因単位のgoalへ変換し、依存順に実装できる。

単一bug修正、製品機能の追加、reviewだけの依頼、対象やcontractを固定できない探索、一般的hardeningには使わない。製品成果の変更が必要ならrefactorを止め、Story、仕様または製品PLANの判断へ戻す。

## 絶対規則

1. UI、アクセシビリティ、公開API、保存形式、URL、event順、error、外部作用を変えない。
2. 適用する全観点を一巡するまで、一件目のfindingで監査を確定しない。
3. P0は実装せずGateをHOLDする。根拠のあるP1／P2だけをgoal化し、P3と根拠不足は実装しない。
4. 実装前に採用goal、依存、owner、排他的write scope、禁止範囲、behavior oracleを凍結する。
5. goal単位のdiff確認とfocused検証は安全確認であり、新規監査または独立reviewではない。
6. 初回独立reviewは、凍結した全goalの実装後に一度だけ開始する。
7. 初回reviewの`fix_here`は一つのcorrection batchへまとめる。再reviewでは既報findingと変更影響を受けた観点だけを開く。
8. 同じ固定範囲で全面監査を繰り返さない。契約、対象surface、因果経路、独立観点集合が変わった場合は現在のrunをHOLDし、新しいscopeとして再判断する。
9. 修正前から存在した見逃しは、探索不足の原因に限定して一度だけ回復確認する。見逃しが再発したら自動loopせずHOLDする。
10. 修正由来の回帰は回数制限を理由に残さない。変更影響を再reviewして解消するか、原因となるrefactorを採用しない。
11. 既存の利用者変更を戻さない。関係する差分はcontractとして読み、関係しない差分には触れない。
12. package、lockfile、toolchain、framework、dependencyをrefactorの都合で変更しない。必要なら現在runをHOLDして別の判断へ分ける。

## 同梱資料

- 監査観点とテスト整理基準は[references/audit-catalog.md](references/audit-catalog.md)を読む。
- run、manifest、stage、review partitionの契約は[references/run-contract.md](references/run-contract.md)を読む。
- manifestを作成または更新したら`python3 scripts/validate_refactor_manifest.py <manifest.json>`を実行する。

## 1. Run Inputを固定する

開始前に次を明記する。

- 対象projectと固定scope
- repository指示、現在の未コミット差分、その保護境界
- 現在の製品contractと挙動維持oracle
- write許可scopeとwrite禁止scope
- 利用可能な自動検証、実Journey、性能baseline
- 外部状態、認証、課金、deployなどの禁止副作用
- 実装者と独立reviewer
- 停止条件

進捗とmanifestは`/tmp/refactor-quality-<project>/`配下の一時成果物にする。branch、commit、worktree、port、sessionなどの実行識別子をPLAN、Story、EVIDENCEへ保存しない。

## 2. Scope Gateを通す

production変更前にrepository指示と現在差分を確認し、entry point、主要データフロー、state owner、副作用、依存方向、公開contract、test seamを一つのmapへする。対象artifactを`surface`または理由付き`excluded`へ分類し、各独立観点が少なくとも一つのsurface artifactへ結び付くことを確認する。

contract、検証baseline、全writer停止、対象scopeのいずれかが揃わなければ開始しない。外部状態を変更する操作、version control操作、PR作成、merge、deployは、利用者からその操作を明示的に依頼された場合だけ行う。

## 3. 初回一括監査を行う

[references/audit-catalog.md](references/audit-catalog.md)から適用観点を先に選び、それぞれについて次を固定する。

- 判定質問
- 守るcontract
- originから利用側の観測結果までの因果経路
- 探索を止める境界
- 反例または直接証拠のprobe

各観点は`origin`、`mechanism`、`observation`を少なくとも一つずつ確認する。一件のblockerや有望な改善で止めず、全観点を一巡してから候補を統合する。

候補には現在の到達経路、悪化する性質、確認方法、挙動維持の最小修正境界が必要である。同じ根本原因は一件へ統合し、次へ分類する。

- `P0`: 現在の製品contractまたは外部作用を破る。refactorを止めてownerへ返す。
- `P1`: 現在の挙動を維持したまま解消すべき重大な構造リスク。
- `P2`: 現在の挙動を維持したまま解消する根拠のある保守性問題。
- `P3`: 任意改善、根拠不足、到達不能。実装しない。

## 4. Goal Freezeを通す

全候補を分類した後、P1／P2だけを根本原因単位のgoalへする。各goalに次を必須とする。

- findingと守るcontract
- mainまたはworkerのowner
- 狭く排他的なwrite scopeと禁止scope
- 依存goalと実装順
- 変更前後で同じ結果を示すbehavior oracle
- focused検証と全体検証
- test portfolio観点のfindingを含むgoalなら、kindが`mixed`でも削除後に残すoracle
- 性能に影響するなら同条件のbefore／after計測、凍結済み合格閾値、結果判定
- regressionのためgoal変更を不採用にする場合のrejection reasonと、元の挙動へ戻したことを示すrestoration oracle

凍結後に新しいgoalを反復追加しない。実装中に新しい問題が見つかった場合は、変更由来の回帰、初回監査の見逃し、scope／contract変更のどれかへ分類し、後述の再入規則に従う。

採用するP1／P2が0件なら`goals`と`implementation_batches`を空のままにし、production codeとtestを変更しない。既存検証を確認して初回独立reviewへ進み、整理のためのgoalやテスト削減を捏造しない。

## 5. Safety Netとtest portfolioを整える

既存testで守れない外部挙動があるgoalだけ、変更前にcharacterization testを追加する。内部名、class名、file配置、静的なstyleや文言を固定するテストを増やさない。

テスト整理は、同じ公開入口、同じ観測結果、同じ失敗の根本原因を重ねて守るもの、到達不能な旧経路、内部実装の固定、同じ分岐の入力値展開だけを候補にする。削除または統合の前に、残す公開挙動のoracleを固定し、必要なら故障注入で残すテストが同じ失敗を検出できることを確認する。

テスト件数、行数、実行時間の削減自体をgoalにしない。`skip`、`todo`、retry、timeout緩和、coverage除外、弱いsnapshotへの置換でgreenや短縮を作らない。

## 6. 依存順の実装batchを進める

goalの依存順と排他的write scopeを守って実装する。implementation batchの配列順を実行順とし、依存goalは必ず後続goalより前のbatchで完了させる。同じbatch内の暗黙順序で依存を満たしたことにしない。独立goalは別batchにできるが、初回独立reviewは全採用goalの実装完了後まで開始しない。

workerへ委譲できるのは、判断が完全に固定済みで、独立または先行依存が完了済み、localで可逆、排他的write scope、strong oracle、分担利益ありをすべて満たすleafだけである。mainは未解決判断、共有状態、統合、採否、独立reviewを所有する。

各goalの完了時にmainがdiff、write scope、focused検証、behavior oracleを確認する。未完了goalを推測で完了扱いしない。この確認で新しい監査roundを開始しない。

## 7. 性能Gateを必要時だけ通す

性能改善を主張する場合、またはrender、canvas、list、scheduler、queue、resource lifecycleなどhot pathを変更する場合だけ計測する。before／afterは同じhost、data、操作、build mode、sample条件で比較し、中央値と幅を残す。

実装前にmetric、workload、sample方法、baselineの変動幅、合格閾値を凍結する。保守性目的のhot-path変更はbaseline変動を越える悪化がないこと、性能改善goalはそれに加えて主張する改善閾値を満たすことを合格条件にする。閾値はprojectのriskとbaselineから決め、測定後に緩めない。

差が測定変動内なら性能改善を主張しない。結果が`fail`なら修正するか原因変更を不採用にし、goalを完了扱いしない。計測用codeやartifactをproductionへ残さない。

## 8. 初回独立reviewを一度だけ行う

凍結したscope、全goal、実差分、維持するcontract、対象外を一時Review Inputへ固定する。実装者とは別のreviewerが全適用観点を一巡し、候補探索が完了するまで修正指示を確定しない。

候補を次へ分類し、同じ根本原因を統合した一つの指示と`GO`、`NO_GO`または`HOLD`を返す。

- `fix_here`: 現在のscopeとcontract内で修正する。
- `later_gate`: 現在のGateでは扱わないが、明確なownerと後続Gateがある。
- `contract_decision`: 製品contractの判断が必要。現在のrunをHOLDする。
- `non_applicable`: 到達不能、根拠不足、対象外。

一件のblockerでreviewを止めない。全観点を一巡してから結果を一度に返す。

## 9. 一括修正と差分再reviewを行う

`fix_here`があれば、そのreviewと一度の回復確認で出た全件を一つのcorrection batchで修正する。correction batchにはsource review、対象candidate、実diffの因果経路が届くaffected dimension、`planned`／`verified`／`reverted`の状態を記録する。完了済みcorrectionは、必ず後続のincremental reviewで全affected dimensionを確認してから`GO`またはreview済み`HOLD`にする。再reviewでは次の二集合を明示する。

- `reopened`: 既報findingと修正の因果経路が届く観点。review対象correctionの全affected dimensionを含める。
- `carried`: contract、surface、因果経路が変わらず、以前の直接根拠と状態を再利用する観点。

両集合は重複せず、合わせて初回の全観点を覆う。再reviewは`reopened`だけを実査し、`carried`は引継ぎ根拠を確認する。carry-forwardは`成立`を意味せず、既知の違反、未解決candidate、HOLD理由を含む以前の状態もそのまま引き継ぐ。未解決問題をcarryしても完了条件は満たさない。

review candidateには`initial`、`regression`、`preexisting_miss`のoriginを記録する。修正前から存在した別問題を見つけた場合は`preexisting_miss`として初回reviewの見逃しにする。探索不足が「既存観点の深さ」か「観点選定」かを特定し、そのcandidateを修正する前に、同じ不足から残り得る問題を一度だけrecovery cycleで確認する。検出元incremental reviewとrecoveryの全`fix_here`を次のcorrection batchへまとめる。recoveryを省略して直接修正・完了しない。recovery後に別の`preexisting_miss`が出た場合は再回復や全面監査をせずHOLDする。

修正由来の回帰は`regression`として、影響する観点を開いて解消するまで確認する。correction由来ならそのbatchを修正するか、変更を取り除いて`reverted`にする。goal実装由来で安全に解消できなければ、原因となるrefactorを取り除き、goalを`rejected`、runをHOLDにする。rejection reason、元の挙動へ戻したrestoration oracle、resolved regressionを記録する。別のHOLD理由があっても回帰を作業treeへ残さない。

Gateの判定質問、現在contract、対象surface、利用側までの因果経路、独立観点集合のいずれかが変わった場合はincremental reviewを続けない。現在のrunをHOLDし、Scope Gateから新しいrunとして再判断する。

## 10. 完了判定と報告

次をすべて満たしたときだけ完了する。

- 凍結した全goalがverifiedで、未処理またはrejectedのgoalがない。回帰の原因となるrefactor変更を不採用にしてgoalを完了できない場合はHOLDする。
- 未解決P0／P1／P2と判定に必要な未確認がない。
- 全`fix_here`がverified correction batchで解消している。
- 全completed correctionが後続incremental reviewで確認済みである。
- 最新reviewが`GO`である。
- 製品挙動、禁止scope、外部状態が変わっていない。
- focused検証、全体検証、必要な性能計測が成功している。

最終報告には、固定scope、採用goal、変更path、対象外、検証結果、review decision、残るfollow-upだけを書く。一時manifest、case台帳、review履歴、実行識別子を永続成果物へ転記しない。
