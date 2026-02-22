# Teammate スポーンプロトコル

このファイルは SKILL.md Step 4 で `Read()` して使用する。Teammate スポーン時に毎回参照すること。

---

## 1. プロンプト構築手順

以下の順序で変数を収集し、テンプレートに埋め込む。**手順をスキップしない。**

### Step A: テンプレート読み込み（毎回必須）

```
template = Read("references/agent-prompt-template.md")
```

**⛔ キャッシュ・記憶・要約で代替しない。毎回 Read する。**

### Step B: ロール定義取得

```
role_catalog = Read("references/role-catalog.md")
→ 該当ロールの role_directive を抽出
```

### Step C: ストーリー情報取得

```
story = Read("$PLAN_DIR/story-analysis.json")
→ customDirective（ロール別）
→ fileOwnership（ロール別 glob パターン）
```

### Step D: タスク情報取得

```
task = task-list.json の該当タスク
→ id, name, description, inputs, outputs, taskPrompt
```

### Step E: needsPriorContext 対応

`needsPriorContext: true` の場合、プロンプト先頭に以下を付加:

```
Before starting, check what was changed by the previous task:
- Run: git log --oneline -3
- Run: git diff HEAD~1 --stat
- Run: git diff HEAD~1
Understand the prior changes, then proceed with the following task:
```

### Step F: テンプレート変数置換

agent-prompt-template.md の変数一覧に従い、全変数を置換する。

---

## 2. Teammate スポーン設定

### 実装系ロール → Teammate（SendMessage 対応）

対象: designer, frontend-developer, backend-developer, tdd-developer, fullstack-developer, copywriter, architect, researcher

```
SendMessage(to: "{agent_name}", message: "{置換済みプロンプト}")
```

- model: opus（全ロール共通）
- cwd: $WORKTREE_PATH（全 Teammate 共通、fileOwnership で論理分離）

### レビュー系ロール → Subagent（Task ツール）

対象: reviewer, tester

```
Task({
  prompt: "{レビュー専用プロンプト}",
  description: "Review: {task_name}",
  subagent_type: "Explore",
  model: "opus"
})
```

レビュー専用プロンプトには以下を含める:
- レビュー対象ファイル一覧（worktree 内の git diff で特定）
- role-catalog.md の reviewer/tester の role_directive
- task-list.json の当該タスクの description と taskPrompt
- **出力形式**: 改善候補を重要度（高/中/低）付きで報告

---

## 3. Plan Approval フロー

`requirePlanApproval: true` のタスクのみ:

1. Teammate が TaskUpdate で `in_progress` に設定
2. Teammate が実装計画を SendMessage で Lead に送信
3. Lead が検証: fileOwnership 違反なし / 他タスクとの競合なし / 技術的に妥当
4. 承認 → SendMessage で実装開始を通知
5. 拒否 → フィードバック付きで修正要求（最大2回、3回目は自動承認）

---

## 4. Self-claim Protocol

Teammate が自分のタスクを完了後:
1. TaskList で同一 Wave 内に未割り当て（owner が空）のタスクを確認
2. あれば TaskUpdate で owner を設定して着手
3. なければ待機

※ この動作は agent-prompt-template.md の「Self-claim Protocol」セクションに記載済み。

---

## 5. Teammate 間メッセージプロトコル

実装 Teammate がタスク完了時に SendMessage で報告する内容:
- 変更したファイルの一覧
- 設計判断の要約（なぜその実装にしたか）
- 次 Wave の Teammate への引き継ぎ事項
