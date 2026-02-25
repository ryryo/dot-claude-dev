---
name: skill-refactorer
description: |
  SKILL.mdファイルを整理・圧縮するスキル。
  10のリファクタリングパターンをチェックリストとして適用し、
  SKILL.mdをオーケストレータとして200行未満に再構成する。

  Trigger:
  スキル整理, SKILL.md圧縮, スキルリファクタ, skill refactor, refactor skill
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
---

# SKILL.md整理（skill-refactorer）

## 10パターン

詳細・チェック項目は [references/patterns.md](.claude/skills/dev/skill-refactorer/references/patterns.md) を必ず参照。

| # | パターン | 要点 |
|---|----------|------|
| 1 | 圧縮 | 詳細を外部に移し200行未満に |
| 2 | DRY化 | 繰り返しを冒頭定義+テーブルに集約 |
| 3 | LLM行動制御 | 委譲処理に「自分でやらない」明示+呼び出しコード |
| 4 | ゲート条件 | 各ステップ末尾にファイル存在チェック |
| 5 | 責務分離 | SKILL.mdはオーケストレータ、詳細はagents/references/ |
| 6 | 廃止・整理 | 未使用参照・冗長例を削除 |
| 7 | 構造化 | frontmatter→ルール→手順→完了条件の統一構成 |
| 8 | 委譲適切性 | 各Stepのメイン/委譲を判定、スキル構造に応じた記述 |
| 9 | テンプレート化 | 新規ファイルはテンプレート+initスクリプトで事前配置 |
| 10 | agents/references配置 | 委譲用→agents/、参照用→references/、雛形→templates/ |

---

## 実行手順

### Step 1: 現状分析

1. Read で対象SKILL.mdと関連ファイル（agents/, references/）を読み込む
2. Read で `references/patterns.md` を読み込む
3. **AskUserQuestion** で問題点をユーザーと共有:
   - 行数、外部ファイル構成、Stepごとの実行方式
   - 10パターンのうちどれが該当するかチェックリストで提示

### Step 2: 整理方針の合意

1. 各パターンの適用箇所を具体的に提示
2. **AskUserQuestion** で方針確認:
   - 削除するセクション
   - agents/ / references/ / templates/ / scripts/ への切り出し対象
   - メイン化/委譲維持の判断

### Step 3: 適用

1. SKILL.md書き換え（Edit/Write）
2. ファイル移動・新規作成（agents/, references/, templates/, scripts/）
3. **AskUserQuestion** で結果確認

---

## 完了条件

- [ ] SKILL.mdが200行未満
- [ ] 10パターンのチェック項目をすべて確認済み
- [ ] ユーザーが承認済み
