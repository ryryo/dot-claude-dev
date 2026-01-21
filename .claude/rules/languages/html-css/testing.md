---
description: HTML/CSSテスト規約。視覚的回帰テストとアクセシビリティテスト。
globs:
  - "**/*.html"
  - "**/*.css"
---

# HTML/CSSテスト規約

## テスト種類

| テスト種類 | ツール | 目的 |
|-----------|--------|------|
| 視覚的回帰 | Playwright/Storybook | UIの予期しない変更を検出 |
| アクセシビリティ | axe-core/Lighthouse | WCAG準拠を確認 |
| レスポンシブ | agent-browser | 各デバイスサイズで表示確認 |

## アクセシビリティテスト

### axe-core（自動テスト）

```javascript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('アクセシビリティ違反がない', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page }).analyze();

  expect(results.violations).toEqual([]);
});
```

### 手動チェックリスト

| カテゴリ | チェック項目 |
|----------|------------|
| キーボード | Tabで全要素にアクセス可能 |
| フォーカス | フォーカス状態が視覚的にわかる |
| コントラスト | 4.5:1以上（通常テキスト） |
| 代替テキスト | 画像にalt属性がある |
| 見出し | h1-h6が正しい階層 |
| フォーム | labelがinputに関連付け |

## 視覚的回帰テスト

### Playwright

```javascript
import { test, expect } from '@playwright/test';

test('ログインページのスナップショット', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveScreenshot('login.png');
});

test('モバイル表示のスナップショット', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/');
  await expect(page).toHaveScreenshot('home-mobile.png');
});
```

### Storybook

```javascript
// Button.stories.ts
export default {
  title: 'Components/Button',
  component: Button,
};

export const Primary = {
  args: {
    variant: 'primary',
    label: 'Button',
  },
};

export const Disabled = {
  args: {
    disabled: true,
    label: 'Disabled',
  },
};
```

## レスポンシブテスト（agent-browser）

### ブレイクポイント

| デバイス | 幅 | テスト項目 |
|----------|-----|----------|
| モバイル | 375px | ハンバーガーメニュー、1カラム |
| タブレット | 768px | サイドバー折りたたみ、2カラム |
| デスクトップ | 1024px | フルレイアウト、3カラム |

### 検証手順

```javascript
// agent-browser検証
mcp__claude-in-chrome__resize_window({ width: 375, height: 667, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })

// 確認項目
// - ナビゲーションがハンバーガーメニューになっている
// - コンテンツが1カラムで表示
// - タッチターゲットが44px以上
```

## CSSの品質チェック

### Stylelint設定

```json
{
  "extends": "stylelint-config-standard",
  "rules": {
    "declaration-block-no-duplicate-properties": true,
    "no-descending-specificity": true,
    "selector-class-pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*(__[a-z0-9]+(-[a-z0-9]+)*)?(--[a-z0-9]+(-[a-z0-9]+)*)?$"
  }
}
```

## テスト優先度

1. **必須**: アクセシビリティ（axe-core）
2. **推奨**: 主要ページのスナップショット
3. **オプション**: 全コンポーネントのStorybook

## 禁止事項

- ❌ スナップショットの無条件更新
- ❌ アクセシビリティ違反の無視
- ❌ 特定ブラウザのみでテスト
