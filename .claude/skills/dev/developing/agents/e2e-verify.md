# e2e-verify

## 役割

E2EのAUTOフェーズ: agent-browserスキル（CLIツール）で操作フローを検証する。

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
agent-browserスキルを使って操作フローを検証してください。

## 検証対象
- コンポーネント: {component_name}
- URL: http://localhost:3000/{path}

## 検証手順

### 1. ページを開く
agent-browser open http://localhost:3000/{path}

### 2. 初期状態確認
agent-browser snapshot -i    # インタラクティブ要素一覧取得
agent-browser screenshot     # スクリーンショット取得

### 3. 要素操作
# snapshot結果の@refを使用
agent-browser fill @e1 "test@example.com"   # フォーム入力
agent-browser click @e2                      # ボタンクリック
agent-browser wait --load networkidle        # 遷移待機

### 4. 結果確認
agent-browser snapshot -i    # 操作後の状態確認
agent-browser screenshot     # 操作後のスクリーンショット

### 5. レスポンシブ検証（必要な場合）
agent-browser set viewport 375 667     # モバイルサイズ
agent-browser screenshot
agent-browser set viewport 768 1024    # タブレットサイズ
agent-browser screenshot

### 6. 終了
agent-browser close

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
- snapshot -i で取得した@refを使って操作する
- 問題があれば詳細に報告
