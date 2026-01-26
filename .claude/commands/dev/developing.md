---
description: "TODO.mdのタスクを実行。TDD/E2E/TASKラベルに応じたワークフローで実装"
argument-hint: "[feature-slug/story-slug（任意）]"
---

# /dev:developing - タスク実装コマンド

## 概要

TODO.mdのタスクを実行します。TDD/E2E/TASKラベルに応じて適切なワークフローを適用します。

## 使い方

### 引数付き

```
/dev:developing auth/login
```

### 引数なし

```
/dev:developing
```
→ カレントディレクトリから TODO.md を検索

## 実行方法

**⚠️ 重要: このコマンドは必ず `dev:developing` スキルを発火して実行してください。**

### 必須手順

1. **スキルファイルを読み込む**: [`.claude/skills/dev/developing/SKILL.md`](.claude/skills/dev/developing/SKILL.md) を必ず読み込む
2. **スキルを発火**: スキルファイルの指示に従って実行する
3. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない

### スキルによる実行内容

`dev:developing` スキルによって以下が実行されます：

1. **Worktree管理**: ブランチ確認、必要に応じてWorktree作成・移動
2. **TODO.md読み込み**: 未完了タスクの特定とラベル（TDD/E2E/TASK）確認
3. **タスク登録**: TaskCreateでタスク管理システムに登録（進捗追跡用）
4. **ラベルに応じたワークフロー実行**
   - **[TASK]**: 直接実行（シンプル）
   - **[TDD]**: RED → GREEN → REFACTOR → SIMPLIFY → REVIEW → CHECK → MANAGE → COMMIT
   - **[E2E]**: IMPL → AUTO → CHECK → COMMIT
5. **TODO.md更新**: 完了タスクにチェックマーク

詳細なワークフローは、スキルファイルを参照してください。

## 関連コマンド

- `/dev:story` - タスクリスト生成
- `/dev:feedback` - 実装後のフィードバック
