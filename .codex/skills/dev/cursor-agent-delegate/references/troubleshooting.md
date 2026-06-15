# 障害対応

Cursor 委任が重い、詰まる、または想定外の状態を返す場合に読む。

## 最初の対応

新しい Cursor/CDP 実行を増やさない。範囲を絞った local command で状態を集める。

```bash
git status --short
lsof -nP -iTCP:9226 -sTCP:LISTEN 2>/dev/null || true
tail -n 20 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl" 2>/dev/null || true
tail -n 20 "$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl" 2>/dev/null || true
```

広い process scan を繰り返さない。必要な場合も 1 回だけ実行し、結果を要約する。

## CDP に接続できない

症状:

- `Connection refused`
- `/json/version` が失敗する

主な原因:

- Cursor が `--remote-debugging-port` なしで起動している。
- 前回の launch が既存の non-CDP Cursor process に吸収された。

対応:

1. Cursor を通常終了する。
2. 通常 profile のまま CDP args 付きで起動する。

```bash
open -na /Applications/Cursor.app --args \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226 \
  "$WORKSPACE"
```

3. `/json/version` を確認する。

一時的な `--user-data-dir` は使わない。別 profile になり、Cursor が未ログイン状態になることがある。

## Cursor Agents target が見つからない

症状:

- CDP は動いているが、title が `Cursor Agents` の target がない。

対応:

- 手動、または AppleScript focus helper で Cursor Agents window を前面に出す。
- `/json` を再確認する。
- `Cursor Agents` target が出るまで prompt を submit しない。

## Workspace lock の失敗

症状:

- `another Cursor CDP operation is already running`

対応:

1. 別の実行が本当に動いている場合は少し待つ。
2. lock pid を確認する。

```bash
cat "$WORKSPACE/.agent_runs/cursor/locks/cdp.lock/pid"
```

3. pid が dead である場合だけ、その lock directory を削除する。

```bash
rm -rf "$WORKSPACE/.agent_runs/cursor/locks/cdp.lock"
```

`--no-lock` は明示的な手動 debug 以外で使わない。

## Process budget 超過

症状:

- process guard が exit code `99` で終了する。
- process audit に `budget_exceeded: true` がある。

確認する。

```bash
tail -n 1 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl"
```

見る field:

- `max_processes`
- `max_descendant_processes`
- `max_sample`
- `command`

対応:

- すぐに上限を上げない。
- 委任 task が Cursor に shell command 実行や subprocess 作成を依頼していないか確認する。
- 通常の CDP prompt/monitor 操作なら、期待される `max_processes` は多くの場合 `1` である。

## CDP 操作 budget 超過

症状:

- `operation guard stopped ... CDP call budget exceeded`
- `operation guard stopped ... click budget exceeded`
- `operation guard stopped ... runtime budget exceeded`

対応:

- 重大な失敗として扱う。
- 最新の monitor JSON と process audit を確認する。
- `--task-id`、`--max-records`、`--max-candidates` で registry scope を狭める。
- 古い registry に対して `--monitor-all` を使わない。

## Monitor が unmatched を返す

主な原因:

- registry が古い。
- Cursor が重複 title を生成した、または title が変わった。
- sidebar virtualization により index が変わった。
- 対象 thread が現在の Cursor Agents project 内に見えていない。

対応:

- 実行中の作業には `--monitor-registry --task-id` を優先する。
- 複数 task の確認には、今回のセッションで作成した registry record だけを使う。
- 手動 debug でない限り、`--max-candidates` を大きくしない。

## Ask mode または read-only 完了

症状:

- Cursor が回答するが、ファイルを編集しない。
- final report は完了を主張しているが、期待した差分がない。

対応:

- Cursor report を完了判定として扱わない。
- `git status --short`、`git diff --name-only`、期待 file path を確認する。
- 編集 task を委任する前に、Agent input が編集可能 mode であることを確認する。

## 範囲外変更

症状:

- 許可した編集範囲外のファイルが変更されている。

対応:

1. diff を確認する。
2. 範囲外変更が worker によるものだと明確で安全な場合だけ、main Codex が修正してよい。
3. ユーザーまたは別 agent の作業である可能性がある場合は、変更前に確認する。
4. 広範囲に破壊的な command は使わない。

## 重い、または応答が悪い

すぐに行うこと:

- 新しい Cursor/CDP command を起動しない。
- `pgrep` / `ps` の loop を繰り返さない。
- 最新の process audit を 1 回だけ確認する。
- `budget_exceeded` または stale lock がないか確認する。
- CDP の状態が混乱している場合は、通常 profile のまま Cursor を通常 restart する。
