---
name: cursor-agent-delegate
description: |
  Codex subagent と Cursor Agent を worker pool として使い分け、複雑ロジック・設計レビュー・深い調査は Codex subagent、低〜中複雑度の局所実装・テスト作成は Cursor Agent に委任し、main Codex 側で差分・検証結果・範囲逸脱を検収する。Use when delegating bounded coding work from Codex to Codex subagents or Cursor Agent, coordinating macOS Cursor IDE AppleScript default workflows, WSL Cursor CLI workflows, or parallel non-overlapping worker tasks.
---

# cursor-agent-delegate

main Codex を orchestrator / final reviewer / integrator、Codex subagent と Cursor Agent を worker として扱う。worker に渡すのは、write scope と検証条件が明確な独立タスクだけにする。

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

## Transport

Cursor Agent を選んだ場合、macOS の標準 transport は `mac-ide-applescript`。AppleScript preflight / smoke が失敗した場合、またはユーザーが CLI を明示した場合だけ `cli` を使う。WSL の標準 transport は `cli`。prompt を手動確認つきで Cursor IDE に渡したい場合だけ `deeplink` を使う。

Transport の詳細、制約、fallback は必要時に [references/transports.md](references/transports.md) を読む。

- `mac-ide-applescript`: macOS 標準。Cursor IDE に prompt を投入する高速経路。
- `cli`: macOS fallback / 明示指定、WSL 標準。`agent` コマンドを使う headless 経路。
- `deeplink`: Cursor IDE に prompt を prefill する手動確認 fallback。

Windows native と Windows GUI automation は対象外。WSL から Windows 側 Cursor IDE を操作しない。

## Step 1: Preflight

必ず委任前に確認する。Codex subagent を使う場合は、利用可能な subagent / worker tool があることを確認し、タスクごとの ownership と write scope を明示する。Cursor Agent を使う場合、macOS では先に `mac-ide-applescript` の preflight を行い、使えない場合だけ CLI preflight を行う。WSL では CLI preflight を行う。

```bash
command -v agent
agent status
agent models | rg '^composer-2\.5\b'
git status --short
```

- `agent` が存在しない場合は preflight failure。
- 標準モデルは `composer-2.5`。速度優先が明示されたときだけ `composer-2.5-fast` を使う。
- WSL では repo が Linux filesystem 配下にあることを推奨する。`/mnt/c/...` は明示許可がなければ warning として扱う。
- 委任前の `git status --short` を記録し、既存変更を Cursor の成果物と混同しない。

Wrapper を使う場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --mode ask \
  --workspace "$PWD" \
  --prompt-file /path/to/prompt.txt
```

macOS で prompt 投入後に送信まで行う場合は `--submit` を明示する。送信後も Cursor UI の状態で完了判定せず、main Codex が diff と検証コマンドで回収する。
編集委任では、送信前に Cursor Agent window が `Ask` mode ではないことを確認する。`Ask` chip が残っている場合、Cursor はファイル編集を行わず read-only 応答で終了する。

macOS で CLI を強制する場合:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport cli \
  --mode ask \
  --workspace "$PWD" \
  --prompt-file /path/to/prompt.txt
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

Cursor Agent read-only 調査:

```bash
agent -p --mode ask \
  --workspace "$WORKSPACE" \
  --model composer-2.5 \
  --output-format text \
  "$PROMPT"
```

Cursor Agent 編集あり:

```bash
agent -p --force --trust \
  --workspace "$WORKSPACE" \
  --model composer-2.5 \
  --output-format stream-json \
  --stream-partial-output \
  "$PROMPT" | tee "$LOG"
```

並列実行は write scope が重ならない場合だけにする。Cursor Agent は 2〜4 件までを目安にし、Codex subagent は実行環境の同時実行上限に従う。各 worker ごとに worker type、workspace、log path または agent id、allowed write scope を記録する。

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
- CLI transport では stream metadata から実際の model / session を確認する。
- AppleScript transport では model を programmatically verify できないため、その旨を報告する。

範囲外変更は採用しない。worker が作った範囲外変更だけを特定できる場合に限り main Codex が修正し、特定できなければユーザーに判断を仰ぐ。

## Step 6: 報告する

最終報告に含める:

- 使用 worker type、transport、model。
- worker が変更したファイル。
- main Codex が確認した diff と検証結果。
- 採用した差分、棄却した差分、残課題。
