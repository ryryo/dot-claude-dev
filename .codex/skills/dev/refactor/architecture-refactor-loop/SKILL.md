---
name: architecture-refactor-loop
description: "責務・依存方向・状態や副作用の境界を監査し、既存挙動を保って段階的にリファクタリングする。read-only監査にも対応する。"
---

# architecture-refactor-loop

指定範囲の構造上の問題を見つけ、既存挙動を保ちながら、採用した改善と検証を完了する。main Codexが設計、採否、統合、レビュー、完了判定を持つ。Astra／Solの通常作業をworker向けの制限へ合わせない。

## Read-only audit mode

- リファクタリング依頼: 以下の調査・実装・検証を進める。
- 監査のみ、または`read-only audit mode`: [監査の契約](references/read-only-audit.md)を読み、findingを返して終了する。実装工程を起動しない。

## 守る契約

公開API、保存形式、schema、URL、イベント順、error semantics、外部副作用を維持する。既存の利用者差分を戻さない。外部状態、production data、secret、remote migration、課金や権限に関わる操作は、既存の明示許可範囲だけで行う。

各goalには具体的なarchitecture pain、変更可能範囲、受け入れ条件、検証方法が必要である。行数、命名、好みだけの整理をgoalにしない。

## 現状把握とDiscovery Gate

適用される指示、既存差分、対象の入口と利用側を確認する。README、build設定、実装、testは対象の契約と検証方法を把握するために必要なものを読む。

次を説明できるarchitecture mapを作る。対象に存在しない要素は非適用でよい。

- 実行入口と主要データフロー
- state ownerと副作用・resource境界
- public contract、module境界、依存方向
- test seamと実行時のリスク

責務境界、依存方向、state ownership、副作用、contract保護、test seam、実行時リスクを一巡する。最初のfindingだけで終えず、各観点のfindingまたは「なし／非適用」の根拠を短く残す。

| 重大度 | 判断 |
| --- | --- |
| P0 | 既存挙動、データ、安全性、build、releaseを壊す重大な問題 |
| P1 | 今後の変更を明確に危険または高コストにする主要な構造問題 |
| P2 | 分離・依存・検証性に問題があり、今回のscopeで直す根拠がある |
| P3 | 好みや軽微な整理。単独goalへ昇格させない |

findingにはpath、到達経路、問題となる責務または契約、最小修正境界、既存oracleを付ける。全観点の確認とP0／P1／P2の採否・defer理由が揃えばDiscovery Gateを通過する。findingやphaseの件数で深さを判定しない。

## 満足条件と計画

実装前に、解消するfinding、deferする理由、守る契約、必要な検証とレビューを完了条件として固定する。対象範囲を一巡した結果、採用goalが一つでもよい。無関係な改善を足してphase数を増やさない。

goalは依存関係と検収できる境界で分け、同じ検証で安全に扱える小変更はまとめる。検証基盤やcharacterization testは既存の保証が不足する場合だけ追加する。

複数goalや再開を管理する場合は[作業記録](references/work-record.md)を使う。既存PLANが同じ役割を担うなら再利用し、進捗を二重管理しない。単一の局所goalは会話内の契約と結果でよい。ユーザーが永続化を求めない限り一時記録を納品物へ加えない。

## 委譲

mainはarchitecture方針、依存方向、public contract、state ownership、migration、統合と採否を持つ。独立した監査、比較、差分レビューは、利用可能かつ許可されたCodex subagentへ任せてよい。

Cursor CLIへの委譲は任意とする。契約判断がなく、排他的なwrite scope、具体的なoracle、局所的なrollbackがあり、分担利益がある実装だけを候補にする。実際に委譲する場合に[Cursor CLI実行規約](../../cursor-agent-sprint-cli/SKILL.md)を読み、task契約・監視・検収を適用する。CLIが使えなければmainが続行する。通常のpreflightを追加しない。

実装前にownerを決め、委譲時は理由、read/write scope、禁止範囲、検収方法を記録する。使わないworkerの判定を複数箇所へ反復記録しない。依存やscopeが変わった場合だけ再判定する。Cursorへレビュー、採否、完了判定、Gitの状態変更やremote操作を任せない。

## 実装・検証・レビュー

1. goalの契約と依存を確認し、必要な安全網を揃えて実装する。
2. mainが実差分、write scope、既存差分の保護を確認する。
3. 変更が破り得る挙動に対応するfocused test、typecheck、lint、integration、build、実動作確認を選ぶ。repositoryが必須とするcheckは維持する。
4. Codex側で差分をレビューし、blocking findingを修正して影響する検証を再実行する。
5. 変更path、検証、レビュー結果、残リスクを記録する。

レビューでは、既存挙動、error semantics、依存方向と循環、責務境界、state・副作用owner、test seam、不要コードの削除根拠を確認する。performance、concurrency、resource lifecycleは変更が届く範囲で確認する。重要なgoalには許可されたread-onlyのfresh reviewを使えるが、mainが採否を決める。

許可済みのローカル修正と必要な検証は、最初の実装で止めず完了まで続ける。検証不能なら理由、代替確認、未確認事項を明記する。構造改善だけを理由に製品挙動を変えない。

## 再監査と完了

batch後は変更が届く境界を確認し、全goalの統合後に固定scopeの最終監査を一度行う。新しいP0／P1／P2は満足条件との関係で採否を決める。scope内で修正可能な問題は続行し、契約の変更や追加権限が必要な問題だけ利用者へ返す。

修正後は影響した観点を再確認する。前提が変わらない合格結果を引き継ぎ、新しい根拠なしに全体の探索や全テストを繰り返さない。

採用goalの実装・必要な検証・Codexレビューが完了し、未解決のblocking findingがなく、対象差分の確認とdefer理由の記録が揃ったら終了する。未コミットの今回差分は成果として残してよい。commit・pushは依頼された場合だけ行う。

最終報告には対象、満足条件への結果、主な設計判断と変更、委譲した場合の検収、検証結果、deferと未確認事項を短く示す。
