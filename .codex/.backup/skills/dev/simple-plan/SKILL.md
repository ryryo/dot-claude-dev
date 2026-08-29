---
name: simple-plan
description: |
  repositoryを調査し、`docs/PLAN/YYMMDD_{slug}.md` にPhase、Gate、完了状態、実行ルール、チェック項目を持つ自己完結した永続計画を作成または再構成する。Use when the user asks for simple-plan、チェックリスト式の計画、複数停止点を持つ中規模作業、段階的なapp分割やlocal migration、production前Gate、または既存planの構成変更。単発Sprintでは収まらないが、詳細なworker委任計画までは不要な作業向け。既存planをそのまま実行・再開するだけの場合は使わない。
---

# Simple Plan

作成後は、このskillを再度読まなくても任意のagentが実行・再開できるplanを書く。

このskillの責務はplanの作成または構造変更まで。実装、deploy、checkbox更新は始めない。

## 役割

`simple-plan` は、単発の `cursor-agent-sprint-cli` より大きく、詳細な `cursor-agent-delegate` より軽い作業を扱う。

使う目安:

- 成果段階が2つ以上ある。
- ユーザー判断、外部state変更、production操作などの停止点がある。
- Phaseごとの完了状態を確認しながら直列に進めたい。

使わない目安:

- 1回の局所Sprintで終わる作業。
- 既存planをそのまま実行または再開するだけの作業。
- 全workerのfile単位owner、model、統合batchまで先に設計しないと危ない作業。

## 手順

### Step 1: 必要な事実を読む

planを書く前に、判断に使う情報だけを読む。

1. 適用される `AGENTS.md` とrepository固有の指示を読む。
2. `git status --short` で既存変更を確認する。
3. 依頼に関係するsource、config、docs、test、commandを読む。
4. 変更する範囲、変更しない範囲、外部stateを変える操作を分ける。
5. 実行可能な検証commandと、ユーザーから見える完了条件を決める。
6. 実装を含むplanでは `cursor-agent-sprint-cli/SKILL.md` を完全に読む。

コードから分かることをユーザーへ質問しない。goal、scope、acceptanceが変わる未解決の選択だけを確認する。

### Step 2: Phase境界を決める

`## 進捗` を `### Phase A: ...` 形式で分ける。Phase名は作業名ではなく、成立する中間状態で書く。

よい境界:

- `studio appが単独でtypecheckできる`
- `bootstrap deployのdry-runまで確認できる`
- `正式公開前のDNSとrouting判断が記録されている`

弱い境界:

- `ファイルを移動する`
- `構造を整える`
- `必要な対応をする`

各Phaseには必ず次を書く。

- `開始条件`: 着手してよい状態。
- `完了状態`: 外部から終わったと分かる状態。
- `実行方針`: 担当境界、Cursor使用有無、Gateで見直す条件。
- flatな `- [ ]` 項目: 通常2から5件。入れ子にしない。
- 必要なGate: 次Phaseへ進む前に止まる条件。

### Step 3: Cursor作業をcheckboxへ落とす

各PhaseでCursorを使うかはplan作成時点で決める。

使わないPhaseは1行でよい。

```markdown
実行方針: Cursorは使わない。理由: <main Codexが直接扱う判断、統合、外部操作など>
```

使うPhaseでは、`実行方針` に責務境界を書き、進捗項目へownerを付ける。

```markdown
実行方針: Cursorを使う。main Codexは<contract / integration / review>を担当し、Cursorは<分離できるleaf scope>だけを担当する。

- [ ] B1 [main]: `cursor-agent-sprint-cli`を起動し、B2-B3を`.codex/tmp/`のSprintへ分解して実行する。Sprint pathとworker結果をこの項目へ記録する。
- [ ] B2 [cursor-sprint]: <単一成果、read/write scope、禁止範囲、acceptance、worker検証>
- [ ] B3 [cursor-sprint]: <単一成果、read/write scope、禁止範囲、acceptance、worker検証>
- [ ] B4 [main]: Cursor diffをreviewし、scope外変更がないことを確認してmain検証commandを実行する。
```

`[cursor-sprint]` itemを置いたPhaseでは、必ずその前に `[main]` の起動itemを置く。これにより、実行agentが上から未完了checkboxを進めれば `cursor-agent-sprint-cli` が発動する。

Gateは初回判断の代わりにしない。Gateは、plan作成後にscopeや実fileが変わった場合に、対象Phaseのcheckboxを書き換える場所である。Cursorの扱いを候補や未決定のまま残さない。

### Step 4: Cursorへ渡せるscopeを絞る

Cursorへ任せてよいのは、次を満たすleaf taskだけ。

- goal、read scope、write scope、禁止範囲、acceptance、検証方法を具体化できる。
- shared contractや重要な設計判断を含まない。
- 他taskとwrite scopeやUI surfaceが重ならない。
- main Codexがdiff reviewと再検証をできる。

shared contract、schema、routing、migration方針、production操作、統合、最終完了判断はmain Codexに残す。

### Step 5: Planを書く

新規planは workspace root の `docs/PLAN/YYMMDD_{lowercase_snake_case}.md` に作る。同名fileがある場合は上書きしない。

1. `assets/plan-template.md` を読む。
2. `docs/PLAN/` がなければ作る。
3. `apply_patch` でplanを作成または更新する。
4. 目的、前提、対象範囲、実行ルール、Phase、全体完了条件を今回の内容で埋める。
5. 不要な例、placeholder、空sectionを削除する。
6. ユーザーの使用言語で書く。

既存planを再構成する場合は、そのfileをsource of truthとして扱う。完了済みの事実、判断ログ、検証結果は保つ。未完了項目を構造変更だけで完了扱いにしない。

### Step 6: 読み直して直す

planを書いたら、完成扱いにする前に全文を読み直す。後からlintで直す前提にしない。

確認すること:

- 先頭から読むだけで、開始位置、実行順序、Gate停止、失敗時の記録先が分かる。
- 目的と完了条件が、観測できる振る舞いになっている。
- 各Phaseに開始条件、完了状態、実行方針、依存順のflatなcheckboxがある。
- Cursorを使わないPhaseは1行で理由が分かる。
- Cursorを使うPhaseは `[main]` の起動item、`[cursor-sprint]` item、`[main]` の検収itemが同じPhase内に並んでいる。
- `[cursor-sprint]` itemより前に、必ず `cursor-agent-sprint-cli` と `.codex/tmp/` を含む `[main]` itemがある。
- 各checkboxが単一成果、主なscope、具体的な検証結果を持つ。
- 実装に必要な指示が別sectionへ散らばっていない。
- 既存の未コミット変更を上書きまたは巻き戻す内容になっていない。

最後に、plan path、Phase一覧、Gate、Cursorを使うPhaseと起動itemを短く報告する。
