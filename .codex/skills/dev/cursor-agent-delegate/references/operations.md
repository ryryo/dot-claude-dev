# Cursor CLI worker の運用

この skill に同梱した runner から headless Cursor CLI worker を直接実行する。Cursor IDE や別 skill は使わない。

## 前提

- Cursor CLI は通常利用できる前提で扱う。
- model は `composer-2.5-fast` に固定する。
- worker は `--print --yolo --trust` で実行する。
- 1 prompt には 1 つの範囲限定タスクだけを書く。
- preflight を通常の作業手順や投入前 checklist に入れない。
- diff、再検証、受け入れ、commit、push、PR は main Codex が行う。

## 1 タスクを投入する

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
PROMPT_FILE="/absolute/path/to/prompt.md"

"$SKILL_DIR/scripts/run_cursor_delegate.sh" \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --submit
```

runner は次の command を background で実行する。

```bash
cursor agent --print --yolo --trust \
  --workspace "$WORKSPACE" \
  --model composer-2.5-fast \
  --output-format json \
  "$PROMPT_TEXT"
```

既定の registry は `$WORKSPACE/.agent_runs/cursor-delegate/thread-registry.jsonl`。stdout、stderr、exit code、終了時刻は同じ directory の `reports/` に task id 単位で保存する。

呼び出し側で作業状態を別 directory に閉じたい場合は `--registry-file` を指定する。

## 1 タスクを監視する

```bash
"$SKILL_DIR/scripts/run_cursor_delegate.sh" \
  --workspace "$WORKSPACE" \
  --monitor-registry \
  --task-id "T20a" \
  --wait \
  --timeout 180
```

`thread.done: true` の場合だけ正常終了した Cursor CLI result として扱う。`thread.failed: true` の場合は `stderr_tail` と result JSON を確認する。

## 複数タスクを監視する

同じ registry に連続 submit した task をまとめて監視する。

```bash
"$SKILL_DIR/scripts/run_cursor_delegate.sh" \
  --workspace "$WORKSPACE" \
  --monitor-all \
  --wait \
  --max-records 4 \
  --timeout 180
```

同時 submit してよいのは write scope が重ならない task だけ。各 task の submit 成功を確認してから、まとめて monitor する。

## 回収後

main Codex が次を確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

worker が報告した検証を main Codex でも再実行する。final report と実際の diff が食い違う場合は diff を正とする。
