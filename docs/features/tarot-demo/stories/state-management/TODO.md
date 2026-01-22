# TODO: Story 6 - 占い状態管理 (state-management)

## ストーリー概要

フロントエンドとして、占いの進行状態（初期/抽選中/結果表示）を管理したい。
「もう一度占う」で状態をリセットできるように。

## タスクリスト

### SM-1: 状態型定義を作成

**分類**: TDD（型定義 + ロジック検証）

- [ ] [TDD][RED] TarotStatus型とTarotState型のテスト作成
- [ ] [TDD][GREEN] TarotStatus型とTarotState型の実装
- [ ] [TDD][REFACTOR] 型定義のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（型の網羅性、命名）
- [ ] [TDD][CHECK] lint/format/build

**詳細**: `TarotStatus = 'idle' | 'drawing' | 'result'`, `TarotState = { status: TarotStatus; selectedCard: string | null }`

---

### SM-2: useTarotState Hookを実装

**分類**: TDD（カスタムHook、明確な入出力）

- [ ] [TDD][RED] useTarotStateのテスト作成（初期状態、戻り値の型）
- [ ] [TDD][GREEN] useTarotStateの基本実装
- [ ] [TDD][REFACTOR] Hookのリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（Hook設計、状態管理）
- [ ] [TDD][CHECK] lint/format/build

**詳細**: `const { status, selectedCard, startDrawing, showResult, reset } = useTarotState()`

---

### SM-3: 状態遷移関数（startDrawing）を実装

**分類**: TDD（状態遷移ロジック、アサーションで検証可能）

- [ ] [TDD][RED] startDrawingのテスト作成（idle→drawing遷移、不正遷移防止）
- [ ] [TDD][GREEN] startDrawingの実装
- [ ] [TDD][REFACTOR] リファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（遷移ガード、エッジケース）
- [ ] [TDD][CHECK] lint/format/build

**詳細**: idleでない場合は遷移しない（状態ガード）

---

### SM-4: 状態遷移関数（showResult）を実装

**分類**: TDD（状態遷移 + データ設定ロジック）

- [ ] [TDD][RED] showResultのテスト作成（drawing→result遷移、selectedCard設定）
- [ ] [TDD][GREEN] showResultの実装
- [ ] [TDD][REFACTOR] リファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（遷移ガード、nullチェック）
- [ ] [TDD][CHECK] lint/format/build

**詳細**: `showResult(cardId: string)` で選択されたカードを保存

---

### SM-5: 状態リセット関数（reset）を実装

**分類**: TDD（状態リセットロジック）

- [ ] [TDD][RED] resetのテスト作成（idle状態に戻る、selectedCardクリア）
- [ ] [TDD][GREEN] resetの実装
- [ ] [TDD][REFACTOR] リファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（完全リセット、副作用なし）
- [ ] [TDD][CHECK] lint/format/build

**詳細**: 任意の状態からidleに戻せる

---

### SM-6: 状態に応じたUI条件分岐を実装

**分類**: E2E（UI表示、視覚的確認が必要）

- [ ] [E2E][IMPL] 状態別UI条件分岐の実装（idle/drawing/result）
- [ ] [E2E][AUTO] agent-browser検証
  - idle状態で「占う」ボタンが表示されるか
  - drawing状態でローディング表示されるか
  - result状態で結果 + 「もう一度占う」ボタンが表示されるか
  - リセットボタンクリックでidle状態に戻るか
- [ ] [E2E][CHECK] lint/format/build

**詳細**: `status`に応じて`<StartButton />`, `<LoadingSpinner />`, `<ResultView />`を切り替え

---

## 受入条件

- [x] 初期状態が'idle'である
- [x] 「占う」クリックで'drawing'状態に遷移する
- [x] 抽選完了後'result'状態に遷移する
- [x] 「もう一度占う」で状態がリセットされる
- [x] 状態遷移が単方向である（idle→drawing→result→idle）

## 技術的ノート

- Reactの状態管理（useState）を使用
- カスタムHook (useTarotState) でロジックを分離
- 状態型を定義してType-safe にする
- 状態遷移関数を提供（startDrawing, showResult, reset）

## 依存関係

- なし（独立した状態管理機能）
