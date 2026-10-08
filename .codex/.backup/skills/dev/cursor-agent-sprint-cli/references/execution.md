# Cursor Sprintの実行

実際にCursorへ委譲する場合に読む。ownerと委譲条件は[入口](../SKILL.md)を正本とし、ここでは初期化、prompt、投入、監視、障害時の復旧を扱う。

## Sprint Directory（作業ディレクトリ）

まず workspace と skill のパスを設定し、同梱スクリプトで sprint directory を初期化する。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-sprint-cli"
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

`brief.md` にはユーザーの目的、範囲、制約、最小検証を書く。`tasks.md` は task id、依存関係、owner、read/write scope、競合、検証方法の source of truth にする。`review.md` には main Codex の統合・検収メモを書く。

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
```

既存の変更はユーザーまたは先行 agent の作業として扱う。戻さず、上書きせず、必要なら避けて作業する。

### 2. Mini Plan（短い実行計画）を書く

`SPRINT_DIR` の `brief.md` と `tasks.md` を編集する。計画は小さく、実行に必要なことだけを書く。`init_sprint.sh` が同梱テンプレートをコピー済みなので、今回使わない task や section を削る。

`brief.md` にはユーザーの目的、範囲、Repository Context、制約、最小検証、受け入れ条件を書く。`tasks.md` には状態一覧、作業依存グラフ、ファイル依存グラフ、投入待ち、並列投入計画、停止中、競合表、統合単位、作業契約を書く。

並列実行は明示する。`作業依存グラフ` と `ファイル依存グラフ` で依存と write scope を可視化し、`並列投入計画` に同時投入する task group を書く。同一 `parallel_group` の ready task は 1 件ずつ完了待ちしない。各 `--submit` の成功だけ確認して group 内の task を連続投入し、その後 `--monitor-all` でまとめて待つ。

task contract はこの形を保つ。`Task ID:` は worker prompt と検証 script の必須ラベルなので英語表記のまま使う。

```text
Task ID: T20a
担当: main-codex | cursor-cli-agent
状態:
目的:
依存:
複雑さ: low | medium | high
判断状態: fixed | bounded | unresolved
独立性: independent | staged | coupled
副作用: local_reversible | shared_reversible | external_or_irreversible
検証 oracle: strong | partial | weak
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

担当は最初に `main-codex` と置く。委任判定の6条件を満たすtaskを `cursor-cli-agent` に変える。complexityは実行量と検証強度に使い、このskillではCodex subagent経路を作らない。

### 3. Worker Prompt（委任プロンプト）を作る

task ごとに `prompts/Txx.md` を 1 つ作る。絶対パスを使う。1 prompt には 1 task だけを書く。

prompt の先頭には `Task Summary:` を置く。このラベルは Cursor CLI thread の title を区別するための必須ラベルなので英語表記のまま使う。先頭 1 から 3 行だけで task id、担当領域、成果物が分かる短い固有文にする。複数 worker で同じ `Task Summary` を使わない。`--submit` する prompt は `Task Summary:` が必須で、180 文字以内にする。

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

Complexity:
low | medium | high

Decision state:
fixed | bounded

Independence:
independent | staged

Side-effect scope:
local_reversible | shared_reversible

Verification oracle:
strong | partial + mainが確認する限定項目

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
- version control／remote操作、planning/progress file 更新をしない。
- 関係ない既存変更を戻さない。
- 他の worker またはユーザーが無関係なファイルを変更中かもしれない前提で作業する。
- repository instructions、TDD、YAGNI、振る舞いベースのテストを守る。
- 未解決のarchitecture、product、security、data ownership判断が必要になったら、推測せず停止して論点を報告する。
- production、外部設定、実data、課金、権限などローカルdiffで戻せないstateを変更しない。

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

### 4. Cursor CLI task を投入する

依存関係が解決済みで、委任判定の6条件を満たし、write scopeが重ならないtaskだけをsubmitする。同一 `parallel_group` に複数のready taskがある場合は、1件ずつmonitorで完了待ちせず、すべて連続submitしてから`--monitor-all`する。

Cursor CLI は、この skill を使う環境では既に利用可能な前提で扱う。通常の sprint plan、task graph、投入前 checklist に preflight task を入れない。

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

### 5. 監視する

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

## 例外処理: Cursor CLI 疎通に失敗した場合

この section は通常フローでは実行しない。`--submit`、`--monitor-registry`、`--monitor-all` の実行結果を見て、Cursor CLI 自体の疎通問題だと判断した場合だけ使う。task graph や sprint の最初の作業には入れない。

preflight に進む条件:

- `cursor` command が見つからない、または `cursor agent` が起動できない。
- login / status / model list / `composer-2.5-fast` 由来のエラーが出る。
- read-only smoke 以前の段階で JSON output が得られず、worker prompt の問題ではなく CLI 疎通問題だと判断できる。
- 複数 task の submit / monitor が同種の CLI-level error で失敗する。

追加投入を止め、復旧確認として次を実行する。

```bash
"$SKILL_DIR/scripts/run_cursor_cli_delegate.sh" \
  --workspace "$WORKSPACE" \
  --registry-file "$REGISTRY_FILE" \
  --preflight
```

preflight は `cursor` command、`cursor agent --version`、`cursor agent status`、`cursor agent models` 内の `composer-2.5-fast`、read-only smoke の JSON result を確認する。成功したら失敗した task を再投入する。失敗した場合は、Cursor CLI 環境の問題として main Codex が復旧、ユーザー確認、または Cursor CLI 委任の中止を判断する。
