# 逐次実行プロトコル

Gate に `[PARALLEL]` タグがない場合、各 Todo を **順番に** 実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      SKILL.md パラメータテーブルに従い、ロール定義を Read して実装する
Step 2 — VERIFY    SKILL.md パラメータテーブルに従い、Agent で reviewer を実行する
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書の完了した Step のチェックボックスを [x] に更新する
```

## Step 1 — IMPL の詳細

### 従来モード

1. Todo の [TDD] ラベルを確認する
2. SKILL.md パラメータテーブルから該当するロールを特定する:
   - `[TDD]` ラベルあり → `references/agents/tdd-developer.md` を Read
   - ラベルなし → `references/agents/implementer.md` を Read
3. ロール定義の手順に従って実装する(エージェントツールは立ち上げない。メインスレッドでそのまま作業。)
4. 実装完了後、変更をコミットする

### Codex モード

Todo の [TDD] ラベルを確認し、ラベルに応じて分岐する。

#### [TDD] ラベルあり → Codex に委任

1. `references/agents/codex-tdd-developer.md` を Read してプロンプトテンプレートを取得
2. テンプレートの変数を埋める:
   - `{仕様書の Todo IMPL 内容}`: 仕様書から対象 Todo の IMPL セクションを引用
   - `{プロジェクト情報}`: CLAUDE.md + package.json 等から要約
   - `{関連コード}`: 仕様書の「参照すべきファイル」を Read して要約（10,000文字以内）
   - `{設計決定事項}`: 仕様書から該当セクションを引用（あれば）
3. 埋めたプロンプトを一時ファイルに書き出す
4. Codex に委任:
   ```bash
   cat /tmp/codex-tdd-prompt.md | codex exec -m gpt-5.4 --sandbox workspace-write --full-auto - 2>/dev/null
   ```
5. 結果を確認:
   - 成功: テストコマンド（`npm test` 等）でテストが通ることを確認 → Claude がコミット
   - 失敗: エラー情報を含めてプロンプトを改善し、リトライ（最大3回）
   - 3回失敗: Claude が `references/agents/tdd-developer.md` で直接実装（フォールバック）

#### ラベルなし → Claude が直接実装（従来モードと同じ）

1. `references/agents/implementer.md` を Read
2. ロール定義の手順に従って実装する
3. 実装完了後、変更をコミットする

## Step 2 — VERIFY の詳細

### 従来モード（3体並列レビュー）

以下の3ファイルを Read し、それぞれ Agent（sonnet）で **並列** 起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

各エージェントには仕様書パス + 対象 Review ID を渡す。

#### 結果の統合

- 3体すべて PASS → 全体 PASS
- 1体でも FAIL → 全体 FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY も同じ3体並列で実行する

### Codex モード（[TDD] タスクのハイブリッドレビュー）

[TDD] ラベルなしの場合は従来モードと同じ（上記の3体並列）。

[TDD] ラベルありの場合、以下の 2 段階で実行する:

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

従来モードと同じ3体並列レビューを実行する。
codex review では検出できない仕様適合性・セキュリティ・プロジェクト慣例を補完する。

#### 結果の統合

- codex review PASS + 3体すべて PASS → 全体 PASS
- いずれかが FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY: codex review + 3体並列の両方を再実行する

## Step 4 — UPDATE の詳細

各 Todo の全 Step 完了後、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`

これにより、仕様書を見るだけで各 Todo の進捗が把握できる。
