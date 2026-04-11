# Spec ↔ Dashboard フォーマット問題 検討メモ

> `/dev:spec` で作る仕様書と、それを表示する dashboard との間の書式上の衝突をどう解決するかの検討メモ。意思決定前の網羅整理。

## 背景 / 問題意識

- `/dev:spec` で作成した計画書 (`docs/PLAN/**`) を dashboard が読み込んでパースし、Gate / Todo / Step / Review 結果 / 進捗を表示している
- dashboard 側で markdown を正規表現パースするロジックが重く非効率に感じる
- しかし markdown にしないと人間が GitHub 等で開いたときに読みづらい
- 「人間可読 ↔ 機械可読」の衝突をどう解くか

## 現状の事実関係

### Writer 側 (`/dev:spec`)

出力モードが2通りある (`.claude/skills/dev/spec/SKILL.md` 参照):

| モード | 条件 | 出力物 |
|---|---|---|
| **シングルモード** | Gate < 3 かつ Todo < 10 | `docs/PLAN/{YYMMDD}_{slug}.md` のみ |
| **ディレクトリモード** | Gate >= 3 または Todo >= 10 | `docs/PLAN/{YYMMDD}_{slug}/spec.md` + `tasks.json` |

- シングルモード: markdown 1 ファイルで完結。概要・設計判断・アーキテクチャ・全 Gate/Todo/Step・Review 記入欄・impl 詳細すべてを含む
- ディレクトリモード: `spec.md` は narrative + チェックリスト + Review 記入欄のみ、impl 詳細は `tasks.json` 側に格納

### Reader 側 (dashboard)

`dashboard/lib/plan-parser.ts` (約 300 行) が markdown を正規表現パースして以下を抽出:

- `# Title`
- `## 概要` セクション
- `## レビューステータス` のチェック状態
- `### Gate X: Y` 見出し
- `#### Todo N: Y` 見出し
- `- [ ] **Step N — Y**` 各 Step のチェックボックス
- Step ブロック内の `> **Review ...** — PASSED — FIX N 回 — summary` blockquote
- Step ブロック内の `- **内容:**` / `- **実装詳細:**` / `- **対象:**`

`dashboard/lib/github.ts` の `fetchPlanFiles`:

- `docs/PLAN` 配下を GitHub API で取得
- ファイルなら `.md` を `parsePlanFile` に渡す
- ディレクトリなら `{dir}/spec.md` を `parsePlanFile` に渡す
- **`tasks.json` は一切参照していない**

## 衝突の本質

表面的には「markdown vs JSON」の衝突に見えるが、実体は別のところにある。

> **mutable な progress state を immutable な narrative と同じ markdown に埋め込んでしまっている** のが根本原因

仕様書が保持する情報は性質が2種類に分かれる:

| 種類 | 更新頻度 | 主な読み手 | 向いている形式 |
|---|---|---|---|
| 概要・設計判断・アーキテクチャ・impl 詳細 | 書いたら不変 | 人間・実装エージェント | Markdown (narrative) |
| チェック状態・Review 結果・FIX 回数・status | Gate ごとに更新 | dashboard・spec-run | 構造化データ (JSON/YAML) |

この2つを1枚の markdown に同居させているため、dashboard が narrative から機械可読情報を掘り返すハメになっている。分離すれば両立する。

## 制約

解決策を評価する前に、守りたい制約を明文化する:

1. **GitHub で markdown を開いて読めること** — 人間が PR レビューやディレクトリ閲覧で読む
2. **シングルモードの軽量性** — 小さい仕様書でファイルが複数にならない手軽さ
3. **移行コストを現実的な範囲に収める** — 8 プロジェクト / 112 PLAN が既に存在する
4. **spec-run 側の更新処理が簡潔** — チェックボックスを倒すたびに複雑な同期が走るのは避けたい
5. **実装エージェント体験を損なわない** — ディレクトリモードで impl 詳細を `tasks.json` に分割している設計思想は尊重したい

## 解決策の選択肢

### Option A: シングルモード廃止、ディレクトリモード一本化

- すべての仕様書を `{slug}/spec.md` + `tasks.json` 形式に統一
- dashboard は `tasks.json` だけ読む
- `tasks.json` スキーマを拡張して per-step の progress (`checked`, `reviewResult`, `reviewFixCount`, `reviewSummary`) を格納
- spec-run は `tasks.json` を primary に更新

**Pro**
- dashboard 側の markdown parser を完全に削除できる
- 構造がシンプル (モードが1つだけ)
- 構造化データの拡張が自由

**Con**
- 小さな仕様書でも常にディレクトリ + 2 ファイル → シングルモードの軽量性が失われる (制約 2 に反する)
- 既存の 112 PLAN のうちシングルモードのものをディレクトリ化する変換が必要 → 移行コスト大 (制約 3 に反する)

### Option B: JSON sidecar をシングルモードにも併置

- シングルモード: `{YYMMDD}_{slug}.md` + `{YYMMDD}_{slug}.json`
- ディレクトリモード: 現状通り `{slug}/spec.md` + `{slug}/tasks.json`
- dashboard は `.md` の隣 / `/spec.md` の隣の JSON を読む共通ルール

**Pro**
- シングルモードの軽量性を「人間向けファイルは1つ」という形で維持
- dashboard 側の markdown parser を完全に削除できる
- 構造化データの拡張が自由 (JSON なのでスキーマ進化も楽)

**Con**
- 常に 2 ファイルを書き出す必要あり (`/dev:spec` も `/dev:spec-run` も更新時に両方を触る)
- ファイル数が純増 (112 PLAN → 224 ファイル)
- 人間視点で「実質1ファイルで完結」感が薄れる (制約 2 に若干反する)

### Option C: Markdown frontmatter に構造化データを埋め込む

- シングル・ディレクトリ両モードで markdown の先頭 frontmatter (YAML) に機械可読な Gate/Todo/Step 構造 + 進捗状態を格納
- body 側は現状通り narrative + impl 詳細 + visible な checkbox/review blockquote
- dashboard は frontmatter の YAML だけをパース (`js-yaml` 等で数行)

**Pro**
- ファイル数が増えない (制約 2 を完全に満たす)
- 既存 PLAN への影響が frontmatter 追記のみ → 移行コスト最小 (制約 3 を満たす)
- 本文の書式変更で dashboard が壊れなくなる
- シングル/ディレクトリの非対称を変えずに済む

**Con**
- 「真の parser 廃止」ではなく「脆い markdown parser → 堅い YAML parser への置換」 (ただし堅牢性は段違い)
- frontmatter と body の checkbox/review 表示が二重化する可能性 → どちらを truth にするか要決定
- frontmatter が 50-100 行規模になり、GitHub で開いたとき最上部に長いテーブルが出る

### Option (参考) D: 現状維持 + 構造化ブロック領域

- markdown の body 内に `<!-- plan:begin -->` ... `<!-- plan:end -->` の領域を設け、そこだけを dashboard がパース
- 領域外は自由 narrative

**Pro**
- 最小変更で着地

**Con**
- 結局 markdown 内に独自マーカーを埋める形になり、堅牢性は frontmatter 案に劣る
- `tasks.json` の位置付けがより曖昧になる

## オプション比較表

| | 軽量性 (制約2) | 破綻しにくさ | 移行コスト (制約3) | parser 消滅 | ファイル数増 |
|---|---|---|---|---|---|
| **A** シングル廃止 | ✗ (常に dir) | ◎ | 大 (md → dir 変換) | ◎ | 中 |
| **B** JSON sidecar | △ (2ファイル常時) | ◎ | 中 (md → json 生成) | ◎ | 大 (倍増) |
| **C** frontmatter 同梱 | ◎ | ○ | 小 (frontmatter 追記) | ○ (縮小) | なし |
| D 構造化ブロック | ◎ | △ | 小 | ✗ | なし |

## 現時点の仮決定

- **方向性は Option C (frontmatter)** で進めることを前提に検討中
- 理由: ユーザーが「markdown 1 ファイルで完結する手軽さ」を重視しているため、シングルモードの形を維持できる C が噛み合う

ただし C を採用する場合にまだ未決の論点が4つ残っている。

## Option C 採用時の未決論点

### 論点 1: Source of truth はどちらか？

frontmatter と body の両方に Gate/Todo/Step 情報 + 進捗情報を持たせる場合、どちらが真か。

| 案 | 意味 | 影響 |
|---|---|---|
| **frontmatter = 真** | body の checkbox / Review blockquote は視覚用。spec-run が両方更新、ドリフト時は frontmatter が勝つ | dashboard は YAML だけ読めばよい。人間の手編集は反映されない |
| **body = 真** | frontmatter は cache。lint で同期検証 | 人間の手編集も反映される。ただし spec-run は body を parse する必要が残る (薄い parser は残存) |

傾向: **frontmatter = 真** が parser 完全廃止の観点では望ましい。ただし人間が markdown のチェックボックスを手で触って進捗を変えるユースケースがあるなら body = 真の方が自然。

**検討材料**: 実際に人間が body のチェックボックスを手編集することはあるか？ 現状の運用だとチェックを触るのは `/dev:spec-run` のみのはずなので frontmatter = 真で問題ないはず、という仮説。

### 論点 2: ディレクトリモードと `tasks.json` の関係

C を適用すると `spec.md` の frontmatter にも構造化データが入る。この時 `tasks.json` はどうなるか。

| 案 | 意味 |
|---|---|
| **残す** | frontmatter は骨格 + 状態、impl 詳細は `tasks.json`。実装エージェントは `tasks.json` を読む (現状通り)。dashboard は frontmatter だけ見る |
| **廃止** | impl 詳細を body に戻し、シングルモードと統一。ディレクトリモードの意義は「ファイルが大きすぎるので見出しだけ抽出」 |

傾向: **残す**。`tasks.json` を残すことで役割分担が明確になる (dashboard = frontmatter、実装エージェント = tasks.json、人間 = body)。ただしディレクトリモードの存在意義が「長大な impl 詳細を分離したい」という運用判断次第なので、実際にファイルサイズがどれくらいかを見て決めるべき。

### 論点 3: Review blockquote は body に残すか

現状 body には以下のような形式で Review 結果が書かれる:

```markdown
- [x] **Step 2 — Review**
  > **Review Step 2**: PASSED — FIX 2回 — 実装OK
```

この blockquote は frontmatter の `review.result` / `fixCount` / `summary` と重複する。

| 案 | Pro | Con |
|---|---|---|
| **残す** | 人間が body を読むときに Review 結果が見える | spec-run が body と frontmatter の両方を更新する必要 |
| **廃止** | frontmatter 一本化、更新シンプル | 人間が body を読むときに Review 結果が見えない (GitHub でフロントマター開く必要) |

傾向: **残す**。人間体験の損失が大きい。更新の二重化は sync 関数 1 つで吸収すればよい。

### 論点 4: 既存 112 PLAN の移行戦略

| 案 | 内容 |
|---|---|
| **parser 転用** | 現行 `lib/plan-parser.ts` を one-shot 移行スクリプトに流用。各 md を読み込んで YAML に変換し frontmatter として先頭に挿入 |
| **手動移行** | 一部のみ新フォーマットにし、旧フォーマットは dashboard に legacy parser を残して両対応 |
| **放置 + 新規のみ新フォーマット** | 既存は触らず、新規の `/dev:spec` 出力のみ新フォーマット。dashboard は frontmatter がなければ legacy parser にフォールバック |

傾向: **parser 転用** がクリーン。8 プロジェクトぶんの PR を順次マージする運用。パース不能な古い書式は手動 triage。

移行後、dashboard から markdown parser 本体を削除。`lib/plan-parser.ts` と `__tests__/plan-parser*.test.ts` 3本が不要になる。

## 次のアクション候補

1. 論点 1-4 を詰める (特に論点 1: frontmatter vs body の source of truth)
2. frontmatter スキーマのたたき台を確定 (`schemaVersion`, `status`, `progress`, `gates[]` の型)
3. `/dev:spec` に仕様書化して `/dev:spec-run` で実装
4. 並行して移行スクリプトを設計

## 参考: frontmatter スキーマのたたき台

```yaml
---
schemaVersion: 1
slug: dashboard-auth
title: Dashboard 認証基盤
status: in-progress        # not-started | in-progress | in-review | completed
createdDate: 2026-04-09
reviewChecked: false
progress: { completed: 3, total: 8 }
gates:
  - id: Gate A
    title: 認証基盤セットアップ
    todos:
      - title: "[TDD] Setup auth middleware"
        tdd: true
        steps:
          - kind: impl         # impl | review
            title: "Step 1 — IMPL"
            checked: true
          - kind: review
            title: "Step 2 — Review"
            checked: true
            review:
              result: PASSED   # PASSED | FAILED | SKIPPED | IN_PROGRESS
              fixCount: 0
              summary: "実装確認OK"
---
```

## 仮決定のまま採用した場合のシングルモード生成例

仮決定 (Option C / frontmatter = 真 / tasks.json はディレクトリモードで残す / Review blockquote は body に残す) のとおり進めた場合、`/dev:spec` がシングルモードで出力する `docs/PLAN/260411_example-feature.md` の全文はこのような形になる。

````markdown
---
schemaVersion: 1
slug: example-feature
title: サンプル機能の実装
status: in-progress
createdDate: 2026-04-11
reviewChecked: false
progress: { completed: 2, total: 6 }
gates:
  - id: Gate A
    title: データ層のセットアップ
    todos:
      - title: "[TDD] スキーマ定義とマイグレーション"
        tdd: true
        steps:
          - kind: impl
            title: "Step 1 — IMPL"
            checked: true
          - kind: review
            title: "Step 2 — Review"
            checked: true
            review:
              result: PASSED
              fixCount: 0
              summary: "スキーマとマイグレーションの整合性を確認"
      - title: "[TDD] リポジトリ層の実装"
        tdd: true
        steps:
          - kind: impl
            title: "Step 1 — IMPL"
            checked: false
          - kind: review
            title: "Step 2 — Review"
            checked: false
            review: null
  - id: Gate B
    title: API エンドポイント
    todos:
      - title: "POST /api/example ハンドラ"
        tdd: false
        steps:
          - kind: impl
            title: "Step 1 — IMPL"
            checked: false
          - kind: review
            title: "Step 2 — Review"
            checked: false
            review: null
---

# サンプル機能の実装

## 概要

ユーザーが任意のラベル付きアイテムを登録し、一覧表示・検索できるようにする。
サーバ側では Drizzle でスキーマを管理し、Next.js App Router の API Route で
CRUD を提供する。認証は既存の `dashboard/lib/auth.ts` を再利用する。

## Gate 0: 実行プロトコル

本仕様書の実行手順 (IMPL / Review の進め方、チェックボックス更新、コミット単位、
失敗時のロールバック) は `/dev:spec-run` スキルで定義されている。実装エージェントは
Gate A に着手する前に `/dev:spec-run` を起動し、その指示に従うこと。

## 設計判断

- **スキーマ**: `items` テーブル 1 枚で十分。`created_at` / `updated_at` は自動更新
- **認証**: 既存 `getSessionFromRequest` をそのまま使う
- **バリデーション**: Zod スキーマを `lib/schemas/item.ts` に集約
- **エラーハンドリング**: API ルートは `{ error: string }` を返す統一フォーマット

## アーキテクチャ

```
app/api/items/route.ts ─→ lib/repositories/item.ts ─→ db (Drizzle)
                          └→ lib/schemas/item.ts (Zod)
```

## 依存関係図

```
Gate A (データ層)
  └→ Gate B (API)
```

## タスクリスト

### Gate A: データ層のセットアップ

#### [TDD] スキーマ定義とマイグレーション

- [x] **Step 1 — IMPL**
  - 内容: `db/schema/items.ts` に `items` テーブルを定義し、`drizzle-kit generate` でマイグレーションを作成
  - 実装詳細: `id` (uuid, pk), `label` (text, not null), `created_at` / `updated_at` (timestamp, default now)
  - テスト: `__tests__/schema/items.test.ts` でカラム定義とインデックスを検証
- [x] **Step 2 — Review**
  > **Review Step 2**: PASSED — スキーマとマイグレーションの整合性を確認

#### [TDD] リポジトリ層の実装

- [ ] **Step 1 — IMPL**
  - 内容: `lib/repositories/item.ts` に `findAll` / `findById` / `create` / `update` / `delete` を実装
  - テスト: `__tests__/repositories/item.test.ts` で各関数の振る舞いを検証 (実 DB を使用)
- [ ] **Step 2 — Review**
  > **Review Step 2**: _未記入_

### Gate B: API エンドポイント

#### POST /api/example ハンドラ

- [ ] **Step 1 — IMPL**
  - 内容: `app/api/items/route.ts` に `POST` ハンドラを実装。Zod バリデーション → リポジトリ呼び出し → 201 返却
  - 対象: `app/api/items/route.ts` (新規)
- [ ] **Step 2 — Review**
  > **Review Step 2**: _未記入_

## レビューステータス

- [ ] **レビュー完了**

実装後、`/dev:spec-run` の指示に従い、Gate ごとのレビューが完了したらこのチェックボックスを倒す。
````

### この例のポイント

- **frontmatter**: dashboard が読む構造化データ。進捗が進むと `checked` / `review` / `progress` / `status` が更新される。`/dev:spec-run` が自動で更新
- **body のチェックボックス**: 人間向けの視覚表現。frontmatter と整合するよう `/dev:spec-run` が同時更新する。ドリフトが発生した場合は frontmatter が真
- **Review blockquote**: 人間が body を GitHub で開いたときにレビュー結果が見えるよう残す。これも `/dev:spec-run` が frontmatter と同時に更新
- **シングルファイルで完結**: tasks.json なし、references/ なし (必要な場合のみ)。「1 ファイルで読める」という手軽さを維持
- **Gate 0**: `/dev:spec-run` への参照を冒頭に記載する既存ルールを維持

### `/dev:spec-run` が 1 ステップ完了したときに書き換える箇所

例えば「[TDD] リポジトリ層の実装」の Step 1 (IMPL) が完了したら、以下を同時に更新する:

1. frontmatter の該当ステップ: `checked: false` → `checked: true`
2. frontmatter の `progress.completed`: `2` → `3`
3. body の該当チェックボックス: `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`

このとき frontmatter を先に更新し、body は frontmatter を読み直して再描画する実装にすれば、sync 関数は単方向で済む。

## 関連ファイル

- `.claude/skills/dev/spec/SKILL.md` — Writer 側プロトコル
- `.claude/skills/dev/spec-run/` — 進捗更新の実行プロトコル
- `dashboard/lib/plan-parser.ts` — 現行の markdown parser (約 300 行)
- `dashboard/lib/github.ts` — `fetchPlanFiles` (ディレクトリモードで `spec.md` のみ読む実装)
- `dashboard/lib/types.ts` — `PlanFile` / `Gate` / `Todo` / `Step` / `ReviewResult` の型定義
- `dashboard/__tests__/plan-parser*.test.ts` — parser のテスト3本
