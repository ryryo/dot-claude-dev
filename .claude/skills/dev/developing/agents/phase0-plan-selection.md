# Phase 0: 計画選択

## 責務

`docs/features/` 以下の `task-list.json` を検索し、ユーザーに選択UIを提供。選択されたパスを環境変数 `$TASK_LIST` として返す。

## 実装ステップ

### Step 1: task-list.json を検索

```bash
files=$(Glob "docs/features/**/task-list.json")
```

0件の場合: メッセージ表示して終了:
```
先に /dev:story を実行してタスクリストを作成してください。
```

### Step 2: 完了済みフィルタ＆タスク統計

各 task-list.json を Read し、`metadata.status` が `"completed"` のものを除外する。
※ `metadata.status` が未定義の場合は `"pending"` として扱う（未完了）。

残ったものについて統計を計算:

```json
{
  "path": "docs/features/auth/task-list.json",
  "totalTasks": 5,
  "tddCount": 2,
  "e2eCount": 2,
  "taskCount": 1
}
```

### Step 3: 件数別処理

**0件**: エラーメッセージ表示して終了

**1件**: AskUserQuestion で確認（自動選択しない）

```
Q: 以下の計画を実行しますか?

【パス】docs/features/auth/task-list.json
【タスク数】5 (TDD: 2 / E2E: 2 / TASK: 1)

選択肢: はい / いいえ (パスを直接指定)
```

**2件以上**: AskUserQuestion でリスト選択

```
Q: 実行する計画を選択してください。

1. docs/features/auth/task-list.json
   (5タスク: TDD 2 / E2E 2 / TASK 1)

2. docs/features/profile/task-list.json
   (3タスク: TDD 1 / E2E 1 / TASK 1)

選択肢: 1 / 2 / パスを直接指定
```

### Step 4: 環境変数を設定して返す

```bash
export TASK_LIST="{選択されたパス}"
```

## エラーハンドリング

| エラー | 対応 |
|--------|------|
| task-list.json の JSON parse エラー | ファイル名を表示してスキップ、次を検索 |
| Glob エラー | エラーメッセージ表示して終了 |
| ユーザーキャンセル | 終了（エラーコード 1） |
