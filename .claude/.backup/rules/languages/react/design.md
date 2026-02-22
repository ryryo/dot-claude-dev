---
description: Reactコンポーネント設計規約。再利用性とアクセシビリティを重視。
globs:
  - "**/*.tsx"
  - "**/components/**/*"
---

# Reactコンポーネント設計規約

## コンポーネント分類

### Presentational（表示）

```tsx
// 見た目だけを担当、ロジックなし
interface CardProps {
  title: string;
  children: React.ReactNode;
}

function Card({ title, children }: CardProps) {
  return (
    <div className="card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

### Container（コンテナ）

```tsx
// データ取得・状態管理を担当
function UserCardContainer({ userId }: { userId: string }) {
  const { user, loading, error } = useUser(userId);

  if (loading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;

  return <UserCard user={user} />;
}
```

## 合成パターン

### Compound Components

```tsx
function Tabs({ children }: { children: React.ReactNode }) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </TabsContext.Provider>
  );
}

Tabs.List = TabList;
Tabs.Panel = TabPanel;

// 使用例
<Tabs>
  <Tabs.List>
    <Tab>Tab 1</Tab>
    <Tab>Tab 2</Tab>
  </Tabs.List>
  <Tabs.Panel>Content 1</Tabs.Panel>
  <Tabs.Panel>Content 2</Tabs.Panel>
</Tabs>
```

### Render Props

```tsx
interface MouseTrackerProps {
  render: (position: { x: number; y: number }) => React.ReactNode;
}

function MouseTracker({ render }: MouseTrackerProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  // ... マウス追跡ロジック
  return <>{render(position)}</>;
}
```

## アクセシビリティ

### 必須属性

```tsx
// ボタン
<button aria-label="閉じる" onClick={onClose}>
  <CloseIcon />
</button>

// フォーム
<label htmlFor="email">Email</label>
<input id="email" type="email" aria-describedby="email-hint" />
<span id="email-hint">例: user@example.com</span>

// モーダル
<div role="dialog" aria-labelledby="modal-title" aria-modal="true">
  <h2 id="modal-title">確認</h2>
</div>
```

### キーボードナビゲーション

```tsx
function Menu() {
  const [focusIndex, setFocusIndex] = useState(0);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        setFocusIndex(i => (i + 1) % items.length);
        break;
      case 'ArrowUp':
        setFocusIndex(i => (i - 1 + items.length) % items.length);
        break;
    }
  };

  return (
    <ul role="menu" onKeyDown={handleKeyDown}>
      {items.map((item, i) => (
        <li role="menuitem" tabIndex={i === focusIndex ? 0 : -1}>
          {item}
        </li>
      ))}
    </ul>
  );
}
```

## レスポンシブ設計

### ブレイクポイント

| 名前 | 幅 | 用途 |
|------|-----|------|
| sm | <640px | モバイル |
| md | 640-768px | タブレット縦 |
| lg | 768-1024px | タブレット横 |
| xl | >1024px | デスクトップ |

### モバイルファースト

```css
/* 基本（モバイル） */
.container { padding: 1rem; }

/* タブレット以上 */
@media (min-width: 768px) {
  .container { padding: 2rem; }
}

/* デスクトップ */
@media (min-width: 1024px) {
  .container { padding: 3rem; }
}
```

## 禁止事項

- ❌ 巨大なコンポーネント（300行以上）
- ❌ Props drilling（3階層以上）
- ❌ 非アクセシブルなインタラクション
- ❌ ハードコードされた文字列（i18n対応）

## 推奨事項

- ✅ 1コンポーネント1責任
- ✅ Propsは最小限に
- ✅ セマンティックHTML
- ✅ 適切なaria属性
