# dev:* スキル群 コンテキスト効率改善計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。

## 概要

`dev:epic` で発覚した「エージェント委譲によるコンテキスト断絶」問題が、`/home/ryryo/dot-claude-dev/.claude/skills/dev/` 配下の他スキルにも存在しないか調査し、同様の問題があれば修正する。

## 背景

`dev:epic` の実行中に以下の問題が判明した:

1. **Explore エージェントの調査結果が後続エージェントに引き継がれない**: メインコンテキストに蓄積された調査結果を、別エージェント（analyze-epic）に渡すためにプロンプトへテキストコピーする必要があり、コンテキストの無駄が発生
2. **メインコンテキストに情報があるのにエージェント委譲する意味が薄い**: 直接メインで実行した方が速く、情報ロスもない

`dev:epic` では Step 4（フィーチャー分析・ストーリー分割）のエージェント委譲を廃止し、メイン直接実行に変更済み。

### エージェント委譲の判定基準

| 委譲が逆効果 | 委譲が適切 |
|-------------|-----------|
| メインコンテキストに既に情報がある場合 | メインコンテキストの情報が不要な独立タスク |
| 前ステップの出力を次ステップで使う場合 | 並列実行で効率化できるタスク |
| 調査結果をプロンプトにコピーする必要がある場合 | メインコンテキストを汚したくない大量探索 |
| | メインが作成した成果物を別視点でレビューする場合 |

#### 委譲が適切な具体例

- **slug 候補生成**: メインコンテキスト不要、haiku で十分 → `agents/resolve-feature-slug.md`
- **プランレビュー**: 配置済みファイルを読めば完結、メインとは別視点でチェック → `agents/review-plan.md`

いずれも `dev:epic` での実例。参照: `.claude/skills/dev/epic/agents/`

## 変更内容

### Phase 1: 調査

各スキルの SKILL.md を読み、エージェント委譲パターンを洗い出す。以下の観点で問題を判定:

- **Step 間コンテキスト断絶**: 前 Step の出力（ヒアリング結果、調査結果、分析結果）を次 Step のエージェントに渡す際、プロンプトへのコピーが必要になっていないか
- **不要な委譲**: メインコンテキストで直接実行した方が効率的なケース

対象スキル:

| スキル | ファイル |
|--------|---------|
| dev:ideation | `.claude/skills/dev/ideation/SKILL.md` |
| dev:story | `.claude/skills/dev/story/SKILL.md` |
| dev:developing | `.claude/skills/dev/developing/SKILL.md` |
| dev:feedback | `.claude/skills/dev/feedback/SKILL.md` |
| dev:opencode-check | `.claude/skills/dev/opencode-check/SKILL.md` |
| dev:cleanup-branches | `.claude/skills/dev/cleanup-branches/SKILL.md` |
| dev:agent-browser | `.claude/skills/dev/agent-browser/SKILL.md` |

### Phase 2: 修正

調査で問題が見つかったスキルに対し、SKILL.md を**構造から再構築**する。
「エージェント委譲しないでね」という注意書きを追加するのではなく、そもそもそんな注意が不要なフローにする。

#### 修正方針（dev:epic で確立したパターン）

1. **SKILL.md から「エージェント委譲」という概念を排除**する。各 Step は「何をするか」だけを書く
2. **メインコンテキストの情報を使う Step の agents/ → references/ 移動**。エージェント用プロンプトとしてではなく、仕様書・リファレンスとして整理し直す
3. SKILL.md の Step 記述は「Write で作成する」「AskUserQuestion で確認する」等、**行動を直接書く**

#### メインコンテキスト不要なタスクはエージェント委譲を維持

すべてをメイン直接実行にするわけではない。以下に該当する Step は Task 委譲のままでよい:

- **メインコンテキストの情報が不要**（例: slug 候補生成、定型的なファイル検証）
- **軽量で独立**（haiku で十分な処理）
- **並列実行で効率化できる**

dev:epic の例: Step 2（slug 候補生成）は haiku 委譲を維持。Step 4（PLAN.md 作成）はメイン直接実行に変更。

#### dev:epic での適用例

| Before | After |
|--------|-------|
| `agents/analyze-epic.md`（エージェント用プロンプト） | **削除** → `references/plan-spec.md`（仕様書） |
| Step 4: 「エージェント委譲（analyze-epic.md / opus）」 | Step 4: 「Write で作成する。仕様は references/plan-spec.md 参照」 |
| 「コンテキスト効率ルール」セクション | **不要**（フロー自体が自然なので注意書き不要） |

---

#### スキル別修正方針（Phase 1 調査結果 + ユーザー判断に基づく）

##### 2A. dev:ideation — Step 1 のみメイン化

| Step | Before | After |
|------|--------|-------|
| 0 ヒアリング | メイン実行 | **変更なし** |
| 1 問題定義 | エージェント委譲（problem-definition.md / opus） | **メイン直接実行**。references/problem-definition.md を参照して Write |
| 2 競合分析 | エージェント委譲（competitor-analysis.md / sonnet） | **委譲を維持**（PROBLEM_DEFINITION.md パス渡しで独立） |
| 3 SLC仕様 | エージェント委譲（slc-ideation.md / opus） | **委譲を維持**（2ファイルパス渡しで独立） |

変更点:
- `agents/problem-definition.md` → `references/problem-definition.md` に移動
- 冒頭の「⚠️ 分析・調査・設計は必ずTaskエージェントに委譲する」を削除
- エージェント委譲テーブルから Step 1 を除去
- Step 1 の記述を「Write で作成する。仕様は references/problem-definition.md 参照」に変更

##### 2B. dev:story — Step 1 analyze + Step 2 decompose をメイン化

| Step | Before | After |
|------|--------|-------|
| 1 analyze | エージェント委譲（analyze-story.md / opus） | **メイン直接実行**。references/analyze-story.md を参照 |
| 1b resolve-slug | エージェント委譲（resolve-slug.md / haiku） | **委譲を維持**（haiku、メインコンテキスト不要） |
| 2 decompose | エージェント委譲（decompose-tasks.md / sonnet） | **メイン直接実行**。references/decompose-tasks.md を参照。コード探索もメインで実行 |
| 3 plan-review | エージェント委譲（plan-review.md / sonnet） | **委譲を維持**（成果物を別視点でレビュー） |

変更点:
- `agents/analyze-story.md` → `references/analyze-story.md` に移動
- `agents/decompose-tasks.md` → `references/decompose-tasks.md` に移動
- 冒頭の「⚠️ 分析・分解・分類は必ずTaskエージェントに委譲する」を削除
- Step 1: メインでストーリー分析 → story-analysis.json を Write
- Step 2: メインでコード探索 + タスク分解 → task-list.json を Write
- Step 2 のメイン化により、ユーザーのストーリー情報 + analyze結果がそのまま decompose で使える

##### 2C. dev:feedback — Step 1-3 全てメイン化

| Step | Before | After |
|------|--------|-------|
| 0 SELECT | メイン実行 | **変更なし** |
| 1 REVIEW | エージェント委譲（review-analyze.md / sonnet） | **メイン直接実行**。references/review-analyze.md を参照 |
| 2a DESIGN | エージェント委譲（update-design.md / sonnet） | **メイン直接実行**。references/update-design.md を参照 |
| 2b 整理 | エージェント委譲（code-simplifier / opus） | **委譲を維持**（DESIGN.md パスだけで独立した整理作業） |
| 3 IMPROVE | エージェント委譲（propose-manage.md / sonnet） | **メイン直接実行**。references/propose-manage.md を参照 |

変更点:
- `agents/review-analyze.md` → `references/review-analyze.md` に移動
- `agents/update-design.md` → `references/update-design.md` に移動
- `agents/propose-manage.md` → `references/propose-manage.md` に移動
- 冒頭の「分析・更新・提案は必ずTaskエージェントに委譲する」を削除
- Step 1 の分析結果がメインコンテキストに残るため、Step 2a/3 で自然に利用可能
- Step 2b（code-simplifier）は独立した整理作業なので委譲を維持

##### 2D. dev:developing — 冒頭ルールの矛盾解消

| 箇所 | Before | After |
|------|--------|-------|
| 冒頭ルール | 「各ステップの実行は**必ず**Taskエージェントに委譲する」 | ワークフロー別に委譲/直接実行を明記 |
| TDD/E2E | 全Step委譲 | **変更なし**（実装作業の委譲は適切） |
| TASK | 「SPOT/FIX以外はサブエージェント呼び出しなし」 | **変更なし**（直接実行が明記済み） |

変更点:
- 冒頭の「各ステップの実行は必ずTaskエージェントに委譲する。自分で実装・テスト・レビューしない。」を修正
- TDD/E2E: 実装ステップはエージェント委譲（コーディング作業、独立性あり）
- TASK: EXEC/VERIFY はメイン直接実行、SPOT/FIX のみエージェント委譲
- 矛盾のない記述に統一

### Phase 3: CLAUDE.md ルール更新

調査・修正結果を踏まえ、以下を更新:

- プロジェクトの CLAUDE.md 内「dev:ideation / dev:story / dev:developing / dev:feedback 実行ルール」から「エージェント委譲を厳守」ルールを見直す
- 各スキルの SKILL.md 自体が自然なフローになっていれば、CLAUDE.md 側で委譲ルールを強制する必要がなくなる

## 影響範囲

- **直接変更**: `dev/` 配下の各スキルの SKILL.md
- **間接影響**: これらスキルを参照するプロジェクトの CLAUDE.md 内ルール記述
- **影響なし**: agents/ 配下のエージェント定義ファイル（リファレンスとして残す）、scripts/、templates/

## 実行戦略付きタスクリスト

### Phase 1: 調査

- [x] 1.1 dev:ideation SKILL.md のエージェント委譲パターン調査 → **問題あり**（全Step強制委譲、Step0→1のコンテキスト断絶）
- [x] 1.2 dev:story SKILL.md のエージェント委譲パターン調査 → **問題あり**（Step1 analyze-storyへのコンテキストコピー必要）
- [x] 1.3 dev:developing SKILL.md のエージェント委譲パターン調査 → **要検討**（冒頭ルールとTASKワークフローの矛盾）
- [x] 1.4 dev:feedback SKILL.md のエージェント委譲パターン調査 → **問題あり**（Step1→2a/3のコンテキスト断絶）
- [x] 1.5 dev:opencode-check SKILL.md のエージェント委譲パターン調査 → **問題なし**（委譲なし）
- [x] 1.6 dev:cleanup-branches SKILL.md のエージェント委譲パターン調査 → **問題なし**（委譲なし）
- [x] 1.7 dev:agent-browser SKILL.md のエージェント委譲パターン調査 → **問題なし**（適切な委譲パターン）
- [x] 1.8 調査結果サマリー作成（問題あり/なし/要検討の分類） → 完了

Phase 1 は各スキルの SKILL.md を読んで判定するだけなので、1セッションで一気に実行可能。

### Phase 2: 修正

#### 2A. dev:ideation（Step 1 メイン化）
- [x] 2A.1 `agents/problem-definition.md` → `references/problem-definition.md` に移動
- [x] 2A.2 SKILL.md 再構築: 冒頭の強制委譲ルール削除、Step 1 をメイン直接実行に変更
- [x] 2A.3 動作確認（SKILL.md の整合性チェック）

#### 2B. dev:story（Step 1 analyze + Step 2 decompose メイン化）
- [x] 2B.1 `agents/analyze-story.md` → `references/analyze-story.md` に移動
- [x] 2B.2 `agents/decompose-tasks.md` → `references/decompose-tasks.md` に移動
- [x] 2B.3 SKILL.md 再構築: 冒頭の強制委譲ルール削除、Step 1/2 をメイン直接実行に変更
- [x] 2B.4 動作確認

#### 2C. dev:feedback（Step 1-3 全てメイン化）
- [x] 2C.1 `agents/review-analyze.md` → `references/review-analyze.md` に移動
- [x] 2C.2 `agents/update-design.md` → `references/update-design.md` に移動
- [x] 2C.3 `agents/propose-manage.md` → `references/propose-manage.md` に移動
- [x] 2C.4 SKILL.md 再構築: 冒頭の強制委譲ルール削除、Step 1/2a/3 をメイン直接実行に変更
- [x] 2C.5 動作確認

#### 2D. dev:developing（冒頭ルール矛盾解消）
- [x] 2D.1 冒頭「全て委譲」ルールをワークフロー別の正確な記述に修正
- [x] 2D.2 動作確認

#### 2E. セルフレビュー
- [x] 2E.1 全修正スキルの一貫性確認（dev:epic パターンとの整合性）

### Phase 3: CLAUDE.md ルール更新

- [ ] 3.1 「エージェント委譲を厳守」ルールの見直し・緩和
- [ ] 3.2 CLAUDE.md 内の該当セクション更新

### Phase 4: スキル改善スキルの作成

Phase 1〜3 で確立した「エージェント委譲の適切性判定→修正」パターンを、再利用可能なスキルとして汎用化する。

- [ ] 4.1 スキル仕様設計（入力: 対象SKILL.md、出力: 改善提案と修正）
- [ ] 4.2 SKILL.md 作成（`dev:skill-optimizer` または類似名称）
- [ ] 4.3 セルフテスト（既存スキルに適用して動作確認）

#### スキルの機能

| 機能 | 説明 |
|------|------|
| **不要なエージェント委譲の検出** | メインコンテキストの情報を必要とするのにエージェントに委譲しているStepを検出し、メイン直接実行に変更 |
| **エージェント分割すべき箇所の検出** | メインコンテキスト不要な独立タスクがメインで実行されている場合、エージェント委譲を提案 |
| **修正の実行** | 検出結果に基づき、SKILL.md の再構築（agents/ → references/ 移動、Step記述の直接行動化）を実行 |

#### 判定基準（Phase 1 の知見を組み込み）

- **委譲を取りやめるべき**: 前Stepの出力を次Stepで使う、プロンプトへのコピーが必要、メインコンテキストに既に情報がある
- **委譲すべき**: メインコンテキスト不要な独立タスク、haiku で十分な軽量処理、並列実行で効率化可能、メインの成果物を別視点でレビュー
