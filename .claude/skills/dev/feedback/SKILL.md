---
name: dev:feedback
description: |
  実装完了後、学んだことをDESIGN.mdに蓄積。スキル/ルールの自己改善を提案。
  ストーリー駆動開発の終点。
  「フィードバック」「/dev:feedback」で起動。

  Trigger:
  フィードバック, 学習事項蓄積, /dev:feedback, feedback, design update
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# フィードバック → 仕様書蓄積（dev:feedback）

## 出力先

| ファイル | Step |
|----------|------|
| `docs/FEATURES/{feature-slug}/DESIGN.md` | 2a |
| `docs/FEATURES/DESIGN.md` | 2a |
| `docs/FEATURES/{feature-slug}/IMPROVEMENTS.md` | 3 |

---

## 実行手順（必ずこの順序で実行）

### Step 0: SELECT（対象計画の選択）

`docs/FEATURES/` 配下を走査し、ユーザーにフィードバック対象を選ばせる。

#### 0a: feature 選択

1. `Glob("docs/FEATURES/*/")` で feature ディレクトリ一覧を取得
2. feature が **1つだけ** → 自動選択（確認メッセージのみ出す）
3. feature が **2つ以上** → **AskUserQuestion** で選択させる
   - 各 option: `{ label: "{feature-slug}", description: "docs/FEATURES/{feature-slug}" }`
4. 選択結果を `feature-slug` として保持

#### 0b: story 選択

1. `Glob("docs/FEATURES/{feature-slug}/stories/*/story-analysis.json")` で story 一覧を取得
2. 各 `story-analysis.json` を Read し、`story.title`（または `story` フィールド）を取得して選択肢の description に使う
3. story が **1つだけ** → 自動選択
4. story が **2つ以上** → **AskUserQuestion** で選択させる
   - 各 option: `{ label: "{story-slug}", description: story.title }`
5. 選択結果を `story-slug` として保持

**ゲート**: `feature-slug` + `story-slug` が確定

---

### Step 1: REVIEW（品質ゲート + 変更分析）

references/review-analyze.md を参照し、git diff を分析して品質ゲート判定 + 分析JSONを作成する。

1. git diff main...HEAD で差分を取得
2. OpenCode CLI（または手動チェックリスト）で実装レビュー
3. 変更内容を分析し、学習事項を抽出 → 分析JSON
4. レビュー結果をユーザーに提示
5. Critical issuesがあれば → **AskUserQuestion** で次のアクションを確認:
   - `/plan-doc` で修正計画書を作成（別スレッドで修正作業）
   - `/dev:story` で修正タスクリストを生成（別スレッドで修正作業）
   - そのまま続行（軽微な場合）

**ゲート**: レビュー + 分析JSON完了

### Step 2: DESIGN（DESIGN.md更新 + 整理）

#### 2a: 機能DESIGN.md + 総合DESIGN.md更新

references/update-design.md を参照し、Step 1 の分析結果を元に DESIGN.md を更新する。

1. 既存の DESIGN.md を Read（なければ新規作成）
2. `docs/FEATURES/{feature-slug}/DESIGN.md` に追記・保存
3. `docs/FEATURES/DESIGN.md` に重要な判断を追記

#### 2b: 総合DESIGNの整理

1. → **Task（opus）** に委譲（code-simplifier スキル）
2. 整理観点:
   - 用語・表現の一貫性
   - セクション構造の論理性
   - 冗長さの排除
   - 将来の追記性

**ゲート**: 機能DESIGN.md + 総合DESIGN.md更新完了

### Step 3: IMPROVE（ルール化検討 + CLAUDE.md更新 + テスト管理）

references/propose-manage.md を参照し、Step 1-2 の結果からルール化候補・CLAUDE.md更新候補を検討して IMPROVEMENTS.md を Write する。

1. 既存ルール一覧を `Glob(".claude/rules/**/*.md")` で収集、CLAUDE.md を Read
2. OpenCode CLI（またはフォールバック基準）で改善分析
3. 候補ごとに具体的な当てはめ先（`.claude/rules/{category}/{name}.md` or `CLAUDE.md` の該当セクション）を明記
4. `docs/FEATURES/{feature-slug}/IMPROVEMENTS.md` に保存
5. TDDタスクがあった場合:
   - → **AskUserQuestion** でテスト整理方針を確認（整理する/すべて保持/スキップ）
   - 選択に応じてテストの簡素化・削除を実行

---

## 完了条件

- [ ] feature-slug + story-slug が確定した（Step 0）
- [ ] 実装レビュー + 変更分析が完了した（Step 1）
- [ ] 機能DESIGN.mdが更新された（Step 2a）
- [ ] 総合DESIGN.mdが更新・整理された（Step 2a + 2b）
- [ ] ルール化候補・CLAUDE.md更新候補が検討された（Step 3）
- [ ] テスト資産が整理された（TDD時）（Step 3）

## 参照

- agents/: code-simplifier（Step 2b 委譲先）
- references/: review-analyze.md, update-design.md, propose-manage.md
