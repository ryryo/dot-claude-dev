---
name: opencode-check
description: |
  opencode CLIの動作確認を行うシンプルなスキル。
  インストール状態、runコマンド、モデル応答の3項目をチェックする。

  Trigger:
  opencode動作確認, opencode check, opencodeが動くか確認
tags:
  - opencode
  - diagnostics
allowed-tools:
  - Bash
  - Read
---

# Opencode Check

opencode CLIが正常に動作するかを3ステップで確認する。

## ワークフロー

### Step 1: チェック実行

Bashで以下の3項目を順次確認する:

```bash
bash ~/dot-claude-dev/.claude/skills/dev/opencode-check/scripts/check.sh
```

**確認項目**:

| # | 項目 | 判定基準 |
|---|------|----------|
| 1 | CLIインストール | `which opencode` が見つかる |
| 2 | `run` コマンド | `opencode run` が正常終了 |
| 3 | モデル応答 | `openai/gpt-5.3-codex` が応答を返す |

### Step 2: 結果報告

チェック結果をユーザーに報告する。全項目PASSなら正常、FAILがあれば原因と対処法を提示。

## 変更履歴

| Version | Date       | Changes  |
|---------|------------|----------|
| 1.0.0   | 2026-02-12 | 初版作成 |
