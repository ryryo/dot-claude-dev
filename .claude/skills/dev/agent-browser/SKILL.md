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

## Step 0: 環境セットアップ

### 0-1. CLI 存在確認 → PREFIX 確定

実行可能なコマンド名を特定し、以降のステップで使う **PREFIX** として保持する。

```bash
which agent-browser 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

- `FOUND` → **PREFIX** にコマンド名を設定、0-2 へ
- `NOT_FOUND` → **AskUserQuestion**: 「agent-browser CLI がありません。`npm install -g agent-browser` でインストールしますか？」
  - 承認 → インストール実行 → **PREFIX** にコマンド名を設定、0-2 へ
  - 拒否 → 中断

### 0-2. ブラウザ動作確認

```bash
agent-browser open 'data:text/html,<h1>OK</h1>' 2>&1
```

- **成功**（`✓` 表示）→ `agent-browser close` → 0-3 へ
- **失敗**（`Executable doesn't exist`）→ Playwright ブラウザバイナリ不足。修復：

```bash
PW_VERSION=$(node -e "console.log(require('$(npm root -g)/agent-browser/node_modules/playwright-core/package.json').version)")
npx --package=playwright-core@$PW_VERSION -- playwright-core install chromium
```

修復後に再度 `agent-browser open 'data:text/html,<h1>OK</h1>'` → 成功なら続行、**再失敗なら AskUserQuestion で報告して中断**

- **その他のエラー** → AskUserQuestion で報告して中断

### 0-3. 対象URLの疎通確認（省略可）

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:XXXX
```

- `200` → OK
- それ以外 → AskUserQuestion で「開発サーバーを起動しますか？」

## Step 1: レポートフォーマット選択

ユーザーの検証指示を分析し、適切なフォーマットを1つ選択する。

| フォーマット | ファイル | 選択基準 |
|---|---|---|
| **ui-layout** | `references/formats/ui-layout.md` | 表示崩れ、レイアウト、デザイン確認が目的 |
| **interaction** | `references/formats/interaction.md` | フォーム入力、ボタン操作、画面遷移が目的 |
| **api-integration** | `references/formats/api-integration.md` | API通信、SSE、エラーハンドリングが目的 |
| **responsive** | `references/formats/responsive.md` | デバイスサイズ別の表示確認が目的 |

複数の目的がある場合は、**最も重要な目的**に合うフォーマットを選ぶ。

`Read` で該当フォーマットファイルを読み込む。

## Step 2: スクリーンショットディレクトリ作成

```bash
mkdir -p /tmp/agent-browser/{YYYYMMDD}-{slug}
```

- `{YYYYMMDD}`: 実行日（例: 20260219）
- `{slug}`: 検証内容を英語で短く表現（例: tarot-ui, login-form）

## Step 3: Task サブエージェント起動

1. `Read` で `references/subagent-prompt.md` を読み込む

2. テンプレートのプレースホルダを置換：
   - `{PREFIX}` → Step 0-1 で確定した PREFIX
   - `{ユーザーの指示}` → ユーザーの検証指示
   - `{SCREENSHOT_DIR}` → Step 2 で作成したディレクトリパス
   - `{レポートフォーマット}` → Step 1 で選択したフォーマット定義

3. Task を起動：

```
Task(
  subagent_type: "general-purpose",
  model: "haiku",
  description: "ブラウザ検証実行",
  prompt: <<置換済みテンプレート>>
)
```

## Step 4: 結果報告

サブエージェントの結果をユーザーに報告。

- サブエージェントのレポートをそのまま提示（省略しない）
- スクリーンショットがある場合は Read で画像を表示
- 検証 OK/NG/未実行 のサマリーを最後に添える
