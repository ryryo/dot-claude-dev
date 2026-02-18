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

# dev:team-run

承認済みの team-plan 計画を Agent Teams + Subagent ハイブリッドで並行実行する。

## ⛔ FORBIDDEN

| ID  | 禁止                               | 正しい方法                      |
| --- | ---------------------------------- | ------------------------------- |
| F1  | Lead がコード編集・実装コード調査  | Teammate に委譲                 |
| F2  | TeamCreate 前に Teammate スポーン  | 必ず Step 3 完了後              |
| F3  | Worktree セットアップのスキップ    | 必ず Step 2 で実行              |
| F4  | テンプレートのキャッシュ・即興生成 | 毎回 Read() 必須                |
| F5  | taskPrompt 欠損タスクの実行        | STOP → dev:team-plan で修正案内 |

## Teammate スポーン

**毎回このプロトコルに従う。省略・記憶で代替しない。**

```
protocol = Read("references/teammate-spawn-protocol.md")
→ protocol の手順 A〜F に従って Teammate をスポーン
```

---

## Step 1: 計画選択 + Pre-flight

DO:

1. `docs/features/team/` 以下の `task-list.json` を Glob で列挙
2. `metadata.status` が `"completed"` のものを除外し、AskUserQuestion で選択
3. 選択した計画のパスを `$PLAN_DIR` として保持
4. Pre-flight 検証（全タスクに対して）:
   - 8必須フィールド: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `taskPrompt`
   - Wave構造: `waves[].tasks[]` フラット配列 + `role` フィールド
   - `taskPrompt` が具体的（ファイルパス・操作内容が明記）
   - `story-analysis.json` の `fileOwnership` が存在

ゲート: Pre-flight 全合格。1つでも不合格 → **即停止** + 不合格タスク ID・欠損フィールドを報告 + `dev:team-plan` での修正を案内

---

## Step 2: Git Worktree セットアップ

DO:

1. `git status --porcelain` で未コミット変更を確認（変更あり → AskUserQuestion で対応選択）
2. `git push && git pull --rebase` でリモート同期（コンフリクト → ユーザーに報告 → AskUserQuestion で対応選択）
3. `bash .claude/skills/dev/team-run/scripts/setup-worktree.sh {slug}` で Worktree 作成
4. `$WORKTREE_PATH` を取得（スクリプトの stdout）

ゲート: `$WORKTREE_PATH` が有効 + `git -C $WORKTREE_PATH branch --show-current` が `feature/{slug}`

---

## Step 3: チーム作成 + タスク登録

DO:

1. 既存チーム確認 → 残っていれば TeamDelete でクリーンアップ
2. `TeamCreate({ team_name: "team-run-{slug}" })`
3. `$PLAN_DIR/task-list.json` の全タスクを TaskCreate で登録（wave, role, requirePlanApproval をメタデータ付与）
4. Wave 間の blockedBy を TaskUpdate で設定
5. TaskList で登録を確認

ゲート: TeamCreate 成功 + 全タスク登録済み。**以降 Delegate mode: Lead はコードを書かない**

---

## Step 4: Wave 実行ループ

DO: 各 Wave について →

1. **実装系ロール**: `Read("references/teammate-spawn-protocol.md")` に従って Teammate をスポーン（run_in_background: true, cwd: $WORKTREE_PATH）
2. **レビュー系ロール**: Task(subagent_type: "Explore", model: "opus") で Subagent 実行
3. Wave 完了判定:
   - 全タスク TaskList で `completed`
   - 各 outputs がファイルとして存在
   - worktree にコミットあり

VERIFY: 完了 → 次 Wave（4-1 に戻る）/ 全 Wave 完了 → Step 5

エラー時: `Read("references/error-handling.md")` に従って対応

---

## Step 5: レビュー・フィードバックループ

DO:

1. Reviewer 報告の改善候補を集約
2. AskUserQuestion で重要度付きリストをユーザーに提示（対応する項目を選択 / 対応不要）
3. 対応不要 → Step 6
4. 対応あり → fix タスク生成 + TaskCreate + Teammate スポーン（Step 4 と同手順）
5. fix 完了後 → AskUserQuestion で再レビュー要否を確認

ゲート: ユーザー承認 or 3ラウンド超過 → Step 6

---

## Step 6: PR作成 + クリーンアップ

DO:

1. `git -C $WORKTREE_PATH status --porcelain` で全コミット済み確認
2. `git -C $WORKTREE_PATH push -u origin feature/{slug}`
3. `gh pr create --title "feat: {slug}" --body "{Summary + Changes + Review Notes}"`
4. `bash .claude/skills/dev/team-run/scripts/cleanup-worktree.sh {slug}`

ゲート: PR URL を取得

---

## Step 7: 結果集約 + TeamDelete

DO:

1. 結果テーブルをユーザーに提示（タスク / ロール / Wave / 状態 / 概要）
2. `$PLAN_DIR/task-list.json` の `metadata.status` を `"completed"` に更新
3. 全 Teammate に `SendMessage("全タスク完了。シャットダウンしてください。")` → 待機
4. `TeamDelete()`

---

## エラーハンドリング

詳細: `Read("references/error-handling.md")`

要約: 5分無応答 → SendMessage 確認 → 再スポーン → 3回失敗 → AskUserQuestion でユーザーに報告
