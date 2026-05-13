# Plan Reviewer

`spec-codex` で作成した PLAN は、実行前に `tasks.json` を主、`spec.md` を補助としてレビューする。Critical / High の問題は計画完成前に修正する。

## Input

- `docs/PLAN/{YYMMDD}_{slug}/tasks.json`
- `docs/PLAN/{YYMMDD}_{slug}/spec.md`
- プロジェクトルートの README / AGENTS / CLAUDE 系ドキュメント
- 外部参照がある場合は `docs/PLAN/{YYMMDD}_{slug}/references/`

## Core Checks

### 1. Schema

- `tasks.json.schemaVersion === 3`。
- `spec.slug`, `spec.title`, `spec.summary`, `spec.createdDate`, `spec.specPath` が揃っている。
- `status`, `reviewChecked`, `preflight`, `gates` が存在する。
- `progress` / `metadata` は作成しない。
- Codex 追加情報は `extensions`、`gates[].kind`、`gates[].parallelizable`、`todos[].delegation` の optional 拡張だけに入っている。

### 2. Gate Contract

各 Gate で確認する。

- `id`, `title`, `summary`, `dependencies`, `goal`, `constraints`, `acceptanceCriteria`, `todos`, `review`, `passed` がある。
- `goal.what` は「何を達成するか」を 1-2 文で示している。
- `goal.why` は設計上の意図を示しており、`what` の言い換えだけになっていない。
- `constraints.must` は採用技術、既存パターン、型契約、整合ルールなどの判断基準になっている。
- `constraints.mustNot` は破壊禁止対象やスコープ外対象を具体的に示している。
- AC は「実装したか」ではなく「結果として何が成立しているか」を書いている。
- AC はコマンド、テスト、HTTP、ブラウザ操作、ファイル確認、手動確認のいずれかで判定できる。
- AC 数は Gate の粒度に合っている。

### 3. Todo

- Todo は軽量フィールドだけを持つ。
- `impl`, `description`, `relatedIssues`, `steps` を持たない。
- `id`, `gate`, `title`, `tdd`, `dependencies`, `affectedFiles` がある。
- `affectedFiles` は具体的なファイルまたは必要十分なディレクトリを指す。
- `[TDD]` は入出力や assertion が明確な作業にだけ付いている。
- `[SIMPLE]` は局所的で review skip の判断が妥当な作業にだけ付いている。
- Todo 依存に循環がない。

### 4. Dependencies

- Gate dependencies は存在する Gate ID だけを参照している。
- Gate dependencies に循環がない。
- 未 passed dependency がある Gate を `passed: true` にする計画になっていない。
- `parallelizable: true` の Gate / Todo は write scope と状態所有が独立している。

### 5. Preflight

- Preflight は network 必須、workspace 外書き込み、対話ログイン/OAuth のみ。
- ローカル生成、test、build、通常の sandbox 内コマンドを Preflight にしていない。
- 各項目に `id`, `title`, `command`, `manual`, `reason`, `ac`, `checked` がある。
- `manual: true` の項目は人間が完了確認できる AC を持つ。
- Preflight がない場合は `preflight: []` で、`spec.md` の Preflight セクションは省略されている。

### 6. spec.md Structure

- 冒頭に `Gate 0: 準備` がある。
- Gate 0 は `spec-codex-run` で実行すること、対象 PLAN、実行ディレクトリ、Cursor Agent 使用有無、Preflight 状態を確認することを示している。
- `概要`, `背景`, `設計決定事項`, `アーキテクチャ詳細`, `変更対象ファイルと影響範囲`, `タスクリスト`, `レビューステータス`, `残存リスク` が適切に存在する。
- `<!-- generated:begin -->` / `<!-- generated:end -->` がある。
- generated 領域は `tasks.json` と同期している。
- authored 領域に実装手順本文、型定義、関数本体、API 実装コードを書いていない。

### 7. Mermaid

[diagram-selector.md](diagram-selector.md) に従い、内容に応じて必要な図だけを使っている。

- UI導線、依存関係、処理構成には `flowchart` / `graph`。
- 時系列処理、API、外部連携には `sequenceDiagram`。
- DB / 永続化モデルがある場合のみ `erDiagram`。
- 状態遷移が重要な場合のみ `stateDiagram`。
- 期限、段階リリース、並行期間が判断に必要な場合のみ `gantt`。
- 図が不足して人間が計画全体を誤読しやすい状態になっていない。
- 図が過剰で、シンプルな変更の理解を妨げていない。

### 8. Cursor / Delegation

- Cursor Agent は毎回「使う / 使わない」を選べる設計になっている。
- `extensions.codex.delegationPolicy.cursorAgent` は `ask-each-run` を基本にしている。
- `todos[].delegation` がある場合、`eligible`, `agent`, `mode`, `writeScope`, `verification`, `promptProfile` が明確。
- Cursor Agent に渡す作業は局所的で、write scope が明確。
- Cursor Agent に `docs/PLAN` 更新、`tasks.json` 更新、`spec.md` 同期、Gate PASS 判定、最終統合、commit/push を渡していない。
- Cursor 向け委任プロンプトは [delegation-brief-template.md](delegation-brief-template.md) の項目を満たせる情報を持っている。

### 9. References

- `spec.md` の「参照すべきファイル」はコードベース外の参照だけを載せている。
- コードベース内ファイルは Gate constraints / affectedFiles で参照している。
- 外部リポジトリ、外部資料、会話内仕様は `references/` にコピーまたは要約されている。
- `references/` 内の資料に実行者が読めない絶対パスや別リポジトリ前提の相対パスが残っていない。

### 10. Residual Risk

- 計画段階で調査、コード読解、参照実装確認、ユーザー確認により解消できる不明点が残存リスクに入っていない。
- 解消可能な不明点は Gate 契約、AC、Preflight、または検証 Gate に落ちている。
- 残存リスクに残るのは外部サービス状態、実機環境、ユーザー権限、将来運用など、計画作成時点で解消できないものだけ。
- 各リスクに対応する Gate / AC / Preflight がある。

### 11. Semantic Consistency

- `spec.md` の設計決定事項と `tasks.json.gates[].constraints` が矛盾していない。
- `spec.md` の背景と `goal.why` が整合している。
- `spec.md` のアーキテクチャ詳細と AC が矛盾していない。
- 変更対象ファイル一覧と `todos[].affectedFiles` が概ね一致している。
- follow-up / review-fix / verification Gate と初期 implementation Gate の役割が混ざっていない。

## Result

### APPROVED

次を満たす場合だけ `APPROVED` とする。

- Critical / High の問題がない。
- Gate 契約だけで実行エージェントが作業を開始できる。
- `spec-codex-run` が `tasks.json` を正として実行できる。
- 人間が `spec.md` で計画全体を把握できる。

### NEEDS_REVISION

Critical / High がある場合は `NEEDS_REVISION` とし、対象、問題、修正内容を具体的に書く。

Critical examples:

- AC が検証不能。
- 外部参照が実行者から読めない。
- Gate 依存関係に循環や不整合がある。
- Cursor 委任で `docs/PLAN` 更新や commit を外部エージェントに渡している。
- 計画段階で解消できる不明点が残存リスクに棚上げされている。

High examples:

- Mermaid が不足し、人間が計画全体を誤読しやすい。
- review-fix Gate と初期 implementation Gate が混ざり、実行順が不明。
- `constraints.mustNot` が曖昧で破壊禁止対象が伝わらない。
- Preflight に通常のローカルコマンドが混ざっている。

## Report Format

```markdown
PLAN REVIEW {APPROVED|NEEDS_REVISION}

## 評価結果

- Schema:
- Gate Contract:
- AC:
- Todo:
- Dependencies:
- Preflight:
- Mermaid:
- Cursor Delegation:
- References:
- Residual Risk:
- Semantic Consistency:

## 指摘事項

### 1. {カテゴリ}

- 対象: {Gate/Todo/section/file}
- 問題: {具体的な問題}
- 修正: {必要な修正}
```
