---
name: dev:team-opencode-exec
description: |
  承認済みのteam-opencode計画（task-list.json）をAgent Teamsで並行実行。
  Wave式チーム実行→レビューフィードバック→クリーンアップ。

  Trigger:
  dev:team-opencode-exec, /dev:team-opencode-exec, チーム実行, team exec
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

# チーム実行（dev:team-opencode-exec）

## 概要

`dev:team-plan` が生成した承認済み task-list.json を入力として、Agent Teams で並行実装する。各エージェント（haiku）は `opencode run` で外部モデルに実装を委譲し、結果をコミットする。最終Waveにはレビュワーを必ず配置し、品質ゲートとフィードバックループで品質を担保する。

## 必須リソース

| リソース                              | 読み込みタイミング                  | 用途                       |
| ------------------------------------- | ----------------------------------- | -------------------------- |
| `references/agent-prompt-template.md` | Phase 1-3（エージェントスポーン前） | 統一エージェントプロンプト |
| `references/role-catalog.md`          | Phase 1-3（role_directive 取得）    | ロール定義の参照           |

**エージェントスポーン時、必ず `agent-prompt-template.md` を Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

## 計画入力元

```
docs/FEATURES/team/{YYMMDD}_{slug}/
├── story-analysis.json    # ストーリー分析結果（チーム設計、ロール定義含む）
└── task-list.json         # タスク定義（waves/roles 形式、承認済み、各タスクに taskPrompt 含む）
```

---

## 計画選択 UI（起動時）

1. `docs/FEATURES/team/` 以下のディレクトリを列挙する
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

選択後、`task-list.json` のパスを `$PLAN_DIR` として保持し、以降の Phase 1-3 で使用する。

---

## opencode モデル選択（Phase 1 前）

`$PLAN_DIR/task-list.json` の `metadata.ocModel` をデフォルト値として AskUserQuestion で提示:

```
Q: opencode run で使用するモデルは？（計画時: {metadata.ocModel}）
選択肢:
- {metadata.ocModel}（計画時と同じ）(Recommended)
- openai/gpt-5.3-codex
- zai-coding-plan/glm-5
- zai-coding-plan/glm-4.7
```

選択されたモデルを `$OC_MODEL` として以降のすべてのコマンドに使用する。

---

## Pre-flight 検証ゲート（モデル選択後・チーム作成前）

`$PLAN_DIR/task-list.json` を Read で読み込み、以下の検証を**全タスク**に対して実施する。

### 検証チェックリスト

- [ ] 8必須フィールドが存在する: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `taskPrompt`
- [ ] 禁止フィールドが存在しない: `title`, `acceptanceCriteria`, `context`（タスクレベル）, `deliverables`
- [ ] Wave構造が `waves[].tasks[]` フラット配列 + `role` フィールド形式である
- [ ] `taskPrompt` が具体的な実装指示を含む（ファイルパス・操作内容が明記されている）

### 判定

- **全タスク合格** → Phase 1 へ進む
- **1つでも不合格** → **即座に停止**。不合格タスクのIDと欠損フィールドをユーザーに報告し、`dev:team-plan` での修正を案内する

**禁止**: `taskPrompt` が欠損・曖昧なタスクに対して、exec 側でプロンプトを即興生成して補完すること。計画の品質問題は plan 側で修正する。

---

## Phase 1: チーム実行（Wave式）

### 1-1: チーム作成

```
TeamCreate({ team_name: "team-opencode-{timestamp}", description: "opencode並行実装" })
```

### 1-2: タスク登録

`$PLAN_DIR/task-list.json` の全タスクを TaskCreate で登録する。Wave間の `blockedBy` も設定。

### 1-3: Wave N のエージェントスポーン

現在のWaveに属するロールごとに1エージェントをスポーン。

**全エージェント共通設定**:

- `model`: haiku
- `subagent_type`: general-purpose
- `run_in_background`: true

**プロンプト構築手順**:

1. `references/agent-prompt-template.md` を Read で読み込む
2. `references/role-catalog.md` から該当ロールの `role_directive` を取得
3. `$PLAN_DIR/story-analysis.json` から該当ロールの `customDirective` を取得
4. `$PLAN_DIR/task-list.json` からタスクの `description`, `inputs`, `outputs`, `taskPrompt` を取得
5. task-list.json の `name` を `{task_name}` として置換
6. `needsPriorContext: true` の場合、`{taskPrompt}` の先頭に以下を付加してから置換する:

   ```
   Before starting, check what was changed by the previous task:
   - Run: git log --oneline -3
   - Run: git diff HEAD~1 --stat
   - Run: git diff HEAD~1
   Understand the prior changes, then proceed with the following task:

   ```

   `needsPriorContext` が未指定または false の場合はそのまま置換する

7. テンプレートの変数を置換してエージェントプロンプトとして使用
8. `role` が `reviewer` または `tester` の場合、`{taskPrompt}` が `"IMPORTANT: Do NOT modify any files."` で始まることを確認する。始まっていない場合、先頭に `"IMPORTANT: Do NOT modify any files. This is a review-only task. Report findings only.\n\n"` を付加する

**必須**: テンプレートの文言を改変・省略・要約しない。変数（`{...}`）のみ置換する。

**レビュワー制約**: reviewer/tester ロールのエージェントは**レビュー報告のみ**を行う。コードの修正・ファイルの変更・コミットは禁止。この制約は agent-prompt-template.md の厳守事項にも記載されている。

### 1-4: 完了待機

TaskList を定期的に確認し、現在のWaveの全タスク完了を待つ。

**タイムアウト**: エージェントが5分以上 in_progress のまま変化がない場合、「エージェント遅延・失敗時のエスカレーション手順」に従う。

**禁止:**

- エージェント遅延を理由に、リーダーがユーザー承認なしで作業を代行する
- 1つのエージェントの遅延を理由に、他のエージェントをシャットダウンする
- Wave未完了のまま次のWaveに進む

### 1-5: 次Wave スポーン

現在のWaveが完了したら、「Wave完了ゲート」のチェックリストを確認し、次のWaveのエージェントをスポーンする（1-3 に戻る）。全Waveが完了するまで繰り返す。

**必須**: 最終Wave（reviewer含む）の完了まで、このループを続ける。Waveを省略しない。

---

## Phase 2: レビュー・フィードバックループ（修正実行込み）

### 2-1: レビュワー報告の受信

最終Waveのレビュワーが改善候補を SendMessage で報告する。

レビュワーの `customDirective` には以下を含めること:

```
レビュー完了後、改善候補を以下の形式で報告してください:
1. [重要度: 高/中/低] 改善内容の簡潔な説明
2. [重要度: 高/中/低] ...

改善候補がない場合は「改善候補なし」と報告してください。
コードの修正は行わないでください。報告のみです。
```

### 2-2: ユーザーへの提示

AskUserQuestion でレビュー結果をユーザーに提示。multiSelect で複数選択可能にする:

```
Q: レビュワーから以下の改善候補が挙がりました。修正する項目を選択してください。
- [高] 候補1: {改善内容}
- [中] 候補2: {改善内容}
- [低] 候補3: {改善内容}
- 対応不要（完了へ進む）
```

### 2-3: フィードバック分岐

- **対応なし** → Phase 3 へ
- **対応あり** → 2-4 へ

### 2-4: Fix タスク生成

ユーザーが選択した改善候補ごとに fix タスクを生成する:

1. 各改善候補から以下の情報を抽出:
   - 対象ファイル（reviewer 報告から特定）
   - 修正内容の具体的な指示
   - 適切なロール（通常は `frontend-developer`）

2. fix タスクの `taskPrompt` をリーダーが構築:
   ```
   以下のレビュー指摘に基づいて修正してください:

   指摘内容: {改善候補の内容}
   対象ファイル: {ファイルパス}

   修正方針:
   - {具体的な修正手順}

   修正後、変更内容を簡潔に報告してください。
   ```

3. `$PLAN_DIR/task-list.json` に新しい Wave（fix wave）として追加し Write で保存:
   ```json
   {
     "id": {最終Wave ID + 1},
     "tasks": [
       {
         "id": "task-{waveId}-{seq}",
         "name": "Fix: {改善候補の要約}",
         "role": "frontend-developer",
         "description": "レビュー指摘対応: {改善内容}",
         "needsPriorContext": true,
         "inputs": ["{対象ファイル}"],
         "outputs": ["{対象ファイル}"],
         "taskPrompt": "{上記で構築したプロンプト}"
       }
     ]
   }
   ```

4. TaskCreate で fix タスクを登録

### 2-5: Fix エージェントスポーン

Phase 1-3 と同じ手順で fix タスクのエージェントをスポーン:

- `references/agent-prompt-template.md` を使用
- `$OC_MODEL` を使用
- `needsPriorContext: true` なので git diff プレフィックスを付加
- fix タスクは**実装系ロール**なので手順4-5（コード適用・コミット）を実行する

### 2-6: Fix 完了確認

Wave完了ゲートと同じチェックを実施:

- [ ] 全 fix タスクが `completed` になっている
- [ ] 成果物ファイルが存在する
- [ ] コミットされている

### 2-7: 再レビュー判断

fix 完了後、AskUserQuestion でユーザーに確認:

```
Q: Fix が完了しました。再レビューを実施しますか？
- 再レビュー実施
- 不要（完了へ進む）
```

- **再レビュー** → 新しい reviewer タスクを生成し、Phase 2-1 に戻る
- **不要** → Phase 3 へ

**ループ制限**: 最大3ラウンド（fix + 再レビュー）。超過時はユーザーに継続可否を確認。

**禁止事項:**

- リーダーが fix タスクの `taskPrompt` を曖昧にする（「改善してください」等）
- fix wave で reviewer をスポーンしない（再レビューは 2-7 でユーザーが判断）
- ユーザー未選択の改善候補を勝手に fix に含める

---

## Phase 3: クリーンアップ

### 3-1: 結果集約

全タスク完了後、各エージェントからの報告を集約してユーザーに提示:

```
## 実行結果

| タスク | ロール | 状態 | 概要 |
|--------|--------|------|------|
| {タスク1} | {ロール} | 完了 / 失敗 | {概要} |
```

### 3-2: シャットダウン

全エージェントに shutdown_request を送信。

### 3-3: 計画ステータス更新

`$PLAN_DIR/task-list.json` の `metadata.status` を `"completed"` に更新して Write で保存する。
これにより次回の計画選択時に候補から除外される。

**注意**: Phase 2 で fix タスクが追加された場合、fix タスクの完了後にのみ `"completed"` にする。fix 未完了の場合は `"review-pending"` のままにする。

### 3-4: TeamDelete

```
TeamDelete()
```

---

## エラーハンドリング

| 状況                      | 対応                                 |
| ------------------------- | ------------------------------------ |
| opencode run エラー       | 同じコマンドを最大3回リトライ        |
| エージェント無応答（5分） | SendMessage で状況確認               |
| 状況確認後も無応答（5分） | エージェントを再スポーン（下記参照） |
| 3回リトライ失敗           | ユーザーに報告、指示を仰ぐ           |
| opencode モデル利用不可   | ユーザーに報告、別モデル選択を促す   |

### エージェント遅延・失敗時のエスカレーション手順

エージェントが期待通りに動かない場合、以下の手順を**順番に**実行する。手順を飛ばさない。

```
1. SendMessage で状況確認（5分無応答後）
     ↓ 5分待っても応答なし
2. 当該エージェントのみ shutdown_request → 同じタスクで新エージェントを再スポーン
     ↓ 再スポーンも失敗（3回）
3. AskUserQuestion でユーザーに報告し、指示を仰ぐ
   選択肢:
   - リーダーが当該タスクのみ代行（他のWave・タスクはスキップしない）
   - タスクをスキップして次へ進む
   - 中止する
```

**禁止事項:**

- リーダーが**ユーザー承認なしに**エージェントの作業を代行しない
- 1つのエージェントが遅延しても、**他のエージェントをシャットダウンしない**
- エージェント代行時も、**後続Waveのスキップは禁止**（代行完了後、次Waveを通常通りスポーンする）

---

## Wave完了ゲート（厳守）

各Waveの完了時に以下のチェックリストを**すべて満たしてから**次のWaveに進む。

### Wave N → Wave N+1 移行チェックリスト

- [ ] 当該Waveの**全タスク**が TaskList で `completed` になっている
- [ ] 各タスクの成果物（outputs）が**ファイルとして実際に存在する**ことを確認（`ls` / `Glob`）
- [ ] 次のWaveが存在する場合、**次Waveのエージェントをスポーンする**（Phase 1-3 に戻る）

### 最終Wave完了 → Phase 2 移行チェックリスト

- [ ] 最終Waveの reviewer タスクが `completed` になっている
- [ ] reviewer からの改善候補報告を受信している
- [ ] Phase 2-2 でユーザーに改善候補を提示する

**以下の行為は禁止:**

- Wave完了前に次Waveのエージェントをスポーンする
- 最終Wave（reviewer）をスキップして Phase 3 に進む
- タスクを実行せずに `completed` にする

---

## タスク完了の定義

TaskUpdate で `completed` にする条件:

### 実装系ロール（designer, frontend-developer, backend-developer 等）

1. **エージェントが実行した場合**: opencode結果を適用し、dev:simple-add でコミット済み
2. **リーダーが代行した場合**: ユーザー承認を得た上で代行し、dev:simple-add でコミット済み
3. **いずれの場合も**: 成果物ファイルが存在し、コミットされていることを確認済み

### レビュー系ロール（reviewer, tester）

1. opencode でレビュー/テストを実行済み
2. 改善候補をリーダーに SendMessage で報告済み
3. **コード変更・コミットは不要**（報告のみで完了）

**禁止**: 上記条件を満たさずにタスクを `completed` にする

### 計画ステータスの遷移

| 状態 | 意味 | 設定タイミング |
|------|------|---------------|
| `pending` | 未実行 | 初期値 |
| `review-pending` | レビュー指摘の修正待ち | Phase 2 で改善候補が選択された時 |
| `completed` | 全完了（fix含む） | Phase 3 で全タスク＋全fix完了時のみ |

---

## 重要な注意事項

1. **opencode コマンドは決め打ち**: プロンプトテンプレートのコマンドをエージェントに改変させない
2. **フォールバック禁止**: opencode 失敗時に直接実装しない。リトライのみ
3. **モデル固定**: 選択されたモデルを全エージェントで統一
4. **CC側はhaiku**: コスト最小化。実装はopencode側が担当
5. **越境防止**: 各エージェントは自分のタスク以外に手を出さない
6. **リーダーは実装しない**: リーダーの役割は調整・監視。実装はエージェント（opencode）が担当。リーダーが直接コードを書くのはユーザー承認後の代行時のみ
7. **Phase順序は絶対**: Phase 1→2→3 の順序を飛ばさない。Wave内のステップ（1-1→1-2→1-3→1-4→1-5）も飛ばさない
8. **全Wave完走が必須**: 最終Waveのreviewerを含め、task-list.jsonで定義した全Waveをスポーン・完了させる。「効率化」のためにWaveを省略しない
