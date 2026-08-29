# GPT-5.5 Prompting Rules for spec-codex

Source: <https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5>

## Main Codex Skill

`spec-codex` / `spec-codex-run` の本体は、次を中心に書く。

- 成果物。
- 判断基準。
- 完了条件。
- 使用する証拠。
- 停止条件。

古いモデル向けの細かい手順列挙をそのまま持ち込まない。必要な実行手順は、迷わず作業できる範囲に限定する。

## PLAN Artifacts

出力される PLAN は短くしない。`spec.md` は人間が全体像を把握するために必要な背景、設計決定、図、リスクを持つ。`tasks.json` は実行エージェント向けの Gate 契約を持つ。

## Cursor Agent Delegation

Cursor Agent や軽量モデルへ委任するプロンプトは、本体スキルとは別方針にする。

- 期待成果物。
- write scope。
- 編集禁止範囲。
- 検証コマンド。
- 完了報告形式。
- `docs/PLAN` 更新禁止。
- commit / push 禁止。

軽量モデルには、暗黙の補完を期待しない。局所タスクの契約として十分に詳細な brief を生成する。
