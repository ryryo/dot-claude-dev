---
description: JavaScriptコーディング規約。ES6+とモダンな書き方を推奨。
globs:
  - "**/*.js"
  - "**/*.mjs"
  - "**/*.cjs"
---

# JavaScriptコーディング規約

## 変数宣言

### const優先

```javascript
// Good: 再代入しない場合はconst
const API_URL = 'https://api.example.com';
const users = [];

// Good: 再代入が必要な場合のみlet
let count = 0;
count++;
```

### var禁止

```javascript
// Bad: varは使用しない
var name = 'John';

// Good: constまたはlet
const name = 'John';
```

## 関数

### アロー関数

```javascript
// Good: 短い関数
const add = (a, b) => a + b;

// Good: 複数行
const processUser = (user) => {
  const { name, email } = user;
  return { name, email: email.toLowerCase() };
};
```

### デフォルトパラメータ

```javascript
// Good
function greet(name = 'Guest') {
  return `Hello, ${name}!`;
}
```

### 残余引数

```javascript
// Good
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0);
}
```

## オブジェクト・配列

### 分割代入

```javascript
// Good: オブジェクト
const { name, email } = user;

// Good: 配列
const [first, second] = items;

// Good: デフォルト値
const { name = 'Unknown' } = user;
```

### スプレッド構文

```javascript
// Good: 配列コピー
const newArray = [...array, newItem];

// Good: オブジェクトマージ
const newUser = { ...user, name: 'New Name' };
```

### ショートハンド

```javascript
// Good
const name = 'John';
const user = { name }; // { name: name } と同等
```

## 非同期処理

### async/await

```javascript
// Good
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error('Failed to fetch');
    return await response.json();
  } catch (error) {
    console.error(error);
    throw error;
  }
}
```

### Promise.all

```javascript
// Good: 並列実行
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts(),
]);
```

## エラーハンドリング

```javascript
// Good: カスタムエラー
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Good: try-catch
try {
  await processData(data);
} catch (error) {
  if (error instanceof ValidationError) {
    // バリデーションエラー処理
  } else {
    throw error;
  }
}
```

## 禁止事項

- ❌ `var`の使用
- ❌ `==`の使用（`===`を使用）
- ❌ `arguments`オブジェクト（残余引数を使用）
- ❌ `with`文
- ❌ `eval()`

## 推奨事項

- ✅ 厳格モード `'use strict'`
- ✅ Optional chaining `?.`
- ✅ Nullish coalescing `??`
- ✅ テンプレートリテラル
