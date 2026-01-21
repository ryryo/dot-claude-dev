# Claude Code 開発手段 総合ガイド

このディレクトリには、Claude Code を活用した先進的な開発手法に関する包括的な資料、ツール、設定が集約されています。

## 📁 ディレクトリ構成

```
docs/SAMPLE/dev/
├── ドキュメント（ベストプラクティス・ガイド）
│   ├── Claude Code Best Practices.md
│   ├── Claude Codeで推奨される「テスト駆動ワークフロー」実践ガイド.md
│   ├── ストーリー駆動AI開発.md
│   ├── カムイウェビナー スキル開発フロー.md
│   └── Introducing advanced tool use on the Claude Developer Platform.md
├── cc-sdd/                          # 仕様駆動開発フレームワーク
└── dotfiles/                        # Claude Code カスタマイズ設定集
```

---

## 🎯 3つの主要コンポーネント

### 1. ドキュメント：開発哲学とベストプラクティス

Claude Code の効果的な活用方法を体系的にまとめた文書群です。

| ドキュメント | 概要 | 主なポイント |
|------------|------|------------|
| **Claude Code Best Practices** | Anthropic 公式のベストプラクティス集 | • `CLAUDE.md` の活用<br>• MCP 統合<br>• ツールの allowlist 設定<br>• チーム共有方法 |
| **テスト駆動ワークフロー実践ガイド** | AI時代に最適化された TDD アプローチ | • テストファースト（仕様固定）<br>• 2〜4周で収束する反復開発<br>• フロントエンド開発への適用範囲<br>• テスト資産の柔軟な管理 |
| **ストーリー駆動AI開発** | 認知負荷を下げる開発手法 | • ユーザーストーリーベースの開発<br>• 仕様書は「駆動」ではなく「保守」のため<br>• コンテキストの圧縮と整理 |
| **カムイウェビナー スキル開発フロー** | 実践的なスキル設計手法 | • トークン消費を半減（Big 3 スキル）<br>• 13フェーズのタスク分割<br>• フィードバックループの重要性<br>• レポート出力による品質管理 |
| **Advanced Tool Use** | Claude Developer Platform の高度な機能 | • Tool use の実装パターン<br>• エラーハンドリング<br>• パフォーマンス最適化 |

#### 重要な開発哲学

**🔄 開発フローの基本原則**
1. **テストファースト**: テストを先に書いて仕様を固定 → 実装 → 検証
2. **ストーリー駆動**: 小さなユーザーストーリー単位で開発 → 仕様書に集約
3. **再現性重視**: 誰が実行しても同じ品質が得られる仕組み作り

---

### 2. cc-sdd：仕様駆動開発フレームワーク

**Spec-Driven Development for Claude Code and other AI Agents**

Kiro IDE の仕様駆動開発プロセスを Claude Code で完全再現したフレームワークです。

#### 🚀 特徴

- ✅ **仕様ファースト保証**: 要件・設計を先に承認 → AIが正確に実装
- ✅ **並列実行対応**: タスク分解と依存関係管理で並行開発可能
- ✅ **チーム統一テンプレート**: カスタマイズ一度で全員が同じ形式
- ✅ **プロジェクトメモリ**: アーキテクチャ、パターン、標準をセッション跨ぎで記憶
- ✅ **7つのAIエージェント対応**: Claude, Cursor, Gemini, Codex, Copilot, Qwen, Windsurf
- ✅ **時間単位での開発**: 週単位が時間単位に短縮

#### 📋 開発フロー

```
/kiro:spec-init <what-to-build>
    ↓
/kiro:spec-requirements <spec-name>
    ↓
/kiro:spec-design <spec-name>
    ↓
/kiro:spec-tasks <spec-name>
    ↓
/kiro:spec-impl <spec-name>
```

**生成される成果物**
- `requirements.md` - EARS形式の要件定義
- `design.md` - Mermaidダイアグラム付きアーキテクチャ設計
- `tasks.md` - 依存関係付き実装タスク分解

#### 🎨 カスタマイズ

`.kiro/settings/` でチーム固有のワークフローに適応：
- **templates/** - ドキュメント構造定義
- **rules/** - AI生成原則と判断基準

#### 📦 インストール

```bash
# Claude Code (コマンド形式)
npx cc-sdd@latest --claude --lang ja

# Claude Code (サブエージェント形式)
npx cc-sdd@latest --claude-agent --lang ja
```

#### 📚 詳細ドキュメント

- [コマンドリファレンス](./cc-sdd/docs/guides/command-reference.md)
- [カスタマイズガイド](./cc-sdd/docs/guides/customization-guide.md)
- [仕様駆動開発ガイド](./cc-sdd/docs/guides/spec-driven.md)
- [Claudeサブエージェント](./cc-sdd/docs/guides/claude-subagents.md)

---

### 3. dotfiles：Claude Code カスタマイズ設定集

プロダクト開発全体をカバーする包括的な設定とスキル集です。

#### 📦 構成要素

```
dotfiles/claude/
├── commands/          # 7つのカスタムコマンド
├── agents/            # 2つの専用エージェント
├── skills/            # 17のプロダクト開発スキル
├── rules/             # 開発ルール（コア + バックエンド別）
├── hooks/             # TypeScript製フック（format, notify）
└── settings.json      # Claude Code 設定
```

#### 🔧 Commands（カスタムコマンド）

| コマンド | 説明 | 機能 |
|---------|------|------|
| `/ask` | 対話的要件ヒアリング | ユーザーニーズを深掘り |
| `/commit-push` | Git コミット＆プッシュ | Conventional Commits + emoji |
| `/create-skill` | スキル作成支援 | SKILL.md テンプレート生成 |
| `/impl` | TDD実装 | RED→GREEN→REFACTOR サイクル |
| `/interview` | インタビュー形式要件定義 | 対話形式で仕様を固める |
| `/review` | コードレビュー | 6フェーズの体系的レビュー |
| `/spec` | 対話的計画作成 | DESIGN.md + TODO.md 生成 |

#### 🤖 Agents（専用エージェント）

| エージェント | 用途 | 特徴 |
|------------|------|------|
| **commit-pusher** | 自動コミット＆プッシュ | pre-commit チェック、変更分割 |
| **fix-lsp-warnings** | LSP警告修正 | 警告検出→修正→再検証ループ |

#### 🎓 Skills（プロダクト開発スキル）

**アイデア・企画フェーズ**
```
problem-definition → competitor-analysis → slc-ideation
```

| スキル | 目的 | 出力 |
|-------|------|------|
| problem-definition | JTBD＋ペイン・ゲイン分析 | PROBLEM_DEFINITION.md |
| competitor-analysis | 競合分析と差別化 | COMPETITOR_ANALYSIS.md |
| slc-ideation | SLCフレームワークでアイデア壁打ち | PRODUCT_SPEC.md |

**要件・設計フェーズ**
```
user-story → ui-sketch → usecase-description → feasibility-check → ddd-modeling → analyzing-requirements
```

| スキル | 目的 | 出力 |
|-------|------|------|
| user-story | ユーザーストーリー＋優先順位付け | USER_STORIES.md |
| ui-sketch | 画面構成＋ワイヤーフレーム | UI_SKETCH.md |
| usecase-description | ユースケース詳細化 | USECASES.md |
| feasibility-check | 技術リスク評価＋PoC計画 | FEASIBILITY.md |
| ddd-modeling | ドメインモデリング | GLOSSARY.md, MODEL.md |
| analyzing-requirements | 技術設計書作成 | DESIGN.md |

**実装フェーズ**
```
planning-tasks → developing → writing-tests
```

| スキル | 目的 | 出力 |
|-------|------|------|
| planning-tasks | TODO.md作成 | TODO.md |
| developing | TDD実装 | コード |
| writing-tests | テスト作成 | テストファイル |

**ユーティリティ**

| スキル | 用途 |
|-------|------|
| creating-rules | .claude/rules/ にルールファイル作成 |
| reviewing-skills | スキルをベストプラクティスでレビュー |
| fix-lsp-warnings | LSP警告の検出・修正 |

#### 📏 Rules（開発ルール）

**Core Rules**
- `testing.md` - テスト戦略とカバレッジ基準
- `tdd.md` - TDDサイクルの実践方法
- `design.md` - アーキテクチャ設計原則
- `commit.md` - コミットメッセージ規約

**Backend Rules**
- `backend/go/` - Go言語固有のルール（testing, coding, design）
- `backend/rust/` - Rust言語固有のルール（testing, coding, design）

#### 🪝 Hooks（TypeScript製）

- `format.ts` - コード整形の自動実行
- `notify.ts` - 重要イベントの通知
- `types.ts` - Hook の型定義

#### 💾 インストール

```bash
cd dotfiles/claude
./install.sh
```

設定が `~/.config/claude/` にシンボリックリンクされます。

---

## 🎯 推奨される活用パターン

### パターン1: ゼロから新規プロダクト開発

```bash
# 1. cc-sdd で仕様作成
/kiro:spec-init ユーザー向けタスク管理アプリ
/kiro:spec-requirements task-app-ja
/kiro:spec-design task-app-ja -y
/kiro:spec-tasks task-app-ja -y

# 2. dotfiles スキルで要件深掘り（必要に応じて）
/problem-definition
/competitor-analysis
/user-story

# 3. dotfiles コマンドで実装
/impl
/review
/commit-push
```

### パターン2: 既存プロダクトへの機能追加

```bash
# 1. dotfiles スキルで要件整理
/user-story
/ui-sketch
/usecase-description

# 2. cc-sdd で設計・タスク分解
/kiro:steering          # 既存コードの理解
/kiro:spec-design new-feature-ja
/kiro:spec-tasks new-feature-ja

# 3. 実装
/impl
```

### パターン3: テスト駆動での品質重視開発

```bash
# テスト駆動ワークフローガイドに従う
1. /writing-tests        # テストだけ書く（実装は書かない）
2. テストレビュー → コミット
3. /developing           # テスト通るまで実装反復
4. 過剰適合チェック → 実装コミット
```

### パターン4: ストーリー駆動でのアジャイル開発

```bash
# ストーリー駆動AI開発の原則に従う
1. /user-story           # 小さなストーリー単位で作成
2. ストーリーごとに開発 (/impl)
3. 完了後、仕様書に統合 (/spec)
```

---

## 🔄 開発フロー統合図

```
┌─────────────────────────────────────────────────────────────────┐
│                        企画・発見フェーズ                        │
├─────────────────────────────────────────────────────────────────┤
│ [dotfiles skills]                                               │
│   problem-definition → competitor-analysis → slc-ideation       │
│                                 ↓                               │
├─────────────────────────────────────────────────────────────────┤
│                        要件・設計フェーズ                        │
├─────────────────────────────────────────────────────────────────┤
│ [dotfiles skills]                                               │
│   user-story → ui-sketch → usecase-description                  │
│             ↓                                                   │
│   feasibility-check → ddd-modeling → analyzing-requirements     │
│                                 ↓                               │
│ [cc-sdd]                                                        │
│   /kiro:spec-init → spec-requirements → spec-design → spec-tasks│
│                                 ↓                               │
├─────────────────────────────────────────────────────────────────┤
│                        実装・テストフェーズ                      │
├─────────────────────────────────────────────────────────────────┤
│ [dotfiles commands + skills]                                    │
│   /spec (planning-tasks) → /impl (developing + writing-tests)   │
│                                 ↓                               │
│   テスト駆動ワークフロー:                                        │
│     1. テストだけ書く → テストコミット                           │
│     2. テスト固定のまま実装反復（2〜4周）                        │
│     3. 過剰適合チェック → 実装コミット                           │
│                                 ↓                               │
├─────────────────────────────────────────────────────────────────┤
│                        レビュー・デプロイフェーズ                │
├─────────────────────────────────────────────────────────────────┤
│ [dotfiles commands + agents]                                    │
│   /review → fix-lsp-warnings → /commit-push                     │
│                                 ↓                               │
│ [cc-sdd]                                                        │
│   /kiro:spec-impl → Pull Request                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 学習ロードマップ

### ステップ1: 基礎理解（1-2日）

1. **ドキュメントを読む**
   - Claude Code Best Practices（全体像把握）
   - テスト駆動ワークフローガイド（開発手法理解）
   - ストーリー駆動AI開発（哲学理解）

2. **簡単なプロジェクトで試す**
   ```bash
   # cc-sdd のクイックスタート
   npx cc-sdd@latest --claude --lang ja
   /kiro:spec-init TODOアプリ
   ```

### ステップ2: 実践導入（1週間）

1. **dotfiles をインストール**
   ```bash
   cd dotfiles/claude && ./install.sh
   ```

2. **プロジェクトに CLAUDE.md を作成**
   - `/init` コマンドで自動生成
   - プロジェクト固有の情報を追記

3. **スキルを1つずつ試す**
   - `/problem-definition` でアイデア検証
   - `/user-story` で要件整理
   - `/impl` でTDD実装

### ステップ3: チーム展開（2-4週間）

1. **カスタマイズ**
   - cc-sdd のテンプレートをチーム仕様に調整
   - dotfiles の rules をプロジェクトに合わせて拡張

2. **フィードバックループ確立**
   - カムイウェビナーの「13フェーズ＋レポート」パターン導入
   - システム仕様書の継続的更新

3. **ベストプラクティス共有**
   - チーム内で CLAUDE.md を共有
   - 有効なスキル・コマンドをドキュメント化

---

## 🔑 重要な設計思想

### トークン効率化
- **Big 3 スキル戦略**: 200個 → 3個に集約（トークン消費半減）
- **タスク分割**: 8万文字の巨大プロンプト → 13フェーズに分割
- **MCP オフ推奨**: 不要なメタ情報の読み込みを回避

### 再現性の追求
- **フォーマット強制**: スキルクリエイターによる型チェック
- **レポート出力**: 各フェーズでレポート生成＝品質管理ポイント
- **フィードバックループ**: システム仕様書への知見還元

### 認知負荷の低減
- **ストーリー駆動**: 小さな単位で焦点を絞る
- **仕様書は保守用**: 開発駆動ではなくコンテキスト圧縮用
- **フェーズごとの脳リフレッシュ**: コンテキスト圧迫を防ぐ

### 柔軟性の確保
- **テスト資産の選別**: 長期価値があるもののみ保持
- **スキルの選択的利用**: 必要なスキルだけ使う（全部使う必要なし）
- **複数エージェント対応**: Claude以外でも同じフローを実現

---

## 📚 参考リンク

### 公式ドキュメント
- [Claude Code 公式サイト](https://claude.ai/code)
- [Anthropic Engineering Blog - Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [cc-sdd NPM Package](https://www.npmjs.com/package/cc-sdd)

### 関連記事・プレゼンテーション
- [KiroのSDD プロセスをClaude Codeで徹底的に再現した](https://zenn.dev/gotalab/articles/3db0621ce3d6d2) - Zenn
- [Claude Codeは仕様駆動の夢を見ない](https://speakerdeck.com/gotalab555/claude-codehashi-yang-qu-dong-nomeng-wojian-nai) - Speaker Deck

### 外部リソース
- [Kiro IDE](https://kiro.dev)
- [Kiro's Spec Methodology](https://kiro.dev/docs/specs/)
- [AI-Assisted SDD Book](https://www.amazon.com/dp/B0CW19YX9R) - Amazon

---

## 🤝 コントリビューション

これらの資料は継続的に改善されています。

- **フィードバック**: 実践での学びや改善提案を歓迎
- **カスタマイズ共有**: チーム固有の有効なカスタマイズを共有
- **新スキル追加**: プロダクト開発フローに有効なスキルの提案

---

## 📝 ライセンス

- **cc-sdd**: MIT License
- **dotfiles**: MIT License
- **ドキュメント**: 各ソースのライセンスに準拠

---

## 🎉 まとめ

このディレクトリは、Claude Code を使った **AI時代のソフトウェア開発** の集大成です。

- **仕様駆動（cc-sdd）** で再現性と品質を担保
- **テスト駆動（dotfiles/TDD）** でAI実装の信頼性を確保
- **ストーリー駆動（開発哲学）** で認知負荷を下げながらアジャイルに開発

これらを組み合わせることで、**「誰が実行しても高品質で同じ成果物が出る」** 開発体制を構築できます。

まずは小さく始めて、チームやプロジェクトに合わせてカスタマイズしていくことをお勧めします。
