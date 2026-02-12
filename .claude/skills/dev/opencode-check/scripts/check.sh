#!/usr/bin/env bash
set -euo pipefail

MODELS=("openai/gpt-5.3-codex" "zai-coding-plan/glm-4.7")
PASS="✅ PASS"
FAIL="❌ FAIL"
total_pass=0
total_count=0

echo "=== opencode CLI 動作確認 ==="
echo ""

# --- Check 1: CLIインストール ---
echo "--- [1] CLIインストール確認 ---"
if OPENCODE_PATH=$(which opencode 2>/dev/null); then
  echo "$PASS: opencode found at $OPENCODE_PATH"
  ((total_pass++))
else
  echo "$FAIL: opencode が見つかりません"
  echo "  対処: npm install -g opencode または brew install opencode"
  echo ""
  echo "=== 結果: FAIL (CLIが未インストールのため後続チェックをスキップ) ==="
  exit 1
fi
((total_count++))
echo ""

# --- Check 2+3: 各モデルのテスト ---
for MODEL in "${MODELS[@]}"; do
  echo "=========================================="
  echo "  モデル: $MODEL"
  echo "=========================================="
  echo ""

  # run コマンド動作
  echo "--- run コマンド動作確認 ---"
  ((total_count++))
  if OUTPUT=$(opencode run -m "$MODEL" "Respond with exactly: PING_OK" 2>&1); then
    if echo "$OUTPUT" | grep -qi "PING_OK"; then
      echo "$PASS: opencode run 正常動作"
      ((total_pass++))
    else
      echo "$FAIL: opencode run は実行できたが想定外の応答"
      echo "  応答: $OUTPUT"
    fi
  else
    echo "$FAIL: opencode run がエラーで終了"
    echo "  エラー: $OUTPUT"
  fi
  echo ""

  # モデル応答確認
  echo "--- モデル応答確認 ---"
  ((total_count++))
  if OUTPUT=$(opencode run -m "$MODEL" "What is 2+3? Reply with just the number." 2>&1); then
    if echo "$OUTPUT" | grep -q "5"; then
      echo "$PASS: $MODEL が正常に応答"
      ((total_pass++))
    else
      echo "$FAIL: モデルは応答したが内容が不正確"
      echo "  応答: $OUTPUT"
    fi
  else
    echo "$FAIL: モデル応答エラー"
    echo "  エラー: $OUTPUT"
  fi
  echo ""
done

# --- 集計 ---
echo "=== 結果: ${total_pass}/${total_count} PASS ==="
if [[ $total_pass -eq $total_count ]]; then
  echo "🎉 全チェック通過 — opencode CLIは正常に動作しています"
  exit 0
else
  echo "⚠️  一部チェックが失敗しています"
  exit 1
fi
