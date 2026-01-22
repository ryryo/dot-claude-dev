# TODO: スプレッドレイアウト (spread-layout)

## Story
ユーザーとして、3枚引きのカードが「過去 - 現在 - 未来」の位置に横並びで表示されてほしい。モバイルでも見やすいレイアウトで。

---

## Tasks

### T1: スプレッドレイアウトコンポーネントの構造定義
- [ ] [TDD][RED] ThreeCardSpreadProps型定義のテスト作成
- [ ] [TDD][GREEN] ThreeCardSpreadProps型定義の実装
- [ ] [TDD][REFACTOR] 型定義のリファクタリング
- [ ] [TDD][REVIEW] セルフレビュー（型定義の網羅性、拡張性）
- [ ] [TDD][CHECK] lint/format/build

### T5: 位置ラベル（過去・現在・未来）の実装
- [ ] [E2E][IMPL] 位置ラベルコンポーネント実装
- [ ] [E2E][AUTO] ラベル表示のagent-browser検証
- [ ] [E2E][CHECK] lint/format/build

### T2: デスクトップレイアウトのCSS実装
- [ ] [E2E][IMPL] デスクトップ（1024px以上）レイアウトCSS実装
- [ ] [E2E][AUTO] デスクトップレイアウトのagent-browser検証（1024px）
- [ ] [E2E][CHECK] lint/format/build

### T3: タブレットレイアウトのCSS実装
- [ ] [E2E][IMPL] タブレット（768px～1024px）レイアウトCSS実装
- [ ] [E2E][AUTO] タブレットレイアウトのagent-browser検証（768px）
- [ ] [E2E][CHECK] lint/format/build

### T4: モバイルレイアウトのCSS実装
- [ ] [E2E][IMPL] モバイル（375px～768px）レイアウトCSS実装
- [ ] [E2E][AUTO] モバイルレイアウトのagent-browser検証（375px）
- [ ] [E2E][CHECK] lint/format/build

### T6: アクセシビリティ対応
- [ ] [E2E][IMPL] aria属性、セマンティックHTML実装
- [ ] [E2E][AUTO] アクセシビリティのagent-browser検証（read_page with filter: "interactive"）
- [ ] [E2E][CHECK] lint/format/build

### T7: レスポンシブ検証（デスクトップ）
- [ ] [E2E][AUTO] デスクトップ全体検証（1024px、1920px）
- [ ] [E2E][CHECK] スクリーンショット確認、最終チェック

### T8: レスポンシブ検証（タブレット）
- [ ] [E2E][AUTO] タブレット全体検証（768px、1024px）
- [ ] [E2E][CHECK] スクリーンショット確認、最終チェック

### T9: レスポンシブ検証（モバイル）
- [ ] [E2E][AUTO] モバイル全体検証（375px、640px）
- [ ] [E2E][CHECK] スクリーンショット確認、最終チェック

### T10: アクセシビリティ検証
- [ ] [E2E][AUTO] 全画面サイズでのアクセシビリティ検証
- [ ] [E2E][CHECK] キーボードナビゲーション、aria属性の最終確認

---

## Notes
- **ブレイクポイント**: sm: 640px, md: 768px, lg: 1024px
- **検証順序**: デスクトップ → タブレット → モバイル
- **アクセシビリティ**: WCAG 2.1 AA準拠
- **CSS手法**: Flexbox/Grid + CSS変数 + モバイルファーストアプローチ
- **依存**: 既存のCardコンポーネント（Card.tsx）を使用
