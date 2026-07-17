---
name: simple-plan
description: |
  repositoryを調査し、`docs/PLAN/YYMMDD_{slug}.md` にPhase・完了状態・Gate・チェック項目・実行ルールを持つ自己完結した永続計画を作成または再構成する。Use when the user asks for simple-plan、チェックリスト式の計画、複数停止点を持つ中規模作業、段階的なapp分割やlocal migration、production前Gate、または既存planの構成変更。単発Sprintでは収まらないが、全体の詳細task graphまでは不要な作業向け。既存planをそのまま実行・再開するだけの場合は使わない。
---

# Simple Plan

複数Phaseをまたぐ作業について、作成後はこのskillを再度使わなくても任意のagentが実行・再開できる永続planを作る。このskillの責務はplanの新規作成または構造変更と検査までであり、planの実行やcheckbox更新は行わない。

## 適用範囲

このskillは`cursor-agent-sprint-cli`以上、詳細な`cursor-agent-delegate`以下の粒度を担う。2つ以上の成果段階、停止点、再開点のいずれかを持ち、Phaseの直列順序とGateで管理できる中規模作業に使う。

- 単発Sprintで完結する局所実装には`cursor-agent-sprint-cli`を直接使う。
- 全Phaseのowner、model、file単位の競合、integration batchを事前設計しなければ実行不能な作業には、より詳細な委任計画を使う。
- 既存planをそのまま実行または再開する場合は、そのplanを直接読む。このskillを経由しない。
- goal、scope、Phase境界、Gate、完了条件を変更する場合は、このskillでplanを再構成する。

## 1. Repositoryを調査する

planを書く前に、判断に必要な範囲を読む。

1. 適用される`AGENTS.md`とrepository固有の指示を読む。
2. `git status --short`で既存変更を確認する。
3. 依頼に関係するsource、config、docs、既存test、現行commandを読む。
4. 現在の振る舞い、変更対象、変更しない範囲、外部stateを変える操作を確認する。
5. 実行可能な検証commandと、ユーザーまたは呼び出し元から観測できるacceptanceを決める。

コードから確認できることをユーザーへ質問しない。goal、scope、acceptanceを変える未解決の選択だけを確認する。

## 2. Planを設計する

### PhaseとGate

`## 進捗`を`### Phase A: ...`形式の有用な中間状態で分ける。各Phaseを上から読むだけで実行できるよう、次を同じPhase内に含める。checkboxは入れ子にしない。

- **開始条件**: 先行Gate、必要な入力、外部承認など、着手可能と判定できる状態。
- **完了状態**: Phaseを終えたと外部から判定できる1文。
- **実行方針**: main agentが直接実行するか、Cursor候補をどの条件で使うか、誰が統合・検収するか。
- **進捗項目**: 通常2から5件程度のflatな`- [ ]`。依存順に並べる。
- **Gate**: 次Phaseの入力、ユーザー判断、外部state変更、またはCursor再判定が必要な位置に置く。

Phaseは「移設後appが単独buildできる」などの成立状態で区切る。「ファイルを移動する」「構造を整える」だけをPhaseの成果にしない。

### 進捗項目の粒度

1項目には主な成果、write scopeまたは責務surface、具体的な検証結果をそれぞれ1つ持たせる。次に該当する場合は分割する。

- route、content、shared UI、config、testなど複数surfaceを同時に含む。
- 「一式」「構造を整える」「必要な対応をする」だけで成果物を特定できない。
- 一部だけ成功する状態が自然に発生する。
- Cursor taskへ分けると複数の独立write scopeになる。

検証は進捗項目またはPhase末尾のGateへ明記する。IDは依存と再開位置を判別できるよう付ける。

### Phase内の実行方針

実行方針は独立したplan-wide sectionへ分離せず、対象Phaseの開始条件と完了状態の直後へ置く。main agentが直接実行するPhaseは1文で明示する。Cursor候補があるPhaseだけ、開始条件、候補scope、main担当、main検収条件、判断結果の記録先を書く。

shared contract、schema、routing、migration方針、production操作、統合、最終検証、完了判断はmain agentに残す。次をすべて満たすleaf taskが見込めるPhaseだけをCursor候補にする。

- goal、read scope、write scope、禁止範囲、acceptance、検証方法を実行時に具体化できる。
- shared contractや重要な設計判断を含まない。
- 他taskとwrite scopeやUI surfaceが重ならない。
- 委任準備、diff review、再検証を含めても速度またはcontext分離の実益がある。

まだ存在しないscaffold、未確定contract、生成pathに依存する分割は確定しない。その直前のPhase末尾にCursor再判定Gateを置き、判断対象の次Phaseに実行方針を書く。Gate到達時に判断結果とSprint pathを次Phaseの実行方針へ記録し、Cursorを使う場合だけ`cursor-agent-sprint-cli`を読んで現在Sprintを`.codex/tmp/`へ詳細化する。worker task graphや未確定file pathは永続planへ書かない。

`## Cursor委任計画`のような横断sectionは作らない。Phaseの実行に必要なowner、委任条件、検収条件をPhase外へ分散させない。

## 3. Planを作成・再構成する

新規planはworkspace rootの`docs/PLAN/YYMMDD_{lowercase_snake_case}.md`へ作る。同名fileがある場合は上書きせず、具体的なslugまたは連番を使う。

1. `assets/plan-template.md`を読む。
2. `docs/PLAN/`がなければ作成する。
3. `apply_patch`でplanを作成し、未編集templateをそのままcopyしない。
4. タイトル、目的、前提・対象範囲、実行ルール、Phase化した進捗、全体完了条件を今回の内容で埋める。
5. 不要な例、placeholder、空sectionを削除する。
6. ユーザーの使用言語で書く。

既存planの構造変更では、そのfileを唯一のsource of truthとして更新する。repositoryの実状態とcheckboxを照合し、有効なdecision、完了記録、検証結果を保つ。未完了項目を構造変更だけで完了扱いにせず、ユーザーの変更を巻き戻さない。

## 4. Planを検査する

作成後に全文を読み直し、次を確認する。

- plan単体で開始位置、実行順序、進捗更新、Gate停止、Cursor再判定、失敗記録を判断できる。
- 目的と完了条件が観測可能な振る舞いを示している。
- 対象、変更しない範囲、外部操作前の停止点が明記されている。
- 各Phaseに開始条件、完了状態、実行方針、依存順のflatな進捗項目、必要なGateがある。
- 現在Phaseの外を参照しなくても、担当、Cursor使用条件、統合・検収責任を判断できる。
- 各項目が単一成果、主なscope、具体的な検証方法を持つ。
- 検証commandが実行可能な形で記載されている。
- Cursor候補は対象Phaseの実行方針にだけ記載され、独立したCursor委任section、未確定path、worker task graphがない。
- placeholder、空section、旧式のworker/model実行注釈が残っていない。
- 既存の未コミット変更を上書きまたは巻き戻す内容になっていない。

最後にplan path、Phase、Gate、Cursor再判定位置を報告して終了する。実装、deploy、checkbox更新は開始しない。
