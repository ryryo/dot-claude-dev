# decompose-tasks

## 役割

ストーリー分析結果からタスクリストを生成する。
各タスクは実装可能な粒度に分解する。

## 推奨モデル

**sonnet** - タスク分解に適切なバランス

## 入力

- `story-analysis.json`

## 出力

`task-list.json`:

```json
{
  "phases": [
    {
      "name": "フェーズ1: バリデーションロジック",
      "tasks": [
        {
          "id": "task-1",
          "name": "validateEmail",
          "description": "メールアドレスの形式を検証する関数",
          "type": "function",
          "input": "string (email)",
          "output": "{ valid: boolean, error?: string }",
          "dependencies": []
        },
        {
          "id": "task-2",
          "name": "validatePassword",
          "description": "パスワードの強度を検証する関数",
          "type": "function",
          "input": "string (password)",
          "output": "{ valid: boolean, error?: string }",
          "dependencies": []
        }
      ]
    },
    {
      "name": "フェーズ2: UIコンポーネント",
      "tasks": [
        {
          "id": "task-3",
          "name": "LoginForm",
          "description": "ログインフォームUIコンポーネント",
          "type": "ui-component",
          "input": "onSubmit callback",
          "output": "React component",
          "dependencies": ["task-1", "task-2"]
        }
      ]
    },
    {
      "name": "フェーズ3: 統合",
      "tasks": [
        {
          "id": "task-4",
          "name": "handleLogin",
          "description": "ログイン処理のAPI呼び出しとリダイレクト",
          "type": "function",
          "input": "{ email: string, password: string }",
          "output": "Promise<void>",
          "dependencies": ["task-3"]
        }
      ]
    }
  ],
  "metadata": {
    "totalTasks": 4,
    "estimatedPhases": 3
  }
}
```

## プロンプト

```
story-analysis.jsonを読み込み、ストーリーを実装可能なタスクに分解してください。

## ストーリー分析
{story_analysis}

## タスク分解のルール

1. **粒度**
   - 1タスク = 1関数/1コンポーネント
   - 30分〜2時間で完了できる粒度

2. **フェーズ分割**
   - 依存関係に基づいてフェーズを分割
   - 独立したタスクは並列実行可能

3. **タスクの種類**
   - function: 純粋関数、ロジック
   - ui-component: UIコンポーネント
   - api: APIエンドポイント
   - integration: 統合処理

4. **入出力の明確化**
   - 関数タスクは必ず入出力を定義
   - UIコンポーネントはpropsとイベントを定義

## 出力形式

JSON形式で出力してください。
```

## 注意事項

- 依存関係は明確に定義する
- フェーズは依存関係に基づいて順序付け
- 各タスクは独立してテスト可能な粒度にする
