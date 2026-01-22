---
description: E2E開発（UI実装）時に自動適用されるルール。agent-browserによる操作フロー検証。
globs:
  - "**/components/**/*.tsx"
  - "**/components/**/*.jsx"
  - "**/pages/**/*.tsx"
  - "**/views/**/*.vue"
---

# E2Eサイクルルール

## 基本原則

1. **実装→検証ループ**: UI実装後にagent-browserで検証
2. **操作フロー重視**: 見た目だけでなく操作の動作を確認
3. **自動化優先**: 可能な限り自動検証、必要な場合のみ目視

## E2Eサイクル

### IMPL（UI実装）

```
✓ コンポーネント構造を作成
✓ スタイリングを適用
✓ レスポンシブ対応
✓ アクセシビリティ対応
```

**チェックリスト**:
- [ ] Props型定義
- [ ] イベントハンドラ
- [ ] エラー状態の表示
- [ ] ローディング状態

### AUTO（agent-browser検証）

MCP版 agent-browser（Claude in Chrome）で検証:

```
1. tabs_context_mcp でタブ情報取得
2. tabs_create_mcp で新規タブ作成
3. navigate でURLへ遷移
4. find で要素検索（自然言語）
5. computer/form_input で操作実行
6. read_page で結果確認
```

**検証項目**:
- [ ] ページ読み込み
- [ ] 要素存在
- [ ] フォーム入力
- [ ] ボタンクリック
- [ ] 状態変化
- [ ] レスポンシブ

## 検証パターン

### フォーム検証

```javascript
// 要素検索
mcp__claude-in-chrome__find({ query: "メールアドレス入力欄", tabId })

// 入力
mcp__claude-in-chrome__form_input({ ref: "ref_1", value: "test@example.com", tabId })

// 送信
mcp__claude-in-chrome__find({ query: "送信ボタン", tabId })
mcp__claude-in-chrome__computer({ action: "left_click", ref: "ref_2", tabId })

// 結果確認
mcp__claude-in-chrome__read_page({ tabId })
```

### レスポンシブ検証

```javascript
// モバイルサイズ
mcp__claude-in-chrome__resize_window({ width: 375, height: 667, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })

// タブレットサイズ
mcp__claude-in-chrome__resize_window({ width: 768, height: 1024, tabId })
mcp__claude-in-chrome__computer({ action: "screenshot", tabId })
```

## アクセシビリティ要件

| 項目 | 要件 |
|------|------|
| キーボード | Tab移動可能、Enter/Space操作可能 |
| aria属性 | 適切なrole, aria-label |
| コントラスト | WCAG 2.1 AA以上 |
| フォーカス | 視覚的にわかる |

## エラー時の対応

1. **検証失敗**: 実装を修正 → 再検証
2. **3回失敗**: 問題を報告、ユーザーに確認
3. **ツールエラー**: 開発サーバー確認、再試行

## 関連スキル

- **dev:developing**: E2Eタスクの実装
- **dev:story**: E2Eタスクの生成
