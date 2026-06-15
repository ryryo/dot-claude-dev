---
name: cursor-agent-delegate
description: |
  macOS の Cursor IDE Agent Window と Codex subagent を worker pool として使い分け、複雑ロジック・設計レビュー・深い調査は Codex subagent、低〜中複雑度の局所実装・テスト作成は Cursor Agent に委任し、main Codex 側で差分・検証結果・範囲逸脱を検収する。Use when delegating bounded coding work from Codex to Codex subagents or Cursor Agent, coordinating macOS Cursor IDE AppleScript/CDP workflows, or parallel non-overlapping worker tasks.
  Anchors: Cursor Agent, macOS Cursor IDE, CDP, Codex subagent, worker delegation.
---

# cursor-agent-delegate

main Codex を orchestrator / reviewer / integrator とし、Codex subagent と Cursor Agent を範囲限定の worker として使う。worker には独立タスクだけを渡し、最終判断・差分検収・commit / push / PR は main Codex が行う。

## 必読ルーティング

このファイルは目的、絶対ルール、実行ステップだけを持つ。詳細は必要になった時点で次を読む。

- 通常運用で Cursor Agent を使う: [references/operations.md](references/operations.md)
- 障害、重い挙動、CDP/lock/guard/monitor 失敗: [references/troubleshooting.md](references/troubleshooting.md)
- transport の制約や実装を確認・変更する: [references/transports.md](references/transports.md)
- worker 選定に迷う: [references/worker-selection.md](references/worker-selection.md)
- worker prompt を作る: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- worker 結果を受け入れる: [references/review-checklist.md](references/review-checklist.md)

## 絶対ルール

- Cursor Agent の標準経路は macOS `mac-ide-cdp`。通常 profile の Cursor IDE を loopback CDP port 付きで使う。
- 別 `--user-data-dir`、`--no-lock`、`--no-process-guard`、大きな guard 上限値は通常運用で使わない。
- `--monitor-all` は今回のセッションで作った registry を一覧確認するために使う。古い thread の完全復元には使わない。
- Cursor の final report は参考情報であり、完了判定そのものではない。main Codex が diff、file contents、verification を検収する。
- worker に planning/progress 更新、Gate PASS 判定、commit、push、merge、PR、最終統合を任せない。
- 複数 worker を並列に動かす場合、同じファイルを複数 worker に編集させない。write scope が少しでも重なるなら分割せず main Codex が扱う。
- 既存未コミット変更やユーザー作業を戻さない。範囲外変更が混ざったら [references/review-checklist.md](references/review-checklist.md) に従う。
- 問題が起きたら新しい Cursor/CDP 実行を増やさず、[references/troubleshooting.md](references/troubleshooting.md) に従う。

## 実行ステップ

### 1. 委任可否を決める

Goal、読むべき範囲、編集してよい範囲、触ってはいけないパス、検証方法を言語化できる場合だけ委任する。並列委任は worker ごとの編集対象ファイルが重ならない場合だけ行う。複雑ロジック・設計比較・深い調査は Codex subagent、低〜中複雑度の局所実装・テスト追加は Cursor Agent を優先する。迷う場合は [references/worker-selection.md](references/worker-selection.md) を読む。

### 2. 委任契約を書く

worker prompt は 1 task だけにする。workspace、task id、最初に読むファイル、編集してよい範囲、禁止事項、検証、最終報告形式を含める。prompt 作成時は [references/delegation-prompt-template.md](references/delegation-prompt-template.md) を読む。

### 3. 実行する

Cursor Agent を使う場合は、実行前に [references/operations.md](references/operations.md) を読む。CDP endpoint、Cursor Agents target、guard、registry、process audit の契約に従って submit / monitor する。transport 仕様を確認する必要がある場合だけ [references/transports.md](references/transports.md) を読む。

Codex subagent を使う場合も、ownership、scope、verification、final report format を prompt に含め、main Codex が結果を検収する。

### 4. 監視・回収する

Cursor Agent の research/review 系は DOM final report を回収してよい。編集系は DOM final report に加えて、実ファイル、diff、verification を確認する。複数 Cursor thread の確認には、今回のセッションで作った registry だけを対象にして `monitor-all` を使う。

### 5. 検収する

worker 完了後は必ず [references/review-checklist.md](references/review-checklist.md) を読む。write scope、既存変更、diff、報告内容、verification を main Codex が確認する。範囲外変更は採用しない。

### 6. 報告・統合する

最終報告には worker type、transport、変更ファイル、検証結果、採用/棄却、残課題を含める。commit / push / PR が必要な場合も main Codex が行う。
