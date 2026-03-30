# 実行プロトコル（従来モード）

各 Todo を順番に実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      仕様書の Todo に従って実装する
Step 2 — VERIFY    agents/ のレビュワー 3体を並列起動してレビューする
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書のチェックボックスを更新する
```

## Step 1 — IMPL

仕様書の Todo IMPL 内容に従って実装する。

- **[TDD] ラベルあり**: テストを先に書き、失敗を確認してから実装する（RED→GREEN→REFACTOR）。詳細は `roles/tdd-developer.md` を参照
- **ラベルなし**: 仕様に忠実に実装する。詳細は `roles/implementer.md` を参照

実装完了後、変更をコミットする。

## Step 2 — VERIFY の詳細（3体並列レビュー）

以下の3ファイルを Read し、それぞれ Agent（sonnet）で **並列** 起動する:

1. `agents/reviewer-quality.md` — 品質・設計
2. `agents/reviewer-correctness.md` — 正確性・仕様適合
3. `agents/reviewer-conventions.md` — プロジェクト慣例

各エージェントには仕様書パス + 対象 Review ID を渡す。

### 結果の統合

- 3体すべて PASS → 全体 PASS
- 1体でも FAIL → 全体 FAIL → Step 3（FIX）へ
- FIX 後の再 VERIFY も同じ3体並列で実行する

## Step 4 — UPDATE

各 Todo の全 Step 完了後、仕様書のチェックボックスを `[x]` に更新する。記録形式は SKILL.md「結果の記録」を参照。
