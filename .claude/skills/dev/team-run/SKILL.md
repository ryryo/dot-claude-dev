---
name: dev:team-run
description: |
  承認済みの team-plan 計画（task-list.json）を Agent Teams + Subagent ハイブリッドで並行実行。
  Git Worktree でファイル分離。Delegate mode / Plan Approval / hooks にフル準拠。

  Trigger:
  dev:team-run, /dev:team-run, チーム実行, team run
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - TaskCreate
  - TaskList
  - TaskGet
  - TaskUpdate
  - TeamCreate
  - TeamDelete
  - SendMessage
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Evaluate whether the team-run skill execution is complete.
            Context: $ARGUMENTS

            The team-run skill has 7 steps. Check if ALL are done:
            1. Plan selected and validated
            2. Git worktree created
            3. Team created and tasks registered
            4. ALL waves executed (all tasks completed)
            5. Review/feedback loop done (or skipped)
            6. PR created via gh pr create
            7. TeamDelete called and results presented

            IMPORTANT:
            - If stop_hook_active is true, allow stopping to prevent infinite loops.
            - If execution failed with an unrecoverable error, allow stopping.
            - If user explicitly requested cancellation, allow stopping.

            Return {"ok": false, "reason": "Step N incomplete. Next: [action]"} to continue,
            or {"ok": true} to allow stopping.
---

# dev:team-run スキル

承認済みの team-plan 計画を Agent Teams + Subagent ハイブリッドで並行実行する。

## 必須リソース

| リソース | 読み込みタイミング | 用途 |
|----------|-------------------|------|
| `references/agent-prompt-template.md` | Step 4（Teammate スポーン前） | 統一 Teammate プロンプト |
| `references/role-catalog.md` | Step 4（role_directive 取得） | ロール定義の参照 |
| `scripts/setup-worktree.sh` | Step 2（環境セットアップ） | Worktree セットアップ（チーム全体で1つ） |
| `scripts/cleanup-worktree.sh` | Step 6/7（クリーンアップ） | Worktree 削除 |

**Teammate スポーン時、必ず `references/agent-prompt-template.md` を Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

---

## Step 1: 計画選択 + 検証

### 1-1: 計画選択

1. `docs/features/team/` 以下のディレクトリを列挙する
2. 各ディレクトリの `task-list.json` を Read し、`metadata.status` が `"completed"` のものを除外する（未定義は `"pending"` 扱い）
3. 残った計画の metadata を表示し、AskUserQuestion で選択:

```
Q: 実行する計画を選択してください。

【計画一覧】
1. {YYMMDD}_{slug} ({totalTasks}タスク / {totalWaves} Wave)
2. {YYMMDD}_{slug} ({totalTasks}タスク / {totalWaves} Wave)
...

選択肢:
- 1
- 2
- パスを直接指定
```

計画が0件の場合: 「先に `dev:team-plan` を実行して計画を作成してください」と案内して終了する。

選択後、`task-list.json` のパスを `$PLAN_DIR` として保持し、以降の Step で使用する。

### 1-2: Pre-flight 検証

`$PLAN_DIR/task-list.json` を Read で読み込み、以下の検証を**全タスク**に対して実施する:

- [ ] 8必須フィールドが存在する: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `taskPrompt`
- [ ] Wave構造が `waves[].tasks[]` フラット配列 + `role` フィールド形式である
- [ ] `taskPrompt` が具体的な実装指示を含む（ファイルパス・操作内容が明記されている）
- [ ] `story-analysis.json` の `fileOwnership` が存在し、各ロールのファイル所有範囲が定義されている

判定:
- **全タスク合格** → Step 2 へ進む
- **1つでも不合格** → **即座に停止**。不合格タスクのIDと欠損フィールドをユーザーに報告し、`dev:team-plan` での修正を案内する

**禁止**: `taskPrompt` が欠損・曖昧なタスクに対して、team-run 側でプロンプトを即興生成して補完すること。計画の品質問題は plan 側で修正する。

---

## Step 2: 環境セットアップ

### 2-1: Git 環境のクリーン化

Worktree 作成前に、Git の状態をクリーンにする。

1. **未コミット変更の確認**:

```bash
git status --porcelain
```

- クリーン → 次へ
- 変更あり → AskUserQuestion でユーザーに確認:
  - 「コミットする」→ Lead が git add + git commit を実行
  - 「スタッシュする」→ `git stash` を実行
  - 「中止する」→ スキル実行を中止

2. **リモートとの同期**:

```bash
git push
git pull --rebase
```

- push/pull 成功 → 次へ
- コンフリクト発生 → AskUserQuestion でユーザーに報告し、手動解決を案内。解決後に再実行
- リモート未設定（新規ローカルブランチ等）→ スキップして次へ

3. **最終確認**:

```bash
git status
```

ワーキングツリーがクリーンであること、かつリモートと同期済みであることを確認してから 2-2 に進む。

### 2-2: Worktree セットアップ

`scripts/setup-worktree.sh` を実行:

```bash
WORKTREE_PATH=$(bash .claude/skills/dev/team-run/scripts/setup-worktree.sh {slug})
```

スクリプトの処理内容:
1. 現在の HEAD から `feature/{slug}` ブランチを作成
2. `.worktrees/{slug}/` にチーム全体で1つの worktree を作成
3. worktree の絶対パスを出力

`$WORKTREE_PATH` を以降のすべてのステップで Teammate の cwd として使用する。

### 2-3: Worktree パスの検証

worktree ディレクトリが存在し、正しいブランチをチェックアウトしていることを確認:

```bash
git -C .worktrees/{slug} branch --show-current
# → feature/{slug} であること
```

---

## Step 3: チーム作成 + タスク登録

### 3-1: チーム作成

```
TeamCreate({ team_name: "team-run-{slug}", description: "ネイティブ並行実装: {slug}" })
```

### 3-2: タスク登録

`$PLAN_DIR/task-list.json` の全タスクを TaskCreate で登録する。Wave間の `blockedBy` も設定。

タスク登録時、以下のメタデータを付与:
- `wave`: Wave番号
- `role`: ロール名
- `requirePlanApproval`: true/false（task-list.json から取得、未設定は false）

### 3-3: Delegate mode の宣言

Lead は以下の役割に限定する:
- タスク割り当て・依存関係管理
- Plan Approval の審査
- Wave 間の遷移制御
- エラーハンドリング・エスカレーション
- ユーザーへの報告・確認

**禁止**: Lead がコードを書く、ファイルを編集する、実装に手を出す

---

## Step 4: Wave 実行ループ

### 4-1: Wave N の Teammate スポーン（実装系ロール）

現在の Wave に属する実装系ロール（designer, frontend-developer, backend-developer, tdd-developer, fullstack-developer, copywriter, architect, researcher）ごとに Teammate をスポーンする。

**プロンプト構築手順**:

1. `references/agent-prompt-template.md` を Read で読み込む
2. `references/role-catalog.md` から該当ロールの `role_directive` を取得
3. `$PLAN_DIR/story-analysis.json` から該当ロールの `customDirective` と `fileOwnership` を取得
4. `$PLAN_DIR/task-list.json` からタスクの `description`, `inputs`, `outputs`, `taskPrompt` を取得
5. `needsPriorContext: true` の場合、プロンプトの先頭に以下を付加:

   ```
   Before starting, check what was changed by the previous task:
   - Run: git log --oneline -3
   - Run: git diff HEAD~1 --stat
   - Run: git diff HEAD~1
   Understand the prior changes, then proceed with the following task:
   ```

6. テンプレートの変数を置換して Teammate プロンプトとして使用
7. `requirePlanApproval: true` の場合、プロンプトに Plan Approval 指示を追加

**Teammate スポーン設定**:

```
model: opus  （基本は opus。明らかに軽量なタスクのみ sonnet）
run_in_background: true
cwd: $WORKTREE_PATH  ← 全 Teammate が共通の worktree で作業（fileOwnership で論理分離）
```

**モデル選択戦略**:

| ロール | モデル | 理由 |
|--------|--------|------|
| designer, architect | opus | 設計判断に高い推論力が必要 |
| frontend-developer, backend-developer, fullstack-developer | opus | 実装品質・複雑な判断 |
| tdd-developer | opus | TDD の RED/GREEN/REFACTOR サイクルに高い判断力が必要 |
| copywriter | sonnet | 文章生成は sonnet で十分 |
| researcher | opus | 分析・調査に高い推論力が必要 |
| reviewer（Subagent） | opus | レビュー品質に高い分析力が必要 |

**Plan Approval フロー**（`requirePlanApproval: true` のタスクのみ）:

1. Teammate が TaskUpdate で `in_progress` に設定
2. Teammate がタスクを分析し、実装計画を SendMessage で Lead に送信
3. Lead が計画を検証:
   - fileOwnership の違反がないか
   - 他タスクとの競合がないか
   - 技術的に妥当か
4. 承認 → SendMessage で Teammate に実装開始を通知
5. 拒否 → フィードバック付きで計画修正を要求（最大2回、3回目は自動承認）

**Self-claim（同一 Wave 内）**:

Teammate が自分のタスクを完了した後、同一 Wave 内に未割り当て（owner が未設定）のタスクがあれば、自律的に TaskUpdate で owner を設定して着手する。この動作はプロンプトテンプレートの「Self-claim Protocol」セクションで指示する。

### 4-2: Wave N のレビュー系ロール → Subagent

レビュー系ロール（reviewer, tester）は Subagent（Task ツール）で実行する。

```
Task({
  description: "{レビュープロンプト}",
  allowed_tools: ["Read", "Glob", "Grep", "Bash"],
  model: "opus"
})
```

理由:
- Read-only 操作のみで十分
- Subagent はコンテキスト汚染を防ぐ
- 結果を summary で Lead に返却でき、構造化された報告が得られる

レビュー Subagent のプロンプトには以下を含める:
- レビュー対象のファイル一覧（worktree 内の差分で特定）
- role-catalog.md の reviewer/tester の role_directive
- task-list.json の当該タスクの description と taskPrompt
- **出力形式**: 改善候補を重要度（高/中/低）付きで報告

### 4-3: hooks

**TeammateIdle hook**:

Teammate が待機状態に入る前に以下を検証:
- [ ] 担当タスクの outputs に記載されたファイルが実際に存在する
- [ ] コミットされている（`git status` でクリーンな状態）
- [ ] 同一 Wave 内に Self-claim 可能なタスクがない

品質未達の場合: Teammate に SendMessage で不足事項を通知し、作業を継続させる

**TaskCompleted hook**:

タスク完了前に以下を検証:
- [ ] outputs ファイルが存在する
- [ ] lint/format エラーがない（プロジェクトに lint 設定がある場合）
- [ ] コミットされている

検証失敗時: TaskUpdate で completed にせず、Teammate に修正を指示

### 4-4: Wave 完了判定

- [ ] 当該 Wave の**全タスク**が TaskList で `completed` になっている
- [ ] 各タスクの成果物（outputs）が**ファイルとして実際に存在する**ことを確認
- [ ] worktree にコミットがある（`git log` で確認）

判定合格 → 次 Wave の Teammate をスポーン（4-1 に戻る）
全 Wave 完了 → Step 5 へ

### 4-5: Teammate 間メッセージプロトコル

実装 Teammate がタスク完了時に SendMessage で送信する内容:
- 変更したファイルの一覧
- 設計判断の要約（なぜその実装にしたか）
- 次 Wave の Teammate への引き継ぎ事項

レビュー Subagent の結果は Lead が受け取り、改善候補として Step 5 で処理する。

---

## Step 5: レビュー・フィードバックループ

### 5-1: Reviewer 報告の集約

最終 Wave のレビュー Subagent（または Reviewer Teammate）からの改善候補を集約する。

### 5-2: ユーザーへの提示

AskUserQuestion でレビュー結果をユーザーに提示:

```
Q: レビュワーから以下の改善候補が挙がりました。修正する項目を選択してください。
- [高] 候補1: {改善内容}
- [中] 候補2: {改善内容}
- [低] 候補3: {改善内容}
- 対応不要（完了へ進む）
```

### 5-3: フィードバック分岐

- **対応なし** → Step 6 へ
- **対応あり** → 5-4 へ

### 5-4: Fix タスク生成

ユーザーが選択した改善候補ごとに fix タスクを生成:

1. 各改善候補から対象ファイル・修正内容・適切なロールを特定
2. fix タスクの `taskPrompt` を Lead が構築:

   ```
   以下のレビュー指摘に基づいて修正してください:

   指摘内容: {改善候補の内容}
   対象ファイル: {ファイルパス}

   修正方針:
   - {具体的な修正手順}

   修正後、変更内容を簡潔に報告してください。
   ```

3. `$PLAN_DIR/task-list.json` に新しい Wave（fix wave）として追加し Write で保存
4. TaskCreate で fix タスクを登録

### 5-5: Fix Teammate スポーン

Step 4-1 と同じ手順で fix タスクの Teammate をスポーン:
- 共通の worktree で作業（既存の worktree を再利用）
- `needsPriorContext: true` なので git diff プレフィックスを付加

### 5-6: Fix 完了確認

Step 4-4 と同じ品質ゲートを適用。

### 5-7: 再レビュー判断

AskUserQuestion でユーザーに確認:

```
Q: Fix が完了しました。再レビューを実施しますか？
- 再レビュー実施
- 不要（完了へ進む）
```

- **再レビュー** → 新しい reviewer Subagent をスポーンし、5-1 に戻る
- **不要** → Step 6 へ

**ループ制限**: 最大3ラウンド（fix + 再レビュー）。超過時はユーザーに継続可否を確認。

---

## Step 6: PR作成 + クリーンアップ

### 6-1: コミット状態の確認

worktree 内で全変更がコミット済みであることを確認:

```bash
git -C $WORKTREE_PATH status --porcelain
```

未コミットの変更がある場合: AskUserQuestion でユーザーに報告し対応を確認。

### 6-2: PR 作成

feature ブランチを push:

```bash
git -C $WORKTREE_PATH push -u origin feature/{slug}
```

```bash
gh pr create --title "feat: {slug}" --body "$(cat <<'EOF'
## Summary
- {story-analysis.json の goal}
- {完了タスク数} / {全タスク数} タスク完了
- {Wave数} Wave で並行実行

## Changes
{各ロールの変更概要}

## Review Notes
{レビュー結果の要約}
EOF
)"
```

### 6-3: Worktree クリーンアップ

```bash
bash .claude/skills/dev/team-run/scripts/cleanup-worktree.sh {slug}
```

---

## Step 7: 結果集約 + TeamDelete

### 7-1: 結果集約

全タスク完了後、各 Teammate からの報告を集約してユーザーに提示:

```
## 実行結果

| タスク | ロール | Wave | 状態 | 概要 |
|--------|--------|------|------|------|
| {タスク1} | {ロール} | {Wave} | 完了 / 失敗 | {概要} |
```

### 7-2: 計画ステータス更新

`$PLAN_DIR/task-list.json` の `metadata.status` を `"completed"` に更新して Write で保存する。

### 7-3: TeamDelete

```
TeamDelete()
```

---

## エラーハンドリング

| 状況 | 対応 |
|------|------|
| Teammate 無応答（5分） | SendMessage で状況確認 |
| 状況確認後も無応答（5分） | Teammate を再スポーン（下記参照） |
| Worktree セットアップ失敗 | エラーメッセージをユーザーに報告、手動対応を案内 |
| Plan Approval 3回拒否 | 自動承認し、リスクをユーザーに報告 |
| lint/build 失敗（TaskCompleted hook） | Teammate に修正を指示（最大3回） |
| 3回リトライ失敗 | ユーザーに報告、指示を仰ぐ |

### Teammate 遅延・失敗時のエスカレーション手順

```
1. SendMessage で状況確認（5分無応答後）
     ↓ 5分待っても応答なし
2. 当該 Teammate のみ shutdown_request → 同じタスクで新 Teammate を再スポーン
     ↓ 再スポーンも失敗（3回）
3. AskUserQuestion でユーザーに報告し、指示を仰ぐ
   選択肢:
   - タスクをスキップして次へ進む
   - 中止する
```

**禁止事項**:
- Lead が**ユーザー承認なしに** Teammate の作業を代行しない（Delegate mode 厳守）
- 1つの Teammate が遅延しても、**他の Teammate をシャットダウンしない**

---

## 重要な注意事項

1. **Delegate mode 厳守**: Lead はコードを書かない。実装は全て Teammate に委譲する
2. **テンプレート忠実度**: agent-prompt-template.md を毎回 Read して使用する。キャッシュや記憶で代替しない
3. **fileOwnership 遵守**: Teammate は自分のファイル所有権範囲外を編集しない
4. **計画の品質保証**: taskPrompt が不十分なタスクを team-run 側で補完しない。plan 側での修正を案内する
5. **reviewer/tester はSubagent**: レビュー系ロールは Task ツールで実行し、コンテキスト汚染を防ぐ
