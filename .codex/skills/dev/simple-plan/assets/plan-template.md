# <作業内容を表すタイトル>

このファイルを実行計画と進捗の正とする。main Codexだけが進捗、Gate通過、完了判断を更新する。

## 目的

<実装後に誰が何をでき、どの振る舞いで確認できるか>

## 前提・対象範囲

- <リポジトリ上で確認した事実>
- <対象に含めるもの>
- <変更しないもの、守る制約>

## 実行ルール

- 作業開始時に、適用される`AGENTS.md`、このplan全文、`git status --short`を確認する。
- 最初の未完了Phaseを選び、そのPhaseの開始条件、完了状態、実行方針を読んでから着手する。
- 依存解決済みの最初の`[ ]`項目から実行する。
- diffと検証結果を確認できた項目だけを`[x]`へ更新する。一部だけ終わった項目は、完了部分と残作業へ分ける。
- Phase内の通常項目とGate条件が完了するまで、次Phaseへ進まない。
- ユーザー承認や外部state変更を含むGateは、明示確認を得るまで`[ ]`のままにする。
- Cursorを使うPhaseでは、`[main]` の起動item、`[cursor-sprint]` item、`[main]` の検収itemを同じPhase内に置く。Gateで取りやめる場合は、対象Phaseのcheckboxを書き換えて理由を記録する。
- Cursor workerにはplan更新、Gate通過、完了判断、commit、deployを任せない。main Codexがdiffを検収し、必要な検証を再実行する。
- 失敗、未検証、scope外変更、blockerは未完了のまま、該当Phaseまたは判断・結果ログへ事実と次の開始条件を記録する。

## 進捗

### Phase A: <最初の有用な中間状態>

開始条件: <このPhaseへ着手できる状態>

完了状態: <このPhaseを終えたと観測できる状態>

実行方針: Cursorは使わない。理由: <main Codexが直接扱うcontract、統合、外部操作など>

- [ ] A1 [main]: <単一の成果、主なscope、検証結果が分かる作業>
- [ ] A2 [main]: <次に成立させる成果>
- [ ] Gate A [main]: <次Phaseの開始条件を確認する。Phase BでCursorを取りやめる場合は、実fileに基づく理由をPhase Bへ記録し、対象checkboxを書き換える>

### Phase B: <次の有用な中間状態>

開始条件: <Gate Aなど、着手前に満たす条件>

完了状態: <このPhaseを終えたと観測できる状態>

実行方針: Cursorを使う。main Codexは<shared contract、統合、最終検証>を担当し、Cursorは<B2-B3の分離できるleaf scope>だけを担当する。

- [ ] B1 [main]: `cursor-agent-sprint-cli`を起動し、B2-B3を`.codex/tmp/`のSprintへ分解して実行する。Sprint pathとworker結果をこの項目へ記録する。
- [ ] B2 [cursor-sprint]: <単一成果、read/write scope、禁止範囲、acceptance、worker検証>
- [ ] B3 [cursor-sprint]: <単一成果、read/write scope、禁止範囲、acceptance、worker検証>
- [ ] B4 [main]: Cursor diffをreviewし、scope外変更がないことを確認してmain検証commandを実行する。

<必要なPhase数に合わせて追加し、不要な例は削除する。各Phaseへ開始条件、完了状態、実行方針を置き、checkboxは入れ子にしない。Cursorを使うPhaseでは `[main]` と `[cursor-sprint]` をitemへ付ける。>

## 全体完了条件

- <ユーザーまたは呼び出し元から観測できる完了条件>
- `<検証コマンド>`が成功し、<期待する結果>になる

## 判断・結果ログ

<Phase内に収まらない横断的な判断、発見事項、リスク、最終結果がある場合だけ残す。実行に必要な指示は該当Phaseへ書き、不要なら見出しごと削除する。>
