# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 基本原則

**デフォルトで Codex に委任する。** Claude が保持するのは、チェックリストで明確に該当する場合のみ。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      チェックリストで委任判断 → Codex or Claude
Step 2 — VERIFY    Codex 委任は codex review → sonnet 3体、Claude 実装は sonnet 3体のみ
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 1 — IMPL

### 委任判断チェックリスト（必須）

各 Todo の IMPL 前に、以下の 3 項目を確認する。

| # | チェック項目 | 「はい」の場合 |
|---|-------------|---------------|
| 1 | この Todo は**前の Todo の実装結果**を見て設計判断を変える必要があるか？ | Claude 保持 |
| 2 | 仕様が曖昧で**ユーザーに確認**しないと実装方針が決まらないか？ | Claude 保持 |
| 3 | この Todo は**他の Todo と同じファイル**を同時に変更する必要があるか？ | Claude 保持 |

- **3項目すべて「いいえ」→ Codex に委任する**（例外なし）
- **1項目でも「はい」→ Claude が保持する。理由を記録する**

「確実性」「複雑さ」「Claude の方が得意」のような主観的理由での保持は禁止。

### Codex に委任する場合

#### 1. タスク分割

Todo 内に**独立したファイル**が複数含まれる場合、ファイルごとに別々の codex exec で**並列実行**する。

| 条件 | 実行方法 |
|------|----------|
| 1ファイルの変更 | codex exec 1回 |
| 複数ファイルだが相互依存あり | codex exec 1回（まとめて渡す） |
| 複数ファイルで独立 | ファイルごとに codex exec を**並列実行** |

#### 2. テンプレート選択

- [TDD] ラベルあり、またはテスト先行が適切 → `roles/codex-tdd-developer.md`
- それ以外 → `roles/codex-developer.md`

#### 3. 実行

テンプレートの変数を埋めて一時ファイルに書き出し、実行する:

```bash
cat /tmp/codex-prompt.md | codex exec -m gpt-5.4 --sandbox workspace-write --full-auto --ephemeral - 2>/dev/null
```

並列実行時はファイル名を分ける（例: `/tmp/codex-prompt-1.md`, `/tmp/codex-prompt-2.md`）。

#### 4. 結果確認

- 成功 → Claude がコミット
- 失敗 → エラー情報を含めてリトライ（最大3回）
- 3回失敗 → Claude が直接実装（フォールバック）

### Claude が直接実装する場合

チェックリストで「はい」が 1 つ以上あった場合のみ。
仕様に忠実に実装する。[TDD] ラベルがある場合は `roles/tdd-developer.md` を参照。
実装完了後、変更をコミットする。

## Step 2 — VERIFY

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
