---
name: dev:deslop
description: "Remove AI-generated code slop from code changes in the current branch"
version: "1.0.0"
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
  - Grep
  - Glob
  - Task
---

# AIコードの不備を解消する

mainとのdiffを確認し、このブランチで追加されたAI生成コードの不備をすべて除去する。
サブエージェントを起動してこの処理を進める。

対象となる不備：

- 人間なら書かないコメント、またはファイル内の他の箇所と一貫性のないコメント
- そのコードベースの該当箇所では通常ありえない過剰な防御チェックやtry/catchブロック（信頼済み・検証済みのコードパスから呼ばれる場合は特に）
- ファイルのスタイルと一致しないその他の記述

最後に変更内容を1〜3文で簡潔にまとめて報告する
