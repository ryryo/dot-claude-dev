---
description: Reactテスト規約。React Testing Libraryを使用。
globs:
  - "**/*.test.tsx"
  - "**/*.spec.tsx"
---

# Reactテスト規約

## テストフレームワーク

- Vitest または Jest
- React Testing Library
- @testing-library/user-event

## テスト構造

### コンポーネントテスト

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Button', () => {
  it('クリック時にonClickが呼ばれる', async () => {
    const handleClick = vi.fn();
    render(<Button label="Click me" onClick={handleClick} />);

    await userEvent.click(screen.getByRole('button', { name: 'Click me' }));

    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('disabledの場合はクリックできない', async () => {
    const handleClick = vi.fn();
    render(<Button label="Click me" onClick={handleClick} disabled />);

    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeDisabled();
  });
});
```

### フォームテスト

```tsx
describe('LoginForm', () => {
  it('有効な入力で送信できる', async () => {
    const handleSubmit = vi.fn();
    render(<LoginForm onSubmit={handleSubmit} />);

    await userEvent.type(screen.getByLabelText('Email'), 'user@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
    });
  });

  it('不正なメールでエラーを表示', async () => {
    render(<LoginForm onSubmit={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Email'), 'invalid');
    await userEvent.tab(); // blur

    expect(screen.getByText(/有効なメールアドレス/)).toBeInTheDocument();
  });
});
```

## クエリ優先順位

1. `getByRole` - アクセシビリティロール
2. `getByLabelText` - フォーム要素
3. `getByPlaceholderText` - プレースホルダー
4. `getByText` - テキストコンテンツ
5. `getByTestId` - 最終手段

## 非同期テスト

```tsx
it('データ取得後に表示される', async () => {
  render(<UserProfile userId="1" />);

  // ローディング状態を確認
  expect(screen.getByText('Loading...')).toBeInTheDocument();

  // データ表示を待機
  await waitFor(() => {
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

## モック

### APIモック

```tsx
vi.mock('./api', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: '1', name: 'John' }),
}));
```

### ルーターモック

```tsx
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => vi.fn(),
}));
```

## 禁止事項

- ❌ 実装の詳細をテスト（内部state、メソッド）
- ❌ `container.querySelector`の使用
- ❌ スナップショットテストの乱用
- ❌ `waitFor`内での副作用

## 推奨事項

- ✅ ユーザー視点でテスト
- ✅ アクセシビリティを考慮したクエリ
- ✅ userEventでユーザー操作をシミュレート
