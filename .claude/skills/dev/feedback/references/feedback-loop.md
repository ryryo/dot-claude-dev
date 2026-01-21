# フィードバック記録方式

meta-skill-creatorの機構を活用したフィードバック記録。

## 記録ファイル

| ファイル | 用途 | 更新タイミング |
|----------|------|----------------|
| LOGS.md | 実行ログ | 毎回実行後 |
| EVALS.json | メトリクス | 毎回実行後 |
| patterns.md | 成功/失敗パターン | パターン発見時 |

## LOGS.md 形式

```markdown
# 実行ログ

## 2024-01-21

### 15:30 - dev:feedback

- **result**: success
- **phase**: Phase 4 (改善提案)
- **story**: user-auth/login-form
- **notes**: Zodバリデーションパターンをルール化候補として検出

### 14:00 - dev:developing

- **result**: success
- **phase**: TDD GREEN
- **story**: user-auth/login-form
- **notes**: validateEmail実装完了
```

## EVALS.json 形式

```json
{
  "skills": {
    "dev:story-to-tasks": {
      "totalRuns": 5,
      "successCount": 5,
      "failureCount": 0,
      "successRate": 1.0,
      "averagePhases": 4,
      "lastRun": "2024-01-21T15:30:00Z"
    },
    "dev:developing": {
      "totalRuns": 12,
      "successCount": 11,
      "failureCount": 1,
      "successRate": 0.92,
      "tddCycles": 8,
      "planCycles": 4,
      "lastRun": "2024-01-21T14:00:00Z"
    },
    "dev:feedback": {
      "totalRuns": 3,
      "successCount": 3,
      "failureCount": 0,
      "successRate": 1.0,
      "patternsDetected": 2,
      "rulesCreated": 1,
      "skillsCreated": 0,
      "lastRun": "2024-01-21T15:30:00Z"
    }
  },
  "overall": {
    "totalRuns": 20,
    "successRate": 0.95,
    "lastUpdated": "2024-01-21T15:30:00Z"
  }
}
```

## patterns.md 形式

```markdown
# 成功/失敗パターン

## 成功パターン

### Zodバリデーション標準化

- **状況**: フォームバリデーションが必要
- **アプローチ**: Zod + React Hook Form の組み合わせ
- **結果**: 型安全なバリデーションを実現
- **適用条件**: TypeScriptプロジェクトでフォームを扱う場合

### TDD先行コミット

- **状況**: 複雑なロジックの実装
- **アプローチ**: テストを先にコミットして仕様を固定
- **結果**: 仕様のブレを防止、レビューしやすい
- **適用条件**: 入出力が明確に定義できる関数

## 失敗パターン

### テスト後付け

- **状況**: 実装を先に書いてからテストを追加
- **問題**: テストがテストケースに過剰適合
- **原因**: 実装を知っているのでテストが甘くなる
- **教訓**: 必ずテストファーストを遵守

### DESIGN.md未更新

- **状況**: 実装完了後にDESIGN.mdを更新しなかった
- **問題**: 設計判断の理由が不明になった
- **原因**: feedbackスキップ
- **教訓**: 実装後は必ずdev:feedbackを実行
```

## 記録コマンド

### 成功時

```bash
# LOGS.md に追記
echo "### $(date +%H:%M) - dev:feedback

- **result**: success
- **phase**: {phase}
- **story**: {feature-slug}/{story-slug}
- **notes**: {notes}
" >> .claude/skills/dev/feedback/LOGS.md
```

### 失敗時

```bash
# LOGS.md に追記
echo "### $(date +%H:%M) - dev:feedback

- **result**: failure
- **phase**: {phase}
- **story**: {feature-slug}/{story-slug}
- **error**: {error_type}
- **notes**: {notes}
" >> .claude/skills/dev/feedback/LOGS.md
```

## 改善サイクル

```
実行 → LOGS.md記録 → EVALS.json更新
                ↓
        パターン分析 → patterns.md蓄積
                ↓
        自己改善提案 → スキル/ルール更新
```

### トリガー条件

- **定期**: 10回実行ごと
- **閾値**: エラー率が10%を超えた場合
- **手動**: `/dev:feedback --analyze` で明示的に実行
