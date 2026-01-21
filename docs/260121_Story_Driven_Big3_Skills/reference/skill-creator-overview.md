# skill-creator 概要

> **参照元**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator`
> **配置先**: `.claude/skills/skill-creator/`

---

## 概要

スキルを作成・更新・プロンプト改善するためのメタスキル。
Big 3（story-to-tasks, developing, feedback）の外側に配置し、feedbackからの呼び出しで連携する。

---

## 設計原則

| 原則 | 説明 |
|------|------|
| **Collaborative First** | ユーザーとの対話を通じて要件を明確化 |
| **Script First** | 決定論的処理はスクリプトで実行（100%精度） |
| **Progressive Disclosure** | 必要な時に必要なリソースのみ読み込み |
| **Self-Contained Skills** | 各スキルは独自のnode_modules・依存関係を持つ |

---

## モード一覧

| モード | 用途 | Big 3との連携 |
|--------|------|---------------|
| **collaborative** | ユーザー対話型スキル共創（推奨） | feedbackで「スキル化候補」検出時 |
| **create** | 要件が明確な場合の新規作成 | 明確な要件がある場合 |
| **update** | 既存スキル更新 | パターン蓄積でルール化が必要な場合 |
| **improve-prompt** | プロンプト改善 | スキルの成功率が低い場合 |

---

## ディレクトリ構造

```
skill-creator/
├── SKILL.md              # 必須: 中枢（500行以内推奨）
├── LOGS.md               # 実行記録
├── EVALS.json            # メトリクス
├── agents/               # LLMサブタスク定義（20ファイル）
├── scripts/              # 決定論的処理（25+ファイル）
├── references/           # 知識の外部化（23ファイル）
├── schemas/              # JSON検証スキーマ（23+ファイル）
└── assets/               # テンプレート（17+ファイル）
```

---

## 主要エージェント

| エージェント | 役割 | 使用フェーズ |
|--------------|------|-------------|
| interview-user.md | ユーザーヒアリング | collaborative Phase 0 |
| analyze-request.md | 要件分析 | create Phase 1 |
| design-workflow.md | ワークフロー設計 | create Phase 2 |
| plan-structure.md | 構造計画 | create Phase 3 |
| analyze-feedback.md | フィードバック分析 | 自己改善サイクル |
| save-patterns.md | パターン保存 | 自己改善サイクル |

---

## 主要スクリプト

| スクリプト | 役割 | 使用タイミング |
|------------|------|----------------|
| init_skill.js | スキル初期化 | 新規作成時 |
| validate_all.js | 全体検証 | 作成/更新完了時 |
| log_usage.js | 実行記録 | 毎回実行後 |
| collect_feedback.js | フィードバック収集 | 改善サイクル |
| apply_self_improvement.js | 改善適用 | 自己改善時 |

---

## フィードバック機構

### 記録ファイル

| ファイル | 用途 | 更新タイミング |
|----------|------|----------------|
| LOGS.md | 実行ログ | 毎回実行後 |
| EVALS.json | メトリクス | 毎回実行後 |
| references/patterns.md | 成功/失敗パターン | パターン発見時 |

### 自己改善サイクル

```
スキル実行
    │
    ▼
[実行結果記録] ← log_usage.js
    │
    ▼
[メトリクス更新] ← EVALS.json
    │
    ▼
[パターン分析] ← analyze-feedback (LLM)
    │
    ├─ patterns[] あり → [パターン保存] → patterns.md更新
    │
    └─ suggestions[] あり → [改善提案生成] → [改善適用]
```

### レベルアップ条件

| レベル | 名称 | 最小使用回数 | 最小成功率 |
|--------|------|-------------|-----------|
| 1 | Beginner | 0 | 0% |
| 2 | Intermediate | 5 | 60% |
| 3 | Advanced | 15 | 75% |
| 4 | Expert | 30 | 85% |

---

## Big 3との連携パターン

### feedbackからの呼び出し

```
[feedback] 実行
    │
    ├─ DESIGN.md蓄積
    │
    └─ パターン検出
         │
         ├─ 同一パターン3回以上 → スキル化候補
         │
         └─ プロジェクト固有規約 → ルール化候補
              │
              ▼
         AskUserQuestion:
         「これらのパターンをスキル/ルールとして保存しますか？」
              │
              ▼ (承認時)
         [skill-creator呼び出し]
              │
              ├─ collaborative: 対話でスキル共創
              └─ create: 新規スキル作成
```

### 呼び出しトリガー

| 条件 | 推奨モード | 理由 |
|------|-----------|------|
| 同一パターン3回以上 | create | パターンが明確 |
| 曖昧な改善要求 | collaborative | 対話で要件明確化 |
| 既存スキル改善 | update/improve-prompt | 既存資産の活用 |

---

## コピー時の注意点

### パス参照の修正

skill-creator内のパス参照を`.claude/skills/skill-creator/`に合わせる必要がある。

**修正対象**:
- SKILL.md内の`[agents/xxx.md]`参照
- SKILL.md内の`[references/xxx.md]`参照
- SKILL.md内の`[scripts/xxx.js]`参照
- scripts/内のファイルパス定数

### 動作確認

```bash
# バリデーション
node .claude/skills/skill-creator/scripts/validate_all.js .claude/skills/skill-creator

# 簡易チェック
node .claude/skills/skill-creator/scripts/quick_validate.js .claude/skills/skill-creator
```

---

## 関連リソース

- **参照元SKILL.md**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/SKILL.md`
- **フィードバックループ**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/references/feedback-loop.md`
- **自己改善サイクル**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/references/self-improvement-cycle.md`
- **スキル構造仕様**: `docs/SAMPLE/dev/meta-skill-creator/skills/skill-creator/references/skill-structure.md`
