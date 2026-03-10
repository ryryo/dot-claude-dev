# タスク分解仕様（decompose-tasks）

ストーリー分析結果からタスクリストを生成する。
各タスクは実装可能な粒度に分解し、ワークフロー（tdd/e2e/task）を分類する。
**後続エージェントがこのファイルだけで作業できるよう、技術コンテキストを必ず含める。**

## 入力

- `story-analysis.json`
- **コードベースの探索結果**（対象ファイルの現状把握が必須）

## 出力構造

`task-list.json` に以下の構造で作成する:

```json
{
  "context": {
    "planPath": "docs/FEATURES/{feature-slug}/PLAN.md（plan.json が存在する場合のみ）",
    "description": "ストーリー全体の技術的な説明",
    "targetFiles": {
      "src/path/to/file.ts": "このファイルの現状と変更内容の要約"
    },
    "existingTests": {
      "src/path/to/file.test.ts": "既存テストの状態と更新要否"
    },
    "relatedModules": {
      "storeName": "関連するストア/モジュールの役割と、タスクとの関係"
    },
    "currentSignatures": {
      "functionName": "現在の関数シグネチャ（変更対象の場合）"
    },
    "technicalNotes": {
      "key": "ブラウザ制約、API仕様、既存パターンなど、実装に必要な補足情報"
    }
  },
  "phases": [
    {
      "name": "フェーズ1: バリデーションロジック",
      "tasks": [
        {
          "id": "task-1",
          "name": "validateEmail",
          "description": "メールアドレスの形式を検証する関数",
          "type": "function",
          "workflow": "tdd",
          "files": {
            "src/lib/validation/validateEmail.ts": "new",
            "src/lib/validation/validateEmail.test.ts": "new"
          },
          "input": "string (email)",
          "output": "{ valid: boolean, error?: string }",
          "dependencies": []
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

## ワークフロー分類ルール

各タスクに `workflow` フィールドを付与する。値は以下の3つ:

### "tdd" — テスト駆動開発
- 入出力が明確に定義可能
- アサーションで検証可能
- ロジック層（ビジネスロジック、バリデーション、計算、データ変換）

### "e2e" — 視覚的検証
- 視覚的な確認が必要
- UX/UI判断が含まれる
- プレゼンテーション層（UIコンポーネント、レイアウト、アニメーション）

### "task" — セットアップ/設定
- テスト不要（設定ファイル、環境構築）
- UI検証不要（コマンド実行結果で検証可能）
- 一回限りのセットアップ

### 判定フロー
```
入出力が明確に定義できる？
    ├─ YES → "tdd"
    └─ NO → 視覚的確認が必要？
              ├─ YES → "e2e"
              └─ NO → "task"
```

→ 詳細: [../references/tdd-criteria.md] | [../references/e2e-criteria.md] | [../references/task-criteria.md]

## 注意事項

- **contextセクションは省略不可**: 後続エージェントの自律実行に必要
- **planPath**: plan.json が存在する場合（dev:epic 連携時）、`context.planPath` に `docs/FEATURES/{feature-slug}/PLAN.md` のパスを含めること
- 依存関係は明確に定義する
- フェーズは依存関係に基づいて順序付け
- 各タスクは独立してテスト可能な粒度にする
- 各タスクに `files` フィールドでパスと操作（new/edit）を明示する
- 各タスクに `workflow` フィールドで実行ワークフローを明示する
