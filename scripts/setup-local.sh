#!/bin/bash
# scripts/setup-local.sh
# dot-claude-dev プロジェクト固有のリモート環境セットアップ

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

# --- プロジェクト固有セットアップ ---
# 必要に応じてここに処理を追加

exit 0
