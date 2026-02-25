---
name: dev:epic
description: |
  フィーチャー全体の設計・ストーリー分割を行い、PLAN.md と plan.json を生成。
  ストーリー駆動開発フローと統合し、dev:story の上位レイヤーとして機能する。
  各ストーリーに executionType とフェーズを付与し、実行計画を構造化する。

  Trigger:
  フィーチャー計画, エピック作成, 全体設計, /dev:epic
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

# フィーチャー計画（dev:epic）

## エージェント委譲ルール

**⚠️ 分析・slug解決は必ずTaskエージェントに委譲する。自分で実行しない。**

呼び出しパターン（全ステップ共通）:
```
agentContent = Read(".claude/skills/dev/epic/agents/{agent}.md")
Task({ prompt: agentContent + 追加コンテキスト, subagent_type: "general-purpose", model: {指定モデル} })
```

| Step | agent | model | 追加コンテキスト |
|------|-------|-------|-----------------|
| 2 | resolve-feature-slug.md | haiku | ユーザーのフィーチャー要件 + 既存 feature 一覧 |
| 4 | analyze-epic.md | opus | ユーザーのフィーチャー要件 + 確定slug + 配置済み PLAN.md |

## 出力先

`docs/FEATURES/{feature-slug}/` に2ファイルを保存する。

| ファイル | 用途 |
|----------|------|
| `PLAN.md` | 人間用の設計ドキュメント（ストーリー一覧 + フェーズ別実行計画） |
| `plan.json` | 構造化データ（stories 配列、executionType、依存関係、優先度） |

---

## ★ 実行手順（必ずこの順序で実行）

### Step 1: フィーチャー要件の聞き取り

1. ユーザーからフィーチャーの要件を聞き取る（引数 or 対話）
   - 何を実現したいか
   - 背景・動機
   - スコープ（含む / 含まない）

要件が不明確な場合は AskUserQuestion で段階的にヒアリング。

### Step 2: feature-slug 解決

1. → **エージェント委譲**（resolve-feature-slug.md / haiku）
   - フィーチャー要件から slug 候補を3つ生成
   - 既存 feature との重複チェック
   - 推奨順位付きで返却
2. **AskUserQuestion** で feature-slug をユーザーが最終確定（resolve の推奨順で選択肢提示）

### Step 3: ワークスペース初期化

1. ワークスペース初期化スクリプトを実行:
   ```bash
   bash .claude/skills/dev/epic/scripts/init-feature-workspace.sh {feature-slug}
   ```
   → `docs/FEATURES/{feature-slug}/` に PLAN.md（テンプレート）と plan.json（テンプレート）が配置される

**ゲート**: PLAN.md と plan.json のテンプレートが配置されていなければ次に進まない。

### Step 4: フィーチャー分析・ストーリー分割

1. 配置済みの PLAN.md を Read:
   ```
   Read("docs/FEATURES/{feature-slug}/PLAN.md")
   ```
2. → **エージェント委譲**（analyze-epic.md / opus）
   - 配置済み PLAN.md の構成に従って内容を生成
   - ストーリー一覧（executionType 付き）を生成
   - plan.json の内容を生成
3. **Write** で `PLAN.md` を上書き保存（生成内容で更新）
4. **Write** で `plan.json` を上書き保存（生成内容で更新）

**ゲート**: analyze-epic の出力に PLAN.md 内容と plan.json 内容が含まれなければ保存しない。

### Step 5: ユーザー確認

1. PLAN.md の概要とストーリー一覧をユーザーに提示
2. AskUserQuestion で確認:
   - **承認** → 完了。dev:story で個別ストーリーの詳細化へ
   - **修正が必要** → ユーザー指示に従い修正 → Step 4 から再実行

---

## executionType の定義

各ストーリーに付与する実行方法の分類:

| executionType | 意味 | 実行方法 |
|---------------|------|----------|
| `manual` | ユーザーが手動で実行 | ダッシュボード設定、外部サービス操作など。PLAN.md に手順を記載 |
| `developing` | dev:developing で実装 | dev:story → task-list.json → dev:developing のフルフロー |
| `coding` | AI で通常コーディング | dev:story 不要。直接コーディングで対応 |

判定基準:
- **developing**: ビジネスロジック、UI、テスト可能な機能 → TDD/E2E/TASK 分類が意味を持つもの
- **manual**: 外部サービスの操作、GUI での設定、人間の判断が必要なもの
- **coding**: 設定ファイル追加、定型的なコード変更など、タスク分解するほどでもないもの

---

## 完了条件

以下2ファイルがすべて保存されていること:

| ファイル | Step |
|----------|------|
| `PLAN.md` | Step 3（テンプレート配置） → Step 4（内容生成・上書き） |
| `plan.json` | Step 3（テンプレート配置） → Step 4（内容生成・上書き） |

- 各ストーリーに `executionType` が付与されている
- ユーザーが承認済み

## 参照

- agents/: analyze-epic.md, resolve-feature-slug.md
- scripts/: init-feature-workspace.sh
- references/templates/: plan.template.json, PLAN.template.md
