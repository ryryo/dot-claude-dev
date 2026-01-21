---
description: HTML/CSSコーディング規約。セマンティックHTMLとモダンCSSを推奨。
globs:
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
---

# HTML/CSSコーディング規約

## HTML

### セマンティックHTML

```html
<!-- Good: セマンティック要素を使用 -->
<header>
  <nav>
    <ul>
      <li><a href="/">Home</a></li>
    </ul>
  </nav>
</header>

<main>
  <article>
    <h1>Article Title</h1>
    <p>Content...</p>
  </article>

  <aside>
    <h2>Related</h2>
  </aside>
</main>

<footer>
  <p>&copy; 2024</p>
</footer>
```

### フォームのアクセシビリティ

```html
<!-- Good: ラベルとinputの関連付け -->
<form>
  <div class="form-group">
    <label for="email">Email</label>
    <input
      id="email"
      type="email"
      name="email"
      required
      aria-describedby="email-hint"
    />
    <span id="email-hint" class="hint">例: user@example.com</span>
  </div>

  <div class="form-group">
    <label for="password">Password</label>
    <input
      id="password"
      type="password"
      name="password"
      required
      minlength="8"
      aria-describedby="password-hint"
    />
    <span id="password-hint" class="hint">8文字以上</span>
  </div>

  <button type="submit">Login</button>
</form>
```

### 画像のアクセシビリティ

```html
<!-- 装飾的な画像 -->
<img src="decoration.png" alt="" role="presentation" />

<!-- 意味のある画像 -->
<img src="product.jpg" alt="赤いスニーカー、サイズ26cm" />

<!-- 図表 -->
<figure>
  <img src="chart.png" alt="月別売上グラフ" />
  <figcaption>2024年の月別売上推移</figcaption>
</figure>
```

## CSS

### CSS変数

```css
:root {
  /* カラー */
  --color-primary: #3b82f6;
  --color-secondary: #64748b;
  --color-error: #ef4444;

  /* スペーシング */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;

  /* フォント */
  --font-family-base: system-ui, sans-serif;
  --font-size-base: 1rem;
  --line-height-base: 1.5;
}
```

### レイアウト（Flexbox/Grid）

```css
/* Flexbox */
.flex-container {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  justify-content: space-between;
}

/* Grid */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}
```

### レスポンシブデザイン（モバイルファースト）

```css
/* 基本（モバイル） */
.container {
  padding: var(--spacing-sm);
}

/* タブレット以上 */
@media (min-width: 768px) {
  .container {
    padding: var(--spacing-md);
  }
}

/* デスクトップ */
@media (min-width: 1024px) {
  .container {
    padding: var(--spacing-lg);
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

### 状態とバリアント

```css
.button {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: 4px;
  cursor: pointer;
}

.button:hover {
  opacity: 0.9;
}

.button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button--primary {
  background: var(--color-primary);
  color: white;
}

.button--secondary {
  background: transparent;
  border: 1px solid var(--color-secondary);
}
```

## 命名規則（BEM）

```css
/* Block */
.card { }

/* Element */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier */
.card--featured { }
.card__header--large { }
```

## 禁止事項

- ❌ `!important`の乱用
- ❌ IDセレクタでスタイリング
- ❌ インラインスタイル（`style`属性）
- ❌ `<br>`での余白調整
- ❌ `<table>`でレイアウト

## 推奨事項

- ✅ CSS変数を活用
- ✅ モバイルファースト
- ✅ Flexbox/Gridでレイアウト
- ✅ セマンティックHTML
- ✅ アクセシビリティ属性
