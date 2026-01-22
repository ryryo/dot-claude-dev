# task-execute

## 役割

TASKワークフローのEXEC/VERIFYフェーズを実行する。
セットアップ、設定、インフラ構築などのタスクを処理する。

## 推奨モデル

**sonnet** - 設定ファイル作成とコマンド実行に適したバランス

## 入力

- タスク名
- タスク説明
- 期待する成果物

## 出力

- 設定ファイル
- 実行結果
- 検証結果

## プロンプト

### EXECフェーズ

```
以下のTASKタスクを実行してください。

タスク: {task_name}
説明: {task_description}

## 実行内容

1. 必要な設定ファイルを作成/編集
2. 必要なコマンドを実行
3. 結果を報告

## 注意事項

- ファイル作成は Write ツールを使用
- コマンド実行は Bash ツールを使用
- エラーが発生した場合は原因を報告
```

### VERIFYフェーズ

```
以下のTASKタスクの検証を行ってください。

タスク: {task_name}
期待する成果物: {expected_output}

## 検証内容

1. ファイル存在確認（Glob/Read）
2. ビルド/コンパイル確認（Bash）
3. サービス起動確認（Bash）

## 検証結果形式

- 成功: "VERIFIED: {検証項目}"
- 失敗: "FAILED: {失敗項目} - {理由}"
```

## 実行パターン

### 設定ファイル作成

```javascript
// TypeScript設定
Write({
  file_path: "tsconfig.json",
  content: `{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}`
})
```

### コマンド実行

```javascript
// 依存関係インストール
Bash({
  command: "npm install typescript @types/node --save-dev",
  description: "Install TypeScript dependencies"
})
```

### 検証

```javascript
// ファイル存在確認
Glob({ pattern: "tsconfig.json" })

// ビルド確認
Bash({
  command: "npx tsc --noEmit",
  description: "Verify TypeScript compilation"
})
```

## 対象タスク例

| カテゴリ | 例 |
|----------|-----|
| 環境構築 | npm init, Docker環境構築 |
| 設定 | ESLint, Prettier, TypeScript設定 |
| CI/CD | GitHub Actions, デプロイスクリプト |
| ドキュメント | README, CHANGELOG |
| 依存関係 | npm install, パッケージ追加 |

## 注意事項

- 設定ファイルは既存のプロジェクト構造に合わせる
- コマンド実行前に必要なディレクトリを確認
- 失敗した場合はエラーメッセージを明確に報告
- 3回失敗した場合はユーザーに確認

## 関連ドキュメント

- [TASKワークフロー詳細](../references/task-flow.md)
- [TASK判定基準](../../story/references/task-criteria.md)
