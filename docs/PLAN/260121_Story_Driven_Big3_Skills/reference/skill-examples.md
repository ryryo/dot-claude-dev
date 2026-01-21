# スキル実装例

## skills/dev/story-to-tasks/SKILL.md

```markdown
---
name: dev:story-to-tasks
description: ストーリーからTDD/PLAN分岐付きタスクリストを生成。「タスクを作成」「/dev:story」で起動。
---

# ストーリー → タスク生成

## 概要

ユーザーストーリーから実装可能なタスクリスト（TODO.md）を生成する。
各タスクにはTDD/PLANラベルを自動付与。

## 入力

- ユーザーからの会話（ストーリー説明）
- または docs/USER_STORIES.md

## 出力

- docs/features/{feature-slug}/stories/{story-slug}/TODO.md（TDD/PLANラベル付き）

## ワークフロー

### フェーズ1: ストーリー理解

ユーザーからストーリーを聞き取る、または既存ファイルを読み込む。

\`\`\`javascript
Read({ file_path: "docs/USER_STORIES.md" })  // 存在すれば
\`\`\`

### フェーズ2: タスク分解

ストーリーを実装可能なタスクに分解。

各タスクについてTDD/PLAN判定：
- 入出力が明確 → [TDD]
- 視覚的確認が必要 → [PLAN]

→ 詳細: references/tdd-criteria.md

### フェーズ3: TODO.md生成

\`\`\`markdown
# TODO

## フェーズ1: ユーザー認証機能

### TDDタスク
- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング

### PLANタスク
- [ ] [PLAN][IMPL] LoginForm UIコンポーネント
- [ ] [PLAN][AUTO] agent-browser検証

### 共通
- [ ] [CHECK] lint/format/build
\`\`\`

### フェーズ4: 確認

\`\`\`javascript
AskUserQuestion({
  questions: [{
    question: "タスクリストを確認してください。問題なければ実装を開始しますか？",
    header: "確認",
    options: [
      { label: "実装開始", description: "/dev:impl で実装を開始" },
      { label: "修正が必要", description: "タスクを調整" }
    ],
    multiSelect: false
  }]
})
\`\`\`

## 完了条件

- [ ] TODO.mdが生成された
- [ ] 各タスクにTDD/PLANラベルが付与された

## 関連スキル

- **dev:developing**: TDDタスクの実装
- **dev:feedback**: 実装後のフィードバック
```

## skills/dev/feedback/SKILL.md

```markdown
---
name: dev:feedback
description: 実装完了後、学んだことをDESIGN.mdに蓄積。スキル/ルールの自己改善も提案。「フィードバック」「/dev:feedback」で起動。
---

# フィードバック → 仕様書蓄積

## 概要

実装完了後、学んだことをシステム仕様書（DESIGN.md）に蓄積。
繰り返しパターンはスキル/ルール化を提案。

## 入力

- 実装済みコード（git diff）
- output/フォルダのレポート（あれば）

## 出力

- docs/features/{feature-slug}/DESIGN.md（追記・更新）
- docs/features/DESIGN.md（総合設計への反映）
- スキル/ルール化の提案

## ワークフロー

### フェーズ1: 変更内容の収集

\`\`\`bash
git diff --stat HEAD~5
git log --oneline -10
\`\`\`

output/フォルダがあればレポートも読み込み。

### フェーズ2: 学習事項の抽出

実装から学んだことを整理：
- 設計判断（なぜこの構造にしたか）
- 技術的な発見
- 注意点・ハマりどころ

### フェーズ3: DESIGN.md更新

既存のDESIGN.mdがあれば追記、なければ新規作成。

\`\`\`markdown
# システム仕様書

## 更新履歴

### 2024-01-21: ユーザー認証機能

**設計判断**:
- JWTではなくセッションベース認証を採用（理由: ...）
- バリデーションはZodを使用

**学んだこと**:
- React Hook Formとの連携でのポイント
- エラーハンドリングのパターン
\`\`\`

### フェーズ4: 自己改善提案

繰り返しパターンを検出し、提案：

\`\`\`markdown
💡 改善提案を検出しました

1. **ルール化候補**:
   - Zodバリデーションパターンを3回使用
   → `.claude/rules/languages/typescript/validation.md` として保存？

2. **スキル化候補**:
   - 認証フロー実装で同じ手順を実行
   → `.claude/skills/dev/auth-setup/SKILL.md` として抽出？
\`\`\`

\`\`\`javascript
AskUserQuestion({
  questions: [{
    question: "これらのパターンをルール/スキルとして保存しますか？",
    header: "自己改善",
    options: [
      { label: "保存する", description: "ルール/スキルファイルを作成" },
      { label: "今回はスキップ", description: "保存しない" }
    ],
    multiSelect: false
  }]
})
\`\`\`

## 完了条件

- [ ] DESIGN.mdが更新された
- [ ] 自己改善提案が表示された（該当あれば）

## 関連スキル

- **dev:story-to-tasks**: 次のストーリーのタスク生成
```

## Worktree活用（オプション）

複数の独立したタスクを並列実行する場合、Worktreeを活用可能。

```bash
# TDDタスク用
git worktree add ../project-{story-slug}-tdd feature/{story-slug}-tdd

# PLANタスク用
git worktree add ../project-{story-slug}-plan feature/{story-slug}-plan
```

→ 詳細: [Worktree運用ガイド](worktree-guide.md)
