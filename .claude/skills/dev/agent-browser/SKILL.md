---
name: dev:agent-browser
description: |
  agent-browser CLIでブラウザ検証をサブエージェント実行。
  E2Eテスト、UI確認、フォーム検証、スクリーンショット取得に使用。

  Trigger:
  agent-browser, ブラウザで確認, ブラウザ検証, E2E確認, UIテスト,
  スクリーンショット撮って, 画面確認, ブラウザテスト
context: fork
allowed-tools:
  - Read
  - Bash
  - Task
  - AskUserQuestion
---

# agent-browser CLIブラウザ検証（dev:agent-browser）

## 禁止事項（最優先）

- **mcp__claude-in-chrome__* ツールは絶対に使用しない**
- agent-browser は **Bash で実行する CLI ツール**。MCP ツールではない

## Step 0: 環境セットアップ（メインスレッドで実行）

**メインスレッドで実行。サブエージェントには委譲しない。**

### 0-1. CLI 存在確認

```bash
which agent-browser 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

- `FOUND` → コマンドプレフィックス: `agent-browser`、0-2 へ
- `NOT_FOUND` → **AskUserQuestion**: 「agent-browser CLI がありません。`npm install -g agent-browser` でインストールしますか？」
  - 承認 → インストール → 0-2 へ
  - 拒否 → 中断

### 0-2. ブラウザ動作確認

```bash
agent-browser open about:blank 2>&1
```

- **成功**（`✓` 表示）→ `agent-browser close` → 0-3 へ
- **失敗**（`Executable doesn't exist`）→ Playwright ブラウザバイナリ不足。修復：

```bash
PW_VERSION=$(node -e "console.log(require('$(npm root -g)/agent-browser/node_modules/playwright-core/package.json').version)")
npx --package=playwright-core@$PW_VERSION -- playwright-core install chromium
```

修復後に再度 `agent-browser open about:blank` → 成功なら続行、**再失敗なら AskUserQuestion で報告して中断**

- **その他のエラー** → AskUserQuestion で報告して中断

### 0-3. 対象URLの疎通確認（省略可）

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:XXXX
```

- `200` → OK
- それ以外 → AskUserQuestion で「開発サーバーを起動しますか？」

## Step 1: Task サブエージェント起動

1. `Read` で `references/subagent-prompt.md` を読み込む

2. テンプレートのプレースホルダを置換：
   - `{コマンドプレフィックス}` / `{確定したプレフィックス}` / `{プレフィックス}` → Step 0 で確定したプレフィックス
   - `{ユーザーの指示}` → ユーザーの検証指示

3. Task を起動：

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "ブラウザ検証実行",
  prompt: <<置換済みテンプレート>>
)
```

## Step 2: 結果報告

サブエージェントの結果をユーザーに簡潔に報告。

- 検証 OK/NG/未実行
- 発見した問題点
- スクリーンショットのパス
