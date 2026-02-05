# propose-manage

## 役割

スキル/ルール化候補の検出 + テスト資産管理を実施。繰り返しパターンからスキル化・ルール化を提案する。
コードの品質・正しさのレビューはStep 1の責務。ここでは「今後の開発を効率化するメタ改善」だけを扱う。

## 推奨モデル

**sonnet** - サブエージェントとしてCodex呼び出し

## 入力

- Step 1（review-analyze.md）の分析JSON
- Step 2のDESIGN.md更新内容
- 既存のルール/スキル一覧
- feature-slug
- TDDタスクの有無

## 実行フロー

### Step 1: コンテキスト収集

```javascript
Read({ file_path: "docs/features/{feature-slug}/DESIGN.md" })
Glob({ pattern: ".claude/skills/**/*.md" })
Glob({ pattern: ".claude/rules/**/*.md" })
```

### Step 2: Codex CLIで改善分析

```bash
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Analyze this implementation for improvement opportunities:

## Analysis JSON
{分析JSONの内容}

## DESIGN.md Updates
{DESIGN.md更新内容}

## Existing Skills/Rules
{既存スキル/ルール一覧}

Evaluate for meta-improvement opportunities (NOT code review):
1. Skill candidates (repeated implementation patterns worth automating as Claude Code skills)
2. Rule candidates (conventions that should be enforced as Claude Code rules)
3. Trade-off analysis (time investment vs. long-term efficiency gain)

NOTE: Do NOT suggest code refactoring or implementation improvements.
Focus only on patterns that should become reusable skills or rules.

Provide:
- Top 3-5 prioritized skill/rule candidates
- Clear rationale and occurrence count for each
- Expected efficiency gain
- Suggested file path (.claude/skills/ or .claude/rules/)
" 2>/dev/null
```

### Step 3: フォールバック（Codex利用不可時）

以下のパターン検出基準に基づいて手動分析:

#### ルール化基準

| 出現回数 | 判定 | アクション |
|---------|------|------------|
| 1回 | 記録のみ | DESIGN.mdに記載 |
| 2回 | 監視 | パターンとして認識 |
| 3回以上 | ルール化候補 | 提案を生成 |

パターンタイプ: コーディングパターン、命名規則、設計判断

#### スキル化基準

| 出現回数 | 判定 | アクション |
|---------|------|------------|
| 1回 | 記録のみ | DESIGN.mdに記載 |
| 2回以上 | スキル化候補 | 提案を生成 |

パターンタイプ: 実装フロー（複数ステップ手順）、セットアップ手順

#### 除外条件

- プロジェクト固有すぎる（他で使えない）
- 一時的なパターン（実験的、将来変更予定）
- 既存と重複（既存ルール/スキルでカバー済み）

### Step 4: テスト評価（TDDタスクがあった場合のみ）

TDDで作成されたテストを以下の観点で分類:

| 判断基準 | アクション |
|---------|-----------|
| 長期的な価値がある | 保持（回帰テスト、仕様ドキュメント） |
| 一時的な価値のみ | 簡素化 or 削除候補 |

評価ポイント:
- **回帰テストとしての価値**: 将来の変更で壊れたことを検知できるか
- **メンテナンスコスト**: 実装変更のたびにテスト修正が必要か
- **ドキュメントとしての価値**: テストが仕様を伝えているか

### Step 5: IMPROVEMENTS.md作成

```markdown
# スキル/ルール化提案 ({feature-slug})

## 1. スキル化候補
- {パターン名}（出現回数: {N}回）
  - 出現場所: {ファイル/ストーリー}
  - 背景 / 文脈
  - 期待される効果
  - 保存先: `.claude/skills/{category}/{name}/SKILL.md`

## 2. ルール化候補
- {ルール名}（出現回数: {N}回）
  - 出現場所: {ファイル/ストーリー}
  - 背景 / 文脈
  - 期待される効果
  - 保存先: `.claude/rules/{category}/{name}.md`

## 3. テスト資産の評価（TDD時のみ）
- 保持推奨: [テスト名一覧と理由]
- 簡素化候補: [テスト名一覧と理由]
- 削除候補: [テスト名一覧と理由]

## 4. メモ / 補足
- 後続エージェントが知っておくべき前提・注意点
```

## 出力

- `docs/features/{feature-slug}/IMPROVEMENTS.md`
- テスト整理方針の提案（TDD時、ユーザー確認用）

## 注意事項

- 既存との重複を避ける
- 具体的な効果を記載
- コードや設定ファイルを直接変更しない
- 実作業は別エージェント（dev:developing, meta-skill-creator等）に委ねる前提
- 「目的・背景・手順・影響範囲」がわかるレベルまで具体的に書く
