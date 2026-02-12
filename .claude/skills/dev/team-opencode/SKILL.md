---
name: dev:team-opencode
description: |
  Agent Teamsでタスクを並行実行。各エージェント(haiku)がopencode runで外部モデルに実装を委譲する。
  TODO.mdまたは直接指示からタスクを読み取り、チームで並行実装。

  Trigger:
  dev:team-opencode, /dev:team-opencode, チームで実装, team opencode, swarm実装
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
---

# Agent Teams + opencode 並行実装（dev:team-opencode）

## 概要

タスクリスト（TODO.mdまたは直接指示）を受け取り、Agent Teamsで並行実装する。
各エージェント（haiku）は `opencode run` で外部モデルに実装を委譲し、結果をコミットする。

## 必須リソース

| リソース | 読み込みタイミング | 用途 |
|----------|-------------------|------|
| `references/agent-prompt-template.md` | Phase 1-3（エージェントスポーン前） | 汎用エージェントプロンプト |
| `references/agent-prompt-template-tdd.md` | Phase 1-3（TDDタスクのスポーン前） | TDD開発エージェントプロンプト |

**⚠️ エージェントスポーン時、必ず該当テンプレートを Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

---

## Phase 0: 初期設定

### 0-1: opencode モデル選択

AskUserQuestion で使用するopencode モデルを確認:

```
Q: opencode run で使用するモデルは？
選択肢:
- openai/gpt-5.3-codex
- zai-coding-plan/glm-5
- zai-coding-plan/glm-4.7
```

選択されたモデルを `$OC_MODEL` として以降のすべてのコマンドに使用する。

### 0-2: タスク読み取り

**入力パターンA: TODO.mdから読み取り**

1. TODO.md のパスをユーザーに確認（またはGlobで探す）
2. Read で TODO.md を読み込み
3. 未完了タスク（`- [ ]`）を抽出

**入力パターンB: 直接指示**

1. ユーザーの指示からタスクを抽出
2. 必要に応じて AskUserQuestion で分解を確認

### 0-3: タスク一覧確認

抽出したタスクをユーザーに提示:

```
以下のタスクをAgent Teamsで並行実装します:
1. {タスク1}
2. {タスク2}
3. {タスク3}

モデル: {$OC_MODEL}
エージェント数: {タスク数、最大5}

実行してよいですか？
```

**ゲート**: ユーザー承認なしに Phase 1 に進まない。

---

## Phase 1: チーム起動・タスク実行

### 1-1: チーム作成

```
TeamCreate({ team_name: "team-opencode-{timestamp}", description: "opencode並行実装" })
```

### 1-2: タスク登録

各タスクを TaskCreate で登録する。

### 1-3: エージェントスポーン

タスクごとに1エージェントをスポーン（最大5並行）。

**全エージェント共通設定**:
- `model`: haiku
- `subagent_type`: general-purpose
- `run_in_background`: true

**プロンプトテンプレート**:

タスクの種類に応じて使い分ける:

| タスク種別 | テンプレート |
|-----------|-------------|
| 汎用（デフォルト） | `references/agent-prompt-template.md` |
| TDD（テスト駆動開発） | `references/agent-prompt-template-tdd.md` |

**判定基準**: タスクに `[TDD]` ラベルがある、またはテスト作成・ロジック実装を伴う場合は TDD テンプレートを使用する。

⚠️ **必須**: 該当テンプレートを Read で読み込み、そのまま使用する。
テンプレートの文言を改変・省略・要約しない。変数（`{...}`）のみ置換する。

```
# 汎用タスクの場合
template = Read("references/agent-prompt-template.md")

# TDDタスクの場合
template = Read("references/agent-prompt-template-tdd.md")

→ 変数を置換してエージェントプロンプトとして使用
```

### 1-4: 完了待機

TaskList を定期的に確認し、全タスクの完了を待つ。

**タイムアウト**: エージェントが5分以上 in_progress のまま変化がない場合、SendMessage で状況確認する。

---

## Phase 2: 完了・クリーンアップ

### 2-1: 結果集約

全タスク完了後、各エージェントからの報告を集約してユーザーに提示:

```
## 実行結果

| タスク | 状態 | 概要 |
|--------|------|------|
| {タスク1} | ✅ / ❌ | {概要} |
| {タスク2} | ✅ / ❌ | {概要} |
```

### 2-2: シャットダウン

全エージェントに shutdown_request を送信。

### 2-3: クリーンアップ

```
TeamDelete()
```

---

## エラーハンドリング

| 状況 | 対応 |
|------|------|
| opencode run エラー | 同じコマンドを最大3回リトライ |
| エージェント無応答（5分） | SendMessage で状況確認 |
| 3回リトライ失敗 | ユーザーに報告、指示を仰ぐ |
| opencode モデル利用不可 | ユーザーに報告、別モデル選択を促す |

## 重要な注意事項

1. **opencode コマンドは決め打ち**: プロンプトテンプレートのコマンドをエージェントに改変させない
2. **フォールバック禁止**: opencode 失敗時に直接実装しない。リトライのみ
3. **モデル固定**: 選択されたモデルを全エージェントで統一
4. **CC側はhaiku**: コスト最小化。実装はopencode側が担当
