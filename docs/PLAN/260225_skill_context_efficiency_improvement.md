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

- [ ] 1.1 dev:ideation SKILL.md のエージェント委譲パターン調査
- [ ] 1.2 dev:story SKILL.md のエージェント委譲パターン調査
- [ ] 1.3 dev:developing SKILL.md のエージェント委譲パターン調査
- [ ] 1.4 dev:feedback SKILL.md のエージェント委譲パターン調査
- [ ] 1.5 dev:opencode-check SKILL.md のエージェント委譲パターン調査
- [ ] 1.6 dev:cleanup-branches SKILL.md のエージェント委譲パターン調査
- [ ] 1.7 dev:agent-browser SKILL.md のエージェント委譲パターン調査
- [ ] 1.8 調査結果サマリー作成（問題あり/なし/要検討の分類）

Phase 1 は各スキルの SKILL.md を読んで判定するだけなので、1セッションで一気に実行可能。

### Phase 2: 修正

- [ ] 2.1 問題ありスキルの agents/ → references/ 移動・仕様書化
- [ ] 2.2 問題ありスキルの SKILL.md 再構築（「何をするか」だけのシンプルなフローに）
- [ ] 2.3 修正内容のセルフレビュー（dev:epic の再構築パターンとの一貫性確認）

### Phase 3: CLAUDE.md ルール更新

- [ ] 3.1 「エージェント委譲を厳守」ルールの見直し・緩和
- [ ] 3.2 CLAUDE.md 内の該当セクション更新
