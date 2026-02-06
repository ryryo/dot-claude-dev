# dev:developing エージェントへの OpenCode CLI (gpt-5.3-codex) 導入検討

## 注意書き
この計画書は**分析・推奨レポート**です。実装計画ではありません。ユーザーが導入パターンを選択した後に、実装タスクリストを作成します。

## 概要
dev:developing の5エージェントに対して、OpenCode CLI（gpt-5.3-codex）を導入する価値があるか分析し、推奨パターンを提示する。

## 背景

### OpenCode CLI導入の動機
dev:story と dev:feedback では既にOpenCode CLIを「Claude（実装者）のバイアスを排除するための別AI視点による客観的分析」として活用している。dev:developing のエージェントにも同じ手法を適用できるか検討する。

### 既存の導入パターン

| スキル | Agent | 用途 | 呼び出しタイミング |
|--------|-------|------|-------------------|
| dev:story | plan-review | タスク分解の品質レビュー | タスクリスト生成後（1回） |
| dev:feedback | review-analyze | 実装品質チェック | git diff分析時（1回） |
| dev:feedback | propose-manage | メタ改善分析 | 改善提案時（1回） |

共通特徴:
- **品質ゲート**として1回だけ呼び出す（ループ内ではない）
- **分析・レビュー**に限定（コード生成には使わない）
- **フォールバック機構**あり（`USE_OPENCODE=false` でチェックリストベース手動分析）
- コマンド: `opencode run -m openai/gpt-5.3-codex "{prompt}" 2>&1`

## dev:developing エージェント構成

| Agent | Model | 役割 | 外部CLI | 分析要素 |
|-------|-------|------|---------|---------|
| **tdd-cycle** | sonnet | RED→GREEN→REFACTOR | なし | REFACTORフェーズに分析要素あり |
| **tdd-review** | opus | セルフレビュー + テスト資産管理 | なし | 全体が分析・レビュー |
| **e2e-cycle** | sonnet | UI実装 + agent-browser検証 | agent-browser | IMPL後に分析余地あり |
| **quality-check** | haiku | lint/format/build | プロジェクトツール | 自動化のみ、分析要素なし |
| **simple-add-dev** | haiku | git commit | なし | 操作のみ、分析要素なし |

## 各エージェントの詳細分析

---

### 1. tdd-review (opus) - セルフレビュー + テスト資産管理

#### 現在の動作
- 過剰適合チェック（テスト入力値のハードコード、順序依存、マジックナンバー）
- 抜け道チェック（null/undefined処理漏れ、境界値、型不整合）
- テスト資産評価（HIGH/MEDIUM/LOW分類、冗長テスト簡素化・削除）
- コード品質チェック（読みやすさ、保守性、規約準拠）

#### OpenCode導入候補箇所: 過剰適合・抜け道チェック

**導入方法**: Step 2（レビュー分析）の冒頭で、OpenCode CLIに実装コードとテストコードを渡し、Claudeとは異なる視点で過剰適合・抜け道を分析させる。Opusの分析と併用し、両者の結果を統合して最終判定。

**期待効果**:
- Opusも同じClaude系モデル。tdd-cycleもClaude(sonnet)が書いたコード。Claude同士だと「同じ思考パターンの盲点」を共有するリスクがある
- GPT系モデルは異なる学習データ・推論パターンを持つため、Claudeが見落とすエッジケースを検出できる可能性がある
- dev:feedbackのreview-analyzeと同じ「品質ゲート」の構造。導入パターンが確立済み

**懸念点**:
- Opusの深い分析力は高い。OpenCodeが上回るとは限らない
- 補完的に使う（Opusを置き換えるのではなく追加する）のがベスト
- TDDタスクごとに1回の呼び出しのため、コスト・遅延は許容範囲

**呼び出しタイミング**: TDDタスクごとに1回（tdd-cycle完了後、quality-check前）

#### 推奨プロンプト案

```bash
opencode run -m openai/gpt-5.3-codex "
Analyze this TDD implementation for over-fitting and loopholes:

## Test File
{テストコード}

## Implementation File
{実装コード}

Check:
1. Over-fitting: Is the implementation only optimized for the specific test cases?
   - Hardcoded values that match test inputs
   - Order-dependent logic
   - Magic numbers derived from test data
2. Loopholes: Are there inputs that would bypass the tests?
   - null/undefined handling gaps
   - Missing boundary value checks
   - Type mismatches
3. Test-implementation coupling: Are tests testing behavior or implementation details?

Provide:
- Over-fitting risk (HIGH/MEDIUM/LOW)
- Loophole risk (HIGH/MEDIUM/LOW)
- Specific issues with file:line references
- Missing test cases that should be added
" 2>&1
```

---

### 2. tdd-cycle (sonnet) - RED→GREEN→REFACTOR

#### 現在の動作
- RED: テスト作成（正常系、異常系、境界値） → テストcommit
- GREEN: 最小実装（仮実装→三角測量→明白な実装）
- REFACTOR: チェックリストベースのリファクタリング（SRP、DIP、DRY、YAGNI、命名）

#### OpenCode導入候補箇所: REFACTORフェーズ

**導入方法**: REFACTORフェーズ完了後、リファクタリング結果をOpenCode CLIに渡し、品質を客観的に評価させる。

**期待効果**:
- リファクタリングの「やりすぎ」「やり足りない」を外部視点で検出
- チェックリストでは捉えにくい設計上の問題を発見

**懸念点**:
- TDDサイクルは高速に回すことが重要。毎サイクルの外部API呼び出しは遅延が大きい
- t_wada式TDDのBaby stepsの精神に反する可能性（1サイクルに時間をかけすぎる）
- tdd-reviewで別途レビューされるため、二重チェックになる
- REFACTORフェーズ内で呼ぶよりも、tdd-reviewに任せた方が効率的

**呼び出しタイミング**: TDDサイクルごと（タスク内で複数回発生しうる）

---

### 3. e2e-cycle (sonnet) - UI実装 + agent-browser検証

#### 現在の動作
- Phase 1 (IMPL): UI実装（Props型定義、イベントハンドラ、状態管理、スタイリング、レスポンシブ、アクセシビリティ）
- Phase 2 (AUTO): agent-browserで検証（要素存在、フォーム操作、レスポンシブ3ブレイクポイント）
- 修正ループ: 問題あり → IMPL修正 → AUTO再検証（最大3回）

#### OpenCode導入候補箇所: IMPL後 / AUTO前のコードレビュー

**導入方法**: UI実装完了後、agent-browser検証前に、実装コードのアクセシビリティ・セマンティクス・UXパターンをOpenCode CLIでレビュー。

**期待効果**:
- aria属性の適切性、セマンティックHTMLの正しさを別視点で確認
- agent-browserでは検出しにくい「構造的な」アクセシビリティ問題を事前に発見

**懸念点**:
- agent-browserの視覚的検証で十分な場合が多い
- E2Eサイクルも高速に回したい（修正ループがある）
- UIコードの品質はquality-check（lint）でもカバーされる
- 導入効果がTDDレビューと比べて限定的

**呼び出しタイミング**: E2Eタスクごとに1回（IMPLループ収束後、quality-check前）

---

### 4. quality-check (haiku) - lint/format/build

**導入の余地: なし**

理由: ESLint、Prettier、TypeScriptコンパイラなどのプロジェクトツールを実行するだけの純粋な自動化エージェント。判断・分析の要素がなく、OpenCode CLIの「別視点による客観分析」の恩恵を受ける箇所がない。

---

### 5. simple-add-dev (haiku) - git commit

**導入の余地: なし**

理由: git add / git commit を実行するだけのオペレーションエージェント。分析要素がない。

---

## 推奨マトリクス

| Agent | 推奨度 | 導入箇所 | 期待効果 | 呼び出し頻度 | 遅延影響 |
|-------|--------|---------|---------|-------------|---------|
| **tdd-review** | ★★★★☆ | 過剰適合・抜け道チェック | Claude同士の盲点を排除 | TDDタスクごとに1回 | 低 |
| **tdd-cycle** | ★★★☆☆ | REFACTORフェーズ | リファクタ品質の客観評価 | TDDサイクルごと（複数回） | 高 |
| **e2e-cycle** | ★★☆☆☆ | IMPL後のUXレビュー | アクセシビリティ改善 | E2Eタスクごとに1回 | 中 |
| **quality-check** | - | なし | - | - | - |
| **simple-add-dev** | - | なし | - | - | - |

### 評価基準の補足

- **推奨度**: 導入効果とコストのバランス
- **呼び出し頻度**: 「タスクごとに1回」は既存パターンと一致し効率的。「サイクルごと」は頻度が高くコスト増
- **遅延影響**: OpenCode CLI呼び出しは数秒〜十数秒。高頻度だとワークフロー全体に影響

## 推奨パターン

### パターンA: tdd-reviewのみ導入（推奨）

```
tdd-cycle(sonnet) → tdd-review(opus + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
```

**選定理由**:
1. 最も効果的: テストと実装の関係分析は「別AI視点」が特に有効な領域
2. コスト最小: TDDタスクごとに1回のみ呼び出し
3. 既存パターンと一致: dev:feedbackのreview-analyzeと同じ「品質ゲート」の位置づけ
4. 既存のOpus分析を置き換えるのではなく補完する
5. tdd-cycleの高速サイクルを阻害しない

**変更量**: tdd-review.md 1ファイルのみ

---

### パターンB: tdd-review + tdd-cycle

```
tdd-cycle(sonnet + OpenCode@REFACTOR) → tdd-review(opus + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
```

**追加効果**:
- REFACTORフェーズの品質がさらに向上
- 設計レベルの問題を早期に検出

**追加リスク**:
- TDDサイクルが遅くなる（Baby stepsの精神に反する可能性）
- tdd-reviewとの二重チェックによるコスト増
- 1タスクで複数回呼び出しが発生

**変更量**: tdd-cycle.md + tdd-review.md の2ファイル

---

### パターンC: tdd-review + e2e-cycle

```
TDD: tdd-cycle(sonnet) → tdd-review(opus + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
E2E: e2e-cycle(sonnet + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
```

**追加効果**:
- E2EタスクでもOpenCodeの恩恵を受けられる
- アクセシビリティの品質向上

**追加リスク**:
- agent-browserとの二重チェック
- E2Eタスクの実行時間増加
- TDDとE2Eで異なるOpenCode導入パターンになり複雑化

**変更量**: tdd-review.md + e2e-cycle.md の2ファイル

---

### パターンD: 全候補に導入（tdd-review + tdd-cycle + e2e-cycle）

```
TDD: tdd-cycle(sonnet + OpenCode@REFACTOR) → tdd-review(opus + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
E2E: e2e-cycle(sonnet + OpenCode) → quality-check(haiku) → simple-add-dev(haiku)
```

**追加効果**: 最大限の品質向上

**追加リスク**: 最大限のコスト増・遅延。過剰品質チェックによる開発速度低下。

**変更量**: tdd-cycle.md + tdd-review.md + e2e-cycle.md の3ファイル

---

## パターン比較サマリー

| | A (推奨) | B | C | D |
|---|---------|---|---|---|
| **対象** | tdd-review | tdd-review + tdd-cycle | tdd-review + e2e-cycle | 全3エージェント |
| **変更ファイル数** | 1 | 2 | 2 | 3 |
| **OpenCode呼び出し/TDDタスク** | 1回 | 2回以上 | 1回 | 2回以上 |
| **OpenCode呼び出し/E2Eタスク** | 0回 | 0回 | 1回 | 1回 |
| **TDDサイクル速度への影響** | なし | あり（遅延） | なし | あり（遅延） |
| **既存パターンとの整合性** | 高 | 中 | 高 | 中 |
| **推奨度** | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ |

## リスク・考慮事項

| リスク | 影響度 | 対策 |
|--------|--------|------|
| OpenCode CLI未インストール環境 | 低 | フォールバック機構を実装（既存パターンを踏襲） |
| API呼び出しのレイテンシ | 中 | 品質ゲート位置（ループ外）に限定することで影響を最小化 |
| gpt-5.3-codexのレスポンス品質 | 低 | Opusの分析を主、OpenCodeを補完として扱う。OpenCodeの結果のみで判断しない |
| コスト増 | 低〜中 | パターンAなら1タスク1回。パターンB/Dはサイクル回数に比例 |
| 過剰品質チェック | 中 | 開発速度とのバランスを監視。過剰なら無効化（`USE_OPENCODE=false`） |

## タスクリスト

**ユーザーがパターンを選択した後に作成します。**

選択肢:
- [ ] パターンA: tdd-reviewのみ導入（推奨）
- [ ] パターンB: tdd-review + tdd-cycle
- [ ] パターンC: tdd-review + e2e-cycle
- [ ] パターンD: 全候補に導入
- [ ] 導入見送り
