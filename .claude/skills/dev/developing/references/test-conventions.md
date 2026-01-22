# テスト規約

## 概要

このドキュメントは、プロジェクトにおけるテストファイルの命名規則、配置場所、およびテストフレームワークの選定基準を定義します。

## テストフレームワーク

| 言語/FW | テストフレームワーク | 理由 |
|---------|---------------------|------|
| **TypeScript/JavaScript** | Vitest | 高速、ESM/TypeScriptネイティブ対応、Vite統合 |
| **React** | Vitest + React Testing Library | ユーザー視点のテスト、アクセシビリティ重視 |
| **PHP** | Pest | describe/it/expect構文でVitest/Jestと統一、モダンDX |

## テストファイル配置規約

### TypeScript / React（コロケーション）

テストファイルは対象ファイルと**同じディレクトリ**に配置する。

```
src/
├── components/
│   ├── Button.tsx
│   ├── Button.test.tsx      ← 同じ場所
│   └── Button.module.css
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts      ← 同じ場所
├── utils/
│   ├── validation.ts
│   └── validation.test.ts   ← 同じ場所
└── services/
    ├── api.ts
    └── api.test.ts          ← 同じ場所
```

**理由:**
- Vite/Vitestエコシステムの標準
- ファイル間の移動が少なく開発効率が高い
- リファクタリング時にテストを忘れにくい

### PHP（tests/ディレクトリ）

テストファイルは**tests/ディレクトリ**に配置し、srcの構造をミラーリングする。

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
├── Unit/
│   ├── Services/
│   │   └── UserServiceTest.php    ← src構造をミラー
│   └── Models/
│       └── UserTest.php
└── Feature/
    └── Http/
        └── Controllers/
            └── UserControllerTest.php
```

**理由:**
- PSR-4オートローディングとの整合性
- Pest/PHPUnitの標準構成
- 本番コードからの自然な分離

## テストファイル命名規則

### TypeScript / JavaScript / React

| パターン | 例 |
|----------|-----|
| `*.test.ts` | `validation.test.ts` |
| `*.test.tsx` | `Button.test.tsx` |
| `*.spec.ts` | `api.spec.ts` |
| `*.spec.tsx` | `Modal.spec.tsx` |

**推奨:** `.test.ts` / `.test.tsx` を優先使用（Vitestのデフォルト）

### PHP

| パターン | 例 |
|----------|-----|
| `*Test.php` | `UserServiceTest.php` |

**配置:** `tests/Unit/` または `tests/Feature/`

## テスト種別

### Unit（単体テスト）

- 単一の関数/メソッド/コンポーネントをテスト
- 外部依存はモック化
- 高速に実行可能

```
tests/Unit/           # PHP
src/**/*.test.ts      # TypeScript（コロケーション）
```

### Feature / Integration（結合テスト）

- 複数のコンポーネント/サービスの連携をテスト
- 一部の外部依存を使用

```
tests/Feature/        # PHP
src/**/*.integration.test.ts  # TypeScript
```

### E2E（エンドツーエンドテスト）

- ユーザー操作フローをテスト
- agent-browserで視覚的検証

```
e2e/                  # 専用ディレクトリ
```

## TDDワークフローとの連携

テストファイルの命名規則に従うことで、TDDワークフロールールが自動適用されます。

| glob パターン | 適用ルール |
|---------------|-----------|
| `**/*.test.ts`, `**/*.spec.ts` | `tdd-workflow.md` |
| `**/*.test.tsx`, `**/*.spec.tsx` | `tdd-workflow.md` + `react/testing.md` |
| `**/tests/**/*.php`, `**/*Test.php` | `tdd-workflow.md` + `php/testing.md` |

## vitest.config.ts 推奨設定

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // コロケーションパターンに対応
    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    // テスト環境
    environment: 'jsdom',

    // グローバルAPI（describe, it, expect）
    globals: true,

    // セットアップファイル
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

## pest.php 推奨設定

```php
<?php

uses(Tests\TestCase::class)->in('Feature');
uses(Tests\TestCase::class)->in('Unit');

// describe/it/expect構文を有効化
expect()->extend('toBeOne', function () {
    return $this->toBe(1);
});
```

## 関連ドキュメント

- [TDDワークフロー](./tdd-flow.md)
- [TypeScriptテスト規約](../../../rules/languages/typescript/testing.md)
- [Reactテスト規約](../../../rules/languages/react/testing.md)
- [PHPテスト規約](../../../rules/languages/php/testing.md)
