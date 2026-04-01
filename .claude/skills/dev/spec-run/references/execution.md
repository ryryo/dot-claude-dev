# 実行プロトコル（従来モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      仕様書の Todo に従って実装する
Step 2 — VERIFY    複雑さに応じてレビュワー 1体 or 3体を起動してレビューする
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 1 — IMPL

仕様書の Todo IMPL 内容に従って実装する。

- **[TDD] ラベルあり**: テストを先に書き、失敗を確認してから実装する（RED→GREEN→REFACTOR）。詳細は `roles/tdd-developer.md` を参照
- **ラベルなし**: 仕様に忠実に実装する。詳細は `roles/implementer.md` を参照

実装完了後、変更をコミットする。

## Step 2 — VERIFY

### 複雑さ判断

Claude が Todo の内容を以下の観点で総合判断し、レビューモードを決定する:

| 判断要素 | シンプル寄り | 複雑寄り |
|----------|------------|---------|
| 変更ファイル数 | 1-2ファイル | 3ファイル以上 |
| 影響範囲 | 局所的 | 複数モジュール横断 |
| リスク | 低（設定、ユーティリティ） | 高（認証、データ処理、API） |
| ロジック複雑度 | 単純な追加・変更 | 条件分岐・状態管理・非同期処理 |

**判断に迷ったら複雑モードを選択する。**

### シンプルモード — レビュワー 1体

`agents/reviewer-correctness.md` を Agent（sonnet）で起動する。
正確性・仕様適合の観点で全体をカバーする。

### 複雑モード — レビュワー 3体並列

以下の3ファイルを Read し、それぞれ Agent（sonnet）で **並列** 起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

各エージェントには仕様書パス + 対象 Review ID を渡す。

### 結果の統合

- すべて PASS → 全体 PASS
- 1体でも FAIL → 全体 FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY も同じモード（シンプル/複雑）で実行する

## Step 4 — UPDATE

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。
