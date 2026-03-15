---
name: dev:spec-run
description: |
  仕様書（docs/PLAN/*.md）の実行プロトコル。
  Todo の実行手順（IMPL → REVIEW → FIX）、Gate 通過条件、Review 実行方法を定義する。
  仕様書の Gate 0 で参照される。

  Trigger: 仕様書を実行, /dev:spec-run, 計画書の実行
---

# 仕様書実行プロトコル（dev:spec-run）

仕様書（`docs/PLAN/*.md`）に基づいて作業するエージェント向けの実行プロトコル。

## 起動フロー

### ステップ 1: 仕様書の特定

#### A. コンテキストから特定できる場合

会話の文脈や Gate 0 からの参照で対象が明確。そのままステップ 2 へ進む。

#### B. `/dev:spec-run` が単独で実行された場合

1. `docs/PLAN/*.md` を Glob で検索し、更新日順でソートする
2. 上位 5 件を AskUserQuestion で提示する（最新を推奨マーク付き）
3. ユーザーが選択した仕様書を対象とする

### ステップ 2: 作業環境の選択

仕様書が確定したら、AskUserQuestion で作業環境を選択させる:

| 選択肢 | 説明 |
|--------|------|
| **現在のブランチで作業** | そのまま実行を開始する |
| **新規ワークツリーを作成** | feature ブランチ + worktree を作成してから実行する |
| **既存ワークツリーで継続** | 既に作成済みの worktree 内で作業を再開する |

#### 現在のブランチで作業

そのまま Gate 0 通過条件を実行し、Todo 実行に進む。

#### 新規ワークツリーを作成

```
1. git status --porcelain で未コミット変更を確認
   └── 変更あり → AskUserQuestion で対応を確認（stash / commit / abort）
2. 仕様書ファイル名からスラッグを生成（例: 260315_auth-api.md → auth-api）
3. git worktree add .worktrees/{slug} -b feature/{slug}
4. .worktrees/{slug} に移動して作業開始
```

#### 既存ワークツリーで継続

```
1. git worktree list で一覧を取得
2. AskUserQuestion で対象の worktree を選択させる
3. 選択した worktree のパスに移動して作業を再開
```

### ステップ 3: 実行開始

Gate 0 通過条件（参照すべきファイルの読み込み等）を実行し、Todo 実行に進む。

---

## Todo 実行の手順

各 Todo は必ず以下を **順番に** 実行する。ステップを飛ばしてはならない。

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      実装を行う
Step 2 — REVIEW    Task(sonnet) で todo-review を実行し、結果を仕様書の記入欄に貼り付ける
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書の完了した Step のチェックボックスを [x] に更新する
```

### Step 4 — UPDATE の詳細

各 Todo の全 Step 完了後、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`

これにより、仕様書を見るだけで各 Todo の進捗が把握できる。

## Gate 通過条件

Gate 内の全 Todo について:

1. **IMPL が完了**していること
2. **REVIEW 結果記入欄にレビュー結果テーブルが記入済み**であること（空欄は不可）
3. **全 REVIEW の総合判定が PASS** であること

REVIEW 結果記入欄が空の Todo がある状態で Gate 通過としてはならない。

## REVIEW の実行方法

### 呼び出し方

```
Task(model: sonnet) で以下を実行:
1. `.claude/skills/dev/spec-run/tasks/todo-review.md` を Read する
2. そのプロンプトに従ってレビューを実行する
3. 引数: 仕様書のパス + 対象 Review ID（例: Review A1）
```

### レビュー 6 観点

| 観点               | 評価内容                                                 |
| ------------------ | -------------------------------------------------------- |
| ストーリー適合性   | 仕様書の概要・背景に記述されたユーザー要件を実現しているか |
| API・SDK 準拠      | ライブラリ・フレームワークの公式仕様に従った使い方か     |
| ベストプラクティス | 言語・FW の慣用的パターン、DRY/KISS/YAGNI に従っているか |
| リスク・前提の検証 | 設計決定事項の前提を破る実装やエッジケースの見落としがないか |
| セキュリティ       | OWASP Top 10、入力バリデーション、機密情報の取り扱い     |
| 保守性・可読性     | 命名の一貫性、過度な複雑さ、既存パターンとの整合         |

各観点を **PASS / FAIL / N/A** で判定する。1つでも FAIL があれば全体 FAIL。

### 結果の記録

レビュー結果は仕様書の各 Todo の **Step 2 記入欄**（blockquote 形式）に貼り付ける:

```markdown
- [x] **Step 2 — Review A1** ✅ PASSED
> **レビュー結果**:
>
> ✅ REVIEW A1 PASSED
>
> | # | 観点 | 判定 | 根拠 |
> |---|------|------|------|
> | 1 | ストーリー適合性 | ✅ PASS | {根拠} |
> | ... | | | |
```

## 仕様書の Todo 構造

各 Todo は以下の形式で記述する:

```markdown
#### Todo N: {タイトル}

- [ ] **Step 1 — IMPL**
  - **対象**: {ファイルパス}
  - **内容**: {何を}
  - **実装詳細**: {どうやって}
  - **ワークフロー**: TDD / E2E / TASK
  - **依存**: {先行タスク}

- [ ] **Step 2 — Review {GateID}{N}**
  > **レビュー結果**:
  >
  > （未記入 — Task(sonnet) で todo-review を実行し、結果テーブルをここに貼り付ける）

**Gate N 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること
```

## 全 Gate 通過後の完了処理

### 現在のブランチで作業した場合

全 Gate 通過を確認し、仕様書の実行完了を宣言する。

### ワークツリーで作業した場合

```
1. worktree 内の全変更がコミット済みであることを確認
   └── 未コミットあり → simple-add-dev でコミット
2. AskUserQuestion で完了後のアクションを選択させる:
   a) メインブランチにマージ
      └── git checkout {main} && git merge feature/{slug} && git worktree remove .worktrees/{slug} && git branch -d feature/{slug}
   b) PR を作成
      └── git push -u origin feature/{slug} && gh pr create
   c) ワークツリーを残して終了（後で再開する場合）
      └── 何もしない
```

## 参照

- `tasks/todo-review.md` — 個別 Todo のレビューエージェント指示書
