---
description: "ストーリーからチーム実行計画を作成。ストーリー分析→タスク分解→レビュー（opencode）→承認"
argument-hint: "[ストーリー or DESIGN.mdパス]"
---

# /dev:team-plan - チーム実行計画作成コマンド

## 概要

ストーリーを分析し、Agent Teams で並行実行するための計画（task-list.json）を作成します。
レビューのみ opencode を活用します。
計画は `docs/FEATURES/team/{YYMMDD}_{slug}/` に永続化され、複数保持可能です。

## 使い方

### ストーリー指定

```
/dev:team-plan ユーザー認証機能の実装
```

### DESIGN.md パス指定

```
/dev:team-plan docs/FEATURES/auth/DESIGN.md
```

### 引数なし

```
/dev:team-plan
```

→ ストーリーをヒアリング

## 実行方法

**必ず `dev:team-plan` スキルを発火して実行してください。**

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
