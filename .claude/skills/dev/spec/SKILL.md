---
name: dev:spec
description: 自己完結した実装仕様書を作成する。別の作業エージェントがこの仕様書だけで実装を完遂できることがゴール。Trigger: 仕様書を作成, /dev:spec, 実装計画, 実装仕様
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

**別の作業エージェントに渡せる自己完結した実装仕様書**を作成する。

自己完結の定義:

- 作業に必要なすべてのコンテキスト（設計判断・コード構造・参照資料）を仕様書内に含む
- 作業エージェントが外部リポジトリや他スキルの知識なしに実装を完遂できる
- ファイルパスがすべてコードベース内で解決可能（外部パスが紛れ込んでいない）

## 出力

| ファイル                                    | 内容                                                                |
| ------------------------------------------- | ------------------------------------------------------------------- |
| `docs/PLAN/{YYMMDD}_{slug}/spec.md`         | 概要・設計決定・アーキテクチャ・依存図・generated タスクリスト・Review 記録 |
| `docs/PLAN/{YYMMDD}_{slug}/tasks.json`      | schema v2 の構造化データ（Gate/Todo/Step 詳細・impl 手順を含む）    |
| `docs/PLAN/{YYMMDD}_{slug}/references/`     | 参照資料（必要な場合のみ）                                          |

---

## ★ 実行手順（この順序を厳守）

### Step 1: コンテキスト収集

1. **会話コンテキストを分析**し、仕様書の対象タスクを特定する
   - 直前の会話で議論されている機能・設計・作業内容があればそれが対象
   - 特定できない場合のみ AskUserQuestion で候補を提示して確認
2. **CLAUDE.md** を Read してプロジェクト構成・技術スタックを把握する
3. **関連ドキュメント・コード**を探索する（Glob, Grep, Read）

### Step 2: 要件の深掘り

以下の 4 項目を判定する:

| 判定項目     | 基準                                         |
| ------------ | -------------------------------------------- |
| 技術選定     | 主要な技術的意思決定が確定しているか         |
| スコープ     | 変更範囲が明確か（含む／含まないの境界）     |
| データフロー | コンポーネント間のデータ受け渡しが定義済みか |
| エッジケース | エラーハンドリング・境界条件の方針があるか   |

- **2 項目以上が未確定** → `/dev:dig` を実行して解消
- **1 項目以下が未確定** → Step 3 へ進む

**ゲート**: 4 項目すべて確定するまで Step 3 に進まない。

### Step 3: タスク分解

仕様書に載せるタスクリストを作成するために `/dev:decomposition` を実行する。

### Step 4: Gate グループ化

タスク分解結果をもとに、関連する Todo を Gate 単位でグループ化する:

- Gate 間は順序依存（前の Gate 通過が次の前提条件）
- Todo の Step 手順・Gate 通過条件・Review 方法は `/dev:spec-run` スキルで定義。仕様書には Gate 0 として参照を記載するだけ
- **`[TDD]` ラベルの判断**: 各 Todo が以下の条件を満たす場合、Todo に `[TDD]` ラベルを付与する:
  - 入出力が明確なロジック（バリデーション、計算、変換、ビジネスロジック等）
  - アサーションで検証可能（`expect(result).toEqual(expected)` のような比較が書ける）
- `[TDD]` ラベルは Todo 単位で付与する。同一 Gate 内で混在可
- `[TDD]` ラベル付き Todo は `dev:spec-run` の実行モードに応じて tdd-developer または codex-tdd-developer で実装する
- **`[SIMPLE]` ラベルの判断**: 各 Todo が以下の条件を満たす場合、Todo に `[SIMPLE]` ラベルを付与する:
  - impl が数行追加・import 追加・定数/文言追加・既知パターンの1箇所適用など軽微な変更のみで完結する（Claude の総合判断。ヒューリスティックの明文化なし）
- `[SIMPLE]` ラベルの付与方法: title の頭に `[SIMPLE]` を付ける。`tasks.json` 側の別フィールドは作らない（`[TDD]` の `tdd:` とは非対称）
- `[SIMPLE]` ラベルの効果: `dev:spec-run` の Codex モードで Codex 委任をスキップし Claude メインセッションが直接実装し、VERIFY も SKIPPED になる。Claude モードでは無視される
- `[SIMPLE]` と `[TDD]` は通常排他的（Claude 判断に委譲。両立が必要なレアケースでは両方付与可）

### Step 5: Preflight 抽出

Step 3/4 で整理したタスク一覧から、**Codex / サブエージェントの sandbox では実行不可能な処理** を Preflight として抽出する。

#### 抽出対象（3 カテゴリのみ）

- **ネットワーク必須** (`network`): `npm/pnpm/yarn/bun/pip install`、`uv sync`、`npx create-*`、`git clone`、`curl`、リモート DB 接続、外部 API 呼び出し
- **ワークスペース外書き込み** (`global-write`): `brew install`、`apt install`、`cargo install`、`pipx install`、グローバル npm、`~/.zshrc` 編集
- **対話必須** (`interactive`): `gh auth login`、`gcloud auth login`、OAuth フロー、パスワードプロンプト

**抽出しないもの**（sandbox で動作するためコード Todo に残す）:

- `prisma generate`、`drizzle-kit generate` 等のローカルコード生成（ネットワーク不要）
- ローカル DB マイグレーション（ローカル Postgres / SQLite）
- `.env` ファイルの作成やコメント編集（値の手動設定が必要な場合のみ Preflight へ）
- テスト実行、lint/format/build（依存導入済みの場合）

#### 処理手順

1. 全 Todo をスキャンし、上記 3 カテゴリに該当する処理を列挙する
2. AskUserQuestion で抽出結果をユーザーに提示し確認する
3. 承認されたものは Gate の Todo ではなく Preflight に移動する:
   - **自動実行可能** (`manual: false`): `command` フィールドに実行コマンドを記述
   - **ユーザー手動操作必須** (`manual: true`): `command` は空、タイトルに具体的な操作手順を記述、表記に `[手動]` を付与
4. 該当がなければ Preflight はスキップ。仕様書に Preflight セクション自体を出力しない

**ゲート**: 抽出対象が 3 カテゴリ外（`prisma generate` 等のローカル完結処理）に及んでいないこと。過剰抽出しない。

### Step 6: 仕様書ドラフト作成

1. `date +%y%m%d` で日付を取得
2. AskUserQuestion で仕様書の slug を確定
3. `mkdir -p docs/PLAN/{YYMMDD}_{slug}` でディレクトリを作成
4. **spec.md 作成**: `references/templates/spec-template-dir.md` を Read し、その構成に従って `docs/PLAN/{YYMMDD}_{slug}/spec.md` に Write
   - 概要・設計決定・アーキテクチャ・依存図・generated タスクリスト（`<!-- generated:begin/end -->` マーカー付き）
   - **Preflight がある場合**: Gate 0 直後に Preflight チェックリストを出力（テンプレートの書式に従う）
   - 実装詳細は **書かない**（tasks.json に格納するため）
5. **tasks.json 作成**: `references/templates/tasks.template.json` を Read し、構造に従って `docs/PLAN/{YYMMDD}_{slug}/tasks.json` に Write
   - `schemaVersion: 2` を設定
   - `spec.slug`, `spec.title`, `spec.summary`（1-2 文）, `spec.createdDate`（YYYY-MM-DD）を設定
   - トップレベル `status: "not-started"`, `reviewChecked: false` を設定
   - **Preflight がある場合**: `preflight` 配列に各項目を格納（`id`, `title`, `command`, `manual`, `reason`）。Preflight がなければ `preflight: []` とする
   - `gates` 配列に全 Gate を格納。各 gate に `id`, `title`, `description`（1 行サマリ）, `dependencies`, `passCondition` を設定
   - `todos` 配列に全 Todo を格納。各 Todo に以下を設定:
     - `id`, `gate`, `title`, `description`（1 行サマリ、dashboard カード用）
     - `tdd: true/false`（`[TDD]` ラベル付き Todo は `true`）
     - `dependencies`, `affectedFiles`, `impl`（実装詳細・コード例を含む完全な手順）, `relatedIssues`
     - `steps`: 必ず 2 要素 `[{kind: "impl", title: "Step 1 — IMPL", checked: false}, {kind: "review", title: "Step 2 — Review", checked: false, review: null}]`
   - `progress`: 全 Todo の steps を合計して `{ completed: 0, total: (2 × todos.length) }` を設定
   - `metadata.createdAt` (ISO 8601), `metadata.totalGates`, `metadata.totalTodos` を設定

### Step 7: 外部参照資料の同梱

仕様書内で参照しているファイルをすべてチェックし、**作業エージェントがアクセスできないもの**を `docs/PLAN/{YYMMDD}_{slug}/references/` に同梱する。

#### 判定基準

| 条件                                          | アクション                         |
| --------------------------------------------- | ---------------------------------- |
| 他リポジトリ / `.reference/` サブモジュール内 | `cp` でコピー                      |
| 外部 API ドキュメント                         | 要点を markdown で新規作成         |
| 会話中の API 仕様・プロトコル定義・データ構造 | リファレンス markdown を新規作成   |
| 特定ライブラリ/SDK の使い方に依存する設計     | 必要なパターン・API を markdown 化 |

#### 同梱後の必須処理

1. **ファイル内パス修正**: 元リポジトリの相対パスが残っていないか Grep で確認し、該当箇所に「元リポジトリ {repo名} 内のファイル。本リポジトリには存在しない」と注記
2. **仕様書の参照パス更新**: 外部絶対パスを `references/` 内のパスに書き換え
3. **最終確認**: 作業エージェントが「このリポジトリ内にある」と誤解するパス記述がないか通読

### Step 8: レビュー

→ **Agent** に委譲（`agents/plan-reviewer.md` を Read してプロンプトとして使用）

レビューエージェントに渡す情報:

- spec.md パス + tasks.json パス、CLAUDE.md パス（存在時）

レビュー観点:

1. **タスク粒度** — 各タスクが 1-2 時間で完了可能か
2. **依存関係** — 順序が正しいか、循環依存がないか
3. **自己完結性** — 仕様書だけで実装を完遂できるか
4. **参照の完全性** — 外部参照がすべて同梱済みでパスが正しいか
5. **漏れ** — セットアップ・エラーハンドリング・テストの不足
6. **リスク** — 残存リスクの緩和策が十分か
7. **Review 構造** — 各 Todo に Step 2（Review 結果記入欄）が定義されているか
8. **Gate 0** — 冒頭に Gate 0（`/dev:spec-run` 参照）が記述されているか

**NEEDS_REVISION** の場合:

1. 指摘事項をユーザーに提示
2. AskUserQuestion で修正方針を確認（自動修正 / 手動調整 / 無視して続行）
3. 修正を反映して再レビュー

**最大 2 回ループ**。超えた場合はユーザー判断に委ねる。

### Step 9: 整合性チェック

→ **Agent** に委譲（`agents/spec-sync.md` を Read してプロンプトとして使用）

エージェントに渡す情報:

- spec.md パス
- tasks.json パス
- 変更コンテキスト: Step 8 のレビューで修正が入った場合はその内容

検証内容:

1. **構造的整合性** — Todo ID/タイトル、Gate 構造、依存関係、TDD ラベル、metadata カウントが spec.md と tasks.json で一致しているか
2. **意味的整合性** — impl 内容が設計決定事項・アーキテクチャ詳細と矛盾していないか

修正ルール:

- 構造的不整合（ID 不一致、カウントずれ等）→ 自動修正
- 意味的矛盾（impl と設計決定の矛盾等）→ AskUserQuestion で確認後に修正

### Step 10: ユーザー最終確認

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
- [ ] レビューが完了（APPROVED or ユーザー判断で続行）
- [ ] ユーザーが承認済み
- [ ] `docs/PLAN/{YYMMDD}_{slug}/spec.md` が存在する
- [ ] `docs/PLAN/{YYMMDD}_{slug}/tasks.json` が存在する
- [ ] tasks.json の `schemaVersion` が 2 である
- [ ] tasks.json の全 Todo に `impl` フィールドが存在し空でない
- [ ] tasks.json の各 Todo の `steps[]` が 2 要素（impl + review）である
- [ ] spec.md に `<!-- generated:begin -->` ... `<!-- generated:end -->` マーカーが存在する
- [ ] spec.md のチェックリストと tasks.json の Todo ID/タイトルが一致する
- [ ] spec.md の Preflight チェックリストと tasks.json の preflight 配列の ID/タイトルが一致する（Preflight がある場合）

## 参照

- `agents/plan-reviewer.md` — 仕様書全体のレビューエージェント指示書（Step 8）
- `agents/spec-sync.md` — spec.md / tasks.json 整合性チェック + 修正エージェント（Step 9、v2 schema 整合性 + generated マーカー確認）
- `/dev:spec-run` — 仕様書実行プロトコル（Gate 0 で参照。`agents/reviewer.md` に統合済み）
- `/dev:dig` — Step 2 で要件の深掘りに使用
- `/dev:decomposition` — Step 3 でタスク分解に使用
