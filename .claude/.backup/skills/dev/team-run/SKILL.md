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
model: opus
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Evaluate whether the team-run skill execution is complete.
            Context: $ARGUMENTS

            The team-run skill has 8 steps. Check if ALL are done:
            1. Plan selected and validated
            2. Git worktree created
            3a. Team created (TeamCreate succeeded)
            3b. Tasks registered (TaskCreate for all tasks)
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

# dev:team-run

承認済みの team-plan 計画を Agent Teams + Subagent ハイブリッドで並行実行する。

## ⛔ FORBIDDEN

| ID  | 禁止                               | 正しい方法                      |
| --- | ---------------------------------- | ------------------------------- |
| F1  | Lead がコード編集・実装コード調査  | Teammate に委譲                 |
| F2  | TeamCreate 前に Teammate スポーン  | 必ず Step 3b 完了後             |
| F3  | Worktree セットアップのスキップ    | 必ず Step 2 で実行              |
| F4  | テンプレートのキャッシュ・即興生成 | 毎回 Read() 必須                |
| F5  | taskPrompt 欠損タスクの実行        | STOP → dev:team-plan で修正案内 |
| F6  | TeamCreate 前の TaskCreate         | 必ず Step 3a ゲート通過後       |
| F7  | プロトコル Read のスキップ         | 各 Step で必ず Read() してから実行 |

## 実行プロトコル

**各 Step は `Read()` でプロトコルを読み込み → 手順実行 → ゲート確認 の順で進める。スキップ禁止（F7）。**

### Step 1: 計画選択 + Pre-flight

```
Read("references/step-1-select-plan.md") → 実行
```
ゲート: `$PLAN_DIR` が有効 + Pre-flight 全合格

---

### Step 2: Git Worktree セットアップ

```
Read("references/step-2-worktree.md") → 実行
```
ゲート: `$WORKTREE_PATH` が有効 + ブランチが `feature/{slug}`

---

### Step 3a: チーム作成

```
Read("references/step-3a-team-create.md") → 実行
```
ゲート: TeamCreate 成功。失敗 → **即停止（F6）**

---

### Step 3b: タスク登録（Teammate 委譲用）

```
Read("references/step-3b-task-register.md") → 実行
```
ゲート: 全タスク登録済み + **全タスク owner 空**（Lead 未割当）。以降 Delegate mode（F1）

---

### Step 4: Wave 実行ループ

```
Read("references/step-4-wave-exec.md") → 実行
Teammate スポーン時: Read("references/teammate-spawn-protocol.md")
エラー時: Read("references/error-handling.md")
```
ゲート: 全 Wave の全タスクが `completed`

---

### Step 5: レビュー・フィードバックループ

```
Read("references/step-5-review-feedback.md") → 実行
```
ゲート: ユーザー承認 or 3ラウンド超過

---

### Step 6: PR作成 + クリーンアップ

```
Read("references/step-6-pr-cleanup.md") → 実行
```
ゲート: PR URL を取得

---

### Step 7: 結果集約 + TeamDelete

```
Read("references/step-7-results-cleanup.md") → 実行
```

---

## エラーハンドリング

```
Read("references/error-handling.md")
```
要約: 5分無応答 → SendMessage 確認 → 再スポーン → 3回失敗 → AskUserQuestion でユーザーに報告
