# dev:epic スキル作成計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。

## 概要

フィーチャー全体の設計・ストーリー分割を行う `dev:epic` スキルを新規作成し、`dev:story` に PLAN.md 参照機能を最小限追加する。

## 背景

現状の `dev:story` は個別ストーリーの分析→タスク分解を行うが、フィーチャー全体の設計・ストーリー分割の上位レイヤーがない。
`plan-doc` は汎用的な計画書作成だが、`docs/FEATURES/` のストーリー駆動開発フローとは統合されていない。

この2つを組み合わせ、**フィーチャーレベルの設計 → ストーリー分割 → 個別ストーリー詳細化** という階層を作る。

## 変更内容

### 1. 新規: `dev:epic` スキル

**出力ファイル**: `docs/FEATURES/{feature-slug}/` に以下を生成

| ファイル | 用途 |
|----------|------|
| `PLAN.md` | 人間用の設計ドキュメント（全体設計、背景、変更内容、影響範囲、実行戦略） |
| `plan.json` | 構造化データ（stories配列、依存関係、優先度、メタデータ） |

**PLAN.md の構成**:
- 概要
- 背景
- 変更内容
- 影響範囲
- ストーリー一覧（優先度・依存関係付き）
- 実行戦略（plan-doc のモデル選択基準・実行方式記法を継承）

**plan.json の構成**:
```json
{
  "feature": {
    "slug": "user-auth",
    "title": "ユーザー認証機能",
    "description": "..."
  },
  "stories": [
    {
      "slug": "login-form",
      "title": "ログインフォーム",
      "description": "...",
      "priority": 1,
      "dependencies": [],
      "status": "pending"
    },
    {
      "slug": "social-login",
      "title": "ソーシャルログイン",
      "description": "...",
      "priority": 2,
      "dependencies": ["login-form"],
      "status": "pending"
    }
  ],
  "metadata": {
    "createdAt": "260225",
    "status": "active"
  }
}
```

**ワークフロー**:
1. ユーザーからフィーチャーの要件を聞き取る
2. Opusエージェントで分析（全体設計 + ストーリー分割）
3. AskUserQuestion で feature-slug 確定
4. PLAN.md + plan.json を生成
5. ユーザーに確認 → 承認後、dev:story で個別ストーリーを詳細化

### 2. 既存変更: `dev:story` の最小変更

**変更箇所**: analyze-story.md エージェントまたは SKILL.md の Step 1

**変更内容**:
- Step 1 の冒頭に「PLAN.md チェック」を追加
- `docs/FEATURES/{feature-slug}/plan.json` が存在する場合:
  - feature-slug は確定済みとしてスキップ
  - plan.json の該当 story 情報をコンテキストとして analyze-story に渡す
  - ストーリー分析のスコープが plan.json と整合するようにする
- plan.json が存在しない場合: 従来通りの動作（変更なし）

**dev:developing への変更**: なし

## 影響範囲

| ファイル | 変更種別 |
|----------|----------|
| `.claude/skills/dev/epic/SKILL.md` | **新規作成** |
| `.claude/skills/dev/epic/agents/analyze-epic.md` | **新規作成** |
| `.claude/skills/dev/epic/agents/resolve-feature-slug.md` | **新規作成** |
| `.claude/skills/dev/epic/scripts/init-feature-workspace.sh` | **新規作成** |
| `.claude/skills/dev/epic/references/templates/plan.template.json` | **新規作成** |
| `.claude/skills/dev/story/SKILL.md` | **微修正**（Step 1 に plan.json チェック追加） |
| `.claude/skills/dev/story/agents/analyze-story.md` | **微修正**（plan コンテキスト受け取り追加） |
| `CLAUDE.md` | **更新**（スキル一覧に dev:epic 追加） |

## タスクリスト

### Phase 1: 設計・テンプレート準備
> 並列実行可能

- [ ] plan.json のスキーマ設計 `[BG:haiku:Explore]` — 既存 story-analysis.json / task-list.json との整合確認
- [ ] PLAN.md テンプレート設計 — plan-doc の構成をベースに feature 向けにカスタマイズ

### Phase 2: dev:epic スキル作成

- [ ] SKILL.md 作成 — ワークフロー定義、エージェント委譲ルール
- [ ] analyze-epic.md エージェント作成 — フィーチャー分析 + ストーリー分割ロジック
- [ ] resolve-feature-slug.md エージェント作成 — 既存 feature との重複チェック（resolve-slug.md ベース）
- [ ] init-feature-workspace.sh 作成 — ディレクトリ初期化スクリプト
- [ ] plan.template.json 作成

### Phase 3: dev:story 最小変更

- [ ] SKILL.md の Step 1 に plan.json チェック追加
- [ ] analyze-story.md に plan コンテキスト受け取り追加

### Phase 4: 統合・ドキュメント

- [ ] CLAUDE.md にスキル追加
- [ ] 動作確認（dev:epic → dev:story → dev:developing の一気通貫フロー）

## リスク・考慮事項

- **plan.json と story-analysis.json の情報重複**: plan.json はフィーチャーレベルの粗い情報、story-analysis.json はストーリーレベルの詳細情報と棲み分ける
- **dev:story 単体利用の互換性**: plan.json がない場合は従来通り動作するようにガード条件を入れる
- **plan.json の status 管理**: dev:story 完了時に該当ストーリーの status を更新するかは、将来的な拡張として保留可能
