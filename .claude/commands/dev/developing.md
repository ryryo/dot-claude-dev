---
description: "TODO.mdのタスクを実行。TDD/E2E/TASKラベルに応じたワークフローで実装"
argument-hint: "[feature-slug/story-slug（任意）]"
---

# /dev:developing - タスク実装コマンド

TODO.mdのタスクを実行します。TDD/E2E/TASKラベルに応じて適切なワークフローを適用します。

## 使い方

### 引数付き起動

```
/dev:developing auth/login
```

### 引数なし起動（カレントディレクトリのTODO.mdを検索）

```
/dev:developing
```

---

## 実行フロー

```
[1] TODO.md検索
    - $1 があれば docs/features/$1/TODO.md を参照
    - なければカレントディレクトリから検索
        ↓
[2] 次のタスク選択
    - 未完了タスクの中から次のタスクを特定
    - ラベル（TDD/E2E/TASK）を確認
        ↓
[3] ワークフロー実行
    - [TASK] → EXEC→VERIFY→COMMIT
    - [TDD] → RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT
    - [E2E] → IMPL→AUTO→CHECK→COMMIT
        ↓
[4] TODO.md更新
    - 完了したタスクにチェックマークを付ける
        ↓
[5] 次のタスク確認
    - 未完了タスクがあれば継続するか確認
    - すべて完了なら終了
```

---

## 入力

### $1（オプション）

feature-slug/story-slug。省略時はカレントディレクトリから検索。

```
/dev:developing auth/login
```

### TODO.md

```markdown
# TODO

## フェーズ1: バリデーション

### TASKタスク
- [ ] [TASK][EXEC] TypeScript環境構築
- [ ] [TASK][VERIFY] ビルド確認

### TDDタスク
- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング
- [ ] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build

### E2Eタスク
- [ ] [E2E][IMPL] LoginForm UIコンポーネント
- [ ] [E2E][AUTO] agent-browser検証
- [ ] [E2E][CHECK] lint/format/build
```

---

## ワークフロー詳細

### TASKワークフロー

```
[1/3] EXEC - タスク実行
    → 設定ファイル作成、コマンド実行
        ↓
[2/3] VERIFY - 検証
    → ファイル存在確認、ビルド確認
        ↓
[3/3] COMMIT
```

### TDDワークフロー

```
[1/6] RED - テスト作成
    → テスト実行して失敗を確認
    → コミット（テストのみ）
        ↓
[2/6] GREEN - 実装
    → テスト実行して成功を確認
    → テストは絶対に変更しない
        ↓
[3/6] REFACTOR - リファクタリング
    → テスト実行して成功を確認
        ↓
[4/6] REVIEW - セルフレビュー
    → 過剰適合・抜け道チェック
    → 問題あればGREENに戻る
        ↓
[5/6] CHECK - 品質チェック
    → lint/format/build
        ↓
[6/6] COMMIT
```

### E2Eワークフロー

```
[1/4] IMPL - UI実装
    → コンポーネント作成
        ↓
[2/4] AUTO - agent-browser検証（ループ）
    → 操作フロー検証
    → 問題あれば修正→再検証
        ↓
[3/4] CHECK - 品質チェック
    → lint/format/build
        ↓
[4/4] COMMIT
```

---

## 出力

- 実装コード
- テストコード（TDDタスク）
- Gitコミット
- 更新されたTODO.md

---

## 次のアクション

| 状況 | 実行 |
|------|------|
| 未完了タスクあり | 継続するか確認 |
| すべて完了 | `/dev:feedback` でフィードバック |

---

## 関連コマンド

- `/dev:story` - タスクリスト生成
- `/dev:feedback` - 実装後のフィードバック
