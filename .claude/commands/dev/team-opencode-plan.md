---
description: "ストーリーからチーム実行計画を作成。opencode でストーリー分析・タスク分解・レビュー・承認"
argument-hint: "[ストーリー or DESIGN.mdパス]"
---

# /dev:team-opencode-plan - チーム実行計画作成コマンド

## 概要

opencode を活用してストーリーを分析し、Agent Teams で並行実行するための計画（task-list.json）を作成します。
計画は `docs/features/team-opencode/{YYMMDD}_{slug}/` に永続化され、複数保持可能です。

## 使い方

### ストーリー指定

```
/dev:team-opencode-plan ユーザー認証機能の実装
```

### DESIGN.md パス指定

```
/dev:team-opencode-plan docs/features/auth/DESIGN.md
```

### 引数なし

```
/dev:team-opencode-plan
```

→ ストーリーをヒアリング

## 実行方法

**必ず `dev:team-opencode-plan` スキルを発火して実行してください。**

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
