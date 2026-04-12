# Sample v2 Fixture

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

---

## 概要

v2 schema と sync-spec-md の参照 fixture。5 種の review 状態を網羅する。

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 準備
Gate B: 実装（Gate A 完了後）
```

### Gate A: 準備

> 基盤セットアップとスキーマ定義

- [ ] **A1**: スキーマ定義
  > **Review A1**: _未記入_
- [ ] **A2**: リポジトリ層
  > **Review A2**: ⏳ IN_PROGRESS

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: 実装

> API ハンドラとビジネスロジックの実装

- [x] **B1**: [TDD] API ハンドラ
  > **Review B1**: ✅ PASSED (FIX 2回) — バリデーション追加後 OK
- [x] **B2**: ドキュメント更新
  > **Review B2**: ⏭️ SKIPPED — docs only
- [ ] **B3**: エラーハンドリング
  > **Review B3**: ❌ FAILED — 500 エラー時のレスポンス形式が仕様と不一致

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
