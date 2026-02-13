# team-opencode スキル分割計画書

## タスク概要

現在の `dev:team-opencode` スキル（SKILL.md 356行、Phase 0-3 を1スキルに同居）を以下の2スキルに分割する:

- **`dev:team-opencode-plan`** -- Phase 0: Planning（ストーリー分析、タスク分解、レビュー、ユーザー承認）
- **`dev:team-opencode-exec`** -- Phase 1-3: Execution / Feedback / Cleanup（チーム実行、レビューフィードバック、クリーンアップ）

### 分割の動機

1. 複数ストーリーの計画を並行作成したい（現状 `init-team-workspace.sh` が毎回クリーンするため1計画しか保持できない）
2. 計画フェーズと実行フェーズの責務分離による見通しの改善
3. 計画だけ先に複数作成し、後から選択して実行するワークフローの実現

---

## 現状分析

### ファイル構成

```
.claude/skills/dev/team-opencode/
├── SKILL.md                                    # 356行 Phase 0-3 全部入り
├── references/
│   ├── role-catalog.md                         # 158行 11ロール定義
│   ├── agent-prompt-template.md                # 87行 エージェントプロンプトテンプレート
│   ├── prompts/
│   │   ├── story-analysis.md                   # Phase 0-2 用 opencode prompt
│   │   ├── task-breakdown.md                   # Phase 0-3 用 opencode prompt
│   │   └── task-review.md                      # Phase 0-4 用 opencode prompt
│   └── templates/
│       ├── story-analysis.template.json        # story-analysis.json 雛形
│       └── task-list.template.json             # task-list.json 雛形
└── scripts/
    └── init-team-workspace.sh                  # 16行 ワークスペース初期化（全消し）
```

### ワークスペース出力先（現状）

```
docs/features/team-opencode/
├── story-analysis.json
├── task-list.json
└── prompts/                 # 各ロールの opencode 実行プロンプト（自動生成）
```

問題: `init-team-workspace.sh` が `rm -rf` で毎回消すため、過去の計画が残らない。

### リソース参照関係

| リソース                       | plan で使う | exec で使う |
| ------------------------------ | :---------: | :---------: |
| `role-catalog.md`              |   Phase 0-2（ストーリー分析でロール設計）   |   Phase 1-3（エージェントプロンプト構築で role_directive 取得）   |
| `agent-prompt-template.md`     |      -      |   Phase 1-3   |
| `prompts/story-analysis.md`    |   Phase 0-2   |      -      |
| `prompts/task-breakdown.md`    |   Phase 0-3   |      -      |
| `prompts/task-review.md`       |   Phase 0-4   |      -      |
| `templates/*.template.json`    |   Phase 0-0   |      -      |
| `init-team-workspace.sh`       |   Phase 0-0   |      -      |

**結論**: `role-catalog.md` のみ両方で必要。その他はどちらか一方でのみ使用。

---

## 分割後のディレクトリ構成

```
.claude/skills/dev/
├── team-opencode-plan/
│   ├── SKILL.md                                 # Phase 0 のみ（~120行見込み）
│   ├── references/
│   │   ├── role-catalog.md                      # 共有: コピーではなくシンボリックリンク
│   │   ├── prompts/
│   │   │   ├── story-analysis.md
│   │   │   ├── task-breakdown.md
│   │   │   └── task-review.md
│   │   └── templates/
│   │       ├── story-analysis.template.json
│   │       └── task-list.template.json
│   └── scripts/
│       └── init-team-workspace.sh               # slug 対応に改修
│
├── team-opencode-exec/
│   ├── SKILL.md                                 # Phase 1-3 のみ（~250行見込み）
│   └── references/
│       ├── role-catalog.md                      # 共有: シンボリックリンク元（実体を保持）
│       └── agent-prompt-template.md
│
└── team-opencode/                               # 廃止（移行完了後に削除）
```

### role-catalog.md の共有方針

`role-catalog.md` は exec 側に実体を配置し、plan 側からシンボリックリンクで参照する。

```bash
# exec 側に実体
.claude/skills/dev/team-opencode-exec/references/role-catalog.md  # 実体

# plan 側からシンボリックリンク
.claude/skills/dev/team-opencode-plan/references/role-catalog.md
  -> ../team-opencode-exec/references/role-catalog.md
```

理由:
- exec 側の方が使用頻度が高い（エージェントスポーン毎に参照）
- plan 側は opencode プロンプトに埋め込むために1回だけ読む

代替案: 両方にコピーを配置する（同期の手間は増えるがシンプル）。シンボリックリンクが git で問題を起こす場合はこちらを採用。

### ワークスペース出力先（変更後）

```
docs/features/team-opencode/
├── 260213_login-feature/            # {YYMMDD}_{slug} 形式
│   ├── story-analysis.json
│   ├── task-list.json
│   └── prompts/
├── 260214_dashboard-redesign/
│   ├── story-analysis.json
│   ├── task-list.json
│   └── prompts/
└── ...
```

命名規則: `{YYMMDD}_{slug}`
- YYMMDD: 作成日（2桁年+月+日）
- slug: ストーリータイトルを kebab-case 化（英数字+ハイフン、最大40文字）
- dev:story の命名規則と統一

---

## 各スキルの責務

### dev:team-opencode-plan

**目的**: ストーリー/指示を受け取り、opencode を活用してチーム実行計画（task-list.json）を生成し、ユーザー承認まで行う。

**ステップ**:

| Step | 内容 | 詳細 |
| ---- | ---- | ---- |
| 0-0 | ワークスペース初期化 | slug 生成、`docs/features/team-opencode/{YYMMDD}_{slug}/` を作成 |
| 0-1 | opencode モデル選択 | AskUserQuestion でモデル確認 |
| 0-2 | ストーリー分析 | role-catalog.md + story-analysis.md で opencode 実行 |
| 0-3 | コード探索 & タスク分解 | コンテキスト収集 + task-breakdown.md で opencode 実行 |
| 0-4 | タスクレビュー | task-review.md で opencode 実行（gpt-5.3-codex 固定） |
| 0-5 | ユーザー承認 | 計画を提示、承認 or 修正 |

**出力**: `docs/features/team-opencode/{YYMMDD}_{slug}/task-list.json`（承認済み）

**allowed-tools**:
- Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion

**frontmatter 抜粋**:

```yaml
name: dev:team-opencode-plan
description: |
  opencode活用のチーム実装計画を作成。ストーリー分析→タスク分解→レビュー→ユーザー承認。
  計画は docs/features/team-opencode/{YYMMDD}_{slug}/ に永続化される。

  Trigger:
  dev:team-opencode-plan, /dev:team-opencode-plan, チーム計画, team plan
```

---

### dev:team-opencode-exec

**目的**: plan が生成した承認済み task-list.json を入力として、Agent Teams でチーム実行し、レビューフィードバック後にクリーンアップする。

**ステップ**:

| Phase | Step | 内容 |
| ----- | ---- | ---- |
| (前提) | - | 計画選択 UI: 既存計画一覧 → ユーザー選択 |
| 1 | 1-0 | opencode モデル確認（plan 時と変更する場合のみ） |
| 1 | 1-1 | チーム作成（TeamCreate） |
| 1 | 1-2 | タスク登録（TaskCreate） |
| 1 | 1-3 | Wave N エージェントスポーン |
| 1 | 1-4 | 完了待機 |
| 1 | 1-5 | 次 Wave スポーン（ループ） |
| 2 | 2-1 | レビュワー報告受信 |
| 2 | 2-2 | ユーザーへ提示 |
| 2 | 2-3 | フィードバック分岐（対応あり → plan に戻すか exec 内で修正） |
| 3 | 3-1 | 結果集約 |
| 3 | 3-2 | シャットダウン |
| 3 | 3-3 | TeamDelete |

**入力**: `docs/features/team-opencode/{YYMMDD}_{slug}/task-list.json`

**allowed-tools**:
- Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
- Task, TaskCreate, TaskList, TaskGet, TaskUpdate
- TeamCreate, TeamDelete, SendMessage

**frontmatter 抜粋**:

```yaml
name: dev:team-opencode-exec
description: |
  承認済みのteam-opencode計画（task-list.json）をAgent Teamsで並行実行。
  Wave式チーム実行→レビューフィードバック→クリーンアップ。

  Trigger:
  dev:team-opencode-exec, /dev:team-opencode-exec, チーム実行, team exec
```

---

## インターフェース設計

### plan → exec 間のデータ受け渡し

**契約**: plan は `docs/features/team-opencode/{YYMMDD}_{slug}/` に以下のファイルを生成し、exec はそこから読み取る。

```
docs/features/team-opencode/{YYMMDD}_{slug}/
├── story-analysis.json     # ストーリー分析結果（チーム設計、ロール定義含む）
├── task-list.json           # タスク定義（waves/roles 形式、承認済み）
└── prompts/                 # 各ロールの opencode 実行プロンプト（任意）
```

### 計画選択 UI（exec 起動時）

exec 起動時に、既存の計画ディレクトリを一覧表示し、ユーザーに選択させる。

```
1. docs/features/team-opencode/ 以下のディレクトリを ls で列挙
2. 各ディレクトリの task-list.json を Read し、metadata を表示
3. AskUserQuestion で選択:

Q: 実行する計画を選択してください。

【計画一覧】
1. 260213_login-feature (5タスク / 3 Wave)
2. 260214_dashboard-redesign (8タスク / 4 Wave)

選択肢:
- 1
- 2
- パスを直接指定
```

選択後、`task-list.json` のパスを `$PLAN_DIR` として保持し、以降の Phase 1-3 で使用する。

### task-list.json のフォーマット（変更なし）

exec は plan が生成した waves/roles 形式の task-list.json のみ受け付ける。dev:story が生成する workflow 形式（tdd/e2e/task ラベル付き）には非対応。

```json
{
  "context": { ... },
  "waves": [
    {
      "id": 1,
      "roles": {
        "ロール名": [
          {
            "id": "task-1-1",
            "name": "タスク名",
            "description": "...",
            "needsPriorContext": false,
            "inputs": [],
            "outputs": [],
            "opencodePrompt": "..."
          }
        ]
      }
    }
  ],
  "metadata": { "totalTasks": 0, "totalWaves": 0, "roles": [] }
}
```

### opencode モデルの受け渡し

plan 側で選択したモデルを task-list.json の metadata に保存する:

```json
{
  "metadata": {
    "totalTasks": 5,
    "totalWaves": 3,
    "roles": ["frontend-developer", "reviewer"],
    "ocModel": "openai/gpt-5.3-codex"
  }
}
```

exec 側は起動時に `metadata.ocModel` を読み取り、`$OC_MODEL` として使用する。ユーザーが変更を希望する場合のみ AskUserQuestion で再選択。

---

## 改修内容の詳細

### 1. init-team-workspace.sh の改修（slug 化対応）

**現状**: 固定パスにクリーンアップ & テンプレートコピー

```bash
WORKSPACE="docs/features/team-opencode"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE/prompts"
```

**改修後**: 引数で slug を受け取り、日付付きディレクトリを作成

```bash
#!/usr/bin/env bash
set -euo pipefail

# 引数チェック
if [ $# -lt 1 ]; then
  echo "Usage: $0 <slug>" >&2
  echo "Example: $0 login-feature" >&2
  exit 1
fi

SLUG="$1"
DATE=$(date +%y%m%d)
WORKSPACE="docs/features/team-opencode/${DATE}_${SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# 既存チェック（同名ディレクトリがあれば警告）
if [ -d "$WORKSPACE" ]; then
  echo "WARNING: $WORKSPACE already exists. Files will be overwritten." >&2
fi

# ディレクトリ作成（クリーンアップしない）
mkdir -p "$WORKSPACE/prompts"

# テンプレート雛形を配置
cp "$TEMPLATES_DIR/story-analysis.template.json" "$WORKSPACE/story-analysis.json"
cp "$TEMPLATES_DIR/task-list.template.json"      "$WORKSPACE/task-list.json"

echo "$WORKSPACE"
```

変更点:
- `rm -rf` を削除（既存計画を破壊しない）
- 引数で slug を受け取る
- 日付プレフィックス `YYMMDD_` を自動付与
- 作成したパスを stdout に出力（呼び出し元で `$PLAN_DIR` としてキャプチャ）
- 同名ディレクトリが存在する場合は警告のみ（上書き可能）

### 2. SKILL.md（plan 側）の作成

現在の SKILL.md から Phase 0（58-145行目）を抽出し、以下を追加/変更:

- frontmatter の name, description, allowed-tools を更新
- Task ツール群（TaskCreate, TaskList 等）を削除（plan では不要）
- TeamCreate, TeamDelete, SendMessage を削除
- ワークスペースパスを `{YYMMDD}_{slug}` 形式に変更
- Step 0-0 で slug 生成ロジックを追加:
  - ユーザーにストーリーを聞く
  - ストーリータイトルから slug を生成（英数字+ハイフン、最大40文字）
  - `init-team-workspace.sh` に slug を渡す
- metadata に `ocModel` フィールドを追加する指示を 0-5 に追加
- 必須リソーステーブルから exec 専用リソースを削除
- 「一時計画フォルダ」セクションのパスを更新

### 3. SKILL.md（exec 側）の作成

現在の SKILL.md から Phase 1-3（148-356行目）を抽出し、以下を追加/変更:

- frontmatter の name, description, allowed-tools を更新
- Read, Write 等の基本ツールに加え、Task/Team ツール群を含める
- 計画選択 UI を Phase 1 の前に追加（上記「計画選択 UI」セクション参照）
- `$PLAN_DIR` 変数を使用してファイルパスを参照するよう全箇所を更新
- `docs/features/team-opencode/story-analysis.json` → `$PLAN_DIR/story-analysis.json`
- `docs/features/team-opencode/task-list.json` → `$PLAN_DIR/task-list.json`
- opencode プロンプト系リソースへの参照を削除
- 必須リソーステーブルを更新（agent-prompt-template.md + role-catalog.md のみ）
- Phase 2-3 のフィードバック分岐で「対応あり → plan に戻る」旨を明記（exec 単体では計画を再生成しない）
- エラーハンドリング、Wave完了ゲート、タスク完了定義、重要な注意事項はそのまま移植

### 4. task-list.template.json の更新

metadata に `ocModel` フィールドを追加:

```json
{
  "context": { ... },
  "waves": [],
  "metadata": {
    "totalTasks": 0,
    "totalWaves": 0,
    "roles": [],
    "ocModel": ""
  }
}
```

### 5. opencode プロンプト内のパス更新

`story-analysis.md`, `task-breakdown.md`, `task-review.md` 内のファイル出力パスを変数化:

現状:
```
Write the file docs/features/team-opencode/story-analysis.json with this structure:
```

変更後:
```
Write the file {plan_dir}/story-analysis.json with this structure:
```

plan 側 SKILL.md の変数置換で `{plan_dir}` を実際のパス（`docs/features/team-opencode/260213_login-feature`）に置換する。

### 6. CLAUDE.md のスキル一覧更新

CLAUDE.md の「利用可能なスキル」テーブルから `dev:team-opencode` を削除し、以下の2行を追加:

| スキル | 用途 |
| ------ | ---- |
| **dev:team-opencode-plan** | ストーリーからチーム実行計画を作成。opencode でストーリー分析・タスク分解・レビュー。計画は永続化され複数保持可能。 |
| **dev:team-opencode-exec** | 承認済み計画をAgent Teamsで並行実行。Wave式実行→レビューフィードバック→クリーンアップ。 |

コマンドテーブルも同様に更新。

---

## 実行ステップ

### Phase A: 準備

- [ ] A-1: 現在の `team-opencode/SKILL.md` を最終確認（変更がないことを確認）
- [ ] A-2: `docs/features/team-opencode/` が空または不要であることを確認

### Phase B: ディレクトリ構造の作成

- [ ] B-1: `team-opencode-plan/` ディレクトリを作成
- [ ] B-2: `team-opencode-exec/` ディレクトリを作成
- [ ] B-3: `team-opencode-plan/references/` ディレクトリを作成
- [ ] B-4: `team-opencode-plan/references/prompts/` ディレクトリを作成
- [ ] B-5: `team-opencode-plan/references/templates/` ディレクトリを作成
- [ ] B-6: `team-opencode-plan/scripts/` ディレクトリを作成
- [ ] B-7: `team-opencode-exec/references/` ディレクトリを作成

### Phase C: リソースファイルの移動・配置

- [ ] C-1: `role-catalog.md` を `team-opencode-exec/references/` にコピー（実体）
- [ ] C-2: `role-catalog.md` を `team-opencode-plan/references/` にシンボリックリンク作成（`../team-opencode-exec/references/role-catalog.md`）
- [ ] C-3: `agent-prompt-template.md` を `team-opencode-exec/references/` に移動
- [ ] C-4: `prompts/story-analysis.md` を `team-opencode-plan/references/prompts/` に移動
- [ ] C-5: `prompts/task-breakdown.md` を `team-opencode-plan/references/prompts/` に移動
- [ ] C-6: `prompts/task-review.md` を `team-opencode-plan/references/prompts/` に移動
- [ ] C-7: `templates/story-analysis.template.json` を `team-opencode-plan/references/templates/` に移動
- [ ] C-8: `templates/task-list.template.json` を `team-opencode-plan/references/templates/` に移動（metadata に ocModel 追加）
- [ ] C-9: `init-team-workspace.sh` を `team-opencode-plan/scripts/` に移動（改修版）

### Phase D: SKILL.md の作成

- [ ] D-1: `team-opencode-plan/SKILL.md` を作成（Phase 0 抽出 + slug 対応 + metadata.ocModel）
- [ ] D-2: `team-opencode-exec/SKILL.md` を作成（Phase 1-3 抽出 + 計画選択 UI + $PLAN_DIR パス化）
- [ ] D-3: opencode プロンプト内のパスを `{plan_dir}` 変数に更新

### Phase E: 動作確認

- [ ] E-1: `init-team-workspace.sh` に slug を渡して正しいディレクトリが作成されることを確認
- [ ] E-2: シンボリックリンクが正しく解決されることを確認（`cat team-opencode-plan/references/role-catalog.md`）
- [ ] E-3: plan SKILL.md の必須リソーステーブルのパスがすべて存在することを確認
- [ ] E-4: exec SKILL.md の必須リソーステーブルのパスがすべて存在することを確認

### Phase F: ドキュメント更新

- [ ] F-1: `CLAUDE.md` のスキル一覧を更新
- [ ] F-2: `CLAUDE.md` のコマンドテーブルを更新
- [ ] F-3: MEMORY.md にスキル分割の決定を記録

### Phase G: クリーンアップ

- [ ] G-1: 旧 `team-opencode/` ディレクトリを削除
- [ ] G-2: 最終動作確認（plan → exec の一連のフローを手動テスト）
- [ ] G-3: コミット

---

## リスクと対策

| リスク | 影響度 | 対策 |
| ------ | :----: | ---- |
| シンボリックリンクが Git で正しく追跡されない | 中 | Git はシンボリックリンクをデフォルトでリンクとして追跡する（`core.symlinks=true`）。問題が出た場合はコピー方式にフォールバック |
| plan と exec で role-catalog.md の内容がずれる | 低 | シンボリックリンクなら実体は1つなので不整合は起きない。コピー方式の場合は更新時に両方を修正するルールを CLAUDE.md に追記 |
| 既存の計画ディレクトリが蓄積してディスクを圧迫 | 低 | 計画ファイルは JSON テキストのみで小さい。必要に応じて古い計画を手動削除。自動クリーンアップは実装しない |
| exec 起動時に計画が0件でエラー | 低 | 計画一覧が空の場合は「先に dev:team-opencode-plan を実行してください」とガイド |
| Phase 2-3 のフィードバック分岐で plan への戻りが煩雑 | 中 | exec から plan を呼び出すのではなく、ユーザーに「plan を再実行してから exec を再実行してください」と案内する。exec 内での計画再生成は行わない |
| 旧 SKILL.md を参照するユーザーの混乱 | 低 | 旧ディレクトリを完全削除し、CLAUDE.md のスキル一覧を更新して明示。トリガーワード `dev:team-opencode` は plan 側の description に含めて互換性を維持 |
| slug の衝突（同日に同名ストーリー） | 低 | `init-team-workspace.sh` で既存ディレクトリを検出した場合は警告を出す。上書きは許可するが、ユーザーに通知する |
| opencode プロンプトの `{plan_dir}` 変数置換漏れ | 中 | plan SKILL.md の Step 0-2, 0-3, 0-4 の各ステップで変数一覧テーブルに `{plan_dir}` を明記し、置換漏れを防ぐ |

---

## 補足: 旧 dev:team-opencode トリガーの互換性

ユーザーが `/dev:team-opencode` と入力した場合の振る舞い:

- plan 側の SKILL.md の description に `dev:team-opencode` をトリガーワードとして含める
- plan が起動し、計画作成フローが始まる
- 計画承認後、ユーザーに `dev:team-opencode-exec を実行してください` と案内する

これにより、旧コマンドでも計画フェーズから自然に開始できる。
