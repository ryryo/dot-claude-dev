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
| `PLAN.md` | 人間用の設計ドキュメント（ストーリー一覧 + フェーズ別ストーリー詳細） |
| `plan.json` | 構造化データ（stories 配列、executionType、依存関係、技術詳細） |

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

### Step 4: 構造計画（"what" レベル）

Step 1 で把握した要件・調査結果を元に、ストーリー構成とフェーズ構造を策定する。

#### 書くもの

**PLAN.md**:
- 概要、背景、変更内容、影響範囲
- ストーリー一覧テーブル（#、ストーリー名、executionType、Phase、依存、状態）
- Phase 見出し + ストーリー名（詳細ブロックは空のまま — Step 5 で埋める）

**plan.json**:
- feature 情報（slug, title, description）
- stories 配列（基本属性のみ: slug, title, description, executionType, phase, dependencies, status）
  - 詳細フィールド（acceptanceCriteria, affectedFiles, testImpact, newDependencies, technicalNotes, referenceImplementation）は空配列のまま
- phases 配列

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

**ゲート**: PLAN.md にストーリー一覧テーブルがあり、plan.json の stories 配列が空でないこと。

### Step 5: ストーリー詳細化（"how" レベル）

plan.json の stories を順に処理し、各ストーリーの技術詳細を埋める。

#### 処理手順

1. plan.json の stories 配列を Read で取得
2. 各ストーリーについて **Task（Explore）** でコードベース探索:
   - 影響ファイルを具体パスまで特定（ディレクトリ指定禁止）
   - 隣接する `.test.*` / `.spec.*` を検索
   - `.reference/` 内の参照実装パスの存在確認
   - 新規依存のバージョン確認
3. plan.json の詳細フィールドを埋める:
   - `acceptanceCriteria`: 検証可能な受入条件（「〜できる」「〜が表示される」形式）
   - `affectedFiles`: 具体的ファイルパス + 操作（new/edit）+ 変更内容
   - `testImpact`: テストファイルパス + 状態（既存/新規）+ 対応（更新/新規作成）
   - `newDependencies`: パッケージ名 + バージョン範囲 + 用途
   - `technicalNotes`: API変更、破壊的変更、マイグレーション等の注意事項
   - `referenceImplementation`: `.reference/` 内の具体パス
4. PLAN.md の Phase セクション内の各ストーリーを構造化ブロックに展開（テンプレートの形式に従う）
5. PLAN.md の末尾に「実行コマンド一覧」セクションを生成:
   - `executionType: "developing"` のストーリーごとに `/dev:developing docs/FEATURES/{feature-slug}/{YYMMDD}_{story-slug}/task-list.json` のコマンドを Phase 別に記載
   - `{YYMMDD}` は dev:story 実行時に決まるため、プレースホルダー `{YYMMDD}` のまま記載し、dev:story 実行後にパスが確定する旨を Note で補足する

#### 品質基準

- ファイルパスはディレクトリではなく具体的ファイルまで指定
- acceptanceCriteria は「〜できる」「〜が表示される」等の検証可能な形式
- affectedFiles に隣接テストがある場合 testImpact に必ず含める
- テーブルの該当行がない場合（例: 新規依存なし）はセクションごと省略可

**ゲート**: 全ストーリーで acceptanceCriteria >= 2、affectedFiles >= 1 であること。

### Step 6: プランレビュー

1. → **Task（sonnet）** に委譲（agents/review-plan.md）
   - PLAN.md と plan.json を読み取り、構成・一貫性・詳細度・パス検証をチェック
   - PASS / FAIL + 問題リストを返却
2. FAIL の場合、問題リストを元に PLAN.md / plan.json を修正し、再度レビュー（最大2回）

### Step 7: ユーザー確認

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
- 各ストーリーに `acceptanceCriteria`（2つ以上）と `affectedFiles`（1つ以上）がある
- ユーザーが承認済み

## 参照

- agents/resolve-feature-slug.md — slug 候補生成（Step 2）
- agents/review-plan.md — プランレビュー（Step 6）
- scripts/init-feature-workspace.sh — ワークスペース初期化（テンプレート配置）
