---
name: dev:feedback
description: |
  実装完了後、学んだことをDESIGN.mdに蓄積。リファクタリング/スキル・ルールの自己改善も提案。
  ストーリー駆動開発の終点。
  「フィードバック」「/dev:feedback」で起動。

  Trigger:
  フィードバック, 学習事項蓄積, /dev:feedback, feedback, design update
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# フィードバック → 仕様書蓄積（dev:feedback）

## エージェント委譲ルール

**分析・更新・提案は必ずTaskエージェントに委譲する。自分で実行しない。**

呼び出しパターン（全ステップ共通）:
```
agentContent = Read(".claude/skills/dev/feedback/agents/{agent}.md")
Task({ prompt: agentContent + 追加コンテキスト, subagent_type: {type}, model: {指定モデル} })
```

| Step | agent | model | type | 追加コンテキスト |
|------|-------|-------|------|-----------------|
| 1 REVIEW | review-analyze.md | sonnet | general-purpose | git diff, feature-slug |
| 2a DESIGN | update-design.md | sonnet | general-purpose | Step 1のJSON + feature-slug |
| 2b DESIGN | (code-simplifier) | opus | code-simplifier | DESIGN.mdのパス + 整理観点 |
| 3 IMPROVE | propose-manage.md | sonnet | general-purpose | Step 1-2の結果 + feature-slug |

## 出力先

| ファイル | Step |
|----------|------|
| `docs/features/{feature-slug}/DESIGN.md` | 2a |
| `docs/features/DESIGN.md` | 2a |
| `docs/features/{feature-slug}/IMPROVEMENTS.md` | 3 |

---

## 実行手順（必ずこの順序で実行）

### Step 1: REVIEW（実装レビュー + 変更分析）

1. → **エージェント委譲**（review-analyze.md / sonnet）
   - Codex CLIで実装バイアスを排除した客観的レビュー
   - 変更内容を分析し、学習事項を抽出 → 分析JSON
2. レビュー結果をユーザーに提示
3. Critical issuesがあれば修正を推奨（dev:developingに戻る選択肢）

**ゲート**: レビュー + 分析JSON完了

### Step 2: DESIGN（DESIGN.md更新 + 整理）

#### 2a: 機能DESIGN.md + 総合DESIGN.md更新

1. → **エージェント委譲**（update-design.md / sonnet）
2. `docs/features/{feature-slug}/DESIGN.md` に追記・保存
3. `docs/features/DESIGN.md` に重要な判断を追記

#### 2b: 総合DESIGNの整理

1. → **エージェント委譲**（code-simplifier / opus）
2. 整理観点:
   - 用語・表現の一貫性
   - セクション構造の論理性
   - 冗長さの排除
   - 将来の追記性

**ゲート**: 機能DESIGN.md + 総合DESIGN.md更新完了

### Step 3: IMPROVE（改善提案 + テスト管理）

1. → **エージェント委譲**（propose-manage.md / sonnet）
2. `docs/features/{feature-slug}/IMPROVEMENTS.md` に保存
3. TDDタスクがあった場合:
   - → **AskUserQuestion** でテスト整理方針を確認（整理する/すべて保持/スキップ）
   - 選択に応じてテストの簡素化・削除を実行

---

## 完了条件

- [ ] 実装レビュー + 変更分析が完了した（Step 1）
- [ ] 機能DESIGN.mdが更新された（Step 2a）
- [ ] 総合DESIGN.mdが更新・整理された（Step 2a + 2b）
- [ ] 改善提案が作成された（Step 3）
- [ ] テスト資産が整理された（TDD時）（Step 3）

## 参照

- agents/: review-analyze.md, update-design.md, propose-manage.md
