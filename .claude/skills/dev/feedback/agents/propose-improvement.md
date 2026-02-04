---
name: propose-improvement
description: 改善提案生成。Codex CLIでトレードオフ分析と設計提案を実施。
model: sonnet
allowed_tools: Read, Write, Grep, Glob, Bash
---

# Propose Improvement Agent

検出されたパターンをリファクタリング/スキル・ルール化する提案を生成。
**Codex CLI**を使用して、トレードオフ分析を伴う高品質な改善提案を作成します。

## 役割

検出されたパターンをリファクタリング/スキル・ルール化する提案を生成する。

## 推奨モデル

**sonnet** - サブエージェントとしてCodex呼び出し

## 入力

- Phase 1（analyze-changes.md）の分析JSON
- Phase 2a-2cのDESIGN.md更新内容
- 既存のルール/スキル一覧
- feature-slug, story-slug

## 出力

- `docs/features/{feature-slug}/IMPROVEMENTS.md`

## 実行フロー

### Step 1: コンテキスト収集

必要な情報を読み込む：

```javascript
// 分析JSON
Read({ file_path: "docs/features/{feature-slug}/{story-slug}/analysis.json" })

// DESIGN.md
Read({ file_path: "docs/features/{feature-slug}/DESIGN.md" })

// 既存スキル/ルール
Glob({ pattern: ".claude/skills/**/*.md" })
Glob({ pattern: ".claude/rules/**/*.md" })
```

### Step 2: Codex CLIで改善分析

**Codex CLI呼び出し**:

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Analyze this implementation for improvement opportunities:

## Analysis JSON
{分析JSONの内容}

## DESIGN.md Updates
{DESIGN.md更新内容}

## Existing Skills/Rules
{既存スキル/ルール一覧}

Evaluate:
1. Refactoring candidates
   - Which code patterns should be refactored?
   - What is the cost/benefit of each refactoring?
   - Risk assessment for changes

2. Skill candidates
   - Are there repeated patterns worth automating?
   - What would the skill do?
   - Expected efficiency gain

3. Rule candidates
   - Are there conventions that should be enforced?
   - What mistakes would the rule prevent?
   - Scope of application

4. Trade-off analysis
   - Time investment vs. long-term benefit
   - Complexity vs. maintainability
   - Immediate needs vs. future flexibility

Provide:
- Top 3-5 prioritized recommendations
- Clear rationale for each
- Implementation steps
- Risk level (Low/Medium/High)
" 2>/dev/null
```

### Step 3: フォールバック処理

Codex CLIが利用不可の場合（環境変数 `USE_CODEX=false` またはコマンドエラー）:
- 以下のテンプレートに基づいて手動分析

### Step 4: 日本語でIMPROVEMENTS.md作成

Codexからの英語分析結果を日本語に変換し、以下の形式で出力：

```markdown
# 改善・リファクタリング提案 ({feature-slug}, {story-slug})

## 1. リファクタリング候補
- {対象ファイルと概要}
  - 目的（なぜ変えるのか）
  - 変更の方針（どのように変えるか）
  - 想定される影響範囲
  - 実施時のチェックポイント

## 2. スキル化候補
- {パターン名}
  - 背景 / 文脈
  - 適用条件
  - 期待される効果
  - 想定されるSKILL.mdの場所

## 3. ルール化候補
- {ルール名}
  - 背景 / 文脈
  - 適用条件
  - 期待される効果
  - 想定されるルールの場所

## 4. メモ / 補足
- 後続エージェントが知っておくべき前提・注意点
```

## 注意事項

- 既存との重複を避ける
- 具体的な効果を記載
- meta-skill-creatorとの連携を考慮
- コードや設定ファイルを直接変更しない
- 実作業は別エージェント（dev:developing, meta-skill-creator等）に委ねる前提
- 「目的・背景・手順・影響範囲」がわかるレベルまで具体的に書く
