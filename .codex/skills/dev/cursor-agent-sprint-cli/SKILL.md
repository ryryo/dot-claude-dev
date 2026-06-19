---
name: cursor-agent-sprint-cli
description: |
  Cursor CLI headless worker を使い、ユーザーの実装指示を短いローカル実行計画に分解し、安全に分離できる小タスクだけを `cursor agent --print --yolo --trust --model composer-2.5-fast` に並列委任する。`.codex/tmp/YYMMDD_slug/` 配下で状態を管理し、docs/PLAN を作らず main Codex が統合と検収を行う。cursor-agent-sprint-cli、Cursor CLI sprint、headless Cursor Agent 並列実装、CLI worker sprint、yolo Cursor CLI worker で軽く並列実装するときに使う。
---

# Cursor Agent Sprint CLI（CLI 版軽量 Sprint）

短時間で完了する worker sprint を Cursor CLI で実行する。sprint の状態は `.codex/tmp/{YYMMDD}_{slug}/` に閉じ込め、委任する作業は範囲を明確にし、統合・検証・最終判断は main Codex が行う。

## 適用条件

以下をすべて満たすときに使う。

- ユーザーが永続的な計画書ではなく、今すぐ実装または調査を進めたい。
- 作業を小さな task graph にできる。
- 委任する edit task ごとに read scope、write scope、禁止パス、検証コマンドを書ける。
- 並列化する task の write scope が重ならない。
- Cursor CLI の `--yolo` 実行を、main Codex の diff 検収で受け止められる。
- 現在の working tree の中で統合と検収まで完了できる。

複数日にまたがる大きな計画、プロダクト判断が曖昧な作業、write scope が重なる作業には使わない。その場合は main Codex が直接扱うか、永続的な計画にするかをユーザーに確認する。

## 絶対ルール

- worker に commit、push、PR 作成、branch 切替、progress file 更新、最終完了判断を任せない。
- 2 つ以上の worker に同じファイル、同じ contract、同じ UI surface を並列編集させない。
- ユーザーが明示しない限り、既存の未コミット変更を戻さない。
- Cursor CLI worker は `--yolo` で動く。final report は参考情報として扱い、diff と検証を main Codex が確認してから受け入れる。
- Cursor CLI model は `composer-2.5-fast` 固定。

## Sprint Directory（作業ディレクトリ）

まず workspace と skill path を設定し、同梱 script で sprint directory を初期化する。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/project/cursor-agent-sprint-cli"
SPRINT_SLUG="<short-slug>"
"$SKILL_DIR/scripts/init_sprint.sh" --workspace "$WORKSPACE" --slug "$SPRINT_SLUG"
. "$WORKSPACE/.codex/tmp/$(date +%y%m%d)_$SPRINT_SLUG/sprint-env.sh"
```

script は次の構成を作る。

```text
.codex/tmp/YYMMDD_slug/
  brief.md
  tasks.md
  prompts/
  reports/
  review.md
  thread-registry.jsonl
  process-audit.jsonl
  sprint-env.sh
```

`brief.md` には user goal、scope、制約、最小検証を書く。`tasks.md` は task id、依存関係、owner、read/write scope、conflict、検証方法の source of truth にする。`review.md` には main Codex の統合・検収メモを書く。

## 進め方

### 1. 先に repo を読む

分割する前に、必要な repository context を読む。

- `AGENTS.md`
- `package.json`
- ユーザー指示に関係する route、module、component、server code
- 影響範囲に近い既存 test

状態を記録する。

```bash
git status --short
git branch --show-current
```

既存の変更はユーザーまたは先行 agent の作業として扱う。戻さず、上書きせず、必要なら避けて作業する。

### 2. Mini Plan（短い実行計画）を書く

`SPRINT_DIR` の `brief.md` と `tasks.md` を編集する。計画は小さく、実行に必要なことだけを書く。`init_sprint.sh` が同梱テンプレートをコピー済みなので、今回不要な task / section を削る。

`brief.md` には目的、scope、repo context、制約、最小検証、acceptance を書く。`tasks.md` には Status Board、Task Graph、File Dependency Graph、Ready Queue、Parallel Execution Plan、Blocked Queue、Conflict Table、Integration Batches、Task Contracts を書く。

並列実行は明示する。`Task Graph` と `File Dependency Graph` で依存と write scope を可視化し、`Parallel Execution Plan` に同時投入する task group を書く。同一 `parallel_group` の ready task は 1 件ずつ完了待ちしない。各 `--submit` の成功だけ確認して group 内の task を連続投入し、その後 `--monitor-all` でまとめて待つ。

task contract はこの形を保つ。`Task ID:` は worker prompt と検証 script の必須ラベルなので英語表記のまま使う。

```text
Task ID: T20a
担当: cursor-cli-agent | main-codex | codex-subagent
種別: contract | parallel | review | integration | validation | setup
状態:
目的:
依存:
並列グループ:
統合バッチ:
読み取り範囲:
書き込み範囲:
禁止:
競合:
受け入れ条件:
worker 検証:
main 検証:
```

task を分類する。

- `contract`: data source、auth、routing、schema、state、API boundary など下流を決める変更。main Codex 優先。
- `parallel`: write scope が局所的で分離できる実装。Cursor CLI worker 候補。
- `review`: read-only の risk analysis、設計比較、test strategy。Codex subagent 候補。
- `integration`: worker 成果の統合、conflict 解消、共有面の調整。必ず main Codex。
- `validation`: typecheck、test、build、browser check、dry-run。最終責任は main Codex。

### 3. Cursor CLI を preflight する

Cursor CLI worker を 1 task でも使う場合は必ず実行する。

```bash
"$SKILL_DIR/scripts/run_cursor_cli_delegate.sh" \
  --workspace "$WORKSPACE" \
  --registry-file "$REGISTRY_FILE" \
  --preflight
```

preflight は `cursor` command、`cursor agent --version`、`cursor agent status`、`cursor agent models` 内の `composer-2.5-fast`、read-only smoke JSON result を確認する。成功するまで実装 task を submit しない。

### 4. Worker Prompt（委任プロンプト）を作る

task ごとに `prompts/Txx.md` を 1 つ作る。絶対パスを使う。1 prompt には 1 task だけを書く。

prompt の先頭には `Task Summary:` を置く。このラベルは Cursor CLI thread の title をばらけさせるための必須契約なので英語表記のまま使う。先頭 1 から 3 行だけで task id、担当領域、成果物が分かる短い固有文にする。複数 worker で同じ `Task Summary` を使わない。`--submit` する prompt は `Task Summary:` が必須で、180 文字以内にする。

```text
Task Summary:
T20a - split archive LP URL validator in src/core/archive-lp/url-validator.ts

あなたはこの repository 内で動く Cursor CLI worker agent です。

Worker:
cursor-cli-agent

Workspace:
/absolute/path/to/workspace

Task ID:
T20a

Goal:
具体的な task を 1 つだけ書く。

Read first:
- /absolute/path/to/file
- /absolute/path/to/file

Write scope:
- Allowed:
  - path/to/file
- Forbidden:
  - docs/PLAN/**
  - .codex/skills/**
  - 明示的に許可された task report 以外の .codex/tmp/**
  - 明示的に許可されていない package-lock.json
  - allowed write scope 外のファイル

Constraints:
- stage、commit、push、PR 作成、branch 切替、planning/progress file 更新をしない。
- 関係ない既存変更を戻さない。
- 他の worker またはユーザーが無関係なファイルを変更中かもしれない前提で作業する。
- repository instructions、TDD、YAGNI、振る舞いベースのテストを守る。

Verification:
- Run: npm test -- <specific test>
- 実行できない場合は、理由と代わりに確認した内容を具体的に報告する。

Final report:
- TASK_ID: T20a
- 変更したファイル
- 変更内容の要約
- 実行した検証と結果
- main Codex に残した作業
```

Codex subagent には同じ構造を使い、`Worker: codex-subagent` と書く。read-only か edit-allowed かを明示する。write scope が強く分離できない限り read-only を優先する。

### 5. Cursor CLI task を投入する

依存関係が解決済みで、write scope が重ならない task だけを submit する。同一 `parallel_group` に複数の ready task がある場合は、1 件ずつ monitor で完了待ちせず、すべて連続 submit してから `--monitor-all` する。

```bash
"$SKILL_DIR/scripts/run_cursor_cli_delegate.sh" \
  --workspace "$WORKSPACE" \
  --prompt-file "$SPRINT_DIR/prompts/T20a.md" \
  --registry-file "$REGISTRY_FILE" \
  --submit
```

内部では次の固定 command を background 起動する。

```bash
cursor agent --print --yolo --trust \
  --workspace "$WORKSPACE" \
  --model composer-2.5-fast \
  --output-format json \
  "$PROMPT_TEXT"
```

stdout は `$SPRINT_DIR/reports/<task-id>.json`、stderr は `$SPRINT_DIR/reports/<task-id>.stderr.log`、exit code は `$SPRINT_DIR/reports/<task-id>.exit-code` に残る。

### 6. 監視と復旧

個別 task を monitor する。

```bash
"$SKILL_DIR/scripts/run_cursor_cli_delegate.sh" \
  --workspace "$WORKSPACE" \
  --registry-file "$REGISTRY_FILE" \
  --monitor-registry \
  --task-id "T20a" \
  --wait \
  --timeout 180 \
  --poll-interval 3
```

sprint 内の task をまとめて monitor する。

```bash
"$SKILL_DIR/scripts/run_cursor_cli_delegate.sh" \
  --workspace "$WORKSPACE" \
  --registry-file "$REGISTRY_FILE" \
  --monitor-all \
  --wait \
  --max-records 5 \
  --timeout 180 \
  --poll-interval 3
```

monitor output が `done: true` の task だけ Cursor CLI result として受け入れる。`failed: true` の場合は stderr tail と JSON output を読んで、main Codex が修正・再投入・棄却を判断する。

### 7. 受け入れ前に検収する

worker 完了後、main Codex は必ず確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

確認項目:

- 変更ファイルが allowed write scope に収まっている。
- 複数 worker が同じファイルや contract を触っていない。
- 既存のユーザー変更または先行 agent 変更が戻されていない。
- final report と実際の diff が一致している。
- ユーザー視点で必要な振る舞いが完了している。
- worker verification が成功している。失敗または未実行なら、理由が具体的で受け入れ可能である。

範囲外変更が見えた場合は、diff を見てから判断する。worker 由来で安全に直せると明確な場合だけ main Codex が修正してよい。ユーザーの変更かもしれない場合は触る前に確認する。

### 8. 統合と検証

worker の完了順ではなく依存順に統合する。main Codex は共有 contract を解決し、リスクに見合う最小検証を実行する。

- 振る舞い変更: focused unit / integration test
- TypeScript / API surface 変更: `npm run typecheck`
- 影響範囲が広い変更: `npm test`
- app-level / routing 変更: `npm run build`
- UI 変更: 可能なら browser check

結果は `review.md` に記録する。diff、scope、report、verification が揃ってから task を accepted にする。

### 9. 報告

最終報告には必要なものだけを書く。

- sprint directory path
- 使った worker type
- 変更ファイル
- 実行した検証と結果
- 棄却または修正した worker output
- 残リスクや follow-up

ユーザーに求められていない限り、内部 plan を長く説明しない。

## Optional: 大きな計画を sprint-cli 実行単位へ分割する

大きな実装計画や調査計画を実行する前に、ユーザーが
`cursor-agent-sprint-cli でどう分けるか考えて`、`フェーズごとに sprint-cli したい`、
`大きい計画を CLI worker に分割したい` などを求めた場合だけ使う。

この option は **実装ではなく分割設計** を行う。計画の source of truth を先に特定し、
main Codex が sprint boundary を決める。ユーザー作業や外部設定が必要な場合は、
preflight、sprint group、barrier、次 sprint group のように stage を分ける。

詳細手順は `references/large-plan-sprint-division.md` を読む。
