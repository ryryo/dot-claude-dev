# 実行プロトコル（Codex モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      [TDD] は codex exec に委任、それ以外は Claude が直接実装
Step 2 — VERIFY    [TDD] は codex review → sonnet 3体、それ以外は sonnet 3体のみ
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書の完了した Step のチェックボックスを [x] に更新する
```

## Step 1 — IMPL の詳細

Todo の [TDD] ラベルを確認し、ラベルに応じて分岐する。

### [TDD] ラベルあり → Codex に委任

1. `references/agents/codex-tdd-developer.md` を Read してプロンプトテンプレートを取得
2. テンプレートの変数を埋める:
   - `{仕様書の Todo IMPL 内容}`: 仕様書から対象 Todo の IMPL セクションを引用
   - `{プロジェクト情報}`: CLAUDE.md + package.json 等から要約
   - `{関連コード}`: 仕様書の「参照すべきファイル」を Read して要約（10,000文字以内）
   - `{設計決定事項}`: 仕様書から該当セクションを引用（あれば）
3. 埋めたプロンプトを `/tmp/codex-tdd-prompt.md` に書き出す（実行後に自動削除不要。次回実行時に上書きされる）
4. Codex に委任:
   ```bash
   cat /tmp/codex-tdd-prompt.md | codex exec -m gpt-5.4 --sandbox workspace-write --full-auto - 2>/dev/null
   ```
5. 結果を確認:
   - 成功: テストコマンド（`npm test` 等）でテストが通ることを確認 → Claude がコミット
   - 失敗: エラー情報を含めてプロンプトを改善し、リトライ（最大3回）
   - 3回失敗: Claude が `references/agents/tdd-developer.md` で直接実装（フォールバック）

### ラベルなし → Claude が直接実装

1. `references/agents/implementer.md` を Read
2. ロール定義の手順に従って実装する（エージェントツールは立ち上げない。メインスレッドでそのまま作業。）
3. 実装完了後、変更をコミットする

## Step 2 — VERIFY の詳細

Todo の [TDD] ラベルに応じて分岐する。

### [TDD] ラベルあり → ハイブリッドレビュー（2段階）

#### Step 2a — codex review（差分バグ検出・先行実行）

1. `references/codex-review-instructions.md` を Read してレビュー指示テンプレートを取得
2. テンプレートの `{変数}` を仕様書の情報で埋める
3. 実行:
   ```bash
   codex review --uncommitted "{レビュー指示}" 2>/dev/null
   ```
4. 結果を解析:
   - バグ報告あり → Step 2b（FIX）へ
   - バグ報告なし → Step 2c へ

#### Step 2b — FIX（codex review 指摘の修正・最大1回）

1. codex review の指摘内容を含めてプロンプトを構成
2. `codex exec --sandbox workspace-write --full-auto` で修正を委任
3. 修正後、テストが通ることを確認
4. 再度 `codex review --uncommitted` で確認
5. Claude がコミット

#### Step 2c — sonnet 3体並列レビュー

以下の3ファイルを Read し、それぞれ Agent（sonnet）で並列起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

codex review では検出できない仕様適合性・セキュリティ・プロジェクト慣例を補完する。

#### 総合判定

- codex review PASS + 3体すべて PASS → 全体 PASS
- いずれかが FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY: codex review + 3体並列の両方を再実行する

### ラベルなし → sonnet 3体並列レビューのみ

従来モードと同じ。上記 Step 2c と同様の3体並列レビューを実行する。

## Step 4 — UPDATE

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。
