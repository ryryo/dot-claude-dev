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

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
