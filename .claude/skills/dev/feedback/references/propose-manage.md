# ルール化・CLAUDE.md更新提案仕様（propose-manage）

ルール化候補の検出 + CLAUDE.md更新候補の検出 + テスト資産管理を実施する。
繰り返しパターンから `.claude/rules/` へのルール追加や `CLAUDE.md` の更新を提案する。
コードの品質・正しさのレビューはStep 1の責務。ここでは「今後の開発を効率化するメタ改善」だけを扱う。

## 入力

- Step 1（review-analyze）の分析JSON
- Step 2のDESIGN.md更新内容
- 既存のルール一覧（`.claude/rules/` 配下）
- CLAUDE.md の現在の内容
- feature-slug
- TDDタスクの有無

## 実行フロー

### 1. コンテキスト収集

```
Read("docs/FEATURES/{feature-slug}/DESIGN.md")
Read("CLAUDE.md")
Glob(".claude/rules/**/*.md")
```

### 2. OpenCode CLIで改善分析

```bash
opencode run -m openai/gpt-5.3-codex "
Analyze this implementation for rule and documentation improvement opportunities:

## Analysis JSON
{分析JSONの内容}

## DESIGN.md Updates
{DESIGN.md更新内容}

## Existing Rules
{既存ルール一覧}

## Current CLAUDE.md
{CLAUDE.mdの内容}

Evaluate for:
1. Rule candidates: conventions/patterns that should be enforced as .claude/rules/ files
   - For each candidate, specify the exact target path: .claude/rules/{category}/{name}.md
   - If updating an existing rule, specify which file and what to add/change
2. CLAUDE.md update candidates: workflow descriptions, conventions, or references that should be added/updated
   - For each candidate, specify the target section in CLAUDE.md
3. Trade-off analysis: time investment vs. long-term efficiency gain

NOTE: Do NOT suggest code refactoring, implementation improvements, or new skill creation.
Focus only on patterns that should become rules or CLAUDE.md updates.

Provide:
- Top 3-5 prioritized candidates
- Clear rationale and occurrence count for each
- Exact target file path or CLAUDE.md section
- Expected efficiency gain
" 2>&1
```

### 3. フォールバック（OpenCode利用不可時）

以下のパターン検出基準に基づいて手動分析する:

#### ルール化基準

| 出現回数 | 判定 | アクション |
|---------|------|------------|
| 1回 | 記録のみ | DESIGN.mdに記載 |
| 2回 | 監視 | パターンとして認識 |
| 3回以上 | ルール化候補 | 提案を生成 |

パターンタイプ: コーディングパターン、命名規則、設計判断、ワークフロー規約

#### CLAUDE.md更新基準

- ワークフローの新しい慣習が確立された
- 既存セクションの記述が実態と乖離している
- 新しいツール・ライブラリの利用ルールが必要

#### 当てはめ先の判定

| パターンの性質 | 当てはめ先 |
|---------------|-----------|
| 特定ファイルパスに紐づく規約 | `.claude/rules/{category}/{name}.md`（globs で自動適用） |
| ワークフロー全体に関わる規約 | `.claude/rules/workflow/{name}.md` |
| プロジェクト全体の方針・概要 | `CLAUDE.md` の該当セクション |
| 既存ルールの拡張 | 該当する既存 `.claude/rules/` ファイルに追記 |

#### 除外条件

- プロジェクト固有すぎる（他で使えない）
- 一時的なパターン（実験的、将来変更予定）
- 既存と重複（既存ルールでカバー済み）

### 4. テスト評価（TDDタスクがあった場合のみ）

TDDで作成されたテストを以下の観点で分類する:

| 判断基準 | アクション |
|---------|-----------|
| 長期的な価値がある | 保持（回帰テスト、仕様ドキュメント） |
| 一時的な価値のみ | 簡素化 or 削除候補 |

評価ポイント:
- **回帰テストとしての価値**: 将来の変更で壊れたことを検知できるか
- **メンテナンスコスト**: 実装変更のたびにテスト修正が必要か
- **ドキュメントとしての価値**: テストが仕様を伝えているか

### 5. IMPROVEMENTS.md作成

以下の構造で `docs/FEATURES/{feature-slug}/IMPROVEMENTS.md` に Write する:

```markdown
# ルール化・CLAUDE.md更新提案 ({feature-slug})

## 1. ルール化候補
- {ルール名}（出現回数: {N}回）
  - 出現場所: {ファイル/ストーリー}
  - 背景 / 文脈
  - 期待される効果
  - 当てはめ先: `.claude/rules/{category}/{name}.md`（新規 or 既存ファイル名）

## 2. CLAUDE.md更新候補
- {更新内容}
  - 対象セクション: CLAUDE.md の「{セクション名}」
  - 背景 / 文脈
  - 具体的な追記・変更内容

## 3. テスト資産の評価（TDD時のみ）
- 保持推奨: [テスト名一覧と理由]
- 簡素化候補: [テスト名一覧と理由]
- 削除候補: [テスト名一覧と理由]

## 4. メモ / 補足
- 後続作業で知っておくべき前提・注意点
```

## 注意事項

- 既存ルールとの重複を避ける
- 具体的な当てはめ先（ファイルパス or CLAUDE.md セクション）を必ず明記する
- コードや設定ファイルを直接変更しない（提案のみ）
- 「目的・背景・具体的な変更内容」がわかるレベルまで具体的に書く
