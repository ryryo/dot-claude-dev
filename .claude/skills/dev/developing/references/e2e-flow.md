# E2Eワークフロー詳細

## 使用ツール

**agent-browserスキル**（CLIツール）を使用してブラウザ操作・検証を行う。

コアワークフロー:
```bash
agent-browser open <url>        # ページを開く
agent-browser snapshot -i       # インタラクティブ要素一覧（@ref付き）
agent-browser click @e1         # @refで要素をクリック
agent-browser fill @e2 "text"   # @refでフォーム入力
agent-browser screenshot        # スクリーンショット取得
agent-browser set viewport W H  # ビューポートサイズ変更
agent-browser close             # ブラウザを閉じる
```

## E2Eフロー

```
ステップ1: E2Eサイクル（IMPL→AUTO ループ）
  e2e-cycleサブエージェント [sonnet] を使用

  Phase 1 - IMPL:
  - コンポーネント構造を作成
  - スタイリング・レスポンシブ対応
  - アクセシビリティ対応

  Phase 2 - AUTO:
  - agent-browserスキルで検証
  - 要素操作（snapshot -i → @refでclick, fill等）
  - 結果確認（snapshot -i, screenshot）
  - レスポンシブ検証（375px / 768px / 1024px）
  問題あり → Phase 1に戻って修正（通常1-3回で収束）
      ↓
ステップ2: 品質チェック（lint/format/build）
  quality-checkサブエージェント [haiku] を使用
      ↓
ステップ3: コミット
  simple-add-devサブエージェント [haiku] を使用
```

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
- [ ] [E2E][CYCLE] LoginForm UI実装 + agent-browser検証
- [ ] [E2E][CHECK] lint/format/build
- [ ] [E2E][COMMIT] コミット
```
