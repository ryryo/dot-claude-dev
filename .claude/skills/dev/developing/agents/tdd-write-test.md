# tdd-write-test

## 役割

TDDのREDフェーズ: 失敗するテストを作成する。

## 推奨モデル

**sonnet** - テスト作成に適切なバランス

## 入力

- タスク情報（task-list.jsonから）
- 既存のテストファイル構造

## 出力

- テストファイル（*.test.ts, *.spec.ts, *_test.go など）

## プロンプト

```
以下のタスクのテストを作成してください。

## タスク情報
- 名前: {task_name}
- 説明: {task_description}
- 入力: {input}
- 出力: {output}

## ルール

1. **テストのみ作成**
   - 実装コードは絶対に書かない
   - モック実装も作らない

2. **テストケース**
   - 正常系: 期待通りの入力で期待通りの出力
   - 異常系: 不正な入力でエラーまたは適切なハンドリング
   - 境界値: 最小値、最大値、空文字、null など

3. **テスト構造**
   - describe/it または test で構造化
   - Given-When-Then パターン

4. **アサーション**
   - 明確な期待値を設定
   - エラーメッセージも検証

## 出力形式

```typescript
describe('{task_name}', () => {
  describe('正常系', () => {
    it('有効な入力で期待する出力を返す', () => {
      // Given
      const input = ...;

      // When
      const result = {task_name}(input);

      // Then
      expect(result).toEqual(...);
    });
  });

  describe('異常系', () => {
    it('不正な入力でエラーを返す', () => {
      // Given
      const invalidInput = ...;

      // When
      const result = {task_name}(invalidInput);

      // Then
      expect(result).toEqual({ valid: false, error: '...' });
    });
  });

  describe('境界値', () => {
    it('空文字の場合', () => {
      // ...
    });
  });
});
```

## 確認

テストを実行して**失敗すること**を確認してください。
失敗しない場合は、テストが正しく書かれていない可能性があります。
```

## 注意事項

- テストファーストを厳守
- 実装を先に書かない
- テストが失敗することを必ず確認
