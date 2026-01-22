# Tarot Demo - PHP Backend

## 環境要件

- PHP 8.1以上
- Composer

## セットアップ

### 依存パッケージのインストール

```bash
composer install
```

## 開発サーバーの起動

```bash
php -S localhost:8000 -t public
```

サーバーが起動したら、以下のURLにアクセスできます:

- ヘルスチェック: http://localhost:8000/api/health

## テストの実行

```bash
vendor/bin/pest
```

## プロジェクト構造

```
backend/
├── public/          # 公開ディレクトリ
│   └── index.php   # エントリーポイント
├── src/            # アプリケーションコード
│   └── Router.php  # ルーティングクラス
├── tests/          # テストコード
│   ├── Feature/    # 機能テスト
│   ├── Unit/       # ユニットテスト
│   └── Pest.php    # Pest設定
└── composer.json   # Composer設定
```
