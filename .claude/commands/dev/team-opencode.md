---
description: "Agent Teamsでタスクを並行実装。opencode runで外部モデルに委譲"
argument-hint: "[TODO.mdパス or タスク指示]"
---

# /dev:team-opencode - Agent Teams並行実装コマンド

## 概要

Agent Teamsで複数タスクを並行実装します。各エージェント(haiku)がopencode runで外部モデルに実装を委譲します。

## 使い方

### TODO.mdを指定

```
/dev:team-opencode docs/features/auth/login/TODO.md
```

### 直接タスク指示

```
/dev:team-opencode バリデーション関数の作成、APIエンドポイントの実装、テストの追加
```

### 引数なし

```
/dev:team-opencode
```

→ カレントディレクトリから TODO.md を検索、またはタスクをヒアリング

## 実行方法

**⚠️ 重要: このコマンドは必ず `dev:team-opencode` スキルを発火して実行してください。**

### 必須手順

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
