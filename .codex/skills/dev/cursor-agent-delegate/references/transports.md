# 操作経路

この skill は macOS の Cursor IDE 操作だけを対象にする。

標準の操作経路:

- `mac-ide-cdp`: clipboard を使わずに prompt を投入し、同じ repository workspace 内の複数 Cursor Agent thread を扱う標準経路。
- `mac-ide-applescript`: Cursor Agents の前面化や小さな UI 補助操作に使う補助経路。
- `deeplink`: ユーザーが Cursor 上で prompt を確認してから実行したい場合の手動 fallback。

macOS 以外の Cursor IDE 運用は対象外である。
この skill では Git worktree を作成・切替・管理しない。並列編集は、worker ごとの編集対象ファイルが重ならない場合だけ行う。

## mac-ide-applescript

macOS のみで使える。これは UI automation であり、安定した Cursor API ではない。

現在の役割:

- Cursor / `Cursor Agents` を前面に出す。
- Agents window が存在することを確認する。
- 個別に smoke test 済みの小さな UI 補助操作を行う。
- clipboard なしの標準 prompt 投入経路としては使わない。

Preflight:

- `/Applications/Cursor.app` が存在する。
- `osascript` が存在する。
- 対象 workspace の Agents window が開いている、またはユーザーが既存の Cursor workspace window から開ける。
- macOS Accessibility 権限により、System Events が Cursor を調査・操作できる。
- 編集委任では、Agent input が `Ask` mode ではなく編集可能な mode である。

検証済みの挙動:

- Cursor を前面化する。
- `Cursor Agents` window を優先する。
- `Cursor Agents` window に focus する。
- UI 状態だけで完了判定しない。

標準経路として採用しない、または未検証の操作:

- `AXTextArea` direct set による prompt 投入: Cursor 3.7.36 では成立しなかった。Agent prompt editor は CDP から Tiptap/ProseMirror の `contenteditable` element として見えるが、安定した writable `AXTextArea` としては扱えない。
- keyboard/clipboard による prompt 投入: AppleScript の例としては多いが、この project では `Cmd+V` / pasteboard 変更を避けるため標準採用しない。
- `System Events keystroke` による長文入力: 遅く、focus に依存するため標準採用しない。

対象外:

- 標準経路で `pbcopy`、pasteboard、`Cmd+V` を使わない。
- model や mode をプログラムから切り替えない。
- `Ask` chip を自動削除しない。
- tool permission を自動承認しない。

Cursor 完了後は、main Codex が result file、`git status`、`git diff`、検証コマンドで確認する。

## mac-ide-cdp

macOS で、clipboard を使わずに prompt を投入し、1 つの repository workspace 内で複数 thread を扱う transport。Cursor 3.7.36 では、下記の Agent Window selector で submit を検証済み。

目的:

- Chrome DevTools Protocol で Cursor の Electron/Chromium UI に接続する。
- Cursor page target と Agent thread を識別する。`page target` は CDP の対象種別、`thread` は Cursor Agents の会話単位を指す。
- CDP `Input.insertText` で clipboard を使わずに text を挿入する。
- DOM の send button を click する。
- target id、title、workspace hint、active chat/thread hint、running/approval の参考状態を記録する。これらは CDP と Cursor UI の識別情報なので英語表記のまま扱う。

Preflight:

```bash
curl http://127.0.0.1:9226/json/version
curl http://127.0.0.1:9226/json
```

Cursor は remote debugging port 付きで起動しておく。例:

```bash
/Applications/Cursor.app/Contents/MacOS/Cursor \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226
```

Cursor がすでに CDP なしで起動している場合、その既存 process に後から CDP を付けられるとは考えない。明示的な test launch または restart flow を使う。

実装の流れ:

1. `/json/version` から browser-level WebSocket URL を読む。
2. `/json` から page target を読む。
3. `type == "page"` を選び、devtools target を除外する。
4. project/workspace title と URL hint から対象 target を選ぶ。
5. `Page.bringToFront` または `Target.activateTarget` で foreground hint を送る。
6. `Runtime.evaluate` で Lexical/contenteditable input を探して focus する。
7. `Input.insertText` で prompt を挿入する。
8. DOM text を読み返す。
9. submit が明示された場合だけ send button を click する。
10. result file がない調査専用タスクでは、DOM 上の完了表示を仮の完了 signal とし、最後に `git status --short` で変更がないことを確認する。

Input selector 候補:

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

Send button selector 候補:

```text
button.ui-prompt-input-submit-button[aria-label="Send message"]
.send-with-mode .anysphere-icon-button
button[aria-label="Send"]
.send-with-mode button
button[aria-label="Send message"]
```

Cursor 3.7.36 で検証済みの Agent Window selector:

```text
input: .tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]
submit: button.ui-prompt-input-submit-button[aria-label="Send message"]
thread item: .glass-sidebar-agent-menu-btn
project selector: button.project-selector__trigger
```

完了 signal:

- submit した prompt 内の final report template を完了とみなさない。
- `Stop generation` / cancel control が消えたことは running state の参考 signal として扱う。
- `.composer-rendered-message` などの visible assistant response bubble に task id と final report が含まれていれば、仮の完了 signal として扱う。
- 最終受け入れは result file、`git status`、`git diff`、検証コマンドに基づいて main Codex が判断する。

複数 thread 監視の注意:

- active thread の running state は、生成中であれば CDP から読める。
- sidebar title は安定した thread id ではない。Cursor が重複 title を生成したり、prompt 冒頭を表示したりすることがある。
- thread 作成時に registry を記録する。記録対象は sidebar index/order、visible title、expected task id、workspace、prompt file。
- thread を切り替えた後は、本文に expected task id が含まれることを確認してから running/done signal を信頼する。

Registry の扱い:

- `run_cursor_delegate.sh --submit` は既定で `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl` に JSONL を追記する。
- `--registry-file FILE` で出力先を変えられる。
- `--no-registry` で記録しない。
- 各 record には `task_id`、`prompt_sha256`、`prompt_file`、`workspace`、CDP page target metadata、`thread_snapshot`、`sidebar_before`、`sidebar_after` が含まれる。
- registry は移動用の手がかりである。正しさは本文の task id、diff、test で判断する。

Monitor の扱い:

- `run_cursor_delegate.sh --monitor-registry --task-id ID` は登録済み thread 候補を開き、本文に `ID` があることを確認し、`running`、`done`、`final_report`、title text、running hint、registry metadata を含む JSON を出力する。
- `run_cursor_delegate.sh --monitor-all` は registry を task id ごとにまとめ、各登録済み thread 候補を開き、本文の task id を確認し、集計 count と thread ごとの DOM result を出力する。
- `--wait` を付けると、assistant final report が見えるか timeout するまで poll する。
- candidate 切替は登録済み thread ごとに `--max-candidates`、`--monitor-all` の読み取り数は `--max-records` で制限する。古い record は、sidebar を無制限に探索せず `unmatched` として扱う。
- CDP 操作は既定で workspace-level lock により保護する。同じ workspace で 2 つ目の wrapper invocation が走った場合は、別の CDP control loop を開かず失敗させる。`--no-lock` は明示的な手動 debug 以外で使わない。
- Python CDP helper は `--max-cdp-calls`、`--max-clicks`、`--max-runtime` で操作 budget を強制する。超過は警告ではなく重大な失敗として扱う。
- wrapper は既定で `scripts/process_guard.py` 経由で CDP helper command を起動する。process guard は `$WORKSPACE/.agent_runs/cursor/process-audit.jsonl` に JSONL audit record を書く。record には `root_pid`、`max_processes`、`max_descendant_processes`、sampled counts、command、exit code が含まれる。`--max-child-processes` を超えた場合は helper process group を停止して non-zero exit する。
- repository artifact が不要な調査・レビュータスクでは、direct DOM result を回収経路として使ってよい。
- 編集タスクでは result file が構造化された作業契約として役に立つ。ただし、同じ machine 上で実行しているため、すべてのタスクに result file を必須とはしない。

Security:

- loopback のみに bind する。
- CDP port を LAN に公開しない。
- CDP は強力な local control port として扱う。
- smoke test が安定するまで、この transport は明示的に使う。

## deeplink

ユーザーが Cursor 上で prompt を確認してから実行したい場合だけ使う。

生成する URL:

```text
cursor://anysphere.cursor-deeplink/prompt?text=<urlencoded prompt>
```

Deeplink は prompt を prefill するだけで、自動実行はしない。
