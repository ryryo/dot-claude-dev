#!/usr/bin/env bash
# Codex の "Invalid request" やタスク失敗時に原因を診断する
# Usage: bash diagnose-codex.sh [CODEX_COMPANION_PATH]
set -euo pipefail

COMPANION="${1:-}"
if [[ -z "$COMPANION" ]]; then
  COMPANION="$(bash "$(dirname "$0")/resolve-codex-plugin.sh" 2>/dev/null)" || {
    echo "❌ codex-companion が見つかりません"
    exit 1
  }
fi

echo "=== Codex 診断レポート ==="
echo ""

# 1. setup 状態
echo "## 1. Setup 状態"
SETUP_JSON=$(node "$COMPANION" setup --json 2>&1) || true
echo "$SETUP_JSON" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(f'  ready:       {d.get(\"ready\")}')
    print(f'  codex CLI:   {d.get(\"codex\", {}).get(\"detail\", \"N/A\")}')
    print(f'  auth:        {d.get(\"auth\", {}).get(\"detail\", \"N/A\")}')
    rt = d.get('sessionRuntime', {})
    print(f'  runtime:     {rt.get(\"mode\", \"N/A\")} ({rt.get(\"label\", \"\")})')
    print(f'  endpoint:    {rt.get(\"endpoint\", \"N/A\")}')
except:
    print('  (JSON パース失敗)')
    print(sys.stdin.read() if hasattr(sys.stdin, 'read') else '')
" 2>/dev/null || echo "  $SETUP_JSON"
echo ""

# 2. プロジェクト信頼レベル
echo "## 2. プロジェクト信頼レベル"
CWD="$(pwd)"
CONFIG="$HOME/.codex/config.toml"
if [[ -f "$CONFIG" ]]; then
  if grep -q "\"$CWD\"" "$CONFIG" 2>/dev/null; then
    TRUST=$(grep -A1 "\"$CWD\"" "$CONFIG" | grep trust_level | sed 's/.*= *"\(.*\)"/\1/')
    echo "  $CWD → $TRUST"
  else
    echo "  ⚠️  $CWD は config.toml の trusted リストに含まれていません"
    echo "  (Codex TUI で一度このプロジェクトを開いて trust する必要があるかもしれません)"
  fi
else
  echo "  ⚠️  $CONFIG が見つかりません"
fi
echo ""

# 3. 認証トークンの有効期限
echo "## 3. 認証トークン"
AUTH_JSON="$HOME/.codex/auth.json"
if [[ -f "$AUTH_JSON" ]]; then
  python3 -c "
import json, base64, datetime, sys
with open('$AUTH_JSON') as f:
    data = json.load(f)
print(f'  auth_mode:    {data.get(\"auth_mode\", \"N/A\")}')
print(f'  API key set:  {data.get(\"OPENAI_API_KEY\") not in (None, \"None\", \"\")}')
token = data.get('tokens', {}).get('access_token', '')
if token:
    parts = token.split('.')
    if len(parts) >= 2:
        payload = parts[1] + '=' * (4 - len(parts) % 4)
        try:
            decoded = json.loads(base64.b64decode(payload))
            exp = decoded.get('exp')
            if exp:
                exp_dt = datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                expired = now > exp_dt
                print(f'  token expires: {exp_dt.isoformat()}')
                print(f'  expired:       {expired}')
                if expired:
                    print(f'  ⚠️  トークンが期限切れです。codex auth で再認証してください')
            else:
                print('  token: exp claim なし')
        except Exception as e:
            print(f'  token decode error: {e}')
else:
    print('  ⚠️  access_token が空です')
print(f'  last_refresh: {data.get(\"last_refresh\", \"N/A\")}')
" 2>/dev/null || echo "  (auth.json のパースに失敗)"
else
  echo "  ⚠️  $AUTH_JSON が見つかりません"
fi
echo ""

# 4. 直近の失敗ジョブ
echo "## 4. 直近の失敗ジョブ"
STATUS_JSON=$(node "$COMPANION" status --all --json 2>&1) || true
echo "$STATUS_JSON" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    recent = d.get('recent', [])
    failed = [j for j in recent if j.get('status') == 'failed']
    if not failed:
        latest = d.get('latestFinished')
        if latest and latest.get('status') == 'failed':
            failed = [latest]
    if not failed:
        print('  失敗ジョブなし')
    else:
        for j in failed[:3]:
            print(f'  [{j.get(\"id\", \"?\")}] {j.get(\"kind\", \"?\")}')
            print(f'    error:   {j.get(\"errorMessage\", \"N/A\")}')
            print(f'    summary: {j.get(\"summary\", \"N/A\")[:80]}')
            print(f'    elapsed: {j.get(\"elapsed\", \"?\")}')
            log = j.get('logFile', '')
            if log:
                print(f'    log:     {log}')
            print()
except:
    print('  (JSON パース失敗)')
" 2>/dev/null || echo "  $STATUS_JSON"
echo ""

# 5. よくある原因と対処法
echo "## 5. よくある原因"
echo ""
echo "  | エラー | 原因 | 対処 |"
echo "  |--------|------|------|"
echo "  | Invalid request | プロジェクト未信頼 / API 変更 / モデル非対応 | codex TUI で trust 設定 / codex --version 確認 |"
echo "  | 401 Unauthorized | トークン期限切れ | codex auth で再認証 |"
echo "  | 429 Too Many Requests | レートリミット | 数分待って再実行 |"
echo "  | timeout | ネットワーク / API 応答遅延 | --timeout 延長 / ネットワーク確認 |"
echo "  | ECONNREFUSED | broker ソケット切断 | Claude Code を再起動 |"
echo ""

# 6. Codex CLI バージョン
echo "## 6. バージョン情報"
echo "  codex CLI:    $(codex --version 2>&1 || echo 'N/A')"
echo "  companion:    $COMPANION"
echo "  node:         $(node --version 2>&1)"
echo ""
echo "=== 診断完了 ==="
