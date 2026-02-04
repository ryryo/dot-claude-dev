# Codex Integration Plan: dev/スキル進化計画

## 概要

Claude Code Orchestraの思想を参考に、現在の`.claude/skills/dev/`スキルをCodex CLI協調型に進化させる計画。

**方針**: 単純なステップ追加ではなく、**既存エージェントの担当変更**を優先し、その後に必要な追加を検討。

---

## 1. 既存エージェントのCodex委譲（担当変更）

### 1.1 対象エージェント

| エージェント | 現在の担当 | 変更後 | 理由 |
|------------|-----------|--------|------|
| **tdd-review.md** | Claude opus | Codex CLI | 批判的分析、過剰適合検出は深い推論が必要 |
| **propose-improvement.md** | Claude opus | Codex CLI | トレードオフ分析、設計提案はCodex向き |
| **tdd-refactor.md** | Claude opus | Codex CLI | リファクタリング判断は設計判断を伴う |

### 1.2 変更しないエージェント

| エージェント | 理由 |
|------------|------|
| **analyze-story.md** | ストーリー理解はClaude、スコープ判断のみCodex検討可 |
| **decompose-tasks.md** | コード探索・context作成はClaudeサブエージェントが適切 |
| **tdd-write-test.md** | テスト作成は実装タスク |
| **tdd-implement.md** | 実装タスク |
| **e2e-*.md** | UI検証はagent-browser |

### 1.3 実装方針

```
# Codex委譲パターン（サブエージェント経由）
agentContent = Read(".claude/skills/dev/.../agents/{agent}.md")
Task({
  prompt: agentContent + 追加コンテキスト,
  subagent_type: "general-purpose",
  model: "sonnet"  # サブエージェントがCodex CLIを呼び出す
})
```

**サブエージェント内でCodex呼び出し**:
```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
{エージェントのプロンプト}
" 2>/dev/null
```

---

## 2. 計画レビュー（新規追加）

### 2.1 タイミング

```
dev:story フロー:
  Step 1: analyze-story → story-analysis.json
  Step 2: decompose-tasks → task-list.json
  Step 3: assign-workflow → TODO.md
  ★ Step 4: plan-review → Codexでレビュー ← 新規追加
  Step 5: ユーザー確認
```

### 2.2 エージェント設計

**ファイル**: `.claude/skills/dev/story/agents/plan-review.md`

```markdown
# plan-review

## 役割

TODO.mdのタスク分解をCodex CLIでレビューする。

## 推奨モデル

**sonnet** - サブエージェントとしてCodex呼び出し

## 入力

- TODO.md
- story-analysis.json
- task-list.json

## Codex呼び出し

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Review this task breakdown:

## Story Analysis
{story-analysis.json内容}

## Task List
{TODO.md内容}

Analyze:
1. Task granularity - Too big? Too small?
2. Dependency ordering - Correct sequence?
3. Workflow assignment - TDD/E2E/TASK appropriate?
4. Missing tasks - Any gaps?
5. Risk assessment - Potential blockers?

Provide:
- Top 3-5 recommendations
- Suggested modifications
- Risk level (Low/Medium/High)
" 2>/dev/null
```

## 出力

レビュー結果をユーザーに提示（TODO.md修正提案を含む）
```

### 2.3 SKILL.md更新

```markdown
### Step 4: 計画レビュー（Codex）

1. → **エージェント委譲**（plan-review.md / sonnet）
2. レビュー結果をユーザーに提示
3. 修正が必要なら Step 3 に戻る

**ゲート**: Codexレビューが完了しなければ次に進まない。
```

---

## 3. 実装後レビュー（dev:feedbackに統合）

### 3.1 タイミング

```
dev:feedback フロー:
  ★ Phase 0: post-impl-review → Codexで実装レビュー ← 新規追加
  Phase 1: analyze-changes → 分析JSON
  Phase 2a: update-design → 機能DESIGN.md
  Phase 2b: 総合DESIGN.md更新
  Phase 2c: code-simplifier
  Phase 3: propose-improvement → Codex ← 既存変更
  Phase 4: evaluate-tests
```

### 3.2 エージェント設計

**ファイル**: `.claude/skills/dev/feedback/agents/post-impl-review.md`

```markdown
# post-impl-review

## 役割

実装完了後、Codex CLIで全体レビューを実施。
実装バイアスを排除した客観的な品質チェック。

## 推奨モデル

**sonnet** - サブエージェントとしてCodex呼び出し

## 入力

- git diff（mainブランチとの差分）
- feature-slug, story-slug

## Codex呼び出し

```bash
# まずdiffを取得
git diff main...HEAD

# Codexでレビュー
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Review this implementation:

## Changes
{git diff出力}

Check:
1. Code quality and patterns
2. Potential bugs
3. Missing edge cases
4. Security concerns
5. Performance issues
6. Test coverage gaps

Provide:
- Summary of changes
- Critical issues (must fix)
- Recommendations (nice to have)
- Overall quality score (1-10)
" 2>/dev/null
```

## 出力

レビュー結果をユーザーに提示。
Critical issuesがあれば修正を推奨。
```

### 3.3 SKILL.md更新

```markdown
### Phase 0: 実装後レビュー（Codex）

1. → **エージェント委譲**（post-impl-review.md / sonnet）
2. レビュー結果をユーザーに提示
3. Critical issuesがあれば修正を推奨（dev:developingに戻る選択肢）

**ゲート**: Codexレビューが完了しなければ次に進まない。
```

---

## 4. 変更サマリー

### 4.1 ファイル変更一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `dev/story/SKILL.md` | 修正 | Step 4（plan-review）追加 |
| `dev/story/agents/plan-review.md` | 新規 | Codex計画レビューエージェント |
| `dev/developing/agents/tdd-review.md` | 修正 | Codex呼び出しに変更 |
| `dev/developing/agents/tdd-refactor.md` | 修正 | Codex呼び出しに変更 |
| `dev/feedback/SKILL.md` | 修正 | Phase 0（post-impl-review）追加 |
| `dev/feedback/agents/post-impl-review.md` | 新規 | Codex実装後レビューエージェント |
| `dev/feedback/agents/propose-improvement.md` | 修正 | Codex呼び出しに変更 |

### 4.2 新規ルール（オプション）

`.claude/rules/workflow/codex-delegation.md`:

```markdown
# Codex Delegation Rule

## いつCodexに相談するか

MUST consult Codex for:
- 設計判断（どう構造化すべき？）
- レビュー（過剰適合、抜け道チェック）
- リファクタリング判断
- トレードオフ分析
- 改善提案

## 呼び出し方法

サブエージェント経由で呼び出し、メインコンテキストを保護:

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
{question}
" 2>/dev/null
```

## 言語プロトコル

1. Codexへは英語で質問
2. 英語で回答を受け取る
3. ユーザーには日本語で報告
```

---

## 5. 実装順序

### Phase 1: 既存エージェントの委譲変更

1. [ ] tdd-review.md をCodex呼び出しに変更
2. [ ] tdd-refactor.md をCodex呼び出しに変更
3. [ ] propose-improvement.md をCodex呼び出しに変更
4. [ ] 動作確認（TDDワークフローで検証）

### Phase 2: 計画レビュー追加

5. [ ] plan-review.md を新規作成
6. [ ] dev/story/SKILL.md を更新（Step 4追加）
7. [ ] 動作確認（dev:storyで検証）

### Phase 3: 実装後レビュー追加

8. [ ] post-impl-review.md を新規作成
9. [ ] dev/feedback/SKILL.md を更新（Phase 0追加）
10. [ ] 動作確認（dev:feedbackで検証）

### Phase 4: ルール整備（オプション）

11. [ ] codex-delegation.md を新規作成
12. [ ] ドキュメント整備

---

## 6. リスクと考慮事項

### 6.1 Codex CLI依存

- **リスク**: Codex CLIがない環境では動作しない
- **対策**: フォールバックとしてClaude opusを使用可能にする設計

```markdown
## フォールバック

Codex CLIが利用不可の場合:
- 環境変数 `USE_CODEX=false` で無効化
- Claude opusにフォールバック
```

### 6.2 レスポンス時間

- **リスク**: Codex呼び出しでワークフローが遅くなる
- **対策**: バックグラウンド実行（`run_in_background: true`）を活用

### 6.3 コスト

- **リスク**: Codex API呼び出しのコスト増
- **対策**:
  - 重要なレビューポイントのみCodex使用
  - 軽微な判断はClaude haiku/sonnetを維持

---

## 7. 今後の拡張

### 7.1 Gemini CLI導入時

Gemini CLIが利用可能になった場合:
- リサーチフェーズをdev:storyの前に追加
- ライブラリ調査、ベストプラクティス収集

### 7.2 Hooks自動協調

将来的に自動協調提案を導入する場合:
- agent-router.py相当のHookを追加
- ユーザー入力から自動的にCodex相談を提案

---

## 参考

- [Claude Code Orchestra](./claude-code-orchestra/) - マルチエージェント協調テンプレート
- [Claude Code Orchestra 記事](./Claude%20Code%20Orchestra_%20Claude%20Code%20×%20Codex%20CLI%20×%20Gemini%20CLIの最適解を探る.md)
