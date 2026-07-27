# Cursor CLIの実行

同梱のCLIは`cursor agent --print --yolo --trust --model composer-2.5-fast`をbackgroundで実行し、既定では`.agent_runs/cursor-delegate/`にregistryとtask reportを保存する。

```bash
WORKSPACE="$(pwd)"
RUNNER="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate/scripts/cursor_cli_delegate.py"
PROMPT_FILE="$WORKSPACE/.agent_runs/cursor-delegate/prompts/<plan-id>-<task-id>.md"
```

planのtask contractをもとに、[delegation-prompt-template.md](delegation-prompt-template.md)に沿って`PROMPT_FILE`を作る。plan自体の更新はworkerに行わせない。

## Submit

```bash
"$RUNNER" \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --submit
```

write scopeが重ならないtask同士は連続してsubmitできる。各submitの成功を確認してから、まとめてmonitorする。

## Monitor

```bash
# 1 task
"$RUNNER" --workspace "$WORKSPACE" \
  --monitor-registry --task-id T20 --wait --timeout 180

# registry 内の最新 task
"$RUNNER" --workspace "$WORKSPACE" \
  --monitor-all --wait --max-records 4 --timeout 180
```

正常終了として扱うのは`thread.done: true`のtaskだけである。`thread.failed: true`の場合は`stderr_tail`とresult JSONを確認し、main Codexが修正・再投入・棄却を判断する。workerの報告を完了判定の根拠にせず、[review-checklist.md](review-checklist.md)でdiffと検証結果を確認する。

保存先は`--registry-file`で変更できる。その他の引数は`"$RUNNER" --help`で確認する。

## 例外: CLI疎通失敗

preflightは通常フローや投入前checklistには含めない。submit / monitorが次のCLI-level errorで失敗した場合だけ、追加投入を止めてpreflightを実行する。

- `cursor` commandまたは`cursor agent`を起動できない。
- login、status、model list、`composer-2.5-fast`でerrorが出る。
- worker promptより前の段階でJSON resultを生成できない。
- 複数taskが同種のCLI-level errorで失敗する。

```bash
"$RUNNER" --workspace "$WORKSPACE" --preflight
```

preflightが成功したら元のtask errorを見直し、必要なtaskだけ再投入する。失敗した場合は復旧を繰り返さず、実装taskをmain Codexへ戻す。Codex subagentを実装fallbackにしない。loginが必要な場合や固定modelが利用できない場合は、ユーザーへ報告する。
