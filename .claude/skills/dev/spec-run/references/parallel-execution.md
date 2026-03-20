# 並列実行プロトコル（`[PARALLEL]` タグ付き Gate）

Gate ヘッダに `[PARALLEL]` タグがある場合、独立した Todo を並列で実行する。

## 並列実行フロー

```
1. Gate 内の全 Todo を分析し、独立性を確認（ファイル重複なし）
2. 各 Todo に対して Agent(isolation: worktree) を起動
   └─ worktree 内フロー:
      a. IMPL — ロール定義に従って実装 → commit
      b. VERIFY — Task で reviewer を起動 → レビュー
      c. FIX — FAIL 時のみ修正 → 再 VERIFY（最大3ラウンド）
      d. 結果を Main に返却
3. 全 Agent の完了を待機
4. 各 worktree のブランチをメインにマージ
   └─ 競合あり → AskUserQuestion でユーザーエスカレーション
5. マージ後、統合レビュー（reviewer を Agent で実行、worktree なし）
   └─ FAIL → 修正 → 再レビュー
6. 仕様書の Review 結果記入欄を更新
7. Gate 通過判定
```

## ロール選択

各 Todo のラベルに応じて SKILL.md パラメータテーブルからロールを選択する。
同一 Gate 内で [TDD] と非[TDD] の Todo が混在してよい。

- `[TDD]` ラベルあり → `references/agents/tdd-developer.md` を Read してロール定義として渡す
- ラベルなし → `references/agents/implementer.md` を Read してロール定義として渡す

## Agent への prompt 構成

各 Todo を実行する Agent には以下を渡す:

1. **ロール定義**: 上記で選択した `references/agents/*.md` の内容
2. **仕様書パス** + **対象 Todo 番号**
3. **IMPL 実行指示**: 仕様書の Todo IMPL 内容をそのまま引用
4. **VERIFY 実行指示**: IMPL 完了後、3体のレビューエージェントを並列起動してレビューを実行
5. **FIX 指示**: FAIL 時は修正して再度3体並列レビューを起動（最大3ラウンド）
6. **コミット指示**: 全変更を意味のあるコミットメッセージでコミット
7. **結果返却**: Review 結果を返却する

### prompt テンプレート

```
Agent(
  isolation: "worktree",
  prompt: """
  {references/agents/{role}.md の内容}

  ## タスク
  仕様書: {仕様書パス}
  対象: Todo {N}

  ## IMPL 内容
  {仕様書の Todo N の IMPL 詳細}

  ## 手順
  1. 仕様書の「参照すべきファイル」を Read する
  2. IMPL を実行する
  3. 全変更をコミットする
  4. 以下の3ファイルを Read し、それぞれ Agent（sonnet）で並列起動して VERIFY を実行する:
     - agents/reviewer-quality.md（品質・設計）
     - agents/reviewer-correctness.md（正確性・仕様適合）
     - agents/reviewer-conventions.md（プロジェクト慣例）
  5. 1体でも FAIL があれば修正し、再度3体並列レビューを実行する（最大3ラウンド）
  6. Review 結果を返却する
  """
)
```

## マージ手順

```
1. 各 Agent が変更ありで完了した場合、worktree のブランチが残る
2. メインブランチに各ブランチを順次マージ:
   git merge {branch-1} && git merge {branch-2} && ...
3. マージ競合が発生した場合:
   a) AskUserQuestion で状況を報告
   b) ユーザーの指示に従って解決
4. マージ完了後、残った worktree とブランチをクリーンアップ:
   git worktree prune
   git branch -d {branch-1} {branch-2} ...
```

## 統合レビュー（3体並列）

マージ完了後、メインブランチ上で統合レビューを実行する:

1. 以下の3ファイルを Read し、それぞれ Agent（sonnet、worktree なし）で並列起動する:
   - `agents/reviewer-quality.md`（品質・設計）
   - `agents/reviewer-correctness.md`（正確性・仕様適合）
   - `agents/reviewer-conventions.md`（プロジェクト慣例）
2. 各エージェントには「統合レビュー」であることを明記し、個別レビューでは検出できない統合問題（インターフェース不一致、重複コード等）に注目するよう指示する
3. 1体でも FAIL → 修正 → 再度3体並列レビュー
4. 全体 PASS → 仕様書に結果を記録

## UPDATE

各 Todo の全 Step 完了後（マージ後）、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`
