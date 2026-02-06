# dev:developing OpenCode CLI 復旧 + spot-review 新設

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

## 概要

dev:developingのtdd-cycle / tdd-reviewには元々Codex CLI連携が存在していたが、commit `462cd41`（2026-02-05）で「Claude自身の分析に完全移行」として削除された。本計画ではこれをOpenCode CLI（gpt-5.3-codex）で**復旧**し、さらに新エージェント `spot-review` を**新設**する。

| 区分 | 対象 | 内容 |
|------|------|------|
| **復旧** | tdd-cycle | 元のCodexリファクタリング分析をOpenCodeで復旧 |
| **復旧** | tdd-review | 元のCodexレビュー分析をOpenCodeで復旧 |
| **新設** | spot-review | commit後の即時OpenCodeレビュー → 修正エージェント |

## 背景

### 削除された経緯（commit 462cd41）

```
🔥 fix: dev:developingからCodex CLI依存を削除（Claude自身の分析に完全移行）
- tdd-cycle: Codexリファクタリング分析→チェックリストベースに統一
- tdd-review: Codexレビュー→opusエージェント自身の分析に統一
```

削除前はCodex CLI（gpt-5.2-codex）を使って「Claudeの実装バイアスを排除する別AI視点の客観分析」を行っていた。現在はdev:story / dev:feedbackでは既にOpenCode CLIに移行済みだが、dev:developingのみ未復旧。

### 復旧の動機

- Claude同士（sonnetが書いたコードをopusがレビュー）だと「同じ思考パターンの盲点」を共有するリスク
- GPT系モデルは異なる推論パターンを持つため補完的に有効
- dev:story / dev:feedbackで既にOpenCode CLIが活用されており、dev:developingだけ欠落している

### 既存のOpenCode導入パターン

| スキル | Agent | 用途 | 呼び出しタイミング |
|--------|-------|------|-------------------|
| dev:story | plan-review | タスク分解の品質レビュー | タスクリスト生成後（1回） |
| dev:feedback | review-analyze | 実装品質チェック | git diff分析時（1回） |
| dev:feedback | propose-manage | メタ改善分析 | 改善提案時（1回） |

共通特徴:
- **品質ゲート**として1回だけ呼び出す（ループ内ではない）
- **分析・レビュー**に限定（コード生成には使わない）
- **フォールバック機構**あり（`USE_OPENCODE=false` でチェックリストベース手動分析）
- コマンド: `opencode run -m openai/gpt-5.3-codex "{prompt}" 2>&1`

## 元のCodexプロンプト（commit 462cd41 削除前）

### tdd-cycle: REFACTORフェーズ

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Analyze this code for refactoring:

## Implementation
{実装コードの内容}

## Test
{テストコードの内容}

Evaluate: SOLID, Testability, Structure, Simplicity, Naming
Prioritize: 1.Testability 2.SRP 3.DRY 4.Naming
Provide specific recommendations with before/after snippets.
" 2>/dev/null
```

フォールバック時はチェックリストベースの手動分析（SRP, DIP, DRY, YAGNI, 命名）。

### tdd-review: レビュー分析

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Review this TDD implementation:

## Implementation
{実装コードの内容}

## Test
{テストコードの内容}

Analyze:
1. Over-fitting: Is the implementation only optimized for test cases?
   - Hardcoded values matching test inputs
   - Order-dependent logic
   - Magic numbers from tests
2. Escape routes: Are there bugs/edge cases that bypass tests?
   - Unhandled null/undefined
   - Missing boundary checks
   - Type mismatches
3. Code quality: Readability, maintainability, conventions
4. Test asset quality:
   - Which tests have long-term regression value?
   - Which tests are redundant or trivial?
   - Can any tests be consolidated via parameterization?

Provide:
- PASS or FAIL verdict
- Specific issues with file:line references
- Concrete fix recommendations
- Test asset recommendations (keep/simplify/remove)
" 2>/dev/null
```

フォールバック時はチェックリストベースの手動分析（過剰適合、抜け道、テスト資産評価）。

## 新しいワークフロー

### Before（現行 = Codex削除後）

```
TDD: tdd-cycle → tdd-review → quality-check → simple-add-dev
E2E: e2e-cycle → quality-check → simple-add-dev
TASK: direct exec → simple-add
```

### After（復旧 + 新設）

```
TDD: tdd-cycle(+OpenCode@REFACTOR) → tdd-review(+OpenCode) → quality-check → simple-add-dev → spot-review(+OpenCode) → COMMIT（修正時）
E2E: e2e-cycle → quality-check → simple-add-dev → spot-review(+OpenCode) → COMMIT（修正時）
TASK: direct exec → simple-add → spot-review(+OpenCode) → COMMIT（修正時）
```

## 変更内容

### 変更1: tdd-cycle.md — OpenCodeリファクタリング分析の復旧

**復旧対象**: Phase 3 REFACTOR内のCodexリファクタリング分析

**復旧方法**: 元のCodexプロンプトの構造・評価観点を維持し、コマンドのみ `opencode run -m openai/gpt-5.3-codex ... 2>&1` に置換。現行のチェックリストはフォールバックとして残す。

**復旧後のプロンプト**:

```bash
opencode run -m openai/gpt-5.3-codex "
Analyze this code for refactoring:

## Implementation
{実装コードの内容}

## Test
{テストコードの内容}

Evaluate: SOLID, Testability, Structure, Simplicity, Naming
Prioritize: 1.Testability 2.SRP 3.DRY 4.Naming
Provide specific recommendations with before/after snippets.
" 2>&1
```

**変更点（元のCodexプロンプトとの差分）**:
- `codex exec --model gpt-5.2-codex --sandbox read-only --full-auto` → `opencode run -m openai/gpt-5.3-codex`
- `2>/dev/null` → `2>&1`
- プロンプト本体は**変更なし**（元のまま復旧）

**フォールバック**: `USE_OPENCODE=false` またはコマンドエラー → 現行のチェックリストベース手動分析（SRP, DIP, DRY, YAGNI, 命名）

**ファイル構造の変更**:
```markdown
### Phase 3: REFACTOR（品質改善）

#### OpenCode CLIでリファクタリング分析:    ← 復旧セクション
{OpenCodeプロンプト}

#### フォールバック（OpenCode利用不可時）:   ← 現行チェックリストをここに移動
チェックリスト:
- [ ] SRP, DIP, DRY, YAGNI, 命名
```

---

### 変更2: tdd-review.md — OpenCodeレビュー分析の復旧

**復旧対象**: Step 2のCodexレビュー分析

**復旧方法**: 元のCodexプロンプトの構造・分析観点を維持し、コマンドのみ置換。現行のチェックリストはフォールバックとして残す。Opusの分析と併用（Opusを主、OpenCodeを補完）。

**復旧後のプロンプト**:

```bash
opencode run -m openai/gpt-5.3-codex "
Review this TDD implementation:

## Implementation
{実装コードの内容}

## Test
{テストコードの内容}

Analyze:
1. Over-fitting: Is the implementation only optimized for test cases?
   - Hardcoded values matching test inputs
   - Order-dependent logic
   - Magic numbers from tests
2. Escape routes: Are there bugs/edge cases that bypass tests?
   - Unhandled null/undefined
   - Missing boundary checks
   - Type mismatches
3. Code quality: Readability, maintainability, conventions
4. Test asset quality:
   - Which tests have long-term regression value?
   - Which tests are redundant or trivial?
   - Can any tests be consolidated via parameterization?

Provide:
- PASS or FAIL verdict
- Specific issues with file:line references
- Concrete fix recommendations
- Test asset recommendations (keep/simplify/remove)
" 2>&1
```

**変更点（元のCodexプロンプトとの差分）**:
- `codex exec --model gpt-5.2-codex --sandbox read-only --full-auto` → `opencode run -m openai/gpt-5.3-codex`
- `2>/dev/null` → `2>&1`
- プロンプト本体は**変更なし**（元のまま復旧）

**フォールバック**: 同上（現行チェックリストベース手動分析）

**Opusとの併用**:
- Step 2冒頭でOpenCode分析を実行
- Opusは自身のチェックリストに基づいて独自分析も実施
- 両者の結果を統合して最終判定（Opusを主、OpenCodeを補完）

**ファイル構造の変更**:
```markdown
### Step 2: OpenCode CLIでレビュー実行    ← 復旧セクション
{OpenCodeプロンプト}

### Step 3: フォールバック処理             ← 現行チェックリストをここに移動
USE_OPENCODE=false またはコマンドエラー時
{チェックリスト}

### Step 4: テスト資産の整理実行           ← 既存（番号繰り下げ）
### Step 5: 結果を日本語で報告             ← 既存（番号繰り下げ）
```

---

### 変更3: spot-review.md — 新規作成

commit後にOpenCodeでレビューし、問題があればその場で修正 → 再コミットするエージェント。**純粋な新設**であり、復旧ではない。

#### dev:feedbackのreview-analyze.mdとの責務分離

| 観点 | review-analyze (dev:feedback) | spot-review (dev:developing) |
|------|------------------------------|------------------------------|
| スコープ | ブランチ全体 (main...HEAD) | 直前のコミットのみ |
| タイミング | 全タスク完了後に1回 | 各タスクのcommit後に毎回 |
| アクション | レポート → ユーザー判断 | 即修正 → 再コミット |
| 出力 | 分析JSON + レビュー報告 | 修正コミット（または問題なし報告） |
| 目的 | 品質ゲート + 学習抽出 | コード品質の即時修正 |
| 修正失敗時 | ユーザーに選択肢提示 | ユーザーに報告（3回失敗ルール） |

#### spot-review フロー

```
1. git diff HEAD~1..HEAD で直前コミットの差分取得
2. OpenCode CLIで分析（Critical Issuesのみ。改善提案は出さない）
3. 判定:
   ├─ PASS（Critical Issues なし） → 「SPOT REVIEW PASSED」報告して終了
   └─ FAIL（Critical Issues あり） → 修正実行 → quality-check → simple-add-dev で修正コミット
4. 修正コミット後、再度 spot-review（最大3回ループ）
5. 3回PASSしなければユーザーにエスカレーション
6. フォールバック: USE_OPENCODE=false またはエラー → チェックリスト手動分析
```

#### spot-review OpenCodeプロンプト

```bash
opencode run -m openai/gpt-5.3-codex "
Review this commit for critical issues only:

## Diff
{git diff HEAD~1..HEAD}

Check (critical issues ONLY - do not suggest improvements):
1. Bugs: null/undefined, race conditions, error handling gaps
2. Security: input validation, auth bypass, sensitive data exposure
3. Edge cases: boundary values, empty inputs, type mismatches
4. Performance: obvious N+1, memory leaks, infinite loops

Provide ONLY:
- PASS (no critical issues) or FAIL (critical issues found)
- If FAIL: list each issue with file:line and specific fix instruction
- Do NOT suggest refactoring, style changes, or improvements
" 2>&1
```

#### spot-review モデル・ツール

| 項目 | 値 |
|------|-----|
| model | sonnet |
| subagent_type | general-purpose |
| allowed_tools | Read, Edit, Bash, Glob, Grep |

#### spot-review 修正ループ

spot-review内で問題を検出した場合:
1. spot-reviewエージェント自身が修正を実行
2. SKILL.md（オーケストレーター）がquality-check → simple-add-dev（修正コミット）を再実行
3. 修正コミット後、再度spot-reviewを実行（最大3回）
4. 3回PASSしなければユーザーにエスカレーション

---

### 変更4: SKILL.md のワークフロー表更新

各ワークフローにspot-review + 修正コミットのステップを追加:
- TDD: CYCLE → REVIEW → CHECK → COMMIT → SPOT-REVIEW(+OpenCode) → COMMIT（修正時）
- E2E: CYCLE → CHECK → COMMIT → SPOT-REVIEW(+OpenCode) → COMMIT（修正時）
- TASK: exec → COMMIT → SPOT-REVIEW(+OpenCode) → COMMIT（修正時）

agents/ 参照リストにspot-review.mdを追加。

---

### 変更5: CLAUDE.md のOpenCode使用エージェントテーブル更新

tdd-cycle、tdd-review、spot-reviewの3エージェントを追加。ワークフロー表も更新。

## 影響範囲

### 変更対象ファイル

| # | ファイル | 変更種別 | 変更内容 |
|---|---------|---------|---------|
| 1 | `.claude/skills/dev/developing/agents/tdd-cycle.md` | **復旧** | REFACTORフェーズのOpenCode分析を復旧 |
| 2 | `.claude/skills/dev/developing/agents/tdd-review.md` | **復旧** | OpenCodeレビュー分析を復旧 |
| 3 | `.claude/skills/dev/developing/agents/spot-review.md` | **新規作成** | commit後の即時レビュー・修正エージェント |
| 4 | `.claude/skills/dev/developing/SKILL.md` | 編集 | ワークフロー表にspot-reviewステップ追加 |
| 5 | `CLAUDE.md` | 編集 | OpenCode使用エージェントテーブルに3エージェント追加 |

### 影響を受けない箇所
- `dev:feedback/agents/review-analyze.md` - スコープ外（将来の軽量化候補として記録）
- `dev:story/agents/plan-review.md` - 既にOpenCode導入済み
- `quality-check.md`, `simple-add-dev.md`, `e2e-cycle.md` - 変更なし

## タスクリスト

### Phase 1: 復旧（並列実行可能）
> 元のCodexプロンプトをOpenCodeに置換して復旧。2ファイルは互いに独立。

- [ ] tdd-cycle.md のOpenCodeリファクタリング分析を復旧 `[PARALLEL]`
  - Phase 3 REFACTORを元の構造に復旧（OpenCode分析 + フォールバック）
  - コマンド: `opencode run -m openai/gpt-5.3-codex ... 2>&1`
  - プロンプト本体は元のCodexプロンプトそのまま
  - フォールバック: 現行チェックリストを維持

- [ ] tdd-review.md のOpenCodeレビュー分析を復旧 `[PARALLEL]`
  - Step 2をOpenCode分析に復旧、現行チェックリストをフォールバックに移動
  - コマンド: 同上
  - プロンプト本体は元のCodexプロンプトそのまま
  - Opusとの併用方針を明記

### Phase 2: 新設
> spot-review.mdは純粋に新規。

- [ ] spot-review.md を新規作成
  - OpenCodeレビュー → 即修正フロー
  - フォールバック機構（USE_OPENCODE=false / コマンドエラー時のチェックリスト手動分析）
  - 報告形式（PASSED / FAILED / ESCALATE）
  - 修正失敗時のエスカレーション（3回ルール）

### Phase 3: オーケストレーター・ドキュメント更新
> Phase 1-2の変更内容と整合させる。

- [ ] SKILL.md のワークフロー表更新
  - TDD/E2E/TASKの各ワークフローにspot-review + 修正COMMITステップ追加
  - 完了条件にspot-reviewパスを追加
  - agents/ 参照リストにspot-review.mdを追加

- [ ] CLAUDE.md のOpenCode使用エージェントテーブル更新
  - tdd-cycle, tdd-review, spot-review の3エージェント追加
  - ワークフロー表を更新

### Phase 4: 検証

- [ ] 全エージェントのOpenCodeコマンド統一チェック
  - `opencode run -m openai/gpt-5.3-codex` が統一されているか
  - `2>&1` が統一されているか
  - `USE_OPENCODE=false` が統一されているか
  - フォールバック機構が全エージェントで一貫しているか

- [ ] ワークフロー整合性チェック
  - SKILL.md ↔ 各agent.md の整合
  - CLAUDE.md ↔ SKILL.md の整合
  - agents/ 参照リストが最新か

## リスク・考慮事項

| リスク | 影響度 | 対策 |
|--------|--------|------|
| OpenCode CLI未インストール環境 | 低 | フォールバック機構を全エージェントに実装（既存パターン踏襲） |
| spot-reviewの修正ループが長期化 | 中 | 最大3回で打ち切り + エスカレーション。Critical Issuesのみに絞る |
| tdd-cycleのTDDサイクル速度低下 | 中 | REFACTORフェーズ末尾の1回のみ。サイクルごとではなくタスク完了時のみ |
| tdd-reviewでOpenCodeとOpusの結論が矛盾 | 低 | Opusを主、OpenCodeを補完として扱う |
| spot-reviewとquality-checkの責務重複 | 低 | quality-checkはlint/format/build（機械的）、spot-reviewはバグ/セキュリティ（分析的） |
| dev:feedbackのreview-analyzeとの重複 | 低 | spot-reviewは「タスク単位・即修正」、review-analyzeは「ブランチ全体・学習抽出」 |

## 注記

- dev:feedbackのreview-analyzeの軽量化は別タスクとして記録。今回のスコープ外
- spot-reviewで修正が発生した場合、SKILL.md（オーケストレーター）がquality-check → simple-add-devを再実行し、再度spot-reviewを呼ぶ（spot-review内ではループしない）
- e2e-cycle.mdへのOpenCode導入は見送り（agent-browserの視覚的検証で十分）
- tdd-cycle / tdd-review のプロンプト本体は元のCodexプロンプトから変更しない（復旧の原則）
