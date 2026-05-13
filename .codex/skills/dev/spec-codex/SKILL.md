---
name: dev:spec-codex
description: |
  Codex Plan Mode 専用。docs/PLAN/{YYMMDD}_{slug}/ に schema v3 仕様書を作成する。
  Gate 契約 (Goal / Constraints / Acceptance Criteria)、Mermaid 図、Cursor Agent 委任ヒントを含む。

  Trigger:
  spec-codex, 仕様書を作成, 実装計画, 実装仕様, docs/PLAN 作成
context: fork
user-invocable: true
---

# spec-codex

Codex を有能なエンジニアとして委任できる契約書としての仕様書を作る。

## Plan Mode ガード

Plan Mode でない場合は次だけを返して停止する。

```
このスキルは Codex Plan Mode 専用です。Plan Mode に切り替えて spec-codex を再実行してください。
```

---

## 実行手順

### Step 1: 対象タスクを確定する

1. 会話から実装対象を読み取る。不明な場合は質問機能で確認する
2. `date +%y%m%d` で日付を取得する
3. slug 候補を 2〜3 案提示し、質問機能でユーザーに確定させる
4. `docs/PLAN/` を確認し、`{YYMMDD}_{slug}` が既存ディレクトリと衝突していないことを確かめる

成果物: 確定した `{YYMMDD}_{slug}`
完了: slug がユーザー確定済みで衝突がない

### Step 2: 作業ディレクトリを準備する

[init-plan.sh](scripts/init-plan.sh) を実行してディレクトリとテンプレートファイルをセットアップする。

```bash
bash .codex/skills/dev/spec-codex/scripts/init-plan.sh {YYMMDD}_{slug}
```

成果物: `docs/PLAN/{YYMMDD}_{slug}/` ディレクトリ + `references/context.md` / `tasks.json`
完了: スクリプトがエラーなく完了し、ディレクトリと各ファイルが存在する

### Step 3: コンテキストを収集する

この PLAN 固有の確認済み事実を記録する。プロジェクト全体のルールや構成は対象外。

1. この実装で触る特定ファイル・API・コマンドを Glob / Grep / Read で確認する
2. コードベース外の参照資料（外部 API ドキュメント等）があれば `references/` にコピーまたは要約する
3. Step 2 でコピーした `docs/PLAN/{YYMMDD}_{slug}/references/context.md` を編集して確認済み事実を記録する

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/context.md`（内容が埋まった状態）
完了: 後続 Step の根拠として使える状態になっている

### Step 4: 要件を深掘りする

1. [discovery-decision-sprint.md](references/discovery-decision-sprint.md) を Read し、Phase 1〜6 を順に実行する
2. Phase 3 の質問は Plan Mode の質問機能を使い、1 ラウンドあたり 2〜3 問でユーザーと対話する
3. Completeness Check が全て満たされたら `docs/PLAN/{YYMMDD}_{slug}/references/discovery.md` を Write する

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/discovery.md`
完了: Completeness Check が全て満たされ、計画段階で解消できる不明点が残存リスクに残っていない

### Step 5: spec.md authored 部を書く

1. [spec-template-dir.md](references/templates/spec-template-dir.md) を Read して構成を把握する
2. [diagram-selector.md](references/diagram-selector.md) を Read し、仕様の内容に応じた Mermaid 図の種類を選ぶ
3. `discovery.md` の `Gate Contract Inputs` を起点に、設計決定事項・アーキテクチャ詳細を `spec.md` に書く
4. generated 領域は `<!-- generated:begin -->` / `<!-- generated:end -->` markers だけ置く

成果物: `docs/PLAN/{YYMMDD}_{slug}/spec.md`（authored セクション）
完了: `discovery.md` の `Gate Contract Inputs` が設計決定事項とアーキテクチャ詳細に反映されている

### Step 6: Gate 契約を設計する

1. [tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Gate` セクションを Read し、必須フィールドを把握する
2. `discovery.md` の `Gate Contract Inputs`（Constraints / Acceptance Criteria）を起点に Gate を設計する
3. Step 2 でコピーした `tasks.json` の `gates[]` を編集して内容を埋める

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `gates[]`
完了: 全 Gate に `goal` / `constraints` / `acceptanceCriteria` が揃い、依存関係に循環がない

### Step 7: Todo と委任ヒントを設計する

1. [tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Todo` セクションを Read し、軽量フィールドの定義を確認する
2. Cursor Agent に委任できる Todo の判断基準は [cursor-delegation-protocol.md](references/cursor-delegation-protocol.md) を Read して確認する
3. `tasks.json` の `gates[].todos[]` を編集して各 Gate の Todo を設計し、委任候補に `delegation` ヒントを付ける

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `gates[].todos[]`
完了: 各 Todo が軽量フィールドのみを持ち、委任候補に `delegation` ヒントが付いている

### Step 8: Preflight を抽出する

1. [tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) の `Preflight` セクションを Read し、対象カテゴリ（network 必須 / global 書き込み / 対話ログイン）を確認する
2. `discovery.md` の `### Preflight` にある項目を起点に、対象カテゴリのみを抽出する
3. `tasks.json` の `preflight[]` を編集する。該当なければ `preflight: []` とし、`spec.md` の Preflight セクションを省略する

成果物: `docs/PLAN/{YYMMDD}_{slug}/tasks.json` の `preflight[]`
完了: network 必須・global 書き込み・対話ログインのみが Preflight に入っており、通常コマンドが混在していない

### Step 9: sync してレビューする

1. sync を実行して `spec.md` の generated 領域を `tasks.json` と一致させる

```bash
node .codex/skills/dev/spec-codex-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
```

2. [plan-reviewer.md](references/plan-reviewer.md) を Read し、全チェック項目に基づいて自己レビューする
3. 結果を `docs/PLAN/{YYMMDD}_{slug}/references/plan-review.md` に Write する
4. NEEDS_REVISION の場合は指摘箇所を修正し sync してから再レビューする（最大 2 回）

成果物: `docs/PLAN/{YYMMDD}_{slug}/references/plan-review.md`
完了: `tasks.json` が parse でき `schemaVersion === 3`。generated 領域が同期されている。`plan-review.md` が `PLAN REVIEW APPROVED`

### Step 10: 完了を報告する

作成したファイルパス、Gate 数、使用した Mermaid 図の種類、Cursor 委任ヒントの有無、残存リスクの有無を報告する。

---

## 完了条件

- `docs/PLAN/{YYMMDD}_{slug}/` 以下に `spec.md` / `tasks.json` / `references/context.md` / `references/discovery.md` / `references/plan-review.md` が存在する
- `tasks.json` の `schemaVersion === 3`
- 全 Gate に `goal` / `constraints` / `acceptanceCriteria` / `todos` / `review` / `passed` がある
- 全 AC が検証可能な状態記述になっている
- `spec.md` に `<!-- generated:begin -->` / `<!-- generated:end -->` があり generated 領域が同期されている
- `plan-review.md` が `APPROVED`

## References

各 Step の手順内でリンク先を Read することで参照される。

- [scripts/init-plan.sh](scripts/init-plan.sh) — Step 2（ディレクトリ初期化）
- [templates/context-template.md](references/templates/context-template.md) — init-plan.sh の cp 元
- [templates/tasks.template.json](references/templates/tasks.template.json) — init-plan.sh の cp 元
- [templates/spec-template-dir.md](references/templates/spec-template-dir.md) — Step 2 / 5
- [discovery-decision-sprint.md](references/discovery-decision-sprint.md) — Step 4
- [diagram-selector.md](references/diagram-selector.md) — Step 5
- [templates/tasks-schema-v3-codex.md](references/templates/tasks-schema-v3-codex.md) — Step 6 / 7 / 8
- [cursor-delegation-protocol.md](references/cursor-delegation-protocol.md) — Step 7
- [plan-reviewer.md](references/plan-reviewer.md) — Step 9
- [gpt-55-prompting.md](references/gpt-55-prompting.md) — このスキル自体の設計方針
- [delegation-brief-template.md](references/delegation-brief-template.md) — spec-codex-run の IMPL で使用
