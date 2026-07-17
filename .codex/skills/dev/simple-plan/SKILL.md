---
name: simple-plan
description: |
  repositoryを調査し、`docs/PLAN/YYMMDD_{slug}.md` に軽量な永続計画を作成し、`- [ ]` / `- [x]` を進捗の正としてmain Codexが実行・更新する。独立して安全に分離できる作業だけを必要に応じて`cursor-agent-sprint-cli`へ委任する。Use when the user asks for simple-plan、チェックリスト式の計画、軽量な実装計画、複数の停止点を持つ作業の進捗管理、または既存`docs/PLAN`の再開・更新。永続計画が不要な即時sprintや、詳細なtask graph・複数worker・shared contract・migration・production barrierを事前設計する大規模作業には使わない。
---

# Simple Plan

次の順序で、調査、判断、plan作成、実行、進捗更新を行う。後のstepを先に実行せず、plan作成後はそのfileを進捗のsource of truthにする。

## Workflow

1. 開始状態を確定する。
2. repositoryを調査する。
3. 進捗項目とCursor sprintの使用有無を決める。
4. planを新規作成または再開する。
5. planを検査し、plan-onlyなら終了する。
6. 未完了項目を実行・検収・更新する。
7. 完了条件を確認して完了を報告する。

## Step 1: 開始状態を確定する

最初に次の3点を決める。

- **新規 / 再開**: ユーザーが既存plan pathを指定した場合は再開し、それ以外は新規作成する。
- **plan-only / execute**: 計画作成だけの依頼ならplan-only、実装や「この計画で進める」依頼ならexecuteとする。
- **write可否**: 現在のcollaboration modeがfile writeを禁止する場合はStep 3まで行い、decision-completeなplanを会話内に提示して止める。modeを回避してfileを作らない。

再開pathが指定された場合は存在を確認して全文を読む。存在しない場合は別planを作らず、正しいpathまたは復元が必要だと報告する。

## Step 2: repositoryを調査する

planを書く前に、判断に必要な範囲だけを読む。

1. 適用される`AGENTS.md`とrepository固有の指示を読む。
2. `git status --short`で既存変更を確認する。
3. 依頼に関係するsource、config、docs、既存testを読む。
4. 現在の振る舞い、変更対象、変更しない範囲を確認する。
5. 実行可能な検証commandと、ユーザーまたは呼び出し元から観測できるacceptanceを決める。

コードから確認できることをユーザーへ質問しない。goal、scope、acceptanceを変える未解決の選択だけを確認する。「目的」「前提・対象範囲」「完了条件」を書ける状態になってからStep 3へ進む。

## Step 3: 進捗と委任を設計する

### 3A. 進捗候補を作る

- 作業を、diffと検証結果で完了判定できる成果単位へ分ける。
- 実装操作の羅列ではなく、成立させる振る舞いを書く。
- 依存する項目を先、依存される項目を後へ並べる。
- 検証も必要な進捗項目として含める。
- phaseとtask IDは、依存や類似項目を区別する場合だけ使う。

### 3B. 各項目をmain実行またはCursor sprintへ分類する

main Codexでの直接実行をdefaultにする。次をすべて満たす項目だけCursor sprint候補にする。

- goal、read scope、write scope、禁止範囲、acceptance、検証方法を具体化できる。
- shared contractや重要な設計判断を含まないleaf taskである。
- main Codexの直近作業が結果待ちにならず、他の作業とwrite scopeが重ならない。
- 局所実装、機械的変更、分離したtest、範囲限定のdocs変更、独立した調査である。
- sprint準備、監視、diff review、再検証を含めても速度またはcontext分離の実益がある。

次はmain Codexに残す。

- 後続の設計や実装が結果に直ちに依存する項目
- 未確定の要件、contract、schema、auth、routing、migrationを決める項目
- write scope、contract、UI surfaceが他taskと重なる項目
- 委任準備と検収の方が重い小さな項目
- production操作、commit、push、PR、branch、統合、最終検証、完了判断

### 3C. Cursor sprintを使う場合だけsprint境界を決める

1. `cursor-agent-sprint-cli`の`SKILL.md`を完全に読む。
2. 複数taskまたはbarrierがある場合は、同skillの`references/large-plan-sprint-division.md`も読む。
3. 各sprintについて、goal、source item、依存・barrier、main-owned task、Cursor候補、禁止範囲、main acceptance、次contractを決める。
4. 「進捗」に「sprint分割を確定する」と「Sprint Sxを実行し、main Codexが検収する」を追加する。
5. worker内部taskは「進捗」へ展開しない。委任詳細は`.codex/tmp/`で管理する。

Cursor sprintを使わない場合は、sprint用の進捗項目と「委任計画」を作らない。

## Step 4: plan fileを作成または再開する

### 4A. 新規作成

workspace rootでpathを決める。

```bash
WORKSPACE="$(pwd)"
DATE="$(date +%y%m%d)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/simple-plan"
PLAN_DIR="$WORKSPACE/docs/PLAN"
SLUG="<lowercase_snake_case>"
PLAN_PATH="$PLAN_DIR/${DATE}_${SLUG}.md"
```

次の順序で作成する。

1. `assets/plan-template.md`が`$SKILL_DIR`に存在することを確認する。
2. `docs/PLAN/`がなければ作成する。
3. `PLAN_PATH`が既に存在しないことを確認する。存在する場合は上書きせず、より具体的なslugまたは連番を使う。
4. templateを読み、`apply_patch`で`PLAN_PATH`を新規作成する。未編集templateをそのままcopyしない。
5. 「タイトル」「目的」「前提・対象範囲」「進捗」「完了条件」の順に今回の内容へ置き換える。
6. Step 3でCursor sprintを使うと決めた場合だけ「委任計画」を埋める。確定済みの「sprint分割」項目は`[x]`、未実行sprintは`[ ]`で書く。
7. 使わないplaceholder、説明文、sprint項目、「委任計画」「補足」を見出しごと削除する。
8. ユーザーの使用言語で書く。

### 4B. 既存planを再開

1. 指定fileを唯一のsource of truthとして使い、新規planを作らない。
2. repositoryの実状態と既存checkboxを照合する。
3. 実態と異なるcheckboxは、根拠を確認してからmain Codexが修正する。
4. 新しく判明した必須task、acceptance、sprint境界だけを追記する。
5. 既存の有効なdecisionと完了記録を消さない。

## Step 5: planを実行可能か検査する

実行前にplanを読み直して確認する。

- 「目的」が実装後の観測可能な状態を示している。
- 「前提・対象範囲」に対象と変更しない範囲がある。
- すべての「進捗」項目が完了判定可能で、依存順に並んでいる。
- 「完了条件」に振る舞いベースのacceptanceと必要な検証commandがある。
- 「委任計画」を残した場合、各sprintのmain acceptanceとbarrierが明確である。
- placeholder、空section、旧式のworker/model実行注釈が残っていない。
- 既存の未コミット変更を上書きまたは巻き戻す計画になっていない。

plan-onlyの場合は、ここでplan pathと要点を報告して終了する。実装を開始しない。executeの場合だけStep 6へ進む。

## Step 6: 実行・検収・進捗更新を反復する

未完了項目がある間、次を1項目ずつ反復する。

1. planを読み、依存が解決済みの最初の`[ ]`項目を選ぶ。
2. main-ownedならmain Codexが実装または調査する。
3. sprint項目なら、「委任計画」の内容を入力として`cursor-agent-sprint-cli`を実行する。
4. 実際のdiff、scope、verificationをmain Codexが確認する。worker reportだけで受け入れない。
5. acceptanceを満たした場合だけ該当項目を`[x]`へ更新する。
6. 一部だけ完了した場合は、完了部分を`[x]`、残りを新しい`[ ]`へ分割する。
7. 失敗、範囲外変更、未検証がある場合は`[ ]`のままにし、必要な理由を短く「補足」または「委任計画」へ残す。
8. 次項目の前に、planだけで完了済み・残作業・barrier・次の検証が分かることを確認する。

workerにplan更新、完了判断、commit、push、PR、branch切替を任せない。planのcheckboxと完了判断はmain Codexだけが更新する。

## Step 7: 完了を判定して報告する

1. すべての必須の進捗項目が`[x]`、または理由付きでdeferredになっていることを確認する。
2. 「完了条件」を上から確認し、必要な最終検証をmain Codexが実行する。
3. scope外変更、未解決conflict、未通過barrierがないことを確認する。
4. 必要な場合だけ短い結果を「補足」へ追加する。
5. plan path、完了した成果、検証結果、未完了・deferred、修正または棄却した委任成果を簡潔に報告する。
