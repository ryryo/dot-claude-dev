---
description: PHPテスト規約。Pestを使用。
globs:
  - "**/tests/**/*.php"
  - "**/*Test.php"
---

# PHPテスト規約

## テストフレームワーク

**Pest** を使用。

## テストファイル配置（tests/ディレクトリ）

テストファイルは**tests/ディレクトリ**に配置し、app/の構造をミラーリングする。

```
app/
├── Services/
│   └── UserService.php
├── Models/
│   └── User.php
└── Http/
    └── Controllers/
        └── UserController.php

tests/
├── Unit/                              ← 単体テスト
│   ├── Services/
│   │   └── UserServiceTest.php        ← app構造をミラー
│   └── Models/
│       └── UserTest.php
└── Feature/                           ← 結合テスト
    └── Http/
        └── Controllers/
            └── UserControllerTest.php
```

### 命名規則

| パターン | 例 | 配置 |
|----------|-----|------|
| `*Test.php` | `UserServiceTest.php` | `tests/Unit/Services/` |
| `*Test.php` | `UserControllerTest.php` | `tests/Feature/Http/Controllers/` |

### テスト種別

| ディレクトリ | 用途 |
|-------------|------|
| `tests/Unit/` | 単一クラス/メソッドのテスト、外部依存はモック |
| `tests/Feature/` | 複数クラスの結合、HTTP/DBを含むテスト |

## テスト構造

```php
<?php

use App\Services\UserService;

describe('UserService', function () {
    beforeEach(function () {
        $this->repository = mock(UserRepository::class);
        $this->service = new UserService($this->repository);
    });

    it('finds user by id', function () {
        // Given
        $user = new User(1, 'John', 'john@example.com');
        $this->repository->shouldReceive('find')->with(1)->andReturn($user);

        // When
        $result = $this->service->findById(1);

        // Then
        expect($result)->toBe($user);
    });

    it('returns null when user not found', function () {
        $this->repository->shouldReceive('find')->andReturn(null);

        $result = $this->service->findById(999);

        expect($result)->toBeNull();
    });
});
```

## アサーション

```php
expect($value)->toBe($expected);              // 厳密等価
expect($value)->toEqual($expected);           // 構造等価
expect($value)->toBeTrue();                   // 真値
expect($value)->toBeFalse();                  // 偽値
expect($value)->toBeNull();                   // null
expect($array)->toHaveCount(3);               // 配列長
expect($array)->toContain($item);             // 配列に含む
expect($object)->toBeInstanceOf(User::class); // インスタンス
expect($string)->toMatch('/pattern/');        // 正規表現
```

## モック（Mockery）

```php
$mock = Mockery::mock(Repository::class);
$mock->shouldReceive('save')
    ->once()
    ->with($entity)
    ->andReturn(true);
```

## データプロバイダー

```php
it('validates email format', function (string $email, bool $expected) {
    $result = validateEmail($email);
    expect($result)->toBe($expected);
})->with([
    ['user@example.com', true],
    ['invalid', false],
    ['', false],
]);
```

## 禁止事項

- ❌ テスト間の状態共有
- ❌ 実際のDB/外部APIへの接続（Unitテスト）
- ❌ 非決定的なテスト（日時依存など）

## 推奨事項

- ✅ テスト名は動作を説明
- ✅ AAA (Arrange-Act-Assert) パターン
- ✅ 1テスト1アサーション（原則）
