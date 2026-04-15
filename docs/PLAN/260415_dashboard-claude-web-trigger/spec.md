# ダッシュボードから Claude Code Web セッションを起動する FAB + Dialog

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> `/dev:spec-run` 実行時に Claude main session が先に実行する。詳細は `tasks.json` の `preflight` 配列を参照。

- [x] **P1**: ai-elements の PromptInput を shadcn registry 経由で導入（2026-04-15 完了）
- [x] **P2**: Toast 通知用に shadcn sonner を導入（2026-04-15 完了）
- [x] **P3**: Vercel env に CLAUDE_SESSION_KEY / CLAUDE_ORG_UUID / CLAUDE_ENV_ID を設定（2026-04-15 完了）
- [x] **P4**: Vercel + 内部 API の e2e 検証（probe endpoint 経由で Path B 確定、2026-04-15 完了）
- [x] **P5**: dashboard/.env.example を更新（CLAUDE_* サンプル行追加 + ANTHROPIC_ROUTINE_* 旧エントリ削除、A3 として実施・既コミット 32b54cf 反映済み）

---

## 概要

PLAN ダッシュボード画面右下に Floating Action Button (FAB) を配置し、サイドバーで現在選択中のリポジトリから 1 つを選んで **claude.ai 内部 API (`POST /v1/sessions`)** 経由で Claude Code Web セッションを起動する。起動成功時は新規タブで claude.ai/code を自動オープンしつつ、Dialog 内にも URL とコピーボタンを残す。

## 背景

- 既に `dot-claude-dev` のダッシュボードは GitHub 上の PLAN を一覧する hub になっており、ここから「次の作業を Claude Code Web に投げる」までを 1 画面で完結させたい。
- 2026-04-14 に公式 Routines API を検証したが、`/fire` の body に repo 指定手段がなく、multi-repo ルーチンは fan-out 動作（1 fire → N session 並列生成）をしてしまうため本要件（1 submit = 1 session、任意 repo 指定）には不適合と判明。
- 代替として **claude.ai 内部 API `POST /v1/sessions`** を採用。`sessionKey` Cookie（HttpOnly, `sk-ant-sid02-...`, 131 chars）で認証し、`session_context.sources[]` に repo URL と `refs/heads/{branch}` を明示することで任意 repo / branch のセッションを 1 回で作れる（詳細は `docs/REFERENCE/claude-code-web-internal-api.md`）。
- 2026-04-15 の Vercel 本番 e2e 検証で、Vercel Node.js runtime からの Node fetch が Cloudflare を素通りし、内部 API に直接到達することを実証済み（probe endpoint の 3 モードすべて期待どおり動作、`session_01MVgg1UsdweHDTBWZrbsu5j` を実際に作成しブラウザで Claude 起動確認）。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | UI 配置 | Floating Action Button（右下固定 / Plus アイコン）→ クリックで Dialog 開閉 | ヘッダー / サイドバーの既存レイアウトに干渉せず、新機能だと一目で分かる。collapsed sidebar とも独立して常時アクセス可 |
| 2   | リポジトリ選択 | サイドバーで既に選択中の `selectedRepos` を form に渡し、その中から 1 つだけ select | 既存のリポジトリ選択 UX を流用 → ユーザーが二度選ばずに済む。0 件選択時は FAB を disable |
| 3   | ブランチ指定 | MVP はデフォルトブランチ固定。UI には `default_branch` を read-only で表示 | 内部 API は `refs/heads/{branch}` で任意ブランチを受け取れるが、UI スコープを絞る。任意 branch は次フェーズ |
| 4   | 認証方式 | `sessionKey` Cookie を Vercel 環境変数 `CLAUDE_SESSION_KEY` に保存。route handler 内で `process.env` 経由で読む | 単一キーの読み書きに外部ストレージ（Redis 等）は過剰。`vercel env add` 1 発で完結し、更新も `refresh-claude-web-cookie` スキルの `vercel env rm + add` で自動化可能 |
| 5   | 起動成功時 | `window.open(sessionUrl, '_blank')` で新規タブを開く + Dialog 内に URL を残す | ポップアップブロック対策とユーザーが後から再アクセス可能にするための二重表示 |
| 6   | 起動履歴 | 保持しない（Toast と Dialog のみ、閉じれば消える） | claude.ai/code 側にセッション一覧があるため二重保存しない |
| 7   | UI ライブラリ | ai-elements の PromptInput を shadcn registry 経由でこのリポにコピー | shadcn/ui ベースとの統合が自然、追従コストはアップデート時の手動追加で許容 |
| 8   | エラー通知 | 主要エラー（missing-env / sessionKey expired / CF block / upstream）を Toast (sonner) と Dialog 内バナーで表示。サーバーログ収集なし | MVP として実用十分。Vercel ログだけで運用 |
| 9   | 認証ガード | `dashboard/proxy.ts` (Next.js middleware) が `/api/sessions/launch` を含む全 `/api/*` を既に認証ガードしているため、route handler 側に追加 auth コードは書かない | 既存 `/api/repos` も同じ理由で route 内 auth を持っていない。middleware 一極集中で挙動が一貫する |
| 10  | エンドポイント | `POST /api/sessions/launch` （body: `{ repo, branch, prompt }`） | RESTful。将来 `/api/sessions` 配下に他の操作（list / cancel）を生やせる余地を残す |
| 11  | sessionKey 期限切れ | 内部 API が 401 を返したら `cookieExpired: true` を付けて 401 転送。Dialog は Toast で「Cookie 切れ。ターミナルで `/refresh-claude-web-cookie` を実行してください」を案内 | sessionKey の有効期限は未確定のため、期限切れパスは必ず用意する |

## アーキテクチャ詳細

### データフロー

```
[Browser]
  │ Sidebar で selectedRepos を選択 (既存)
  │
  │ FAB click → Dialog open
  │ Repo select → branch 自動決定
  │ Prompt 入力 → Submit
  ▼
[POST /api/sessions/launch]  body: {repo, branch, prompt}
  │ (auth は proxy.ts middleware で済み — route 内では追加チェックなし)
  │ 1. body 検証
  │ 2. env から sessionKey / orgUuid / envId を取得
  │ 3. createClaudeWebSession() 呼び出し
  ▼
[lib/claude-web-client.ts]  純関数
  │ fetch → POST https://claude.ai/v1/sessions
  │   headers:
  │     User-Agent: Chrome 系 UA (必須: curl UA だと CF 403)
  │     Cookie: sessionKey={sk-ant-sid02-...}
  │     anthropic-version: 2023-06-01
  │     anthropic-beta: ccr-byoc-2025-07-29
  │     anthropic-client-feature: ccr
  │     x-organization-uuid: {orgUuid}
  │   body:
  │     title, events: [{type:'event', data:{uuid, session_id:'', type:'user', message:{role:'user', content:prompt}}}],
  │     environment_id, session_context: {sources, outcomes, model}
  ▼
[claude.ai 内部 API]
  │ 200 → { id: "session_...", ... }
  │ 401 → sessionKey 期限切れ
  │ 4xx/5xx → その他エラー
  ▼
[Browser]
  │ ok:    Toast success + window.open(sessionUrl) + Dialog 内 URL 表示
  │ 401:   Toast「Cookie 切れ。ターミナルで /refresh-claude-web-cookie を実行」+ Dialog バナー
  │ error: Toast error + Dialog バナーにメッセージ
```

### 主要型定義

```ts
// lib/claude-web-client.ts (新規)
export interface CreateSessionInput {
  sessionKey: string;
  orgUuid: string;
  environmentId: string;
  repo: string;        // owner/name
  branch: string;      // default branch
  prompt: string;
  model?: string;      // default: 'claude-sonnet-4-6'
  fetchImpl?: typeof fetch;
}

export type CreateSessionResult =
  | { ok: true; sessionId: string; sessionUrl: string }
  | { ok: false; code: 'missing-env' | 'invalid-input' | 'cookie-expired' | 'forbidden' | 'rate-limit' | 'upstream-error' | 'network'; message: string };

export async function createClaudeWebSession(input: CreateSessionInput): Promise<CreateSessionResult>;

// lib/types.ts (修正)
export interface GitHubRepo {
  // ...既存フィールド
  default_branch: string;  // ★追加
}
```

### API レスポンス契約 (`POST /api/sessions/launch`)

| status | 条件 | body |
| --- | --- | --- |
| 200 | 起動成功 | `{ "sessionId": "session_...", "sessionUrl": "https://claude.ai/code/session_..." }` |
| 400 | 必須 body 欠落 / invalid-input | `{ "error": "..." }` |
| 401 | dashboard auth 未通過 | 既存 auth 層と同じ |
| 401 | sessionKey 期限切れ | `{ "error": "sessionKey expired. Run /refresh-claude-web-cookie", "cookieExpired": true }` |
| 429 | upstream rate-limit | `{ "error": "..." }` |
| 500 | env 未設定 | `{ "error": "CLAUDE_SESSION_KEY / CLAUDE_ORG_UUID / CLAUDE_ENV_ID env が未設定です" }` |
| 502 | upstream 403/network/その他 5xx | `{ "error": "..." }` |

### UI 階層

```
app/page.tsx
└── DashboardLayout (既存)
    ├── AppSidebar (既存)
    └── SidebarInset (既存)
        └── main (既存 — Kanban / Table)
└── SessionLauncherFab (★新規)
    ├── Button (FAB, fixed bottom-6 right-6)
    └── SessionLauncherDialog (★新規)
        ├── DialogHeader / DialogDescription
        ├── repo <select>
        ├── branch readonly 表示
        ├── PromptInput (ai-elements)
        │   ├── PromptInputTextarea
        │   └── PromptInputToolbar > PromptInputSubmit
        ├── 結果 success / error バナー
        └── DialogFooter
```

### env 仕様

```bash
# dashboard/.env.local (ローカル)
CLAUDE_SESSION_KEY=sk-ant-sid02-...            # 131 chars, HttpOnly Cookie from claude.ai
CLAUDE_ORG_UUID=72f15ec8-6c9f-4c94-9014-5021153382bb
CLAUDE_ENV_ID=env_01RqJFrxgn6poGNpyCTFWHh5
```

Vercel 側：
- **Production**: 3 変数すべて設定済み（2026-04-15）。CLAUDE_SESSION_KEY は sensitive フラグ付き
- **Preview / Development**: Vercel CLI の非対話モードで sensitive 変数を追加できない既知のバグがあるため未設定。本 MVP は `vercel --prod` 前提で運用

sessionKey の更新フロー（Cookie 期限切れ時）:
1. ターミナルで `/refresh-claude-web-cookie` スキル起動（今回の検証で frontmatter を追加した。セッション再起動すれば `Skill` ツール経由でも呼べる）
2. Chrome から抽出 → Vercel env を `vercel env rm + add` で置換 → 再デプロイ（sensitive env の反映には再デプロイが必要）

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/lib/types.ts` | `GitHubRepo` に `default_branch: string` 追加 | 既存 import 箇所はすべてフィールド追加のみで型エラーなし |
| `dashboard/app/layout.tsx` | `<Toaster />` (sonner) を <body> 末尾にマウント | 既存 UI に影響なし |
| `dashboard/app/page.tsx` | `<SessionLauncherFab>` を DashboardLayout の children 末尾に追加 | 既存レイアウトに視覚干渉なし（fixed positioning） |
| `dashboard/.env.example` | `ANTHROPIC_ROUTINE_*` 行を削除、`CLAUDE_SESSION_KEY` / `CLAUDE_ORG_UUID` / `CLAUDE_ENV_ID` のプレースホルダ行を追加 | 新メンバのセットアップ手順が正確になる |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/lib/claude-web-client.ts` | 内部 API `POST /v1/sessions` を呼ぶ純関数 `createClaudeWebSession` |
| `dashboard/__tests__/lib/claude-web-client.test.ts` | vitest で 7 ケースの単体テスト |
| `dashboard/app/api/sessions/launch/route.ts` | POST handler。body 検証 + claude-web-client 呼び出し（auth は middleware 任せ） |
| `dashboard/components/session-launcher-fab.tsx` | 右下 FAB ボタン + Dialog 開閉 state |
| `dashboard/components/session-launcher-dialog.tsx` | Dialog 中身：form + submit + 結果表示 |
| `dashboard/components/ai-elements/prompt-input.tsx` | P1 で shadcn add により自動生成（手書きしない、2026-04-15 に Preflight P1 で導入済み） |
| `dashboard/components/ui/sonner.tsx` | P2 で shadcn add により自動生成（2026-04-15 に Preflight P2 で導入済み） |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/components/dashboard-layout.tsx` | FAB は `<DashboardLayout>` の外側 / fixed positioning なので layout 自体には触れない |
| `dashboard/components/app-sidebar.tsx` | サイドバー UI は既存のまま流用（リポジトリ選択ロジックを再利用するだけ） |

### 削除するファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/app/api/probe/claude-web/route.ts` | 検証用 probe endpoint。Path B 確定後に撤去（Todo 6 で git commit 前に削除） |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `docs/REFERENCE/claude-code-web-internal-api.md` | 内部 API `POST /v1/sessions` のエンドポイント / ヘッダ / body フォーマット（B1 実装時の正確な仕様） |
| `docs/REFERENCE/claude-code-web-session-creation.md` | 経路選択の経緯（Routines API 不採用 → 内部 API 採用）と両者の比較 |
| `.claude/skills/dev/refresh-claude-web-cookie/SKILL.md` | sessionKey 更新手順（UI 側の期限切れエラーメッセージから案内する） |
| `dashboard/lib/types.ts` | 既存型と GitHubRepo の現在の形を把握 |
| `dashboard/app/api/repos/route.ts` | 既存 Route Handler の return 形式パターン（B2 の参考。auth コードは持っていないことを確認） |
| `dashboard/proxy.ts` | Next.js middleware による `/api/*` 一括 auth ガードの matcher を確認（B2 が追加 auth を書かない根拠） |
| `dashboard/lib/github.ts` | `fetchUserRepos` が GitHub API レスポンスを pass-through していることを確認（A1 が型追加のみで完結する根拠） |
| `dashboard/app/page.tsx` | C3 マウント先、selectedRepos / reposData の利用箇所 |
| `dashboard/components/dashboard-layout.tsx` | FAB を配置する際のレイヤー関係（Sidebar の z-index） |

### 参照資料（references/ にコピー済み）

| ファイル | 目的 |
| -------- | ---- |
| `references/ai-elements-prompt-input.md` | ai-elements PromptInput の API・典型構成（C2 実装時に参照） |

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 基盤準備
Gate B: 内部 API ラッパーとエンドポイント（Gate A 完了後）
Gate C: FAB と Launcher Dialog の UI 構築（Gate A, B 完了後）
Gate D: 動作検証（Gate C 完了後）
```

### Gate A: 基盤準備

> 型拡張・Toaster 配線・.env.example 修正。後続の API・UI が依存する土台を整える。

- [x] **A1**: [SIMPLE] GitHubRepo 型に default_branch を追加
  > **Review A1**: ✅ PASSED — GitHubRepo に default_branch: string を追加。tsc 通過 (関連エラーなし)。テストモック __tests__/github.test.ts と __tests__/types-contract.test.ts も同フィールドを満たすよう更新。
- [x] **A2**: [SIMPLE] dashboard/app/layout.tsx に <Toaster /> をマウント
  > **Review A2**: ✅ PASSED — layout.tsx に Toaster import 追加 + <Toaster richColors closeButton position='top-right' /> を <body> 内 children 直後に配置。components/ui/sonner.tsx は P2 で導入済み確認。tsc 関連エラーなし。
- [x] **A3**: [SIMPLE] dashboard/.env.example を CLAUDE_* 前提に書き換え
  > **Review A3**: ⏭️ SKIPPED — 既コミット 32b54cf で .env.example は CLAUDE_SESSION_KEY / CLAUDE_ORG_UUID / CLAUDE_ENV_ID 行追加・ANTHROPIC_ROUTINE_* 行削除済み。今回は Read で現状を確認、変更不要のため SKIPPED。

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: 内部 API ラッパーとエンドポイント

> 純関数の claude.ai 内部 API クライアントと、env を読む Next.js Route Handler を実装する。

- [x] **B1**: [TDD] dashboard/lib/claude-web-client.ts で POST /v1/sessions を呼ぶ純関数を実装
  > **Review B1**: ✅ PASSED — TDD で 7 テスト (missing-env / invalid-input / happy / 401 / 403 / 429 / network) すべて GREEN。reviewer-correctness が API ヘッダ・body・status code map・security (sessionKey 漏洩なし) を仕様書と reference doc に対し全 PASS 判定。
- [x] **B2**: POST /api/sessions/launch route handler
  > **Review B2**: ✅ PASSED — thin wrapper として B1 を呼ぶ実装、auth は proxy.ts middleware に委譲、runtime='nodejs' 明示。reviewer-correctness が status code map (missing-env→500 / invalid-input→400 / rate-limit→429 / cookie-expired→401+cookieExpired / forbidden/network/upstream→502) を全 PASS 判定。sessionKey はレスポンスに含めない。

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: FAB と Launcher Dialog の UI 構築

> 右下 FAB → Dialog → PromptInput → 起動・結果表示の UI 層を組み上げ、page.tsx に統合する。

- [x] **C1**: components/session-launcher-fab.tsx (右下固定 FAB ボタン)
  > **Review C1**: ✅ PASSED — fixed bottom-6 right-6 z-40 で右下 FAB を実現、candidateRepos 0 件で disabled、aria-label と title 完備。reviewer-correctness が全項目 PASS 判定。
- [x] **C2**: components/session-launcher-dialog.tsx (Dialog 中身: フォーム + 送信 + 結果表示)
  > **Review C2**: ✅ PASSED — POST /api/sessions/launch に repo/branch/prompt のみ送信、200→window.open + sonner success + Dialog 内 URL/Copy/ExternalLink、401 cookieExpired→専用メッセージ + duration:10000 toast、その他→toast.error + バナー、送信中 disable、close で state リセット。security: sessionKey クライアント漏洩なし。
- [x] **C3**: [SIMPLE] dashboard/app/page.tsx に SessionLauncherFab をマウント
  > **Review C3**: ✅ PASSED — import 追加、DashboardLayout の children 末尾に <SessionLauncherFab selectedRepos={selectedRepos} repos={reposData.repos} /> を配置。

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: 動作検証

> ブラウザでハッピーパスとエラーパスを通し、想定どおりに動くことを確認する。probe endpoint も撤去する。

- [ ] **D1**: ブラウザでハッピーパス + エラーパスを手動検証
  > **Review D1**: _未記入_
- [ ] **D2**: [SIMPLE] probe endpoint を削除しデプロイ
  > **Review D2**: _未記入_

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| 内部 API 非公開 | Anthropic 側が `POST /v1/sessions` のシグネチャや認証を変更すると即死する | `lib/claude-web-client.ts` を 1 箇所に閉じ、変更時は型・テストごと差し替えやすくしている。`docs/REFERENCE/claude-code-web-internal-api.md` に実測結果を蓄積している |
| sessionKey 期限切れ | ある日突然 401 になり全セッション起動が失敗 | Route 層で 401 をキャッチして `cookieExpired: true` を返す。UI 側で Toast に「`/refresh-claude-web-cookie` を実行してください」と表示。手順は SKILL.md に明文化済み |
| sessionKey 漏洩 | 任意ユーザーが個人アカウントとしてセッションを作れてしまう | Vercel env の sensitive 属性で保管・クライアント側に出さない（Route Handler 経由でしか触れない）。probe endpoint のレスポンスにも Cookie 値は絶対に含めない（既に実装済み）。万一漏洩したら claude.ai 再ログインで即無効化可能 |
| Cloudflare 仕様変更 | CF が Node fetch をブロックするようになると素通り不可能に | 2026-04-15 時点で passthrough を実証済み。変更検知のために probe endpoint と同等の監視スクリプトを運用に組み込める余地を残す（このスコープでは実装しない） |
| ポップアップブロック | window.open がブラウザ設定でブロックされ新規タブが開かない | Dialog 内に sessionUrl を残し、Copy / Open ボタンから再アクセス可能にする |
| ZDR 組織での利用不可 | Zero Data Retention 有効組織では cloud session 自体が使えず 403 などが返る | エラーメッセージで原因を明示。ZDR 組織での利用は仕様外と README に明記 |
| デフォルトブランチ縛り | フィーチャーブランチで作業したいユースケースに非対応 | 内部 API は `refs/heads/{branch}` で任意 branch を受け取れるため、次フェーズで branch select UI を追加するだけで対応可能（API 側の変更不要） |
| ai-elements の API 変更 | shadcn registry から取り込んだコンポーネントが将来仕様変更される | コンポーネントはコピーされてリポに入るため、registry 側変更は自動追従しない。アップデート時のみ手動再 add で対応 |
| Vercel Preview env 未設定 | `vercel` (non-prod) デプロイでは CLAUDE_SESSION_KEY が無く動かない | MVP は `vercel --prod` 前提。Preview で必要になったら Vercel ダッシュボードから手動設定（CLI バグ回避） |
