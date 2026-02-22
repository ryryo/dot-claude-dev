---
description: TypeScriptコーディング規約。型安全性と可読性を重視。
globs:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScriptコーディング規約

## 型定義

### 明示的な型定義

```typescript
// Good: 明示的な戻り値の型
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Good: インターフェースで構造を定義
interface User {
  id: string;
  name: string;
  email: string;
}
```

### 型推論の活用

```typescript
// Good: 変数の型は推論に任せる
const user = { id: '1', name: 'John' }; // User型を推論

// Good: 配列リテラルも推論
const numbers = [1, 2, 3]; // number[]を推論
```

### Union型とリテラル型

```typescript
// Good: 限定された値にはリテラル型
type Status = 'pending' | 'active' | 'completed';

// Good: 判別可能なUnion型
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: Error };
```

## Zod連携

### スキーマ定義

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(8, 'パスワードは8文字以上必要です'),
});

type User = z.infer<typeof UserSchema>;
```

### バリデーション

```typescript
function validateUser(input: unknown): Result<User> {
  const result = UserSchema.safeParse(input);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, error: new Error(result.error.message) };
}
```

## エラーハンドリング

### Result型パターン

```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function parseJson<T>(json: string): Result<T> {
  try {
    return { ok: true, value: JSON.parse(json) };
  } catch (e) {
    return { ok: false, error: e as Error };
  }
}
```

## 禁止事項

- ❌ `any`型の使用（`unknown`を使用）
- ❌ 型アサーション `as`の乱用
- ❌ `!`（非nullアサーション）の乱用
- ❌ `@ts-ignore`の使用

## 推奨事項

- ✅ `strict: true`を有効化
- ✅ 関数の戻り値の型を明示
- ✅ `unknown`から型ガードで絞り込む
- ✅ Discriminated Unionを活用
