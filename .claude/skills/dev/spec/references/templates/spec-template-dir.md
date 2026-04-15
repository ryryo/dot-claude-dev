# 仕様書テンプレート（ディレクトリ構造用）

`docs/PLAN/{YYMMDD}_{slug}/spec.md` は以下の構成で作成する。
実装詳細は `tasks.json` に格納されるため、このファイルは概要・設計・チェックリストに特化する。

**注意**: 「## タスクリスト」節は `<!-- generated:begin -->` ... `<!-- generated:end -->` マーカーで囲み、
マーカー内部は `sync-spec-md.mjs` スクリプトが tasks.json から自動生成する。
`/dev:spec` の Step 6 では **(1) spec.md の authored セクション（背景・設計決定・アーキテクチャ）を書く** → **(2) その設計を参照して tasks.json を書く** → **(3) スクリプトで generated 領域を埋める** の 3 段で作成する。初回 Write 時は generated 領域を**空のマーカーのみ**にする。
以後 tasks.json を Edit/Write すると PostToolUse hook が同スクリプトを自動発火し、spec.md の generated 領域が追従する。

---

## 必須セクション

```markdown
# {タイトル}

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> Codex / サブエージェントの sandbox 制限（ネットワーク不可 / ワークスペース外書き込み不可 / 対話不可）により、以下のいずれかに該当する処理のみを列挙する:
> - **ネットワーク必須**: `npm/pnpm/yarn/bun/pip install`、`uv sync`、`npx create-*`、`git clone`、`curl`、リモート API 呼び出し 等
> - **ワークスペース外書き込み**: `brew install`、`apt install`、`cargo install`、`~/.zshrc` 編集 等
> - **対話必須**: `gh auth login`、`gcloud auth login`、OAuth フロー、パスワードプロンプト 等
>
> 該当がなければこのセクション全体を省略してよい。
> これらは `/dev:spec-run` 実行時に Claude main session が先に実行する。
> 詳細（コマンド / manual フラグ / reason）は `tasks.json` の `preflight` 配列を参照。

- [ ] **P1**: {タイトル}
- [ ] **P2**: **[手動]** {タイトル}

---

## 概要

[1-2 文で何を達成するか]

## 背景

[なぜこの変更が必要か、設計判断の理由]

## 設計決定事項

[確定した意思決定を表形式で列挙]

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | ...      | ...  | ...  |

## アーキテクチャ詳細

[データフロー図、構造定義、仕様値など実装に必要な詳細]
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

> {Gate description — あれば}

- [ ] **A1**: {タイトル}
  > **Review A1**: _未記入_

- [ ] **A2**: {タイトル}
  > **Review A2**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: {フェーズ名}

- [ ] **B1**: {タイトル}
  > **Review B1**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
```

---

## [TDD] ラベルの判定

入出力が明確に定義でき、アサーションで検証可能な Todo に `[TDD]` ラベルを付与する。
`tasks.json` の `tdd: true` フィールドと対応する。

| 対象 | 例 |
|------|-----|
| バリデーション | validateEmail, validatePassword |
| 計算・変換 | calculateTotal, formatDate, parseJson |
| ビジネスロジック | checkPermission, applyRules |

ラベルなしの Todo は `dev:spec-run` で Claude が直接実装する。
