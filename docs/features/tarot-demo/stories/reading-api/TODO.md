# TODO: 運勢メッセージ生成API (reading-api)

## Story 4: 運勢メッセージ生成API

バックエンドとして、引いたカードに応じた意味と総合的なアドバイスをAPIで返す。
ポジションに応じた解釈も付ける。

---

## Task 1: タロットカードデータ型定義

カード情報（ID、名前、意味、正位置/逆位置）を表すTypeScript型を定義する。

- [ ] [TASK][EXEC] Card型、MajorArcana型、MinorArcana型の定義を作成
- [ ] [TASK][VERIFY] 型定義が正しくエクスポートされていることを確認

---

## Task 2: カードマスターデータ作成

78枚のタロットカードのマスターデータ（ID、名前、意味）を定義する。

- [ ] [TASK][EXEC] メジャーアルカナ22枚のデータを定義
- [ ] [TASK][EXEC] マイナーアルカナ56枚のデータを定義（4スート×14枚）
- [ ] [TASK][VERIFY] データファイルが正しく読み込めることを確認

---

## Task 3: カードIDからカード情報を取得する関数

カードIDを受け取り、対応するカード情報を返す関数を実装する。

- [ ] [TDD][RED] getCardByIdのテスト作成
  - 有効なカードIDで正しいカード情報を返す
  - 存在しないカードIDでnullを返す
  - 型安全である
- [ ] [TDD][GREEN] getCardById関数の実装
- [ ] [TDD][REFACTOR] コードの重複排除と命名改善
- [ ] [TDD][REVIEW] セルフレビュー（過剰適合・抜け道チェック）
- [ ] [TDD][CHECK] lint/format/build

---

## Task 4: ポジション別解釈生成ロジック

カードとポジション（過去・現在・未来など）から、ポジション別の解釈メッセージを生成する関数を実装する。

- [ ] [TDD][RED] generatePositionInterpretationのテスト作成
  - ポジション（past/present/future）に応じた解釈を生成
  - カードの意味とポジションを組み合わせた自然な日本語メッセージを生成
  - 未定義のポジションでエラーを返す
- [ ] [TDD][GREEN] generatePositionInterpretation関数の実装
- [ ] [TDD][REFACTOR] テンプレートロジックの整理
- [ ] [TDD][REVIEW] セルフレビュー（過剰適合・抜け道チェック）
- [ ] [TDD][CHECK] lint/format/build

---

## Task 5: 総合アドバイス生成ロジック

複数カードの組み合わせから総合的なアドバイスメッセージを生成する関数を実装する。

- [ ] [TDD][RED] generateOverallAdviceのテスト作成
  - 1枚のカードから総合アドバイスを生成
  - 3枚のカードから総合アドバイスを生成
  - 空配列でエラーを返す
- [ ] [TDD][GREEN] generateOverallAdvice関数の実装
- [ ] [TDD][REFACTOR] メッセージ生成ロジックの改善
- [ ] [TDD][REVIEW] セルフレビュー（過剰適合・抜け道チェック）
- [ ] [TDD][CHECK] lint/format/build

---

## Task 6: リクエストバリデーション関数

APIリクエストのバリデーション（カードID、ポジション）をZodスキーマで実装する。

- [ ] [TDD][RED] ReadingRequestスキーマのテスト作成
  - 正しい形式のリクエストで成功
  - 不正なカードID形式で失敗
  - 不正なポジションで失敗
  - 必須フィールド欠如で失敗
- [ ] [TDD][GREEN] ReadingRequestスキーマの実装
- [ ] [TDD][REFACTOR] スキーマ定義の整理
- [ ] [TDD][REVIEW] セルフレビュー（過剰適合・抜け道チェック）
- [ ] [TDD][CHECK] lint/format/build

---

## Task 7: 運勢メッセージ生成APIエンドポイント実装

POST /api/tarot/reading エンドポイントを実装し、リクエストを処理してレスポンスを返す。

- [ ] [TDD][RED] APIハンドラー関数のテスト作成
  - 正常なリクエストで200とデータを返す
  - バリデーションエラーで400を返す
  - カード取得失敗で404を返す
- [ ] [TDD][GREEN] APIハンドラー関数の実装
- [ ] [TDD][REFACTOR] エラーハンドリングの整理
- [ ] [TDD][REVIEW] セルフレビュー（過剰適合・抜け道チェック）
- [ ] [TDD][CHECK] lint/format/build

---

## Task 8: API統合テスト（E2E）

実際のHTTPリクエストでAPIエンドポイントをテストする。

- [ ] [E2E][IMPL] 統合テストスクリプト作成
  - 開発サーバーの起動
  - 正常系のHTTPリクエスト送信
  - 異常系のHTTPリクエスト送信
- [ ] [E2E][AUTO] HTTPクライアントで実際にリクエストを送信して動作確認
  - 正常系: 200 OKとデータが返る
  - 不正なカードID: 400 Bad Request
  - 不正なポジション: 400 Bad Request
  - 空のリクエスト: 400 Bad Request
- [ ] [E2E][CHECK] lint/format/build

---

## タスク分類サマリー

- **TASK**: 2タスク（型定義、データ作成）
- **TDD**: 5タスク（ロジック関数、バリデーション、APIハンドラー）
- **E2E**: 1タスク（統合テスト）

**合計**: 8タスク
