---
description: タスクをTDD/E2Eに分岐する判定ルール。story-to-tasksスキルで使用。
globs:
  - "**/TODO.md"
  - "**/task-list.json"
---

# TDD/E2E分岐判定ルール

## 判定フロー

```
タスクを分析
    ↓
入出力が明確に定義できる？
    ├─ YES → TDD
    └─ NO → 視覚的確認が必要？
              ├─ YES → E2E
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

## 関連スキル

- **dev:story-to-tasks**: TDD/E2E分類を実行
- **dev:developing**: 分類に基づいて実装
