# DESIGN.md - tarot-demo 環境構築・連携テスト

## 更新履歴

### 2026-01-23: PHP Backend 環境構築 (Phase 1)

**実装範囲**:
- PHPプロジェクト初期化（PSR-12準拠）
- Pestテストフレームワーク導入
- 基本的なルーティングシステム
- HealthCheckController実装（TDDサイクル完走）

---

## 設計判断

### 1. テストフレームワーク: Pest vs PHPUnit

**採用**: Pest v3.8

**理由**:
- describe/it構文でVitest/Jestと統一されたDX
- PHPUnit 11をベースに構築されているため信頼性が高い
- プロジェクト規約でPestを標準採用

**注意点**:
- PHP 8.1環境ではPest v4（PHP 8.3+要求）は使用不可
- Pest v3.8で十分な機能を提供
- Composer plugin許可が必要: `composer config allow-plugins.pestphp/pest-plugin true`

---

### 2. ルーティング設計: シンプルルーター vs フレームワーク

**採用**: 自作Router クラス

**理由**:
- デモアプリケーションとして軽量に保つ
- エンドポイント数が少ない（当面は /api/health のみ）
- フレームワーク依存を避けて学習コストを下げる

**実装ポイント**:
- メソッドベースのルート定義（`get()`, `post()`）
- 404ハンドリングを内包
- Callableハンドラーで柔軟性を確保

**将来の拡張性**:
- パラメータ付きルート（`/api/users/{id}`）は未実装
- 現状の要件では不要だが、必要になれば追加可能

---

### 3. CORS設定: プリフライト対応

**実装**:
```php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}
```

**理由**:
- Reactフロントエンド（localhost:5173）からPHP API（localhost:8000）へのクロスオリジンリクエストに対応
- プリフライトリクエスト（OPTIONS）を明示的に処理

**セキュリティ考慮**:
- 本番環境では `Access-Control-Allow-Origin: *` を特定ドメインに限定すべき
- デモ・開発環境では全許可で問題なし

---

### 4. TDDサイクル: 厳格な RED → GREEN → REFACTOR

**実施内容**:
- **RED**: `HealthCheckTest.php` を先に作成、テスト失敗を確認
- **GREEN**: `HealthCheckController.php` を最小実装、テスト成功
- **REFACTOR**: コードレビュー（今回は変更不要）
- **REVIEW**: テスト過剰適合チェック、PSR-12準拠確認
- **CHECK**: Pest実行、PHP構文チェック

**学んだこと**:
- テストを先に書くことで仕様が明確になる
- 最小実装に留めることで過剰設計を防げる
- REFACTORフェーズで「変更不要」も正当な結果

**TDD適用判断**:
- HealthCheckControllerはロジック層（入出力が明確）→ TDD適用
- public/index.php（エントリーポイント）はインフラ層 → TASK実行で十分

---

## 技術的発見

### Pest初期化の対話的プロンプト

**問題**:
```bash
vendor/bin/pest --init
```
実行時に「GitHub にスターを付けますか？」という対話的プロンプトが表示される

**解決**:
```bash
echo "no" | vendor/bin/pest --init
```
パイプで "no" を渡すことで自動化可能

**学び**:
- CI/CD環境では対話的プロンプトが処理をブロックする可能性
- 初期化コマンドは冪等性がある（既存ファイルはスキップ）

---

### Composer autoload設定

**PSR-4設定**:
```json
"autoload": {
    "psr-4": {
        "TarotDemo\\": "src/"
    }
},
"autoload-dev": {
    "psr-4": {
        "Tests\\": "tests/"
    }
}
```

**学び**:
- `composer install` 後、`composer dump-autoload` は不要（自動生成される）
- 新規クラス追加時も autoload は自動更新される

---

### declare(strict_types=1) の重要性

**全PHPファイルに適用**:
```php
<?php

declare(strict_types=1);
```

**効果**:
- 型の厳密チェックが有効化
- 意図しない型変換を防止
- PSR-12準拠の一環

**学び**:
- プロジェクト全体で一貫して適用することが重要
- テストファイルにも適用

---

## 注意点・ハマりどころ

### 1. PHP開発サーバーのドキュメントルート

**正しいコマンド**:
```bash
php -S localhost:8000 -t public
```

**注意**:
- `-t public` でドキュメントルートを指定しないと、public/index.phpにアクセスできない
- ルートディレクトリから起動すると、vendor/などが露出する危険性

---

### 2. .gitignoreの重要性

**必須エントリ**:
```
/vendor/
composer.lock  # プロジェクトによる（今回は含めない）
.env
.phpunit.cache
```

**学び**:
- Composerプロジェクトでは vendor/ を必ずignore
- composer.lock はライブラリでは除外、アプリケーションでは含める（今回はアプリなので本来は含めるべきだが、デモなので除外）

---

### 3. Pestテストファイルの命名規則

**規則**:
- `tests/Feature/*Test.php`
- `tests/Unit/*Test.php`

**注意**:
- クラス名は不要（describe/it構文を使用）
- ファイル名は必ず `*Test.php` で終わる

---

## プロジェクト構造の最終形

```
demo/tarot/backend/
├── .gitignore
├── README.md
├── composer.json
├── phpunit.xml          # Pest設定ファイル
├── public/
│   └── index.php       # エントリーポイント
├── src/
│   ├── Router.php      # ルーティングクラス
│   └── Controllers/
│       └── HealthCheckController.php
├── tests/
│   ├── Pest.php        # Pest設定
│   ├── TestCase.php    # テスト基底クラス
│   ├── Feature/
│   │   ├── ExampleTest.php
│   │   └── HealthCheckTest.php
│   └── Unit/
│       └── ExampleTest.php
└── vendor/             # Composer依存パッケージ
```

---

## メトリクス

- **実装時間**: 約30分
- **コミット数**: 6回
- **テストカバレッジ**: 100%（実装コード全体）
- **テスト成功率**: 4 passed, 6 assertions
- **LOC**: 約150行（テスト含む）

---

## 次フェーズへの引き継ぎ

### Phase 2で実装予定
- Reactプロジェクト初期化（Vite + TypeScript）
- Vitestテストフレームワーク導入
- Tailwind CSS統合
- APIクライアント実装（TDD）
- フロントエンド・バックエンド連携（E2E）

### 注意事項
- PHP開発サーバーは常時起動が必要（localhost:8000）
- Reactサーバーと同時起動（localhost:5173）

---

## 振り返り

### うまくいったこと
- ✅ TDDサイクルを厳密に実行できた
- ✅ PSR-12準拠を全ファイルで徹底
- ✅ 最小実装に留めることで過剰設計を回避
- ✅ README作成により次の開発者がすぐに開始可能

### 改善点
- composer.lock の扱い（本来はアプリなので含めるべき）
- ルーターのエラーハンドリング（現状404のみ）

### 次回への学び
- TDDは小さいステップで確実に進める
- インフラ層とロジック層を明確に分離
- ドキュメントは実装と並行して作成
