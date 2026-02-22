---
description: JavaScriptテスト規約。Vitestを使用。
globs:
  - "**/*.test.js"
  - "**/*.spec.js"
---

# JavaScriptテスト規約

## テストフレームワーク

**Vitest** を使用。

## テスト構造

```javascript
describe('calculateTotal', () => {
  describe('正常系', () => {
    it('アイテムの合計金額を計算する', () => {
      const items = [
        { price: 100 },
        { price: 200 },
      ];

      const result = calculateTotal(items);

      expect(result).toBe(300);
    });
  });

  describe('異常系', () => {
    it('空配列で0を返す', () => {
      expect(calculateTotal([])).toBe(0);
    });

    it('undefinedでエラーを投げる', () => {
      expect(() => calculateTotal(undefined)).toThrow('Items is required');
    });
  });
});
```

## アサーション

```javascript
// 等価
expect(result).toBe(expected);       // 厳密等価
expect(result).toEqual(expected);    // 構造等価

// 真偽
expect(result).toBeTruthy();
expect(result).toBeFalsy();

// 数値
expect(result).toBeGreaterThan(5);
expect(result).toBeLessThan(10);
expect(result).toBeCloseTo(0.3, 5);  // 浮動小数点

// 配列
expect(array).toContain(item);
expect(array).toHaveLength(3);

// オブジェクト
expect(obj).toHaveProperty('name');
expect(obj).toMatchObject({ name: 'John' });

// 例外
expect(() => fn()).toThrow();
expect(() => fn()).toThrow('error message');
```

## モック

### 関数モック

```javascript
import { vi } from 'vitest';

const mockFn = vi.fn();
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'test' });

// 呼び出し確認
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockFn).toHaveBeenCalledTimes(2);
```

### モジュールモック

```javascript
vi.mock('./api', () => ({
  fetchData: vi.fn().mockResolvedValue({ data: 'test' }),
}));
```

### タイマーモック

```javascript
import { vi, test } from 'vitest';

vi.useFakeTimers();

test('debounce', () => {
  const fn = vi.fn();
  const debounced = debounce(fn, 100);

  debounced();
  debounced();
  debounced();

  vi.advanceTimersByTime(100);

  expect(fn).toHaveBeenCalledTimes(1);
});
```

## 非同期テスト

```javascript
// async/await
it('データを取得する', async () => {
  const data = await fetchData();
  expect(data).toEqual({ id: 1 });
});

// Promise
it('データを取得する', () => {
  return fetchData().then(data => {
    expect(data).toEqual({ id: 1 });
  });
});
```

## セットアップ・クリーンアップ

```javascript
describe('Database', () => {
  beforeAll(async () => {
    await db.connect();
  });

  afterAll(async () => {
    await db.disconnect();
  });

  beforeEach(() => {
    // 各テスト前
  });

  afterEach(() => {
    vi.clearAllMocks();
  });
});
```

## 禁止事項

- ❌ テスト間の依存関係
- ❌ 実装の詳細をテスト
- ❌ 不安定なテスト（タイミング依存）
