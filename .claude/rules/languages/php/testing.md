---
description: PHPテスト規約。PHPUnit/Pestを使用。
globs:
  - "**/tests/**/*.php"
  - "**/*Test.php"
---

# PHPテスト規約

## テストフレームワーク

PHPUnit または Pest を使用。

## PHPUnit テスト構造

```php
<?php

declare(strict_types=1);

namespace Tests\Unit;

use App\Services\UserService;
use App\Repositories\UserRepository;
use PHPUnit\Framework\TestCase;

class UserServiceTest extends TestCase
{
    private UserService $service;
    private UserRepository $repository;

    protected function setUp(): void
    {
        $this->repository = $this->createMock(UserRepository::class);
        $this->service = new UserService($this->repository);
    }

    public function testFindByIdReturnsUser(): void
    {
        // Given
        $expectedUser = new User(1, 'John', 'john@example.com');
        $this->repository
            ->expects($this->once())
            ->method('find')
            ->with(1)
            ->willReturn($expectedUser);

        // When
        $result = $this->service->findById(1);

        // Then
        $this->assertSame($expectedUser, $result);
    }

    public function testFindByIdReturnsNullWhenNotFound(): void
    {
        $this->repository
            ->method('find')
            ->willReturn(null);

        $result = $this->service->findById(999);

        $this->assertNull($result);
    }
}
```

## Pest テスト構造

```php
<?php

use App\Services\UserService;

describe('UserService', function () {
    beforeEach(function () {
        $this->repository = mock(UserRepository::class);
        $this->service = new UserService($this->repository);
    });

    it('finds user by id', function () {
        $user = new User(1, 'John', 'john@example.com');
        $this->repository->shouldReceive('find')->with(1)->andReturn($user);

        $result = $this->service->findById(1);

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
// PHPUnit
$this->assertEquals($expected, $actual);
$this->assertSame($expected, $actual);
$this->assertTrue($condition);
$this->assertNull($value);
$this->assertCount(3, $array);
$this->assertContains($item, $array);
$this->assertInstanceOf(User::class, $object);

// Pest
expect($value)->toBe($expected);
expect($value)->toEqual($expected);
expect($value)->toBeTrue();
expect($value)->toBeNull();
expect($array)->toHaveCount(3);
expect($array)->toContain($item);
expect($object)->toBeInstanceOf(User::class);
```

## モック

### PHPUnit

```php
$mock = $this->createMock(Repository::class);
$mock->expects($this->once())
    ->method('save')
    ->with($this->equalTo($entity))
    ->willReturn(true);
```

### Mockery

```php
$mock = Mockery::mock(Repository::class);
$mock->shouldReceive('save')
    ->once()
    ->with($entity)
    ->andReturn(true);
```

## データプロバイダー

```php
/**
 * @dataProvider emailProvider
 */
public function testValidateEmail(string $email, bool $expected): void
{
    $result = $this->validator->validateEmail($email);
    $this->assertSame($expected, $result);
}

public static function emailProvider(): array
{
    return [
        'valid email' => ['user@example.com', true],
        'invalid email' => ['invalid', false],
        'empty string' => ['', false],
    ];
}
```

## 禁止事項

- ❌ テスト間の状態共有
- ❌ 実際のDB/外部APIへの接続（Unitテスト）
- ❌ 非決定的なテスト（日時依存など）

## 推奨事項

- ✅ テスト名は動作を説明
- ✅ AAA (Arrange-Act-Assert) パターン
- ✅ 1テスト1アサーション（原則）
