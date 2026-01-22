# TODO: Story 11 - メインアプリ統合 (app-integration)

## 概要
すべてのコンポーネントとロジックを統合したメインアプリケーションを実装する。
状態に応じて適切な画面（スタート画面、カード表示、結果画面）を表示し、ユーザーが占いを楽しめるようにする。

## 前提条件
- Story 5: useTarotReading（API呼び出し）が完了していること
- Story 6: useTarotState（状態管理）が完了していること
- Story 7: CardFlipAnimation（カードフリップ）が完了していること
- Story 8: SpreadLayout（3枚レイアウト）が完了していること
- Story 9: ResultScreen（結果画面）が完了していること
- Story 10: StartScreen（スタート画面）が完了していること

---

## タスクリスト

### 1. アプリケーション構造設計

- [ ] [E2E][IMPL] App.tsx（またはTarotApp.tsx）のコンポーネント構造設計
  - 必要なコンポーネントのimport（StartScreen、SpreadLayout、ResultScreen等）
  - 必要なフックのimport（useTarotState、useTarotReading）
  - Props型定義
  - 基本的なJSX構造の作成

- [ ] [E2E][AUTO] App.tsx構造のagent-browser検証
  - ファイルが作成され、TypeScriptエラーがないことを確認
  - ページが読み込まれることを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 2. 状態管理とAPI呼び出しの統合

- [ ] [TDD][RED] 状態管理フックの統合テスト作成
  - useTarotStateフックが正しく呼び出されることをテスト
  - 必要な状態と関数が取得できることをテスト

- [ ] [TDD][GREEN] 状態管理フックの統合実装
  - useTarotStateフックを呼び出し
  - state、selectedCards、setSelectedCards、resetを取得

- [ ] [TDD][REFACTOR] 状態管理フックの統合リファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [TDD][RED] API呼び出しフックの統合テスト作成
  - useTarotReadingフックが正しく呼び出されることをテスト
  - reading、loading、error、fetchReadingが取得できることをテスト

- [ ] [TDD][GREEN] API呼び出しフックの統合実装
  - useTarotReadingフックを呼び出し
  - エラーハンドリングロジックの実装

- [ ] [TDD][REFACTOR] API呼び出しフックの統合リファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

---

### 3. StartScreen統合とカードドロー処理

- [ ] [TDD][RED] カードドロー処理のテスト作成
  - onStartハンドラーが3枚のランダムカードを選択することをテスト
  - 状態がflippingに遷移することをテスト

- [ ] [TDD][GREEN] カードドロー処理の実装
  - onStartハンドラーを実装
  - 3枚のランダムカード選択ロジック
  - setSelectedCardsで状態に保存
  - 状態遷移処理

- [ ] [TDD][REFACTOR] カードドロー処理のリファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [E2E][IMPL] StartScreen統合UI実装
  - state === 'idle'の条件でStartScreenを表示
  - onStartハンドラーをStartScreenに渡す

- [ ] [E2E][AUTO] StartScreen統合のagent-browser検証
  - idleステートでStartScreenが表示されることを確認
  - 「占いを始める」ボタンクリックでカードドロー処理が実行されることを確認
  - 状態がflippingに遷移することを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 4. SpreadLayout統合とカードフリップ表示

- [ ] [TDD][RED] フリップ完了検知のテスト作成
  - すべてのカードのフリップ完了を検知できることをテスト
  - フリップ完了後、次の処理に進むことをテスト

- [ ] [TDD][GREEN] フリップ完了検知の実装
  - フリップ完了検知の仕組みを実装
  - 完了後の処理トリガー実装

- [ ] [TDD][REFACTOR] フリップ完了検知のリファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [E2E][IMPL] SpreadLayout統合UI実装
  - state === 'flipping'の条件でSpreadLayoutを表示
  - selectedCardsをpropsとして渡す
  - CardFlipAnimationコンポーネントの統合確認

- [ ] [E2E][AUTO] SpreadLayout統合のagent-browser検証
  - flippingステートでSpreadLayoutが表示されることを確認
  - 3枚のカードがフリップアニメーション付きで表示されることを確認
  - すべてのカードのフリップ完了後、次の処理に進むことを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 5. API呼び出しトリガーとreading状態の管理

- [ ] [TDD][RED] API呼び出しトリガーのテスト作成
  - フリップ完了後、fetchReadingが呼び出されることをテスト
  - selectedCardsがパラメータとして渡されることをテスト
  - 状態がreadingに遷移することをテスト

- [ ] [TDD][GREEN] API呼び出しトリガーの実装
  - フリップ完了後のfetchReading呼び出し
  - パラメータの設定
  - 状態遷移処理

- [ ] [TDD][REFACTOR] API呼び出しトリガーのリファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [E2E][IMPL] reading状態のUI実装
  - API呼び出し中のローディング表示
  - 状態遷移の視覚的フィードバック

- [ ] [E2E][AUTO] reading状態のagent-browser検証
  - API呼び出し中、適切なローディング表示がされることを確認
  - API成功時、状態がresultに遷移することを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 6. ResultScreen統合と結果表示

- [ ] [TDD][RED] リセット処理のテスト作成
  - onResetハンドラーがreset関数を呼び出すことをテスト
  - 状態がidleにリセットされることをテスト

- [ ] [TDD][GREEN] リセット処理の実装
  - onResetハンドラーを実装
  - reset関数の呼び出し

- [ ] [TDD][REFACTOR] リセット処理のリファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [E2E][IMPL] ResultScreen統合UI実装
  - state === 'result'の条件でResultScreenを表示
  - readingとselectedCardsをpropsとして渡す
  - onResetハンドラーを渡す

- [ ] [E2E][AUTO] ResultScreen統合のagent-browser検証
  - resultステートでResultScreenが表示されることを確認
  - リーディング結果が正しく表示されることを確認
  - 「もう一度占う」ボタンクリックで初期状態に戻ることを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 7. エラーハンドリング

- [ ] [TDD][RED] エラーハンドリングのテスト作成
  - API失敗時、エラーメッセージが表示されることをテスト
  - 再試行ボタンが表示されることをテスト
  - 再試行ボタンクリックで再度API呼び出しが実行されることをテスト

- [ ] [TDD][GREEN] エラーハンドリングの実装
  - error状態のチェック
  - 再試行ハンドラーの実装
  - エラー状態のクリア処理

- [ ] [TDD][REFACTOR] エラーハンドリングのリファクタリング

- [ ] [TDD][REVIEW] セルフレビュー

- [ ] [TDD][CHECK] lint/format/build

- [ ] [E2E][IMPL] エラー画面UI実装
  - エラーメッセージの表示
  - 再試行ボタンの配置

- [ ] [E2E][AUTO] エラー画面のagent-browser検証
  - API失敗時、エラーメッセージが表示されることを確認
  - 再試行ボタンが表示され、機能することを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 8. ローディング状態の表示

- [ ] [E2E][IMPL] ローディング状態のUI実装
  - drawing状態のローディング表示
  - reading状態のローディング表示
  - ローディングインジケーターコンポーネントの実装または使用
  - ローディング中のユーザー操作制限

- [ ] [E2E][AUTO] ローディング状態のagent-browser検証
  - カードドロー中、ローディング表示がされることを確認
  - API呼び出し中、ローディング表示がされることを確認
  - ローディング中、ユーザーが誤操作できないことを確認

- [ ] [E2E][CHECK] lint/format/build

---

### 9. 統合テストとデバッグ

- [ ] [E2E][IMPL] 全フローの統合
  - すべてのコンポーネントとロジックの最終統合
  - 状態遷移フローの最適化

- [ ] [E2E][AUTO] 全フローのagent-browser検証
  - スタートから結果表示までの全フローをテスト
  - すべての状態遷移が正しく動作することを確認
  - エラーケースのテスト
  - リセット機能のテスト
  - レスポンシブ表示の確認

- [ ] [E2E][CHECK] 最終lint/format/build

---

## 完了条件
- [ ] すべてのコンポーネントが正しく統合されている
- [ ] 状態遷移が正しく動作する（idle → drawing → flipping → reading → result → idle）
- [ ] API呼び出しが正しく実行され、結果が表示される
- [ ] エラーハンドリングが適切に機能する
- [ ] ローディング状態が適切に表示される
- [ ] リセット機能が正しく動作する
- [ ] すべてのテストが通る
- [ ] TypeScriptエラーがない
- [ ] Lint/Formatエラーがない
- [ ] ブラウザで全フローがスムーズに動作する

## 備考
- 状態管理のフローが複雑なため、状態遷移図を参照しながら実装すること
- ユーザー体験を重視し、各状態遷移がスムーズに行われるよう注意すること
- すべてのコンポーネントとフックが既に実装されていることが前提
