---
description: "ストーリーからTDD/PLAN分岐付きタスクリスト（TODO.md）を生成"
argument-hint: "[ストーリー説明（任意）]"
---

# /dev:story - ストーリー → タスク生成コマンド

ユーザーストーリーからTDD/PLAN分岐付きタスクリスト（TODO.md）を生成します。
Worktree作成後、最初に実行するコマンドです。

## 使い方

### 引数付き起動

```
/dev:story ログインフォームを作成する。メールアドレスとパスワードでログインできるようにする
```

### 引数なし起動（対話的）

```
/dev:story
```

### USER_STORIES.mdからの読み込み

```
/dev:story
```
→ docs/USER_STORIES.md が存在すれば自動で読み込み

---

## 実行フロー

```
[1] ストーリー取得
    - $1 があればそのまま使用
    - なければ USER_STORIES.md を確認
    - それもなければユーザーに質問
        ↓
[2] ストーリー分析（opus）
    - 目的・スコープ・受入条件を抽出
    - slug候補を生成
        ↓
[3] slug確定（AskUserQuestion）
    - feature-slug候補を提示
    - story-slug候補を提示
    - ユーザーが選択または入力
        ↓
[4] タスク分解（sonnet）
    - ストーリーをタスクに分解
    - 依存関係を特定
        ↓
[5] TDD/PLAN分類（haiku）
    - 各タスクにラベルを付与
    - TODO.mdを生成
        ↓
[6] ユーザー確認
    - TODO.mdを表示
    - 実装開始 or 修正
```

---

## 入力

### $1（オプション）

ストーリー説明。省略時は対話的に取得。

```
/dev:story ユーザーがメールアドレスとパスワードでログインできるようにする
```

### USER_STORIES.md（オプション）

```markdown
# ユーザーストーリー

## ログインフォーム

ユーザーとして、
メールアドレスとパスワードでログインできるようにしたい。
それによって、自分のアカウントにアクセスできる。

### 受入条件

- 有効なメールアドレス形式のみ受け付ける
- パスワードは8文字以上
- ログイン成功時はダッシュボードにリダイレクト
```

---

## 出力

### story-analysis.json

```json
{
  "story": { "title": "...", "description": "..." },
  "goal": "...",
  "scope": { "included": [...], "excluded": [...] },
  "acceptanceCriteria": [...],
  "slugCandidates": { "feature": [...], "story": [...] }
}
```

### task-list.json

```json
{
  "phases": [
    {
      "name": "フェーズ1: バリデーション",
      "tasks": [...]
    }
  ]
}
```

### TODO.md

```markdown
# TODO

## フェーズ1: バリデーション

### TDDタスク
- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング

### PLANタスク
- [ ] [PLAN][IMPL] LoginForm UIコンポーネント
- [ ] [PLAN][AUTO] agent-browser検証

### 共通
- [ ] [CHECK] lint/format/build
```

---

## 次のアクション

| 選択 | 実行 |
|------|------|
| 実装開始 | dev:developing を呼び出し |
| 修正が必要 | TODO.mdを調整後、再確認 |

---

## 関連コマンド

- `/dev:feedback` - 実装後のフィードバック
