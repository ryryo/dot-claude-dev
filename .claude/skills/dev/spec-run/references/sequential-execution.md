# 逐次実行プロトコル

Gate に `[PARALLEL]` タグがない場合、各 Todo を **順番に** 実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      SKILL.md パラメータテーブルに従い、ロール定義を Read して実装する
Step 2 — VERIFY    SKILL.md パラメータテーブルに従い、Agent で reviewer を実行する
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書の完了した Step のチェックボックスを [x] に更新する
```

## Step 1 — IMPL の詳細

1. Todo の [TDD] ラベルを確認する
2. SKILL.md パラメータテーブルから該当するロールを特定する:
   - `[TDD]` ラベルあり → `references/agents/tdd-developer.md` を Read
   - ラベルなし → `references/agents/implementer.md` を Read
3. ロール定義の手順に従って実装する(エージェントツールは立ち上げない。メインスレッドでそのまま作業。)
4. 実装完了後、変更をコミットする

## Step 2 — VERIFY の詳細

1. `agents/reviewer.md` を Read する
2. SKILL.md パラメータテーブルから model を確認する
3. Agent でレビューを実行し、結果を仕様書の記入欄に記載する

## Step 4 — UPDATE の詳細

各 Todo の全 Step 完了後、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`

これにより、仕様書を見るだけで各 Todo の進捗が把握できる。
