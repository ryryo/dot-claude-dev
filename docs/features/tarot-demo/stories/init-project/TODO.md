# TODO - Story: tarot-demo-app 環境構築・連携テスト

## フェーズ1: PHPバックエンド環境構築

### TASKタスク

- [x] [TASK][EXEC] PHPプロジェクト初期化
  - `demo/tarot/backend/`にPHPプロジェクトを初期化
  - `composer.json`を作成し、PSR-12準拠の基本設定を含める
  - ディレクトリ構造（`src/`, `tests/`, `public/`）を作成
- [x] [TASK][VERIFY] PHPプロジェクト初期化の確認
  - `composer.json`が存在し、プロジェクト構造が正しいか確認

- [x] [TASK][EXEC] Pestテストフレームワーク導入
  - Pestとその依存パッケージをインストール
  - `pest.php`設定ファイルを作成
  - テストディレクトリをセットアップ
  - サンプルテストを作成（`tests/Pest.php`, `tests/ExampleTest.php`）
- [x] [TASK][VERIFY] Pestテストフレームワーク導入の確認
  - `vendor/bin/pest`コマンドでサンプルテストが成功するか確認

- [ ] [TASK][EXEC] PHPバックエンド基本設定
  - エントリーポイント（`public/index.php`）を作成
  - 基本的なルーティングとCORS設定を追加
  - 基本Router実装（`src/Router.php`）を作成
- [ ] [TASK][VERIFY] PHPバックエンド基本設定の確認
  - 必要なファイルが生成されたか確認

- [ ] [TASK][EXEC] PHP開発サーバー起動確認
  - PHP組み込みサーバーを起動
  - ヘルスチェックエンドポイント（`/api/health`）にアクセス
  - 正常なレスポンスが返されることを確認
- [ ] [TASK][VERIFY] PHP開発サーバー起動確認の検証
  - 起動コマンドをREADMEに記載
  - サーバー停止

### TDDタスク

- [ ] [TDD][RED] ヘルスチェックエンドポイント実装のテスト作成
  - `tests/Feature/HealthCheckTest.php`を作成
  - `/api/health`エンドポイントが存在するか
  - ステータスコード200が返されるか
  - レスポンスボディに`status: ok`が含まれるか
- [ ] [TDD][GREEN] ヘルスチェックエンドポイント実装
  - テストを通す最小限の実装
  - `src/Controllers/HealthCheckController.php`を作成
  - ルーティングに追加
- [ ] [TDD][REFACTOR] ヘルスチェックエンドポイント実装のリファクタリング
  - コードの重複排除
  - 命名改善
  - 複雑度低減
- [ ] [TDD][REVIEW] ヘルスチェックエンドポイント実装のセルフレビュー
  - テストが成功しているか再確認
  - PSR-12準拠か確認
- [ ] [TDD][CHECK] ヘルスチェックエンドポイント実装のlint/format/build確認
  - Pestでテスト実行
  - PHPコードのチェック

---

## フェーズ2: Reactフロントエンド環境構築

### TASKタスク

- [ ] [TASK][EXEC] Reactプロジェクト初期化
  - `demo/tarot/frontend/`にVite + React + TypeScriptプロジェクトを初期化
  - `npm create vite@latest`コマンドを実行
  - 基本的なファイル構造を生成
- [ ] [TASK][VERIFY] Reactプロジェクト初期化の確認
  - `package.json`, `vite.config.ts`, `tsconfig.json`が生成されたか確認
  - 必要なディレクトリが作成されたか確認

- [ ] [TASK][EXEC] Vitestテストフレームワーク導入
  - Vitest、React Testing Library、@testing-library/user-eventをインストール
  - `vitest.config.ts`を設定
  - サンプルテストを作成（`src/App.test.tsx`）
- [ ] [TASK][VERIFY] Vitestテストフレームワーク導入の確認
  - `npm test`コマンドでサンプルテストが成功するか確認

- [ ] [TASK][EXEC] Tailwind CSS導入
  - Tailwind CSS、PostCSS、Autoprefixerをインストール
  - `tailwind.config.js`を作成
  - `postcss.config.js`を作成
  - `src/index.css`にTailwindディレクティブを追加
- [ ] [TASK][VERIFY] Tailwind CSS導入の確認
  - Tailwindの設定ファイルが正しく生成されたか確認
  - `src/index.css`が更新されたか確認

- [ ] [TASK][EXEC] React開発サーバー起動確認
  - `npm run dev`コマンドで開発サーバーを起動
  - ブラウザでアクセスして基本的なページが表示されるか確認
- [ ] [TASK][VERIFY] React開発サーバー起動確認の検証
  - 起動コマンドをREADMEに記載
  - サーバー停止

### E2Eタスク

- [ ] [E2E][IMPL] Tailwind CSS動作確認UI実装
  - `src/App.tsx`にTailwindクラスを適用したサンプルコンポーネントを作成
  - 複数のスタイリング要素を含める（色、スペーシング、レスポンシブ等）
- [ ] [E2E][AUTO] Tailwind CSS動作確認agent-browser検証
  - タブコンテキスト取得
  - `http://localhost:5173`にアクセス
  - Tailwindクラスが正しく適用されているか確認
  - レスポンシブ表示を確認（モバイル・タブレット・デスクトップ）
  - スクリーンショット取得
- [ ] [E2E][CHECK] Tailwind CSS動作確認のlint/format/build確認
  - `npm run build`でビルド成功を確認
  - ESLint実行

---

## フェーズ3: フロントエンド・バックエンド連携

### TDDタスク

- [ ] [TDD][RED] APIクライアント実装のテスト作成
  - `src/lib/__tests__/api.test.ts`を作成
  - APIクライアントが正しくリクエストを送信するか
  - レスポンスを正しく解析するか
  - エラーハンドリングが正しく動作するか
- [ ] [TDD][GREEN] APIクライアント実装
  - `src/lib/api.ts`を作成
  - fetchラッパー関数を実装
  - テストを通す最小限の実装
- [ ] [TDD][REFACTOR] APIクライアント実装のリファクタリング
  - エラーハンドリング改善
  - コード整理
  - 型定義改善
- [ ] [TDD][REVIEW] APIクライアント実装のセルフレビュー
  - テストが成功しているか再確認
  - TypeScriptの型安全性を確認
- [ ] [TDD][CHECK] APIクライアント実装のlint/format/build確認
  - Vitestでテスト実行
  - TypeScriptコンパイル確認

### E2Eタスク

- [ ] [E2E][IMPL] ヘルスチェックAPI呼び出し実装
  - `src/App.tsx`を更新
  - バックエンドの`/api/health`エンドポイントを呼び出す機能を実装
  - レスポンスを画面に表示
  - ローディング状態と エラー状態の表示を実装
- [ ] [E2E][AUTO] ヘルスチェックAPI呼び出し検証
  - タブコンテキスト取得
  - `http://localhost:5173`にアクセス
  - APIレスポンスが正しく表示されているか確認
  - ローディング状態が表示されるか確認
  - スクリーンショット取得
- [ ] [E2E][CHECK] ヘルスチェックAPI呼び出し実装のlint/format/build確認
  - `npm run build`でビルド成功を確認
  - ESLint実行

- [ ] [E2E][IMPL] フロントエンド→バックエンド連携確認
  - 両方のサーバーを起動
  - PHP: `php -S localhost:8000 -t public/`
  - React: `npm run dev`
- [ ] [E2E][AUTO] フロントエンド→バックエンド連携検証
  - タブコンテキスト取得
  - `http://localhost:5173`にアクセス
  - フロントエンドからバックエンドAPIが呼び出されているか確認
  - CORSエラーが発生していないか確認
  - APIレスポンスが正しく表示されているか確認
  - ネットワークタブでリクエスト・レスポンスを確認
  - スクリーンショット取得
- [ ] [E2E][CHECK] フロントエンド→バックエンド連携確認のlint/format/build確認
  - 両サーバー停止

---

## フェーズ4: ドキュメント整備

### TASKタスク

- [ ] [TASK][EXEC] README作成
  - `demo/tarot/README.md`を作成
  - プロジェクト概要
  - システムアーキテクチャ図（オプション）
  - 環境要件
  - 環境構築手順（PHP・Node.js設定）
  - 開発サーバー起動方法（バックエンド・フロントエンド）
  - テスト実行方法（Pest・Vitest）
  - プロジェクト構造
  - トラブルシューティング
- [ ] [TASK][VERIFY] README作成の確認
  - `demo/tarot/README.md`が作成されたか確認
  - 記載内容が完全か確認
  - フォーマットが適切か確認

---

## 共通

- [ ] [CHECK] 全体的なlint/format/build確認
  - PHPプロジェクト: Pestテスト実行、PHPチェック
  - Reactプロジェクト: Vitestテスト実行、ビルド確認、ESLint実行
  - 両環境でエラーがないか確認
