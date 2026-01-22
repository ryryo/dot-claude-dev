# TODO: デッキ生成・シャッフルAPI (deck-shuffle-api)

## ストーリー概要
バックエンドとして、占いを始めるときに78枚のタロットカード（大アルカナ22枚、小アルカナ56枚）がシャッフルされた状態でAPIから提供する。毎回異なる占い結果を得られるようにする。

## タスクリスト

### Phase 1: 型定義とシャッフルロジック（並列実行可能）

#### task-01: タロットカードの型定義
- [ ] [TDD][RED] 大アルカナのカード名リテラル型を定義
- [ ] [TDD][RED] 小アルカナのスート・ランクのリテラル型を定義
- [ ] [TDD][RED] Cardインターフェースを定義（種別、名前、スート、ランクなど）
- [ ] [TDD][RED] ZodスキーマでCard型のバリデーションを定義
- [ ] [TDD][GREEN] 型定義の実装
- [ ] [TDD][REFACTOR] 型定義のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build

#### task-03: シャッフル関数の実装
- [ ] [TDD][RED] shuffleArray関数のテスト作成（要素数不変）
- [ ] [TDD][RED] shuffleArray関数のテスト作成（全要素含有）
- [ ] [TDD][RED] shuffleArray関数のテスト作成（ランダム性）
- [ ] [TDD][RED] shuffleArray関数のテスト作成（エッジケース：空配列、1要素）
- [ ] [TDD][GREEN] Fisher-Yatesシャッフルアルゴリズムの実装
- [ ] [TDD][GREEN] 元配列を変更しない実装
- [ ] [TDD][REFACTOR] シャッフル関数のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build

### Phase 2: デッキ定数データ

#### task-02: タロットデッキ定数データの作成
- [ ] [TDD][RED] デッキ枚数検証テストの作成（78枚）
- [ ] [TDD][RED] 大アルカナ枚数検証テストの作成（22枚）
- [ ] [TDD][RED] 小アルカナ枚数検証テストの作成（56枚）
- [ ] [TDD][GREEN] 大アルカナ22枚のカードデータを配列で定義
- [ ] [TDD][GREEN] 小アルカナ56枚のカードデータを生成（4スート×14ランク）
- [ ] [TDD][GREEN] 各カードにダミー画像パスを追加（/images/cards/dummy-{id}.png）
- [ ] [TDD][GREEN] 全78枚を結合したDEFAULT_DECK定数を作成
- [ ] [TDD][REFACTOR] デッキ定数のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build

**注記**: カード画像は実装時にダミーパスを設定。実際の画像ファイルは後で差し替え可能な構造にする。

### Phase 3: デッキ生成サービス

#### task-05: デッキ生成サービスの実装
- [ ] [TDD][RED] createShuffledDeck関数のテスト作成（78枚返却）
- [ ] [TDD][RED] createShuffledDeck関数のテスト作成（全カード含有）
- [ ] [TDD][RED] createShuffledDeck関数のテスト作成（ランダム性）
- [ ] [TDD][GREEN] createShuffledDeck関数の実装
- [ ] [TDD][GREEN] Result型でラップして返す実装
- [ ] [TDD][REFACTOR] サービス関数のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build

### Phase 4: APIエンドポイント

#### task-07: APIエンドポイントの実装
- [ ] [TASK][EXEC] pages/api/deck/shuffle.tsを作成
- [ ] [TASK][EXEC] GETリクエストのハンドラを実装
- [ ] [TASK][EXEC] createShuffledDeckを呼び出し
- [ ] [TASK][EXEC] 成功時は200とカード配列を返す
- [ ] [TASK][EXEC] エラー時は500とエラーメッセージを返す
- [ ] [TASK][VERIFY] 実装内容の確認

#### task-08: APIエンドポイントのE2Eテスト
- [ ] [E2E][IMPL] 開発サーバーを起動（npm run dev）
- [ ] [E2E][AUTO] curlでGET /api/deck/shuffleを呼び出し
- [ ] [E2E][AUTO] レスポンスが200で78枚のカードが返されることを確認
- [ ] [E2E][AUTO] 複数回呼び出して異なる順序になることを確認
- [ ] [E2E][CHECK] lint/format/build

### Phase 5: 品質チェック

#### task-09: 品質チェック（最終）
- [ ] [TASK][EXEC] npm run lintでESLintチェック
- [ ] [TASK][EXEC] npm run formatでPrettier実行
- [ ] [TASK][EXEC] npm run buildでビルド成功を確認
- [ ] [TASK][EXEC] npm testで全テスト成功を確認
- [ ] [TASK][VERIFY] すべてのチェックが通過したことを確認

## 受入条件チェックリスト
- [ ] 78枚のカードデータが正しく定義されている（大アルカナ22枚、小アルカナ56枚）
- [ ] APIからシャッフルされたデッキが取得できる
- [ ] 毎回異なる順序でカードが返される
- [ ] すべてのカードが重複なく含まれる

## 分類の理由

### TDD分類
- **task-01, task-02, task-03, task-05**: 型定義、デッキ定数、シャッフルロジック、サービス層はすべて入出力が明確で、アサーションで検証可能なビジネスロジック層。
  - 引数と戻り値が定義できる
  - `expect(result).toEqual(expected)`で検証可能
  - 視覚的確認は不要

### E2E分類
- **task-08**: APIエンドポイントのE2Eテストは、実際のHTTPリクエスト/レスポンスを検証する必要があり、開発サーバー起動と実際の呼び出しが必要。curlコマンドでの検証が適切。

### TASK分類
- **task-07**: APIエンドポイントファイルの作成は設定的な作業で、ハンドラ関数の実装は薄いラッパー層。
- **task-09**: lint/format/buildの実行は一回限りのチェック作業で、テスト不要。

## 注意事項
- task-01とtask-03は並列実行可能（依存関係なし）
- task-02はtask-01に依存（Card型が必要）
- task-05はtask-02とtask-03に依存（デッキ定数とシャッフル関数が必要）
- すべてのTDDタスクでRED→GREEN→REFACTOR→REVIEW→CHECKサイクルを厳守
