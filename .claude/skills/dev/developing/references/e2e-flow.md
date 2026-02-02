# E2Eワークフロー詳細

## 使用ツール

**agent-browserスキル**（CLIツール）を使用してブラウザ操作・検証を行う。

コアワークフロー:
```bash
agent-browser open <url>        # ページを開く
agent-browser snapshot -i       # インタラクティブ要素一覧（@ref付き）
agent-browser click @e1         # @refで要素をクリック
agent-browser fill @e2 "text"   # @refでフォーム入力
agent-browser close             # ブラウザを閉じる
```

## E2Eフロー

```
ステップ1: UI実装
  - コンポーネント構造を作成
  - スタイリング・レスポンシブ対応
      ↓
ステップ2: agent-browserスキルで自動検証（ループ）
  1. agent-browser open → snapshot -i → screenshot
  2. 要素操作（fill, click等）
  3. 結果確認（snapshot -i, screenshot）
  問題あり → ステップ1に戻って修正（通常1-3回で収束）
      ↓
ステップ3: 目視確認（ユーザー任意）
  ユーザーがlocalhost で直接確認
      ↓
ステップ4: 品質チェック（lint/format/build）
      ↓
ステップ5: コミット
```

## 主要コマンド

| コマンド | 用途 |
|--------|------|
| `agent-browser open <url>` | ページを開く |
| `agent-browser snapshot -i` | インタラクティブ要素取得（@ref付き） |
| `agent-browser click @e1` | クリック |
| `agent-browser fill @e1 "text"` | フォーム入力 |
| `agent-browser screenshot` | スクリーンショット取得 |
| `agent-browser set viewport W H` | ビューポートサイズ変更 |
| `agent-browser wait --load networkidle` | ネットワーク待機 |
| `agent-browser get text @e1` | テキスト取得 |
| `agent-browser close` | ブラウザ閉じる |

## 検証パターン例

### フォーム検証

```bash
agent-browser open http://localhost:3000/login
agent-browser snapshot -i
# → textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i    # 結果確認
```

### レスポンシブ検証

```bash
agent-browser set viewport 375 667      # モバイル
agent-browser screenshot
agent-browser set viewport 768 1024     # タブレット
agent-browser screenshot
agent-browser set viewport 1024 768     # デスクトップ
agent-browser screenshot
```

## TODO.md でのラベル表記

```markdown
- [ ] [E2E][IMPL] LoginForm UIコンポーネント実装
- [ ] [E2E][AUTO] agent-browserスキルで自動検証
- [ ] [E2E][CHECK] lint/format/build
```
