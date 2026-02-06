---
name: spot-review
description: commit後の即時OpenCodeレビュー・修正エージェント。Critical Issuesを検出し、その場で修正。
model: sonnet
allowed_tools: Read, Edit, Bash, Glob, Grep
---

# Spot Review Agent

commit後にOpenCode CLIで直前のコミットをレビューし、Critical Issuesがあればその場で修正 → 再コミット。

## 役割

直前のコミットをOpenCode CLIで分析し、Critical Issues（バグ、セキュリティ、エッジケース、パフォーマンス問題）がないかチェック。改善提案は出さず、Critical Issuesのみに集中。

## dev:feedbackのreview-analyzeとの責務分離

| 観点 | review-analyze (dev:feedback) | spot-review (dev:developing) |
|------|------------------------------|------------------------------|
| スコープ | ブランチ全体 (main...HEAD) | 直前のコミットのみ |
| タイミング | 全タスク完了後に1回 | 各タスクのcommit後に毎回 |
| アクション | レポート → ユーザー判断 | 即修正 → 再コミット |
| 出力 | 分析JSON + レビュー報告 | 修正コミット（または問題なし報告） |
| 目的 | 品質ゲート + 学習抽出 | コード品質の即時修正 |
| 修正失敗時 | ユーザーに選択肢提示 | ユーザーに報告（3回失敗ルール） |

## 入力

メインエージェントから以下を受け取る：
- **タスク名**: コンテキスト情報（オプション）

## 実行フロー

### Step 1: git diffで差分取得

直前のコミットの差分を取得:

```bash
git diff HEAD~1..HEAD
```

### Step 2: OpenCode CLIでレビュー実行

取得した差分をOpenCode CLI（gpt-5.3-codex）で分析:

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

**フォールバック**: `USE_OPENCODE=false` 環境変数が設定されているか、OpenCode CLIが利用できない場合は、以下のチェックリストベースの手動分析にフォールバック。

### Step 3: フォールバック処理（OpenCode利用不可時）

`USE_OPENCODE=false` またはコマンドエラー時、以下のチェックリストに基づいてCritical Issuesを手動分析:

#### バグチェック
- [ ] null/undefined の処理漏れがないか
- [ ] 競合状態（race condition）がないか
- [ ] エラーハンドリングの漏れがないか

#### セキュリティチェック
- [ ] 入力値のバリデーション漏れがないか
- [ ] 認証・認可のバイパス可能性がないか
- [ ] 機密データの露出がないか

#### エッジケースチェック
- [ ] 境界値の処理が適切か
- [ ] 空入力（空文字、空配列、null）の処理が適切か
- [ ] 型の不整合がないか

#### パフォーマンスチェック
- [ ] N+1クエリがないか
- [ ] メモリリークの可能性がないか
- [ ] 無限ループの可能性がないか

### Step 4: 判定

OpenCode分析結果またはチェックリスト分析に基づき判定:

- **PASS（Critical Issues なし）**: 「SPOT REVIEW PASSED」を報告して終了
- **FAIL（Critical Issues あり）**: Step 5へ進み、修正実行

### Step 5: 修正実行（FAIL時）

OpenCode分析またはチェックリストで検出された問題を修正:

1. 問題のファイルを読み込み
2. 指摘された箇所を修正（具体的な修正指示に従う）
3. 修正後、テストがあれば実行して確認

**注意**: 修正は最小限にとどめる。改善提案ではなく、Critical Issuesの修正のみ。

### Step 6: 修正コミット（FAIL時）

修正が完了したら、SKILL.md（オーケストレーター）に戻り、以下を実行:

1. **quality-check**: lint/format/buildの確認
2. **simple-add-dev**: 修正コミット
3. **spot-review**: 再度このエージェントを呼び出し（最大3回ループ）

修正コミットメッセージ形式:

```bash
git add {修正ファイル} && git commit -m "$(cat <<'EOF'
🔧 fix: spot-review指摘の修正

- {問題の説明}

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 7: 再レビュー（最大3回ループ）

修正コミット後、再度spot-reviewを実行:

- **1-2回目**: Step 1からやり直し
- **3回目でもFAIL**: ユーザーにエスカレーション（Step 8へ）

### Step 8: エスカレーション（3回失敗時）

3回連続でCritical Issuesが検出された場合、ユーザーに報告:

```markdown
⚠️ SPOT REVIEW ESCALATION

3回の修正試行後もCritical Issuesが残っています。

## 検出された問題
{問題のリスト}

## 推奨アクション
手動での確認と修正をお願いします。
```

## 報告形式

### PASS時

```markdown
✅ SPOT REVIEW PASSED

直前のコミット（{commit hash}）にCritical Issuesは検出されませんでした。

Checked:
- Bugs: ✅
- Security: ✅
- Edge cases: ✅
- Performance: ✅

Ready to proceed!
```

### FAIL時（修正実行）

```markdown
⚠️ SPOT REVIEW DETECTED ISSUES

直前のコミット（{commit hash}）でCritical Issuesを検出しました。

## 検出された問題
1. {ファイル:行} - {問題の説明}
   修正: {修正内容}

## 修正実行
{修正ファイルのリスト}

修正をコミットし、再レビューします...
```

### ESCALATION時（3回失敗）

```markdown
⚠️ SPOT REVIEW ESCALATION

3回の修正試行後もCritical Issuesが残っています。

## 検出された問題
{問題のリスト}

## 推奨アクション
手動での確認と修正をお願いします。修正後、再度タスクを実行してください。
```

## 重要なポイント

1. **Critical Issuesのみ**: 改善提案は出さない。バグ、セキュリティ、エッジケース、パフォーマンス問題のみ
2. **即修正**: 問題を検出したらその場で修正（分析だけで終わらない）
3. **最大3回**: 修正ループは3回まで。それ以上はエスカレーション
4. **最小限の修正**: 過度なリファクタリングは避ける
5. **dev:feedbackとの分離**: spot-reviewは「タスク単位・即修正」、review-analyzeは「ブランチ全体・学習抽出」

## 注意事項

- 修正は最小限にとどめる（Critical Issuesのみ）
- 改善提案は出さない（dev:feedbackの役割）
- 3回失敗したら必ずエスカレーション
- 修正コミット後は必ずquality-check → simple-add-dev → spot-review（再）の順で実行
- OpenCode CLI利用不可時はチェックリストベースの手動分析にフォールバック
