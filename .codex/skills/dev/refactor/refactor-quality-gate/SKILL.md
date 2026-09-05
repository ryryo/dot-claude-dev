---
name: refactor-quality-gate
description: "製品挙動を変えない中〜大規模refactorで、scope固定、architecture／front-end専門スキルによる独立read-only監査、finding採否、goal freeze、依存順実装、性能確認、最終reviewを統合する。単一修正、機能追加、review-only、一般的hardeningには使わない。"
---

# Refactor Quality Gate

このスキルは専門監査を再実装しない。固定scopeに対して別エージェントが元のarchitecture／front-endスキルを直接使い、main Codexが結果の採否、goal統合、実装、最終判定を担当する。

標準進行:

`scope固定 → 専門監査を並行実行 → finding統合 → goal freeze → 依存順実装 → 独立review → 必要な修正 → 変更影響review`

## 責務境界

- 本スキル: scope、製品contract、禁止範囲、監査分担、finding採否、goal、実装順、検証、性能Gate、最終統合を所有する。
- architecture監査: [architecture-refactor-loop](../architecture-refactor-loop/SKILL.md)の`Read-only audit mode`をfreshな別エージェントが使う。
- front-end監査: [front-end-refactor-loop](../front-end-refactor-loop/SKILL.md)の`Read-only audit mode`を別のfreshなエージェントが使う。
- test portfolio: main Codexが公開挙動と失敗原因を基準に確認し、テスト数や行数をgoalにしない。
- 最終review: 実装者とは別のreviewerが[review-gate](../../review-gate/SKILL.md)を使う。

監査エージェントはread-onlyであり、findingの採否、goal化、実装、完了判定をしない。main Codexは監査結果をそのまま採用せず、現在の到達経路、製品contract、変更可能範囲で反証する。

## 適用条件と禁止事項

次をすべて満たす場合だけ使う。

- 複数module、state owner、resource lifecycle、React境界、性能、test portfolioのうち複数観点を横断する。
- 現在の製品contract、対象surface、検証oracle、write禁止範囲を固定できる。
- P1／P2を根本原因単位の独立したgoalへ分けられる。

UI、アクセシビリティ、公開API、保存形式、URL、event順、error semantics、外部作用を意図的に変えない。製品成果の変更が必要ならP0またはcontract decisionとして止め、Story／製品ownerへ返す。package、lockfile、toolchain、framework、dependencyをrefactorの都合で変えない。

既存の未コミット差分を最初に確認し、利用者または別writerの変更を戻さない。外部状態、version control、PR、merge、deployは利用者が明示的に許可した範囲だけで行う。

## 一時記録

本スキル自身の進行記録が必要なら`/tmp/refactor-quality-<project>.md`を一つだけ使い、次だけを短く記録する。

- scope、contract、禁止範囲、既存差分
- 各専門監査の対象と結果
- 採用／却下／deferした根本原因
- goalのowner、write scope、依存、oracle、状態
- 実装batch、検証、性能結果、review判定

本スキル独自のmanifest、schema、validator、case台帳は作らない。直接参照する専門スキルまたは`review-gate`が自身の契約で必須とするtask-local成果物は、そのスキルの責務として許可する。branch、commit、worktree、port、sessionなどの実行識別子をPLAN、Story、EVIDENCEへ保存しない。

## 1. Scopeを固定する

production変更前に次を決める。

- entry pointから利用側までのproduction surfaceと明示的なexcluded範囲
- canonical state、主要データフロー、副作用／resource owner、公開contract
- 現在の未コミット差分と保護境界
- focused test、全体test、typecheck、build、必要な実Journey
- write許可／禁止scope、外部副作用、停止条件
- 性能に触れる可能性があるhot pathと既存fixture

scopeまたはcontractが曖昧なまま監査や実装へ進まない。

## 2. 専門監査を別エージェントへ渡す

architectureとfront-endの両方が適用される場合、別々のfreshなread-onlyエージェントへ可能なら並行して渡す。同じエージェントに両観点をまとめず、main Codex自身の事前結論や疑っている修正案を答えとして渡さない。

各依頼に含めるもの:

- repositoryの絶対path、固定scope、contract、excluded範囲
- `git status --short`で許容する既存差分
- 対応する元スキルと`Read-only audit mode`を直接使う指示
- 編集、テスト実行、進捗file、commit／pushを禁止するread-only制約
- 現在の実装と差分をfreshに読むこと
- evidence付きfinding、却下／defer、既に直っている問題を分ける出力契約

別エージェントが利用できない場合、main Codexの自己監査だけで専門監査完了を名乗らない。利用できない観点を未確認として報告し、続行可否を判断する。

main Codexは別にtest portfolioを確認する。削除／統合候補は、同じ公開入口、同じ観測結果、同じ失敗原因を重ねて守るもの、到達不能な旧経路、内部実装だけを固定するものに限る。異なるstate transition、failure、retry、cleanup、event順、resource ownership、auth／client分離は統合しない。

## 3. Findingを統合してGoal Freezeする

両監査とtest portfolioの候補を一巡してから、同じ根本原因を統合する。

- P0: 現在の製品contractまたは外部作用を破る。実装せずHOLDする。
- P1: 挙動を維持したまま解消すべき重大な構造リスク。
- P2: 挙動を維持したまま解消する根拠のある保守性問題。
- P3／non-applicable: 好み、行数だけの分割、到達不能、根拠不足。実装しない。

各P1／P2 goalに、守るcontract、main／worker owner、狭く排他的なwrite scope、禁止scope、依存順、behavior oracle、focused／全体検証、必要な性能計測を固定する。新しい機能、UI、dependencyを解決策にしない。

## 4. 依存順に実装する

goalごとに必要なcharacterization testを先に置き、依存順に小さなbatchで実装する。main Codexはshared contract、state owner、resource lifecycle、routing、integration判断を持つ。別workerへ渡せるのは、判断が固定済みで独立し、write scopeが狭く、localで可逆、strong oracleがあるleafだけである。

各batch後にmain Codexがdiff、write scope、behavior oracle、focused検証を確認する。これは実装上の安全確認であり、新しい監査や最終reviewではない。

## 5. 性能Gate

render、context、canvas、list、scheduler、queue、serialization、resource lifecycle、bundle境界を変えるgoalは、実装前にmetric、workload、sample方法、baselineの幅、合格条件を固定する。同じhost、fixture、操作、build modeでbefore／afterを測る。

保守性目的ならbaseline変動を越えて悪化しないことを必須にする。性能改善を主張する場合だけ、追加の改善閾値を置く。計測差分が変動内なら改善を主張せず、計測用codeやartifactをproductionへ残さない。

## 6. 独立reviewと修正

全goalの実装と必要な性能確認後、固定scope、全goal、実diff、維持するcontract、対象外、検証結果をfreshな別reviewerへ渡し、`review-gate`で全適用観点を一度にreviewする。

`fix_here`は根本原因単位にまとめて修正し、既報findingと修正差分が届く観点だけを再reviewする。contract、surface、因果経路、観点集合が変わった場合は差分reviewを続けずscopeを再固定する。修正前からの見逃しが判明した場合は、同じ探索不足が残した候補を一度だけfreshな専門監査で回復確認する。再び見逃しが出たら自動loopせずHOLDする。

## 完了条件

- 全専門観点を別エージェントがread-onlyで確認し、main Codexが採否を終えている。
- 全P1／P2 goalと必要なcorrectionが検証済みで、未解決P0／P1／P2がない。
- 製品挙動、禁止scope、外部状態を変えていない。
- focused／全体検証、必要な性能計測が成功している。
- 最新の独立`review-gate`がGOである。

最終報告は、固定scope、採用goal、変更path、対象外、検証、性能結果、review判定、残るfollow-upだけにする。
