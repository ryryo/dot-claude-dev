# 実行プロトコル（Claudeモード, v3）

各 Gate を順番に実行する。**Gate 単位で契約（Goal/Constraints/AC）を実装エージェントに渡し、AC が成立したことをもって完了を判定する。**

## 実行ステップ

```
Step 0 — CONTEXT      仕様書の「参照すべきファイル」を全て Read（最初の Gate 着手前に1回だけ）
Preflight フェーズ     Preflight 該当時のみ、Claude main session が順次実行
Step 1 — IMPL         Gate 契約に基づいて実装（直接 or エージェント委任）
Step 2 — VERIFY       全 AC を検証し、複雑さに応じてレビュワーを起動する
Step 3 — FIX          FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE       tasks.json を更新（gate.passed / acceptanceCriteria / review / progress / status）
```

## Step 0 — CONTEXT

最初の Gate 着手前に 1 回だけ実行する。

1. spec.md の「参照すべきファイル」を全て Read する
2. tasks.json を Read して以下を把握する:
   - 全 `gates[]`（id / title / dependencies / goal / constraints / acceptanceCriteria / todos）
   - `preflight[]`
   - `progress` / `status`

## Preflight フェーズ（該当時のみ）

`tasks.json.preflight[]` が 1 件以上あるときのみ実行する。

1. 各項目を記載順に処理する
2. 判定:
   - `manual: false` → Bash で `command` を実行
   - `manual: true` → AskUserQuestion で操作内容と完了確認を提示し、完了報告を待つ
3. 完了確認: 各 Preflight の `ac` が成立しているか検証する（記述されたコマンド出力等を確認）
4. 成立 → tasks.json の `preflight[].checked = true` を Edit で書き込む
5. 全 Preflight 完了後、Step 1 へ進む

### Preflight 失敗時

1. エラー内容をユーザーに直接報告する
2. AskUserQuestion で 3 択を提示:
   - 手動で対応後リトライ
   - この項目をスキップして残りの Gate 実行を継続（リスク警告付き）
   - 作業中断

## Step 1 — IMPL

各 Gate について以下を実行する。

### 1-1. Gate 契約の組み立て

tasks.json から現在の Gate のフィールドを抽出する:

- `goal.what` / `goal.why`
- `constraints.must` / `constraints.mustNot`
- `acceptanceCriteria[]`
- `todos[]`（id / title / affectedFiles / dependencies / tdd）

### 1-2. 実行戦略の決定

Claude が Gate の内容を総合判断し、**実行モード**と**モデル**を決定する。

#### 実行モード

| モード                     | 判断基準                                                                                                                                                | 実行方法                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **直接実装**（デフォルト） | 会話コンテキストが実装に有用、または特段の理由がない場合                                                                                                | main session が直接実装する                                              |
| **エージェント委任**       | Gate 契約 + 参照ファイルだけで十分実装できる（会話コンテキストへの依存が低い） + 編集するファイルの独立性が高く、並行実装した方が実装が早く完了できる。 | Agent ツールで実装エージェントを起動。独立した Todo が複数あれば並列起動 |

#### モデル選択（エージェント委任時）

| 難易度 | モデル                    | 目安                                                                |
| ------ | ------------------------- | ------------------------------------------------------------------- |
| **高** | opus（extended thinking） | 複数モジュール横断、複雑なロジック、認証・データ処理・API、状態管理 |
| **中** | opus                      | 標準的なコード実装、テスト作成                                      |
| **低** | sonnet                    | 設定変更、単純な追加、パターンの踏襲、ドキュメント                  |

直接実装ではモデル選択は不要（main session のモデルで実行される）。

#### ロール選択（エージェント委任時）

Gate 内の Todo に応じてロールを選択する:

- `tdd: true` の Todo を含む → `roles/tdd-developer.md`
- 含まない → `roles/implementer.md`

### 1-3. Gate 契約の引き渡し

エージェント委任の場合、以下を渡す:

- Gate 契約（Goal / Constraints / AC / Todo リスト）
- spec.md の「設計決定事項」「アーキテクチャ詳細」サマリ
- 参照すべきファイルの内容

直接実装では、main session が同じ契約情報を参照しながら実装する。

### 1-4. 実装と AC 進捗書き込み

実装者（main session またはエージェント）は以下を行う:

1. AC ごとに「成立する状態」を作る（手順は自律的に判断）
2. AC が成立するたびに tasks.json の該当 AC `checked: true` を Edit で書き込む
3. 全 AC 成立後、変更をコミット

エージェントモードの場合、エージェントは main session に Gate 完了を報告する。
main session は完了を確認し、Step 2 へ進む。

## Step 2 — VERIFY

### Gate Review の複雑さ判断

Claude が Gate の内容を以下の観点で総合判断し、レビューモードを決定する:

| 判断要素       | SKIP（レビュー不要）         | シンプル寄り               | 複雑寄り                     |
| -------------- | ---------------------------- | -------------------------- | ---------------------------- |
| 変更内容       | docs / config / コメントのみ | コード変更あり（軽微）     | コード変更あり（重要）       |
| 変更ファイル数 | —                            | 1-2 ファイル               | 3 ファイル以上               |
| 影響範囲       | —                            | 局所的                     | 複数モジュール横断           |
| リスク         | なし                         | 低（設定、ユーティリティ） | 高（認証、データ処理、API）  |
| ロジック複雑度 | なし                         | 単純な追加・変更           | 条件分岐 / 状態管理 / 非同期 |

**判断に迷ったら複雑モードを選択する。**

### SKIP — レビュー不要

変更がドキュメント / コメント / 設定のみでロジックを含まない場合、VERIFY をスキップして自動 PASS。

`gates[].review = { result: "SKIPPED", fixCount: 0, summary: "docs only" }` を書き込む。

Step 3（FIX）も不要。Step 4（UPDATE）へ進む。

### シンプルモード — レビュワー 1 体

`agents/reviewer-correctness.md` を Agent（sonnet）で起動する。

### 複雑モード — レビュワー 3 体並列

以下の 3 ファイルを Read し、Agent（sonnet）で **並列** 起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

各エージェントには **Gate ID + Gate 契約 + 変更差分** を渡す。

### AC 検証

レビュー結果と並行して、各 AC の検証手段（コマンド / テスト / HTTP など）を実行し、`gates[].acceptanceCriteria[].checked` が全て `true` になっていることを確認する。実装エージェントが書き漏れた AC があれば main session が補完する。

### 結果の統合

- すべて PASS + 全 AC checked → 全体 PASS
- 1 体でも FAIL or 未 checked AC あり → 全体 FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY も同じモード（シンプル / 複雑）で実行する

## Step 3 — FIX

FAIL の場合のみ。最大 3 ラウンド。

実装エージェント（または main session）が指摘内容を反映して修正し、再度 VERIFY を実行する。

## Step 4 — UPDATE

**tasks.json のみを Edit して更新する。spec.md は直接編集しない**（PostToolUse hook が sync-spec-md を起動して spec.md を自動再生成する）。

### 更新対象フィールド

1. **該当 Gate の `acceptanceCriteria[].checked`**: 全 AC を `true` に
2. **該当 Gate の `review`**: `{ result: "PASSED"|"FAILED"|"SKIPPED", fixCount: n, summary: "..." }`
3. **該当 Gate の `passed`**: 全 AC checked + `review.result` が PASSED または SKIPPED なら `true`
4. **トップレベル `progress`** を再計算:
   - `gatesTotal = gates.length`
   - `gatesPassed = gates.filter(g => g.passed).length`
   - `currentGate` = 最初の `passed=false` の Gate.id（全 passed なら null）
   - `currentGateAC` = currentGate の AC checked 数 / 総数
5. **トップレベル `status`** を再計算:
   - `gatesPassed == 0 && currentGateAC.passed == 0` → `"not-started"`
   - `gatesPassed < gatesTotal` → `"in-progress"`
   - `gatesPassed == gatesTotal && !reviewChecked` → `"in-review"`
   - `gatesPassed == gatesTotal && reviewChecked` → `"completed"`

Edit 後、PostToolUse hook が sync-spec-md.mjs を起動し、spec.md の generated 領域が再生成される。

**hook 未発火時のフォールバック**: Edit 後に Read で spec.md を確認し、generated 領域が更新されていなければ明示実行:

```bash
node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs <tasks.json-path>
```

---

## worktree モード（オプション）

SKILL.md のステップ 4 で worktree 使用を選択した場合、本プロトコルは **worktree 内の cwd** で実行される。

### 前提

- `cd $WORKTREE_PATH` が `worktree-setup.md` フェーズ 2 末尾で実行済み
- Bash tool の cwd は worktree 内
- 以降の全 Bash / ファイル操作は worktree 内で完結する

### 各 Step の差分

| Step           | 差分                                                                                   |
| -------------- | -------------------------------------------------------------------------------------- |
| Step 0 CONTEXT | 仕様書を worktree 内のパスで Read（worktree は base から派生なので同じ構造）           |
| Preflight      | worktree 内で実行（`node_modules` / `.env` は worktree 側に配置）                      |
| Step 1 IMPL    | worktree 内のファイルを編集、worktree 内でコミット（自動的に feature/{slug} ブランチ） |
| Step 2 VERIFY  | レビュワー Agent は worktree の差分に対してレビュー（cwd 継承）                        |
| Step 3 FIX     | worktree 内で修正、再コミット                                                          |
| Step 4 UPDATE  | worktree 内の tasks.json を更新 → hook が worktree 内の spec.md を再生成               |

### 注意

- base 側の spec.md / tasks.json を直接編集してはならない
- worktree のセットアップ手順は `references/worktree-setup.md`、完了時の merge / cleanup は `references/worktree-teardown.md` を参照
