# 外部プロジェクトの settings.json とスクリプト構成を最新化する計画

**作成日**: 2026-02-25
**対象**: dot-claude-dev のリファクタリングに追随する外部プロジェクトの更新

## 背景

dot-claude-dev で以下のリファクタリングを実施した:

1. `setup-claude-remote.sh` をテンプレートとして `.claude/skills/setup-project/scripts/` に移動（スリム化済み）
2. opencode セットアップを `scripts/setup-opencode.sh` として分離
3. プロジェクト固有セットアップ用の `scripts/setup-local.sh` テンプレートを新設
4. `settings.json` の SessionStart フックを 3 分割（setup-claude-remote.sh + setup-opencode.sh + setup-local.sh）
5. `PreToolUse` の suggest-compact.sh フックを削除

## 調査結果

### 対象プロジェクト

| プロジェクト | パス |
|---|---|
| ai-codlnk.com | `~/ai-codlnk.com` |
| base-ui-design | `~/base-ui-design` |
| meurai-editer | `~/meurai-editer` |
| slide_ad2 | `~/slide_ad2` |

### 各プロジェクトの現在の状態

#### ai-codlnk.com

- **settings.json**: `permissions.defaultMode: bypassPermissions` あり（固有設定）
- **SessionStart**: setup-claude-remote.sh のみ（旧構成、opencode 込み）
- **PreToolUse**: suggest-compact.sh あり（削除対象）
- **setup-claude-remote.sh**: 旧テンプレート（opencode + agent-browser 込みの大きなスクリプト）
- **プロジェクト固有セットアップ**: なし（コメントのみ）
- **setup-self-remote.sh**: なし
- **setup-opencode.sh / setup-local.sh**: なし

#### base-ui-design

- **settings.json**: `enabledPlugins` あり（固有設定: `ui-ux-pro-max@ui-ux-pro-max-skill`）
- **SessionStart**: setup-claude-remote.sh のみ（旧構成）
- **PreToolUse**: suggest-compact.sh あり（削除対象）
- **setup-claude-remote.sh**: 旧テンプレート
- **プロジェクト固有セットアップ**: **あり** — pnpm install（node_modules 未存在時）
- **setup-self-remote.sh**: なし
- **setup-opencode.sh / setup-local.sh**: なし
- **その他スクリプト**: check-lp-pages-e2e.mjs, check-lp-pages.mjs, generate-lp-styles-data.mjs, resize-lp-images.mjs（プロジェクト固有、保持必須）

#### meurai-editer

- **settings.json**: `permissions.defaultMode: bypassPermissions` あり（固有設定）
- **SessionStart**: setup-claude-remote.sh のみ、ただし `matcher: "startup"`（特殊）
- **PreToolUse**: suggest-compact.sh あり（削除対象）
- **setup-claude-remote.sh**: 旧テンプレート
- **プロジェクト固有セットアップ**: **あり（大量）** — 以下を実行:
  - `npm install`（ルート）
  - `types` パッケージのビルド（`npm install && npm run build`）
  - `frontend/editor`, `frontend/teaser`, `backend/tarot`, `backend/tzolkin`, `tests/e2e` の `npm install`
  - `git fetch origin`（リモートブランチ取得）
- **setup-self-remote.sh**: なし
- **setup-opencode.sh / setup-local.sh**: なし
- **その他スクリプト**: 多数のプロジェクト固有スクリプト（保持必須）

#### slide_ad2

- **settings.json**: 固有設定なし
- **SessionStart**: setup-claude-remote.sh のみ（旧構成）
- **PreToolUse**: suggest-compact.sh あり（削除対象）
- **setup-claude-remote.sh**: 旧テンプレート
- **プロジェクト固有セットアップ**: なし（コメントのみ）
- **setup-self-remote.sh**: なし
- **setup-opencode.sh / setup-local.sh**: なし
- **その他スクリプト**: api-server.js, compare-designs.sh, generate-sample-*.mjs（保持必須）

### リスク分析

| リスク | 影響度 | 対策 |
|---|---|---|
| base-ui-design のプロジェクト固有セットアップ消失 | 高 | setup-local.sh に移行 |
| meurai-editer のプロジェクト固有セットアップ消失 | 高 | setup-local.sh に移行（最大のカスタマイズ量） |
| settings.json の固有設定消失（permissions, enabledPlugins） | 高 | 手動マージで保持 |
| meurai-editer の matcher: "startup" の意味不明 | 低 | 空文字列 `""` に統一（動作に問題なければ） |
| 旧 suggest-compact.sh フックが残る | 低 | 削除（フック先ファイルも存在しない） |

### dot-claude-dev の最新テンプレート構成

**settings.json テンプレート** (`create-settings-json.sh` が生成):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh" }
        ]
      }
    ]
  }
}
```

**スクリプト構成**:
- `scripts/setup-claude-remote.sh` — 共通テンプレート（dot-claude-dev クローン + setup-claude.sh 実行のみ、46行）
- `scripts/setup-opencode.sh` — opencode CLI インストール + OAuth 認証復元（共通テンプレート）
- `scripts/setup-local.sh` — プロジェクト固有セットアップ（テンプレートをベースに各プロジェクトでカスタマイズ）

## 実行計画

### 全プロジェクト共通手順

各プロジェクトに対して以下の順序で実行する。

#### Step 1: setup-claude-remote.sh の置換

旧テンプレート（opencode + agent-browser 込み）を新テンプレート（共通部分のみ）に置換:

```bash
TEMPLATE_DIR="$HOME/dot-claude-dev/.claude/skills/setup-project/scripts"
cp "$TEMPLATE_DIR/setup-claude-remote.sh" "$PROJECT/scripts/setup-claude-remote.sh"
```

#### Step 2: setup-opencode.sh のコピー

```bash
cp "$HOME/dot-claude-dev/scripts/setup-opencode.sh" "$PROJECT/scripts/setup-opencode.sh"
```

#### Step 3: setup-local.sh の作成

- プロジェクト固有セットアップが**ない**場合: テンプレートをそのままコピー
- プロジェクト固有セットアップが**ある**場合: テンプレートをベースにカスタム部分を移植

```bash
TEMPLATE_DIR="$HOME/dot-claude-dev/.claude/skills/setup-project/scripts"
cp "$TEMPLATE_DIR/setup-local.sh" "$PROJECT/scripts/setup-local.sh"
# → カスタム部分がある場合は手動で追記
```

#### Step 4: settings.json の更新

既存の固有設定（permissions, enabledPlugins 等）を保持しつつ、hooks セクションを更新:
- SessionStart: 3 フック構成に変更
- PreToolUse: suggest-compact.sh を削除
- Stop: commit-check.sh を保持
- その他固有設定: そのまま保持

#### Step 5: 確認

```bash
# スクリプトの存在確認
ls -la "$PROJECT/scripts/setup-claude-remote.sh"
ls -la "$PROJECT/scripts/setup-opencode.sh"
ls -la "$PROJECT/scripts/setup-local.sh"
# settings.json の確認
cat "$PROJECT/.claude/settings.json"
```

### プロジェクト別の詳細

#### 1. ai-codlnk.com（難易度: 低）

- Step 1-2: 共通手順通り
- Step 3: テンプレートをそのままコピー（カスタム部分なし）
- Step 4: settings.json 更新
  - `permissions.defaultMode: bypassPermissions` を保持
  - SessionStart → 3 フック構成
  - PreToolUse セクション削除

**更新後の settings.json**:
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh" }
        ]
      }
    ]
  }
}
```

#### 2. base-ui-design（難易度: 中）

- Step 1-2: 共通手順通り
- Step 3: setup-local.sh にプロジェクト固有セットアップを移植
  - 移植元: 旧 setup-claude-remote.sh 末尾の「プロジェクト固有セットアップ」セクション
  - 移植内容: pnpm install（node_modules 未存在時）
- Step 4: settings.json 更新
  - `enabledPlugins` を保持
  - SessionStart → 3 フック構成
  - PreToolUse セクション削除

**setup-local.sh のカスタム部分**:
```bash
# --- Node.js 依存関係セットアップ ---
if [ -f "$CLAUDE_PROJECT_DIR/package.json" ] && [ ! -d "$CLAUDE_PROJECT_DIR/node_modules" ]; then
  if command -v pnpm &>/dev/null; then
    echo "[setup-local] node_modules missing, running pnpm install..."
    pnpm install --dir "$CLAUDE_PROJECT_DIR" 2>&1 | tail -5
    echo "[setup-local] ✓ pnpm install completed"
  else
    echo "[setup-local] WARNING: pnpm not found, skipping dependency install."
  fi
else
  echo "[setup-local] node_modules already present, skipping install."
fi
```

**更新後の settings.json**:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh" }
        ]
      }
    ]
  },
  "enabledPlugins": {
    "ui-ux-pro-max@ui-ux-pro-max-skill": true
  }
}
```

#### 3. meurai-editer（難易度: 高）

- Step 1-2: 共通手順通り
- Step 3: setup-local.sh に大量のプロジェクト固有セットアップを移植
  - 移植元: 旧 setup-claude-remote.sh 末尾
  - 移植内容: 複数サブディレクトリの npm install + types ビルド + git fetch
- Step 4: settings.json 更新
  - `permissions.defaultMode: bypassPermissions` を保持
  - SessionStart の `matcher: "startup"` → `matcher: ""` に変更（統一）
  - PreToolUse セクション削除

**setup-local.sh のカスタム部分**:
```bash
# --- 依存関係のインストール ---
echo "[setup-local] Installing dependencies..."

# ルート（concurrently等の共通devDependencies）
cd "$CLAUDE_PROJECT_DIR" && npm install
echo "[setup-local] root: installed."

# types パッケージ（テスト依存関係の前提条件）
cd "$CLAUDE_PROJECT_DIR/types" && npm install && npm run build
echo "[setup-local] types: installed and built."

# frontend/editor（テスト実行に必須）
cd "$CLAUDE_PROJECT_DIR/frontend/editor" && npm install
echo "[setup-local] frontend/editor: installed."

# frontend/teaser
cd "$CLAUDE_PROJECT_DIR/frontend/teaser" && npm install
echo "[setup-local] frontend/teaser: installed."

# backend/tarot
cd "$CLAUDE_PROJECT_DIR/backend/tarot" && npm install
echo "[setup-local] backend/tarot: installed."

# backend/tzolkin
cd "$CLAUDE_PROJECT_DIR/backend/tzolkin" && npm install
echo "[setup-local] backend/tzolkin: installed."

# tests/e2e
cd "$CLAUDE_PROJECT_DIR/tests/e2e" && npm install
echo "[setup-local] tests/e2e: installed."

# リモートブランチ取得（develop以外も含めて全ブランチ）
cd "$CLAUDE_PROJECT_DIR" && git fetch origin
echo "[setup-local] git fetch: done."
```

**更新後の settings.json**:
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh" }
        ]
      }
    ]
  }
}
```

#### 4. slide_ad2（難易度: 低）

- Step 1-2: 共通手順通り
- Step 3: テンプレートをそのままコピー（カスタム部分なし）
- Step 4: settings.json 更新
  - 固有設定なし
  - SessionStart → 3 フック構成
  - PreToolUse セクション削除

**更新後の settings.json**:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh" }
        ]
      }
    ]
  }
}
```

### 実行順序

1. **slide_ad2**（最もシンプル、リハーサルとして最適）
2. **ai-codlnk.com**（カスタムなし、permissions 保持の確認）
3. **base-ui-design**（小規模カスタム移植の確認）
4. **meurai-editer**（最大のカスタム移植、最後に実行）

### ロールバック手順

各プロジェクトはGit管理下のため、問題が発生した場合は `git checkout` で戻せる:

```bash
cd ~/PROJECT_NAME
git checkout -- scripts/setup-claude-remote.sh .claude/settings.json
git clean -f scripts/setup-opencode.sh scripts/setup-local.sh
```

## チェックリスト

- [ ] slide_ad2: スクリプト更新 + settings.json 更新
- [ ] ai-codlnk.com: スクリプト更新 + settings.json 更新（permissions 保持）
- [ ] base-ui-design: スクリプト更新 + setup-local.sh カスタマイズ + settings.json 更新（enabledPlugins 保持）
- [ ] meurai-editer: スクリプト更新 + setup-local.sh カスタマイズ + settings.json 更新（permissions 保持, matcher 統一）
