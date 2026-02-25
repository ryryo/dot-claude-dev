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

## 出力先

`docs/FEATURES/{feature-slug}/` に2ファイルを保存する。

| ファイル | 用途 |
|----------|------|
| `PLAN.md` | 人間用の設計ドキュメント（ストーリー一覧 + フェーズ別実行計画） |
| `plan.json` | 構造化データ（stories 配列、executionType、依存関係、優先度） |

---

## ★ 実行手順（必ずこの順序で実行）

### Step 1: フィーチャー要件の把握

1. ユーザーからフィーチャーの要件を聞き取る（引数 or 対話）
   - 何を実現したいか
   - 背景・動機
   - スコープ（含む / 含まない）
2. 要件が不明確な場合は AskUserQuestion で段階的にヒアリング
3. 必要に応じて Task（Explore）でコードベース調査を行い、現状を把握する

### Step 2: feature-slug 決定

1. → **Task（haiku）** に委譲（agents/resolve-feature-slug.md）
   - フィーチャー要件から slug 候補を3つ生成
   - 既存 feature との重複チェック（Glob で自動取得）
   - 推奨順位付きで返却
2. **AskUserQuestion** で feature-slug をユーザーが最終確定（推奨順で選択肢提示）

### Step 3: ワークスペース初期化

1. ワークスペース初期化スクリプトを実行:
   ```bash
   bash .claude/skills/dev/epic/scripts/init-feature-workspace.sh {feature-slug}
   ```
   → `docs/FEATURES/{feature-slug}/` に PLAN.md（テンプレート）と plan.json（テンプレート）が配置される

**ゲート**: PLAN.md と plan.json が配置されていなければ次に進まない。

### Step 4: PLAN.md と plan.json の作成

Step 1 で把握した要件・調査結果を元に、Step 3 で配置済みの PLAN.md と plan.json を Read し、その構成に従って Write で上書きする。

#### ストーリーの属性

| 属性 | 形式 | 例 |
|------|------|-----|
| slug | ハイフンケース、英小文字 | `login-form` |
| title | 日本語、20文字以内 | `ログインフォーム` |
| description | 日本語、100文字以内 | `OAuth対応のログインフォームを...` |
| executionType | `manual` / `developing` / `coding` | `developing` |
| phase | フェーズ番号（1〜） | `1` |
| dependencies | 依存する slug の配列 | `["login-form"]` |
| status | 初期値は `pending` | `pending` |

#### ストーリー粒度・フェーズ分割

- 粒度: 「1つの dev:story セッションで完結できる」サイズ
- フェーズ: 依存関係に基づいて分割。同一フェーズ内は並列実行可能

**ゲート**: PLAN.md と plan.json がテンプレートから更新されていなければ次に進まない。

### Step 5: プランレビュー

1. → **Task（sonnet）** に委譲（agents/review-plan.md）
   - PLAN.md と plan.json を読み取り、構成・一貫性・実行可能性をチェック
   - PASS / FAIL + 問題リストを返却
2. FAIL の場合、問題リストを元に PLAN.md / plan.json を修正し、再度レビュー（最大2回）

### Step 6: ユーザー確認

1. PLAN.md の概要とストーリー一覧をユーザーに提示
2. AskUserQuestion で確認:
   - **承認** → 完了。dev:story で個別ストーリーの詳細化へ
   - **修正が必要** → ユーザー指示に従い修正

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

- `docs/FEATURES/{feature-slug}/PLAN.md` が作成されている
- `docs/FEATURES/{feature-slug}/plan.json` が作成されている
- 各ストーリーに `executionType` が付与されている
- ユーザーが承認済み

## 参照

- agents/resolve-feature-slug.md — slug 候補生成（Step 2）
- agents/review-plan.md — プランレビュー（Step 5）
- scripts/init-feature-workspace.sh — ワークスペース初期化（テンプレート配置）
