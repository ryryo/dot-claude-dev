# Hook 実動作検証

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

---

## 概要

`sync-spec-md-hook.sh` が `/dev:spec-run` 実行中に tasks.json 編集時に正しく発火するかを検証する最小スペック。

**検証ポイント**:
1. tasks.json の Edit 時に PostToolUse hook が発火する
2. spec.md の generated 領域が自動更新される
3. hook エラーが spec-run フローをブロックしない

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: Hook 検証
```

### Gate A: Hook 検証

> PostToolUse hook が tasks.json 編集時に発火し spec.md を自動更新することを確認

- [x] **A1**: hook-verify.txt を新規作成
  > **Review A1**: ⏭️ SKIPPED — text file only — hook verified

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認
