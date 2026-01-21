# TDD判定基準

## TDD対象の特徴

以下の特徴を持つタスクはTDDで実装する。

### 1. 入出力が明確

- 関数の引数と戻り値が明確に定義できる
- 境界条件が特定できる
- エッジケースが列挙できる

**例**:
```typescript
// 入力: email (string)
// 出力: { valid: boolean, error?: string }
function validateEmail(email: string): ValidationResult
```

### 2. アサーションで検証可能

- 期待値と実際の値を比較できる
- 状態変化が検証可能
- エラー条件が特定できる

**例**:
```typescript
expect(validateEmail("user@example.com")).toEqual({ valid: true });
expect(validateEmail("invalid")).toEqual({ valid: false, error: "Invalid email format" });
```

### 3. ロジック層

- ビジネスロジック
- バリデーション
- データ変換
- 計算処理
- パーサー

### 4. 副作用の制御

- 副作用がない（純粋関数）
- または副作用がモック可能

## TDD対象の例

| タスク種別 | 例 |
|-----------|-----|
| バリデーション | validateEmail, validatePassword, validateForm |
| 計算 | calculateTotal, computeDiscount, sumItems |
| 変換 | formatDate, parseJson, transformData |
| ビジネスロジック | checkPermission, applyRules, processOrder |
| ユーティリティ | slugify, debounce, deepClone |

## TDD非対象の例

以下はTDDではなくPLANで実装する。

| タスク種別 | 理由 |
|-----------|------|
| UIコンポーネント | 視覚的確認が必要 |
| レイアウト | 見た目の判断が必要 |
| アニメーション | 動きの確認が必要 |
| レスポンシブ対応 | 複数画面サイズでの確認が必要 |

## TDDワークフロー

TDDタスクは以下のサイクルで実装する:

```
[RED] テスト作成（失敗するテスト）
    ↓
[GREEN] 実装（テストを通す最小実装）
    ↓
[REFACTOR] リファクタリング
    ↓
[REVIEW] セルフレビュー
    ↓
[CHECK] 品質チェック
```

→ 詳細: `.claude/rules/workflow/tdd-workflow.md`
