---
description: HTML/CSSテスト規約。agent-browserによる視覚的検証とアクセシビリティテスト。
globs:
  - "**/*.html"
  - "**/*.css"
---

# HTML/CSSテスト規約

## テスト種類

| テスト種類 | ツール | 目的 |
|-----------|--------|------|
| 視覚的検証 | agent-browser | UIの表示確認、操作検証 |
| アクセシビリティ | axe-core / agent-browser | WCAG準拠を確認 |
| レスポンシブ | agent-browser | 各デバイスサイズで表示確認 |

## 視覚的検証（agent-browser）

### 基本フロー

```javascript
// 1. タブコンテキスト取得
mcp__claude-in-chrome__tabs_context_mcp({ createIfEmpty: true })

// 2. ページに遷移
mcp__claude-in-chrome__navigate({ url: "http://localhost:3000", tabId })

// 3. スクリーンショット取得
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })

// 4. 要素検索（自然言語）
mcp__claude-in-chrome__find({ query: "ログインボタン", tabId })

// 5. 操作実行
mcp__claude-in-chrome__computer({ action: "left_click", ref: "ref_1", tabId })

// 6. 結果確認
mcp__claude-in-chrome__read_page({ tabId })
```

### 検証項目

| カテゴリ | 確認内容 |
|----------|----------|
| レイアウト | 要素の配置、余白、整列 |
| タイポグラフィ | フォントサイズ、行間、色 |
| インタラクション | ホバー、フォーカス、クリック反応 |
| 状態表示 | ローディング、エラー、空状態 |

## レスポンシブ検証

### ブレイクポイント

| デバイス | 幅 | テスト項目 |
|----------|-----|----------|
| モバイル | 375px | ハンバーガーメニュー、1カラム |
| タブレット | 768px | サイドバー折りたたみ、2カラム |
| デスクトップ | 1024px | フルレイアウト、3カラム |

### 検証手順

```javascript
// モバイルサイズで検証
mcp__claude-in-chrome__resize_window({ width: 375, height: 667, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })

// 確認項目
// - ナビゲーションがハンバーガーメニューになっている
// - コンテンツが1カラムで表示
// - タッチターゲットが44px以上

// タブレットサイズで検証
mcp__claude-in-chrome__resize_window({ width: 768, height: 1024, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })

// デスクトップサイズで検証
mcp__claude-in-chrome__resize_window({ width: 1024, height: 768, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })
```

## アクセシビリティ検証

### agent-browserでの確認

```javascript
// インタラクティブ要素のみ取得
mcp__claude-in-chrome__read_page({ filter: "interactive", tabId })

// 確認項目
// - ボタンに適切なラベルがある
// - フォーム要素にlabelが関連付けられている
// - aria属性が適切に設定されている
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

## フォーム検証

```javascript
// 入力フィールドを検索
mcp__claude-in-chrome__find({ query: "メールアドレス入力欄", tabId })

// 値を入力
mcp__claude-in-chrome__form_input({ ref: "ref_1", value: "test@example.com", tabId })

// 送信ボタンをクリック
mcp__claude-in-chrome__find({ query: "送信ボタン", tabId })
mcp__claude-in-chrome__computer({ action: "left_click", ref: "ref_2", tabId })

// 結果を確認
mcp__claude-in-chrome__read_page({ tabId })
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

1. **必須**: 主要ページの視覚的検証（agent-browser）
2. **必須**: レスポンシブ検証（3ブレイクポイント）
3. **推奨**: アクセシビリティ検証
4. **オプション**: エッジケース（長いテキスト、空データ等）

## 禁止事項

- ❌ 視覚的確認なしでのUI変更マージ
- ❌ アクセシビリティ違反の無視
- ❌ モバイル検証のスキップ

## エラー時の対応

1. **検証失敗**: 実装を修正 → 再検証
2. **3回失敗**: 問題を報告、ユーザーに確認
3. **ツールエラー**: 開発サーバー確認、再試行
