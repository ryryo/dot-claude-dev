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

**agent-browserスキル**（CLIツール）で検証:

```bash
agent-browser open <url>              # ページを開く
agent-browser snapshot -i             # インタラクティブ要素一覧（@ref付き）
agent-browser click @e1               # @refで要素をクリック
agent-browser fill @e1 "text"         # @refでフォーム入力
agent-browser screenshot              # スクリーンショット取得
agent-browser set viewport W H        # ビューポートサイズ変更
agent-browser close                   # ブラウザ閉じる
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
```

## アクセシビリティ要件

| 項目 | 要件 |
|------|------|
| キーボード | Tab移動可能、Enter/Space操作可能 |
| aria属性 | 適切なrole, aria-label |
| コントラスト | WCAG 2.1 AA以上 |
| フォーカス | 視覚的にわかる |

## エージェント構成

```
e2e-cycle(sonnet) → quality-check(haiku) → spot-review(sonnet+OpenCode) → [FAIL時] spot-fix(opus)
```

| Step | Agent | 責務 |
|------|-------|------|
| 1 CYCLE | e2e-cycle | UI実装 → agent-browser検証ループ |
| 2 CHECK | quality-check | lint/format/build |
| 3 SPOT | spot-review | commit後の即時レビュー(+OpenCode)。検出のみ |
| 3b FIX | spot-fix | SPOT FAIL時: 修正→CHECK→再SPOT（最大3回） |

## エラー時の対応

1. **検証失敗**: 実装を修正 → 再検証（e2e-cycle内でループ）
2. **3回失敗**: 問題を報告、ユーザーに確認
3. **ツールエラー**: 開発サーバー確認、再試行

## 関連スキル

- **dev:developing**: E2Eタスクの実装
- **dev:story**: E2Eタスクの生成
