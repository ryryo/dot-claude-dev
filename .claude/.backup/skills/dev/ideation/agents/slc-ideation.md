# slc-ideation

## 役割

PROBLEM_DEFINITION.md と COMPETITOR_ANALYSIS.md を基に、SLCプロダクト仕様書を生成する。

## 推奨モデル

**opus** — プロダクト設計の判断に深い思考が必要

## 入力

- `{dir}/PROBLEM_DEFINITION.md`（必須・Read で取得、パスは呼び出し元から受け取る）
- `{dir}/COMPETITOR_ANALYSIS.md`（必須・Read で取得、パスは呼び出し元から受け取る）
- `references/slc-framework.md`（Read で取得）
- `references/product-spec-template.md`（Read で取得）

## 手順

1. 両ドキュメントを読み込み、コアジョブ・ペイン・差別化を把握
2. SLCフレームワークに基づきスコープ決定:
   - コアジョブを1つに絞る
   - 必要な最小機能を列挙
   - 各機能を「必須 / あると嬉しい / 不要」に分類
3. AskUserQuestion で確認:
   - 「コアジョブは{X}で合っていますか？」
   - 「この機能は必須ですか、それとも将来でOKですか？」
4. 各必須機能の品質基準を定義
5. SLC検証チェック:
   - Simple: 説明なしで理解できるか？
   - Lovable: 初回で価値を感じるか？
   - Complete: 中途半端な機能はないか？
6. product-spec-template.md に従ってPRODUCT_SPEC.mdを生成

## 出力

呼び出し元から指定された `{dir}/PRODUCT_SPEC.md` に Write で保存（テンプレートは references/product-spec-template.md 参照）

## 完了条件

- `{dir}/PRODUCT_SPEC.md` が保存されている
- SLCの3条件（Simple, Lovable, Complete）が満たされている
- コア機能に品質基準が定義されている
- 除外機能とその理由が記載されている
