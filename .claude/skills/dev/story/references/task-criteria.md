# TASK判定基準

## 概要

TASKは、テスト不要・UI検証不要のセットアップ/設定/インフラ構築タスクを対象とする。

## TASK対象の特徴

### 1. テスト不要

- 設定ファイルの作成・変更
- 環境構築コマンドの実行
- 依存関係のインストール
- ビルド設定の調整

### 2. UI検証不要

- コマンドの実行結果で検証可能
- ファイルの存在確認で検証可能
- ビルド/コンパイル成功で検証可能

### 3. 一回限りのセットアップ

- プロジェクト初期化
- 環境構築
- CI/CDパイプライン設定
- ドキュメント作成

## TASK対象の例

| カテゴリ | 例 |
|----------|-----|
| 環境構築 | npm init, Docker環境構築 |
| 設定 | ESLint, Prettier, TypeScript, Vite設定 |
| 依存関係 | npm install, パッケージ追加/更新 |
| CI/CD | GitHub Actions, デプロイスクリプト |
| ドキュメント | README, CHANGELOG, API仕様書 |
| インフラ | データベースマイグレーション, 環境変数設定 |

## TASK判定フロー

```
タスクを分析
    ↓
入出力が明確に定義できる？
    ├─ YES → TDD候補
    └─ NO → 視覚的確認が必要？
              ├─ YES → E2E候補
              └─ NO → セットアップ/設定タスク？
                        ├─ YES → TASK
                        └─ NO → 再分析（タスクを分解）
```

## task-list.json での指定

```json
{
  "id": "task-1",
  "name": "ESLint設定",
  "type": "integration",
  "workflow": "task",
  "files": { ".eslintrc.js": "new" },
  "description": "ESLintの設定ファイルを作成する"
}
```

## TASKワークフロー

```
EXEC（実行）→ VERIFY（検証）→ COMMIT
```

### EXECフェーズ

- 設定ファイルの作成/編集
- コマンドの実行
- 依存関係のインストール

### VERIFYフェーズ

- ファイル存在確認
- ビルド/コンパイル確認
- コマンド実行結果確認

## 判定のヒント

### TASKを選ぶべきケース

- プロジェクト初期化（`npm init`, `cargo new`）
- リンター/フォーマッター設定（ESLint, Prettier）
- TypeScript/Vite/Webpack設定
- Docker/docker-compose設定
- CI/CD設定（GitHub Actions）
- 環境変数設定（`.env`ファイル）
- ドキュメント作成（README, CONTRIBUTING）

### TASKを避けるべきケース

- ロジックを含む実装 → TDD
- UIコンポーネント → E2E
- 繰り返し実行されるスクリプト → TDD

## 関連ドキュメント

- [TDD判定基準](./tdd-criteria.md)
- [E2E判定基準](./e2e-criteria.md)
- [TASKワークフロー](../../developing/references/task-flow.md)
