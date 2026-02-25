---
name: skill-refactorer
description: |
  SKILL.mdを最も効率的に動作するよう整理するスキル。
  7ステップのリファクタリング手順でスキルの実行効率・コンテキスト効率を最適化する。

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

## リファクタリング手順

詳細は [references/patterns.md](.claude/skills/dev/skill-refactorer/references/patterns.md) を必ず参照。

| Step | 内容 | 判断ポイント |
|------|------|-------------|
| 1 | 各Stepの実行方式を判定 | メイン実行 vs Task委譲、スキル全体の記述方式 |
| 2 | ファイル配置を整理 | agents/ vs references/ vs templates/ の判定フロー |
| 3 | SKILL.mdから詳細を分離 | 何を外部に移すか、テンプレート化の判断 |
| 4 | 繰り返し構造をDRY化 | 冒頭テーブル集約、1行参照化 |
| 5 | LLMの行動制御 | 委譲の明示、ゲート条件の配置 |
| 6 | 全体構造を整える | 理想構造への再構成 |
| 7 | 不要なものを削除 | 未使用参照・冗長記述の除去 |

---

## 実行フロー

### Phase 1: 分析

1. Read で対象SKILL.mdと関連ファイル（agents/, references/, scripts/, templates/）を読み込む
2. Read で `references/patterns.md` を読み込む
3. 7ステップのチェック項目に沿って問題点を洗い出す
4. **AskUserQuestion** で分析結果をユーザーと共有し、方針を合意する

### Phase 2: 適用

1. 合意した方針に基づき、Step 1→7 の順に適用する
2. ファイル移動・新規作成・SKILL.md書き換えを実行
3. **AskUserQuestion** で結果を確認する

---

## 完了条件

- [ ] スキルの実行効率・コンテキスト効率が改善されている
- [ ] 7ステップのチェック項目をすべて確認済み
- [ ] ユーザーが承認済み
