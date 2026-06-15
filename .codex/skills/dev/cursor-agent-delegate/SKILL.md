---
name: cursor-agent-delegate
description: |
  macOS の Cursor IDE Agent Window と Codex subagent を worker pool として使い分け、複雑ロジック・設計レビュー・深い調査は Codex subagent、低〜中複雑度の局所実装・テスト作成は Cursor Agent に委任し、main Codex 側で差分・検証結果・範囲逸脱を検収する。Use when delegating bounded coding work from Codex to Codex subagents or Cursor Agent, coordinating macOS Cursor IDE AppleScript/CDP workflows, or parallel non-overlapping worker tasks.
  Anchors: Cursor Agent, macOS Cursor IDE, CDP, Codex subagent, worker delegation.
---

# cursor-agent-delegate

main Codex を orchestrator / final reviewer / integrator、Codex subagent と Cursor Agent を worker として扱う。worker に渡すのは、write scope と検証条件が明確な独立タスクだけにする。

## Reference Map

この `SKILL.md` は判断基準と安全契約だけを置く。実行手順や障害対応は必ず該当 reference を読む。

- 通常運用、CDP 起動、submit、monitor、guard log 確認: [references/operations.md](references/operations.md)
- CDP / Cursor / lock / process guard / monitor 失敗時: [references/troubleshooting.md](references/troubleshooting.md)
- Cursor / AppleScript / CDP / deeplink の制約: [references/transports.md](references/transports.md)
- worker 選定: [references/worker-selection.md](references/worker-selection.md)
- worker prompt 作成: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- 検収 checklist: [references/review-checklist.md](references/review-checklist.md)

## Operating Contract

- 通常運用では `mac-ide-cdp` を使う。
- Cursor は通常 profile のまま loopback CDP port 付きで起動する。別 `--user-data-dir` は使わない。
- `--no-lock`、`--no-process-guard`、大きな guard 上限値は通常運用で使わない。
- `--monitor-all` は fresh registry 用の dashboard として扱い、古い thread の完全復元には使わない。
- 問題が起きたら新しい Cursor/CDP 実行を増やさず、[references/troubleshooting.md](references/troubleshooting.md) に従う。
- Cursor の final report は証拠であり、完了判定の authority ではない。main Codex が diff / file contents / tests を検収する。

## 役割分担

| 役割                                             | 担当           |
| ------------------------------------------------ | -------------- |
| タスク分解・依頼契約・最終検収                   | main Codex     |
| 複雑ロジック、設計比較、深い調査、難しいレビュー | Codex subagent |
| 局所実装、テスト追加、既存 pattern に沿う修正    | Cursor Agent   |
| 最終統合・進捗更新・commit / push / PR           | main Codex     |

worker には planning/progress ファイル更新、Gate PASS 判定、commit、push、merge、最終統合を任せない。

## Worker Selection

worker 選定の詳細は必要時に [references/worker-selection.md](references/worker-selection.md) を読む。

- `codex-subagent`: 複雑な domain logic、アルゴリズム、状態遷移、設計比較、深いレビュー、リスク洗い出し。
- `cursor-agent`: 純粋関数、adapter、schema、単体テスト、既存 pattern に沿う局所修正、高速な実装代行。
- `main-codex`: 曖昧な仕様整理、最終統合、scope 判定、完了判定、commit / push / PR。

Codex subagent も worker であり、最終判断者ではない。subagent の結論や差分も main Codex が検収する。

## macOS Cursor Transport

Cursor Agent を選んだ場合、この skill は macOS の Cursor IDE Agent Window だけを対象にする。標準 transport は `mac-ide-cdp`。AppleScript は Cursor Agents window の前面化、Agent window 選択、補助クリック、ショートカット smoke に使えるが、現行 build で検証済みの no-clipboard prompt 投入は CDP 経路だけとする。prompt を手動確認つきで Cursor IDE に渡したい場合だけ `deeplink` を使う。

Transport の詳細、制約、fallback は必要時に [references/transports.md](references/transports.md) を読む。

- `mac-ide-cdp`: macOS 標準。Cursor IDE を remote debugging port 付きで起動し、CDP で Agent thread / contenteditable input を操作する経路。
- `mac-ide-applescript`: macOS 補助。Cursor Agents window の activate/focus や補助操作に使う。`Cmd+V` 系は標準採用しない。`AXTextArea` direct set による prompt 投入は現行 Cursor Agents build では未成立。
- `deeplink`: Cursor IDE に prompt を prefill する手動確認 fallback。

macOS Cursor IDE 以外は対象外。headless worker が必要な場合はこの skill ではなく別 skill として扱う。

## Step 1: Preflight

必ず委任前に確認する。Codex subagent を使う場合は、利用可能な subagent / worker tool があることを確認し、タスクごとの ownership と write scope を明示する。Cursor Agent を使う場合は macOS / Cursor IDE / Agent Window の preflight を行う。

```bash
test "$(uname -s)" = Darwin
test -d /Applications/Cursor.app
command -v osascript
git status --short
```

- Cursor IDE 側の model は UI state として扱う。AppleScript transport では programmatically verify しない。
- `mac-ide-cdp` では `http://127.0.0.1:<port>/json` と `/json/version` が読めることを確認する。
- 委任前の `git status --short` を記録し、既存変更を Cursor の成果物と混同しない。

Wrapper を使う場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --mode ask \
  --workspace "$PWD" \
  --prompt-file /path/to/prompt.txt
```

`auto` は `mac-ide-cdp` を使う。prompt 投入後に送信まで行う場合は `--submit` を明示するが、send button / shortcut がその Cursor build で検証済みでない場合は fail closed にする。送信後も Cursor UI の状態で完了判定せず、main Codex が result file、diff、検証コマンドで回収する。
Cursor 3.7.36 の `Cursor Agents` window では `button.ui-prompt-input-submit-button[aria-label="Send message"]` による submit を smoke 済み。research-only など result file がないタスクでは、provisional completion signal として「`Stop generation` が消える」「assistant response bubble に task id / final report が出る」を併用し、最後に `git status --short` でファイル変更がないことを確認する。
編集委任では、送信前に Cursor Agent window が `Ask` mode ではないことを確認する。`Ask` chip が残っている場合、Cursor はファイル編集を行わず read-only 応答で終了する。

CDP probe を行う場合:

```bash
curl http://127.0.0.1:9226/json/version
curl http://127.0.0.1:9226/json
```

## Step 2: Worker と委任可否を判断する

Codex subagent に渡してよい作業:

- 複雑な domain logic、アルゴリズム、状態遷移設計。
- 複数実装案の比較、設計レビュー、リスク洗い出し。
- 仕様から実装契約への分解。
- 高難度の diff review やテスト戦略レビュー。

Cursor Agent に渡してよい作業:

- 純粋関数、helper、schema、validator、adapter、単体テスト。
- 新規小ディレクトリまたは少数ファイルに閉じた実装。
- 依存が薄く、検証コマンドで正誤を判断できる作業。
- 既存コード調査、要約、テスト観点の洗い出し。

main Codex に残す作業:

- 共通 state、routing、認可、DB migration、export pipeline など高結合な変更。
- 複数領域をまたぐ最終統合。
- docs/PLAN、tasks.json、spec.md、進捗管理ファイルの更新。
- commit / push / PR。
- 期待動作や完了条件が曖昧な作業。

worker の ownership、write scope、検証条件を言語化できない場合は委任しない。

## Step 3: Worker Prompt を作る

プロンプトは結論ではなく契約として書く。詳細テンプレートは [references/delegation-prompt-template.md](references/delegation-prompt-template.md) を読む。

必須項目:

- Workspace absolute path。
- Goal は 1 件だけ。
- Read first の実在パス。
- Write scope と forbidden paths。
- 既存未コミット変更を戻さない指示。
- 実装制約。
- Verification command。
- Final report format。

長い prompt は一時ファイルに保存し、wrapper の `--prompt-file` で渡す。

## Step 4: 実行する

Codex subagent:

- subagent / worker tool が利用可能な場合だけ使う。
- prompt には ownership、write scope、他 worker の存在、既存変更を戻さないこと、検証、報告形式を含める。
- 複数 subagent を並列にする場合は write scope を重複させない。

Cursor Agent 単発投入:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE"
```

新規 thread を作って submit する場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --new-agent \
  --submit
```

`--submit` 時は既定で `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl` に JSONL registry を追記する。registry には task id、prompt hash、CDP target、workspace、submit 直後の chat title、sidebar snapshot を保存する。場所を変える場合は `--registry-file "$PATH"`、記録しない場合は `--no-registry` を使う。

登録済み thread の状態と直接 result を読む場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-registry \
  --task-id "$TASK_ID" \
  --wait
```

monitor は registry の sidebar snapshot から候補 thread を開き、本文に expected task id があることを確認してから DOM の assistant response を返す。research / review などファイル成果物が不要なタスクでは、この direct DOM result を標準回収経路にしてよい。編集タスクでは result file があると structured contract として強いが、最終 authority は常に main Codex の diff / verification。

registry 内の task id 付き thread をまとめて監視する場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-all \
  --wait
```

`--monitor-all` は registry の最新 record を task id ごとに 1 件ずつ読み、各 thread を本文 task id で確認して `done_count`、`running_count`、`unmatched_count`、各 thread の direct DOM result を返す。並列委任中の dashboard 的な確認に使う。
古い registry や title が変わった thread を含む場合は、候補総当たりで UI を長時間占有しないよう `--max-candidates` の既定 3 件、`--max-records` の既定 8 件で打ち切り、見つからない thread は `unmatched` として扱う。

CDP transport は共通 guard を持つ。wrapper は workspace 単位の lock を取り、同じ workspace で複数の Cursor CDP 操作が同時に走る場合は fail closed する。Python helper は `--max-cdp-calls`、`--max-clicks`、`--max-runtime` で protocol call 数、UI click 数、実行時間を制限する。さらに wrapper は process guard 経由で helper を起動し、実際に起動された process 数を `$WORKSPACE/.agent_runs/cursor/process-audit.jsonl` に記録する。`--max-child-processes` を超えた場合は helper の process group を止める。通常運用で `--no-lock`、`--no-process-guard`、大きな上限値を使わない。

Cursor Agent 複数 thread 管理の調査:

```bash
curl http://127.0.0.1:9226/json
```

並列実行は write scope が重ならない場合だけにする。Cursor Agent は 2〜4 件までを目安にし、Codex subagent は実行環境の同時実行上限に従う。各 worker ごとに worker type、workspace、Cursor thread / worktree / run id、allowed write scope を記録する。
同一 project 内の thread 切替は sidebar の `.glass-sidebar-agent-menu-btn` を使う。title は Cursor が自動生成し、重複や prompt 冒頭への置換が起きるため、title だけを thread id として扱わない。作成直後に sidebar index / visible title / expected task id を registry に記録し、切替後は本文の task id で確認する。実行中 monitoring は active thread では `Stop generation` を取得できるが、複数 running thread を安定監視するにはこの registry 実装が必要。

## Step 5: 検収する

worker 終了後、main Codex が必ず検収する。詳細チェックリストは [references/review-checklist.md](references/review-checklist.md) を読む。

```bash
git status --short
git diff --name-only
git diff --stat
```

確認すること:

- 変更ファイルが write scope に収まっている。
- 既存未コミット変更を巻き戻していない。
- worker の報告と実際の diff / reasoning / 検証結果が一致している。
- 検証コマンドが成功している、または失敗理由が妥当。
- AppleScript transport では model を programmatically verify できないため、その旨を報告する。
- CDP transport では target id / title / URL / workspace 推定を記録する。

範囲外変更は採用しない。worker が作った範囲外変更だけを特定できる場合に限り main Codex が修正し、特定できなければユーザーに判断を仰ぐ。

## Step 6: 報告する

最終報告に含める:

- 使用 worker type、transport、model。
- worker が変更したファイル。
- main Codex が確認した diff と検証結果。
- 採用した差分、棄却した差分、残課題。
