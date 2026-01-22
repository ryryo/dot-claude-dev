# TODO: result-screen

## Story
ユーザーとして、占い結果として各カードの名前・画像・意味が表示されてほしい。正位置/逆位置も明示して、総合運勢のまとめと「もう一度占う」ボタンも欲しい。

## 受入条件
- [AC1] 3枚のカードそれぞれについて、カード名・画像・正位置または逆位置・意味が表示されること
- [AC2] 総合運勢のまとめテキストが表示されること
- [AC3] 「もう一度占う」ボタンがあり、クリックでカード選択画面に戻れること
- [AC4] モバイル・タブレット・デスクトップで適切に表示されること
- [AC5] スクリーンリーダーでカード情報と総合運勢が読み上げられること
- [AC6] キーボード操作で「もう一度占う」ボタンにフォーカスし、Enterで実行できること

---

## タスク

### 1. ResultCard コンポーネント作成

- [ ] [E2E][IMPL] ResultCardコンポーネント実装
  - Props: cardName, imageUrl, isReversed, meaning
  - 正位置/逆位置バッジ表示
  - カード画像表示（逆位置は180度回転）
  - 意味テキスト表示
  - レスポンシブデザイン
- [ ] [E2E][AUTO] ResultCard agent-browser検証
  - カード名・画像・正逆・意味の表示確認
  - 正位置/逆位置でバッジ表示の違いを確認
  - 逆位置で画像が180度回転することを確認
  - モバイル・デスクトップでレスポンシブ確認
- [ ] [E2E][CHECK] lint/format/build

### 2. 総合運勢生成ロジック作成

- [ ] [TDD][RED] generateFortuneSummary のテスト作成
  - 正位置が多い場合のテスト
  - 逆位置が多い場合のテスト
  - 正逆が混在する場合のテスト
  - 空データ・不正データのテスト
- [ ] [TDD][GREEN] generateFortuneSummary の実装
- [ ] [TDD][REFACTOR] generateFortuneSummary のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
  - テストケース以外でも動作するか
  - エッジケース考慮済みか
- [ ] [TDD][CHECK] lint/format/build

### 3. TarotResult コンポーネント作成

- [ ] [E2E][IMPL] TarotResultコンポーネント実装
  - Props: selectedCards, onRetry
  - 3枚のResultCardを表示
  - 総合運勢を表示（generateFortuneSummary使用）
  - 「もう一度占う」ボタン配置
  - レスポンシブレイアウト（モバイル: 縦、デスクトップ: 横）
  - アクセシビリティ対応（aria-label, role等）
- [ ] [E2E][AUTO] TarotResult agent-browser検証
  - 3枚のカード情報が正しく表示されることを確認
  - 総合運勢が表示されることを確認
  - 「もう一度占う」ボタンが動作することを確認
  - モバイル・デスクトップでレスポンシブ表示確認
  - キーボード操作でボタンにフォーカス・実行できることを確認
  - スクリーンリーダーでカード情報と総合運勢が読み上げられることを確認
- [ ] [E2E][CHECK] lint/format/build

---

## 完了条件
- すべてのタスクが完了
- すべての受入条件を満たす
- E2E検証が成功
- TDDサイクルが完了
- lint/format/buildエラーなし
