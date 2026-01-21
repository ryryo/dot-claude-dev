# detect-patterns

## 役割

実装履歴から繰り返しパターンを検出する。

## 推奨モデル

**haiku** - パターン検出は単純なタスク

## 入力

- DESIGN.mdの履歴
- 実装コード
- git log

## 出力

```json
{
  "patterns": [
    {
      "id": "pattern-1",
      "name": "Zodバリデーションパターン",
      "type": "rule",
      "occurrences": 3,
      "locations": [
        "src/auth/validate.ts",
        "src/user/validate.ts",
        "src/form/validate.ts"
      ],
      "description": "Zodを使用したフォームバリデーションの共通パターン",
      "suggestedPath": ".claude/rules/languages/typescript/validation.md"
    },
    {
      "id": "pattern-2",
      "name": "認証フロー実装",
      "type": "skill",
      "occurrences": 2,
      "locations": [
        "login-form story",
        "signup-form story"
      ],
      "description": "認証関連UIの実装手順",
      "suggestedPath": ".claude/skills/dev/auth-setup/SKILL.md"
    }
  ],
  "metadata": {
    "analyzedCommits": 10,
    "analyzedFiles": 25,
    "totalPatterns": 2
  }
}
```

## プロンプト

```
実装履歴から繰り返しパターンを検出してください。

## DESIGN.md履歴
{design_history}

## 最近の変更
{recent_changes}

## 検出基準

1. **ルール化候補**
   - 3回以上使用したコーディングパターン
   - 共通の命名規則
   - 繰り返し出現する設計判断

2. **スキル化候補**
   - 2回以上実行した同じ手順
   - 複数ステップからなる実装フロー
   - 再利用可能なワークフロー

## パターン情報

各パターンに以下を含める:
- id: 一意の識別子
- name: パターン名
- type: "rule" または "skill"
- occurrences: 出現回数
- locations: 出現場所
- description: 説明
- suggestedPath: 保存先のパス提案

## 出力形式

JSON形式で出力してください。
```

## 注意事項

- 3回以上の出現をルール化候補
- 2回以上の手順をスキル化候補
- 保存先パスは規約に従う
