---
description: PHPコーディング規約。PSR-12準拠。
globs:
  - "**/*.php"
---

# PHPコーディング規約

## 基本スタイル（PSR-12）

### ファイル構造

```php
<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\User;
use App\Repositories\UserRepository;

class UserService
{
    public function __construct(
        private readonly UserRepository $userRepository
    ) {}

    public function findById(int $id): ?User
    {
        return $this->userRepository->find($id);
    }
}
```

### クラス定義

```php
class User
{
    public function __construct(
        private readonly int $id,
        private string $name,
        private string $email
    ) {}

    public function getName(): string
    {
        return $this->name;
    }

    public function setName(string $name): void
    {
        $this->name = $name;
    }
}
```

## 型宣言

### 厳格な型付け

```php
<?php
declare(strict_types=1);

function add(int $a, int $b): int
{
    return $a + $b;
}
```

### Union型（PHP 8+）

```php
function process(string|int $value): string|null
{
    // ...
}
```

### Nullable型

```php
function findUser(int $id): ?User
{
    return $this->repository->find($id);
}
```

## エラーハンドリング

### 例外

```php
class ValidationException extends Exception
{
    public function __construct(
        private readonly array $errors,
        string $message = 'Validation failed'
    ) {
        parent::__construct($message);
    }

    public function getErrors(): array
    {
        return $this->errors;
    }
}

// 使用例
try {
    $this->validate($data);
} catch (ValidationException $e) {
    return response()->json([
        'errors' => $e->getErrors()
    ], 422);
}
```

### Result パターン

```php
readonly class Result
{
    private function __construct(
        public bool $success,
        public mixed $value = null,
        public ?string $error = null
    ) {}

    public static function success(mixed $value): self
    {
        return new self(true, $value);
    }

    public static function failure(string $error): self
    {
        return new self(false, error: $error);
    }
}
```

## 配列操作

### array_map / array_filter

```php
// Good
$names = array_map(fn($user) => $user->getName(), $users);
$active = array_filter($users, fn($user) => $user->isActive());

// PHP 8.1+: アロー関数
$totals = array_map(
    fn(Order $order) => $order->getTotal(),
    $orders
);
```

### Collection（Laravel）

```php
$activeUsers = collect($users)
    ->filter(fn($user) => $user->isActive())
    ->map(fn($user) => $user->getName())
    ->toArray();
```

## 命名規則

| 要素 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `UserService` |
| メソッド | camelCase | `getUserById` |
| 変数 | camelCase | `$userName` |
| 定数 | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |

## 禁止事項

- ❌ `global`キーワード
- ❌ `extract()`関数
- ❌ `eval()`関数
- ❌ 短いタグ `<?`
- ❌ 型宣言なしの関数

## 推奨事項

- ✅ `declare(strict_types=1);`
- ✅ readonly クラス/プロパティ（PHP 8.1+）
- ✅ コンストラクタプロモーション
- ✅ 名前付き引数
