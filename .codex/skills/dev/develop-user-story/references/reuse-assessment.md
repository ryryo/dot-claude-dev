# 既存資産・参照実装の再利用判定

適用指示、台帳、template、REFERENCE、dependency管理、現行実装が再利用候補を示す場合に読む。現在の利用者成果と検証基準を満たす最小単位を選ぶための資料であり、参照製品全体の監査は行わない。

## 候補を絞り、実sourceを読む

1. 利用者成果とoracleに対応するcapabilityを定める。REFERENCEや比較表は候補の入口とし、要約だけで採否を決めない。
2. 同一repository内は現行path、baseline、owner、公開契約、テストを確認する。外部候補はprovenanceの固定revision／解決済みversionをmaterializeし、一致を確認する。
3. 存在する範囲で`primitive／domain → consumer／adapter → route／UI／job等の統合点 → behavior test`を辿る。存在しない層は探索範囲と結果を示す。適用先が求める修正履歴も対象capabilityに絞って確認する。

hidden directoryは明示pathまたは`rg --hidden`で探索する。通常検索の不一致や未初期化gitlinkを「実装が存在しない」根拠にしない。

sourceを読む前に除外できるのは、license非互換、runtime不適合、対象capabilityがないなど、sourceの可用性とは独立した根拠がある場合だけである。その理由は採用し得る最小module／patternへ適用する。製品全体や巨大engineが不適合でも、portableな部分まで同じ理由で除外しない。

必要な外部sourceを取得・展開できなければ、その採否と依存する実装方式の確定を止める。要約だけで採用したり、調査を避けるため再実装へ切り替えたりしない。依存しない調査は進めてよい。

## 採用単位と接続方法を決める

同一repository内再利用、固定dependency、無改変／改変snapshot copy、契約・algorithmを参照した再実装、不採用から、適用できる方式を比較する。広いdependencyを避ける判断と、狭いmodule／patternの部分移植を避ける判断を混同しない。

PLANまたはその参照先へ、確認した事実と採否を記録する。

| 記録 | 内容 |
| --- | --- |
| 所在 | 同一repository内は現行path・baseline・owner・公開契約。外部はprovenance記録とmaterializeしたsourceのpath |
| 確認範囲 | consumer、統合点、test。存在しない場合は探索範囲と結果 |
| 採用境界 | 最小採用単位、現在契約への接続差分、持ち込まない依存・状態・機能 |
| 合否 | 回帰oracle、parity／negative oracle、方式の選定理由 |

外部sourceのrevision／version、license、provenance自体はREFERENCE、EVIDENCE、noticeまたはdependency管理を正本とし、PLANは参照する。実行時のbranch等の識別子は記録しない。

## 実装開始と前提変更時に再確認する

最初のコード・テスト編集前に、採用済みまたは実装根拠に使う候補のsource、版、公開契約、記録したconsumer／testを現在contextで一度照合する。不在と記録した層はその探索範囲と適用先のoracleを確認する。不採用候補は除外根拠が変わった場合だけ再確認する。

通常のdefectごとに探索を繰り返さない。ただし実画面・実サービス・実メディアの結果が選定時のruntime等の前提を反証した場合、またはPLANにないclock、scheduler、queue、retry、resource lifecycle、serialization等を独自実装する必要が判明した場合は、次のpatch前に該当capabilityの採否へ戻る。

採用方式、source、採用単位、依存、license、実装・検証責務を意味的に変える場合はPLANを先に更新し、[PLAN独立レビューGate](plan-workflow.md#plan独立レビューgate)を影響範囲について再開する。

## 独立レビューで採否を照合する

PLAN reviewerは採用候補・利用側・testと、除外候補の根拠を独立に確認する。consumerがあるcapabilityは、oracleから利用側までの連鎖を少なくとも一本辿る。consumer／testが存在しない場合は、探索範囲・検索結果と適用先側のparity／negative oracleを照合する。存在しないことが確認でき、適用先の合否を定められるなら、それだけで未確認にはしない。

必要なsourceが未materialize、存在すると記録されたconsumer／testが読めない、または広い不適合理由で狭い候補を落としている場合は採否の根拠不足として返す。作成者の要約や結論を再確認の代わりにしない。
