# Cursor IDE / Agent Window 外部操作リサーチ

調査日: 2026-06-15  
対象: Codex から Cursor IDE / Cursor Agent window を worker として叩く transport 設計  
方針: **Cmd+V / pasteboard / clipboard 注入を主経路にしない**

---

## 1. 結論

この資料の結論は、初期調査時点から更新する。

採用する主経路:

1. **macOS: Cursor を remote debugging port 付きで起動し、CDP で Agent Window の DOM / Tiptap editor を直接操作する**
2. **AppleScript: `Cursor Agents` window の前面化、window 選択、補助クリック、ショートカット smoke に使う**

採用しない主経路:

- `pbcopy` / pasteboard に prompt を置く
- `Cmd+V` で prompt を貼る
- `Cmd+I -> Cmd+V -> Return` を標準経路にする
- `AXTextArea` direct set を標準 prompt 投入経路にする
- UI 応答テキストを AppleScript で読んで完了判定する
- non-macOS Cursor IDE automation

既存の公開実装には `Cmd+V` 系が多い。ただし、今回の設計ではそれらは「実例として存在する」「権限・focus・clipboard 汚染で壊れやすい」というリスク確認として扱い、実装の主経路にはしない。

---

## 2. なぜ Cmd+V 系を避けるか

`Cmd+V` / clipboard 経路は実装が簡単だが、worker transport としては弱い。

- clipboard を破壊する。
- focus 事故で別アプリに prompt を貼る可能性がある。
- 複数行 prompt の整形や IME 状態に影響される。
- Cursor window / panel / selected input の状態に強く依存する。
- 成功しても「どの入力欄に入ったか」を機械的に保証しにくい。
- 既存のユーザー作業中 prompt や入力途中の内容を上書きしやすい。

そのため、macOS IDE 経路では以下を優先する。

```text
Cursor Agents window
  -> CDP で Cursor Agents target を検出
  -> Tiptap / ProseMirror contenteditable を focus
  -> Input.insertText で prompt を投入
  -> DOM text を read-back
  -> submit は明示 opt-in かつ send 経路検証後のみ
  -> 完了判定は UI ではなく git diff / tests / result file
```

---

## 3. Transport 方針

| Transport | 位置づけ | 入力方法 | 完了判定 | 採用判断 |
|---|---|---|---|---|
| `mac-ide-cdp` | macOS default | CDP `Input.insertText` または DOM/Lexical API | DOM/result file + diff/test | 採用 |
| `mac-ide-applescript` | macOS helper | window focus / 補助操作 | Codex の diff/test | 補助採用 |
| `deeplink` | 手動確認 fallback | Cursor deeplink prefill | 人間確認 + diff/test | 限定採用 |
| `clipboard-paste` | legacy | `pbcopy` + `Cmd+V` | 不安定 | 非採用 |

`mac-ide-applescript` は Cursor IDE の UI automation であり、安定 API ではない。前面化や補助操作には使えるが、長文 prompt の no-clipboard 投入は現行 build では CDP のほうが実測上安定している。そのため、Codex 側の検収 contract を強くする。

---

## 4. mac-ide-applescript の具体実装

### 4.1 Preflight

委任前に確認する。

```bash
test "$(uname -s)" = Darwin
test -d /Applications/Cursor.app
command -v osascript
```

さらに runtime で確認する。

- Cursor process が存在する。
- `Cursor Agents` window が開いている。
- 対象 workspace が Agent window の workspace selector で選ばれている。
- edit 委任の場合、入力欄 toolbar に `Ask` chip が残っていない。
- System Events が Cursor の Accessibility tree を読める。

`Ask` chip が残っていると、Cursor は「Ask mode なので編集できない」と返し、ファイル編集を行わない。これは実測済み。

複数の Cursor / Agent window 候補がある場合は fail closed にする。window title だけで workspace を断定せず、対象 window をユーザーに前面化してもらうか、Computer Use / CDP で target を明示選択する。

### 4.2 Prompt 投入

AppleScript 単独での no-clipboard prompt 投入は、現行 Cursor Agents build では標準経路にしない。

実測結果:

- `Cursor Agents` window の activate / focus は可能。
- Agent prompt editor は CDP では `.tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]` として見える。
- 同じ prompt editor は Accessibility tree では安定した writable `AXTextArea` として見えなかった。
- そのため、`AXTextArea` を探索して `value` を direct set する実装は fail closed にする。

```applescript
tell application "Cursor" to activate
delay 1

tell application "System Events"
  if not (exists process "Cursor") then error "Cursor process is not available"
  tell process "Cursor"
    set frontmost to true
    if exists window "Cursor Agents" then
      tell window "Cursor Agents" to set focused to true
      -- focus/preflight helper only
    end if
  end tell
end tell
```

実装上の注意:

- AppleScript でできることは「前面化」「Agent window 確認」「補助クリック」「ショートカット smoke」に分ける。
- `AXTextArea` direct set は、将来の Cursor build で実測できた場合だけ opt-in experimental として戻す。
- `Cmd+V` fallback は標準では持たない。必要なら明示 opt-in の legacy fallback に隔離する。
- `submit` は必ず明示 opt-in にする。

prompt 投入と read-back は CDP 経路で行う。

### 4.3 Submit

送信も UI 状態依存なので、原則は分離する。

- no-submit smoke: prompt が入力欄へ入ることだけを確認する。
- submit smoke: `--submit` 指定時だけ送信する。
- 実編集 smoke: `Ask` chip を外した状態で送信する。

送信方法の優先度:

1. CDP で send button DOM selector が安定して確認できる場合のみ DOM click。
2. focused editor に対する CDP key event。
3. AppleScript shortcut は smoke 済みの場合だけ補助経路として使う。

### 4.4 `Ask` chip / mode 切替

現時点では `Ask` chip を AppleScript だけで安定して外す実装は採用しない。

理由:

- `Cursor Agents` window の Accessibility tree は大きく、全探索が遅い。
- prompt editor から parent / sibling toolbar を AppleScript で安定して辿れない場合がある。
- Computer Use では `Remove Ask` button が明確に見えてクリックできたが、AppleScript から同じ経路を安定化するには追加検証が必要。
- Electron / VS Code fork の AX tree は `AXGroup` や `AXScrollArea` のネスト、画面幅、サイドバー状態、diff / approval sheet の表示で順序が変わる。

したがって、edit 委任の preflight contract は次の通り。

```text
Before submit:
- Cursor Agents window is open.
- Target workspace is selected.
- Ask chip is absent.
- Input mode is edit-capable.
```

`Ask` が残っている場合は preflight warning / failure とし、Cursor に送る前に人間または Computer Use で外す。

AppleScript 経路で manual / preflight に残すもの:

- 正しい workspace の Agent window を開く。
- Agent / edit-capable mode にする。
- approval dialog / modal を閉じる。
- model selection。
- Run mode / allowlist 設定。
- 複数 window の target 選択。

---

## 5. CDP / DOM 経路の具体実装候補

CDP は Cmd+V を避ける長期本命になり得る。Cursor は Electron app なので、remote debugging port 付きで起動すると DevTools Protocol から DOM を操作できる。

参考実装:

- OpenCLI Cursor adapter: https://github.com/jackwener/OpenCLI
- PocketCursor: https://github.com/qmHecker/pocket-cursor
- Chrome DevTools Protocol Input domain: https://chromedevtools.github.io/devtools-protocol/tot/Input/

### 5.1 起動

手動起動:

```bash
/Applications/Cursor.app/Contents/MacOS/Cursor \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226
```

PocketCursor は `cursor --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222` のような起動を前提にしている。

Cursor が CDP なしで既に起動している場合、後から同じ process に CDP port を生やすことは前提にしない。一度終了して CDP flags 付きで起動する運用にする。

### 5.2 Target discovery

CDP endpoint から Cursor window target を列挙する。

```bash
curl http://127.0.0.1:9226/json
curl http://127.0.0.1:9226/json/version
```

実装手順:

1. `/json` を読む。
2. `/json/version` から browser-level `webSocketDebuggerUrl` も取得する。
3. `type == "page"` の target を選ぶ。
4. `devtools://` target は除外する。
5. `title` から workspace 名を推定する。
6. `webSocketDebuggerUrl` に接続する。
7. 複数 workspace がある場合は、Codex prompt の workspace absolute path / name と照合する。

必要に応じて、対象 window は次の順で前面化する。

1. CDP `Page.bringToFront`。
2. browser-level WebSocket の `Target.activateTarget`。
3. macOS 補助として `osascript -e 'tell application "Cursor" to activate'`。

これは前面化用であり、入力に clipboard は使わない。

### 5.3 Text insertion without Cmd+V

候補は2つ。主経路は CDP native の `Input.insertText` とする。

#### A. CDP `Input.insertText`

PocketCursor は CDP の `Input.insertText` を使う。これは OS clipboard を使わない。

概念コード:

```python
def cdp_insert_text(ws, text):
    ws.send(json.dumps({
        "id": next_id(),
        "method": "Input.insertText",
        "params": {"text": text},
    }))
    return json.loads(ws.recv())
```

前提:

- 先に `Runtime.evaluate` で対象の Lexical editor / contenteditable input を focus する。
- selection を末尾へ collapse する。
- その後 `Input.insertText` に `{ text }` を送る。
- 挿入後に `editor.textContent.trim()` などで read-back する。

#### B. DOM `document.execCommand('insertText')`

OpenCLI の `composer.js` は、Composer を開いた後に DOM 上の入力欄を探し、`document.execCommand('insertText', false, text)` で挿入している。clipboard なしではあるが、今回の設計では `Input.insertText` を第一候補、`execCommand` を fallback 候補にする。

概念コード:

```js
const editor =
  document.activeElement?.isContentEditable
    ? document.activeElement
    : document.querySelector(
        '.composer-bar [data-lexical-editor="true"], ' +
        '[id*="composer"] [contenteditable="true"], ' +
        '.aislash-editor-input'
      );

if (!editor) throw new Error("Cursor input not found");
editor.focus();
document.execCommand("insertText", false, promptText);
```

`execCommand` は古い API だが、Lexical / contenteditable に人間入力に近いイベントを通せる場合がある。安定性は Cursor の DOM 実装に依存する。

### 5.4 Selector 候補

既存実例からの候補:

```text
[data-lexical-editor="true"]
.aislash-editor-input
.composer-bar [data-lexical-editor="true"]
[id*="composer"] [contenteditable="true"]
.composite.auxiliarybar[data-composer-id]
.composer-bar[data-composer-id]
textarea
[role="textbox"]
```

実装では selector を1つに固定しない。複数 selector を試し、見つかった element の以下を確認する。

- visible
- editable / contenteditable
- disabled ではない
- workspace / active chat の context が期待通り

### 5.5 Send

送信候補:

1. DOM 上の send button を selector で click。
2. focused editor に `KeyboardEvent` / CDP key event で Enter / Cmd+Return。
3. CDP `Input.dispatchKeyEvent`。

Enter より Send button click を優先する。確認済み selector 候補:

```text
button.ui-prompt-input-submit-button[aria-label="Send message"]
.send-with-mode .anysphere-icon-button
button[aria-label="Send"]
.send-with-mode button
button[aria-label="Send message"]
```

概念コード:

```js
const sendButton =
  document.querySelector('button.ui-prompt-input-submit-button[aria-label="Send message"]') ||
  document.querySelector('[aria-label="Send message"]') ||
  document.querySelector('button[title*="Send"]') ||
  Array.from(document.querySelectorAll('button'))
    .find((b) => /send/i.test(b.textContent || b.getAttribute('aria-label') || ''));

if (!sendButton) throw new Error("Send button not found");
setTimeout(() => sendButton.click(), 0);
```

### 5.6 Response / running state

CDP では DOM から以下を取得できる可能性がある。

- active conversation text
- running / stop button state
- tool confirmation UI
- context meter
- screenshot
- diff / command block DOM

応答 DOM の selector 候補:

```text
[data-message-role]
.composer-human-ai-pair-container
[data-message-role="human"]
.aislash-editor-input-readonly
[data-message-role="ai"]
[data-message-kind="tool"]
.anysphere-markdown-container-root
.markdown-section
.markdown-block-code
.markdown-table-container
[data-stop-button="true"]
```

チャット切替や複数 workspace 対応では、PocketCursor 型の registry が参考になる。

- 各 Cursor target の workspace / title / WebSocket URL を保存する。
- active chat を永続化する。
- `data-composer-id` や `data-resource-name` を使って chat id を安定化する。
- DOM event listener を注入する場合は `Runtime.addBinding` / `Page.addScriptToEvaluateOnNewDocument` を使う。

ただし、Cursor UI の状態は最終 authority にしない。Codex は必ず以下で検収する。

2026-06-15 の実測では、research-only prompt を2本 submit し、次の provisional completion signal で完了を検出できた。

- submit selector: `button.ui-prompt-input-submit-button[aria-label="Send message"]`
- input selector: `.tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]`
- running signal: visible button text / aria-label に `Stop generation` が出る。
- completion signal: `Stop generation` が消え、`.composer-rendered-message` の assistant response 側に task id と final report が出る。
- false positive: prompt 本文にも `STATUS: done` や `FILES_CHANGED: none` が含まれるため、document 全体の text search だけで完了判定しない。
- thread switch: sidebar の `.glass-sidebar-agent-menu-btn` を title で click できる。title は重複し得るため、切替後は本文の task id で確認する。

追加の parallel-running smoke:

- 35〜65 秒の read-only delay を含む Cursor Agent thread を複数 submit し、active thread では CDP から `Stop generation` を実行中に取得できた。
- Cursor Agent は同一 project 内で複数 thread を走らせられる。実測では delay 付き thread がそれぞれ `Worked for 42s`、`43s`、`50s`、`56s` として完了した。
- ただし、複数 running thread の安定した並列監視は title だけでは不十分。Cursor が title を同じ `Parallel-running cursor agent smoke test` に畳む、または prompt 冒頭を sidebar item として表示する場合がある。
- 実装には thread registry が必要。作成直後に sidebar item index、visible title、expected task id、created order を保存し、切替後に本文 task id で検証する。
- `Stop generation` は active thread の running signal としては使えるが、inactive thread の running state を直接読むには thread 切替が必要。切替対象の識別が曖昧なままでは誤監視する。

実装反映:

- `run_cursor_delegate.sh --submit` は既定で `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl` に JSONL registry を追記する。
- `--registry-file FILE` で保存先を指定できる。
- `--no-registry` で記録を無効化できる。
- record には `task_id`、`prompt_sha256`、`prompt_file`、`workspace`、CDP target、submit 直後の `thread_snapshot`、`sidebar_before`、`sidebar_after` を入れる。
- registry は navigation aid であり、切替後は本文 task id で確認し、最終検収は result file / diff / tests で行う。

同一 mac 上では、research / review / summary タスクの回収は result file より DOM direct result の方が自然な場合がある。実装では `--monitor-registry --task-id ID --wait` が registered thread を開き、assistant bubble から `final_report` を直接返す。

使い分け:

- DOM direct result: ファイル成果物が不要な調査、レビュー、要約、観点洗い出し。
- result file: 編集タスク、長い structured output、UI DOM だけでは欠落・折り畳み・誤抽出が怖い成果物。
- diff/tests: 常に最終 authority。DOM result も result file も worker report であり、main Codex が検収する。

```bash
git status --short
git diff --name-only
git diff --stat
<verification command>
```

### 5.7 セキュリティ

remote debugging port は強い権限を持つ。必ず local-only にする。

- bind は `127.0.0.1` 前提。
- port は固定または明示設定。
- LAN へ公開しない。
- 起動済み Cursor の port を自動検出する場合、対象 process が本当に Cursor か確認する。
- CDP transport は no-clipboard prompt insertion の標準経路にする。ただし submit は send 経路が smoke 済みになるまで fail closed にする。
- この資料では macOS Cursor IDE 以外を対象外にする。必要なら別 skill として扱う。

---

## 6. 完了検知と result file contract

Cursor UI を読んで完了判定する設計は採用しない。代わりに、worker prompt に result file contract を入れる。

### 6.1 標準 result directory

委任 run ごとに一意の run id を作る。

```text
.agent_runs/cursor/<run-id>/
  prompt.txt
  result.json.tmp
  result.json
  result.md
  ui_advisory.jsonl
```

正は `result.json`。`result.md` は人間向け要約、`ui_advisory.jsonl` は wrapper / UI 観測ログにする。

`result.json` schema:

```json
{
  "schema_version": 1,
  "run_id": "20260615-123456-cursor-a",
  "worker": "cursor-agent",
  "transport": "mac-ide-applescript",
  "workspace": "/absolute/path",
  "status": "completed",
  "goal": "one concrete task",
  "allowed_write_scope": ["src/foo.ts", "tests/foo.test.ts"],
  "files_changed_claimed": ["src/foo.ts"],
  "verification": [
    {
      "command": "npm test -- foo",
      "exit_code": 0,
      "summary": "passed"
    }
  ],
  "approvals_requested": [
    {
      "kind": "terminal",
      "summary": "what Cursor asked for",
      "decision": "not_auto_approved"
    }
  ],
  "blocked_reason": null,
  "notes_for_main_codex": "rerun tests and inspect diff",
  "model": "Cursor IDE selected model; not programmatically verified",
  "finished_at": "2026-06-15T12:34:56+09:00"
}
```

`status` は `completed | blocked | failed` の terminal state にする。Cursor worker は完了時だけ `result.json.tmp` を書き、最後に `result.json` へ rename する。外側は partial write を読まない。

### 6.2 Prompt contract に入れる文言

```text
When finished, write a result file at:
<workspace>/.agent_runs/cursor/<run-id>/result.json

Write result.json.tmp first, then rename it to result.json only after the JSON is complete.

The result JSON must include:
- schema_version
- run_id
- status: completed | blocked | failed
- files_changed_claimed
- verification command and result
- approvals_requested
- blocked_reason when blocked or failed
- notes_for_main_codex

Do not commit.
Do not push.
Do not merge.
Do not edit files outside the allowed write scope.
```

### 6.3 Codex 側の回収

外側 wrapper / Codex は `result.json` の存在だけでは完了採用しない。まず次を確認する。

- `result.json` が存在する。
- mtime / size が短時間で安定している。
- JSON parse に成功する。
- `run_id` が一致する。
- `status` が terminal state。

その後、Codex は result file だけを信用せず diff を確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

確認すること:

- result file の changed files と実 diff が一致する。
- write scope 外の変更がない。
- 既存未コミット変更を戻していない。
- verification command が成功している、または失敗理由が具体的。
- AppleScript transport では model を programmatically verify できないと記録する。
- `result.json` が出ない場合は timeout / blocked 扱いにする。途中 diff があっても自動採用しない。

---

## 7. Approval / tool confirmation

approval UI は検知対象にはできるが、自動承認の対象にはしない。

参考:

- cursor-remote は AppleScript で `Allow` / `Approve` / `Accept` button を検出している。
- PocketCursor は command rules で allow / deny pattern を分け、deny を優先する設計を持つ。

今回の skill では、初期実装は次に留める。

- `Allow` / `Approve` / `Accept` / `Deny` / `Cancel` / `Reject` button の存在を検知する。
- 検知したら Codex がユーザーに報告する。
- `ui_advisory.jsonl` に観測イベントとして記録する。
- 自動 approve はしない。
- deny pattern に一致する command は、Cursor 側に続行させない。

自動承認を将来検討する場合でも、最初に許可できるのは read-only / safe command に限定する。

許可候補:

```text
git status
git diff
ls
pwd
cat <allowed read path>
```

拒否候補:

```text
rm
mv
git reset
git checkout --
git clean
git push
git commit
merge / rebase / branch switch
deploy / release / publish
workspace 外ファイルの read/write/delete
.env / secrets / private key / token / credentials
DB migration / production data operation
permission / allowlist / approval 設定の緩和
credential / token / private key へのアクセス
```

deny は allow より常に優先する。

Cursor 応答コピー、選択範囲コピー、pasteboard からの応答取得は監査不能なので、result contract の代替にしない。

---

## 8. 既存実装から拾うもの / 捨てるもの

### 8.1 Run Cursor Composer from Terminal / Gist

URL: https://gist.github.com/husniadil/b207227c31ff8a26e03bf00c3a53ebfd

拾う:

- 外部 process から Cursor Composer を起動する需要があること。
- AppleScript / Accessibility 権限が必要になること。

捨てる:

- `pbcopy`
- `Cmd+V`
- `Cmd+I -> paste -> Return` を標準経路にする設計

### 8.2 aerkn1/ai-orchestrator-pro

URL: https://github.com/aerkn1/ai-orchestrator-pro  
参考: `adapters/run_cursor.sh`

拾う:

- 複数 AI worker を orchestrator が束ねる構成。
- Cursor 用 prompt / workspace / rule を事前生成する設計。
- Cursor を実装 worker、別 agent を reviewer とする役割分担。

捨てる:

- prompt 投入の primary path としての clipboard/paste。

### 8.3 yasegev/cursor-remote

URL: https://github.com/yasegev/cursor-remote  
参考: `mac-agent/services/cursor_controller.py`

拾う:

- Cursor process 起動確認。
- Cursor activate。
- approval dialog 検知。
- `Allow` / `Approve` / `Accept`、`Deny` / `Cancel` / `Reject` の button 探索。
- `Stop` button による running heuristic。

捨てる:

- prompt 投入としての clipboard/paste。
- UI 応答 copy を完了判定にする設計。
- 自動 approve。

### 8.4 sms-2-cursor

URL: https://github.com/jacksonbaxter/sms-2-cursor

拾う:

- 応答取得を UI から読むのではなく、ファイル出力へ逃がす設計。
- File watcher で result file を回収する考え方。

捨てる:

- pyautogui / keyboard typing / paste を主経路にする設計。

### 8.5 OpenCLI

URL: https://github.com/jackwener/OpenCLI  
参考: `docs/adapters/desktop/cursor.md`, `clis/cursor/composer.js`

拾う:

- Cursor を CDP endpoint で操作する設計。
- `/json` / WebSocket target 経由で Cursor UI に接続する発想。
- DOM 上の input selector を複数試す設計。
- `document.execCommand('insertText', false, text)` で clipboard を使わず text を入れる実装。

注意:

- `Meta+I` で Composer を開く部分は current UI に依存する。
- Agent window を直接対象にするなら selector / target selection は追加調査が必要。

### 8.6 PocketCursor

URL: https://github.com/qmHecker/pocket-cursor

拾う:

- Cursor を CDP port 付きで起動する運用。
- 複数 Cursor workspace / chat を target として扱う registry。
- Lexical editor への CDP text insertion。
- DOM monitor で AI response / confirmation / context state を見る設計。
- command rules の allow / deny pattern。

注意:

- Windows focus fallback は今回対象外。
- Telegram 連携部分は不要。
- command auto-approve は初期実装に入れない。

### 8.7 model-matchmaker

URL: https://github.com/coyvalyss1/model-matchmaker

拾う:

- 実行元 process によって Accessibility 権限が変わるという知見。
- Cursor 子 process / hook から直接 UI automation すると権限で詰まる場合があること。
- Terminal.app proxy は参考にはなる。

注意:

- モデル切替の keyboard automation は今回の prompt transport の主経路ではない。

---

## 9. 実装ロードマップ

### Phase 1: mac-ide-cdp を標準 prompt 投入経路にする

実装済み / 優先:

- CDP endpoint で `Cursor Agents` target を検出する。
- `New Agent` button を DOM click できる。
- `.tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]` を focus する。
- CDP `Input.insertText` で clipboard なしに prompt を入れる。
- DOM text read-back で prompt 一致を確認する。
- no-submit smoke を持つ。
- submit は明示 opt-in にし、send 経路が未検証なら fail closed にする。
- `Ask` chip がある edit 委任は preflight warning / failure にする。
- Cmd+V fallback は標準経路から外す。

追加候補:

- `--require-agent-window`: `Cursor Agents` target がなければ failure。
- `--legacy-paste-fallback`: 明示指定時だけ paste fallback。
- `--assert-workspace NAME`: Agent sidebar / workspace selector が期待値を含むか確認。
- `--assert-no-ask`: DOM 上に Ask chip が見える場合は failure。
- `--submit`: send button selector / shortcut を smoke 済みの場合だけ有効化。

### Phase 1b: mac-ide-applescript を補助経路として整理

実装済み / 優先:

- Cursor / `Cursor Agents` window の activate / focus。
- System Events の Accessibility 権限確認。
- AppleScript 単独 prompt 投入は標準経路にしない。

追加候補:

- `--focus-only` を明示した wrapper。
- Agent window / modal / approval dialog の advisory 検出。
- 補助クリックを実装する場合は個別 smoke test を必須にする。

### Phase 2: result file contract

実装候補:

- `run_cursor_delegate.sh` が run id と `.agent_runs/cursor/<run-id>/` を作る。
- `prompt.txt` を保存する。
- prompt template に `result.json` path を差し込む。
- Cursor worker には `result.json.tmp -> result.json` rename を指示する。
- 終了後、Codex が `result.json` と git diff を照合する。

### Phase 3: approval advisory

実装候補:

- AppleScript または Computer Use で approval button の有無を検知。
- 検知したらユーザーに報告。
- 自動 approve はしない。

### Phase 4: mac-ide-cdp submit / monitoring

実装候補:

```bash
scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --cdp-endpoint http://127.0.0.1:9226 \
  --workspace /Users/ryryo/dev/dot-claude-dev \
  --prompt-file /tmp/prompt.md
```

責務:

1. CDP endpoint の疎通確認。
2. target list 取得。
3. target workspace selection。
4. input selector 探索。
5. text insertion without clipboard。
6. send button click。
7. optional DOM/screenshot artifact dump。
8. result file + diff/test は main Codex が検収。

---

## 10. サブエージェント追加調査タスク

今回の subagent 調査で、次の実装メモを取り込んだ。残る作業は実測 smoke と script 化。

### Task A: CDP target / selector 調査

Goal:

- Cursor Agents window に対する CDP target selection と input selector を実測する。

調査で得た実装メモ:

- `/json/version` で browser-level WebSocket、`/json` で page target を取る。
- `type == "page"`、`devtools://` 除外、title/workspace 推定。
- `Page.bringToFront`、`Target.activateTarget`、macOS `osascript activate` は前面化補助。
- 入力は `Runtime.evaluate` で focus し、CDP `Input.insertText` を主経路にする。
- `execCommand('insertText')` は clipboard なし fallback。
- send は Enter より DOM button click を優先する。

実測済み:

- 通常ログイン済み Cursor profile を remote debugging port 付きで再起動すると CDP target が見える。
- 別 `--user-data-dir` profile で起動するとログイン状態が引き継がれない。
- `Cursor Agents` target は title `Cursor Agents`、URL `vscode-file://.../workbench.html` として見える。
- `New Agent` button は DOM click できる。
- 入力欄 selector は `.tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]`。
- CDP `Input.insertText` で clipboard を使わず no-submit smoke が通る。
- submit なしで入力欄の DOM text / HTML read-back ができる。

残る実測:

- `Cursor Agents` window と通常 composer panel の selector 差分を確認する。
- send button selector / shortcut を submit なしの範囲で安全に特定する。

### Task B: AX preflight 調査

Goal:

- AppleScript / Accessibility tree で `Cursor Agents` window の workspace、Ask chip、Send button をどこまで安定検出できるか調べる。

調査で得た実装メモ:

- `AXTextArea` direct set は現行 build では未成立。
- AppleScript は window focus / helper operation に寄せる。
- 複数 window は fail closed。
- `Ask` chip / workspace / model / approval は自動修正より preflight に寄せる。
- parent/sibling toolbar traversal は壊れやすい。

実測済み:

- `Cursor Agents` window の focus は可能。
- `AXTextArea` direct set による prompt insertion は失敗し、CDP では同じ editor が contenteditable として見える。

残る実測:

- `Ask` chip がある edit 委任を warning / failure にできる。
- approval / modal の advisory 検出ができるか確認する。

### Task C: result file / approval contract

Goal:

- Cursor worker prompt に入れる result file schema と approval handling を固める。

調査で得た実装メモ:

- 正は `result.json`。
- `result.json.tmp -> result.json` rename で partial write を避ける。
- `ui_advisory.jsonl` は補助ログ。
- UI completion / Stop button / response text は完了判定の正にしない。
- Codex は必ず diff と verification command で検収する。

残る実測:

- UI response を読まなくても Codex が完了回収できる。
- write scope 外変更を検出できる。
- `result.json` timeout / blocked の扱いを wrapper に実装する。

---

## 11. 更新後の推奨順

短期:

1. `mac-ide-cdp` = Cursor Agents target + Tiptap contenteditable + `Input.insertText`。
2. `mac-ide-applescript` = Agent window focus / helper operation。
3. result file contract。
4. Codex 側の diff/test 検収。

中期:

1. send button / shortcut の submit smoke。
2. approval advisory。
3. workspace / mode assertion。
4. legacy paste fallback の opt-in 化または削除。

長期:

1. `mac-ide-cdp` submit / monitoring。
2. DOM selector 複数化。
3. screenshot / DOM dump artifact。
4. response DOM reading は補助情報に限定。

---

## 12. 参考リンク

### CDP / DOM

- OpenCLI: https://github.com/jackwener/OpenCLI
- OpenCLI Cursor adapter doc: https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/desktop/cursor.md
- OpenCLI `composer.js`: https://github.com/jackwener/OpenCLI/blob/main/clis/cursor/composer.js
- PocketCursor: https://github.com/qmHecker/pocket-cursor
- Chrome DevTools Protocol Input domain: https://chromedevtools.github.io/devtools-protocol/tot/Input/

### AppleScript / Accessibility

- cursor-remote: https://github.com/yasegev/cursor-remote
- cursor-remote `cursor_controller.py`: https://github.com/yasegev/cursor-remote/blob/main/mac-agent/services/cursor_controller.py
- ai-orchestrator-pro: https://github.com/aerkn1/ai-orchestrator-pro
- Run Cursor Composer from Terminal Gist: https://gist.github.com/husniadil/b207227c31ff8a26e03bf00c3a53ebfd

### Completion / remote bridge

- sms-2-cursor: https://github.com/jacksonbaxter/sms-2-cursor
- model-matchmaker: https://github.com/coyvalyss1/model-matchmaker

---

## 13. まとめ

公開実装を見ると、Cursor IDE を外部から叩く実例はある。ただし多くは `Cmd+V` / clipboard に依存している。

今回の skill では、そこを主経路にしない。

採用する実装方針は次の通り。

- macOS default は CDP による `Cursor Agents` target 操作と contenteditable prompt insertion。
- AppleScript は Agent window focus / helper operation に使う。
- `Cmd+V` fallback は標準から外す。
- edit 委任では `Ask` mode を preflight で弾く。
- 完了判定は UI ではなく result file + git diff + verification command。
- 複数 thread / worktree 管理も CDP transport に寄せる。

Codex は orchestrator / reviewer のまま、Cursor IDE は bounded worker として扱う。Cursor に commit、push、merge、完了判定は任せない。
