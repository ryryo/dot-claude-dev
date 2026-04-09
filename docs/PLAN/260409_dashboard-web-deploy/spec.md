# PLAN Dashboard Web Deploy（GitHub API統合）

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

PLAN Dashboard のローカルファイルシステム依存（`projects.yaml` + `fs` モジュール）を廃止し、GitHub API 経由で任意のリポジトリの `docs/PLAN` を取得することで、Vercel にデプロイ可能なダッシュボードへ移行する。ユーザーは Web UI からリポジトリを選択し、その選択状態は LocalStorage に永続化される。

## 背景

現状の `dashboard/` は、`projects.yaml` にローカル絶対パスを持ち、`fs` モジュールでファイルを直接読むため Vercel に上げると動作しない。方式A（GitHub API 直接取得）を採用し、最小限の変更でデプロイ可能にする。リポジトリ選択 UI を Web 上に持つことで `projects.yaml` の手動管理も不要になる。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|----------|------|------|
| 1 | データ取得方式 | 方式A: GitHub API 直接取得 | 追加インフラ不要、最短立ち上げ |
| 2 | リポジトリ選択保存先 | LocalStorage（キー: `plan-dashboard-selected-repos`） | セッションをまたいで維持、サーバーレスと相性が良い |
| 3 | 認証 | 環境変数 `GITHUB_TOKEN`（PAT: read:repo 最小権限） | シングルユーザー前提、Vercel env var で管理 |
| 4 | エラーハンドリング | 部分成功 + Next.js fetch キャッシュ併用 | 取得できたリポジトリのみ表示、失敗リポジトリはエラーバッジ |
| 5 | API キャッシュ | `next: { revalidate: 300 }` (5分) | GitHub API レート制限緩和 + 表示速度向上 |
| 6 | plans API 入力 | `GET /api/plans?repos=owner/repo1,owner/repo2` | クエリパラメータでリポジトリを受け取るステートレス設計 |
| 7 | projectName フィールド | `owner/repo` のフルネーム（例: `ryryo/dot-claude-dev`） | 一意性保証、GitHub URL と一致 |
| 8 | projects.yaml 廃止 | 完全削除（`lib/config.ts` も削除） | GitHub API に移行後は不要 |

## アーキテクチャ詳細

### データフロー図

```
[ブラウザ]
  │
  ├─ 起動時: GET /api/repos
  │    └─ GitHub API: GET /user/repos?per_page=100&sort=updated&type=all
  │         └─ GitHubRepo[] を返す
  │
  ├─ LocalStorage から選択済みリポジトリを復元
  │    └─ キー: "plan-dashboard-selected-repos"
  │    └─ 値: string[] (例: ["ryryo/dot-claude-dev", "ryryo/meurai-editer"])
  │
  └─ 選択変更時: GET /api/plans?repos=ryryo/dot-claude-dev,ryryo/meurai-editer
       └─ GitHub API: GET /repos/{owner}/{repo}/contents/docs/PLAN  (各リポジトリ)
            └─ .md ファイル → GET contents → parsePlanFile()
            └─ サブディレクトリ → GET {dir}/spec.md → parsePlanFile()
       └─ { plans: PlanFile[], errors: RepoError[] } を返す
```

### GitHub Contents API レスポンス型

```typescript
// lib/github.ts で定義
interface GitHubRepo {
  id: number
  name: string          // リポジトリ名 (例: "dot-claude-dev")
  full_name: string     // "owner/repo" (例: "ryryo/dot-claude-dev")
  private: boolean
  description: string | null
  updated_at: string    // ISO 8601
  html_url: string
}

interface GitHubContent {
  name: string          // ファイル/ディレクトリ名
  path: string          // "docs/PLAN/260409_dashboard-web-deploy.md"
  type: 'file' | 'dir'
  sha: string
}

interface GitHubFileContent extends GitHubContent {
  content: string       // base64 エンコード
  encoding: 'base64'
}

// /api/plans レスポンス追加型
interface RepoError {
  repo: string          // "owner/repo"
  message: string
}
```

### LocalStorage スキーマ

```
キー: "plan-dashboard-selected-repos"
値: JSON.stringify(string[])
例: '["ryryo/dot-claude-dev","ryryo/meurai-editer"]'
```

### ProjectConfig の変更

```typescript
// 変更前
interface ProjectConfig {
  name: string
  path: string  // "/Users/ryryo/dev/dot-claude-dev"
}

// 変更後（lib/types.ts）
interface ProjectConfig {
  name: string  // 表示名 (例: "dot-claude-dev")
  repo: string  // "owner/name" (例: "ryryo/dot-claude-dev")
}
```

### /api/plans レスポンス

```typescript
// 変更前
{ projects: ProjectConfig[], plans: PlanFile[] }

// 変更後
{ plans: PlanFile[], errors: RepoError[] }
```

### parsePlanFile の互換性

`parsePlanFile(content, filePath, projectName)` は変更不要。  
`filePath` に GitHub パス（例: `docs/PLAN/260409_dashboard-web-deploy/spec.md`）を渡す。  
`path.basename` / `path.dirname` はスラッシュ区切りで動作するため互換あり。

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|----------|----------|------|
| `dashboard/lib/types.ts` | `ProjectConfig.path → repo`、`GitHubRepo`/`RepoError` 型追加 | Gate 1 |
| `dashboard/app/api/plans/route.ts` | GitHub API 経由取得に刷新、`?repos=` クエリ対応 | Gate 2 |
| `dashboard/app/page.tsx` | `/api/repos` フェッチ追加、RepoSelector 統合、エラー表示 | Gate 3 |

### 新規作成ファイル

| ファイル | 内容 |
|----------|------|
| `dashboard/lib/github.ts` | GitHub API クライアント（fetchUserRepos, fetchPlanFiles） |
| `dashboard/app/api/repos/route.ts` | GET /api/repos: ユーザーのリポジトリ一覧返却 |
| `dashboard/components/repo-selector.tsx` | リポジトリ選択 UI + LocalStorage 永続化 |

### 削除するファイル

| ファイル | 理由 |
|----------|------|
| `dashboard/lib/config.ts` | projects.yaml 読み込みが不要になるため |
| `dashboard/lib/project-scanner.ts` | GitHub API クライアントに置き換えるため |
| `dashboard/projects.yaml` | GitHub API からリポジトリ一覧を取得するため |

### 変更しないファイル

| ファイル | 理由 |
|----------|------|
| `dashboard/lib/plan-parser.ts` | filePath を文字列として使うため互換あり |
| `dashboard/components/kanban-board.tsx` | plans: PlanFile[] の型は変わらない |
| `dashboard/components/plan-card.tsx` | 同上 |
| `dashboard/components/project-filter.tsx` | Gate 3 で RepoSelector に置き換えるが UI 参考として残す |
| `dashboard/components/dashboard-layout.tsx` | filterContent スロットで差し替えるため変更不要 |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
|----------|------|
| `dashboard/lib/types.ts` | 現行型定義の確認 |
| `dashboard/lib/plan-parser.ts` | `parsePlanFile` の引数・戻り値の確認 |
| `dashboard/app/api/plans/route.ts` | 現行 API の構造確認 |
| `dashboard/app/page.tsx` | 現行フロントの SWR・フィルタ構造確認 |
| `dashboard/components/project-filter.tsx` | 置き換え元コンポーネントの UI 参考 |
| `dashboard/components/dashboard-layout.tsx` | `filterContent` スロットの使い方確認 |

## タスクリスト

> **実装詳細は `tasks.json` を参照。** このセクションは進捗管理と Review 記録用。

### 依存関係図

```
Gate 1: バックエンド基盤
├── G1-T1: types.ts 更新 [TDD]
└── G1-T2: lib/github.ts 作成 [TDD]

Gate 2: API Routes刷新（Gate 1 完了後）
├── G2-T1: /api/repos/route.ts 作成
├── G2-T2: /api/plans/route.ts 刷新
└── G2-T3: lib/config.ts・project-scanner.ts・projects.yaml 削除

Gate 3: フロントエンド刷新（Gate 2 完了後）
├── G3-T1: RepoSelector コンポーネント作成
├── G3-T2: app/page.tsx 刷新
└── G3-T3: エラーバッジ・部分成功表示実装

Gate 4: デプロイ設定（Gate 3 完了後）
├── G4-T1: Vercel デプロイ設定
└── G4-T2: ローカル E2E 動作確認手順整備
```

### Gate 1: バックエンド基盤

- [x] **G1-T1**: types.ts 更新（ProjectConfig.path → repo、GitHubRepo/RepoError 型追加） [TDD]
  > **Review G1-T1**: ✅ PASSED (FIX 1回)
  > - project-scanner.ts の path→repo 変更を revert（G2-T3で削除予定のため as any で維持）

- [x] **G1-T2**: lib/github.ts 作成（GitHub API クライアント） [TDD]
  > **Review G1-T2**: ✅ PASSED (FIX 1回)
  > - spec.md取得時に非404エラーをre-throw、fetchContentsのdocstringに404制約を明記

**Gate 1 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate 2: API Routes刷新

- [x] **G2-T1**: app/api/repos/route.ts 作成
  > **Review G2-T1**: ✅ PASSED
  > - P1指摘(認証なし)は仕様の「シングルユーザー前提」設計決定により意図的

- [x] **G2-T2**: app/api/plans/route.ts 刷新
  > **Review G2-T2**: ✅ PASSED
  > - P1指摘(後方互換/認証なし)はG3-T2で解消予定+シングルユーザー設計決定

- [x] **G2-T3**: lib/config.ts・lib/project-scanner.ts・projects.yaml 削除
  > **Review G2-T3**: ✅ PASSED — tsc --noEmit エラーなし、残存インポート0件

**Gate 2 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate 3: フロントエンド刷新

- [x] **G3-T1**: RepoSelector コンポーネント作成
  > **Review G3-T1**: ✅ PASSED — P2(checkbox aria-label)は既存パターンと一致

- [x] **G3-T2**: app/page.tsx 刷新
  > **Review G3-T2**: ✅ PASSED — P2(LocalStorage復元値とrepos照合)は将来改善課題

- [x] **G3-T3**: エラーバッジ・部分成功表示実装
  > **Review G3-T3**: ✅ PASSED — コメントなし

**Gate 3 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate 4: デプロイ設定

- [x] **G4-T1**: Vercel デプロイ設定
  > **Review G4-T1**: ✅ PASSED — tsc + npm run build 成功

- [x] **G4-T2**: ローカル E2E 動作確認手順整備
  > **Review G4-T2**: ✅ PASSED — npm run build 成功、E2Eはユーザーが手動確認

**Gate 4 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| GitHub API レート制限（未認証: 60req/h、PAT: 5000req/h） | 多数のリポジトリ・PLANファイルで制限到達 | `revalidate: 300` で5分キャッシュ、PAT 必須 |
| private リポジトリの権限 | PAT に `repo` スコープが不足すると 404 | 設定手順書に `repo` スコープ明記 |
| docs/PLAN が存在しないリポジトリ | 空配列返却 → RepoSelector でリポジトリが空表示 | 将来的に「PLAN なし」バッジで示す（今回スコープ外） |
| `parsePlanFile` の `path` モジュール依存 | Vercel Edge Runtime では動作しない可能性 | Node.js Runtime（デフォルト）で実行するため問題なし |
