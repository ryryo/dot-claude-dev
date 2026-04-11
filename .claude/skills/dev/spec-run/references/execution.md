# 実行プロトコル（Claudeモード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT      仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Preflight フェーズ     Preflight セクション該当時のみ、Claude main session が順次実行（スキップ条件あり）
Step 1 — IMPL         仕様書の Todo に従って実装する
Step 2 — VERIFY       複雑さに応じてレビュワー 1体 or 3体を起動してレビューする
Step 3 — FIX          FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE       仕様書のチェックボックスを更新する
```

## Step 0 — CONTEXT

### シングルモード

仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）。

### ディレクトリモード

1. spec.md の「参照すべきファイル」を全て Read する
2. tasks.json を Read して全体構造（`gates`, Todo の `id`/`gate`/`title`/`dependencies`）を把握する
3. 各 Todo の `impl` フィールドは**この時点では読まない**（部分読み込みで後述）

## Preflight フェーズ（該当時のみ）

仕様書に `## Preflight` セクション（通常モード）または `tasks.json` の `preflight` 配列（ディレクトリモード）が存在し、項目が 1 件以上ある場合のみ実行する。該当が無ければ何もせず Step 1 へ進む。

### 実行手順

1. Preflight 項目を記載順に処理する（依存関係はないため順序通り）
2. 各項目を判定する:
   - `manual: false`（自動実行可能）→ Bash ツールで `command` を実行
   - `manual: true`（ユーザー手動操作必須）→ AskUserQuestion で操作内容と完了確認を提示し、完了報告を待つ
3. 実行成功 → 仕様書の該当チェックボックスを `[x]` に更新する
4. 全 Preflight 完了後、Step 1 へ進む

### Preflight 失敗時

Claude main session での実行が失敗した場合:

1. sandbox 起因ではないため diagnose スクリプトは不要
2. エラー内容をユーザーに直接報告する
3. AskUserQuestion で以下を選択させる:
   - 1. 手動で対応後リトライ
   - 2. この Preflight 項目をスキップして残りの Gate 実行を継続（リスク警告付き）
   - 3. 作業中断

### 注意

- Preflight は Gate/Todo とは独立して実行する（Gate 冒頭ではなく spec-run 起動直後に1回だけ）
- **Preflight セクションが無い場合は完全にスキップ**（既存仕様書との後方互換のため警告なし）
- Codex モードとClaudeモードで Preflight フェーズの動作は完全に同一

## Step 1 — IMPL

### シングルモード

仕様書の Todo IMPL 内容に従って実装する。

### ディレクトリモード

tasks.json から**現在の Todo の `impl` フィールドだけ**を取得して実装する。
他の Todo の impl は読まない（コンテキストウィンドウ節約）。

```
取得例: tasks.json の todos 配列から id == "A1" の要素を抽出し、impl フィールドを使用
```

### 共通

- **[TDD] ラベルあり / `tdd: true`**: テストを先に書き、失敗を確認してから実装する（RED→GREEN→REFACTOR）。詳細は `roles/tdd-developer.md` を参照
- **ラベルなし**: 仕様に忠実に実装する。詳細は `roles/implementer.md` を参照

実装完了後、変更をコミットする。

## Step 2 — VERIFY

### 複雑さ判断

Claude が Todo の内容を以下の観点で総合判断し、レビューモードを決定する:

| 判断要素 | SKIP（レビュー不要） | シンプル寄り | 複雑寄り |
|----------|---------------------|------------|---------|
| 変更内容 | ドキュメント・設定・コメントのみ | コード変更あり（軽微） | コード変更あり（重要） |
| 変更ファイル数 | — | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | — | 局所的 | 複数モジュール横断 |
| リスク | なし（実行パスに影響しない） | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | ロジック変更なし | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

### SKIP — レビュー不要

変更がドキュメント（`.md`）、コメント、設定ファイルのみでロジックを含まない場合、VERIFY をスキップして自動 PASS とする。

記録形式: `> **Review XX**: ⏭️ SKIPPED (docs only)`

Step 3（FIX）も不要。そのまま Step 4（UPDATE）へ進む。

### シンプルモード — レビュワー 1体

`agents/reviewer-correctness.md` を Agent（sonnet）で起動する。
正確性・仕様適合の観点で全体をカバーする。

### 複雑モード — レビュワー 3体並列

以下の3ファイルを Read し、それぞれ Agent（sonnet）で **並列** 起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

各エージェントには仕様書パス + 対象 Review ID を渡す。

### 結果の統合

- すべて PASS → 全体 PASS
- 1体でも FAIL → 全体 FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY も同じモード（シンプル/複雑）で実行する

## Step 4 — UPDATE

### シングルモード

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。

### ディレクトリモード

spec.md のチェックボックスを `[x]` に更新し、Review 結果を blockquote に記入する:

```markdown
- [x] **Todo A1**: カラーコントラスト修正
  > **Review A1**: ✅ PASSED
```

---

## worktree モード（オプション）

SKILL.md の Step 4 で worktree 使用を選択した場合、本 execution プロトコルは **worktree 内の cwd** で実行される。差分は以下の通り。

### 前提

- `cd $WORKTREE_PATH` が Step 4.6 で実行済み
- Bash tool の cwd は worktree 内
- 以降の全 Bash / ファイル操作は worktree 内で完結する

### 各 Step の差分

| Step | 差分 |
|------|------|
| Step 0 CONTEXT | 仕様書の「参照すべきファイル」は worktree 内のパスで Read する。worktree は master から派生なので同じファイルが存在する |
| Preflight フェーズ | worktree 内で実行（`node_modules` / `.env` は worktree 側に配置される）。master 側には影響しない |
| Step 1 IMPL | worktree 内のファイルを直接編集。コミットも worktree 内（`git commit` は自動的に feature/{slug} ブランチに対して行われる） |
| Step 2 VERIFY | レビュワー Agent は worktree 内の差分に対してレビューする。Agent の cwd は継承される |
| Step 3 FIX | worktree 内で修正、再コミット |
| Step 4 UPDATE | **worktree 内の spec.md** のチェックボックスを更新。master 側の spec.md は完了処理の merge 後に反映される |

### 注意

- master 側の spec.md を直接編集してはならない（cwd が worktree の前提が崩れる）
- Codex モードで worktree を使う場合は `references/codex-execution.md` の該当セクションを参照
- worktree セットアップ手順は `references/worktree-setup.md`、完了時の merge / cleanup は `references/worktree-teardown.md` を参照
