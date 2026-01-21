---
description: HTML/CSSデザイン規約。一貫性のあるUIを実現。
globs:
  - "**/*.html"
  - "**/*.css"
  - "**/components/**/*"
---

# HTML/CSSデザイン規約

## デザイントークン

### カラーパレット

```css
:root {
  /* プライマリ */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;

  /* グレースケール */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-500: #6b7280;
  --color-gray-900: #111827;

  /* セマンティック */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
}
```

### タイポグラフィ

```css
:root {
  /* フォントサイズ（rem） */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */

  /* フォントウェイト */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* 行の高さ */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
}
```

### スペーシング

```css
:root {
  --spacing-0: 0;
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-2: 0.5rem;   /* 8px */
  --spacing-3: 0.75rem;  /* 12px */
  --spacing-4: 1rem;     /* 16px */
  --spacing-6: 1.5rem;   /* 24px */
  --spacing-8: 2rem;     /* 32px */
  --spacing-12: 3rem;    /* 48px */
  --spacing-16: 4rem;    /* 64px */
}
```

## コンポーネント設計

### ボタン

```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);

  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-medium);

  transition: all 0.2s ease;
}

/* サイズバリアント */
.button--sm { padding: var(--spacing-1) var(--spacing-3); }
.button--lg { padding: var(--spacing-3) var(--spacing-6); }

/* カラーバリアント */
.button--primary {
  background: var(--color-primary-500);
  color: white;
}
.button--primary:hover { background: var(--color-primary-600); }

.button--outline {
  background: transparent;
  border: 1px solid var(--color-gray-300);
}
.button--outline:hover { background: var(--color-gray-50); }
```

### フォーム要素

```css
.input {
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.input--error {
  border-color: var(--color-error);
}

.label {
  display: block;
  margin-bottom: var(--spacing-1);
  font-weight: var(--font-weight-medium);
}

.error-message {
  margin-top: var(--spacing-1);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}
```

## レイアウトパターン

### コンテナ

```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-4);
}
```

### スタック（縦積み）

```css
.stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.stack--sm { gap: var(--spacing-2); }
.stack--lg { gap: var(--spacing-8); }
```

### クラスター（横並び）

```css
.cluster {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
  align-items: center;
}
```

## アクセシビリティ

### フォーカス表示

```css
/* デフォルトのフォーカス */
:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* カスタムフォーカス */
.button:focus-visible {
  box-shadow: 0 0 0 3px var(--color-primary-200);
}
```

### スクリーンリーダー専用

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
```

## レスポンシブブレイクポイント

```css
/* モバイルファースト */
/* 基本スタイル: モバイル */

@media (min-width: 640px) {
  /* sm: 小型タブレット */
}

@media (min-width: 768px) {
  /* md: タブレット */
}

@media (min-width: 1024px) {
  /* lg: デスクトップ */
}

@media (min-width: 1280px) {
  /* xl: 大型デスクトップ */
}
```

## 禁止事項

- ❌ マジックナンバー（直接値）
- ❌ 一貫性のないスペーシング
- ❌ コントラスト不足の配色
- ❌ タッチターゲット44px未満
