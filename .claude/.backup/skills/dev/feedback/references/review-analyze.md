# レビュー・分析仕様（review-analyze）

実装レビュー + 変更分析を一体で実施する。git diffを読み、マージ可否の品質ゲート判定と学習事項の抽出を行う。
改善提案（リファクタリング・スキル/ルール化）はStep 3の責務。ここでは「この実装、マージして大丈夫か？」だけを判定する。

## 入力

- git diff（mainブランチとの差分）
- feature-slug

## 実行フロー

### 1. 差分取得

```bash
git diff main...HEAD
git diff main...HEAD --stat
git log main...HEAD --oneline
```

### 2. OpenCode CLIで実装レビュー

```bash
opencode run -m openai/gpt-5.3-codex "
Review this implementation:

## Changes
{git diff出力}

Check:
1. Code quality (clean code, consistent style, appropriate abstraction)
2. Potential bugs (null/undefined, error boundaries, race conditions)
3. Missing edge cases (boundary values, empty/invalid inputs)
4. Security concerns (input validation, auth, sensitive data)
5. Performance issues (N+1, unnecessary re-renders, memory leaks)
6. Test coverage gaps (untested paths, missing error cases)

Provide:
- Summary of changes
- Critical issues (must fix before merge)
- Overall quality score (1-10)

NOTE: Do NOT include improvement recommendations or refactoring suggestions.
Focus only on correctness, safety, and merge-readiness.
" 2>&1
```

### 3. フォールバック（OpenCode利用不可時）

環境変数 `USE_OPENCODE=false` またはコマンドエラーの場合、以下のチェックリストで手動レビュー:

- [ ] クリーンコード原則に従っている
- [ ] 一貫したコーディングスタイル
- [ ] null/undefined処理
- [ ] エラー境界のカバレッジ
- [ ] 境界値・空入力・無効入力
- [ ] 入力検証、認証/認可、機密データ
- [ ] N+1クエリ、不要な再レンダリング、メモリリーク
- [ ] 未テストのパス、欠落しているエラーケース

### 4. 変更内容を分析 → JSON出力

git diffとレビュー結果から以下のJSON形式で分析結果を生成する:

```json
{
  "changedFiles": [
    { "path": "src/auth/validate.ts", "type": "added", "description": "バリデーション関数を追加" }
  ],
  "addedFeatures": ["メールアドレスバリデーション"],
  "designDecisions": [
    { "decision": "Zodを使用", "reason": "型安全性と表現力の両立", "alternatives": ["手動", "Yup"] }
  ],
  "discoveries": [
    { "topic": "Zodのエラーメッセージ", "detail": ".message()でカスタムエラーメッセージを設定可能" }
  ],
  "warnings": [
    { "topic": "バリデーション順序", "detail": "長さチェックを先にしないとエラーメッセージが不適切" }
  ]
}
```

抽出項目:
1. **変更されたファイル**: パス、変更タイプ（added/modified/deleted）、説明
2. **追加された機能**: 機能名リスト
3. **設計判断**: 何を、なぜ、代替案
4. **技術的な発見**: 新しく学んだこと
5. **注意点・ハマりどころ**: 将来の開発者への警告

### 5. 結果を日本語で報告

## 報告形式

### 問題なしの場合

```markdown
## REVIEW PASSED

### 変更サマリー
{変更の概要}

### 評価結果
- コード品質: PASS/NEEDS ATTENTION
- バグリスク: PASS/NEEDS ATTENTION
- エッジケース: PASS/NEEDS ATTENTION
- セキュリティ: PASS/NEEDS ATTENTION
- パフォーマンス: PASS/NEEDS ATTENTION
- テストカバレッジ: PASS/NEEDS ATTENTION

### 品質スコア: X/10

### 分析JSON
{上記JSON}
```

### 問題ありの場合

```markdown
## REVIEW NEEDS ATTENTION

### 変更サマリー
{変更の概要}

### Critical Issues（修正必須）
1. **ファイル:行番号** - 問題の説明
```

Critical Issuesがある場合、**AskUserQuestion** で次のアクションをユーザーに確認する:
- `/plan-doc` で修正計画書を作成（別スレッドで修正作業）
- `/dev:story` で修正タスクリストを生成（別スレッドで修正作業）
- そのまま続行（軽微な場合）

## 注意事項

- 過度な指摘は避ける
- Critical issuesは本当に重要なもののみ（マージをブロックする問題だけ）
- 改善提案・リファクタリング候補はここでは出さない（ルール化・CLAUDE.md更新検討は Step 3 の責務）
- 設計判断は「なぜ」を重視
- 発見は具体的に記録
- 警告は将来の開発者のために
