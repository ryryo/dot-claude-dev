# Phase 0: 計画選択

## 責務

`docs/features/` 以下の `task-list.json` を検索し、ユーザーに選択UIを提供。選択されたパスを環境変数 `$TASK_LIST` として返す。

## 実装ステップ

### Step 1: task-list.json を検索

```bash
files=$(Glob "docs/features/**/task-list.json")
count=$(echo "$files" | wc -l)
```

件数に応じて分岐。

### Step 2: 件数別処理

#### 0件の場合

メッセージ表示して終了:
```
先に /dev:story を実行してタスクリストを作成してください。
```

終了コード: 0（正常終了）

#### 1件の場合

AskUserQuestion で確認（自動選択しない）:

```json
{
  "question": "以下の計画を実行しますか?\n\n【パス】{path}\n【タスク数】{totalTasks} (TDD: {tddCount} / E2E: {e2eCount} / TASK: {taskCount})",
  "choices": ["はい", "いいえ (パスを直接指定)"]
}
```

- **はい**: Step 3へ
- **いいえ**: パスを手動入力させる（入力後 Step 3へ）

#### 2件以上の場合

AskUserQuestion でリスト選択:

```json
{
  "question": "実行する計画を選択してください。\n\n{numList}\n\nいずれでもない場合はパスを直接指定してください。",
  "choices": ["{choice1}", "{choice2}", ..., "パスを直接指定"]
}
```

選択肢は以下の形式で生成:
```
1. docs/features/auth/task-list.json
   (5タスク: TDD 2 / E2E 2 / TASK 1)

2. docs/features/profile/task-list.json
   (3タスク: TDD 1 / E2E 1 / TASK 1)
```

- **番号選択**: 対応するパスを Step 3へ
- **パスを直接指定**: ユーザーが手動入力（その後 Step 3へ）

### Step 3: 環境変数を設定して返す

```bash
export TASK_LIST="{選択されたパス}"
echo "TASK_LIST=$TASK_LIST"
```

選択されたパスを返し、Phase 1で使用。

## Helper: タスク統計を計算

各 task-list.json から統計を抽出:

```typescript
interface TaskListStats {
  path: string;
  totalTasks: number;
  tddCount: number;
  e2eCount: number;
  taskCount: number;
}

function getTaskListStats(path: string): TaskListStats {
  const content = Read(path);
  const json = JSON.parse(content);
  const tasks = json.tasks || [];

  const tddCount = tasks.filter((t: any) => t.workflow === 'tdd').length;
  const e2eCount = tasks.filter((t: any) => t.workflow === 'e2e').length;
  const taskCount = tasks.filter((t: any) => t.workflow === 'task').length;

  return {
    path,
    totalTasks: tasks.length,
    tddCount,
    e2eCount,
    taskCount
  };
}
```

## 完了条件

- [ ] task-list.json が見つからない場合: メッセージ表示して終了
- [ ] 1件: ユーザーが「はい」または手動指定パス入力
- [ ] 2件以上: ユーザーが番号選択または手動指定パス入力
- [ ] `$TASK_LIST` が環境変数として設定された
- [ ] Phase 1へ引き継ぎ完了

## エラーハンドリング

| エラー | 対応 |
|--------|------|
| task-list.json の JSON parse エラー | ファイル名を表示してスキップ、次を検索 |
| Glob エラー | エラーメッセージ表示して終了 |
| ユーザーキャンセル | 終了（エラーコード 1） |
