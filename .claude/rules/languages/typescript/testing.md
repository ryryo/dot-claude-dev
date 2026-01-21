---
description: TypeScriptテスト規約。Vitest/Jestを使用したTDDを前提。
globs:
  - "**/*.test.ts"
  - "**/*.spec.ts"
---

# TypeScriptテスト規約

## テストフレームワーク

Vitest または Jest を使用。

## テスト構造

### describe/it パターン

```typescript
describe('validateEmail', () => {
  describe('正常系', () => {
    it('有効なメールアドレスでtrueを返す', () => {
      expect(validateEmail('user@example.com')).toEqual({
        valid: true,
      });
    });
  });

  describe('異常系', () => {
    it('不正な形式でfalseとエラーを返す', () => {
      expect(validateEmail('invalid')).toEqual({
        valid: false,
        error: 'Invalid email format',
      });
    });
  });

  describe('境界値', () => {
    it('空文字でfalseを返す', () => {
      expect(validateEmail('')).toEqual({
        valid: false,
        error: 'Email is required',
      });
    });
  });
});
```

### Given-When-Then パターン

```typescript
it('有効なメールアドレスでtrueを返す', () => {
  // Given
  const email = 'user@example.com';

  // When
  const result = validateEmail(email);

  // Then
  expect(result).toEqual({ valid: true });
});
```

## アサーション

### 基本アサーション

```typescript
expect(result).toBe(expected);           // 厳密等価
expect(result).toEqual(expected);        // 構造等価
expect(result).toBeTruthy();             // 真値
expect(result).toBeNull();               // null
expect(result).toBeDefined();            // 定義済み
```

### 型安全なアサーション

```typescript
// Result型のアサーション
function expectSuccess<T>(result: Result<T>): asserts result is { ok: true; value: T } {
  expect(result.ok).toBe(true);
}

function expectError(result: Result<unknown>): asserts result is { ok: false; error: Error } {
  expect(result.ok).toBe(false);
}
```

## モック

### 関数モック

```typescript
const mockFetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ data: 'test' }),
});

vi.stubGlobal('fetch', mockFetch);
```

### モジュールモック

```typescript
vi.mock('./api', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: '1', name: 'Test' }),
}));
```

## テストカバレッジ

- 目標: 80%以上
- 重点: ビジネスロジック、バリデーション
- 除外: 型定義、設定ファイル

## 禁止事項

- ❌ テスト内で実装を変更
- ❌ テスト間の依存
- ❌ 非同期テストでの`done`コールバック（async/awaitを使用）
