# decompose-tasks

## 役割

ストーリー分析結果からタスクリストを生成する。
各タスクは実装可能な粒度に分解し、ワークフロー（tdd/e2e/task）を分類する。
**後続エージェントがこのファイルだけで作業できるよう、技術コンテキストを必ず含める。**

## 推奨モデル

**sonnet** - タスク分解に適切なバランス

## 入力

- `story-analysis.json`
- **コードベースの探索結果**（対象ファイルの現状把握が必須）

## 出力

`task-list.json`:

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

## コード探索（必須）

タスク分解の**前に**、以下のコード探索を行うこと:

1. **対象ファイルの特定**: story-analysis.jsonのスコープから変更対象ファイルをGlob/Grepで探す
2. **現状の把握**: 対象ファイルをReadで読み、現在のシグネチャ・型・構造を確認する
3. **関連モジュールの確認**: import先やストアなど、タスク実行に必要な周辺情報を収集する
4. **既存テストの確認**: テストファイルの有無と更新要否を判断する

この探索結果を `context` セクションに記録する。

## プロンプト

```
story-analysis.jsonを読み込み、ストーリーを実装可能なタスクに分解してください。

## ストーリー分析
{story_analysis}

## 必須手順

### Step 1: コード探索
タスク分解の前に、対象ファイルを実際に読み込んで以下を把握してください:
- 変更対象ファイルのパスと現状（シグネチャ、型、構造）
- 関連モジュール（import先、ストア、フック）
- 既存テストファイルの有無と更新要否
- 実装に必要なブラウザAPI/ライブラリの制約

### Step 2: contextセクション作成
探索結果を `context` セクションにまとめてください。
後続エージェントがこのJSONだけを見て作業を開始できるだけの情報を含めること。

### Step 3: タスク分解 + ワークフロー分類
contextを踏まえてタスクを分解し、各タスクに `workflow` フィールドを付与してください。

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

5. **対象ファイルの明示（filesフィールド）**
   - 各タスクに `files` フィールドを追加し、対象ファイルパスと操作（new/edit）を記載
   - descriptionは「何をするか」に集中させ、ファイルパスは `files` に分離する

## ワークフロー分類ルール

各タスクに `workflow` フィールドを付与する。値は以下の3つ:

### "tdd" — テスト駆動開発
- 入出力が明確に定義可能
- アサーションで検証可能
- ロジック層（ビジネスロジック、バリデーション、計算、データ変換）
- 副作用がない、またはモック可能

例: validateEmail, calculateTotal, parseJson, checkPermission

### "e2e" — 視覚的検証
- 視覚的な確認が必要
- UX/UI判断が含まれる
- プレゼンテーション層（UIコンポーネント、レイアウト、アニメーション）

例: LoginForm, Dashboard, Modal, Header

### "task" — セットアップ/設定
- テスト不要（設定ファイル、環境構築）
- UI検証不要（コマンド実行結果で検証可能）
- 一回限りのセットアップ

例: npm init, ESLint設定, Docker環境構築, README作成

### 判定フロー
```
入出力が明確に定義できる？
    ├─ YES → "tdd"
    └─ NO → 視覚的確認が必要？
              ├─ YES → "e2e"
              └─ NO → "task"
```

→ 詳細: [../references/tdd-criteria.md] | [../references/e2e-criteria.md] | [../references/task-criteria.md]

## 出力形式

JSON形式で出力してください。
contextセクションは必須です。
各タスクに `workflow` フィールド（"tdd" / "e2e" / "task"）を必ず含めてください。
```

## 注意事項

- **contextセクションは省略不可**: 後続エージェントの自律実行に必要
- **planPath**: plan.json が存在する場合（dev:epic 連携時）、`context.planPath` に `docs/FEATURES/{feature-slug}/PLAN.md` のパスを含めること。dev:developing が全体計画を参照する際に使用
- 依存関係は明確に定義する
- フェーズは依存関係に基づいて順序付け
- 各タスクは独立してテスト可能な粒度にする
- 各タスクに `files` フィールドでパスと操作（new/edit）を明示する
- 各タスクに `workflow` フィールドで実行ワークフローを明示する
