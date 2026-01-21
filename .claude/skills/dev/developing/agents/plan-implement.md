# plan-implement

## 役割

PLANのIMPLフェーズ: UIコンポーネントを実装する。

## 推奨モデル

**sonnet** - UI実装に適切なバランス

## 入力

- タスク情報
- デザイン仕様（あれば）

## 出力

- UIコンポーネント
- スタイル

## プロンプト

```
UIコンポーネントを実装してください。

## タスク情報
- 名前: {task_name}
- 説明: {task_description}

## 実装項目

### 1. コンポーネント構造
- Props定義（TypeScript型）
- 状態管理（useState, useReducer）
- イベントハンドラ

### 2. スタイリング
- CSS Modules / Tailwind / styled-components
- レスポンシブ対応
- アクセシビリティ

### 3. インタラクション
- ユーザー入力の処理
- バリデーションフィードバック
- ローディング状態
- エラー表示

## コンポーネント設計例

```tsx
interface {ComponentName}Props {
  onSubmit: (data: FormData) => void;
  isLoading?: boolean;
  error?: string;
}

export function {ComponentName}({ onSubmit, isLoading, error }: {ComponentName}Props) {
  const [formData, setFormData] = useState<FormData>(initialData);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* フォーム要素 */}
      {error && <ErrorMessage message={error} />}
      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Submit'}
      </Button>
    </form>
  );
}
```

## アクセシビリティ

- 適切なaria属性
- キーボードナビゲーション
- スクリーンリーダー対応
- コントラスト比
```

## 注意事項

- アクセシビリティを考慮
- レスポンシブ対応
- エラー状態の表示
