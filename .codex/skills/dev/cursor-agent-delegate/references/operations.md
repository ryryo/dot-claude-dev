# Cursor CLI の実行

同梱 CLI は `cursor agent --print --yolo --trust --model composer-2.5-fast` を background 実行し、既定で `.agent_runs/cursor-delegate/` に registry と task report を保存する。

```bash
WORKSPACE="$(pwd)"
RUNNER="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate/scripts/cursor_cli_delegate.py"
PROMPT_FILE="$WORKSPACE/.agent_runs/cursor-delegate/prompts/<plan-id>-<task-id>.md"
```

planのtask contractから[delegation-prompt-template.md](delegation-prompt-template.md)に沿って`PROMPT_FILE`を作る。workerにplan自体を更新させない。

## Submit

```bash
"$RUNNER" \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --submit
```

write scope が重ならない task だけを連続 submit できる。各 submit の成功を確認してからまとめて monitor する。

## Monitor

```bash
# 1 task
"$RUNNER" --workspace "$WORKSPACE" \
  --monitor-registry --task-id T20 --wait --timeout 180

# registry 内の最新 task
"$RUNNER" --workspace "$WORKSPACE" \
  --monitor-all --wait --max-records 4 --timeout 180
```

`thread.done: true` の task だけを正常終了として扱う。`thread.failed: true` なら `stderr_tail` と result JSON を確認し、main Codex が修正・再投入・棄却を判断する。worker の報告を根拠に完了判定せず、[review-checklist.md](review-checklist.md) で diff と検証を確認する。

`--registry-file` で保存先を変更できる。その他の引数は `"$RUNNER" --help` で確認する。

## 例外: CLI 疎通失敗

preflight は通常フローや投入前 checklist に入れない。submit / monitor が次の CLI-level error で失敗した場合だけ、追加投入を止めて実行する。

- `cursor` command または `cursor agent` を起動できない。
- login、status、model list、`composer-2.5-fast` の error。
- worker prompt より前の段階で JSON result を生成できない。
- 複数 task が同種の CLI-level error で失敗する。

```bash
"$RUNNER" --workspace "$WORKSPACE" --preflight
```

成功したら元の task error を見直し、必要な task だけ再投入する。失敗したら復旧を繰り返さず、main Codex または Codex subagent へ割り当て直す。login が必要な場合や固定 model が利用できない場合はユーザーへ報告する。
