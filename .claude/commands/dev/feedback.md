---
description: "実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案"
argument-hint: "[feature-slug/story-slug（任意）]"
---

# /dev:feedback - フィードバック → 仕様書蓄積コマンド

実装完了後、学んだことをDESIGN.mdに蓄積し、繰り返しパターンのスキル/ルール化を提案します。
dev:developing完了後、PR作成前に実行するコマンドです。

## 使い方

### 引数付き起動

```
/dev:feedback user-auth/login-form
```

### 引数なし起動

```
/dev:feedback
```
→ 現在のWorktreeから自動推定、または質問

---

## 実行フロー

```
[1] 変更内容の収集
    - git diff --stat
    - git log --oneline
    - 変更ファイルを分析
        ↓
[2] 学習事項の抽出（sonnet）
    - 設計判断とその理由
    - 技術的な発見
    - 注意点・ハマりどころ
        ↓
[3] DESIGN.md更新（opus）
    - 機能別DESIGN.mdに追記
    - 重要な判断は総合DESIGN.mdにも反映
        ↓
[4] パターン検出（haiku）
    - 繰り返しパターンを検出
    - ルール化/スキル化候補を特定
        ↓
[5] 改善提案（opus）
    - 提案を表示
    - ユーザー確認
        ↓
[6] スキル/ルール作成（オプション）
    - 承認されれば meta-skill-creator を呼び出し
```

---

## 入力

### $1（オプション）

`{feature-slug}/{story-slug}` 形式。

```
/dev:feedback user-auth/login-form
```

省略時は以下の順で推定:
1. Worktreeのブランチ名から推定
2. 直近のTODO.mdのパスから推定
3. ユーザーに質問

---

## 出力

### DESIGN.md更新

```markdown
## 更新履歴

### 2024-01-21: login-form

**設計判断**:
- JWTではなくセッションベース認証を採用（理由: サーバーサイドでの即時無効化が必要）
- バリデーションはZodを使用（理由: TypeScriptとの型連携が優れている）

**学んだこと**:
- React Hook FormとZodの連携ではzodResolverを使用
- useFormのmode: 'onBlur'でフィールドからフォーカスが外れた時点で検証

**注意点**:
- パスワードバリデーションは長さチェックを先に
```

### 改善提案（該当する場合）

```markdown
💡 改善提案を検出しました

## ルール化候補

### 1. Zodバリデーションパターン
- **出現回数**: 3回
- **保存先**: `.claude/rules/languages/typescript/validation.md`
- **効果**: コードの一貫性向上

## スキル化候補

### 1. 認証フロー実装
- **出現回数**: 2回
- **保存先**: `.claude/skills/dev/auth-setup/SKILL.md`
- **効果**: 実装時間の短縮
```

---

## ユーザー確認

```
これらのパターンをルール/スキルとして保存しますか？

[1] 保存する → meta-skill-creatorでルール/スキルを作成
[2] 今回はスキップ → 保存しない
[Other] 選択的に保存
```

---

## 次のアクション

| 選択 | 実行 |
|------|------|
| 保存する | meta-skill-creator を呼び出し |
| スキップ | PR作成へ進む |

---

## フィードバック記録

毎回実行後に記録:
- LOGS.md: 実行ログ
- EVALS.json: メトリクス

---

## 関連コマンド

- `/dev:story` - ストーリーからタスク生成
