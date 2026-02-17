# dev:team-run スキル作成計画

## 注意書き

この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

---

## 概要

opencode を使用せず Claude Code のネイティブ機能のみで動作する新しいチーム実行スキル `dev:team-run` を作成する。Agent Teams の公式ベストプラクティス（Delegate mode, Plan Approval, Teammate間メッセージ, Self-claim, hooks）にフル準拠し、チーム全体で1つの Git Worktree を使用してユーザーの作業ディレクトリから隔離する。Teammate 間のファイル衝突は fileOwnership（論理的分離）で防止する。

## 背景

### 現行の課題（team-opencode-exec）

現行の `dev:team-opencode-exec` スキルには以下の構造的課題がある:

1. **opencode への全面依存による3層トークンコスト**: すべてのタスクが `CC(haiku) → opencode run → 外部モデル` という3層構造で実行される。トークンコスト3層化、応答遅延、opencode 障害が SPOF
2. **Agent Teams の機能を活かしきれていない**: Teammate間直接メッセージ、自己クレーム、プラン承認が未活用
3. **ファイル衝突リスク**: 同じディレクトリで複数 Teammate が作業するため上書きリスクがある
4. **モデル戦略の欠如**: 全エージェントが haiku + 同一 OC_MODEL 固定。ロールの複雑度に応じたモデル選択ができない

### 新スキルの方針

| 項目 | 決定 |
|------|------|
| スキル名 | `dev:team-run` |
| ディレクトリ | `.claude/skills/dev/team-run/` |
| Git分離方式 | **Git Worktree**（チーム全体で1つ）+ 最終PR。`feature/{slug}` ブランチで1つの worktree を作成し、全 Teammate が同じ worktree で作業。ファイル衝突は fileOwnership（論理的分離）で防止。全Wave完了後に `gh pr create` でPR作成 |
| 実行方式 | **ハイブリッド**: 実装系ロール（designer, frontend-developer, backend-developer等）は Agent Teams の Teammate（独立した Claude Code セッション）、レビュー系ロール（reviewer, tester）は Subagent（Task ツール） |
| Agent Teams公式機能 | **フル導入**: Delegate mode, Plan Approval（複雑タスク）, Teammate間メッセージ, Self-claim, TeammateIdle/TaskCompleted hooks。team-plan の計画を活かして効率化 |

### 公式ベストプラクティスからの導入項目

#### Agent Teams ドキュメントより

1. **Delegate mode**: Lead を調整専任に限定。実装には手を出さない
2. **Plan Approval**: 複雑なタスク（`requirePlanApproval: true`）で実装前に計画提出 → Lead承認
3. **Teammate間メッセージ**: 実装者が完了時にreviewerに直接通知。reviewerが実装者にフィードバック
4. **Self-claim**: 同一Wave内で未割り当てタスクをTeammateが自律的に取得
5. **TeammateIdle hook**: Teammate待機前に品質ゲート（成果物存在確認等）
6. **TaskCompleted hook**: タスク完了前にlint/build チェック
7. **十分なコンテキスト**: スポーン時にタスク固有の詳細をプロンプトに含める
8. **適切なタスクサイズ**: 5-6タスク/Teammateで生産性維持
9. **ファイル衝突回避**: fileOwnership で論理分離（公式推奨）。Git Worktree はユーザー作業ディレクトリからのチーム隔離用

#### Subagents ドキュメントより

10. **レビュー系ロールはSubagent**: Read-only tools限定。結果をsummaryで返す
11. **model選択**: 基本は opus。明らかに軽量なタスクのみ sonnet/haiku

#### Best Practices ドキュメントより

12. **検証手段の提供**: テスト、lint、build等でTeammateが自己検証
13. **コンテキスト管理**: Subagent（レビュー）はコンテキスト汚染を防ぐ

#### Hooks Reference より

14. **TeammateIdle**: exit code 2でTeammateを継続させる（品質未達時）
15. **TaskCompleted**: exit code 2でタスク完了をブロック（テスト未通過時）

---

## 計画入力元（dev:team-plan が生成）

```
docs/features/team/{YYMMDD}_{slug}/
├── story-analysis.json    # チーム設計（ロール、Wave構造、fileOwnership）
└── task-list.json         # タスク定義（8必須フィールド + taskPrompt）
```

team-plan で事前に設計された:
- **ロール構成**: role-catalog.md ベースのロール割当
- **Wave構造**: 依存関係付きの順次実行構造
- **fileOwnership**: ロールごとのファイル所有権
- **taskPrompt**: 各タスクの実装指示（team-run では Teammate への直接プロンプトとして使用）

### task-list.json のタスクスキーマ（8必須フィールド）

```json
{
  "id": "task-1-1",
  "name": "HeroSectionのコピー作成",
  "role": "copywriter",
  "description": "HeroSectionのマーケティングコピーを作成",
  "needsPriorContext": false,
  "inputs": ["docs/features/team/copy-hero.md"],
  "outputs": ["src/components/lp/HeroSection.tsx"],
  "taskPrompt": "以下の仕様でHeroSectionを実装..."
}
```

team-run では `taskPrompt` を opencode に渡すのではなく、Teammate への直接実装指示として使用する。

---

## 全体フロー

```
Step 1: 計画選択 + 検証
  ├── docs/features/team/ から計画選択（AskUserQuestion）
  └── Pre-flight 検証（8必須フィールド、Wave構造、fileOwnership）

Step 2: 環境セットアップ
  ├── feature/{slug} ブランチ作成
  ├── scripts/setup-worktree.sh 実行 → チーム全体で1つの worktree 作成
  └── worktree パスを記録（.worktrees/{slug}/）

Step 3: チーム作成 + タスク登録
  ├── TeamCreate({ team_name: "team-run-{slug}" })
  ├── TaskCreate で全タスクを登録（Wave間の blockedBy 設定）
  └── Teammate スポーンの準備（プロンプトテンプレート読み込み）

Step 4: Wave 実行ループ（全Wave完走まで繰り返し）
  ├── 実装系ロール → Agent Teams Teammate をスポーン
  │   ├── 全 Teammate の cwd を共通の worktree に設定
  │   ├── fileOwnership でファイル衝突を論理的に防止
  │   ├── Plan Approval（requirePlanApproval: true の場合）
  │   ├── ネイティブ実装（Glob/Grep/Read/Edit/Write/Bash）
  │   ├── Self-claim（同一 Wave 内の未割り当てタスク）
  │   ├── TaskCompleted hook → lint/build チェック
  │   └── 完了時に SendMessage でレビュワーまたは次 Wave に通知
  ├── レビュー系ロール → Subagent（Task）をスポーン
  │   ├── Read-only tools のみ（Read/Glob/Grep/Bash(read-only)）
  │   └── 結果を summary で返却（コンテキスト汚染防止）
  ├── TeammateIdle hook で品質ゲート（成果物存在確認）
  └── Wave 完了 → 次 Wave

Step 5: レビュー・フィードバックループ
  ├── Reviewer 報告 → AskUserQuestion で改善候補提示
  ├── ユーザー選択 → Fix タスク生成
  ├── Fix Teammate スポーン → 修正実装
  └── 再レビュー判断（最大3ラウンド）

Step 6: PR作成 + クリーンアップ
  ├── worktree 内の変更が全てコミット済みであることを確認
  ├── feature/{slug} ブランチを push
  ├── gh pr create でPR作成
  └── scripts/cleanup-worktree.sh で worktree 削除

Step 7: 結果集約 + TeamDelete
  ├── 結果集約 → ユーザーに提示
  ├── metadata.status を "completed" に更新
  └── TeamDelete
```

---

## 各ファイルの変更内容

### 1. `.claude/skills/dev/team-run/SKILL.md`（新規作成）

メインスキル定義。以下のセクション構成とする。

#### frontmatter

```yaml
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
---
```

#### 必須リソース

| リソース | 読み込みタイミング | 用途 |
|----------|-------------------|------|
| `references/agent-prompt-template.md` | Step 4（Teammate スポーン前） | 統一 Teammate プロンプト |
| `references/role-catalog.md` | Step 4（role_directive 取得） | ロール定義の参照 |
| `scripts/setup-worktree.sh` | Step 2（環境セットアップ） | Worktree セットアップ（チーム全体で1つ） |
| `scripts/cleanup-worktree.sh` | Step 6/7（クリーンアップ） | Worktree 削除 |

**Teammate スポーン時、必ず `agent-prompt-template.md` を Read で読み込んでからプロンプトを構築すること。記憶や要約で代替しない。**

#### Step 1: 計画選択 + 検証

**1-1: 計画選択**

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

**1-2: Pre-flight 検証**

`$PLAN_DIR/task-list.json` を Read で読み込み、以下の検証を**全タスク**に対して実施する:

- [ ] 8必須フィールドが存在する: `id`, `name`, `role`, `description`, `needsPriorContext`, `inputs`, `outputs`, `taskPrompt`
- [ ] Wave構造が `waves[].tasks[]` フラット配列 + `role` フィールド形式である
- [ ] `taskPrompt` が具体的な実装指示を含む（ファイルパス・操作内容が明記されている）
- [ ] `story-analysis.json` の `fileOwnership` が存在し、各ロールのファイル所有範囲が定義されている

判定:
- **全タスク合格** → Step 2 へ進む
- **1つでも不合格** → **即座に停止**。不合格タスクのIDと欠損フィールドをユーザーに報告し、`dev:team-plan` での修正を案内する

**禁止**: `taskPrompt` が欠損・曖昧なタスクに対して、team-run 側でプロンプトを即興生成して補完すること。計画の品質問題は plan 側で修正する。

#### Step 2: 環境セットアップ

**2-1: Worktree セットアップ**

`scripts/setup-worktree.sh` を実行:

```bash
WORKTREE_PATH=$(bash .claude/skills/dev/team-run/scripts/setup-worktree.sh {slug})
```

スクリプトの処理内容:
1. 現在の HEAD から `feature/{slug}` ブランチを作成
2. `.worktrees/{slug}/` にチーム全体で1つの worktree を作成
3. worktree の絶対パスを出力

`$WORKTREE_PATH` を以降のすべてのステップで Teammate の cwd として使用する。

**2-2: Worktree パスの検証**

worktree ディレクトリが存在し、正しいブランチをチェックアウトしていることを確認:

```bash
git -C .worktrees/{slug} branch --show-current
# → feature/{slug} であること
```

#### Step 3: チーム作成 + タスク登録

**3-1: チーム作成**

```
TeamCreate({ team_name: "team-run-{slug}", description: "ネイティブ並行実装: {slug}" })
```

**3-2: タスク登録**

`$PLAN_DIR/task-list.json` の全タスクを TaskCreate で登録する。Wave間の `blockedBy` も設定。

タスク登録時、以下のメタデータを付与:
- `wave`: Wave番号
- `role`: ロール名
- `requirePlanApproval`: true/false（task-list.json から取得、未設定は false）

**3-3: Delegate mode の宣言**

Lead は以下の役割に限定する:
- タスク割り当て・依存関係管理
- Plan Approval の審査
- Wave 間の遷移制御
- エラーハンドリング・エスカレーション
- ユーザーへの報告・確認

**禁止**: Lead がコードを書く、ファイルを編集する、実装に手を出す

#### Step 4: Wave 実行ループ

**4-1: Wave N の Teammate スポーン（実装系ロール）**

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

**4-2: Wave N のレビュー系ロール → Subagent**

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

**4-3: hooks**

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

**4-4: Wave 完了判定**

- [ ] 当該 Wave の**全タスク**が TaskList で `completed` になっている
- [ ] 各タスクの成果物（outputs）が**ファイルとして実際に存在する**ことを確認
- [ ] worktree にコミットがある（`git log` で確認）

判定合格 → 次 Wave の Teammate をスポーン（4-1 に戻る）
全 Wave 完了 → Step 5 へ

**4-5: Teammate 間メッセージプロトコル**

実装 Teammate がタスク完了時に SendMessage で送信する内容:
- 変更したファイルの一覧
- 設計判断の要約（なぜその実装にしたか）
- 次 Wave の Teammate への引き継ぎ事項

レビュー Subagent の結果は Lead が受け取り、改善候補として Step 5 で処理する。

#### Step 5: レビュー・フィードバックループ

**5-1: Reviewer 報告の集約**

最終 Wave のレビュー Subagent（または Reviewer Teammate）からの改善候補を集約する。

**5-2: ユーザーへの提示**

AskUserQuestion でレビュー結果をユーザーに提示:

```
Q: レビュワーから以下の改善候補が挙がりました。修正する項目を選択してください。
- [高] 候補1: {改善内容}
- [中] 候補2: {改善内容}
- [低] 候補3: {改善内容}
- 対応不要（完了へ進む）
```

**5-3: フィードバック分岐**

- **対応なし** → Step 6 へ
- **対応あり** → 5-4 へ

**5-4: Fix タスク生成**

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

**5-5: Fix Teammate スポーン**

Step 4-1 と同じ手順で fix タスクの Teammate をスポーン:
- 共通の worktree で作業（既存の worktree を再利用）
- `needsPriorContext: true` なので git diff プレフィックスを付加

**5-6: Fix 完了確認**

Step 4-4 と同じ品質ゲートを適用。

**5-7: 再レビュー判断**

AskUserQuestion でユーザーに確認:

```
Q: Fix が完了しました。再レビューを実施しますか？
- 再レビュー実施
- 不要（完了へ進む）
```

- **再レビュー** → 新しい reviewer Subagent をスポーンし、5-1 に戻る
- **不要** → Step 6 へ

**ループ制限**: 最大3ラウンド（fix + 再レビュー）。超過時はユーザーに継続可否を確認。

#### Step 6: PR作成 + クリーンアップ

**6-1: コミット状態の確認**

worktree 内で全変更がコミット済みであることを確認:

```bash
git -C $WORKTREE_PATH status --porcelain
```

未コミットの変更がある場合: AskUserQuestion でユーザーに報告し対応を確認。

**6-2: PR 作成**

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

**6-3: Worktree クリーンアップ**

```bash
bash .claude/skills/dev/team-run/scripts/cleanup-worktree.sh {slug}
```

#### Step 7: 結果集約 + TeamDelete

**7-1: 結果集約**

全タスク完了後、各 Teammate からの報告を集約してユーザーに提示:

```
## 実行結果

| タスク | ロール | Wave | 状態 | 概要 |
|--------|--------|------|------|------|
| {タスク1} | {ロール} | {Wave} | 完了 / 失敗 | {概要} |
```

**7-2: 計画ステータス更新**

`$PLAN_DIR/task-list.json` の `metadata.status` を `"completed"` に更新して Write で保存する。

**7-3: TeamDelete**

```
TeamDelete()
```

---

### 2. `.claude/skills/dev/team-run/references/agent-prompt-template.md`（新規作成）

team-opencode-exec の `agent-prompt-template.md` をベースに、opencode 部分を削除し、ネイティブ実装用に改修する。

#### テンプレート本文

```
あなたは{team_name}チームのメンバー「{agent_name}」です。

## あなたの役割

{role_directive}

{custom_directive}

## タスク

{タスク内容}

## 入力ファイル

{input_files}

## 期待する成果物

{output_files}

## ファイル所有権

あなたが編集してよいファイル:
{file_ownership}

上記以外のファイルは読み取り専用です。編集しないでください。

## 実行手順

1. TaskUpdate でタスク#{id} を in_progress にし、owner を「{agent_name}」に設定

{plan_approval_section}

2. 以下の実装指示に従って、ネイティブに実装してください:

{taskPrompt}

利用可能なツール: Glob, Grep, Read, Edit, Write, Bash
- Read で既存ファイルを確認してから Edit/Write で変更する
- Bash でテスト・lint・build を実行して品質を確認する

3. 成果物をコミットする:
git add {output_files}
git commit -m "feat({agent_name}): {task_name}"

コミットに失敗した場合（変更なし等）はスキップして次に進む。

4. TaskUpdate でタスク#{id} を completed にする

5. SendMessage でリーダー(team-lead)に結果を報告する:
- 変更したファイルの一覧
- 設計判断の要約
- 次のTeammateへの引き継ぎ事項

## Self-claim Protocol

自分のタスクが完了した後:
1. TaskList で同じ Wave 内に未割り当て（owner が空）のタスクを確認する
2. 未割り当てタスクがあれば、TaskUpdate で owner を自分に設定し、手順1からやり直す
3. 未割り当てタスクがなければ、待機する

## 厳守事項

- 直接実装する。opencode や外部ツールは使用しない
- ファイル所有権の範囲外のファイルを編集しない
- タスク#{id} 以外のタスクには手を出さない（Self-claim を除く）
- 完了報告後、リーダーから追加指示がなければ待機する
- **reviewer/tester ロールの場合**: 手順2（実装）と手順3（コミット）はスキップする。分析結果を改善候補として重要度(高/中/低)付きでリーダーに報告するのみ。コードの修正・ファイルの変更・コミットは一切行わない
```

#### Plan Approval セクション（requirePlanApproval: true の場合のみ挿入）

```
1b. 【Plan Approval】実装に入る前に、以下の情報を SendMessage でリーダー(team-lead)に送信してください:
- 変更予定のファイル一覧
- 実装方針の概要（2-3文）
- 想定されるリスク

リーダーの承認を待ってから手順2に進んでください。
```

#### 変数一覧

| 変数 | ソース | 例 |
|------|--------|-----|
| `{team_name}` | TeamCreate で生成 | `team-run-auth` |
| `{agent_name}` | task-list.json の `role` | `frontend-developer` |
| `{role_directive}` | role-catalog.md から取得 | （ロール定義文） |
| `{custom_directive}` | story-analysis.json の `customDirective` | `敬語で統一。` |
| `{タスク内容}` | task-list.json の `description` | `認証フォームの実装` |
| `{input_files}` | task-list.json の `inputs` | `docs/auth-spec.md` |
| `{output_files}` | task-list.json の `outputs` | `src/components/AuthForm.tsx` |
| `{file_ownership}` | story-analysis.json の `fileOwnership[role]` | `src/components/**`, `src/pages/**` |
| `{id}` | TaskCreate で生成 | `1`, `2`, `3` |
| `{taskPrompt}` | task-list.json の `taskPrompt` | `以下の仕様で認証フォームを実装...` |
| `{task_name}` | task-list.json の `name` | `認証フォームの実装` |
| `{plan_approval_section}` | requirePlanApproval に応じて挿入/空文字 | （上記セクション） |

#### 使用ルール

1. テンプレート本文の文言を追加・削除・言い換えしない
2. 変数のみ置換する
3. 「厳守事項」セクションは必ず含める
4. `{custom_directive}` が null の場合は空文字に置換する
5. `{input_files}` が空の場合は「なし」に置換する
6. `{file_ownership}` は story-analysis.json の fileOwnership から該当ロールの glob パターンを改行区切りで列挙する
7. reviewer/tester ロールの場合、Subagent（Task）で実行するため、このテンプレートの代わりにレビュー専用プロンプトを使用する

---

### 3. `.claude/skills/dev/team-run/references/role-catalog.md`

team-opencode-exec の `role-catalog.md` と同一内容。シンボリックリンクで共有する:

```bash
ln -s ../../team-opencode-exec/references/role-catalog.md .claude/skills/dev/team-run/references/role-catalog.md
```

ただし、team-opencode-exec が将来削除される可能性を考慮し、**コピーを推奨**する。内容は以下のロール定義:

- **実装系**: frontend-developer, backend-developer, tdd-developer, fullstack-developer
- **設計・企画系**: designer, copywriter, architect
- **品質・検証系**: reviewer, tester
- **調査・分析系**: researcher

（内容は既存の role-catalog.md と完全に同一。省略。）

---

### 4. `.claude/skills/dev/team-run/scripts/setup-worktree.sh`（新規作成）

```bash
#!/bin/bash
# チーム全体で1つの Git Worktree をセットアップするスクリプト
# Usage: setup-worktree.sh <slug>
#
# 処理:
# 1. feature/{slug} ブランチを作成
# 2. .worktrees/{slug}/ に worktree を作成
# 3. worktree の絶対パスを stdout に出力

set -euo pipefail

SLUG="$1"
WORKTREE_PATH=".worktrees/${SLUG}"
FEATURE_BRANCH="feature/${SLUG}"

# feature ブランチが既に存在する場合はスキップ
if git show-ref --verify --quiet "refs/heads/${FEATURE_BRANCH}"; then
    echo "Branch ${FEATURE_BRANCH} already exists, reusing" >&2
else
    git branch "${FEATURE_BRANCH}"
    echo "Created branch: ${FEATURE_BRANCH}" >&2
fi

# worktree が既に存在する場合はスキップ
if [ -d "${WORKTREE_PATH}" ]; then
    echo "Worktree ${WORKTREE_PATH} already exists, reusing" >&2
else
    git worktree add "${WORKTREE_PATH}" "${FEATURE_BRANCH}"
    echo "Created worktree: ${WORKTREE_PATH}" >&2
fi

# 絶対パスを stdout に出力（Lead が $WORKTREE_PATH として使用）
cd "${WORKTREE_PATH}" && pwd
```

---

### 5. `.claude/skills/dev/team-run/scripts/cleanup-worktree.sh`（新規作成）

```bash
#!/bin/bash
# Worktree クリーンアップスクリプト
# Usage: cleanup-worktree.sh <slug>
#
# 処理:
# 1. .worktrees/{slug}/ の worktree を削除
# 2. worktree を prune
# 注意: feature/{slug} ブランチは PR 用に残す

set -euo pipefail

SLUG="$1"
WORKTREE_PATH=".worktrees/${SLUG}"

echo "=== Cleanup Worktree: ${SLUG} ==="

# worktree の削除
if [ -d "${WORKTREE_PATH}" ]; then
    git worktree remove "${WORKTREE_PATH}" --force 2>/dev/null || true
    echo "Removed worktree: ${WORKTREE_PATH}"
fi

# .worktrees ディレクトリが空なら削除
if [ -d ".worktrees" ] && [ -z "$(ls -A .worktrees 2>/dev/null)" ]; then
    rmdir .worktrees
    echo "Removed empty .worktrees directory"
fi

# worktree の整理
git worktree prune

echo "=== Cleanup Complete ==="
```

---

### 6. `.claude/commands/dev/team-run.md`（新規作成）

```markdown
---
description: "承認済み計画をネイティブ Agent Teams + Subagent ハイブリッドで並行実行。Git Worktree分離"
argument-hint: "[計画ディレクトリパス]"
---

# /dev:team-run - ネイティブチーム並行実行コマンド

## 概要

`dev:team-plan` で作成・承認済みの計画（task-list.json）を Agent Teams + Subagent ハイブリッドで並行実行します。
opencode を使用せず Claude Code のネイティブ機能のみで実装。
Git Worktree でファイル分離し、最終的に PR を作成します。

## 使い方

### 計画パス指定

\```
/dev:team-run docs/features/team/260217_auth/
\```

### 引数なし

\```
/dev:team-run
\```

→ 既存計画一覧を表示し、ユーザーが選択

## 実行方法

**必ず `dev:team-run` スキルを発火して実行してください。**

1. **スキルを発火**: スキルファイルの指示に従って実行する
2. **直接実装を禁止**: スキルを発火させずに、このコマンドファイルの内容から直接実装を開始してはならない
```

---

### 7. `CLAUDE.md`（更新）

#### スキルテーブル「チーム実行」セクション

現在:
```markdown
### チーム実行（Agent Teams + opencode）

| スキル                      | 用途                                                                                                                                                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:team-plan**           | ストーリーからチーム実行計画を作成。ストーリー分析・タスク分解・レビュー（opencode）。計画は永続化され複数保持可能。Triggers: /dev:team-plan, チーム計画, team plan       |
| **dev:team-opencode-exec**  | 承認済み計画をAgent Teamsで並行実行。Wave式実行→レビューフィードバック→クリーンアップ。Triggers: /dev:team-opencode-exec, チーム実行                                                        |
```

変更後:
```markdown
### チーム実行（Agent Teams）

| スキル                      | 用途                                                                                                                                                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:team-plan**           | ストーリーからチーム実行計画を作成。ストーリー分析・タスク分解・レビュー（opencode）。計画は永続化され複数保持可能。Triggers: /dev:team-plan, チーム計画, team plan       |
| **dev:team-opencode-exec**  | 承認済み計画をAgent Teams+opencodeで並行実行。Wave式実行→レビューフィードバック→クリーンアップ。Triggers: /dev:team-opencode-exec, チーム実行                                               |
| **dev:team-run**            | 承認済み計画をネイティブAgent Teams+Subagentハイブリッドで並行実行。Git Worktree分離。opencode不使用。Triggers: /dev:team-run, チーム実行(native), team run                                 |
```

#### コマンドテーブル

追加:
```markdown
| `/dev:team-run`            | 承認済み計画をネイティブAgent Teamsで並行実行。Git Worktree分離               |
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

## team-opencode-exec との差分サマリ

| 項目 | team-opencode-exec | team-run |
|------|-------------------|----------|
| 実行エンジン | opencode run (外部モデル) | Claude Code ネイティブ |
| CC側モデル | haiku 固定 | opus（基本）/ sonnet（軽量タスク） |
| レビュー系ロール | Agent Teams (haiku + opencode) | Subagent (Task, opus) |
| ファイル分離 | なし（同一ディレクトリ） | Git Worktree（チーム全体で1つ）+ fileOwnership（論理分離） |
| Delegate mode | なし（Lead が代行可能） | あり（Lead は調整専任） |
| Plan Approval | なし | あり（requirePlanApproval: true のタスク） |
| Self-claim | なし | あり（同一 Wave 内） |
| Teammate間メッセージ | 一方通行（Wave→Wave） | 双方向（SendMessage） |
| hooks | なし | TeammateIdle + TaskCompleted |
| 最終成果物 | コミット済みコード | PR（gh pr create） |
| fileOwnership | 論理的（plan で定義） | 論理的（プロンプトで指示）。公式推奨の方式 |

---

## 影響範囲

| ファイル | 操作 | 説明 |
|---------|------|------|
| `.claude/skills/dev/team-run/SKILL.md` | 新規作成 | メインスキル定義 |
| `.claude/skills/dev/team-run/references/agent-prompt-template.md` | 新規作成 | Teammate 用プロンプトテンプレート |
| `.claude/skills/dev/team-run/references/role-catalog.md` | 新規作成（コピー） | ロール定義 |
| `.claude/skills/dev/team-run/scripts/setup-worktree.sh` | 新規作成 | Worktree セットアップ（チーム全体で1つ） |
| `.claude/skills/dev/team-run/scripts/cleanup-worktree.sh` | 新規作成 | Worktree クリーンアップ |
| `.claude/commands/dev/team-run.md` | 新規作成 | コマンドファイル |
| `CLAUDE.md` | 更新 | スキルテーブル・コマンドテーブルに追加 |
| `.gitignore` | 更新 | `.worktrees/` を追加 |

**既存ファイルへの破壊的変更なし**: team-opencode-exec は変更せず、team-run を並行して追加する。

---

## タスクリスト

### Phase 1: ディレクトリ構成 + スクリプト作成
> スクリプトは独立ファイルのため並列作成可能。

- [ ] `.claude/skills/dev/team-run/` ディレクトリ構造を作成
- [ ] `.claude/skills/dev/team-run/scripts/setup-worktree.sh` を作成 `[PARALLEL]`
- [ ] `.claude/skills/dev/team-run/scripts/cleanup-worktree.sh` を作成 `[PARALLEL]`
- [ ] スクリプトに実行権限を付与（`chmod +x`）
- [ ] `.gitignore` に `.worktrees/` を追加

### Phase 2: リファレンスファイル作成

- [ ] `references/agent-prompt-template.md` を作成（opencode 部分削除、ネイティブ実装用に改修。Self-claim Protocol、Plan Approval セクション、fileOwnership セクション追加）
- [ ] `references/role-catalog.md` を team-opencode-exec からコピー

### Phase 3: メインスキル定義（SKILL.md）
> Phase 1, 2 の成果物を参照するため、Phase 1, 2 完了後に実施。

- [ ] `.claude/skills/dev/team-run/SKILL.md` を作成
  - frontmatter（name, description, trigger, allowed-tools）
  - 必須リソーステーブル
  - Step 1: 計画選択 + Pre-flight 検証
  - Step 2: 環境セットアップ（Worktree）
  - Step 3: チーム作成 + タスク登録 + Delegate mode 宣言
  - Step 4: Wave 実行ループ（Teammate スポーン、Subagent レビュー、hooks、Self-claim、Plan Approval）
  - Step 5: レビュー・フィードバックループ
  - Step 6: PR作成 + クリーンアップ
  - Step 7: 結果集約 + TeamDelete
  - エラーハンドリング
  - 重要な注意事項

### Phase 4: コマンドファイル + CLAUDE.md 更新

- [ ] `.claude/commands/dev/team-run.md` を作成 `[PARALLEL]`
- [ ] `CLAUDE.md` を更新（スキルテーブルに `dev:team-run` 追加、コマンドテーブルに `/dev:team-run` 追加） `[PARALLEL]`

### Phase 5: 検証
> 全ファイル作成後に実施。

- [ ] `.claude/skills/dev/team-run/` 以下の全ファイルが正しく配置されていることを Glob で確認
- [ ] SKILL.md 内の相対パス参照（`references/...`, `scripts/...`）が正しいことを確認
- [ ] `setup-worktree.sh` の構文チェック（`bash -n`）
- [ ] `cleanup-worktree.sh` の構文チェック（`bash -n`）
- [ ] CLAUDE.md のスキル一覧・コマンド一覧に不整合がないことを確認
- [ ] agent-prompt-template.md の変数一覧が SKILL.md の変数置換手順と一致することを確認
- [ ] `.gitignore` に `.worktrees/` が含まれていることを確認
