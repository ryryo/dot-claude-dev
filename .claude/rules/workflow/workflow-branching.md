---
description: タスクをTDD/E2E/TASKに分岐する判定ルール。dev:storyスキルで使用。
globs:
  - "**/TODO.md"
  - "**/task-list.json"
---

# ワークフロー分岐判定ルール（TDD/E2E/TASK）

## 判定フロー

```
タスクを分析
    ↓
入出力が明確に定義できる？
    ├─ YES → TDD
    └─ NO → 視覚的確認が必要？
              ├─ YES → E2E
              └─ NO → セットアップ/設定タスク？
                        ├─ YES → TASK
                        └─ NO → 再分析（タスクを分解）
```

## TDD判定基準

### 必須条件（すべて満たす）

1. **入出力が明確**
   - 関数の引数と戻り値が定義できる
   - 期待値と実際値の比較が可能

2. **アサーションで検証可能**
   - `expect(result).toEqual(expected)`
   - 状態変化が検証できる

3. **ロジック層**
   - ビジネスロジック
   - バリデーション
   - データ変換
   - 計算処理

### TDD対象の例

| カテゴリ | 例 |
|----------|-----|
| バリデーション | validateEmail, validatePassword |
| 計算 | calculateTotal, computeDiscount |
| 変換 | formatDate, parseJson |
| ビジネスロジック | checkPermission, applyRules |
| ユーティリティ | slugify, debounce |

## E2E判定基準

### 必須条件（いずれかを満たす）

1. **視覚的確認が必要**
   - 見た目の正しさを判断
   - デザイン仕様との一致

2. **UX/UI判断が含まれる**
   - ユーザビリティの確認
   - 操作感の確認

3. **プレゼンテーション層**
   - UIコンポーネント
   - レイアウト
   - アニメーション

### E2E対象の例

| カテゴリ | 例 |
|----------|-----|
| フォーム | LoginForm, SignupForm |
| レイアウト | Header, Sidebar, Dashboard |
| コンポーネント | Button, Modal, Card |
| ナビゲーション | Navbar, Breadcrumb |
| フィードバック | Toast, Alert, Spinner |

## TASK判定基準

### 必須条件（いずれかを満たす）

1. **テスト不要**
   - 設定ファイルの作成・変更
   - 環境構築コマンドの実行

2. **UI検証不要**
   - コマンドの実行結果で検証可能
   - ファイルの存在確認で検証可能

3. **一回限りのセットアップ**
   - プロジェクト初期化
   - 環境構築

### TASK対象の例

| カテゴリ | 例 |
|----------|-----|
| 環境構築 | npm init, Docker環境構築 |
| 設定 | ESLint, Prettier, TypeScript設定 |
| CI/CD | GitHub Actions, デプロイスクリプト |
| ドキュメント | README, CHANGELOG |
| 依存関係 | npm install, パッケージ追加 |

## TODO.mdラベル形式

### TDDタスク

```markdown
- [ ] [TDD][RED] {タスク名} のテスト作成
- [ ] [TDD][GREEN] {タスク名} の実装
- [ ] [TDD][REFACTOR] {タスク名} のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build
```

### E2Eタスク

```markdown
- [ ] [E2E][IMPL] {タスク名} 実装
- [ ] [E2E][AUTO] {タスク名} agent-browser検証
- [ ] [E2E][CHECK] lint/format/build
```

### TASKタスク

```markdown
- [ ] [TASK][EXEC] {タスク名} 実行
- [ ] [TASK][VERIFY] {タスク名} 検証
```

## 曖昧なケースの判断

### API呼び出し

```
API呼び出しロジック → TDD（モックで検証）
API結果の表示UI → E2E（視覚的確認）
```

### フォーム

```
バリデーションロジック → TDD
フォームUI → E2E
```

### 状態管理

```
状態更新ロジック → TDD
状態に基づくUI表示 → E2E
```

## 分解のヒント

判定が難しいタスクは分解を検討:

```
「ログインフォームを作成」
    ↓ 分解
├─ [TDD] validateEmail
├─ [TDD] validatePassword
├─ [TDD] handleLogin（APIロジック）
└─ [E2E] LoginForm（UI）
```

```
「TypeScriptプロジェクト初期化 + ユーザー認証機能」
    ↓ 分解
├─ [TASK] TypeScript設定
├─ [TASK] ESLint/Prettier設定
├─ [TDD] validateEmail
├─ [TDD] validatePassword
└─ [E2E] LoginForm
```

## 関連スキル

- **dev:story**: TDD/E2E/TASK分類を実行
- **dev:developing**: 分類に基づいて実装
