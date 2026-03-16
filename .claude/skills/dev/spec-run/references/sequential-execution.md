# 逐次実行プロトコル

Gate に `[PARALLEL]` タグがない場合、各 Todo を **順番に** 実行する。ステップを飛ばしてはならない。

## 実行ステップ

```
Step 0 — CONTEXT   仕様書の「参照すべきファイル」を全て Read する（最初の Todo 着手前に1回だけ）
Step 1 — IMPL      実装を行う
Step 2 — REVIEW    Agent(model: sonnet) で agents/reviewer.md を実行し、結果を仕様書の記入欄に貼り付ける
Step 3 — FIX       FAIL がある場合のみ修正（最大3ラウンド）。全 PASS なら不要
Step 4 — UPDATE    仕様書の完了した Step のチェックボックスを [x] に更新する
```

## Step 4 — UPDATE の詳細

各 Todo の全 Step 完了後、仕様書を Edit で更新する:

- `- [ ] **Step 1 — IMPL**` → `- [x] **Step 1 — IMPL**`
- `- [ ] **Step 2 — Review {ID}**` → `- [x] **Step 2 — Review {ID}** ✅ PASSED`

これにより、仕様書を見るだけで各 Todo の進捗が把握できる。

