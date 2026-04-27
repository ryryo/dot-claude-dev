# 仕様書テンプレート（ディレクトリ構造用 / schema v3）

`docs/PLAN/{YYMMDD}_{slug}/spec.md` は以下の構成で作成する。

**v3 設計思想**: 「どう作るか」の詳細手順は仕様書に書かない。代わりに **Gate ごとの Goal / Constraints / Acceptance Criteria** を契約として明示し、実装エージェントが自律的に判断できるようにする。

`tasks.json` は契約の構造化データ、`spec.md` は背景・設計判断・契約の人間可読サマリ。**実装手順（impl）は両方とも持たない**。

**generated 領域**: 「## タスクリスト」節は `<!-- generated:begin -->` ... `<!-- generated:end -->` マーカーで囲み、内部は `sync-spec-md.mjs` が tasks.json から自動生成する。`/dev:spec` の Step 6 では **(1) authored セクション（背景・設計決定・アーキテクチャ）** → **(2) tasks.json の Gate 契約と Todo** → **(3) スクリプトで generated 領域を埋める** の 3 段で作成する。

---

## 必須セクション

```markdown
# {タイトル}

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> Codex / サブエージェントの sandbox 制限（ネットワーク不可 / ワークスペース外書き込み不可 / 対話不可）により、以下のいずれかに該当する処理のみを列挙する:
> - **ネットワーク必須**: `npm/pnpm/yarn/bun/pip install`、`uv sync`、`npx create-*`、`git clone`、`curl`、リモート API 呼び出し 等
> - **ワークスペース外書き込み**: `brew install`、`apt install`、`cargo install`、`~/.zshrc` 編集 等
> - **対話必須**: `gh auth login`、`gcloud auth login`、OAuth フロー、パスワードプロンプト 等
>
> 該当がなければこのセクション全体を省略してよい。
> これらは `/dev:spec-run` 実行時に Claude main session が先に実行する。
> 詳細（コマンド / manual フラグ / reason / ac）は `tasks.json` の `preflight` 配列を参照。

- [ ] **P1**: {タイトル}
- [ ] **P2**: **[手動]** {タイトル}

---

## 概要

[1-2 文で何を達成するか]

## 背景

[なぜこの変更が必要か / 解決したい課題 / 機会]

## 設計決定事項

[確定した意思決定を表形式で列挙。Gate 契約の must / mustNot の根拠になる]

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | ...      | ...  | ...  |

## アーキテクチャ詳細

[データフロー図 / 構造定義 / 仕様値などを記載。実装手順ではなく **「実装後の最終形」** を描く]
[ASCII 図、JSON スキーマ、型定義などを含める]

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |

### 参照資料（references/ にコピー済み）

| ファイル | 目的 |
| -------- | ---- |

[外部参照がない場合はこのサブセクション自体を省略]

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

[Gate 単位で依存関係を図示 — sync-spec-md が tasks.json の gates[].dependencies から生成]

### Gate A: {フェーズ名}

> {Gate summary — あれば}

**Goal**: {what} — {why}

**Constraints**:
- ✅ MUST: ...
- ❌ MUST NOT: ...

**Acceptance Criteria**:
- [ ] **A.AC1**: ...
- [ ] **A.AC2**: ...

**Todos** ({n}):
- **A1**: {タイトル} — `path/to/file.ts` ほか
- **A2**: {タイトル} — `path/to/file.ts`

**Review**: _未記入_

### Gate B: {フェーズ名}

...

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
```

---

## ラベルの判定

### `[TDD]` ラベル

入出力が明確に定義でき、アサーションで検証可能な Todo に `[TDD]` ラベルを付与する。
`tasks.json` の `tdd: true` フィールドと対応する。

| 対象 | 例 |
|------|-----|
| バリデーション | validateEmail, validatePassword |
| 計算・変換 | calculateTotal, formatDate, parseJson |
| ビジネスロジック | checkPermission, applyRules |

### `[SIMPLE]` ラベル

数行追加・import 追加・定数追加・既知パターンの 1 箇所適用などの軽微な変更で完結する Todo に付与する。

- Codex モードでは Codex 委任をスキップし Claude main session が直接実装、VERIFY も SKIPPED
- Claude モードでは無視
- `tasks.json` 側の別フィールドは作らず、title 先頭に `[SIMPLE]` を付ける

`[SIMPLE]` と `[TDD]` は通常排他的（必要なら両方付与可）。
