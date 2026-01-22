# TODO: スタート画面 (start-screen)

## ストーリー概要

ユーザーとして、アプリを開いたときに最初に表示されるスタート画面がほしい。
タイトル、説明文、「占う」ボタンがあり、ボタンをクリックすると占いが始まるようにしたい。

## タスクリスト

### Task 1: StartScreenコンポーネントの基本構造作成

**分類**: E2E（UIコンポーネント、視覚的確認が必要）

- [ ] [E2E][IMPL] StartScreenコンポーネントの基本構造を実装
  - src/components/StartScreen/ディレクトリを作成
  - StartScreen.tsxに基本構造を実装（h1タイトル、p説明文、buttonボタン）
  - Tailwind CSSでスタイリング（中央配置、余白、フォントサイズ）
  - index.tsでエクスポート
- [ ] [E2E][AUTO] agent-browserでコンポーネント表示を検証
  - タイトル、説明文、ボタンの表示を確認
  - レイアウトが中央配置されているか確認
- [ ] [E2E][CHECK] lint/format/build

**受入条件**: コンポーネントが単独でレンダリングでき、タイトル・説明文・ボタンが表示される

---

### Task 2: useTarotStateフックとの統合

**分類**: TDD（状態管理ロジック、入出力が明確）

- [ ] [TDD][RED] useTarotStateフックとの統合テスト作成
  - StartScreen.test.tsx作成
  - ボタンクリック時にstartReading関数が呼ばれることを検証
  - state === 'idle'のときのみ表示されることを検証
- [ ] [TDD][GREEN] useTarotStateフックとの統合実装
  - useTarotStateフックをインポート
  - startReading関数を取得
  - ボタンのonClickイベントにstartReading関数を接続
  - state === 'idle'のときのみコンポーネントを表示する条件分岐を実装
- [ ] [TDD][REFACTOR] コードの品質改善
  - 重複排除
  - 命名改善
- [ ] [TDD][REVIEW] セルフレビュー
  - テストに過剰適合していないか確認
  - エッジケース（state変化、複数回クリック等）を考慮したか確認
- [ ] [TDD][CHECK] lint/format/build

**受入条件**: ボタンクリック時にstartReading()が呼ばれ、stateが'idle'から'selecting'に遷移する

---

### Task 3: レスポンシブデザインの実装

**分類**: E2E（視覚的確認が必要、デザイン仕様との一致）

- [ ] [E2E][IMPL] レスポンシブデザインを実装
  - モバイル(375px): フォントサイズ小、余白小、1カラム
  - タブレット(768px): フォントサイズ中、余白中
  - デスクトップ(1024px): フォントサイズ大、余白大、最大幅設定
  - Tailwind CSSのブレイクポイント（sm:, md:, lg:）を使用
- [ ] [E2E][AUTO] agent-browserでレスポンシブ表示を検証
  - モバイルサイズ(375x667)でスクリーンショット取得
  - タブレットサイズ(768x1024)でスクリーンショット取得
  - デスクトップサイズ(1024x768)でスクリーンショット取得
  - 各サイズで適切なレイアウトか確認
- [ ] [E2E][CHECK] lint/format/build

**受入条件**: 各デバイスサイズで視覚的に適切に表示される

---

### Task 4: アクセシビリティ対応

**分類**: E2E（キーボード操作、フォーカス状態の視覚的確認が必要）

- [ ] [E2E][IMPL] アクセシビリティ対応を実装
  - セマンティックHTML要素を使用（h1, p, button）
  - ボタンにaria-label属性を追加（必要に応じて）
  - フォーカス状態のスタイリング（focus-visible）
  - キーボード操作の確認（Tab, Enter, Space）
- [ ] [E2E][AUTO] agent-browserでアクセシビリティを検証
  - read_page({ filter: "interactive" })でインタラクティブ要素を取得
  - ボタンに適切なラベルがあるか確認
  - キーボード操作（Tab, Enter）をシミュレート
- [ ] [E2E][CHECK] lint/format/build

**受入条件**: キーボードでボタンにフォーカスでき、Enter/Spaceで操作可能。適切なaria属性が設定されている

---

### Task 5: StartScreen E2E検証

**分類**: E2E（総合的な動作確認、視覚的検証）

- [ ] [E2E][IMPL] 開発サーバー起動（必要に応じて）
- [ ] [E2E][AUTO] agent-browserで総合検証
  - tabs_context_mcp でタブ情報取得
  - navigate で localhost:3000 に遷移
  - find で「占う」ボタンを検索
  - screenshot で初期表示を確認
  - computer({ action: "left_click" }) でボタンクリック
  - read_page で状態遷移後の画面を確認
  - レスポンシブ表示を確認（3ブレイクポイント）
- [ ] [E2E][CHECK] lint/format/build

**受入条件**: すべての要素が表示され、ボタンクリックで状態が遷移することが確認できる

---

## 依存関係

- Story 6 (state-management): useTarotStateフックが実装済みであること

## 技術スタック

- React + TypeScript
- Tailwind CSS
- Vitest + React Testing Library
- agent-browser（MCP版 Claude in Chrome）

## 完了条件

- [ ] すべてのタスクが完了
- [ ] すべてのテストがパス
- [ ] すべてのE2E検証がパス
- [ ] lint/format/buildエラーなし
- [ ] 受入条件がすべて満たされている
