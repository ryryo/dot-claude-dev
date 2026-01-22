# e2e-verify

## 役割

E2EのAUTOフェーズ: MCP agent-browser（Claude in Chrome）で操作フローを検証する。

## 推奨モデル

**haiku** - 検証タスクに最適

## 入力

- 実装されたUIコンポーネント
- 期待する動作
- 開発サーバーURL

## 出力

- 検証結果
- スクリーンショット

## プロンプト

```
MCP agent-browser（Claude in Chrome）で操作フローを検証してください。

## 検証対象
- コンポーネント: {component_name}
- URL: http://localhost:3000/{path}

## 検証手順

### 1. タブ準備
```javascript
// タブ情報取得
mcp__claude-in-chrome__tabs_context_mcp({ createIfEmpty: true })

// 新規タブ作成
mcp__claude-in-chrome__tabs_create_mcp()
```

### 2. ページ遷移
```javascript
mcp__claude-in-chrome__navigate({
  url: "http://localhost:3000/{path}",
  tabId: {tab_id}
})
```

### 3. 初期状態確認
```javascript
// スクリーンショット取得
mcp__claude-in-chrome__computer({
  action: "screenshot",
  tabId: {tab_id}
})

// ページ構造確認
mcp__claude-in-chrome__read_page({ tabId: {tab_id} })
```

### 4. 要素検索・操作
```javascript
// 要素検索（自然言語）
mcp__claude-in-chrome__find({
  query: "メールアドレス入力欄",
  tabId: {tab_id}
})
// → ref_1 が返される

// フォーム入力
mcp__claude-in-chrome__form_input({
  ref: "ref_1",
  value: "test@example.com",
  tabId: {tab_id}
})

// ボタンクリック
mcp__claude-in-chrome__find({
  query: "ログインボタン",
  tabId: {tab_id}
})
mcp__claude-in-chrome__computer({
  action: "left_click",
  ref: "ref_2",
  tabId: {tab_id}
})
```

### 5. 結果確認
```javascript
// 状態変化確認
mcp__claude-in-chrome__read_page({ tabId: {tab_id} })

// スクリーンショット取得
mcp__claude-in-chrome__computer({
  action: "screenshot",
  tabId: {tab_id}
})
```

### 6. レスポンシブ検証（必要な場合）
```javascript
// モバイルサイズに変更
mcp__claude-in-chrome__resize_window({
  width: 375,
  height: 667,
  tabId: {tab_id}
})

// スクリーンショット取得
mcp__claude-in-chrome__computer({
  action: "screenshot",
  tabId: {tab_id}
})
```

## 期待する動作
{expected_behavior}

## 報告形式

- 成功: "VERIFIED: 期待通りの動作を確認"
- 失敗: "FAILED: [問題の説明]"

問題がある場合:
1. 問題の詳細
2. スクリーンショット
3. 修正提案
```

## 注意事項

- 開発サーバーが起動していることを確認
- 操作は慎重に（クリック位置など）
- 問題があれば詳細に報告
