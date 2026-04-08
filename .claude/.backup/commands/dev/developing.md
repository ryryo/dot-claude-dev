---
description: "task-list.jsonのタスクを実行。workflowフィールドに応じたワークフローで実装"
argument-hint: "[feature-slug/story-slug（任意）]"
---

# /dev:developing - タスク実装コマンド

## 概要

task-list.jsonのタスクを実行します。workflowフィールド（tdd/e2e/task）に応じて適切なワークフローを適用します。

## 使い方

### 引数付き

```
/dev:developing auth/login
```

### 引数なし

```
/dev:developing
```

→ カレントディレクトリから task-list.json を検索

## 実行方法

**⚠️ 重要: このコマンドは必ず `dev:developing` スキルを発火して実行してください。**

### 必須手順

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
