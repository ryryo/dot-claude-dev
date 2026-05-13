---
name: dev:spec-codex
description: |
  Codex Plan Mode で docs/PLAN/{YYMMDD}_{slug}/ の schema v3 仕様書を作成します。
  Gate 契約、Mermaid 図、Cursor Agent 委任ヒント、Codex 実行互換の
  v3 optional 拡張を含めます。

  Trigger:
  spec-codex, 仕様書を作成, 実装計画, 実装仕様, docs/PLAN 作成
user-invocable: true
---

# spec-codex

Codex Plan Mode 専用で、実装エージェントに委任できる schema v3 仕様書を作成する。`Goal / Constraints / Acceptance Criteria` を Gate 契約として定義し、Codex で扱うための図選択、Cursor Agent 委任、review/run 互換情報を含める。

## ゴール

**「Codex を有能なエンジニアとして委任できる」契約書としての仕様書**を作成する。

v3 の規律:

- 詳細な実装手順や `impl` は書かない。実装エージェントが Gate 契約に基づいて自律的に判断できるようにする。
- 各 Gate に `Goal / Constraints / Acceptance Criteria` を明示する。
- AC は「何が成立しているか」を検証可能な形で書く。
- Todo は粒度の合意、影響範囲、委任可否のヒントにとどめる。
- `tasks.json` を実行時の Single Source of Truth とし、`spec.md` は人間が全体像を把握するための文書にする。

## Plan Mode Gate

このスキルは Codex Plan Mode でのみ実行する。Plan Mode でない場合は、次だけを返して停止する。

```text
このスキルは Codex Plan Mode 専用です。Plan Mode に切り替えて spec-codex を再実行してください。
```

## Output

- `docs/PLAN/{YYMMDD}_{slug}/spec.md`: 人間が全体像を把握するための背景、決定事項、参照実装との差分、必要な Mermaid 図、generated タスクリスト。
- `docs/PLAN/{YYMMDD}_{slug}/tasks.json`: schema v3 を正とする Gate 契約。Codex 互換の optional 拡張を持てる。
- `docs/PLAN/{YYMMDD}_{slug}/references/`: 外部参照が必要な場合のみ同梱する。

## 実行手順

### Step 1: 対象タスクを確定する

成果物: PLAN identity

契約: [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Spec`

検収ゲート:

- `docs/PLAN/{YYMMDD}_{slug}/` の `{YYMMDD}` が `date +%y%m%d` の結果と一致している。
- `{slug}` が対象タスクを表し、既存 `docs/PLAN/{YYMMDD}_{slug}` と衝突していない。
- `tasks.json.spec` が契約の `Spec` を満たしている。

### Step 2: コンテキストを収集する

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/context.md`

契約: [templates/context-template.md](references/templates/context-template.md)

`context.md` の検収ゲート:

- `context.md` が契約の見出しと表構造を満たしている。
- `context.md` の `Project Rules`, `Relevant Files`, `External References`, `Commands`, `Excluded Assumptions` が後続の `spec.md`, `tasks.json`, `discovery.md` と矛盾していない。
- `tasks.json` の AC や review で使うコマンドが `context.md` の `Commands` に記録されている。

### Step 3: Discovery / Decision Sprint

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/discovery.md`

契約: [discovery-decision-sprint.md](references/discovery-decision-sprint.md)

`discovery.md` の検収ゲート:

- `discovery.md` が契約の `Required discovery.md Structure` を満たしている。
- Step 4 の `spec.md` 設計決定事項は、`discovery.md` の `### Decisions for spec.md` にある項目を反映している。
- Step 5 の Gate constraints / acceptanceCriteria は、`discovery.md` の `### Constraints for tasks.json` と `### Acceptance Criteria` にある項目を反映している。
- Step 7 の Preflight は、`discovery.md` の `### Preflight` にある項目と矛盾していない。
- `discovery.md` の `### Residual Risks` に、計画段階で解消できる不明点が残っていない。

### Step 4: authored spec.md を設計する

成果物: `docs/PLAN/{YYMMDD}_{slug}/spec.md`

契約:

- [templates/spec-template-dir.md](references/templates/spec-template-dir.md)
- [diagram-selector.md](references/diagram-selector.md)

`spec.md` の検収ゲート:

- `spec.md` が契約の見出し構成を満たしている。
- `## 背景` があり、`context.md` と `discovery.md` で確認した現状、問題、差分が反映されている。
- `## 設計決定事項` があり、`discovery.md` の `### Decisions for spec.md` にある決定が表で反映されている。
- `## アーキテクチャ詳細` の Mermaid 図が `diagram-selector.md` の選択基準と一致している。
- `## 変更対象ファイルと影響範囲` があり、`tasks.json.gates[].todos[].affectedFiles` と矛盾していない。
- `## 残存リスク` があり、`discovery.md` の `### Residual Risks` にある外部要因だけが反映されている。

### Step 5: Gate 契約を設計する

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `gates[]`

契約: [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Gate`

`gates[]` の検収ゲート:

- 各 Gate が契約の `Gate` を満たしている。
- `constraints.must` / `constraints.mustNot` が `discovery.md` の `### Constraints for tasks.json` を反映している。
- `acceptanceCriteria[]` が `discovery.md` の `### Acceptance Criteria` を反映している。
- AC が契約の `AcceptanceCriteria` を満たしている。
- Gate dependency graph に循環がない。
- `parallelizable: true` の Gate は affected file と状態所有が他 Gate と衝突しない。

### Step 6: Todo と委任ヒントを設計する

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `gates[].todos[]`

契約:

- [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Todo`
- [cursor-delegation-protocol.md](references/cursor-delegation-protocol.md)
- [delegation-brief-template.md](references/delegation-brief-template.md)

`todos[]` の検収ゲート:

- 各 Todo が契約の `Todo` を満たしている。
- `affectedFiles[]` が Step 4 の `## 変更対象ファイルと影響範囲` と矛盾していない。
- `tdd: true` の Todo は、対応する AC にテストまたは検証条件がある。
- `delegation.eligible: true` の Todo が delegation 契約を満たしている。

### Step 7: Preflight を抽出する

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `preflight[]` と `spec.md` の `## Preflight（環境セットアップ）`

契約:

- [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Preflight`
- [templates/spec-template-dir.md](references/templates/spec-template-dir.md) の `Preflight`

`preflight[]` の検収ゲート:

- `discovery.md` の `### Preflight` にある項目が反映されている。
- 各項目が契約の `Preflight` を満たしている。
- ローカル生成、test、build、sandbox 内で実行できる通常コマンドが含まれていない。
- `preflight[]` が空の場合、`spec.md` に `## Preflight（環境セットアップ）` がない。
- `preflight[]` が空でない場合、`spec.md` の `## Preflight（環境セットアップ）` に同じ項目 ID とタイトルがある。

### Step 8: ファイルを作成する

成果物:

- `docs/PLAN/{YYMMDD}_{slug}/spec.md`
- `docs/PLAN/{YYMMDD}_{slug}/tasks.json`
- `docs/PLAN/{YYMMDD}_{slug}/references/context.md`
- `docs/PLAN/{YYMMDD}_{slug}/references/discovery.md`

契約:

- [templates/context-template.md](references/templates/context-template.md)
- [discovery-decision-sprint.md](references/discovery-decision-sprint.md)
- [templates/spec-template-dir.md](references/templates/spec-template-dir.md)
- [templates/tasks.template.json](references/templates/tasks.template.json)
- [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md)
- [scripts/sync-spec-md.mjs](../spec-codex-run/scripts/sync-spec-md.mjs)

```bash
node .codex/skills/dev/spec-codex-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
```

ファイル作成の検収ゲート:

- `tasks.json` が JSON として parse できる。
- `tasks.json.schemaVersion === 3`。
- `tasks.json.spec.specPath === "spec.md"`。
- `spec.md` に generated markers がある。
- `spec.md` の generated 領域に `tasks.json.gates[]` の Gate が出力されている。
- `spec.md` の generated 依存関係図が `tasks.json.gates[].dependencies` と一致している。

### Step 9: レビューする

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/plan-review.md`

契約: [plan-reviewer.md](references/plan-reviewer.md)

`plan-review.md` の検収ゲート:

- `plan-review.md` が契約の `Report Format` を満たしている。
- 完了時の `plan-review.md` が `APPROVED` である。
- Critical / High の指摘が `spec.md`, `tasks.json`, `context.md`, `discovery.md` のいずれかに反映済みである。

### Step 10: 完了報告する

成果物: ユーザーへの完了報告

完了報告の検収ゲート:

- `spec.md`, `tasks.json`, `context.md`, `discovery.md`, `plan-review.md` のパスが含まれている。
- Gate 数が含まれている。
- 使用した Mermaid 図の種類が含まれている。
- Cursor 委任ヒントの有無が含まれている。
- 残存リスクがある場合、計画段階で解消不能な理由と対応する Gate / AC / Preflight が含まれている。

## 完了条件

- `docs/PLAN/{YYMMDD}_{slug}/spec.md` が存在する。
- `docs/PLAN/{YYMMDD}_{slug}/tasks.json` が存在する。
- `docs/PLAN/{YYMMDD}_{slug}/references/context.md` が存在する。
- `docs/PLAN/{YYMMDD}_{slug}/references/discovery.md` が存在する。
- `docs/PLAN/{YYMMDD}_{slug}/references/plan-review.md` が存在し、`PLAN REVIEW APPROVED` が記録されている。
- `tasks.json.schemaVersion === 3`。
- `spec.md` 冒頭に `Gate 0: 準備` がある。
- `spec.md` に `<!-- generated:begin -->` / `<!-- generated:end -->` がある。
- generated 領域が `tasks.json` と同期している。
- 全 Gate に `goal.what`, `goal.why`, `constraints.must`, `constraints.mustNot`, `acceptanceCriteria`, `todos`, `review`, `passed` がある。
- 全 AC が検証可能な状態記述になっている。
- Gate dependencies に存在しない ID や循環がない。
- Todo に `impl`、詳細な実装手順本文、`steps` がない。
- 必要な Mermaid 図だけが `spec.md` に入っている。
- Cursor Agent 委任ヒントがある場合、write scope、禁止事項、検証、報告形式を示せる情報がある。
- 外部参照は `references/` にコピーまたは要約されている。
- 計画段階で解消できる不明点が残存リスクに残っていない。
- [plan-reviewer.md](references/plan-reviewer.md) の Critical / High が解消されている。

## References

- [gpt-55-prompting.md](references/gpt-55-prompting.md)
- [discovery-decision-sprint.md](references/discovery-decision-sprint.md)
- [diagram-selector.md](references/diagram-selector.md)
- [cursor-delegation-protocol.md](references/cursor-delegation-protocol.md)
- [delegation-brief-template.md](references/delegation-brief-template.md)
- [templates/spec-template-dir.md](references/templates/spec-template-dir.md)
- [templates/tasks.template.json](references/templates/tasks.template.json)
- [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md)
- [plan-reviewer.md](references/plan-reviewer.md)
