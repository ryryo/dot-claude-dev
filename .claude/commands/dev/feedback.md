---
description: "実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案"
argument-hint: "[feature-slug/story-slug（任意）]"
---

# /dev:feedback - フィードバック → 仕様書蓄積コマンド

## 概要

実装完了後、学んだことをDESIGN.mdに蓄積し、繰り返しパターンのスキル/ルール化を提案します。
`dev:developing` 完了後、PR作成前に実行するコマンドです。

## 使い方

### 引数付き

```
/dev:feedback user-auth/login-form
```

### 引数なし

```
/dev:feedback
```
→ 現在のWorktreeから自動推定、または質問

## 実行方法

**⚠️ 重要: このコマンドは必ず `dev:feedback` スキルを発火して実行してください。**

### 必須手順

1. **スキルファイルを読み込む**: [`.claude/skills/dev/feedback/SKILL.md`](.claude/skills/dev/feedback/SKILL.md) を必ず読み込む
2. **スキルを発火**: スキルファイルの指示に従って実行する
3. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない

### スキルによる実行内容

`dev:feedback` スキルによって以下が実行されます：

1. 変更内容の収集（git diff, git log）
2. 学習事項の抽出（設計判断、技術的発見、注意点）
3. DESIGN.md の更新（機能別・総合）
4. パターン検出（繰り返しパターンの特定）
5. 改善提案（ルール化/スキル化候補の提示）
6. スキル/ルール作成（承認時、meta-skill-creator を呼び出し）

詳細なワークフローは、スキルファイルを参照してください。

## 関連コマンド

- `/dev:story` - ストーリーからタスク生成
- `/dev:developing` - タスク実装
