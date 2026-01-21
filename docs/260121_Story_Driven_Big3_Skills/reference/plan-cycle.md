# PLANサイクル詳細

## 使用ツール

**MCP版 agent-browser（Claude in Chrome）**を使用:
- Chrome拡張経由でブラウザを直接操作
- mcp__claude-in-chrome__* ツール群を使用

> 注: CLI版 agent-browser（npm install -g agent-browser）は使用しない

## PLANフロー

```
┌─────────────────────────────────────────────────────────────────┐
│ ステップ1: UI実装                                                │
├─────────────────────────────────────────────────────────────────┤
│ - コンポーネント構造を作成                                        │
│ - スタイリングを適用                                              │
│ - レスポンシブ対応                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ステップ2: agent-browser自動検証（ループ）                        │
├─────────────────────────────────────────────────────────────────┤
│ agent-browserで自動チェック可能な項目を検証：                      │
│                                                                 │
│ 1. ページ読み込み確認                                            │
│ 2. 要素存在チェック（セマンティックロケータ）                      │
│ 3. スクリーンショット取得                                         │
│ 4. 期待状態との比較（LLMが画像を分析）                            │
│                                                                 │
│ 問題あり → ステップ1に戻って修正                                  │
│ ⚡ 自動検証で問題なければ次へ（通常1-3回で収束）                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ステップ3: 目視確認（ユーザー任意）                               │
├─────────────────────────────────────────────────────────────────┤
│ ユーザーが開発サーバー（localhost）で直接確認。                    │
│ エージェントは実装完了を報告し、次のタスクへ進む。                  │
│                                                                 │
│ ※ ユーザーから修正指示があれば対応                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ステップ4: 品質チェック                                          │
├─────────────────────────────────────────────────────────────────┤
│ npm run lint && npm run format && npm run build                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ステップ5: コミット                                              │
└─────────────────────────────────────────────────────────────────┘
```

## MCP版 agent-browser セットアップ

1. Claude in Chrome拡張をインストール
2. MCPサーバーを有効化
3. Claude Codeから直接ブラウザ操作が可能

## MCP版 主要ツール

| ツール | 用途 |
|--------|------|
| `mcp__claude-in-chrome__tabs_context_mcp` | タブ情報取得（最初に実行） |
| `mcp__claude-in-chrome__tabs_create_mcp` | 新規タブ作成 |
| `mcp__claude-in-chrome__navigate` | URLへの遷移 |
| `mcp__claude-in-chrome__find` | 要素の検索（自然言語） |
| `mcp__claude-in-chrome__computer` | クリック・入力・スクロール操作 |
| `mcp__claude-in-chrome__form_input` | フォーム入力（ref指定） |
| `mcp__claude-in-chrome__read_page` | ページ状態の確認 |

## 操作フロー検証の手順

```
1. tabs_context_mcp でタブ情報取得
2. tabs_create_mcp で新規タブ作成
3. navigate でURLへ遷移
4. find で要素を検索（自然言語: "ログインボタン"）
5. computer で操作実行（クリック、入力）
6. read_page で結果確認
```

## 検証パターン例

### フォーム検証（MCP版）

```javascript
// 1. タブ準備
mcp__claude-in-chrome__tabs_context_mcp({ createIfEmpty: true })
mcp__claude-in-chrome__tabs_create_mcp()

// 2. ページ遷移
mcp__claude-in-chrome__navigate({ url: "http://localhost:3000/login", tabId: 123 })

// 3. 要素検索
mcp__claude-in-chrome__find({ query: "メールアドレス入力欄", tabId: 123 })
// → ref_1 が返される

// 4. フォーム入力
mcp__claude-in-chrome__form_input({ ref: "ref_1", value: "test@example.com", tabId: 123 })

// 5. ボタンクリック
mcp__claude-in-chrome__find({ query: "ログインボタン", tabId: 123 })
mcp__claude-in-chrome__computer({ action: "left_click", ref: "ref_2", tabId: 123 })

// 6. 結果確認
mcp__claude-in-chrome__read_page({ tabId: 123 })
// → ダッシュボードが表示されていることを確認
```

### レスポンシブ検証（MCP版）

```javascript
// ビューポートサイズ変更
mcp__claude-in-chrome__resize_window({ width: 375, height: 667, tabId: 123 })

// スクリーンショット取得
mcp__claude-in-chrome__computer({ action: "screenshot", tabId: 123 })
```

## 自然言語による要素検索

`find`ツールは自然言語で要素を検索可能:

| クエリ例 | 検索対象 |
|----------|----------|
| "ログインボタン" | ログイン用のボタン |
| "メールアドレス入力欄" | email入力フィールド |
| "送信ボタン" | submit/送信ボタン |
| "エラーメッセージ" | エラー表示要素 |

## TODO.md でのラベル表記

```markdown
- [ ] [PLAN][IMPL] LoginForm UIコンポーネント実装
- [ ] [PLAN][AUTO] agent-browser自動検証
- [ ] [PLAN][CHECK] lint/format/build
```

## 参照ルール

実装時は `.claude/rules/workflow/plan-cycle.md` が自動適用される。
