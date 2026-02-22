---
description: "承認済み計画をAgent Teamsで並行実行。Wave式実行→レビューフィードバック→クリーンアップ"
argument-hint: "[計画ディレクトリパス]"
---

# /dev:team-opencode-exec - チーム並行実行コマンド

## 概要

`dev:team-plan` で作成・承認済みの計画（task-list.json）を Agent Teams で並行実行します。
Wave 式のチーム実行→レビューフィードバック→クリーンアップまで一貫して行います。

## 使い方

### 計画パス指定

```
/dev:team-opencode-exec docs/FEATURES/team/260213_auth/
```

### 引数なし

```
/dev:team-opencode-exec
```

→ 既存計画一覧を表示し、ユーザーが選択

## 実行方法

**必ず `dev:team-opencode-exec` スキルを発火して実行してください。**

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
