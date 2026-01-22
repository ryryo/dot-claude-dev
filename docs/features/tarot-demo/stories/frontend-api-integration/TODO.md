# TODO: APIクライアント (frontend-api-integration)

## ストーリー概要

フロントエンドとして、バックエンドAPIを呼び出して占い結果を取得・管理したい。
エラーハンドリングとローディング状態も管理できるように。

## タスクリスト

### Task 1: Result型の定義

**分類**: TDD

**理由**: 入出力が明確（Result<T, E>型の定義）で、アサーションで検証可能なロジック層のタスク。success/failureの動作をユニットテストで検証できる。

- [ ] [TDD][RED] Result型の定義のテスト作成
  - Result<T, E>型の構造テスト
  - success()ヘルパーのテスト
  - failure()ヘルパーのテスト
  - isSuccess型ガードのテスト
  - isFailure型ガードのテスト
- [ ] [TDD][GREEN] Result型の定義の実装
  - Result<T, E>型の定義
  - success()関数の実装
  - failure()関数の実装
  - 型ガード関数の実装
- [ ] [TDD][REFACTOR] Result型の定義のリファクタリング
  - 型定義の整理
  - ドキュメントコメントの追加
- [ ] [TDD][REVIEW] セルフレビュー
  - 過剰適合チェック
  - エッジケース確認
- [ ] [TDD][CHECK] lint/format/build

---

### Task 2: API型定義の作成

**分類**: TDD

**理由**: Zodスキーマのバリデーション動作をユニットテストで検証可能。正常データ・異常データでのバリデーション結果を明確にアサートできる。

- [ ] [TDD][RED] API型定義の作成のテスト作成
  - TarotReadingRequestスキーマのバリデーションテスト（正常系）
  - TarotReadingRequestスキーマのバリデーションテスト（異常系）
  - TarotReadingResponseスキーマのバリデーションテスト（正常系）
  - TarotReadingResponseスキーマのバリデーションテスト（異常系）
  - APIErrorResponseスキーマのバリデーションテスト
- [ ] [TDD][GREEN] API型定義の作成の実装
  - TarotReadingRequest型とZodスキーマ定義
  - TarotReadingResponse型とZodスキーマ定義
  - APIErrorResponse型とZodスキーマ定義
- [ ] [TDD][REFACTOR] API型定義の作成のリファクタリング
  - スキーマの共通部分抽出
  - エラーメッセージの改善
- [ ] [TDD][REVIEW] セルフレビュー
  - バリデーションの抜け道チェック
  - 境界値の確認
- [ ] [TDD][CHECK] lint/format/build

---

### Task 3: HTTPクライアントの実装

**分類**: TDD

**理由**: HTTPクライアントの動作（fetchモック、エラーハンドリング、Zodバリデーション）はユニットテストで検証可能。入力（URL、リクエストボディ）と出力（Result型）が明確。

- [ ] [TDD][RED] HTTPクライアントの実装のテスト作成
  - post()メソッドの成功ケーステスト
  - HTTPエラー（4xx）のハンドリングテスト
  - HTTPエラー（5xx）のハンドリングテスト
  - ネットワークエラーのハンドリングテスト
  - Zodバリデーション失敗時のテスト
  - Content-Type設定のテスト
- [ ] [TDD][GREEN] HTTPクライアントの実装の実装
  - httpClient.post()の実装
  - fetchのラッパー実装
  - エラーハンドリングロジック
  - Zodバリデーション統合
- [ ] [TDD][REFACTOR] HTTPクライアントの実装のリファクタリング
  - エラーハンドリングの共通化
  - 型定義の整理
- [ ] [TDD][REVIEW] セルフレビュー
  - エラーケースの網羅性確認
  - モックの適切さ確認
- [ ] [TDD][CHECK] lint/format/build

---

### Task 4: 占い結果取得APIクライアントの実装

**分類**: TDD

**理由**: APIクライアント関数の動作をHTTPクライアントのモックで検証可能。入力（TarotReadingRequest）と出力（Result<TarotReadingResponse>）が明確。

- [ ] [TDD][RED] 占い結果取得APIクライアントの実装のテスト作成
  - fetchTarotReading()の成功ケーステスト
  - fetchTarotReading()のエラーケーステスト
  - 正しいエンドポイントを呼び出すテスト
  - 正しいリクエストボディを送信するテスト
- [ ] [TDD][GREEN] 占い結果取得APIクライアントの実装の実装
  - fetchTarotReading()関数の実装
  - エンドポイントURL構築
  - HTTPクライアント呼び出し
- [ ] [TDD][REFACTOR] 占い結果取得APIクライアントの実装のリファクタリング
  - エンドポイントパスの定数化
  - エラーメッセージの改善
- [ ] [TDD][REVIEW] セルフレビュー
  - リクエスト・レスポンス型の整合性確認
  - エラー伝播の適切さ確認
- [ ] [TDD][CHECK] lint/format/build

---

### Task 5: ローディング状態管理フックの実装

**分類**: TDD

**理由**: カスタムHooksの状態遷移（loading, error, data）はReact Testing Libraryでユニットテスト可能。renderHookを使って動作を検証できる。

- [ ] [TDD][RED] ローディング状態管理フックの実装のテスト作成
  - 初期状態のテスト（loading=false, data=null, error=null）
  - fetchReading()呼び出し中のloadingテスト
  - 成功時のdata設定テスト
  - エラー時のerror設定テスト
  - 複数回呼び出し時の状態リセットテスト
- [ ] [TDD][GREEN] ローディング状態管理フックの実装の実装
  - useTarotReading()フックの実装
  - loading状態管理
  - error状態管理
  - data状態管理
  - fetchReading()関数の実装
- [ ] [TDD][REFACTOR] ローディング状態管理フックの実装のリファクタリング
  - 状態更新ロジックの整理
  - useCallbackの適用
- [ ] [TDD][REVIEW] セルフレビュー
  - 状態遷移の網羅性確認
  - メモリリークの確認
- [ ] [TDD][CHECK] lint/format/build

---

### Task 6: 環境変数によるAPIベースURL設定

**分類**: TASK

**理由**: 設定ファイル（.env.example）の作成と環境変数の設定。テスト不要・UI検証不要な一回限りのセットアップタスク。

- [ ] [TASK][EXEC] 環境変数によるAPIベースURL設定実行
  - .env.exampleファイルの作成
  - VITE_API_BASE_URL変数の設定
  - デフォルト値の定義
  - config.tsファイルの作成（環境変数読み込み）
- [ ] [TASK][VERIFY] 環境変数によるAPIベースURL設定検証
  - .env.exampleファイルの存在確認
  - config.tsでの環境変数読み込み確認
  - デフォルト値のフォールバック確認

---

### Task 7: ローディングスピナーコンポーネント

**分類**: E2E

**理由**: UIコンポーネントの表示確認が必要。視覚的にスピナーが回転していることを確認する。

- [ ] [E2E][IMPL] ローディングスピナーコンポーネント実装
  - LoadingSpinner.tsxを作成
  - Tailwind CSSでスピナーアニメーション実装
  - サイズprops対応（sm, md, lg）
  - アクセシビリティ対応（aria-label）
- [ ] [E2E][AUTO] ローディングスピナーコンポーネントagent-browser検証
  - 開発サーバー起動
  - Storybookまたはテストページでスピナー表示確認
  - 各サイズでの表示確認
  - アニメーション動作確認
- [ ] [E2E][CHECK] lint/format/build

---

### Task 8: エラーメッセージコンポーネント

**分類**: E2E

**理由**: UIコンポーネントの表示確認が必要。エラーメッセージが適切に表示されることを視覚的に確認する。

- [ ] [E2E][IMPL] エラーメッセージコンポーネント実装
  - ErrorMessage.tsxを作成
  - エラーメッセージ表示UI
  - リトライボタン実装
  - Tailwind CSSでエラースタイル
  - アクセシビリティ対応（role="alert"）
- [ ] [E2E][AUTO] エラーメッセージコンポーネントagent-browser検証
  - 開発サーバー起動
  - エラーメッセージ表示確認
  - リトライボタンクリック動作確認
  - スクリーンリーダー対応確認
- [ ] [E2E][CHECK] lint/format/build

---

## 実装順序

1. Task 1: Result型の定義（基礎型）
2. Task 2: API型定義の作成（型とスキーマ）
3. Task 6: 環境変数によるAPIベースURL設定（環境設定）
4. Task 3: HTTPクライアントの実装（通信基盤）
5. Task 4: 占い結果取得APIクライアントの実装（APIロジック）
6. Task 5: ローディング状態管理フックの実装（Hooks層）
7. Task 7: ローディングスピナーコンポーネント（UI）
8. Task 8: エラーメッセージコンポーネント（UI）

## 分類サマリー

- **TDD**: 5タスク（Task 1, 2, 3, 4, 5）
- **E2E**: 2タスク（Task 7, 8）
- **TASK**: 1タスク（Task 6）

## 見積もり

- **総タスク数**: 6
- **複雑度**: 小4、中2
- **推定工数**: 中程度
