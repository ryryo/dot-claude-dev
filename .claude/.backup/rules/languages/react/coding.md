---
description: Reactコーディング規約。関数コンポーネントとHooksを使用。
globs:
  - "**/*.tsx"
  - "**/components/**/*.ts"
---

# Reactコーディング規約

## コンポーネント構造

### 関数コンポーネント

```tsx
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ label, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
```

### コンポーネントファイル構成

```
components/
├── Button/
│   ├── index.ts        # エクスポート
│   ├── Button.tsx      # コンポーネント
│   ├── Button.test.tsx # テスト
│   └── Button.css      # スタイル（または .module.css）
```

## Hooks

### useStateパターン

```tsx
const [value, setValue] = useState<string>('');
const [items, setItems] = useState<Item[]>([]);
```

### useEffectパターン

```tsx
useEffect(() => {
  const controller = new AbortController();

  fetchData(controller.signal).then(setData);

  return () => controller.abort();
}, [dependency]);
```

### カスタムHooks

```tsx
function useUser(id: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchUser(id)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [id]);

  return { user, loading, error };
}
```

## フォーム（React Hook Form + Zod）

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormData = z.infer<typeof schema>;

function LoginForm({ onSubmit }: { onSubmit: (data: FormData) => void }) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    mode: 'onBlur',
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register('password')} />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit">Login</button>
    </form>
  );
}
```

## 状態管理

- ローカル状態: useState
- コンポーネント間共有: Context または Zustand
- サーバー状態: TanStack Query

## 禁止事項

- ❌ クラスコンポーネント
- ❌ useEffect内での直接のsetState（無限ループ注意）
- ❌ インラインスタイル（スタイリングソリューションを使用）
- ❌ 直接のDOM操作

## 推奨事項

- ✅ 小さなコンポーネントに分割
- ✅ Props型を明示的に定義
- ✅ メモ化は必要な場合のみ（useMemo, useCallback）
