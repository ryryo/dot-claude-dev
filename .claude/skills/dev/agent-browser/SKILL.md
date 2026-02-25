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

セットアップスクリプトを実行する。CLI インストール、ブラウザバイナリ修復、環境判定（ローカル / Cloud Code Web）をすべて自動処理する。

```bash
# SKILL_DIR はこの SKILL.md と同じディレクトリ
bash "${SKILL_DIR}/setup-agent-browser.sh" [--check-url URL]
```

- 最終行が `SUCCESS:<prefix>` → **PREFIX** を取得して Step 1 へ
- 最終行が `FAIL:<reason>` → AskUserQuestion で `<reason>` を報告して中断

### URL疎通確認

対象URLがある場合は `--check-url` オプションで渡す。スクリプトが疎通結果をログ出力する。
サーバーが起動していない場合は AskUserQuestion で「開発サーバーを起動しますか？」と確認する。

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
