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
- Claude in Chrome と agent-browser は**完全に別物**

| 項目 | agent-browser | Claude in Chrome |
|------|--------------|------------------|
| **種類** | CLIツール（Playwright製） | MCPツール（Chrome拡張機能） |
| **実行方法** | `Bash`で直接コマンド実行 | `mcp__claude-in-chrome__*`ツール呼び出し |
| **ブラウザ** | Chromium（独立インスタンス） | ユーザーのChrome |
| **用途** | 自動テスト・検証 | ユーザーのブラウザ操作自動化 |

## Step 0: 環境セットアップ（メインスレッドで実行）

**Step 0 は必ずメインスレッドで実行する。サブエージェントには絶対に委譲しない。**
サブエージェントはセットアップ済みの環境でブラウザ操作だけを行う。

### 0-1. CLI 存在確認

```bash
which agent-browser 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

- `FOUND` → コマンドプレフィックス: `agent-browser`、0-2 へ
- `NOT_FOUND` → セットアップが必要。**AskUserQuestion** で確認：

> agent-browser CLI がインストールされていません。
> グローバルにインストールしてもよいですか？
> - `npm install -g agent-browser`

ユーザーが承認 → インストール実行 → 0-2 へ
ユーザーが拒否 → 中断

### 0-2. ブラウザ動作確認

```bash
agent-browser open about:blank 2>&1
```

- **成功**（`✓` が出力される）→ `agent-browser close` して 0-3 へ
- **失敗** → エラーメッセージを確認して分岐：

#### `Executable doesn't exist` エラー（Playwright ブラウザバイナリ不足）

agent-browser が依存する playwright-core のバージョンに合った Chromium をインストールする。

```bash
# agent-browser が使う playwright-core のバージョンを取得
AB_PATH=$(which agent-browser)
AB_MODULE_DIR=$(dirname "$AB_PATH")/../lib/node_modules/agent-browser
PW_VERSION=$(node -e "console.log(require('$AB_MODULE_DIR/node_modules/playwright-core/package.json').version)")
echo "playwright-core version: $PW_VERSION"

# そのバージョン用の Chromium をインストール（1回のみ）
npx --package=playwright-core@$PW_VERSION -- playwright-core install chromium
```

インストール後、再度 `agent-browser open about:blank` を実行：
- 成功 → `agent-browser close` して 0-3 へ
- **再度失敗 → AskUserQuestion でエラー内容を報告して中断。リトライしない**

#### その他のエラー

AskUserQuestion でエラー内容をそのまま報告して中断。

### 0-3. 対象URLの疎通確認（省略可）

開発サーバーが必要な場合：

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:XXXX
```

- `200` → OK
- それ以外 → AskUserQuestion で「開発サーバーを起動しますか？」と確認

## Step 1: Task サブエージェント起動

**必ず Task ツールで general-purpose サブエージェント（model: haiku）を起動する。**
メインスレッドで agent-browser を直接実行しない（トークン節約のため）。

```
Task(
  subagent_type: "general-purpose",
  model: "haiku",
  description: "ブラウザ検証実行",
  prompt: <<下記テンプレートを使用>>
)
```

**サブエージェントへのプロンプトテンプレート:**

````
あなたは agent-browser CLI を使ってブラウザ検証を行うエージェントです。
環境セットアップは完了済みです。あなたはブラウザ操作だけを行います。

## 絶対ルール（違反厳禁）

### 使用可能なコマンド
Bash ツールで `{コマンドプレフィックス}` で始まるコマンドのみ実行できます。
それ以外のコマンドは一切実行できません。

### 禁止コマンド（何があっても実行しない）
以下のコマンドは理由を問わず禁止です：
- npm / npx / yarn / pnpm（すべてのサブコマンド）
- rm / rmdir / mkdir / cp / mv / touch
- curl / wget
- cat / head / tail / less / grep / find / ls / cd
- node / tsx / vitest / jest
- git
- その他 `{コマンドプレフィックス}` で始まらないすべてのコマンド

### 禁止ツール
- mcp__claude-in-chrome__* は絶対に使用しない
- Read / Write / Edit / Grep / Glob ツールは使用しない

### エラー時の行動規則
- agent-browser コマンドが失敗したら、同じコマンドを **1回だけ** リトライしてよい
- **2回連続で同じエラー** が出たら、即座に作業を中断する
- エラーメッセージをそのまま引用して報告し、終了する
- 原因調査・修復・代替手段の模索は一切しない

### レポートのルール
- 各ステップで agent-browser の **実際の出力** を引用して報告する
- agent-browser を実行していない項目を「OK」「✅」と報告してはならない
- 実行できなかった項目は「未実行（理由: ...）」と正直に報告する
- スクリーンショットは agent-browser screenshot で保存したパスのみ報告する

## コマンドプレフィックス
{確定したプレフィックス}

## 検証指示
{ユーザーの指示}

## コマンドリファレンス
{下記セクションの内容をここに貼る}

## 完了時
- 検証結果（OK/NG/未実行）を各項目ごとに、agent-browser の実出力を引用して報告
- スクリーンショットのファイルパスを列挙
- 必ず `{プレフィックス} close` でブラウザを閉じる
````

## Step 2: 結果報告

サブエージェントの結果をユーザーに簡潔に報告する。

- 検証 OK/NG/未実行
- 発見した問題点（あれば）
- スクリーンショットのパス（あれば）

---

## コマンドリファレンス

### クイックスタート

```bash
agent-browser open <url>        # ページに移動
agent-browser snapshot -i       # 参照付きの対話要素を取得
agent-browser click @e1         # 参照で要素をクリック
agent-browser fill @e2 "text"   # 参照で入力欄に入力
agent-browser close             # ブラウザを閉じる
```

### コアワークフロー

1. ナビゲート: `agent-browser open <url>`
2. スナップショット: `agent-browser snapshot -i` (`@e1`, `@e2` のような参照付き要素を返す)
3. スナップショットから取得した参照を使用して対話
4. ナビゲーションまたは重要なDOM変更後に再スナップショット

### ナビゲーション

```bash
agent-browser open <url>      # URLに移動
agent-browser back            # 戻る
agent-browser forward         # 進む
agent-browser reload          # ページを再読み込み
agent-browser close           # ブラウザを閉じる
```

### スナップショット（ページ分析）

```bash
agent-browser snapshot        # 完全なアクセシビリティツリー
agent-browser snapshot -i     # 対話要素のみ（推奨）
agent-browser snapshot -c     # コンパクトな出力
agent-browser snapshot -d 3   # 深度を3に制限
```

### 対話（スナップショットの@refを使用）

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

### 情報取得

```bash
agent-browser get text @e1        # 要素のテキストを取得
agent-browser get value @e1       # 入力値を取得
agent-browser get title           # ページタイトルを取得
agent-browser get url             # 現在のURLを取得
```

### スクリーンショット

```bash
agent-browser screenshot          # 標準出力にスクリーンショット
agent-browser screenshot path.png # ファイルに保存
agent-browser screenshot --full   # フルページ
```

### 待機

```bash
agent-browser wait @e1                     # 要素を待つ
agent-browser wait 2000                    # ミリ秒待つ
agent-browser wait --text "Success"        # テキストを待つ
agent-browser wait --load networkidle      # ネットワークアイドルを待つ
```

### ビューポート

```bash
agent-browser set viewport 375 667        # モバイル
agent-browser set viewport 768 1024       # タブレット
agent-browser set viewport 1280 800       # デスクトップ
```

### セマンティックロケーター（参照の代替）

```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
```

### セッション（並列ブラウザ）

```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
```

### JSON出力（解析用）

```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

### デバッグ

```bash
agent-browser open example.com --headed  # ブラウザウィンドウを表示
agent-browser console                    # コンソールメッセージを表示
agent-browser errors                     # ページエラーを表示
```

### 認証状態の保存・復元

```bash
# ログイン後に状態を保存
agent-browser state save auth.json

# 別セッションで状態を復元
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

---

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
