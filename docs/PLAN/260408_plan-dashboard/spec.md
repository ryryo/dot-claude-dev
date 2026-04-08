# PLAN ダッシュボード — プロジェクト横断 PLAN 管理 UI

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モードを選択済みであること。

---

## 概要

dot-claude-dev リポジトリの `dashboard/` ディレクトリに Next.js アプリを構築し、ローカルの複数プロジェクトの `docs/PLAN/` にある仕様書を看板的に一覧表示するダッシュボードを提供する。

## 背景

dev:spec で作成した仕様書が複数プロジェクトに散在しており、全体の進捗を横断的に把握する手段がない。sync-skills と同様にプロジェクト一覧を管理し、各プロジェクトの PLAN ファイルを集約して表示することで、プロジェクト横断の進捗管理を実現する。

参考: ブログ記事「プロジェクト専用ダッシュボードを自作しようと思う」（`/Users/ryryo/dev/ablog/src/content/posts/260408-260408-14-59-v1.mdx`）での企画検討。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|---------|------|------|
| 1 | アプリ配置 | `dashboard/` ディレクトリに独立した Next.js プロジェクト | 既存の skill/rule 構造と分離。vitest 等との競合を回避 |
| 2 | UI ライブラリ | shadcn/ui + ai-elements（npx でインストール） | ai-elements は将来の AI チャット UI にも対応。shadcn/ui がベース |
| 3 | データ取得 | next dev でリアルタイム。API route から fs.readFile | ローカル開発サーバーとして使用。最もシンプル |
| 4 | プロジェクト管理 | `dashboard/projects.yaml` で対象プロジェクトを管理 | sync-skills と同様のアプローチ。手動で追加・削除 |
| 5 | ステータス判定 | PLAN ファイル内のチェックボックスから 4 ステータスを自動判定 | 既存のマークダウン形式を活用。追加マーカー不要 |
| 6 | 看板 UI | 4 カラム表示。D&D なし | ステータスはマークダウンのチェックボックスが真のソース。UI からの変更は不要 |
| 7 | スコープ外 | AI チャット UI、テンプレートコピー、D&D | 将来的に追加可能だが今回は対象外 |

## アーキテクチャ詳細

### ステータス判定ロジック

PLAN ファイル内の全チェックボックス（`- [ ]` / `- [x]`）を集計し、ファイルレベルのステータスを判定:

```
全チェックボックスを集計
  │
  ├── チェックボックスなし → 未実装
  ├── すべて [x] → 完了
  ├── [x] と [ ] が混在 → 実装中
  │     └── ただし未チェック Todo に Review 記入あり → レビュー待ち
  └── すべて [ ] → 未実装
```

判定優先順位: 完了 > レビュー待ち > 実装中 > 未実装

Review 記入の判定: `> **Review` で始まる blockquote の直後の行が空でなければ記入済み。

### PLANファイルから抽出する情報

```typescript
interface PlanFile {
  // ファイル情報
  filePath: string;        // 絶対パス
  fileName: string;        // ファイル名（例: 260408_plan-dashboard.md）
  projectName: string;     // プロジェクト名（projects.yaml の name）

  // パース結果
  title: string;           // マークダウンの H1
  status: PlanStatus;      // 4ステータス
  gates: Gate[];           // Gate 構造（あれば）
  todos: TodoItem[];       // 全 Todo
  progress: {              // 進捗率
    total: number;
    completed: number;
    percentage: number;
  };
}

type PlanStatus = 'not-started' | 'in-progress' | 'in-review' | 'completed';

interface Gate {
  id: string;
  title: string;
  todos: TodoItem[];
}

interface TodoItem {
  title: string;
  checked: boolean;
  hasReview: boolean;      // Review blockquote の有無
  reviewFilled: boolean;   // Review 内容が記入済みか
}
```

### projects.yaml の構造

```yaml
projects:
  - name: meurai-editer
    path: /Users/ryryo/dev/meurai-editer
  - name: base-ui-design
    path: /Users/ryryo/dev/base-ui-design
  - name: kamui-ryryo
    path: /Users/ryryo/dev/kamui-ryryo
  - name: goosely-editor
    path: /Users/ryryo/dev/goosely-editor
  - name: dot-claude-dev
    path: /Users/ryryo/dev/dot-claude-dev
```

### ディレクトリ構造

```
dashboard/
├── app/
│   ├── layout.tsx          # ルートレイアウト
│   ├── page.tsx            # ダッシュボードページ
│   └── api/
│       └── plans/
│           └── route.ts    # PLAN データ API
├── components/
│   ├── dashboard-layout.tsx   # サイドバー + メイン
│   ├── project-filter.tsx     # プロジェクトチェックボックス
│   ├── kanban-board.tsx       # 4カラム看板
│   ├── plan-card.tsx          # PLAN カード
│   └── plan-detail.tsx        # 展開時の詳細
├── lib/
│   ├── types.ts               # 型定義
│   ├── plan-parser.ts         # PLAN マークダウンパーサー
│   ├── project-scanner.ts     # プロジェクトスキャナー
│   └── config.ts              # YAML 読み込み
├── __tests__/
│   ├── plan-parser.test.ts    # パーサーテスト
│   └── project-scanner.test.ts # スキャナーテスト
├── projects.yaml              # プロジェクト設定
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### データフロー

```
[projects.yaml] → config.ts → project-scanner.ts → plan-parser.ts
                                     │                    │
                                     ▼                    ▼
                              PLANファイル一覧      PlanFile[]（パース済み）
                                                         │
                                                         ▼
                                               /api/plans (route.ts)
                                                         │
                                                         ▼
                                               page.tsx (useSWR/fetch)
                                                         │
                                    ┌────────────────────┼───────────────┐
                                    ▼                    ▼               ▼
                            project-filter    kanban-board        plan-detail
                            (チェックボックス)  (4カラム)         (展開表示)
```

## 変更対象ファイルと影響範囲

### 新規作成ファイル

| ファイル | 内容 |
|---------|------|
| `dashboard/` 以下すべて | Next.js アプリ全体（上記ディレクトリ構造参照） |

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|---------|---------|------|
| `.gitignore` | `dashboard/.next/`, `dashboard/node_modules/` 追加 | なし |
| `package.json`（ルート） | `dashboard:dev` スクリプト追加 | なし |

### 変更しないファイル

| ファイル | 理由 |
|---------|------|
| `.claude/skills/` 配下 | ダッシュボードは skill とは独立 |
| `docs/PLAN/` の既存ファイル | 読み取り専用。パース対象だが変更しない |

## 参照すべきファイル

### コードベース内

| ファイル | 目的 |
|---------|------|
| `.claude/skills/sync-skills/SKILL.md` | プロジェクト同期の参考パターン |
| `docs/PLAN/260402_dqa-screenshot-before-script.md` | Gate/Todo/Review 構造の実例 |
| `.gitmodules` | 既存サブモジュール構成の確認 |

## タスクリスト

> **実装詳細は `tasks.json` を参照。** このセクションは進捗管理と Review 記録用。

### 依存関係図

```
Gate A: プロジェクトセットアップ
├── Todo A1: Next.js 初期化 + UI ライブラリセットアップ
└── Todo A2: .gitignore + npm scripts 更新（A1 に依存）

Gate B: データ層（Gate A 完了後）
├── Todo B1: projects.yaml 設定 + 型定義（A2 に依存）
├── Todo B2: [TDD] PLAN マークダウンパーサー（B1 に依存）
└── Todo B3: [TDD] プロジェクトスキャナー（B1 に依存）

Gate C: API + UI（Gate B 完了後）
├── Todo C1: API route 実装（B2, B3 に依存）
├── Todo C2: レイアウト + プロジェクトフィルター（C1 に依存）
├── Todo C3: 看板ビュー（C2 に依存）
└── Todo C4: PLAN カード + 詳細展開（C3 に依存）

Gate D: 統合テスト（Gate C 完了後）
└── Todo D1: 統合動作確認（C4 に依存）
```

### Gate A: プロジェクトセットアップ

- [ ] **Todo A1**: Next.js プロジェクト初期化 + UI ライブラリセットアップ
  > **Review A1**:

- [ ] **Todo A2**: .gitignore + npm scripts 更新
  > **Review A2**:

**Gate A 通過条件**: `cd dashboard && npm run dev` でエラーなく起動し、shadcn/ui コンポーネントが利用可能な状態

### Gate B: データ層

- [ ] **Todo B1**: projects.yaml 設定ファイル + 型定義
  > **Review B1**:

- [ ] **Todo B2**: [TDD] PLAN マークダウンパーサー
  > **Review B2**:

- [ ] **Todo B3**: [TDD] プロジェクトスキャナー
  > **Review B3**:

**Gate B 通過条件**: 全テスト PASS。パーサーが 4 ステータスを正しく判定。スキャナーが実プロジェクトの PLAN を収集できる

### Gate C: API + UI

- [ ] **Todo C1**: API route 実装 (/api/plans)
  > **Review C1**:

- [ ] **Todo C2**: ダッシュボードレイアウト + プロジェクトフィルター
  > **Review C2**:

- [ ] **Todo C3**: 看板ビュー (4 カラム表示)
  > **Review C3**:

- [ ] **Todo C4**: PLAN カード + 詳細展開
  > **Review C4**:

**Gate C 通過条件**: ブラウザで看板が表示され、プロジェクトフィルターで絞り込み、PLAN カードの展開が動作する

### Gate D: 統合テスト

- [ ] **Todo D1**: 統合動作確認
  > **Review D1**:

**Gate D 通過条件**: 実プロジェクトデータで全機能が正常動作

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| Gate/Todo 構造のない古い PLAN ファイル | ステータス判定不可 | チェックボックスなし → 「未実装」にフォールバック |
| プロジェクトパスが無効（削除済み等） | スキャナーがエラー | try-catch でスキップ、エラーログ出力 |
| PLAN ファイル数が多い場合のパフォーマンス | API レスポンス遅延 | 初回は問題なし。必要に応じてキャッシュ追加 |
| ai-elements の Next.js バージョン互換性 | ビルドエラー | ai-elements が要求するバージョンに合わせる |
