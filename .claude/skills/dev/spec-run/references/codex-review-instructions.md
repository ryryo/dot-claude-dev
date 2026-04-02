# Codex Adversarial Review — Focus テンプレート

Codex モードの VERIFY で `adversarial-review` に渡す focus テンプレート。
Claude オーケストレーターが複雑さに応じてシンプルモード（統合版1回）または複雑モード（3観点並列）を選択する。

## 実行コマンド

```bash
# シンプルモード: 統合版 focus を1回実行
node "$CODEX_COMPANION" adversarial-review --wait {focus テキスト}

# 複雑モード: 3観点を並列実行
node "$CODEX_COMPANION" adversarial-review --background {quality-focus}
node "$CODEX_COMPANION" adversarial-review --background {correctness-focus}
node "$CODEX_COMPANION" adversarial-review --background {conventions-focus}
# 完了待ち
node "$CODEX_COMPANION" status --wait
```

## 複雑さの判断基準

Claude が各 Todo の以下の要素を総合判断して決定する:

| 判断要素 | シンプル寄り | 複雑寄り |
|----------|------------|---------|
| 変更ファイル数 | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | 局所的 | 複数モジュール横断 |
| リスク | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

## Focus テンプレート

### 統合版（シンプルモード用）

1回の adversarial-review で全観点をカバーする。

```
以下の仕様に基づいて変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}
対象 Todo: {Todo の IMPL 内容 — 要約}

レビュー観点:
1. 品質・設計: ベストプラクティス準拠、DRY/KISS/YAGNI、保守性・可読性
2. 正確性・仕様適合: 仕様要件の充足、API/SDK準拠、エッジケース、セキュリティ
3. プロジェクト慣例: CLAUDE.md準拠、既存パターンとの一貫性、命名規則
```

### quality-focus（品質・設計）

```
品質・設計の観点で変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}
対象 Todo: {Todo の IMPL 内容 — 要約}

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
正確性・仕様適合の観点で変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}
対象 Todo: {Todo の IMPL 内容 — 要約}
設計決定事項: {仕様書の設計決定事項 — あれば記載}
残存リスク: {仕様書の残存リスク — あれば記載}

重点確認項目:
- 仕様書のユーザー要件を正しく実現しているか（過不足の両面）
- 使用しているライブラリ・APIの公式仕様に従った使い方か
- 非推奨APIや非標準的な使い方をしていないか
- 設計決定事項・残存リスクに記載された前提を破る実装がないか
- 隠れたエッジケースや障害モードが見落とされていないか
- OWASP Top 10 に該当する脆弱性がないか
- 入力バリデーションが適切か（システム境界での検証）
```

### conventions-focus（プロジェクト慣例）

```
プロジェクト慣例の観点で変更をレビューしてください。

仕様概要: {仕様書の概要 — 1-2文}
対象 Todo: {Todo の IMPL 内容 — 要約}

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
| `{Todo の IMPL 内容}` | 仕様書の対象 Todo | 要約 |
| `{設計決定事項}` | 仕様書の設計決定事項セクション | あれば記載、なければ省略 |
| `{残存リスク}` | 仕様書の残存リスクセクション | あれば記載、なければ省略 |

## 結果の判定

adversarial-review は構造化 JSON を返す:

```json
{
  "verdict": "needs-attention | approve",
  "summary": "...",
  "findings": [
    { "file": "...", "line_start": 0, "severity": "critical|high|medium|low", "title": "...", "body": "...", "recommendation": "...", "confidence": 0.0 }
  ],
  "next_steps": ["..."]
}
```

### 判定基準

- **verdict が "approve"** → PASS
- **verdict が "needs-attention"**:
  - severity が critical/high の finding がある → FAIL
  - severity が medium 以下のみ → Claude が内容を精査し、実質的な問題か判断して PASS/FAIL を決定

### 複雑モード（3観点並列）の統合判定

- 3観点すべて PASS → 全体 PASS
- いずれかが FAIL → 全体 FAIL → FIX へ
