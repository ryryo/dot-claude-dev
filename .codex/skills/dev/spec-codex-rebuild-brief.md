# spec-codex / spec-codex-run Rebuild Brief

このブリーフは、別エージェントに `.codex/skills/dev/spec-codex` と `.codex/skills/dev/spec-codex-run` を 1 から作り直させるための指示である。

既存の `.codex/skills/dev/spec-codex-ex` と `.codex/skills/dev/spec-codex-run-ex` は、要求事項の抜け漏れ確認用の参照に限る。文章構造、表現、手順設計は引き継がない。

## 作成対象

- 新規作成: `.codex/skills/dev/spec-codex/`
- 新規作成または再作成: `.codex/skills/dev/spec-codex-run/`
- 既存参照:
  - `.claude/skills/dev/spec/`
  - `.claude/commands/dev/dig.md`
  - `.codex/skills/dev/spec-codex-ex/`
  - `.codex/skills/dev/spec-codex-run-ex/`
  - `.codex/skills/dev/parallel-agent-brief/`
  - `/Users/ryryo/dev/chrome_extension/docs/PLAN`
  - `/Users/ryryo/dev/lead-form/docs/SPEC`

## 最重要方針

スキル本文は、長い手順列挙や強制文でエージェントを制御しない。成果物、契約、検収条件、次工程との接続で作る。

良い構造:

- `SKILL.md` は実行フロー全体を把握できる短い本体にする。
- 詳細な作業契約は `references/` に置く。
- 各 Step は「成果物」「参照する契約」「検収ゲート」「次 Step への入力」を持つ。
- 外部 reference を読まないと成果物を満たせない構造にする。
- 「必ず読め」「絶対」「読まないと進むな」のような命令文で制御しない。

悪い構造:

- Step 本文に reference の要約を大量に書く。
- Step 本文だけ読めば作業できる。
- 「旧」「元」「相当」「〜を維持しつつ」など、作成経緯や思考過程がスキル本文に残る。
- 「残存リスクを報告する」で、計画段階で解ける不明点を棚上げできる。
- `SKILL.md` が reference の目次だけになり、何を作るかが分からない。

## spec-codex の要件

### Plan Mode

- Codex Plan Mode 専用。
- Plan Mode でない場合は、Plan Mode で再実行するよう返して停止する。
- Codex の質問機能を使う前提なので、Plan Mode 制約はスキルの入口条件にする。

### ゴール

`spec-codex` は、Codex を有能なエンジニアとして委任できる契約書としての仕様書を作る。

v3 の規律:

- 詳細な実装手順や `impl` は書かない。
- 各 Gate に `Goal / Constraints / Acceptance Criteria` を置く。
- AC は「結果として何が成立しているか」を検証可能に書く。
- Todo は粒度、影響範囲、委任可否のヒントに留める。
- `tasks.json` を実行時の Single Source of Truth にする。
- `spec.md` は人間が計画全体を理解する文書にする。

### 出力

`docs/PLAN/{YYMMDD}_{slug}/` に次を作る。

- `spec.md`
- `tasks.json`
- `references/context.md`
- `references/discovery.md`
- `references/plan-review.md`
- 必要な外部参照資料

`context.md`, `discovery.md`, `plan-review.md` は補助資料ではなく、後続成果物の根拠になる契約資料として扱う。

### Discovery / Decision Sprint

`.claude/commands/dev/dig.md` の深掘り工程を、別スキルとして呼ぶのではなく `spec-codex` 内に含める。

ただし `SKILL.md` に深掘り手順を要約しない。`references/discovery-decision-sprint.md` に契約を置き、Step 側は `references/discovery.md` の成果物ゲートだけを書く。

`references/discovery.md` の契約には少なくとも次を含める。

- Context Collection
- Assumption Map
- Interview Rounds
- Applied Findings
- Completeness Check
- Sprint Summary
- Gate Contract Inputs

重要:

- 高リスク前提を明示的に扱う。
- 主要トピックは必要に応じて2段階以上掘る。
- トレードオフ、障害モード、マイグレーション/ロールバック、保守性を扱う。
- 計画段階で解ける不明点を残存リスクへ置かない。
- 解消不能な外部要因だけを残存リスク候補にする。
- `Gate Contract Inputs` が後続の `spec.md` と `tasks.json` に接続される構造にする。

### context.md

`references/context.md` も成果物にする。

目的:

- PLAN が前提にする確認済み事実を記録する。
- 未確認の API、ファイル、コマンドを PLAN の前提から除外する。
- `spec.md`, `tasks.json`, `discovery.md` の根拠にする。

必要な構成例:

- Project Rules
- Relevant Files
- External References
- Commands
- Excluded Assumptions

### Mermaid

Mermaid は規模ではなく内容で選ぶ。

- UI導線、依存関係、処理構成: `flowchart` / `graph`
- API、外部連携、時系列処理: `sequenceDiagram`
- DB / 永続化モデル: `erDiagram`
- 状態遷移: `stateDiagram`
- Gate / work package 依存: `flowchart` / `graph`
- 期限や段階リリースが判断に必要な場合のみ: `gantt`

中規模なら graph + sequenceDiagram、大規模なら graph + sequenceDiagram + erDiagram + 必要なら gantt、のように固定しない。

### GPT-5.5 方針

公式 OpenAI prompt guidance を設計軸にする。

URL: `https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5`

反映すること:

- スキル本体は成果物、判断基準、完了条件を中心にする。
- 旧モデル向けの長い手順列挙をそのまま持ち込まない。
- ただし、出力される PLAN 自体は短くしない。実行と人間理解に必要な詳細は保持する。

### Cursor Agent 委任

Cursor Agent は使える場合だけ使う。ユーザーの契約状態やログイン状態が変わるので、毎回使用可否を選べる設計にする。

確認コマンドの候補:

```bash
cursor-agent about
cursor-agent models
cursor-agent -p --mode ask --output-format text --workspace <workspace> "Respond with exactly: ok"
```

基本形:

```bash
cursor-agent -p --mode ask --output-format text --workspace <workspace> --model <model> "<prompt>"
```

Cursor Agent に渡すプロンプトは、GPT-5.5 本体向けとは逆に詳細な作業契約にする。

Cursor 委任 brief に含めるもの:

- 作業場所
- 対象 Gate / Todo / AC
- 参照ファイル
- write scope
- 編集禁止範囲
- 検証コマンド
- 完了報告形式

Cursor Agent に渡してよい作業:

- 純粋関数
- validator
- formatter
- schema
- 単体テスト
- 小さな adapter
- 局所的な docs 調査
- write scope が明確で、他 Gate や共通 state に干渉しない作業

Cursor Agent に渡さない作業:

- `docs/PLAN` 更新
- `tasks.json` 更新
- `spec.md` generated 領域同期
- Gate PASS 判定
- 最終統合
- commit / push
- routing、共通 state、export pipeline、実ブラウザ最終検証など高結合作業

### schema v3 互換

`schemaVersion: 3` を維持する。dashboard 互換を壊さない。

既存必須フィールドの意味は変えない。追加は optional のみ。

optional 拡張例:

```json
{
  "extensions": {
    "codex": {
      "diagramPlan": [],
      "delegationPolicy": {
        "stateOwner": "main-codex",
        "cursorAgent": "ask-each-run",
        "defaultCursorModel": "composer-2-fast"
      }
    }
  }
}
```

`gates[]` optional:

```json
{
  "kind": "implementation | follow-up | review-fix | verification",
  "parallelizable": true
}
```

`todos[]` optional:

```json
{
  "delegation": {
    "eligible": true,
    "agent": "cursor-agent",
    "mode": "ask",
    "writeScope": [],
    "verification": [],
    "promptProfile": "detailed-worker"
  }
}
```

### templates

`.claude/skills/dev/spec/references/templates` にあった考え方を落とさない。

`spec-codex` に必要なテンプレート:

- `references/templates/spec-template-dir.md`
- `references/templates/tasks.template.json`
- `references/templates/tasks-schema-v3-codex.md`
- `references/templates/context-template.md`
- `references/discovery-decision-sprint.md`
- `references/diagram-selector.md`
- `references/cursor-delegation-protocol.md`
- `references/delegation-brief-template.md`
- `references/plan-reviewer.md`
- `references/gpt-55-prompting.md`

`SKILL.md` はこれらの内容を要約しすぎない。各 Step の検収条件が参照先の契約に依存する構造にする。

## spec-codex-run の要件

### 名前

`.codex/skills/dev/spec-codex-run`

旧 `spec-run` trigger は互換のため残す。

### 対象

`docs/PLAN/{YYMMDD}_{slug}/tasks.json` を正として Gate 単位に実行する。

既存 v3 PLAN は optional Codex 拡張がなくても実行できる。

### 実行責任

main Codex が保持する責任:

- `docs/PLAN` 状態更新
- `tasks.json` 更新
- `spec.md` 同期
- Gate PASS 判定
- 最終統合
- commit / push

Cursor Agent や subagent は局所作業だけを担当する。

### Gate 通過条件

Gate を `passed: true` にできる条件:

- 全 dependency Gate が `passed: true`
- 全 AC が `checked: true`
- review が `PASSED` または適切な `SKIPPED`

未 passed dependency がある Gate は、AC と review が成立していても `passed: true` にしない。

### follow-up / review-fix / verification

実行後に増える再レビュー差分 Gate は初期設計 Gate と区別する。

- `kind: "follow-up"`
- `kind: "review-fix"`
- `kind: "verification"`

### Codex review

工程に応じて使い分ける。

- Gate 中レビュー: `codex review --uncommitted -`
- 最終レビュー: `codex review --base <base>`
- commit 単位レビュー: `codex review --commit <sha>`

review prompt には Gate id、仕様ファイルパス、Goal、Constraints、AC、対象ファイル、除外したい無関係差分を含める。

`codex review` が使えない場合は自己レビューし、代替レビューであることを記録する。

### sync-spec-md.mjs

`spec-codex-run/scripts/sync-spec-md.mjs` を置く。

要件:

- `tasks.json` から `spec.md` generated 領域を同期する。
- v3 Gate 契約を表示する。
- Gate dependency graph は Mermaid で出す。
- optional `kind`, `parallelizable`, `delegation` があれば表示する。
- 既存 v3 PLAN で動く。

### worktree

worktree は optional。開始時に選べる。

既存 `spec-agent-run` の worktree setup / teardown / scripts は参照してよいが、名前とパスは `spec-codex-run` に統一する。

## README / 周辺更新

- README に新スキル名を反映する。
- `.codex/skills/dev/parallel-agent-brief/SKILL.md` 内で `spec-agent-run` を参照している箇所があれば `spec-codex-run` に更新する。
- ただし、`*-ex` は参照用なので README で通常利用スキルとして案内しない。

## 品質チェック

完成後に確認すること:

- `.codex/skills/dev/spec-codex/SKILL.md` が単なる reference 目次になっていない。
- 各 Step が成果物、契約、検収ゲート、次工程との接続を持っている。
- `SKILL.md` 本文だけで詳細作業を完結できない。reference の契約が成果物の形を決めている。
- 作成経緯や議論の痕跡がスキル本文に入っていない。
- `spec.md`, `tasks.json`, `context.md`, `discovery.md`, `plan-review.md` の関係が明確。
- Mermaid 選択が規模固定になっていない。
- Cursor Agent 委任が毎回選択可能。
- Cursor 用 prompt が詳細作業契約になっている。
- `schemaVersion: 3` 互換が維持されている。
- 既存 `/Users/ryryo/dev/chrome_extension/docs/PLAN` の v3 PLAN を読める。
- `tasks.template.json` が JSON として parse できる。
- Markdown relative links が解決できる。
- `sync-spec-md.mjs` が `node --check` を通る。

## 期待する最終成果

別エージェントは、既存 `*-ex` の文を修正するのではなく、上記要件から新しい `.codex/skills/dev/spec-codex` と `.codex/skills/dev/spec-codex-run` を作成する。

完成報告には次を含める。

- 作成/変更したファイル一覧
- 旧参照から採用した要素
- 意図的に採用しなかった要素
- 検証結果
- 残課題がある場合は、その理由
