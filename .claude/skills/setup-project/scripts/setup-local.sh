#!/bin/bash
# setup-local.sh
# プロジェクト固有のリモート環境セットアップ
# テンプレート: setup-project スキルで各プロジェクトの scripts/ にコピーされる
#
# このファイルはプロジェクトごとに自由に編集してください。
# setup-claude-remote.sh（共通設定）とは独立しているため、
# 共通テンプレートの更新時にも上書きされません。

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

# --- プロジェクト固有セットアップ ---
# プロジェクト固有の処理をここに追加してください
# 例: npm install, docker setup, 環境変数の設定など

exit 0
