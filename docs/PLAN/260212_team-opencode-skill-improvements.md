# dev:team-opencode スキル改善計画

## 注意書き

実行時はタスクリストのチェックを随時更新すること。

## 概要

slide_ad2のLP改修タスクで `dev:team-opencode` を実行した際に発見された8つの問題を改善する。

核心的な改善は **「計画フェーズ（Phase 0）の新設」** であり、dev:story と同様に story-analysis.json / task-list.json を作成するプロセスをスキルに組み込む。これにより問題の大半が構造的に解決される。

## 背景

LP改修では「コピーライター / デザイナー / 実装者 / レビュワー」のロール分業チームを組成して実行した。その過程で以下の問題が発生した:

- リーダーがロール設計を一から考える必要があった（スキルにガイダンスなし）
- エージェントが自分のタスク以外を勝手に実行した
- 直列依存タスクの制御ができなかった
- 成果物の品質チェックなく次工程に進んだ（敬語不統一など）
- テンプレートが worker-N 固定で、ロール名を付けられなかった
- 完了後に追加タスク（トーン修正）が必要になったが、対応フローがなかった

---

## 設計方針

| 方針                   | 内容                                                                                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| dev:story との関係     | dev:team-opencode は `docs/features/team-opencode/` を一時計画フォルダとして使用し、起動時にクリーンアップ＆初期化する |
| ロール分業前提         | 創作・設計・実装・レビューなど専門性の異なるロールでチームを組成する。ファイル分業やハイブリッドは対象外               |
| 計画はリーダーが実行   | 計画フェーズはリーダー（Claude Code）が自ら実行する。opencode に委譲するのはタスク実行のみ                             |
| ロールカタログで再利用 | よくあるロール定義を `references/role-catalog.md` に一元管理し、プロンプトテンプレートから参照する                     |

---

## 改善候補と解決状況

| #   | 改善候補                   | 計画フェーズ新設で解決 | 残存する対応                                    |
| --- | -------------------------- | :--------------------: | ----------------------------------------------- |
| 1   | ロール設計ガイダンス       |        **解決**        | -                                               |
| 2   | エージェント越境防止       |        **解決**        | テンプレート厳守事項も追加                      |
| 3   | 直列依存タスクの制御       |        **解決**        | -                                               |
| 6   | 品質ゲートの導入           |        **解決**        | レビュワーを最終Waveに必須配置                  |
| 7   | テンプレートのロール名対応 |        **解決**        | -                                               |
| 8   | 追加タスク対応フロー       |        **解決**        | レビュワー → AskUserQuestion → Phase 0-2 ループ |

---

## 新アーキテクチャ: 計画フェーズの新設

### 一時計画フォルダ

```
docs/features/team-opencode/
├── story-analysis.json    # ストーリー分析（ゴール、スコープ、受入条件）
├── task-list.json         # ロールごとのタスク定義（Wave構造 + ロール割当）
└── prompts/               # 各ロールの opencode 実行プロンプト（自動生成）
    ├── copywriter.md
    ├── designer.md
    ├── implementer.md
    └── reviewer.md
```

Phase 0-0 として起動時に毎回 `scripts/init-team-workspace.sh` を実行:

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="docs/features/team-opencode"

# クリーンアップ
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE/prompts"

# テンプレート雛形を配置
cp references/templates/story-analysis.template.json "$WORKSPACE/story-analysis.json"
cp references/templates/task-list.template.json      "$WORKSPACE/task-list.json"
```

SKILL.md からは `Bash("bash scripts/init-team-workspace.sh")` で呼び出すだけ。

---

### story-analysis.json テンプレート

dev:story の story-analysis.json に `teamDesign` セクションを追加した拡張版。ロール一覧、Wave構造（直列依存）、品質ゲートを定義する。

```json
{
  "story": { "title": "", "description": "" },
  "goal": "",
  "scope": { "included": [], "excluded": [] },
  "acceptanceCriteria": [],
  "teamDesign": {
    "roles": [],
    "waves": [],
    "qualityGates": []
  }
}
```

#### `teamDesign.roles` の例

```json
"roles": [
  {
    "name": "copywriter",
    "catalogRef": "copywriter",
    "customDirective": "コピーライティングフレームワークに従う。敬語で統一。",
    "outputs": ["docs/features/team-opencode/lp-copy.md"]
  },
  {
    "name": "designer",
    "catalogRef": "designer",
    "customDirective": "Brutalist Editorial デザインシステムに準拠。Tailwind v4記法。",
    "outputs": ["docs/features/team-opencode/lp-design.md"]
  },
  {
    "name": "implementer",
    "catalogRef": "implementer",
    "customDirective": null,
    "outputs": ["src/components/lp/*.tsx"]
  },
  {
    "name": "reviewer",
    "catalogRef": "reviewer",
    "customDirective": "Tailwind v4記法チェック + トーン統一チェック",
    "outputs": []
  }
]
```

- `catalogRef`: ロールカタログのキーを参照
- `customDirective`: タスク固有の追加指示（null ならカタログのデフォルトのみ）

#### `teamDesign.waves` の例

```json
"waves": [
  {
    "id": 1,
    "parallel": ["copywriter", "designer"],
    "description": "コピーとデザイン仕様を並行作成"
  },
  {
    "id": 2,
    "parallel": ["implementer"],
    "blockedBy": [1],
    "description": "Wave 1 の成果物を元に実装"
  },
  {
    "id": 3,
    "parallel": ["reviewer"],
    "blockedBy": [2],
    "description": "実装完了後の横断レビュー"
  }
]
```

---

### task-list.json テンプレート

dev:story の task-list.json との差分:

- `phases` → `waves`（直列/並列制御を明示）
- 各タスクに `taskPrompt` フィールド追加
- `inputs` / `outputs` でWave間のデータフローを明示
- Wave内のタスクをロール別配列で管理（`roles: { [roleName]: Task[] }`）

```json
{
  "context": {
    "description": "",
    "targetFiles": {},
    "relatedModules": {},
    "technicalNotes": {}
  },
  "waves": [
    {
      "id": 1,
      "roles": {
        "copywriter": [
          {
            "id": "task-1-1",
            "name": "HeroSectionのコピー作成",
            "description": "PASBECONAのP（Problem）A（Affinity）を反映したヘッダーコピー",
            "outputs": ["docs/features/team-opencode/copy-hero.md"],
            "taskPrompt": "..."
          },
          {
            "id": "task-1-2",
            "name": "EvidenceSectionのコピー作成",
            "description": "E（Evidence）に対応する実績・根拠セクションのコピー",
            "outputs": ["docs/features/team-opencode/copy-evidence.md"],
            "taskPrompt": "..."
          },
          {
            "id": "task-1-3",
            "name": "CTASectionのコピー作成",
            "description": "N（Narrow down）A（Action）に対応するCTAコピー",
            "outputs": ["docs/features/team-opencode/copy-cta.md"],
            "taskPrompt": "..."
          }
        ],
        "designer": [
          {
            "id": "task-2-1",
            "name": "HeroSectionのデザイン仕様",
            "description": "ヒーロー領域のコンポーネント構造・レスポンシブ仕様",
            "outputs": ["docs/features/team-opencode/design-hero.md"],
            "taskPrompt": "..."
          },
          {
            "id": "task-2-2",
            "name": "EvidenceSectionのデザイン仕様",
            "description": "実績セクションのカード・グリッド構造・Tailwindクラス",
            "outputs": ["docs/features/team-opencode/design-evidence.md"],
            "taskPrompt": "..."
          },
          {
            "id": "task-2-3",
            "name": "CTASectionのデザイン仕様",
            "description": "CTAボタン・フォーム領域のコンポーネント構造",
            "outputs": ["docs/features/team-opencode/design-cta.md"],
            "taskPrompt": "..."
          }
        ]
      }
    },
    {
      "id": 2,
      "blockedBy": [1],
      "roles": {
        "implementer": [
          {
            "id": "task-3-1",
            "name": "HeroSection実装",
            "description": "copy-hero.md + design-hero.md に基づくReactコンポーネント実装",
            "inputs": ["docs/features/team-opencode/copy-hero.md", "docs/features/team-opencode/design-hero.md"],
            "outputs": ["src/components/lp/HeroSection.tsx"],
            "taskPrompt": "..."
          },
          {
            "id": "task-3-2",
            "name": "EvidenceSection実装",
            "description": "copy-evidence.md + design-evidence.md に基づく実装",
            "inputs": ["docs/features/team-opencode/copy-evidence.md", "docs/features/team-opencode/design-evidence.md"],
            "outputs": ["src/components/lp/EvidenceSection.tsx"],
            "taskPrompt": "..."
          },
          {
            "id": "task-3-3",
            "name": "CTASection実装",
            "description": "copy-cta.md + design-cta.md に基づく実装",
            "inputs": ["docs/features/team-opencode/copy-cta.md", "docs/features/team-opencode/design-cta.md"],
            "outputs": ["src/components/lp/CTASection.tsx"],
            "taskPrompt": "..."
          }
        ]
      }
    }
  ],
  "metadata": {
    "totalTasks": 9,
    "totalWaves": 3,
    "roles": ["copywriter", "designer", "implementer", "reviewer"]
  }
}
```

各ロール内のタスクは **1つのopencode呼び出しで完結する粒度** に分解する。1タスク = 1セクション or 1コンポーネント程度が目安。

---

## ロールカタログ: references/role-catalog.md

よくあるロールの定義と `role_directive` を一元管理する。story-analysis.json の `catalogRef` で参照し、プロンプト生成時にテンプレートへ挿入する。

### 構造

以下はWebアプリ・サービス開発で汎用的に使えるロール一覧。プロジェクト固有のロールは `customDirective` で補完する。

```markdown
# ロールカタログ

## 実装系

### frontend-developer

説明: フロントエンド実装担当。UIコンポーネント、画面、インタラクションの実装。

role_directive: |
あなたはフロントエンド開発者です。以下の方針で実装してください:

- 提供された仕様書・デザインに厳密に従う
- 既存コードの構造・命名規則・スタイルガイドに合わせる
- アクセシビリティとレスポンシブ対応を考慮する
- 独自の判断で仕様やデザインを変更しない

デフォルト出力: ソースコードファイル

---

### backend-developer

説明: バックエンド実装担当。API、DB、ビジネスロジックの実装。

role_directive: |
あなたはバックエンド開発者です。以下の方針で実装してください:

- API設計書・スキーマ定義に厳密に従う
- エラーハンドリングとバリデーションを適切に実装する
- セキュリティ（認証・認可・入力検証）を考慮する
- パフォーマンスとスケーラビリティを意識する

デフォルト出力: ソースコードファイル

---

### tdd-developer

説明: TDD開発担当。テスト駆動でロジックを実装。

role_directive: |
あなたはTDD開発者です。t_wadaのTDDで、YAGNIの原則に従い、Baby stepsで実装してください。

- RED: まずテストを書き、失敗することを確認する
- GREEN: テストを通す最小限の実装のみ書く
- REFACTOR: テストが通る状態を維持しながら品質改善
  テストを先に書かずに実装を始めない。テストを変更してグリーンにしない。

デフォルト出力: テストファイル + ソースコードファイル

---

### fullstack-developer

説明: フルスタック実装担当。フロントからバックまで一貫して実装。

role_directive: |
あなたはフルスタック開発者です。以下の方針で実装してください:

- フロント〜バックエンドを一貫した設計で実装する
- API境界の型安全性を確保する
- 仕様書に厳密に従い、独自の判断で変更しない

デフォルト出力: ソースコードファイル

## 設計・企画系

### designer

説明: UI/UXデザイン仕様書担当。コンポーネント構造、スタイル、レスポンシブ仕様を定義。

role_directive: |
あなたはUIデザイナーです。以下の方針でデザイン仕様書を作成してください:

- 既存のデザインシステムに準拠する
- コンポーネント構造を擬似コードで記述する
- スタイルクラスを具体的に指定する
- レスポンシブ対応（モバイル/タブレット/デスクトップ）を明記する

デフォルト出力: Markdownファイル（docs/\*.md）

---

### copywriter

説明: コピーライティング担当。マーケティングコピー、UIテキスト、ドキュメント文章。

role_directive: |
あなたはコピーライターです。以下の方針でコピーを作成してください:

- ターゲットユーザーの課題と欲求を深く理解する
- 明確で説得力のある文章を書く
- トーン&マナーの一貫性を保つ

デフォルト出力: Markdownファイル（docs/\*.md）

---

### architect

説明: 設計担当。システム構成、データモデル、API設計、技術選定。

role_directive: |
あなたはソフトウェアアーキテクトです。以下の方針で設計してください:

- 要件を満たす最もシンプルな構成を選ぶ
- 既存のアーキテクチャとの整合性を保つ
- トレードオフを明示し、判断根拠を記録する
- スキーマ・API仕様は具体的な型定義で記述する

デフォルト出力: Markdownファイル（docs/\*.md）

## 品質・検証系

### reviewer

説明: レビュー担当。全成果物の横断レビューと品質チェック。

role_directive: |
あなたはレビュー担当です。以下の観点でレビューしてください:

- プロジェクトルール（コーディング規約等）への準拠
- 成果物間の整合性
- セキュリティ・パフォーマンスの懸念
- 問題を発見した場合、修正を直接実施する

デフォルト出力: 修正済みコード + レビュー報告（SendMessage）

---

### tester

説明: テスト担当。テスト計画、テストケース作成、テスト実行。

role_directive: |
あなたはQAテスターです。以下の方針でテストしてください:

- 仕様書に基づくテストケースを網羅的に作成する
- 正常系・異常系・境界値を必ず含める
- 再現手順を明確に記録する
- テスト結果を構造化して報告する

デフォルト出力: テストファイル + テスト結果報告

## 調査・分析系

### researcher

説明: 調査・分析担当。技術調査、競合分析、ベストプラクティス調査。

role_directive: |
あなたはリサーチャーです。以下の方針で調査してください:

- 客観的で裏付けのある情報を収集する
- 調査結果を構造化してMarkdownで報告する
- 実装への具体的な示唆を含める

デフォルト出力: Markdownファイル（docs/\*.md）
```

---

## エージェントプロンプトテンプレート改訂

### 統一テンプレート: agent-prompt-template.md

旧: `worker-{N}` 固定 + 汎用/TDD の2テンプレート
新: 1つのテンプレートにロール固有差分を挿入する方式

```markdown
あなたは{team_name}チームのメンバー「{agent_name}」です。

## あなたの役割

{role_directive}

{custom_directive}

## タスク

{タスク内容}

## 入力ファイル

{input_files}

## 期待する成果物

{output_files}

## 実行手順

1. TaskUpdate でタスク#{id} を in_progress にし、owner を「{agent_name}」に設定

2. 以下のコマンドをそのまま実行してください。モデルやコマンドを変更しないでください:

opencode run -m {OC_MODEL} "{taskPrompt}" 2>&1

3. opencode の出力結果を確認する

4. opencode が生成したコードやファイルがあれば、指示通りに適用する

5. TaskUpdate でタスク#{id} を completed にする

6. SendMessage でリーダー(team-lead)に結果を報告する

## 厳守事項

- opencode run のモデルは必ず {OC_MODEL} を使用。他のモデルに変更しない
- opencode run でエラーが出た場合、同じコマンドを最大3回リトライする
- 直接分析・直接実装にフォールバックしない。opencode run の結果のみ使用する
- コマンドを改変しない。テンプレート通りに実行する
- タスク#{id} 以外のタスクには手を出さない。完了後はリーダーに報告し、指示を待つ
- TaskList で他の未割り当てタスクを見つけても、自分で拾わない
- 完了報告後、リーダーから追加指示がなければ待機する
```

### 変数一覧

| 変数                 | ソース                                   |
| -------------------- | ---------------------------------------- |
| `{team_name}`        | TeamCreate で生成                        |
| `{agent_name}`       | task-list.json の `role`                 |
| `{role_directive}`   | role-catalog.md から取得                 |
| `{custom_directive}` | story-analysis.json の `customDirective` |
| `{タスク内容}`       | task-list.json の `description`          |
| `{input_files}`      | task-list.json の `inputs`               |
| `{output_files}`     | task-list.json の `outputs`              |
| `{id}`               | TaskCreate で生成                        |
| `{OC_MODEL}`         | Phase 0 で選択                           |
| `{taskPrompt}`   | task-list.json の `taskPrompt`       |

### TDD テンプレートの統合

旧 `agent-prompt-template-tdd.md` は廃止。`tdd-developer` ロールとしてカタログに統合済み。

---

## 改訂 SKILL.md フロー

```
Phase 0: 計画（NEW — Claude Code が実行）
  0-0: クリーンアップ＆テンプレート初期化
  0-1: opencode モデル選択
  0-2: ストーリー分析 → story-analysis.json
  0-3: コード探索＆タスク分解 → task-list.json
  0-4: opencode codex でタスクレビュー → 修正ループ（最大3回）
  0-5: ユーザー承認

Phase 1: チーム実行（Wave 式）
  1-1: チーム作成（TeamCreate）
  1-2: タスク登録（TaskCreate + blockedBy）
  1-3: Wave 1 のエージェントスポーン
  1-4: 完了待機
  1-5: Wave N+1 スポーン（繰り返し）

Phase 2: レビュー・フィードバックループ
  2-1: レビュワー（最終Wave）が改善候補を報告
  2-2: AskUserQuestion でユーザーに提示
  2-3: 追加対応あり → Phase 0-2 に戻る
       追加対応なし → Phase 3 へ

Phase 3: クリーンアップ
  3-1: シャットダウン
  3-2: TeamDelete
```

---

## Phase 0-5: opencode codex タスクレビューの詳細

dev:story の plan-review と同様、タスク分解の品質を opencode の codex モデルで検証する。

### フロー

```
0-3: task-list.json 生成完了
  ↓
0-4: opencode run -m openai/gpt-5.3-codex "..." で以下を検証:
  - タスク粒度（1 opencode呼び出しで完結する粒度か）
  - Wave間の依存関係（inputs/outputs の整合性）
  - ロール割当の妥当性（catalogRef と作業内容の一致）
  - 漏れタスク（セットアップ、エラーハンドリング等）
  ↓
APPROVED → 0-5 へ
NEEDS_REVISION → task-list.json を修正 → 再レビュー（最大3回）
3回失敗 → 現状のままユーザーに提示し判断を仰ぐ
```

### opencode 呼び出し例

```bash
opencode run -m openai/gpt-5.3-codex "
Review this team task breakdown:

## Story Analysis
{story-analysis.json}

## Task List
{task-list.json}

Analyze:
1. Task granularity - Each task should be completable in a single opencode call
2. Wave dependencies - inputs/outputs consistent across waves?
3. Role assignment - Does each task match its assigned role?
4. Missing tasks - Setup, error handling, edge cases?
5. Risk - External dependencies, technical unknowns?

Respond with:
- APPROVED or NEEDS_REVISION
- Top 3-5 recommendations (if NEEDS_REVISION)
- Suggested modifications as JSON patches to task-list.json
" 2>&1
```

### 修正の適用

NEEDS_REVISION の場合、リーダーが codex の提案を反映して task-list.json を更新し、再度 0-4 を実行する。codex の提案をそのまま適用するのではなく、リーダーが妥当性を判断してから適用する。

---

## レビュー・フィードバックループの詳細（Phase 2）

最終Waveに**必ずレビュワー**を配置する。レビュワーは改善候補を構造化して SendMessage で報告し、リーダーが AskUserQuestion でユーザーに提示する。

### フロー

```
Phase 1 完了（最終Wave = レビュワー）
  ↓
レビュワーが改善候補リストを SendMessage で報告
  例: ["トーンが敬語でない", "Tailwind v4記法の不統一", "EvidenceSection未実装"]
  ↓
AskUserQuestion でユーザーに提示
  Q: レビュワーから以下の改善候補が挙がりました。対応しますか？
  - 候補1: {改善内容}
  - 候補2: {改善内容}
  - 対応不要（完了へ進む）
  ↓
対応あり → Phase 0-2 に戻る
  - story-analysis.json / task-list.json を更新
  - 新Wave のエージェントをスポーン → Phase 1-3 から再実行
  ↓
対応なし → Phase 3（クリーンアップ）へ
```

### レビュワーの報告フォーマット

レビュワーの `customDirective` に以下を含める:

```
レビュー完了後、改善候補を以下の形式で報告してください:
1. [重要度: 高/中/低] 改善内容の簡潔な説明
2. [重要度: 高/中/低] ...

改善候補がない場合は「改善候補なし」と報告してください。
```

### ループ制限

最大3ラウンド。超過時はユーザーに継続可否を確認。

---

## 実装タスクリスト

### Phase A: ファイル構造とスクリプトの準備

- [ ] [TASK] `references/role-catalog.md` 新規作成（Webアプリ開発汎用ロール: 実装系4 + 設計系3 + 品質系2 + 調査系1）
- [ ] [TASK] `references/templates/` にテンプレート雛形を作成:
  - `story-analysis.template.json`（teamDesign セクション付き）
  - `task-list.template.json`（waves + roles + taskPrompt）
- [ ] [TASK] `scripts/init-team-workspace.sh` 作成（クリーンアップ + テンプレートコピー）

### Phase C: エージェントプロンプト統一

- [ ] [TASK] `agent-prompt-template.md` 改訂（ロール変数 + 越境防止 + 入出力フィールド）
- [ ] [TASK] `agent-prompt-template-tdd.md` 廃止（tdd-developer ロールに統合）

### Phase D: SKILL.md 改訂

- [ ] [TASK] Phase 0（計画フェーズ）新設: 0-0 ~ 0-5
- [ ] [TASK] Phase 1 改訂: Wave式スポーン（候補3）
- [ ] [TASK] Phase 2 改訂: レビュー・フィードバックループ（候補6+8）
- [ ] [TASK] 変数一覧テーブル更新

### Phase E: 検証

- [ ] [TASK] 実際のタスクで試行実行（ドライラン）
