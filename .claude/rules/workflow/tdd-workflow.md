---
description: TDD開発時に自動適用されるルール。RED→GREEN→REFACTORサイクルを厳格に遵守。
globs:
  - "**/*.test.ts"
  - "**/*.spec.ts"
  - "**/test_*.py"
---

# TDDワークフロールール

## 基本原則

1. **テストファースト**: 実装より先にテストを書く
2. **テスト固定**: 一度書いたテストは変更しない（仕様のブレ防止）
3. **最小実装**: テストを通す最小限のコードのみ書く
4. **リファクタリング**: 機能追加なしで品質改善

## RED→GREEN→REFACTORサイクル

### RED（テスト作成）

```
✓ テストのみ作成
✓ 実装は書かない
✓ モック実装も作らない
✓ テストが失敗することを確認
```

**禁止事項**:
- ❌ 実装と同時にテストを書く
- ❌ 実装後にテストを追加

### GREEN（実装）

```
✓ テストを通す最小限の実装
✓ テストは変更しない
✓ 将来の要件を先取りしない
✓ 過度な抽象化を避ける
```

**禁止事項**:
- ❌ テストを変更して通す
- ❌ 不要な機能を追加

### REFACTOR（リファクタリング）

```
✓ テストが成功し続けることを確認
✓ 機能追加はしない
✓ 品質改善のみ
```

**チェックリスト**:
- [ ] 単一責任原則
- [ ] 重複排除
- [ ] 命名改善
- [ ] 複雑度低減

### REVIEW（セルフレビュー）

```
✓ 「この実装、テストに過剰適合してない？抜け道ない？」
✓ 過剰適合: テストケースだけに最適化されていないか
✓ 抜け道: テストをすり抜ける不具合・エッジケースがないか
```

**チェックリスト**:
- [ ] テスト以外のケースでも正しく動作するか
- [ ] 境界値、null/undefined、空配列を考慮したか
- [ ] コード品質と保守性

**問題あれば**: GREENに戻って修正

## コミット戦略

1. **テストコミット**: REDフェーズ完了時（tdd-cycleエージェント内で実行）
2. **実装コミット**: フック駆動（commit-check.sh PostToolUseフックが各Task完了後に自動検出・指示）

## エージェント構成（4ステップ + フック駆動コミット）

```
tdd-cycle(opus+OpenCode) → [hook: auto-commit] → tdd-review(sonnet+OpenCode) → quality-check(haiku) → [hook: auto-commit] → spot-review(sonnet+OpenCode) → [FAIL時] spot-fix(opus)
```

| Step | Agent | 責務 |
|------|-------|------|
| 1 CYCLE | tdd-cycle | RED→テストcommit→GREEN→REFACTOR(+OpenCode) |
| 2 REVIEW | tdd-review | 過剰適合・抜け道(+OpenCode) + テスト資産管理 |
| 3 CHECK | quality-check | lint/format/build |
| 4 SPOT | spot-review | commit後の即時レビュー(+OpenCode)。検出のみ |
| 4b FIX | spot-fix | SPOT FAIL時: 修正→CHECK→再SPOT（最大3回） |

※ コミットはフック（commit-check.sh）が各Task完了後に自動検出・指示。明示的なCOMMITステップは不要。

## アンチパターン

| パターン | 問題 | 対策 |
|----------|------|------|
| テスト後付け | テストがテストケースに過剰適合 | テストファースト厳守 |
| テスト変更 | 仕様がブレる | テスト固定の原則 |
| 過剰実装 | 不要なコードが増える | 最小実装の原則 |

## 関連スキル

- **dev:developing**: TDDタスクの実装
- **dev:story**: TDDタスクの生成
