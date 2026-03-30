# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 基本原則

**デフォルトで Codex に委任する。** Claude が保持するのは以下の例外のみ:

- 前のタスクの結果に依存する設計判断が必要
- ユーザーに確認すべき曖昧な仕様がある
- 複数タスクを横断するアーキテクチャ変更

上記に該当しないタスクはすべて Codex に委任する。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      デフォルトで Codex に委任。例外のみ Claude が直接実装
Step 2 — VERIFY    Codex 委任タスクは codex review → sonnet 3体、Claude 実装は sonnet 3体のみ
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 1 — IMPL

各 Todo の IMPL 前に、Claude が委任判断を行う。

### 委任判断

1. Todo の内容を分析し、上記「基本原則」の例外に該当するか判断する
2. 該当しなければ Codex に委任する（[TDD] ラベルはテンプレート選択のヒントとして使う）

### Codex に委任する場合

1. テンプレートを選択する:
   - [TDD] ラベルあり、またはテスト先行が適切と判断 → `roles/codex-tdd-developer.md`
   - それ以外 → `roles/codex-developer.md`
2. テンプレートの変数を埋めて `/tmp/codex-prompt.md` に書き出す
3. 実行:
   ```bash
   cat /tmp/codex-prompt.md | codex exec -m gpt-5.4 --sandbox workspace-write --full-auto - 2>/dev/null
   ```
4. 結果を確認:
   - 成功 → Claude がコミット
   - 失敗 → エラー情報を含めてリトライ（最大3回）
   - 3回失敗 → Claude が直接実装（フォールバック）

### Claude が直接実装する場合

仕様に忠実に実装する。[TDD] ラベルがある場合は `roles/tdd-developer.md` を参照。
実装完了後、変更をコミットする。

## Step 2 — VERIFY

Codex に委任したタスクと Claude が実装したタスクで分岐する。

### Codex 委任タスク → ハイブリッドレビュー（2段階）

#### Step 2a — codex review（差分バグ検出・先行実行）

1. `references/codex-review-instructions.md` を Read してレビュー指示テンプレートを取得
2. テンプレートの `{変数}` を仕様書の情報で埋める
3. 実行:
   ```bash
   codex review --uncommitted "{レビュー指示}" 2>/dev/null
   ```
4. バグ報告あり → Step 2b、なし → Step 2c

#### Step 2b — FIX（codex review 指摘の修正・最大1回）

1. codex review の指摘を含めて `codex exec` で修正を委任
2. 修正後、テストが通ることを確認
3. 再度 `codex review --uncommitted` で確認
4. Claude がコミット

#### Step 2c — sonnet 3体並列レビュー

`agents/` 内の3体のレビューエージェントを Agent（sonnet）で並列起動する。

### Claude 実装タスク → sonnet 3体並列レビューのみ

上記 Step 2c と同様。

### 総合判定

- すべて PASS → 全体 PASS
- いずれかが FAIL → Step 3（FIX）へ

## Step 4 — UPDATE

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。
