# Cursor IDE / Composer を AppleScript・CDP で外部操作する実例調査メモ

調査日: 2026-06-15  
目的: 「Codex などの外部エージェントが、Cursor CLI ではなく AppleScript や UI 自動化経由で Cursor IDE / Composer / Agent を叩く」実例を、日本語・英語の公開記事・リポジトリから整理する。

---

## 1. 結論

現時点で、**「Codex が PM としてタスク分解し、AppleScript 経由で Cursor IDE / Composer 2.5 に実装を外注する」そのものズバリの公開記事・リポジトリは多くない**。

ただし、同じ思想にかなり近い実装は複数ある。

特に近いのは次の4系統。

1. **AppleScript / osascript で Cursor Composer を開き、プロンプトを貼り付けて送信する実装**
2. **iPhone / SMS / Telegram など外部入力から、ローカルの Cursor IDE を操作する実装**
3. **Chrome DevTools Protocol, CDP で Cursor の Electron DOM を直接操作する実装**
4. **Cursor Hooks / Claude Code Hooks から、Cursor のモデル切替やウィンドウ操作を自動化する実装**

実装の堅牢性で見ると、だいたい次の順になる。

| 方式 | 使いやすさ | 堅牢性 | 代表例 |
|---|---:|---:|---|
| AppleScript / pyautogui | 高い | 中〜低 | cursor-remote, sms-2-cursor, Gist |
| CDP / DOM 操作 | 中 | 中〜高 | OpenCLI, PocketCursor |
| Cursor Hooks + osascript | 中 | 中 | model-matchmaker, Claude Code Hooks記事 |
| Cursor CLI | 高い | 高い | 公式CLI。ただし「IDE内Composerを操作」ではない |

今回のX文脈に最も近いのは、**AppleScriptでCursor IDE内のComposerを開いてプロンプトを投げる系統**。より発展させるなら、CDPでComposer入力欄や応答DOMを直接扱う実装が参考になる。

---

## 2. なぜ Cursor CLI ではなく AppleScript / UI 自動化なのか

Cursor CLI は「ターミナルから Cursor Agent を使う」用途には向いている。CI、バッチ処理、非対話実行、スクリプト化には適している。

一方で、AppleScript / CDP が狙っているのは少し違う。

**いま開いている Cursor IDE の状態をそのまま使う**ことが主目的になる。

具体的には以下。

- 既存のワークスペース
- IDE内のComposer / Agent / Chat UI
- 選択中ファイルや現在のプロジェクト状態
- 差分表示・承認UI・チェックポイント
- モデル選択・Agentモード・PlanモードなどのUI状態
- Cursor内で蓄積された会話・文脈

CLIは「別プロセスでエージェントを起動する」寄りだが、AppleScriptやCDPは「人間が操作しているCursor IDEそのものを外部から操作する」寄り。

そのため、**Codex = PM / 管理者、Cursor Composer = 実装担当**のような分業を作る場合は、AppleScriptやCDPでIDE本体を叩く動機が強くなる。

---

## 3. 最重要リポジトリ・記事

### 3.1 Run Cursor Composer from Terminal / Gist

URL: https://gist.github.com/husniadil/b207227c31ff8a26e03bf00c3a53ebfd

#### 概要

`osascript cursor_prompt.scpt "..."` のように実行し、Cursor Composerへプロンプトを送るAppleScript実装。

#### 何をしているか

- Cursorを起動または前面化
- `Cmd+I` でComposerを開く
- クリップボードにプロンプトを入れる
- `Cmd+V` で貼り付け
- Returnで送信

#### 近さ

★★★★★

今回の話にかなり近い。最小構成で「外部プロセスからCursor Composerへ投げる」例として参考になる。

#### 注意点

- UIに依存する
- macOS Accessibility / Automation 権限が必要
- Cursor側のショートカットやUI変更に弱い

---

### 3.2 aerkn1/ai-orchestrator-pro

URL: https://github.com/aerkn1/ai-orchestrator-pro

#### 概要

複数AIをCLIアダプタで束ねるオーケストレーション環境。README上では Gemini, Claude Code, Cursor Auto, Codex 5, Warp Sonnet 4.5 などを使う構成になっている。

#### 重要ポイント

READMEでは以下のような設計が示されている。

- Ideation Cluster
- Development Cluster
- Marketing Cluster
- CLI-Based Execution
- Human-in-the-Loop
- Sub-Agent System
- Shared Workspace
- Cursor adapter auto-generates `.cursorrules`

開発フェーズでは、Cursorでコード生成し、Codexでレビューするような流れもある。

#### 特に重要なファイル

`adapters/run_cursor.sh`  
https://github.com/aerkn1/ai-orchestrator-pro/blob/main/adapters/run_cursor.sh

#### 何をしているか

`run_cursor.sh` では以下を行う。

- system/user prompt を読み込む
- プロジェクト用workspaceを作る
- `CURSOR_PROMPT.md` を作る
- `.cursorrules` を生成する
- Cursor workspace file を作る
- macOSではAppleScriptを生成する
- Cursorを開く
- AppleScriptで `Cmd+I` を押してComposerを開く
- クリップボードのプロンプトを貼り付ける
- Returnで生成開始する

該当箇所では、AppleScriptに以下のような意図が書かれている。

```applescript
-- AppleScript to trigger Cursor Composer and paste the prompt
```

#### 近さ

★★★★★

「複数AIをオーケストレーションし、Cursorを実装担当にする」という意味でかなり近い。

#### 見るべき点

- `.cursorrules` を自動生成してからCursorを叩く設計
- Cursorを単なるCLIではなく、IDEとして開いて自動生成を観察する設計
- CodexやClaudeなど他AIとの役割分担

---

### 3.3 yasegev/cursor-remote

URL: https://github.com/yasegev/cursor-remote

#### 概要

iPhoneからMac上のCursor IDEを操作するためのシステム。

READMEでは、iPhone app と Mac Agent が Firebase 経由でつながり、Mac AgentがCursorを操作する構成になっている。

#### README上の機能

- Send prompts to Cursor from iPhone
- View status updates and responses
- Approve/deny tool actions remotely
- Mac Agent listens for prompts from Firebase
- Pastes prompts into Cursor using AppleScript
- Monitors Cursor for approval requests

#### 特に重要なファイル

`mac-agent/services/cursor_controller.py`  
https://github.com/yasegev/cursor-remote/blob/main/mac-agent/services/cursor_controller.py

#### 何をしているか

`CursorController` クラスが、AppleScriptでCursor IDEを操作する。

主な実装:

- Cursorが起動中か確認
- Cursorをactivate
- Cursorをlaunch
- プロンプトをクリップボードへコピー
- Composerなら `Cmd+I`
- Chatなら `Cmd+L`
- `Cmd+V` で貼り付け
- Returnで送信
- Approval dialogを検出
- Allow / Approve / Accept ボタンをクリック
- Deny / Cancel / Reject ボタンをクリック
- 生成中かどうかをStopボタンの有無で推定
- 最後の応答をコピーしようとする

#### 近さ

★★★★★

「外部エージェント / 外部UIから、ローカルのCursor IDEを実装ワーカーとして操作する」意味で非常に近い。

#### 参考になる点

AppleScript経由で実用化する場合、このリポジトリの `CursorController` はかなり参考になる。

特に以下が重要。

- ComposerとChatを切り替える引数 `use_composer`
- `Cmd+I` と `Cmd+L` の使い分け
- approval dialog の検出
- approve / deny ボタンの操作
- `is_agent_running()` でStopボタンを探す実装

---

### 3.4 Zenn: Cursorのコミットメッセージ作成自動化スクラップ

URL: https://zenn.dev/kabeya/scraps/ccaab43cf56e02

#### 概要

日本語で見つかった中ではかなり近い事例。VS Code / Cursor拡張から、Cursor Composerへテキストを送る方法としてAppleScriptを試している。

#### 何をしているか

記事中では、Cursor Composerへ外部からテキストを送るために、以下のような方針を試している。

- System Eventsでキーストロークをシミュレート
- クリップボードに文字列を書き込む
- `tell application "Cursor" to activate`
- `Cmd+V` でComposerへ貼り付け
- Returnで送信

#### 近さ

★★★★☆

日本語ではかなり近い。ただし「Composerとの会話取得」については難しさも書かれており、UI自動化の限界も見える。

#### 参考になる点

- 日本語でAppleScript経由のCursor Composer操作を検討している
- 失敗・制約も含めて実装上のリアルさがある
- Cursor拡張からCursor Composerを叩くという少し変則的な構成

---

## 4. CDP / DOM 経由で Cursor IDE を操作する実装

AppleScriptは人間操作の再現なので実装は簡単だが、UIの変化やフォーカス事故に弱い。より堅牢にするなら、CursorがElectronアプリであることを利用し、Chrome DevTools ProtocolでDOMを操作する方法がある。

---

### 4.1 jackwener/OpenCLI Cursor adapter

URL: https://github.com/jackwener/OpenCLI

Cursor adapter document:  
https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/desktop/cursor.md

#### 概要

OpenCLIのCursor adapterは、Cursor IDEをCDP経由で操作する。

ドキュメントでは、CursorはElectron / VS Code forkなので、CDPで内部UIを操作し、Composer操作やchat session操作ができると説明されている。

#### できること

- `opencli cursor status`
- `opencli cursor dump`
- `opencli cursor screenshot`
- `opencli cursor send "message"`
- `opencli cursor ask "message"`
- `opencli cursor read`
- `opencli cursor composer "prompt"`
- `opencli cursor model`
- `opencli cursor extract-code`
- `opencli cursor history`
- `opencli cursor export`

#### 特に重要なファイル

`clis/cursor/composer.js`  
https://github.com/jackwener/OpenCLI/blob/main/clis/cursor/composer.js

#### 何をしているか

`composer.js` は以下を行う。

- `Meta+I` でComposerを開く
- DOM上のComposer入力欄を探す
- `document.execCommand('insertText', false, text)` でテキスト挿入
- Enterで送信

#### 近さ

★★★★★

AppleScriptではないが、「Cursor IDE内のComposerを外部から叩く」実装としては非常に近い。堅牢化するならこの方向が本命。

#### 必要条件

Cursorをremote debugging port付きで起動する必要がある。

```bash
/Applications/Cursor.app/Contents/MacOS/Cursor --remote-debugging-port=9226
```

---

### 4.2 qmHecker/pocket-cursor

URL: https://github.com/qmHecker/pocket-cursor

#### 概要

Telegramと実行中のCursor IDEを双方向同期するツール。

READMEでは、Telegramから送ったメッセージをCursorのLexical editorへ注入し、CursorのAI応答をDOM監視してTelegramへ返す、と説明されている。

#### README上の特徴

- Telegram → Cursor: messages from your phone are typed into Cursor
- Cursor → Telegram: AI responses stream back to your phone
- Uses Chrome DevTools Protocol
- Cursor is Electron app, Chromium under the hood
- Launching with debug port gives full DOM access via WebSocket

#### 特に重要な実装

`cursor_send_message(text, raw=False)` では以下を行う。

- CDPでCursorのactive connectionを取得
- DOM上の入力欄を探す
- `.aislash-editor-input` または `[data-lexical-editor="true"]` を探索
- editorをfocus
- `Input.insertText` でテキスト挿入
- send buttonをDOM selectorで探してクリック

#### 近さ

★★★★☆

「Codex → Cursor」ではないが、外部UIからCursor IDEを操作する実装として非常に参考になる。

#### AppleScriptとの違い

AppleScriptは人間のキーボード操作に近い。PocketCursorはElectron内部のDOMを直接見ている。

そのため、以下の点で強い。

- 応答の読み取りがしやすい
- スクリーンショットやDOM取得ができる
- 入力欄や送信ボタンを直接特定できる
- 複数ワークスペースやチャットの追跡が可能

一方で、CursorをCDP有効で起動する必要がある。

---

## 5. CursorのUIをキーボード自動化する周辺実装

### 5.1 coyvalyss1/model-matchmaker

URL: https://github.com/coyvalyss1/model-matchmaker

#### 概要

Cursor / Claude Code 用のlocal hook。プロンプト送信前に内容と現在のモデルを見て、適切なモデルを推奨する。

Auto-Switchを有効にすると、Cursorのモデル切替をキーボード自動化で行う。

#### README上の説明

Auto-Switchでは以下を行う。

1. `Cmd+/` でモデルドロップダウンを開く
2. モデル名をタイプして検索
3. Enterでモデル選択
4. 必要に応じてメッセージ送信
5. Terminal windowが一瞬開いて閉じる

#### 特に重要なファイル

`hooks/auto-switch-model.sh`  
https://github.com/coyvalyss1/model-matchmaker/blob/main/hooks/auto-switch-model.sh

#### 何をしているか

- Cursorのモデルドロップダウンを `Cmd+/` で開く
- AppleScriptで検索語をタイプ
- Enterで選択
- Cursor子プロセスではAccessibility権限が足りないため、Terminal.appをプロキシとして使う

#### 近さ

★★★★☆

プロンプト投入ではなくモデル切替だが、Cursor IDEのUIをAppleScriptで操作する実装として参考になる。

#### 実務的に重要な知見

Cursorの子プロセスから直接AppleScript/Accessibility操作をすると権限で詰まる場合がある。そこでTerminal.app経由でosascriptを実行している。

これは、CodexやClaude CodeのhookからCursor UIを操作するときにも参考になる。

---

### 5.2 jacksonbaxter/sms-2-cursor

URL: https://github.com/jacksonbaxter/sms-2-cursor

#### 概要

SMSからCursor IDEへコーディング指示を送る自動化システム。

ワークフローは以下。

SMS → Google Voice Gateway → Email → Local Machine → Cursor IDE → File Output → Email → SMS

#### README上の構成

- Email Handler
- Cursor Automation
- File Watcher
- Orchestrator

Cursor Automationは、pyautoguiとAppleScriptでCursor IDEを操作する。

#### 特に重要なファイル

`cursor_automation.py`  
https://github.com/jacksonbaxter/sms-2-cursor/blob/main/cursor_automation.py

#### 何をしているか

- AppleScriptでCursorをactivate
- System EventsでCursorプロセスをfrontmostにする
- pyautoguiでAgent panelを検出
- `cmd+i` でAgent panelを開く
- pyautoguiでプロンプトをタイプ
- Enterで送信
- Cursorに完了後の要約ファイルを書かせる
- File Watcherがそのファイルを読んでSMS返信する

#### 近さ

★★★★☆

外部からローカルCursorを操作する実装として近い。特に「応答取得をファイル出力に逃がす」設計が参考になる。

---

## 6. 日本語の周辺記事

### 6.1 Qiita: Codex Desktop の Computer UseでmacOSを操作

URL: https://qiita.com/nogataka/items/ad8800f067eb5d4a9e54

#### 概要

Cursor特化ではないが、Codex DesktopのComputer UseでmacOS GUIを操作するワークフローの日本語記事。

#### 参考になる点

- Codex Desktopが画面を見て操作する発想
- Screen Recording / Accessibility 権限
- Desktop app とCLIの使い分け
- GUI操作を含むE2E作業の設計

#### 近さ

★★★☆☆

Cursor Composerを直接叩く記事ではないが、「CodexがmacOS GUIを操作する」という観点では参考になる。

---

### 6.2 Zenn: Claude Code HooksでGhostty/Cursor等を最前面化

URL: https://zenn.dev/toono_f/articles/claude-code-hooks-window-focus

#### 概要

Claude Code Hooksから、作業完了時などにGhostty / Cursor / Windsurf / VS Codeなどを最前面化する記事。

#### 参考になる点

- Hookから `osascript` を呼ぶ
- `tell application "Cursor" to activate`
- 作業完了時にユーザーへ視覚的に知らせる
- macOSアプリ操作にosascriptを使う基本パターン

#### 近さ

★★★☆☆

Composerへプロンプト投入する実装ではないが、Hook + osascript + Cursor の構成として参考になる。

---

### 6.3 Cursor Forum: RaycastからComposerへ貼り付け

URL: https://forum.cursor.com/t/correctly-paste-multiline-text-into-chat-or-composer-e-g-from-raycast/38005

#### 概要

RaycastのScript Commandから、整形した複数行テキストをCursorのChat / Composerへ正しく貼り付ける話。

#### 参考になる点

- Cursorの入力欄への複数行貼り付け問題
- Raycast Script Command
- AppleScript / pasteboard 経由の貼り付け

#### 近さ

★★★☆☆

小技寄りだが、Cursor Composer入力欄の扱いでは参考になる。

---

## 7. 実装パターン別の整理

### 7.1 AppleScriptで叩く最小構成

一番単純な構成。

```text
外部エージェント / スクリプト
  ↓
pbcopy でプロンプトをクリップボードへ
  ↓
tell application "Cursor" to activate
  ↓
System Events: Cmd+I
  ↓
System Events: Cmd+V
  ↓
Return
  ↓
Cursor Composer が実行
```

#### メリット

- 実装が簡単
- Cursorの公式APIがなくても動く
- 人間の操作をそのまま再現できる
- 既存のCursor IDE状態をそのまま使える

#### デメリット

- UI変更に弱い
- フォーカス事故が起きやすい
- Accessibility権限が必要
- 失敗検知が難しい
- 応答取得が難しい
- 並列実行に向かない

#### 代表例

- Run Cursor Composer from Terminal Gist
- ai-orchestrator-pro `run_cursor.sh`
- cursor-remote `CursorController`
- sms-2-cursor
- ZennのComposer送信スクラップ

---

### 7.2 AppleScript + ファイル出力で応答取得する構成

Cursorの応答を画面から読むのは難しいため、プロンプト側で「完了したら指定ファイルに要約を書いて」と指示する方式。

```text
外部スクリプト
  ↓
Cursor Composerへ指示
  ↓
Cursor Agentがコード編集
  ↓
完了後、summary_task_xxx.txt を書く
  ↓
File Watcherがそのファイルを読む
  ↓
外部システムへ返信
```

#### メリット

- 応答取得が単純
- UI読み取りに依存しない
- SMS/Slack/Telegram連携に向く

#### デメリット

- Cursor Agentにファイルを書かせる必要がある
- 失敗時にファイルが出ない
- 実装結果の完全なレビューには不十分

#### 代表例

- sms-2-cursor

---

### 7.3 CDPでCursorのDOMを直接操作する構成

Cursorをremote debugging port付きで起動し、Electron内部のDOMを直接操作する。

```text
外部エージェント / CLI
  ↓
CDP WebSocket
  ↓
Cursor Electron DOM
  ↓
Lexical editorへ Input.insertText
  ↓
Send button click
  ↓
DOM監視で応答取得
```

#### メリット

- AppleScriptより制御しやすい
- 応答取得がしやすい
- 入力欄や送信ボタンをDOM selectorで探せる
- スクリーンショット・DOM dump・履歴抽出などが可能
- フォーカス事故が少ない

#### デメリット

- CursorをCDP有効で起動する必要がある
- DOM構造変更には弱い
- セキュリティ面の配慮が必要
- 実装がAppleScriptより複雑

#### 代表例

- OpenCLI Cursor adapter
- PocketCursor

---

### 7.4 HookからCursor UIを操作する構成

Cursor Hooks / Claude Code Hooks / Codex側のイベントから、osascriptやキーボード操作を発火する。

```text
beforeSubmitPrompt / Stop Hook / 外部イベント
  ↓
シェルスクリプト
  ↓
osascript / Terminal.app proxy
  ↓
Cursor UI操作
```

#### メリット

- ユーザー操作の前後に介入できる
- モデル切替やウィンドウ前面化に向く
- PMエージェントがワーカーIDEを制御する入口になる

#### デメリット

- 権限まわりが複雑
- 実行元プロセスによってAccessibility権限が足りないことがある
- Terminal.appなどをプロキシにする必要がある場合がある

#### 代表例

- model-matchmaker
- Claude Code HooksでCursorを前面化するZenn記事

---

## 8. Codex PM → Cursor実装ワーカー構成を作るなら

今回のX文脈に近い構成を作るなら、段階的には以下がよさそう。

### Phase 1: AppleScriptで最小動作

まずは以下だけ作る。

```bash
codex_orchestrator.sh "実装タスク本文"
```

内部で行うこと。

1. タスク本文を一時ファイルに保存
2. プロンプトを整形
3. `pbcopy`
4. Cursorをactivate
5. `Cmd+I`
6. `Cmd+V`
7. Return

参考:

- Run Cursor Composer from Terminal Gist
- ai-orchestrator-pro `run_cursor.sh`
- cursor-remote `paste_and_submit_prompt`

### Phase 2: `.cursorrules` / `.cursor/rules` 自動生成

Cursorへ投げる前に、プロジェクトルールを生成する。

```text
.cursor/rules/task-worker.mdc
.cursorrules
CURSOR_PROMPT.md
```

参考:

- ai-orchestrator-pro
- PocketCursor `pocket-cursor.mdc`

### Phase 3: 完了検知を入れる

最初はUI読み取りではなく、ファイル出力でよい。

プロンプト末尾に以下を入れる。

```text
作業が完了したら、必ず .agent_runs/latest_result.md に以下を書いてください。
- 実施内容
- 変更ファイル
- テスト結果
- 残タスク
```

外側のPMスクリプトは、このファイルの更新をwatchする。

参考:

- sms-2-cursor

### Phase 4: Approval / Tool confirmation対策

Cursorの承認UIが出たら検知・通知する。

AppleScriptなら:

- Allow / Approve / Accept ボタンを探す
- Deny / Cancel / Reject ボタンを探す
- Stopボタン有無で生成中判定

参考:

- cursor-remote `detect_approval_dialog()`
- cursor-remote `click_approve_button()`
- cursor-remote `is_agent_running()`

### Phase 5: CDP化

AppleScriptが不安定になったら、CDPに寄せる。

```bash
/Applications/Cursor.app/Contents/MacOS/Cursor --remote-debugging-port=9226
```

その上で、CDPから以下を行う。

- Composerを開く
- DOMで入力欄を探す
- `Input.insertText`
- Send button click
- 応答DOMを読む
- conversation export

参考:

- OpenCLI Cursor adapter
- PocketCursor

---

## 9. 実装するときの注意点

### 9.1 Accessibility / Automation 権限

AppleScript / System Events / pyautogui系はmacOSのAccessibility権限が必要。

特に以下に注意。

- 実行しているターミナルアプリ
- Terminal.app
- iTerm2
- Cursor
- Python実行環境
- Codex Desktop / Claude Code Desktop
- Raycast

実行元が変わると権限も変わる。

model-matchmakerでは、Cursor子プロセスが権限を持たない問題を避けるため、Terminal.appをプロキシにしていた。

### 9.2 フォーカス事故

AppleScript方式では、意図しないアプリに貼り付けるリスクがある。

対策:

- `tell application "Cursor" to activate`
- `frontmost of process "Cursor"` を確認
- 実行直前にウィンドウタイトルを確認
- 失敗時は送信せず停止
- クリップボード復元

### 9.3 UI変更

CursorのUIやショートカットが変わると壊れる。

対策:

- ショートカットを設定化
- `Cmd+I` / `Cmd+L` を切り替え可能にする
- 送信前に入力欄フォーカス確認
- CDP方式なら複数selectorを持つ

### 9.4 応答取得

AppleScriptだけでCursorの応答を読むのは難しい。

選択肢:

1. Cursorに完了ファイルを書かせる
2. `Cmd+Shift+C` 等で最後の応答コピーを試す
3. Accessibility treeを読む
4. CDPでDOMを読む
5. CursorのSQLite state DBを読む

実用面では、まずは **完了ファイル方式** が簡単。

### 9.5 セキュリティ

外部からCursorに命令を送る構成は、実質的にローカルマシン上で任意操作が可能になる。

対策:

- 信頼できる送信元だけ許可
- 危険コマンドはdeny
- `rm -rf`, credential, secret, token, private key などをブロック
- 実行前に承認ステップを入れる
- ログを残す
- kill switchを用意する

参考:

- model-matchmakerのdeny/allow/rate limit/kill switch
- PocketCursorのcommand rules

---

## 10. 参考リンク一覧

### AppleScript / UI自動化系

- Run Cursor Composer from Terminal / Gist  
  https://gist.github.com/husniadil/b207227c31ff8a26e03bf00c3a53ebfd

- ai-orchestrator-pro  
  https://github.com/aerkn1/ai-orchestrator-pro

- ai-orchestrator-pro / run_cursor.sh  
  https://github.com/aerkn1/ai-orchestrator-pro/blob/main/adapters/run_cursor.sh

- cursor-remote  
  https://github.com/yasegev/cursor-remote

- cursor-remote / cursor_controller.py  
  https://github.com/yasegev/cursor-remote/blob/main/mac-agent/services/cursor_controller.py

- sms-2-cursor  
  https://github.com/jacksonbaxter/sms-2-cursor

- sms-2-cursor / cursor_automation.py  
  https://github.com/jacksonbaxter/sms-2-cursor/blob/main/cursor_automation.py

- Cursor Forum: Correctly paste multiline text into Chat or Composer  
  https://forum.cursor.com/t/correctly-paste-multiline-text-into-chat-or-composer-e-g-from-raycast/38005

### CDP / DOM操作系

- OpenCLI  
  https://github.com/jackwener/OpenCLI

- OpenCLI Cursor adapter doc  
  https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/desktop/cursor.md

- OpenCLI / composer.js  
  https://github.com/jackwener/OpenCLI/blob/main/clis/cursor/composer.js

- OpenCLI / send.js  
  https://github.com/jackwener/OpenCLI/blob/main/clis/cursor/send.js

- PocketCursor  
  https://github.com/qmHecker/pocket-cursor

### Cursor Hooks / モデル切替系

- model-matchmaker  
  https://github.com/coyvalyss1/model-matchmaker

- model-matchmaker / auto-switch-model.sh  
  https://github.com/coyvalyss1/model-matchmaker/blob/main/hooks/auto-switch-model.sh

- model-matchmaker / model-advisor.sh  
  https://github.com/coyvalyss1/model-matchmaker/blob/main/hooks/model-advisor.sh

### 日本語記事

- Zenn: Cursorのコミットメッセージ作成自動化スクラップ  
  https://zenn.dev/kabeya/scraps/ccaab43cf56e02

- Qiita: Codex Desktop の Computer UseでmacOSを操作  
  https://qiita.com/nogataka/items/ad8800f067eb5d4a9e54

- Zenn: Claude Code HooksでGhostty/Cursor等を最前面化  
  https://zenn.dev/toono_f/articles/claude-code-hooks-window-focus

---

## 11. 個人的なおすすめ順

### まず読むべき

1. `yasegev/cursor-remote` の `cursor_controller.py`
2. `aerkn1/ai-orchestrator-pro` の `run_cursor.sh`
3. ZennのCursor Composer送信スクラップ
4. `jackwener/OpenCLI` の Cursor adapter

### AppleScriptで最小実装するなら

- `cursor-remote` の `CursorController` を参考にする
- `run_cursor.sh` の `.cursorrules` / workspace setup を参考にする
- 応答取得は `sms-2-cursor` のようにファイル出力に逃がす

### 長期的に安定させるなら

- OpenCLI / PocketCursor のようにCDP化する
- DOM selectorを複数用意する
- 応答取得・スクショ・履歴exportもCDPで扱う
- ApprovalだけはAppleScript/Accessibilityと併用する可能性がある

---

## 12. まとめ

今回の調査で確認できたことは以下。

- Cursor CLIは存在するが、IDE内Composerを直接操作する目的とは少し違う。
- AppleScript経由でCursor IDE / Composerを叩く実装は実際に複数ある。
- 日本語ではZennのComposer送信スクラップが近い。
- 英語では `cursor-remote`, `ai-orchestrator-pro`, `sms-2-cursor` がAppleScript系の実例として有用。
- より堅牢な方向では `OpenCLI` と `PocketCursor` のCDP方式が参考になる。
- Codex PM → Cursor実装ワーカー構成を作るなら、最初はAppleScriptで十分。ただし応答取得や安定運用まで考えるなら、CDP化を検討した方がよい。
