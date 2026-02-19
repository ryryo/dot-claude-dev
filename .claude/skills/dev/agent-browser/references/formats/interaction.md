## レポートフォーマット: interaction（操作フロー確認）

### 各ステップで必ず実行するコマンド
- 操作**前後**で `snapshot -i` を実行し、**両方の出力を引用**（差分がわかるように）
- 操作後に `console` を実行し、**出力をそのまま引用**
- 各操作ステップで `screenshot {SCREENSHOT_DIR}/{NN}-{description}.png` を保存

### レポート構造

```
## 操作ステップ {N}: {操作内容}

### 操作前 snapshot -i
[出力引用]

### 実行したコマンド
{PREFIX} {command}

### 操作後 snapshot -i
[出力引用]

### console 出力
[出力引用、なければ「出力なし」]

### スクリーンショット
- {パス}
```
