# 並列実行プロトコル（`[PARALLEL]` タグ付き Gate）

Gate ヘッダに `[PARALLEL]` タグがある場合、独立した Todo を並列で実行する。

## 並列実行フロー

```
1. Gate 内の全 Todo を分析し、独立性を確認（ファイル重複なし）
2. 各 Todo に対して Agent(isolation: worktree) を起動
   ├─ Agent ①: Todo A → IMPL → REVIEW → (FIX) → commit
   ├─ Agent ②: Todo B → IMPL → REVIEW → (FIX) → commit
   └─ Agent ③: Todo C → IMPL → REVIEW → (FIX) → commit
3. 全 Agent の完了を待機
4. 各 worktree のブランチをメインにマージ
   └─ 競合あり → AskUserQuestion でユーザーエスカレーション
5. 仕様書の Review 結果記入欄を更新
6. Gate 通過判定
```

## Agent への prompt 構成

各 Todo を実行する Agent には以下を渡す:

1. **ロール定義**（該当する場合のみ）: ワークフローに応じて `agents/` から選択（下記マッピング参照）
2. **仕様書パス** + **対象 Todo 番号**
3. **IMPL 実行指示**: 仕様書の Todo IMPL 内容をそのまま引用
4. **REVIEW 実行指示**: IMPL 完了後、`agents/reviewer.md` の手順で自己レビューを実行
5. **コミット指示**: 全変更を意味のあるコミットメッセージでコミット
6. **結果返却**: Review 結果を返却する

### TDD / E2E ワークフロー（ロール定義あり）

```
Agent(
  isolation: "worktree",
  prompt: """
  {agents/{role}.md の内容}

  ## タスク
  仕様書: {仕様書パス}
  対象: Todo {N}

  ## IMPL 内容
  {仕様書の Todo N の IMPL 詳細}

  ## 手順
  1. 仕様書の「参照すべきファイル」を Read する
  2. IMPL を実行する
  3. agents/reviewer.md の手順で REVIEW を実行する
  4. FAIL があれば修正する（最大3ラウンド）
  5. 全変更をコミットする
  6. Review 結果を返却する
  """
)
```

### TASK ワークフロー（ロール定義なし）

仕様書の IMPL 詳細がそのまま指示になる。特定のロールは不要。

```
Agent(
  isolation: "worktree",
  prompt: """
  ## タスク
  仕様書: {仕様書パス}
  対象: Todo {N}

  ## IMPL 内容
  {仕様書の Todo N の IMPL 詳細}

  ## 手順
  1. 仕様書の「参照すべきファイル」を Read する
  2. IMPL を実行する
  3. agents/reviewer.md の手順で REVIEW を実行する
  4. FAIL があれば修正する（最大3ラウンド）
  5. 全変更をコミットする
  6. Review 結果を返却する
  """
)
```

## ワークフロー → ロールのマッピング

| ワークフロー | IMPL ロール | REVIEW ロール |
|---|---|---|
| TDD | `agents/tdd-developer.md` | `agents/reviewer.md` |
| E2E | `agents/frontend-developer.md` | `agents/reviewer.md` |
| TASK | なし（仕様書の IMPL 詳細で十分） | `agents/reviewer.md` |

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

## UPDATE

各 Todo の全 Step 完了後（マージ後）、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`
