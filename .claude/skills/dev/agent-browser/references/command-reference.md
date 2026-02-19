# agent-browser コマンドリファレンス

## クイックスタート

```bash
agent-browser open <url>        # ページに移動
agent-browser snapshot -i       # 参照付きの対話要素を取得
agent-browser click @e1         # 参照で要素をクリック
agent-browser fill @e2 "text"   # 参照で入力欄に入力
agent-browser close             # ブラウザを閉じる
```

## コアワークフロー

1. ナビゲート: `agent-browser open <url>`
2. スナップショット: `agent-browser snapshot -i` (`@e1`, `@e2` のような参照付き要素を返す)
3. スナップショットから取得した参照を使用して対話
4. ナビゲーションまたは重要なDOM変更後に再スナップショット

## ナビゲーション

```bash
agent-browser open <url>      # URLに移動
agent-browser back            # 戻る
agent-browser forward         # 進む
agent-browser reload          # ページを再読み込み
agent-browser close           # ブラウザを閉じる
```

## スナップショット（ページ分析）

```bash
agent-browser snapshot        # 完全なアクセシビリティツリー
agent-browser snapshot -i     # 対話要素のみ（推奨）
agent-browser snapshot -c     # コンパクトな出力
agent-browser snapshot -d 3   # 深度を3に制限
```

## 対話（スナップショットの@refを使用）

```bash
agent-browser click @e1           # クリック
agent-browser dblclick @e1        # ダブルクリック
agent-browser fill @e2 "text"     # クリアして入力
agent-browser type @e2 "text"     # クリアせずに入力
agent-browser press Enter         # キーを押す
agent-browser press Control+a     # キー組み合わせ
agent-browser hover @e1           # ホバー
agent-browser check @e1           # チェックボックスをチェック
agent-browser uncheck @e1         # チェックボックスのチェックを外す
agent-browser select @e1 "value"  # ドロップダウンを選択
agent-browser scroll down 500     # ページをスクロール
agent-browser scrollintoview @e1  # 要素を表示領域までスクロール
```

## 情報取得

```bash
agent-browser get text @e1        # 要素のテキストを取得
agent-browser get value @e1       # 入力値を取得
agent-browser get title           # ページタイトルを取得
agent-browser get url             # 現在のURLを取得
```

## スクリーンショット

```bash
agent-browser screenshot          # 標準出力にスクリーンショット
agent-browser screenshot path.png # ファイルに保存
agent-browser screenshot --full   # フルページ
```

## 待機

```bash
agent-browser wait @e1                     # 要素を待つ
agent-browser wait 2000                    # ミリ秒待つ
agent-browser wait --text "Success"        # テキストを待つ
agent-browser wait --load networkidle      # ネットワークアイドルを待つ
```

## ビューポート

```bash
agent-browser set viewport 375 667        # モバイル
agent-browser set viewport 768 1024       # タブレット
agent-browser set viewport 1280 800       # デスクトップ
```

## セマンティックロケーター（参照の代替）

```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
```

## セッション（並列ブラウザ）

```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
```

## JSON出力（解析用）

```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

## デバッグ

```bash
agent-browser open example.com --headed  # ブラウザウィンドウを表示
agent-browser console                    # コンソールメッセージを表示
agent-browser errors                     # ページエラーを表示
```

## 認証状態の保存・復元

```bash
# ログイン後に状態を保存
agent-browser state save auth.json

# 別セッションで状態を復元
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

## 検証パターン例

### フォーム検証

```bash
agent-browser open http://localhost:3000/form
agent-browser wait --load networkidle
agent-browser snapshot -i
# 出力: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i    # 結果確認
agent-browser screenshot /tmp/form_result.png
agent-browser close
```

### レスポンシブ検証

```bash
agent-browser open http://localhost:3000
agent-browser wait --load networkidle

# モバイル
agent-browser set viewport 375 667
agent-browser screenshot /tmp/mobile.png

# タブレット
agent-browser set viewport 768 1024
agent-browser screenshot /tmp/tablet.png

# デスクトップ
agent-browser set viewport 1024 768
agent-browser screenshot /tmp/desktop.png

agent-browser close
```

### ページ表示確認

```bash
agent-browser open http://localhost:3000
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser screenshot /tmp/page.png --full
agent-browser close
```
