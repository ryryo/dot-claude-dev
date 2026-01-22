# ストーリー駆動開発 Big 3 スキル構築計画

## 概要

カムイウェビナーの「Big 3スキル + フェーズ分割」アプローチを、dotfiles/claude/の既存スキル構造をベースに実装する。

## 確定事項

実装前に確定した設計判断。

### slug決定方法

**AskUserQuestionツールで複数候補を提示**

```
ストーリー受領
    ↓
[analyze-story.md] ストーリー分析
    ↓
AskUserQuestion({
  questions: [
    {
      question: "feature-slugを選択してください",
      header: "Feature",
      options: [
        { label: "user-auth", description: "ユーザー認証機能" },
        { label: "dashboard", description: "ダッシュボード機能" },
        { label: "settings", description: "設定機能" }
      ],
      multiSelect: false
    },
    {
      question: "story-slugを選択してください",
      header: "Story",
      options: [
        { label: "login-form", description: "ログインフォーム実装" },
        { label: "validation", description: "バリデーション追加" },
        { label: "error-handling", description: "エラーハンドリング" }
      ],
      multiSelect: false
    }
  ]
})
    ↓
ユーザー: 選択 or 「その他」で独自入力
    ↓
slug確定 → 以降の処理で使用
```

**ポイント**:
- ストーリー分析結果から適切な候補を自動生成
- 既存のfeature-slugがあれば優先的に提示
- 「その他」で自由入力も可能

### 既存スキル活用

| 参照元 | 用途 | 備考 |
|--------|------|------|
| `docs/SAMPLE/dev/dotfiles/claude/commands/impl.md` | TDDフローのベース | PLANフロー用は別途作成 |
| `docs/SAMPLE/dev/dotfiles/claude/skills/analyzing-requirements/references/design-template.md` | DESIGN.mdテンプレート | PLANセクション追加が必要 |
| `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/` | skill-creator | そのままコピー＋パス修正 |

### 呼び出しインターフェース

**コマンド形式**で統一:

| コマンド | 呼び出しスキル | 引数 |
|----------|---------------|------|
| `/dev:story` | story-to-tasks | ストーリー説明（任意） |
| `/dev:feedback` | feedback | feature-slug, story-slug（任意） |

### 言語別ルール

**全言語同時作成**:
- TypeScript / React
- JavaScript
- PHP
- Python
- HTML / CSS

### agent-browser検証方式

**MCP版 agent-browser（Claude in Chrome）による操作フロー検証**:
- 実際にクリック・入力操作を実行
- UIの動作を検証（表示確認だけでなく操作確認）
- 期待する動作と実際の動作を比較

→ 詳細: [PLANサイクル](reference/plan-cycle.md)

### 統合テスト

**シンプルなサンプルストーリーを用意**:
- 例: 「ログインフォームを作成する」
- TDDタスク（バリデーションロジック）とPLANタスク（UI）の両方を含む

## Big 3 スキルの設計

| Big 3 名称 | 役割 | スキル名 |
|------------|------|----------|
| タスク仕様書作成 | ストーリー → TODO.md（TDD/E2E/TASK分岐付き） | dev:story-to-tasks |
| 実装 | TDD or E2E or TASKフローで実装 | dev:developing（既存活用） |
| フィードバック | 実装結果 → DESIGN.md蓄積＋スキル自己改善 | dev:feedback |

### Big 3 の循環フロー

```
ストーリー → タスク生成 → 実装 → フィードバック
                                      │
                                      ↓
                              システム仕様書（DESIGN.md）
                              （実装から学んだことを蓄積）
```

**ポイント**: 仕様書は最初に作るのではなく、**実装後のフィードバックで徐々に蓄積・更新**される。

### 出力ファイル構造

複数のストーリーが機能/フェーズ単位のDESIGN.mdに収束し、さらに総合設計に統合される。

```
docs/
├── features/
│   ├── DESIGN.md                      # 総合設計（全機能を俯瞰）
│   │
│   ├── {feature-slug}/                # 機能/フェーズ単位
│   │   ├── DESIGN.md                  # 機能別設計（複数ストーリーから蓄積）
│   │   ├── output/                    # 機能全体の成果物
│   │   └── stories/
│   │       └── {story-slug}/          # ストーリー単位
│   │           ├── story-analysis.json  # analyze-story.mdの出力
│   │           ├── task-list.json       # decompose-tasks.mdの出力
│   │           ├── TODO.md              # assign-workflow.mdの出力
│   │           └── output/              # ストーリーの成果物
│   │
│   └── user-auth/                     # 例: user-auth機能
│       ├── DESIGN.md
│       ├── output/
│       └── stories/
│           ├── login-form/
│           │   ├── story-analysis.json
│           │   ├── task-list.json
│           │   ├── TODO.md
│           │   └── output/
│           └── password-reset/
│               ├── story-analysis.json
│               ├── task-list.json
│               ├── TODO.md
│               └── output/
```

**サブエージェント間の引き継ぎ**:
```
analyze-story.md
    ↓ story-analysis.json
decompose-tasks.md
    ↓ task-list.json
assign-workflow.md
    ↓ TODO.md
developing（TDD/E2E/TASK）
    ↓
feedback
    ↓ features/{feature-slug}/DESIGN.md に追記
```

**蓄積フロー**:
```
login-form ────┐
password-reset ┼─→ features/user-auth/DESIGN.md ─┐
session-mgmt ──┘                                  │
                                                  ├─→ features/DESIGN.md
layout ────────┐                                  │    （総合設計）
widgets ───────┼─→ features/dashboard/DESIGN.md ──┘
```

**ファイルの役割**:
| ファイル | スコープ | 更新タイミング |
|----------|----------|----------------|
| stories/{story-slug}/story-analysis.json | ストーリー | analyze-story実行時 |
| stories/{story-slug}/task-list.json | ストーリー | decompose-tasks実行時 |
| stories/{story-slug}/TODO.md | ストーリー | assign-workflow実行時 |
| features/{feature-slug}/DESIGN.md | 機能単位 | feedback実行時 |
| features/DESIGN.md | プロジェクト全体 | feedback実行時（または定期統合） |

### Worktree運用（1ストーリー = 1 Worktree）

各ストーリーはWorktreeで独立した作業環境を作り、衝突を防ぐ。

```
ストーリー受領
    ↓
slug決定: feature-slug（例: user-auth）, story-slug（例: login-form）
    ↓
git worktree add ../project-{story-slug} feature/{story-slug}
    ↓
cd ../project-{story-slug} && claude
    ↓
[story-to-tasks] → 詳細: #1-story-to-tasksタスク仕様書作成
    → docs/features/{feature-slug}/stories/{story-slug}/story-analysis.json
    → docs/features/{feature-slug}/stories/{story-slug}/task-list.json
    → docs/features/{feature-slug}/stories/{story-slug}/TODO.md
    ↓
[developing] → 詳細: #2-developing実装
    ↓
[feedback] → 詳細: #3-feedbackフィードバック
    → docs/features/{feature-slug}/DESIGN.md に追記
    → docs/features/DESIGN.md にも反映
    ↓
マージ（PR作成 → レビュー → マージ）
    ↓
git worktree remove ../project-{story-slug}
```

**メリット**:
- mainブランチを汚さない
- 各ストーリーが独立した環境で開発される
- 途中で別のストーリーが入っても衝突しない
- 結果的に複数ストーリーの並列開発も可能（副次的効果）

**命名規則**:
- Worktreeディレクトリ: `../project-{story-slug}`
- ブランチ名: `feature/{story-slug}`

→ 詳細: [Worktree運用ガイド](reference/worktree-guide.md)

### Big 3 と skill-creator の連携

```
ストーリー → [story-to-tasks] → タスク
                                   ↓
                             [developing]（TDD/PLAN）
                                   ↓
                             [feedback]
                                   │
                                   ├─ DESIGN.md蓄積
                                   │
                                   └─ スキル化/ルール化候補検出
                                        ↓
                                  [skill-creator呼び出し]
                                        ↓
                                   新規スキル/ルール作成
```

**設計方針**:
- **Big 3**: 開発ワークフロー専用（story-to-tasks → developing → feedback）
- **skill-creator**: スキル/ルール作成・更新用（Big 3の外側に配置）
- **連携**: feedbackが「スキル化候補」を検出した時にskill-creatorを呼び出し

### 1. story-to-tasks（タスク仕様書作成）

ストーリーから直接タスクリストを生成。TDD/PLAN分岐を自動判定。
Worktree作成後、最初に実行するスキル。

**入力**:
- ユーザーストーリー（会話 or USER_STORIES.md）
- feature-slug（例: user-auth）
- story-slug（例: login-form）

**出力**（`docs/features/{feature-slug}/stories/{story-slug}/`に保存）:
- `story-analysis.json` - ストーリー分析結果
- `task-list.json` - タスクリスト
- `TODO.md` - TDD/E2E/TASKラベル付きタスク

**Task仕様書（agents/）**:

| Phase | Task | ファイル | 推奨モデル | 役割 |
|-------|------|----------|-----------|------|
| 1 | ストーリー分析 | `analyze-story.md` | **opus** | ストーリーの目的・スコープ・受入条件を抽出 |
| 2 | タスク分解 | `decompose-tasks.md` | sonnet | ストーリーを実装可能なタスクに分解 |
| 3 | TDD/E2E/TASK分類 | `assign-workflow.md` | haiku | 各タスクをTDD/E2E/TASKに分類・ラベル付与 |

→ 詳細: [TDD/E2E/TASK判定基準](reference/tdd-e2e-task-criteria.md)
→ 実行環境: [Worktree運用](#worktree運用1ストーリー--1-worktree)

### 2. developing（実装）

TODO.mdのタスクを実行。Worktree内で独立した環境で開発する。

- `[TDD]` ラベル → TDDワークフロー（impl.mdベース）
- `[E2E]` ラベル → E2Eワークフロー（agent-browser操作検証）
- `[TASK]` ラベル → TASKワークフロー（セットアップ/設定）

**Task仕様書（agents/）**:

| フロー | Task | ファイル | 推奨モデル | 役割 |
|--------|------|----------|-----------|------|
| TDD | テスト作成 | `tdd-write-test.md` | sonnet | RED: 失敗するテストを書く |
| TDD | 実装 | `tdd-implement.md` | sonnet | GREEN: テストを通す最小実装 |
| TDD | リファクタ | `tdd-refactor.md` | **opus** | REFACTOR: コード品質改善 |
| E2E | UI実装 | `e2e-implement.md` | sonnet | UIコンポーネント実装 |
| E2E | 検証 | `e2e-verify.md` | haiku | agent-browser操作フロー検証 |
| TASK | 実行 | `task-execute.md` | sonnet | 設定/セットアップ実行 |

→ 詳細: [TDDワークフロー](reference/tdd-workflow.md) | [E2Eサイクル](reference/e2e-cycle.md) | [TASKワークフロー](reference/task-workflow.md)
→ 実行環境: [Worktree運用](#worktree運用1ストーリー--1-worktree)

### 3. feedback（フィードバック）

実装完了後、学んだことをシステム仕様書に反映。
developing完了後、PR作成前に実行するスキル。

**入力**:
- feature-slug（例: user-auth）
- story-slug（例: login-form）
- 実装済みコード（git diff）

**出力**:
- `docs/features/{feature-slug}/DESIGN.md` に追記
- `docs/features/DESIGN.md`（総合設計）にも反映

**フィードバック内容**:
- 実装で判明した仕様・設計判断をDESIGN.mdに追記
- よく使うパターンをスキル/ルールとして抽出・提案
- プロジェクト固有の規約をルール化

**Task仕様書（agents/）**:

| Phase | Task | ファイル | 推奨モデル | 役割 |
|-------|------|----------|-----------|------|
| 1 | 変更分析 | `analyze-changes.md` | sonnet | git diffから学習事項を抽出 |
| 2 | 仕様書更新 | `update-design.md` | **opus** | DESIGN.mdに設計判断を追記 |
| 3 | パターン検出 | `detect-patterns.md` | haiku | 繰り返しパターンを検出 |
| 4 | 改善提案 | `propose-improvement.md` | **opus** | スキル化/ルール化を提案 |

→ 実行環境: [Worktree運用](#worktree運用1ストーリー--1-worktree)

**フィードバック記録**（skill-creatorの機構を活用）:
- **LOGS.md**: 実行記録（success/failure、フェーズ、メモ）
- **EVALS.json**: メトリクス（成功率、実行回数）
- **patterns.md**: 成功/失敗パターン蓄積

**DESIGN.mdは「実装の記録」として育てていく**。

## skill-creator（スキル作成・更新）

Big 3の外側に配置するメタスキル。feedbackからの呼び出しで連携。

**参照元**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator`

### 役割

| モード | 用途 | 呼び出し条件 |
|--------|------|-------------|
| collaborative | ユーザー対話でスキル共創 | feedbackで「スキル化候補」検出時 |
| create | 新規スキル作成 | 明確な要件がある場合 |
| update | 既存スキル更新 | パターン蓄積でルール化が必要な場合 |
| improve-prompt | プロンプト改善 | スキルの成功率が低い場合 |

### 自己改善サイクル

```
スキル実行 → LOGS.md記録 → EVALS.jsonメトリクス
                ↓
       パターン分析 → patterns.md蓄積
                ↓
       自己改善提案 → スキル/ルール更新
```

→ 詳細: [skill-creator参照](reference/skill-creator-overview.md)

## TDD/E2E/TASKフロー概要

### TDDフロー（Claude Code推奨ワークフロー準拠）

```
テストファースト → テストコミット → 実装反復（テスト固定）→ 品質チェック → コミット
```

→ 詳細: [TDDワークフロー](reference/tdd-workflow.md)

### E2Eフロー（agent-browser + 目視確認）

```
UI実装 → agent-browser自動検証（ループ）→ 目視確認（任意）→ 品質チェック → コミット
```

→ 詳細: [E2Eサイクル](reference/e2e-cycle.md)

### TASKフロー（セットアップ/設定）

```
実行（EXEC）→ 検証（VERIFY）→ コミット
```

→ 詳細: [TASKワークフロー](reference/task-workflow.md)

### TDD/E2E/TASK 適用判断

| 基準 | TDD | E2E | TASK |
|------|-----|-----|------|
| 入出力 | 明確に定義可能 | 見た目やUXで判断 | コマンド実行結果で判断 |
| 検証方法 | アサーション | 視覚的確認 | 実行結果・ファイル存在確認 |
| レイヤー | ロジック層 | プレゼンテーション層 | インフラ/設定層 |
| 対象 | バリデーション、計算、API | UIコンポーネント、レイアウト | 環境構築、設定ファイル、CI/CD |

→ 詳細: [TDD/E2E/TASK判定基準](reference/tdd-e2e-task-criteria.md)

## ファイル構成

### 新規作成ファイル

```
.claude/
├── skills/
│   ├── dev/                            # 開発関連スキル（Big 3）
│   │   ├── story-to-tasks/
│   │   │   ├── SKILL.md                # タスク仕様書作成（TDD/E2E/TASK分岐）
│   │   │   ├── agents/                 # Task仕様書
│   │   │   │   ├── analyze-story.md    # ストーリー分析
│   │   │   │   ├── decompose-tasks.md  # タスク分解
│   │   │   │   └── assign-workflow.md  # TDD/E2E/TASK分類
│   │   │   └── references/
│   │   │       ├── tdd-criteria.md     # TDD判定基準
│   │   │       ├── e2e-criteria.md     # E2E判定基準
│   │   │       └── task-criteria.md    # TASK判定基準
│   │   │
│   │   ├── developing/                 # （既存からコピー＋拡張）
│   │   │   ├── SKILL.md
│   │   │   └── agents/                 # Task仕様書
│   │   │       ├── tdd-write-test.md   # TDD: テスト作成（RED）
│   │   │       ├── tdd-implement.md    # TDD: 実装（GREEN）
│   │   │       ├── tdd-refactor.md     # TDD: リファクタ
│   │   │       ├── e2e-implement.md    # E2E: UI実装
│   │   │       ├── e2e-verify.md       # E2E: agent-browser検証
│   │   │       └── task-execute.md     # TASK: セットアップ実行
│   │   │
│   │   └── feedback/
│   │       ├── SKILL.md                # フィードバック＋自己改善
│   │       ├── LOGS.md                 # 実行記録
│   │       ├── EVALS.json              # メトリクス
│   │       ├── agents/                 # Task仕様書
│   │       │   ├── analyze-changes.md  # 変更分析
│   │       │   ├── update-design.md    # 仕様書更新
│   │       │   ├── detect-patterns.md  # パターン検出
│   │       │   └── propose-improvement.md # 改善提案
│   │       └── references/
│   │           ├── update-format.md    # 仕様書更新フォーマット
│   │           ├── improvement-patterns.md # 自己改善パターン検出基準
│   │           └── feedback-loop.md    # フィードバック記録方式（skill-creatorから）
│   │
│   └── meta-skill-creator/             # メタスキル（Big 3外）
│       ├── SKILL.md                    # スキル作成・更新
│       ├── LOGS.md
│       ├── EVALS.json
│       ├── agents/                     # LLMサブタスク定義（20ファイル）
│       ├── scripts/                    # 決定論的処理（25+ファイル）
│       ├── references/                 # 知識の外部化（23ファイル）
│       ├── schemas/                    # JSON検証スキーマ（23+ファイル）
│       └── assets/                     # テンプレート（17+ファイル）
│
├── rules/
│   └── workflow/
│       ├── tdd-workflow.md             # TDD 6ステップワークフロー
│       ├── e2e-cycle.md                # E2Eサイクルルール
│       └── workflow-branching.md       # TDD/E2E/TASK分岐判定ルール
│
└── commands/
    └── dev/                            # 開発関連コマンド
        ├── story.md                    # /dev:story コマンド
        └── feedback.md                 # /dev:feedback コマンド
```

### 既存ファイル活用（コピー・参照）

| コピー元 | コピー先 | 用途 |
|----------|----------|------|
| `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/` | `.claude/skills/meta-skill-creator/` | メタスキル全体（コピー＋パス修正） |
| `docs/SAMPLE/dev/dotfiles/claude/commands/impl.md` | 参照のみ | TDDフローのベース設計 |
| `docs/SAMPLE/dev/dotfiles/claude/skills/analyzing-requirements/references/design-template.md` | `.claude/skills/dev/feedback/references/design-template.md` | DESIGN.mdテンプレート（PLANセクション追加） |

## タスクリスト

### Phase 1: skill-creatorコピー＆カスタマイズ

- [x] `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/` → `.claude/skills/meta-skill-creator/` コピー
- [x] meta-skill-creatorのパス参照を修正（`.claude/skills/meta-skill-creator/`に合わせる）
- [x] meta-skill-creatorの動作確認

### Phase 2: 新規スキル作成（Big 3）

#### story-to-tasks
- [x] `.claude/skills/dev/story-to-tasks/SKILL.md` 作成
- [x] `.claude/skills/dev/story-to-tasks/agents/analyze-story.md` 作成
- [x] `.claude/skills/dev/story-to-tasks/agents/decompose-tasks.md` 作成
- [x] `.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md` 作成（後にassign-workflow.mdにリネーム）
- [x] `.claude/skills/dev/story-to-tasks/references/tdd-criteria.md` 作成
- [x] `.claude/skills/dev/story-to-tasks/references/e2e-criteria.md` 作成

#### developing
- [x] `.claude/skills/dev/developing/SKILL.md` 作成（impl.mdを参照してTDD/E2E/TASK対応）
- [x] `.claude/skills/dev/developing/agents/tdd-write-test.md` 作成
- [x] `.claude/skills/dev/developing/agents/tdd-implement.md` 作成
- [x] `.claude/skills/dev/developing/agents/tdd-refactor.md` 作成
- [x] `.claude/skills/dev/developing/agents/e2e-implement.md` 作成
- [x] `.claude/skills/dev/developing/agents/e2e-verify.md` 作成（agent-browser操作フロー検証）
- [x] `.claude/skills/dev/developing/references/tdd-flow.md` 作成（impl.mdベース）
- [x] `.claude/skills/dev/developing/references/e2e-flow.md` 作成（agent-browser検証フロー）

#### feedback
- [x] `.claude/skills/dev/feedback/SKILL.md` 作成（skill-creator連携機能含む）
- [x] `.claude/skills/dev/feedback/agents/analyze-changes.md` 作成
- [x] `.claude/skills/dev/feedback/agents/update-design.md` 作成
- [x] `.claude/skills/dev/feedback/agents/detect-patterns.md` 作成
- [x] `.claude/skills/dev/feedback/agents/propose-improvement.md` 作成
- [x] `.claude/skills/dev/feedback/references/design-template.md` コピー＆拡張（PLANセクション追加）
- [x] `.claude/skills/dev/feedback/references/update-format.md` 作成
- [x] `.claude/skills/dev/feedback/references/improvement-patterns.md` 作成
- [x] `.claude/skills/dev/feedback/references/feedback-loop.md` コピー（skill-creatorから）

### Phase 3: ルール作成・TASK対応

- [x] `.claude/rules/workflow/tdd-workflow.md` 作成（TDD 6ステップ）
- [x] `.claude/rules/workflow/e2e-cycle.md` 作成
- [x] `.claude/rules/workflow/workflow-branching.md` 作成

#### Phase 3追加: TASK分類対応
- [x] `.claude/skills/dev/story-to-tasks/references/task-criteria.md` 作成
- [x] `.claude/rules/workflow/workflow-branching.md` 修正（TASK判定基準追加）
- [x] `.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md` → `assign-workflow.md` リネーム・修正
- [x] `.claude/skills/dev/story-to-tasks/SKILL.md` 修正（3分類対応）
- [x] `.claude/skills/dev/developing/references/task-flow.md` 作成
- [x] `.claude/skills/dev/developing/agents/task-execute.md` 作成
- [x] `.claude/skills/dev/developing/SKILL.md` 修正（TASKワークフロー追加）
- [x] `CLAUDE.md` 修正（3分類コンセプト）

### Phase 4: コマンド作成

- [x] `.claude/commands/dev/story.md` 作成（/dev:story）
- [x] `.claude/commands/dev/feedback.md` 作成（/dev:feedback）

### Phase 5: 言語別ルール作成（並列可能）

#### HTML/CSS
- [x] `.claude/rules/languages/html-css/coding.md`
- [x] `.claude/rules/languages/html-css/testing.md`
- [x] `.claude/rules/languages/html-css/design.md`

#### TypeScript/React
- [x] `.claude/rules/languages/typescript/coding.md`
- [x] `.claude/rules/languages/typescript/testing.md`
- [x] `.claude/rules/languages/react/coding.md`
- [x] `.claude/rules/languages/react/testing.md`
- [x] `.claude/rules/languages/react/design.md`

#### JavaScript
- [x] `.claude/rules/languages/javascript/coding.md`
- [x] `.claude/rules/languages/javascript/testing.md`

#### PHP
- [x] `.claude/rules/languages/php/coding.md`
- [x] `.claude/rules/languages/php/testing.md`

#### Python
- [x] `.claude/rules/languages/python/coding.md`
- [x] `.claude/rules/languages/python/testing.md`

### Phase 6: 統合テスト

#### サンプルストーリー準備
- [ ] テスト用サンプルストーリー作成（「ログインフォームを作成する」）
- [ ] TDDタスク例（バリデーションロジック）の期待値定義
- [ ] PLANタスク例（UIコンポーネント）の期待値定義

#### 動作確認
- [ ] story-to-tasksの動作確認（slug自動生成＋確認フロー）
- [ ] TDD/PLAN分岐の動作確認
- [ ] TDDフロー（RED→GREEN→REFACTOR）の動作確認
- [ ] PLANフロー（agent-browser操作検証）の動作確認
- [ ] feedbackの動作確認（DESIGN.md蓄積）
- [ ] skill-creator連携の動作確認（パターン検出→スキル化提案）

### Phase 7: ドキュメント

- [x] CLAUDE.md更新（Available Skills）

## 既存スキルとの関係

### story-to-tasks（新規）

planning-tasksを参考に、ストーリーから直接タスク生成。

**特徴**:
1. DESIGN.mdを経由せず、ストーリーから直接TODO.md生成
2. タスクに`[TDD]`/`[E2E]`/`[TASK]`ラベルを自動付与
3. TDDタスク、E2Eタスク、TASKタスクをグループ化

### developing（既存活用）

既存のTDDスキルをコピーして活用。`[TDD]`ラベル付きタスクに適用。
`[E2E]`ラベルはE2Eサイクル（agent-browser）で実装。
`[TASK]`ラベルはTASKワークフロー（EXEC→VERIFY→COMMIT）で実装。

### feedback（新規）

実装完了後にDESIGN.mdを更新・蓄積。
従来のanalyzing-requirementsとは逆方向（実装→仕様書）。

**skill-creator連携**:
- パターン検出時にスキル化/ルール化を提案
- ユーザー承認後、skill-creatorを呼び出して新規スキル/ルール作成

### skill-creator（コピー）

`docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/`からコピー。
Big 3の外側に配置し、feedbackからの呼び出しで連携。

**設計原則**（参照元を継承）:
- Collaborative First: ユーザーとの対話で要件明確化
- Script First: 決定論的処理はスクリプトで実行
- Progressive Disclosure: 必要な時に必要なリソースのみ読み込み

## 参考資料

- [Worktree運用ガイド](reference/worktree-guide.md)
- [Task仕様書ガイド](reference/task-spec-guide.md)
- [TDDワークフロー詳細](reference/tdd-workflow.md)
- [PLANサイクル詳細](reference/plan-cycle.md)
- [TDD/PLAN判定基準](reference/tdd-plan-criteria.md)
- [スキル実装例](reference/skill-examples.md)
- [skill-creator概要](reference/skill-creator-overview.md)
