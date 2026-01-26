# Base UIスキル作成計画

## 注意書き

この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

---

## 概要

Base UIをベストプラクティスに従って使用するためのClaude Codeスキルを作成する。Headless UIコンポーネントライブラリの特性を活かし、アクセシビリティ、スタイリング、コンポジションのガイダンスを提供するスキルを構築する。

---

## 背景

### Base UIとは

Base UIは、Radix、Floating UI、Material UIの開発者によって作成された、**スタイルなし（Headless）のReactコンポーネントライブラリ**。

**主な特徴**:
- **Headless設計**: デフォルトスタイルなし、完全なカスタマイズ自由度
- **アクセシビリティ重視**: WCAG 2.2準拠、ARIA Authoring Practices Guide準拠
- **構成可能性（Composable）**: 柔軟なコンポーネント組み合わせ

**統計情報**:
- GitHubスター: 8.2k
- 現行バージョン: v1.1.0（2025年12月にv1リリース）
- ライセンス: MIT

### なぜスキルが必要か

1. **Headless UIの学習曲線**: スタイルなしコンポーネントは自由度が高い反面、正しい使い方を知らないと品質が下がる
2. **アクセシビリティの担保**: ARIA属性、キーボード操作など、Base UIの機能を最大限活用するためのガイダンスが必要
3. **スタイリング統一**: Tailwind CSS、CSS Modules、CSS-in-JSなど複数のアプローチを一貫して適用するための指針が必要
4. **コンポジションパターン**: `render` prop、サブコンポーネント構成など、Base UI特有のパターンを効率的に習得させる

---

## 変更内容

### 作成するスキル構成

```
.claude/skills/base-ui/
  SKILL.md                          # 全体ワークフロー（指揮者）
  agents/
    component-selector.md           # コンポーネント選定エージェント
    implementation-guide.md         # 実装ガイドエージェント
    styling-assistant.md            # スタイリング支援エージェント
    accessibility-checker.md        # アクセシビリティ検証エージェント
  references/
    overview.md                     # Base UI概要・基本情報
    components/
      catalog.md                    # 全コンポーネント一覧
      patterns/
        dialog.md                   # Dialog実装パターン
        form.md                     # フォーム関連パターン
        select.md                   # Select実装パターン
        menu.md                     # Menu実装パターン
    styling/
      tailwind.md                   # Tailwind CSSでのスタイリング
      css-modules.md                # CSS Modulesでのスタイリング
      css-variables.md              # CSS変数の活用
      data-attributes.md            # data属性によるスタイリング
    accessibility/
      aria-guide.md                 # ARIA属性ガイド
      keyboard-navigation.md        # キーボードナビゲーション
      focus-management.md           # フォーカス管理
    composition/
      render-prop.md                # render propパターン
      subcomponents.md              # サブコンポーネント構成
      custom-components.md          # カスタムコンポーネント作成
    animation/
      css-transitions.md            # CSSトランジション
      motion-integration.md         # Motion（Framer Motion）連携
    examples/
      login-form.md                 # ログインフォーム実装例
      modal-dialog.md               # モーダルダイアログ実装例
      dropdown-menu.md              # ドロップダウンメニュー実装例
```

---

## 各ファイルの内容概要

### SKILL.md（全体ワークフロー）

```markdown
---
name: base-ui
description: |
    Base UIコンポーネントをベストプラクティスに従って実装するスキル。
    Headless UIの正しい使い方、アクセシビリティ対応、スタイリング統一を支援。

    Triggers: Base UI, ベースUI, headless component, アクセシブルなUI
---

# Base UI Implementation Guide

Base UIコンポーネントを使用したUI実装のワークフロー。

## Prerequisite

- React 18以上のプロジェクト
- `@base-ui/react` パッケージのインストール
- スタイリングソリューションの選定（Tailwind/CSS Modules/etc.）

## Workflow

### Phase 1: 要件分析・コンポーネント選定
- [ ] **Step 1**: 要件を分析し、適切なBase UIコンポーネントを選定
  - Agent: `component-selector`
  - Output: 選定コンポーネント一覧

### Phase 2: 実装
- [ ] **Step 2**: コンポーネント実装ガイダンス
  - Agent: `implementation-guide`
  - Input: 選定コンポーネント
  - Output: 実装コード

### Phase 3: スタイリング
- [ ] **Step 3**: スタイリング適用
  - Agent: `styling-assistant`
  - Input: 実装コード
  - Output: スタイル適用済みコード

### Phase 4: 品質検証
- [ ] **Step 4**: アクセシビリティ検証
  - Agent: `accessibility-checker`
  - Input: 完成コード
  - Output: 検証レポート・修正提案
```

### agents/component-selector.md

**責務**: ユーザーの要件に基づいて最適なBase UIコンポーネントを選定

**内容**:
- 45コンポーネントのカテゴリ分類を把握
- 要件→コンポーネントマッピング
- 代替案の提示

**参照リソース**:
- `references/components/catalog.md`

### agents/implementation-guide.md

**責務**: 選定されたコンポーネントの正しい実装パターンを提供

**内容**:
- サブコンポーネント構成の説明
- Portal設定、フォーカス管理の適用
- TypeScript型定義

**参照リソース**:
- `references/components/patterns/*.md`
- `references/composition/*.md`

### agents/styling-assistant.md

**責務**: プロジェクトのスタイリング方針に合わせたスタイル適用

**内容**:
- Tailwind/CSS Modules/CSS-in-JSの選択肢提示
- data属性、CSS変数の活用方法
- レスポンシブ・ダークモード対応

**参照リソース**:
- `references/styling/*.md`

### agents/accessibility-checker.md

**責務**: 実装されたUIのアクセシビリティ検証

**内容**:
- ARIA属性の確認
- キーボード操作の検証
- スクリーンリーダー対応チェック

**参照リソース**:
- `references/accessibility/*.md`

---

### references/ 詳細

#### references/overview.md

```markdown
# Base UI 概要

## 基本情報
- **パッケージ**: `@base-ui/react`
- **バージョン**: v1.1.0
- **ライセンス**: MIT

## インストール
\`\`\`bash
npm i @base-ui/react
\`\`\`

## 必須セットアップ

### Portal用isolation設定
\`\`\`tsx
// layout.tsx
<body>
  <div className="root">{children}</div>
</body>
\`\`\`

\`\`\`css
.root {
  isolation: isolate;
}
\`\`\`

### iOS 26+ Safari対応
\`\`\`css
body {
  position: relative;
}
\`\`\`

## 3つのコア特性
1. **Headless**: スタイルなし、完全カスタマイズ
2. **Accessible**: WCAG 2.2準拠
3. **Composable**: 柔軟な組み立て
```

#### references/components/catalog.md

全45コンポーネントの一覧とカテゴリ分類:

| カテゴリ | コンポーネント |
|----------|----------------|
| **インタラクティブ** | Accordion, Alert Dialog, Dialog, Menu, Menubar, Context Menu |
| **フォーム** | Field, Fieldset, Form, Input, Number Field, Checkbox, Radio, Select, Switch |
| **表示** | Avatar, Button, Meter, Progress, Tabs, Toggle |
| **ポップアップ** | Popover, Preview Card, Tooltip, Toast |
| **ナビゲーション** | Navigation Menu, Scroll Area |
| **その他** | Collapsible, Separator, Slider, Toolbar |

#### references/styling/tailwind.md

Tailwind CSSでのスタイリングパターン:

```tsx
<Dialog.Popup className="fixed inset-0 flex items-center justify-center">
  <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
    <Dialog.Title className="text-lg font-semibold text-gray-900">
      Title
    </Dialog.Title>
  </div>
</Dialog.Popup>
```

#### references/styling/data-attributes.md

data属性によるスタイリング:

```css
/* 状態に基づくスタイリング */
[data-checked] { /* チェック時 */ }
[data-unchecked] { /* 未チェック時 */ }
[data-open] { /* 開いている時 */ }
[data-closed] { /* 閉じている時 */ }
[data-disabled] { /* 無効時 */ }
```

#### references/composition/render-prop.md

render propパターン:

```tsx
// カスタムコンポーネントとの合成
<Dialog.Trigger render={<MyButton />}>
  Open Dialog
</Dialog.Trigger>

// 要素の変更
<Menu.Item render={<a href="/settings" />}>
  Settings
</Menu.Item>

// 状態に基づくスタイリング
<Switch.Thumb
  className={(state) => state.checked ? 'bg-blue-500' : 'bg-gray-300'}
/>
```

#### references/accessibility/aria-guide.md

ARIA属性の適切な使用:

- Dialog: `aria-labelledby`, `aria-describedby`
- Form: `aria-invalid`, `aria-errormessage`
- Menu: `role="menu"`, `role="menuitem"`

#### references/examples/login-form.md

完全なログインフォーム実装例:

```tsx
import { Field, Form } from '@base-ui/react';

function LoginForm() {
  return (
    <Form.Root>
      <Field.Root name="email">
        <Field.Label>Email</Field.Label>
        <Field.Control type="email" required />
        <Field.Error match="valueMissing">
          Please enter your email
        </Field.Error>
      </Field.Root>

      <Field.Root name="password">
        <Field.Label>Password</Field.Label>
        <Field.Control type="password" required minLength={8} />
        <Field.Error match="tooShort">
          Password must be at least 8 characters
        </Field.Error>
      </Field.Root>

      <button type="submit">Login</button>
    </Form.Root>
  );
}
```

---

## 影響範囲

- **新規作成**: `.claude/skills/base-ui/` ディレクトリ配下すべて
- **既存ファイル**: 変更なし

---

## 実装優先順位

### Priority 1: コア機能（必須）

| 優先度 | ファイル | 理由 |
|--------|----------|------|
| P1-1 | `SKILL.md` | スキルのエントリポイント |
| P1-2 | `references/overview.md` | 基本情報・セットアップ |
| P1-3 | `references/components/catalog.md` | コンポーネント一覧 |
| P1-4 | `agents/component-selector.md` | 最初のワークフローステップ |

### Priority 2: 実装支援（重要）

| 優先度 | ファイル | 理由 |
|--------|----------|------|
| P2-1 | `agents/implementation-guide.md` | 実装ガイダンス |
| P2-2 | `references/components/patterns/dialog.md` | 最も使用頻度の高いパターン |
| P2-3 | `references/components/patterns/form.md` | フォーム実装パターン |
| P2-4 | `references/composition/render-prop.md` | コア合成パターン |

### Priority 3: スタイリング

| 優先度 | ファイル | 理由 |
|--------|----------|------|
| P3-1 | `agents/styling-assistant.md` | スタイリング支援 |
| P3-2 | `references/styling/tailwind.md` | 最も一般的なスタイリング |
| P3-3 | `references/styling/data-attributes.md` | Base UI固有の手法 |
| P3-4 | `references/styling/css-modules.md` | 代替スタイリング |

### Priority 4: アクセシビリティ・品質

| 優先度 | ファイル | 理由 |
|--------|----------|------|
| P4-1 | `agents/accessibility-checker.md` | 品質検証 |
| P4-2 | `references/accessibility/aria-guide.md` | ARIA基本ガイド |
| P4-3 | `references/accessibility/keyboard-navigation.md` | キーボード操作 |

### Priority 5: 追加パターン・例

| 優先度 | ファイル | 理由 |
|--------|----------|------|
| P5-1 | `references/components/patterns/select.md` | Select実装 |
| P5-2 | `references/components/patterns/menu.md` | Menu実装 |
| P5-3 | `references/examples/login-form.md` | 実践例 |
| P5-4 | `references/animation/css-transitions.md` | アニメーション |

---

## タスクリスト

### Phase 1: 基盤構築

> メインスレッドで順次実行。スキルの骨格を作成。

- [ ] ディレクトリ構造作成
- [ ] SKILL.md作成
- [ ] references/overview.md作成
- [ ] references/components/catalog.md作成

### Phase 2: エージェント作成

> メインスレッドで順次実行。

- [ ] agents/component-selector.md作成
- [ ] agents/implementation-guide.md作成
- [ ] agents/styling-assistant.md作成
- [ ] agents/accessibility-checker.md作成

### Phase 3: リファレンス（コンポーネントパターン）

> 並列実行可能。独立したドキュメント作成。

- [ ] references/components/patterns/dialog.md作成 `[PARALLEL]`
- [ ] references/components/patterns/form.md作成 `[PARALLEL]`
- [ ] references/components/patterns/select.md作成 `[PARALLEL]`
- [ ] references/components/patterns/menu.md作成 `[PARALLEL]`

### Phase 4: リファレンス（スタイリング）

> 並列実行可能。

- [ ] references/styling/tailwind.md作成 `[PARALLEL]`
- [ ] references/styling/css-modules.md作成 `[PARALLEL]`
- [ ] references/styling/css-variables.md作成 `[PARALLEL]`
- [ ] references/styling/data-attributes.md作成 `[PARALLEL]`

### Phase 5: リファレンス（コンポジション・アクセシビリティ）

> 並列実行可能。

- [ ] references/composition/render-prop.md作成 `[PARALLEL]`
- [ ] references/composition/subcomponents.md作成 `[PARALLEL]`
- [ ] references/accessibility/aria-guide.md作成 `[PARALLEL]`
- [ ] references/accessibility/keyboard-navigation.md作成 `[PARALLEL]`
- [ ] references/accessibility/focus-management.md作成 `[PARALLEL]`

### Phase 6: リファレンス（アニメーション・例）

> 並列実行可能。

- [ ] references/animation/css-transitions.md作成 `[PARALLEL]`
- [ ] references/animation/motion-integration.md作成 `[PARALLEL]`
- [ ] references/examples/login-form.md作成 `[PARALLEL]`
- [ ] references/examples/modal-dialog.md作成 `[PARALLEL]`
- [ ] references/examples/dropdown-menu.md作成 `[PARALLEL]`

### Phase 7: 品質検証

> メインスレッドで検証。

- [ ] スキル構造の整合性確認
- [ ] エージェント間の参照パス確認
- [ ] SKILL.mdのワークフロー動作確認

---

## 技術的考慮事項

### Base UI v1.1.0の主要変更点

- パッケージ名が `@mui/base` から `@base-ui/react` に変更
- シンプルなパッケージ構造
- モダンなスタイリングパターン対応

### スタイリングソリューション対応

| ソリューション | 対応方針 |
|----------------|----------|
| Tailwind CSS | `className` propに直接適用 |
| CSS Modules | スコープ付きクラスをインポート |
| CSS-in-JS | styled関数でラップ |
| Plain CSS | data属性セレクタを活用 |

### コンポジションの注意点

1. **ref転送必須**: カスタムコンポーネントは必ず`forwardRef`を使用
2. **props展開必須**: 受け取ったpropsをすべて展開
3. **render propのパフォーマンス**: 頻繁に再レンダリングされる場合は関数形式を使用

---

## リスク・考慮事項

1. **Base UIのバージョンアップ**: v1.x系の更新に追従する必要あり
2. **スタイリングの多様性**: プロジェクトごとに異なるスタイリング方針への対応
3. **アニメーションライブラリ**: Motion以外のライブラリ（GSAP等）との連携は別途検討

---

## 参考資料

- [Base UI公式ドキュメント](https://base-ui.com/)
- [Base UI GitHubリポジトリ](https://github.com/mui/base-ui)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
