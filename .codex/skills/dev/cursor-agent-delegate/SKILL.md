---
name: cursor-agent-delegate
description: |
  macOS の Cursor IDE Agent Window と Codex subagent を worker pool として使い分ける。複雑なロジック・設計レビュー・深い調査は Codex subagent に、低〜中程度の局所実装・テスト作成は Cursor Agent に委任する。差分の検収・検証・最終判断は main Codex が担う。Use when delegating bounded coding work from Codex to Codex subagents or Cursor Agent, coordinating macOS Cursor IDE AppleScript/CDP workflows, or parallel non-overlapping worker tasks.
  Anchors: Cursor Agent, macOS Cursor IDE, CDP, Codex subagent, worker delegation.
---

# cursor-agent-delegate

main Codex を orchestrator・reviewer・integrator として位置づけ、Codex subagent と Cursor Agent を範囲限定の worker として活用する。worker には独立したタスクだけを渡し、最終判断・差分の検収・commit / push / PR は main Codex が行う。

## 参照先

このファイルは目的・絶対ルール・実行ステップのみを持つ。詳細は必要になった時点で以下を読む。

- Cursor Agent の通常運用: [references/operations.md](references/operations.md)
- 障害・CDP/lock/guard/monitor の失敗・重い挙動: [references/troubleshooting.md](references/troubleshooting.md)
- transport の制約や実装の確認・変更: [references/transports.md](references/transports.md)
- worker の選定に迷う場合: [references/worker-selection.md](references/worker-selection.md)
- worker prompt の作成: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- worker の結果を受け入れる際: [references/review-checklist.md](references/review-checklist.md)

## 絶対ルール

- Cursor Agent の標準経路は macOS `mac-ide-cdp`。通常 profile の Cursor IDE を loopback CDP port 付きで使う。
- 別 `--user-data-dir`・`--no-lock`・`--no-process-guard`・大きな guard 上限値は通常運用では使わない。
- `--monitor-all` は今回のセッションで作成した registry を一覧確認するために使う。古い thread の完全復元には使わない。
- Cursor の final report は参考情報であり、完了判定そのものではない。main Codex が diff・ファイル内容・検証結果を確認して判断する。
- worker には以下を任せない: planning / progress の更新、Gate PASS 判定、commit、push、merge、PR、最終統合。
- 複数の worker を並列で動かす場合、同じファイルを複数の worker に編集させない。write scope が少しでも重なるなら分割せず main Codex が扱う。
- 既存の未コミット変更やユーザーの作業を元に戻さない。範囲外変更が混入した場合は [references/review-checklist.md](references/review-checklist.md) に従う。
- 問題が起きたとき、新しい Cursor / CDP の実行を増やさない。[references/troubleshooting.md](references/troubleshooting.md) に従う。

## 実行ステップ

### 1. 委任するかどうかを決める

goal・読む範囲・編集してよい範囲・触ってはいけないパス・検証方法を言語化できる場合だけ委任する。並列委任は worker ごとの編集対象ファイルが重ならない場合だけ行う。複雑なロジック・設計比較・深い調査は Codex subagent に、低〜中程度の局所実装・テスト追加は Cursor Agent に優先して割り当てる。選定に迷う場合は [references/worker-selection.md](references/worker-selection.md) を読む。

### 2. 委任内容をまとめる

worker prompt には 1 つのタスクだけを書く。workspace・task id・最初に読むファイル・編集してよい範囲・禁止事項・検証コマンド・最終報告形式を含める。prompt の作成時は [references/delegation-prompt-template.md](references/delegation-prompt-template.md) を読む。

### 3. 実行する

**Cursor Agent を使う場合:** 実行前に [references/operations.md](references/operations.md) を読む。CDP endpoint・Cursor Agents target・guard・registry・process audit の各契約に従って submit・monitor を行う。transport の仕様を確認する必要がある場合だけ [references/transports.md](references/transports.md) を読む。

**Codex subagent を使う場合:** ownership・scope・verification・final report format を prompt に含め、main Codex が結果を検収する。

### 4. 監視・回収する

research / review 系の Cursor Agent タスクは DOM final report を回収してよい。編集系は DOM final report に加えて、実ファイル・diff・検証結果を確認する。複数の Cursor thread を確認する場合は、今回のセッションで作成した registry だけを対象に `monitor-all` を使う。

### 5. 検収する

worker が完了したら必ず [references/review-checklist.md](references/review-checklist.md) を読む。write scope・既存の変更・diff・報告内容・検証結果を main Codex が確認する。範囲外の変更は採用しない。

### 6. 報告・統合する

最終報告には worker type・transport・変更ファイル・検証結果・採用 / 棄却の判断・残課題を含める。commit / push / PR が必要な場合も main Codex が行う。
