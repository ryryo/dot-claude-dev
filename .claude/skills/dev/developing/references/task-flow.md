# TASKワークフロー詳細

## 概要

TASKワークフローは、セットアップ/設定/インフラ構築など、テスト不要・UI検証不要のタスクを対象とする。

## 3ステップワークフロー

```
EXEC（実行）→ VERIFY（検証）→ COMMIT
```

| ステップ | 内容 | 目的 |
|----------|------|------|
| EXEC | タスク実行 | 設定ファイル作成、コマンド実行 |
| VERIFY | 検証 | ファイル存在確認、ビルド成功確認 |
| COMMIT | コミット | 変更をコミット |

## EXECフェーズ

### 実行内容

- 設定ファイルの作成/編集
- コマンドの実行
- 依存関係のインストール
- 環境変数の設定

### 実行パターン

#### 設定ファイル作成

```bash
# TypeScript設定
Write({ file_path: "tsconfig.json", content: {...} })

# ESLint設定
Write({ file_path: ".eslintrc.js", content: {...} })

# Docker設定
Write({ file_path: "Dockerfile", content: {...} })
```

#### コマンド実行

```bash
# プロジェクト初期化
npm init -y

# 依存関係インストール
npm install typescript @types/node --save-dev

# 環境構築
docker-compose up -d
```

## VERIFYフェーズ

### 検証パターン

#### ファイル存在確認

```javascript
// ファイルが存在するか確認
Glob({ pattern: "tsconfig.json" })
// → ファイルが存在すれば成功
```

#### ビルド/コンパイル確認

```bash
# TypeScriptコンパイル
npx tsc --noEmit

# Viteビルド
npm run build

# Dockerビルド
docker-compose build
```

#### コマンド実行結果確認

```bash
# パッケージ確認
npm list typescript

# サービス確認
docker-compose ps
```

### 検証チェックリスト

| カテゴリ | 検証項目 |
|----------|----------|
| 設定ファイル | ファイルが存在する |
| ビルド | コンパイル/ビルドが成功する |
| 依存関係 | パッケージがインストールされている |
| サービス | サービスが起動している |

## COMMITフェーズ

### コミットメッセージ例

```bash
# 環境構築
git commit -m "chore: add TypeScript configuration"
git commit -m "chore: setup ESLint and Prettier"
git commit -m "chore: add Docker environment"

# CI/CD
git commit -m "ci: add GitHub Actions workflow"

# ドキュメント
git commit -m "docs: add README.md"
```

## TODO.mdラベル形式

```markdown
### TASKタスク
- [ ] [TASK][EXEC] TypeScript環境構築 実行
- [ ] [TASK][VERIFY] TypeScript環境構築 検証
```

## ラベル説明

| ラベル | 意味 |
|--------|------|
| [TASK][EXEC] | タスク実行（設定ファイル作成、コマンド実行） |
| [TASK][VERIFY] | 検証（ファイル存在確認、ビルド成功確認） |

## 注意事項

- TASKタスクは通常、フェーズの最初に実行（環境構築が必要なため）
- 検証は必ず実行後に行う
- 失敗した場合は修正して再実行

## エラー時の対応

1. **実行失敗**: エラーメッセージを確認し、修正後再実行
2. **検証失敗**: 設定を見直し、必要に応じて再設定
3. **3回失敗**: 問題を報告、ユーザーに確認

## 関連ドキュメント

- [TDDワークフロー](./tdd-flow.md)
- [E2Eワークフロー](./e2e-flow.md)
- [TASK判定基準](../../story/references/task-criteria.md)
