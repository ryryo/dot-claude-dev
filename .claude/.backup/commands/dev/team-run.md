---
description: "承認済み計画をネイティブ Agent Teams + Subagent ハイブリッドで並行実行。Git Worktree分離"
argument-hint: "[計画ディレクトリパス]"
---

# /dev:team-run - ネイティブチーム並行実行コマンド

## 概要

`dev:team-plan` で作成・承認済みの計画（task-list.json）を Agent Teams + Subagent ハイブリッドで並行実行します。
opencode を使用せず Claude Code のネイティブ機能のみで実装。
Git Worktree でファイル分離し、最終的に PR を作成します。

## 使い方

### 計画パス指定

```
/dev:team-run docs/FEATURES/team/260217_auth/
```

### 引数なし

```
/dev:team-run
```

→ 既存計画一覧を表示し、ユーザーが選択

## 実行方法

**必ず `dev:team-run` スキルを発火して実行してください。**

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
