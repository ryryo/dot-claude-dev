# 通常運用

Cursor Agent への通常の委任手順を説明する。

## 前提条件

- macOS の Cursor IDE だけを対象にする。
- Cursor は loopback CDP port 付きで起動している必要がある。
- 通常の Cursor profile を使う。一時的な `--user-data-dir` は使わない。
- `--no-lock` と `--no-process-guard` は通常運用では使わない。
- 1 つの prompt には 1 つの範囲限定タスクだけを書く。
- 差分確認・テスト・commit・push・PR・最終的な受け入れは main Codex が行う。

## Cursor Agents をセットアップ / 復旧する

Cursor Agent を使う Gate の前に、必ず setup script を実行する。これは CDP port、`Cursor Agents` target、project/model、read-only smoke task の submit / monitor まで確認する標準入口である。

Cursor Agent の標準モデル family は Composer 2.5 とする。Cursor 公式ブログ / model docs では、Composer 2.5 は standard と同等知能の fast variant を持ち、fast が既定とされている。スキルでも tier は `--model-tier fast|standard` で明示する。

| tier | model id | 使う場面 |
| --- | --- | --- |
| `fast` | `composer-2.5-fast` | main Codex が待っている対話的な委任、小さな実装、smoke test |
| `standard` | `composer-2.5` | 非同期で待てる調査・局所実装、複数 worker のコストを抑えたい作業 |

`CURSOR_AGENT_MODEL_TIER` または `--model-tier` で tier を選ぶ。`CURSOR_AGENT_MODEL` または `--expected-model` は直接 model id を固定する必要がある場合だけ使う。現在 UI に表示されている model 名や、問題報告用 screenshot に写っている model 名を期待値として採用しない。model id は実行時に `cursor-agent --list-models` でも確認できる。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/setup_cursor_agents.sh \
  --workspace "$WORKSPACE" \
  --model-tier fast
```

既存の Cursor が CDP なしで起動している場合、後から port は付けられない。setup script はその状態では失敗するため、ユーザーに確認してから次を実行する。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/setup_cursor_agents.sh \
  --workspace "$WORKSPACE" \
  --model-tier fast \
  --restart-cursor-approved
```

setup script は一時 profile を使わない。`Cursor Agents` target がない場合は Cursor UI の `ファイル > New Agents Window` を開き直し、target が出るまで待つ。project/model が期待と違えば submit 前に失敗する。

## Cursor Agent に 1 タスクを投入する

prompt file には以下を含める。

- `Workspace`
- `Task ID`
- 具体的な `Goal` 1 件
- 編集してよい範囲
- 禁止パスと禁止行為
- 検証コマンド（read-only タスクの場合はその旨を明記）
- 最終報告の形式

実行する。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --expected-project "$(basename "$WORKSPACE")" \
  --model-tier fast \
  --new-agent \
  --submit
```

既定の出力先:

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

`matched: true`・`running: false`・final report 内の task id が確認できた場合だけ、DOM result を回収結果として扱う。

prompt は英語表記の `Task ID:` を推奨する。日本語表記の `タスク ID:` も抽出対象だが、registry / monitor の安定性のため worker prompt template では `Task ID:` を使う。final report には `TASK_ID: <id>` または同じ task id を含める。

## 複数タスクを監視する

今回のセッションで作成した registry record だけを対象にする。

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-all \
  --wait \
  --max-records 4 \
  --max-candidates 2
```

`--monitor-all` は現在のセッション用の一覧確認として使う。古い thread を長期的に復元する仕組みとしては使わない。

## Guard ログを確認する

```bash
tail -n 20 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl"
tail -n 20 "$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl"
```

process audit で確認するフィールド:

- `budget_exceeded`
- `exit_code`
- `max_processes`
- `max_descendant_processes`
- `command`
- `samples`

monitor で確認するフィールド:

- `matched`
- `done`
- `running`
- `final_report`
- `guard.cdp_calls`
- `guard.clicks`

## Cursor 完了後に確認する

main Codex は必ず以下を実行する。

```bash
git status --short
git diff --name-only
git diff --stat
```

編集タスクでは、許可したファイルの内容も確認し、検証コマンドを再実行する。Cursor の final report は参考情報であり、完了判定そのものではない。
