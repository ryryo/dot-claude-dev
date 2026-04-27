# Codex Review — Focus テンプレート

Codex モードの VERIFY で `codex review` に渡す focus テンプレート。
Claude オーケストレーターが複雑さに応じてシンプルモード（統合版1回）または複雑モード（3観点並列）を選択する。

## 実行コマンド

> **CLI 制約**: `--commit <SHA>` / `--base <BRANCH>` / `--uncommitted` と `[PROMPT]` は**排他的引数**であり併用不可。
> **companion v1.0.2 変更**: `node "$CODEX_COMPANION" review` はフォーカステキスト非対応になった。VERIFY では native `codex review` CLI を使うこと（`node "$CODEX_COMPANION" review` は使わない）。

### 使い分け

| やりたいこと | コマンド | 対象差分 |
|-------------|---------|---------|
| コミット指定（カスタム指示なし） | `codex review --commit {SHA}` | 指定コミットの差分 |
| カスタム指示付き（推奨） | `codex review - < .tmp/focus.md` | `origin/main..HEAD` の差分を自動検出 |
| 未コミット変更 | `codex review --uncommitted` | staged + unstaged + untracked |

**IMPL 直後の VERIFY では `[PROMPT]` 方式を使う**（HEAD が対象コミットなので自動検出で十分）。

### シンプルモード（1回）

```bash
codex review - < .tmp/codex-review-focus.md
```

### 複雑モード（3観点並列）

```bash
codex review - < .tmp/codex-review-quality.md &
codex review - < .tmp/codex-review-correctness.md &
codex review - < .tmp/codex-review-conventions.md &
wait
```

## 複雑さの判断基準

Claude が各 Gate の変更内容を総合判断して決定する:

| 判断要素 | シンプル寄り | 複雑寄り |
|----------|------------|---------|
| 変更ファイル数 | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | 局所的 | 複数モジュール横断 |
| リスク | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

## Focus テンプレート

### 統合版（シンプルモード用）

1回の codex review で全観点をカバーする。

```
以下の Gate 契約に基づいて変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}

Gate {Gate ID}:
- Goal: {gate.goal.what} / {gate.goal.why}
- Constraints (MUST): {gate.constraints.must を箇条書き}
- Constraints (MUST NOT): {gate.constraints.mustNot を箇条書き}
- Acceptance Criteria: {gate.acceptanceCriteria を `[AC.ID] description` 形式で}

レビュー観点:
1. 品質・設計: ベストプラクティス準拠、DRY/KISS/YAGNI、保守性・可読性
2. 正確性・仕様適合: Gate 契約の充足（Goal/AC/Constraints）、API/SDK準拠、エッジケース、セキュリティ
3. プロジェクト慣例: CLAUDE.md準拠、既存パターンとの一貫性、命名規則
```

### quality-focus（品質・設計）

```
品質・設計の観点で Gate {Gate ID} の変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}

Gate 契約:
- Goal: {gate.goal.what}
- Acceptance Criteria: {gate.acceptanceCriteria を `[AC.ID] description` 形式で}

重点確認項目:
- 当該言語・FWの慣用的パターンに従っているか
- DRY/KISS/YAGNI等の設計原則に反する実装がないか
- エラーハンドリング戦略が適切か（過剰でも不足でもない）
- 命名が一貫性を持ち意図が伝わるか
- 過度に複雑なロジックがないか（将来の変更が困難な構造）
- 適切な抽象化レベルか（過剰な抽象化も問題）
```

### correctness-focus（正確性・仕様適合）

```
正確性・仕様適合の観点で Gate {Gate ID} の変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}

Gate 契約:
- Goal: {gate.goal.what} / {gate.goal.why}
- Constraints (MUST): {gate.constraints.must を箇条書き}
- Constraints (MUST NOT): {gate.constraints.mustNot を箇条書き}
- Acceptance Criteria: {gate.acceptanceCriteria を `[AC.ID] description` 形式で}

設計決定事項: {仕様書の設計決定事項 — あれば記載}
残存リスク: {仕様書の残存リスク — あれば記載}

重点確認項目:
- Gate Goal が達成されているか / 全 AC が成立しているか
- Constraints の MUST / MUST NOT が守られているか
- 使用しているライブラリ・APIの公式仕様に従った使い方か
- 非推奨APIや非標準的な使い方をしていないか
- 設計決定事項・残存リスクに記載された前提を破る実装がないか
- 隠れたエッジケースや障害モードが見落とされていないか
- OWASP Top 10 に該当する脆弱性がないか
- 入力バリデーションが適切か（システム境界での検証）
```

### conventions-focus（プロジェクト慣例）

```
プロジェクト慣例の観点で Gate {Gate ID} の変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}

Gate 契約:
- Goal: {gate.goal.what}
- 影響ファイル: {gate.todos[].affectedFiles を集約}

重点確認項目:
- CLAUDE.mdに記載されたプロジェクトルール・制約に従っているか
- 技術スタック・FWの使い方がプロジェクト方針と一致しているか
- 同様の処理を行う既存コードと同じパターンを使っているか
- ディレクトリ構造・ファイル配置がプロジェクトの慣例に従っているか
- インポート・エクスポート方式がプロジェクト内で統一されているか
- 変数名・関数名・クラス名がプロジェクトの命名規則に従っているか
- ファイル名・ディレクトリ名の命名パターンが一貫しているか
```

## テンプレート変数の埋め方

| 変数 | 取得元 | 注意事項 |
|------|--------|----------|
| `{仕様書の概要}` | 仕様書の「概要」セクション | 1-2文に要約 |
| `{Gate ID}` | `tasks.json.gates[].id` | そのまま |
| `{gate.goal.what / why}` | `tasks.json.gates[].goal` | そのまま引用 |
| `{gate.constraints.must / mustNot}` | `tasks.json.gates[].constraints` | 箇条書き |
| `{gate.acceptanceCriteria}` | `tasks.json.gates[].acceptanceCriteria` | id + description |
| `{gate.todos[].affectedFiles}` | `tasks.json.gates[].todos[].affectedFiles` | 重複排除して列挙 |
| `{設計決定事項}` | 仕様書の設計決定事項セクション | あれば記載、なければ省略 |
| `{残存リスク}` | 仕様書の残存リスクセクション | あれば記載、なければ省略 |

## 結果の判定

`codex review` は優先度付きテキストコメントを返す:

- `[P1]` — critical: 出荷阻止レベルの問題
- `[P2]` — important: 重要だが文脈次第
- `[P3]` — minor: 軽微な改善提案

### 判定基準

- **コメントなし / P3 のみ** → PASS
- **P2 あり** → Claude が内容を精査し、仕様の設計決定に基づく意図的な動作かを判断して PASS/FAIL 決定
- **P1 あり** → FAIL

### 複雑モード（3観点並列）の統合判定

- 3観点すべて PASS → 全体 PASS
- いずれかが FAIL → 全体 FAIL → FIX へ
