# team-plan スキル改善計画（リネーム + native 実行化 + テンプレート導入）

## 概要

`dev:team-opencode-plan` スキルを `dev:team-plan` にリネームし、計画フェーズ（ストーリー分析・タスク分解）を native 実行に変更する。opencode はタスクレビュー（Phase 0-4、Codex 固定）でのみ使用する。加えて、チーム構成テンプレートを導入し、計画フェーズの効率化を図る。

## 背景

### 現行の課題

現行の `team-opencode-plan` は全フェーズで `opencode run` を使用しており、以下の構造的課題がある:

1. **3層トークンコスト**: Lead + CC haiku + opencode 外部モデルの3層構造。計画フェーズは CC が直接実行すれば2層で済む
2. **レイテンシ**: opencode run の起動オーバーヘッドが計画フェーズに不要な遅延を生む
3. **耐障害性**: opencode の障害がストーリー分析・タスク分解という基本作業にまで波及する SPOF
4. **テンプレートの不在**: 毎回ゼロからチーム構成を設計する必要がある。feature-dev、refactor 等のよくあるパターンが再利用できない
5. **名前の不整合**: opencode を計画フェーズで使わなくなるのに `team-opencode-plan` は不適切

### 参考資料の知見

| 知見 | 出典 | 本計画での反映 |
|------|------|---------------|
| 「Teammate内Subagentは3層コスト」 | Zenn記事 | 計画フェーズの opencode 依存を排除（native 実行化） |
| 「自動化そのものより設計パターンの体系化が価値」 | Zenn記事 | テンプレート導入。AUTO 判定ではなく明示的選択 |
| 「ベストプラクティスの事前組み込みが効果的」 | Zenn記事 | テンプレートの fileOwnership で適用漏れ防止 |
| 「同一ファイル編集は気づかない上書き」 | Zenn記事 | テンプレートの fileOwnership で事前防止 |
| 「Claudeに直接言っても同等の構成を提案できる」 | Zenn記事 | テンプレートは「推奨デフォルト」。カスタムモードも必ず残す |

> 参考資料:
> - [Claude Code Agent Teams 公式ドキュメント](https://code.claude.com/docs/en/agent-teams)
> - [Agent Teams を使ってわかったチーム設計の勘所と自動化の限界](https://zenn.dev/sc30gsw/articles/4eee68a83454a2)
> - [sc30gsw/claude-code-customes team-builder](https://github.com/sc30gsw/claude-code-customes/tree/main/.claude/skills/team-builder)

---

## 現行ファイル構成

```
.claude/skills/dev/team-opencode-plan/
├── SKILL.md                              # メインスキル定義
├── references/
│   ├── role-catalog.md                   # ロール定義カタログ（変更なし）
│   ├── prompts/
│   │   ├── story-analysis.md             # ストーリー分析プロンプト（native向けに修正）
│   │   ├── task-breakdown.md             # タスク分解プロンプト（native向けに修正）
│   │   └── task-review.md               # タスクレビュープロンプト（変更なし・codex固定）
│   └── templates/
│       ├── story-analysis.template.json  # story-analysis.json雛形
│       └── task-list.template.json       # task-list.json雛形
└── scripts/
    └── init-team-workspace.sh            # ワークスペース初期化スクリプト
```

### 現行 SKILL.md のフェーズ構成

| Phase | 内容 | 実行方法 |
|-------|------|----------|
| 0-0 | ワークスペース初期化（slug選択→init-team-workspace.sh実行） | bash |
| 0-1 | opencode モデル選択（AskUserQuestion） | ユーザー選択 |
| 0-2 | ストーリー分析 → story-analysis.json | `opencode run -m $OC_MODEL` |
| 0-3 | タスク分解 → task-list.json | `opencode run -m $OC_MODEL` |
| 0-4 | タスクレビュー | `opencode run -m openai/gpt-5.3-codex`（固定） |

### 現行 story-analysis.md プロンプト（変数置換前）

```
Analyze the following story/instructions and produce a story-analysis.json.

## User Story
{user_story}

## Available Roles
{role_catalog}

## Output Format
Write the file {plan_dir}/story-analysis.json with this structure:
{
  "story": { "title": "...", "description": "..." },
  "goal": "...",
  "scope": { "included": [...], "excluded": [...] },
  "acceptanceCriteria": [...],
  "teamDesign": {
    "roles": [...],
    "waves": [...],
    "qualityGates": ["最終Waveにレビュワー配置"]
  }
}

## Rules
- The final wave MUST include a reviewer role
- Use blockedBy to express sequential dependencies between waves
- Roles within the same wave run in parallel
```

### 現行 task-breakdown.md プロンプト（要点）

- opencode にコードベース探索からタスク分解まで一貫実行させる
- タスクスキーマ: 8必須フィールド（id, name, role, description, needsPriorContext, inputs, outputs, taskPrompt）
- 禁止フィールド: title, acceptanceCriteria, context（タスクレベル）, deliverables
- Wave構造: `waves[].tasks[]` フラット配列 + `role` フィールド
- `taskPrompt` は具体的な実装指示（ファイルパス・操作内容・期待結果を含む）

### 現行 task-review.md プロンプト

```
Review this team task breakdown:
## Story Analysis
{story_analysis}
## Task List
{task_list}

Analyze:
1. Task granularity
2. Wave dependencies
3. Role assignment
4. Missing tasks
5. Risk
6. Schema compliance
7. taskPrompt quality
8. Reviewer constraint

Respond with: APPROVED or NEEDS_REVISION + recommendations
```

### 現行 init-team-workspace.sh の出力パス

```bash
WORKSPACE="docs/features/team-opencode/${DATE}_${SLUG}"
```

### team-opencode-exec の関連箇所

exec スキル（`.claude/skills/dev/team-opencode-exec/SKILL.md`）の以下の箇所が plan スキルを参照している:

- 概要文: 「`dev:team-opencode-plan` が生成した承認済み task-list.json を入力として」
- 計画入力元: `docs/features/team-opencode/{YYMMDD}_{slug}/`
- 計画選択 UI: `docs/features/team-opencode/` 以下のディレクトリを列挙
- 計画0件時の案内: 「先に `dev:team-opencode-plan` を実行して計画を作成してください」

### CLAUDE.md の関連箇所

- スキル一覧テーブル「チーム実行（Agent Teams + opencode）」セクション
- コマンド一覧テーブルの `/dev:team-opencode-plan`

---

## 変更内容

### 1. リネーム（全箇所統一）

| 対象 | 現在 | 変更後 |
|------|------|--------|
| スキルディレクトリ | `.claude/skills/dev/team-opencode-plan/` | `.claude/skills/dev/team-plan/` |
| スキル名（frontmatter） | `dev:team-opencode-plan` | `dev:team-plan` |
| トリガー | `dev:team-opencode-plan, /dev:team-opencode-plan, チーム計画` | `dev:team-plan, /dev:team-plan, チーム計画, team plan` |
| 計画出力先 | `docs/features/team-opencode/{YYMMDD}_{slug}/` | `docs/features/team/{YYMMDD}_{slug}/` |
| 初期化スクリプト内パス | `docs/features/team-opencode/` | `docs/features/team/` |

### 2. フェーズ構成の変更

| Phase | 現行 | 変更後 | 備考 |
|-------|------|--------|------|
| 0-0 | ワークスペース初期化 | ワークスペース初期化 | 出力パス変更のみ |
| 0-1 | opencode モデル選択 | **テンプレート選択** | AskUserQuestion でチーム構成テンプレートを選択 |
| 0-2 | ストーリー分析（opencode run） | ストーリー分析（**native 実行**） | テンプレートをヒントに、Claude Code が Glob/Grep/Read/Write で直接実行 |
| 0-3 | タスク分解（opencode run） | タスク分解（**native 実行**） | Claude Code が Glob/Grep/Read/Write で直接実行 |
| 0-4 | タスクレビュー（opencode codex 固定） | タスクレビュー（**変更なし**） | opencode run -m openai/gpt-5.3-codex 固定を維持 |

### 3. テンプレート導入

#### テンプレートファイル構成

```
references/team-templates/
├── feature-dev.json       # 機能開発（designer + developer + reviewer）
├── refactor.json          # リファクタリング（architect + developer + tester）
├── investigation.json     # 調査・バグ調査（researcher x3 競合仮説）
├── tdd-focused.json       # TDD重視（tdd-developer + reviewer）
└── frontend-only.json     # フロントエンド（designer + frontend-dev + reviewer）
```

#### テンプレートスキーマ

```json
{
  "name": "feature-dev",
  "description": "標準的な機能開発（設計→実装→レビュー）",
  "waves": [
    {
      "id": 1,
      "roles": ["designer"],
      "purpose": "UI/UX設計、デザイントークン定義"
    },
    {
      "id": 2,
      "roles": ["frontend-developer", "backend-developer"],
      "purpose": "並列実装",
      "blockedBy": [1]
    },
    {
      "id": 3,
      "roles": ["reviewer"],
      "purpose": "品質レビュー",
      "blockedBy": [2]
    }
  ],
  "fileOwnership": {
    "designer": ["src/styles/**", "src/design/**"],
    "frontend-developer": ["src/components/**", "src/pages/**"],
    "backend-developer": ["src/api/**", "src/services/**"],
    "reviewer": []
  }
}
```

#### Phase 0-1 での利用フロー

```
AskUserQuestion:
Q: チーム構成テンプレートを選択してください。
選択肢:
- feature-dev（推奨）: 設計→実装→レビューの3Wave構成
- refactor: 設計→実装→テストの3Wave構成
- investigation: researcher×3の競合仮説調査
- tdd-focused: TDD開発→レビュー
- frontend-only: デザイン→フロント実装→レビュー
- カスタム: テンプレートなしでゼロから設計
```

- テンプレート選択時: そのロール構成・Wave構造・ファイル所有権をストーリー分析のヒントとして渡す。テンプレートは強制ではなく推奨デフォルト
- カスタム選択時: 従来通りゼロからチーム構成を設計

### 4. プロンプトテンプレートの変更方針

#### story-analysis.md → native 実行向けに修正

- opencode 向けの指示構造を、Claude Code が直接実行する**手順書**に変換
- 変数置換テーブルは維持 + `{template}` 変数を追加（テンプレート選択結果）
- コードベース探索指示を追加（native ではリーダーが Glob/Grep/Read で明示的に探索）
- 出力先（`$PLAN_DIR/story-analysis.json`）は同一

#### task-breakdown.md → native 実行向けに修正

- 「Explore the codebase」を Glob/Grep/Read での明示的探索手順に変更
- `taskPrompt` フィールドは**維持**（exec フェーズで opencode が使用するため）
- `{designSystemRefs}` をリーダー自身が DESIGN.md やデザイントークンファイルから Read で取得する手順に変更

#### task-review.md → 変更なし

引き続き `opencode run -m openai/gpt-5.3-codex` で使用。

### 5. SKILL.md の主要な変更

- frontmatter: name → `dev:team-plan`、description・trigger 更新
- 「必須リソース」テーブル: `references/team-templates/*.json` を追加、用途列の「opencode用プロンプト」→「手順書」
- Phase 0-1: opencode モデル選択 → テンプレート選択に完全置換
- Phase 0-2: ストーリー分析を native 実行に変更
  - プロンプトテンプレートを Read で読み込み、変数置換
  - `opencode run` → Claude Code が自身のツールで直接実行
  - コードベース探索を Glob/Grep/Read で実施
  - story-analysis.json を Write で出力
- Phase 0-3: タスク分解を native 実行に変更（同上パターン）
- Phase 0-4: 変更なし（opencode codex 固定を維持）
- `$OC_MODEL` 変数の参照をすべて削除（Phase 0-4 は codex 固定を直接記述）
- 「重要な注意事項」セクション:
  - 「opencode コマンドは決め打ち」→ Phase 0-4 のみに限定
  - 「フォールバック禁止」→ Phase 0-4 のみに限定
  - 「計画もopencode活用」→ 「計画は native 実行、レビューのみ opencode 活用」
  - Phase順序: 0-0 → 0-1 → 0-2 → 0-3 → 0-4

### 6. init-team-workspace.sh

```diff
-WORKSPACE="docs/features/team-opencode/${DATE}_${SLUG}"
+WORKSPACE="docs/features/team/${DATE}_${SLUG}"
```

### 7. team-opencode-exec への影響対応

| 箇所 | 変更内容 |
|------|----------|
| 概要文 | `dev:team-opencode-plan` → `dev:team-plan` |
| 計画入力元パス | `docs/features/team-opencode/` → `docs/features/team/` |
| 計画選択 UI のディレクトリ | `docs/features/team-opencode/` → `docs/features/team/` |
| 計画0件時の案内 | `dev:team-opencode-plan` → `dev:team-plan` |

### 8. CLAUDE.md の更新

- スキル一覧テーブル: `dev:team-opencode-plan` → `dev:team-plan`、説明文を更新
- コマンド一覧テーブル: `/dev:team-opencode-plan` → `/dev:team-plan`

---

## タスクリスト

### Phase 1: ディレクトリ・ファイルリネーム
> ファイルシステム上の移動を先に実施し、以降の変更はすべて新パスで行う。

- [ ] `git mv .claude/skills/dev/team-opencode-plan .claude/skills/dev/team-plan`
- [ ] 既存の `docs/features/team-opencode/` の有無を確認し、移行方針を決定

### Phase 2: init-team-workspace.sh 修正

- [ ] `WORKSPACE` の値を `docs/features/team/${DATE}_${SLUG}` に変更
- [ ] 動作確認（`bash .claude/skills/dev/team-plan/scripts/init-team-workspace.sh test-slug` で `docs/features/team/` にディレクトリが作成されることを確認）
- [ ] テスト用に作成したディレクトリを削除

### Phase 3: プロンプトテンプレート修正

- [ ] `references/prompts/story-analysis.md` を native 実行向けに修正
  - opencode 用の指示構造を、Claude Code が直接実行する手順書に変換
  - 変数置換テーブルに `{template}` を追加
  - コードベース探索の具体的手順（Glob/Grep/Read）を追加
- [ ] `references/prompts/task-breakdown.md` を native 実行向けに修正
  - 「Explore the codebase」を Glob/Grep/Read での明示的探索手順に変更
  - `taskPrompt` フィールドは維持（exec 用）
  - `{designSystemRefs}` 取得手順をリーダー自身の Read 操作に変更

### Phase 4: チーム構成テンプレート作成

- [ ] `references/team-templates/` ディレクトリ作成
- [ ] `feature-dev.json` 作成（designer + frontend/backend-developer + reviewer、3Wave構成）
- [ ] `refactor.json` 作成（architect + developer + tester、3Wave構成）
- [ ] `investigation.json` 作成（researcher x3 競合仮説、1Wave構成）
- [ ] `tdd-focused.json` 作成（tdd-developer + reviewer、2Wave構成）
- [ ] `frontend-only.json` 作成（designer + frontend-dev + reviewer、3Wave構成）

### Phase 5: SKILL.md 書き換え

- [ ] frontmatter 更新（name: `dev:team-plan`、description、trigger）
- [ ] 「必須リソース」テーブル更新（`references/team-templates/*.json` 追加、用途列更新）
- [ ] Phase 0-1: opencode モデル選択 → テンプレート選択に完全置換
- [ ] Phase 0-2: ストーリー分析を native 実行に変更（opencode run → Glob/Grep/Read/Write）
- [ ] Phase 0-3: タスク分解を native 実行に変更（同上パターン）
- [ ] Phase 0-4: 変更なし（番号維持、opencode codex 固定維持）
- [ ] `$OC_MODEL` 変数の参照をすべて削除
- [ ] 「重要な注意事項」セクション更新
- [ ] 「計画出力先」のパスを `docs/features/team/` に更新

### Phase 6: team-opencode-exec への影響対応

- [ ] exec SKILL.md の概要文: `dev:team-opencode-plan` → `dev:team-plan`
- [ ] exec SKILL.md の計画入力元パス: `docs/features/team-opencode/` → `docs/features/team/`
- [ ] exec SKILL.md の計画選択 UI ディレクトリ: `docs/features/team-opencode/` → `docs/features/team/`
- [ ] exec SKILL.md の計画0件時の案内: `dev:team-opencode-plan` → `dev:team-plan`

### Phase 7: CLAUDE.md 更新

- [ ] スキル一覧「チーム実行」セクション: `dev:team-opencode-plan` → `dev:team-plan`、説明文を更新
- [ ] コマンド一覧: `/dev:team-opencode-plan` → `/dev:team-plan`、説明文を更新
- [ ] exec スキルの説明文から `team-opencode-plan` への参照を `team-plan` に更新

### Phase 8: テンプレート JSON 微修正

- [ ] `task-list.template.json` の `metadata.ocModel` フィールドは維持（exec 起動時にユーザーが選択する値のプレースホルダ）

### Phase 9: 検証

- [ ] `.claude/skills/dev/team-plan/` 以下の全ファイルが正しく配置されていることを Glob で確認
- [ ] SKILL.md 内の相対パス参照（`references/...`, `scripts/...`）が正しいことを確認
- [ ] `init-team-workspace.sh` を実行して `docs/features/team/` に作成されることを確認
- [ ] `references/team-templates/` に5つのテンプレート JSON が正しいスキーマで配置されていることを確認
- [ ] CLAUDE.md のスキル一覧・コマンド一覧に不整合がないことを確認
- [ ] exec SKILL.md 内で `team-plan` への参照が正しいことを確認
- [ ] コードベース全体で `team-opencode-plan` の残存参照がないことを Grep で確認
