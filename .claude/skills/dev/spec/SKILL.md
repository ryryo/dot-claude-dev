---
name: dev:spec
description: 自己完結した実装仕様書を作成する。Gate 単位で Goal / Constraints / Acceptance Criteria を契約として明示し、実装エージェントに委任できる形で渡す。Trigger: 仕様書を作成, /dev:spec, 実装計画, 実装仕様
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

## ゴール

**「Claude を有能なエンジニアとして委任できる」契約書としての仕様書**を作成する。

v3 の規律:

- 詳細な実装手順（impl）は書かない。エンジニアが自律的に決められるようにする
- 各 Gate に **Goal / Constraints / Acceptance Criteria** を明示する
- AC は「何が成立しているか」を検証可能な形で書く（コマンド・テスト・手動操作 何でも可）
- Todo は粒度の合意と影響範囲の明示にとどめる（軽量化）

## 出力

| ファイル                                | 内容                                                                             |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| `docs/PLAN/{YYMMDD}_{slug}/spec.md`     | 概要・背景・設計決定・アーキテクチャ・generated タスクリスト（Gate 契約 + Todo） |
| `docs/PLAN/{YYMMDD}_{slug}/tasks.json`  | schema v3 の構造化データ（Gate 契約 + Todo + Preflight）                         |
| `docs/PLAN/{YYMMDD}_{slug}/references/` | 参照資料（必要な場合のみ）                                                       |

---

## ★ 実行手順

### Step 1: コンテキスト収集

1. 直前の会話から仕様書の対象タスクを特定する。特定できないときのみ AskUserQuestion で確認
2. CLAUDE.md を Read してプロジェクト構成・技術スタックを把握する
3. 関連ドキュメント・コードを Glob / Grep / Read で探索する

### Step 2: 要件の深掘り

以下 4 項目を判定する:

| 判定項目     | 基準                                         |
| ------------ | -------------------------------------------- |
| 技術選定     | 主要な技術的意思決定が確定しているか         |
| スコープ     | 変更範囲が明確か（含む／含まないの境界）     |
| データフロー | コンポーネント間のデータ受け渡しが定義済みか |
| エッジケース | エラーハンドリング・境界条件の方針があるか   |

- **2 項目以上が未確定** → `/dev:dig` を実行して解消
- **1 項目以下が未確定** → Step 3 へ進む

### Step 3: Gate 設計と契約化

仕様書の中核。**Gate 単位で契約を組み立てる** ことで、後段の実装エージェントが詳細手順なしで動ける状態にする。

1. 機能を **検証可能な単位** で Gate に分割する
   - 1 Gate = 「これが満たされれば次に進める」と人間が確信できる粒度
   - 通常 1 Gate = 1-3 時間の実装ボリューム
2. 各 Gate に以下を定義する:
   - **Goal**: `what`（何を達成するか 1-2 文） + `why`（設計上の意図）
   - **Constraints**: `must` / `mustNot` の配列（採用技術・整合性ルール・破壊禁止対象等）
   - **Acceptance Criteria**: 検証可能な受け入れ基準のリスト
3. AC の書き方:
   - 「実装したか」ではなく **「結果として何が成立しているか」** を書く
   - 形式は自由（タスクの種類による）。例:
     - コマンド出力: `bun run type-check が 0 errors`
     - テスト: `bun test path/to/file が GREEN`
     - HTTP: `GET /api/x が 200 を返し JSON {a, b} を含む`
     - ブラウザ: `/xxx を開くと yyy が表示される（手動）`
     - ファイル: `.env.example に NEW_KEY が記載されている`
4. Gate 間の依存関係（前 Gate 通過が次の前提）を `dependencies` に書く

### Step 4: Todo 分解

各 Gate の AC を満たすために必要な Todo を列挙する。

- Todo は **粒度の合意 + 影響範囲の明示** に絞る（impl は書かない）
- フィールド: `id` / `gate` / `title` / `tdd` / `dependencies` / `affectedFiles`
- **`[TDD]` ラベル**: 入出力が明確でアサーション検証可能な Todo に付与（`tdd: true`）
- **`[SIMPLE]` ラベル**: 数行追加・import 追加・定数追加・既知パターンの 1 箇所適用などの軽微な変更で完結する Todo に付与（title 先頭に `[SIMPLE]`）
- 両ラベルは通常排他的だが、必要なら両方付与可

### Step 5: Preflight 抽出

sandbox では実行不可能な処理（3 カテゴリのみ）を Preflight として抽出する。

- **ネットワーク必須**: `npm/pnpm/yarn/bun/pip install`、`uv sync`、`npx create-*`、`git clone`、`curl`、リモート API
- **ワークスペース外書き込み**: `brew install`、`apt install`、`cargo install`、グローバル npm、`~/.zshrc` 編集
- **対話必須**: `gh auth login`、`gcloud auth login`、OAuth フロー、パスワードプロンプト

抽出しないもの: `prisma generate` などのローカル生成、ローカル DB マイグレーション、テスト実行。

各項目に `id` / `title` / `command` / `manual` / `reason` / **`ac`**（完了確認の Acceptance Criteria）を設定する。

該当なし → Preflight セクション全体を省略。

### Step 6: ファイル作成（authored → tasks.json → generated 同期）

1. `date +%y%m%d` で日付を取得
2. AskUserQuestion で `slug` を確定
3. `mkdir -p docs/PLAN/{YYMMDD}_{slug}` でディレクトリを作成
4. **spec.md authored 部分作成**: `references/templates/spec-template-dir.md` を Read し、authored セクションのみ Write
   - Gate 0（`/dev:spec-run` 参照） / 概要 / 背景 / 設計決定事項 / アーキテクチャ詳細 / 変更対象ファイル / 参照すべきファイル / レビューステータス / 残存リスク
   - Preflight がある場合は Gate 0 直後にチェックリストを出力
   - 「タスクリスト」セクションは `<!-- generated:begin -->` / `<!-- generated:end -->` マーカーのみ置き、内部は **空** にする
   - 実装手順は **書かない**
5. **tasks.json 作成**: `references/templates/tasks.template.json` を Read し、`schemaVersion: 3` で Write
   - `spec.slug`, `spec.title`, `spec.summary`（1-2 文）, `spec.createdDate`（YYYY-MM-DD）
   - `status: "not-started"`, `reviewChecked: false`
   - `preflight[]`: 各項目に `id` / `title` / `command` / `manual` / `reason` / `ac` / `checked: false`
   - `gates[]`: 各 Gate に `id` / `title` / `summary` / `dependencies` / `goal{what,why}` / `constraints{must,mustNot}` / `acceptanceCriteria[]`（各 AC は `id`/`description`/`checked: false`） / `todos[]`（軽量フィールドのみ） / `review: null` / `passed: false`
   - `progress` / `metadata` は **書かない**（dashboard で動的計算するため tasks.json には保持しない）
6. **generated 領域の同期**: tasks.json の Edit/Write で PostToolUse hook が `sync-spec-md.mjs` を自動発火する。hook 環境外の場合は明示実行:
   ```bash
   node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
   ```

### Step 7: 外部参照資料の同梱

仕様書内で参照しているファイルのうち、作業エージェントがアクセスできないものを `references/` に同梱する。

| 条件                          | アクション                        |
| ----------------------------- | --------------------------------- |
| 他リポジトリ 内               | `cp` でコピー                     |
| 外部 API ドキュメント         | 要点を markdown で新規作成        |
| 会話中の API 仕様・データ構造 | リファレンス markdown を新規作成  |
| 特定 SDK 依存の設計           | 必要な API パターンを markdown 化 |

同梱後:

1. ファイル内に元リポジトリの相対パスが残っていないか Grep で確認 → 該当箇所に注記
2. 仕様書側の参照パスを `references/` 内パスに書き換え

### Step 8: レビュー

→ `agents/plan-reviewer.md` を Read して Agent に委譲。

レビュー観点（v3 ベース、詳細は `agents/plan-reviewer.md`）:

1. **Gate 契約の質** — Goal/Constraints/AC が委任可能な水準で書かれているか
2. **AC の検証可能性** — 機械検証 / 人手確認のどちらでも判定可能か
3. **タスク粒度** — Gate 1-3 時間、Todo が単一責任
4. **依存関係** — 順序が正しく循環依存がない
5. **参照の完全性** — 外部参照が同梱済みでパスが正しい
6. **漏れ** — セットアップ・エラーハンドリング・テストが抜けていない
7. **意味的整合性** — Gate 契約と spec.md の設計決定 / アーキテクチャに矛盾がない

NEEDS_REVISION の場合は AskUserQuestion で修正方針を確認し、最大 2 回ループ。

### Step 9: ユーザー最終確認

仕様書完成を報告し、AskUserQuestion で次のアクションを確認:

- **コミット** → `/dev:simple-add` でコミット
- **修正** → 指示に従い修正
- **実装へ進む** → `/dev:spec-run` で仕様書を実行

---

## 完了条件

- [ ] 冒頭に Gate 0（`/dev:spec-run` 参照）が記述されている
- [ ] 仕様書内の全参照ファイルがコードベース内パスで解決可能
- [ ] 外部参照は `references/` にコピー済み、パスも修正済み
- [ ] Gate 間の依存関係が依存関係図に図示されている
- [ ] 全 Gate に `goal{what, why}` / `constraints{must, mustNot}` / `acceptanceCriteria[]` が設定されている
- [ ] 全 AC が **検証可能な記述** になっている
- [ ] レビューが完了（APPROVED or ユーザー判断で続行）
- [ ] ユーザーが承認済み
- [ ] `docs/PLAN/{YYMMDD}_{slug}/spec.md` が存在する
- [ ] `docs/PLAN/{YYMMDD}_{slug}/tasks.json` が存在する
- [ ] tasks.json の `schemaVersion` が **3** である
- [ ] tasks.json の各 Todo が軽量フィールドのみ（`impl` を持たない）
- [ ] spec.md に `<!-- generated:begin -->` ... `<!-- generated:end -->` マーカーが存在し、内容が tasks.json と同期している

## 参照

- `references/templates/tasks.template.json` — schema v3 雛形
- `references/templates/tasks-schema-v3.md` — schema 仕様書
- `references/templates/spec-template-dir.md` — spec.md テンプレート
- `agents/plan-reviewer.md` — レビューエージェント
- `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` — generated 領域の自動生成
- `/dev:spec-run` — 仕様書実行プロトコル
- `/dev:dig` — Step 2 で要件の深掘りに使用
