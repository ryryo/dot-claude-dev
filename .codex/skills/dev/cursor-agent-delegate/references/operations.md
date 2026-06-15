# 通常運用

この reference は、Cursor Agent へ通常の委任を行うときの入口である。

## 前提条件

- macOS の Cursor IDE だけを対象にする。
- Cursor は loopback CDP port 付きで起動している必要がある。
- 通常の Cursor profile を使う。一時的な `--user-data-dir` は使わない。
- 通常運用では `--no-lock` と `--no-process-guard` を使わない。
- 1 つの prompt では 1 つの範囲限定タスクだけを委任する。
- 差分確認、test、commit、push、PR、最終受け入れは main Codex が行う。

## CDP 付きで Cursor を起動する

CDP がまだ listen していない場合は、通常 profile のまま起動する。

```bash
open -na /Applications/Cursor.app --args \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226 \
  "$WORKSPACE"
```

確認する。

```bash
curl http://127.0.0.1:9226/json/version
curl http://127.0.0.1:9226/json
```

`Cursor Agents` という page target が必要である。`page target` は CDP の返す対象種別なので英語表記のまま扱う。

## Cursor Agent に 1 タスクを投入する

prompt file には次を含める。

- `Workspace`
- `Task ID`
- 具体的な `Goal` 1 件
- 編集してよい範囲
- 禁止パスと禁止行為
- 検証コマンド、または read-only であることの明示
- 最終報告形式

実行する。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --new-agent \
  --submit
```

既定の出力先は次の 2 つ。

- `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl`
- `$WORKSPACE/.agent_runs/cursor/process-audit.jsonl`

テスト実行では、明示的に `.tmp/...` 配下の registry file と process report file を指定してよい。

## 1 タスクを監視する

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-registry \
  --task-id "$TASK_ID" \
  --wait
```

DOM result は、`matched: true`、`running: false`、final report 内の task id が確認できた場合だけ回収結果として扱う。

## 複数タスクを監視する

今回のセッションで作成した registry record だけを対象にする。`registry record` は JSONL に保存される記録単位なので英語表記のまま扱う。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-all \
  --wait \
  --max-records 4 \
  --max-candidates 2
```

`--monitor-all` は現在のセッション用の一覧確認である。古い thread を長期的に復元する仕組みとしては使わない。

## Guard ログを確認する

```bash
tail -n 20 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl"
tail -n 20 "$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl"
```

process audit で見る field:

- `budget_exceeded`
- `exit_code`
- `max_processes`
- `max_descendant_processes`
- `command`
- `samples`

monitor で見る field:

- `matched`
- `done`
- `running`
- `final_report`
- `guard.cdp_calls`
- `guard.clicks`

## Cursor 完了後に確認する

main Codex は必ず実行する。

```bash
git status --short
git diff --name-only
git diff --stat
```

編集タスクでは、許可したファイルの中身も確認し、検証コマンドを再実行する。Cursor の final report は参考情報であり、完了判定そのものではない。
