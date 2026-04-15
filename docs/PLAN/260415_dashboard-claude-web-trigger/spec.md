# ダッシュボードから Claude Code Web セッションを起動する FAB + Dialog

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> `/dev:spec-run` 実行時に Claude main session が先に実行する。詳細は `tasks.json` の `preflight` 配列を参照。

- [x] **P1**: ai-elements の PromptInput を shadcn registry 経由で導入
- [x] **P2**: Toast 通知用に shadcn sonner を導入
- [ ] **P3**: **[手動]** claude.ai/code/routines で『汎用エージェント』ルーチンを作成し API トリガーを発行
- [ ] **P4**: **[手動]** dashboard/.env.local と Vercel env に ANTHROPIC_ROUTINE_TRIGGER_ID / ANTHROPIC_ROUTINE_TOKEN を設定

---

## 概要

PLAN ダッシュボード画面右下に Floating Action Button (FAB) を配置し、サイドバーで現在選択中のリポジトリから 1 つを選んで Routines API 経由で Claude Code Web セッションを起動する。起動成功時は新規タブで claude.ai/code を自動オープンしつつ、Dialog 内にも URL とコピーボタンを残す。

## 背景

- 既に `dot-claude-dev` のダッシュボードは GitHub 上の PLAN を一覧する hub になっており、ここから「次の作業を Claude Code Web に投げる」までを 1 画面で完結させたい。
- 2026-04-14 の Routines API リリースにより、外部システムから claude.ai/code セッションを起動する公式手段が整った（詳細は `docs/REFERENCE/claude-code-web-session-creation.md`）。
- URL パラメータでセッションを起こす案は Anthropic が公式に却下しているため、Routines API + 事前トークン発行が唯一の正攻法。
- ブランチ指定は API 側未対応で、プロンプトに `git checkout` を埋め込む回避策が必要だが、今回は MVP として **デフォルトブランチ固定** で回り、UI 上はブランチ名を表示するのみとする。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | UI 配置 | Floating Action Button（右下固定 / Plus アイコン）→ クリックで Dialog 開閉 | ヘッダー / サイドバーの既存レイアウトに干渉せず、新機能だと一目で分かる。collapsed sidebar とも独立して常時アクセス可 |
| 2   | リポジトリ選択 | サイドバーで既に選択中の `selectedRepos` を form に渡し、その中から 1 つだけ select | 既存のリポジトリ選択 UX を流用 → ユーザーが二度選ばずに済む。0 件選択時は FAB を disable |
| 3   | ブランチ指定 | デフォルトブランチ固定。UI には `default_branch` を read-only で表示 | Routines API が常にデフォルトから clone する制約に合わせる。MVP ではプロンプト埋め込み回避策まで実装しない |
| 4   | Routine 管理 | 単一 Routine を環境変数 `ANTHROPIC_ROUTINE_TRIGGER_ID` / `ANTHROPIC_ROUTINE_TOKEN` で固定 | 設計最小。Routine 側を `$TEXT` を実行するだけの薄いシェルにすれば、すべてのフォーム送信を 1 つの汎用エージェントで処理可能 |
| 5   | 起動成功時 | `window.open(sessionUrl, '_blank')` で新規タブを開く + Dialog 内に URL を残す | ポップアップブロック対策とユーザーが後から再アクセス可能にするための二重表示 |
| 6   | 起動履歴 | 保持しない（Toast と Dialog のみ、閉じれば消える） | claude.ai/code 側にセッション一覧があるため二重保存しない |
| 7   | UI ライブラリ | ai-elements の PromptInput を shadcn registry 経由でこのリポにコピー | shadcn/ui ベースとの統合が自然、追従コストはアップデート時の手動追加で許容 |
| 8   | エラー通知 | 主要エラー（missing-env / 401 / 403 / 429 / network）を Toast (sonner) と Dialog 内バナーで表示。サーバーログ収集なし | MVP として実用十分。Vercel ログだけで運用 |
| 9   | 認証 | `dashboard/proxy.ts` (Next.js middleware) が `/api/sessions/launch` を含む全 `/api/*` を既に認証ガードしているため、route handler 側に追加 auth コードは書かない | 既存 `/api/repos` も同じ理由で route 内 auth を持っていない。middleware 一極集中で挙動が一貫する |
| 10  | エンドポイント | `POST /api/sessions/launch` （body: `{ repo, branch, prompt }`） | RESTful。将来 `/api/sessions` 配下に他の操作（list / cancel）を生やせる余地を残す |

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
  │ 2. env から triggerId / token 取得
  │ 3. launchClaudeWebSession() 呼び出し
  ▼
[lib/routines-client.ts]  純関数
  │ fetch → POST https://api.anthropic.com/v1/claude_code/routines/{triggerId}/fire
  │   headers:  Authorization: Bearer {token}
  │             anthropic-beta: experimental-cc-routine-2026-04-01
  │             anthropic-version: 2023-06-01
  │   body:     { text: "Repo: {repo}\nBranch: {branch}\n\nTask: {prompt}" }
  ▼
[Anthropic Routines API]
  │ 200 → { type:"routine_fire", claude_code_session_id, claude_code_session_url }
  │ 401/403/429/5xx → エラー
  ▼
[Browser]
  │ ok:    Toast success + window.open(sessionUrl) + Dialog 内 URL 表示
  │ error: Toast error + Dialog バナーにメッセージ
```

### 主要型定義

```ts
// lib/routines-client.ts (新規)
export interface LaunchInput {
  triggerId: string;
  token: string;
  repo: string;        // owner/name
  branch: string;      // default branch
  prompt: string;
  fetchImpl?: typeof fetch;
}

export type LaunchResult =
  | { ok: true; sessionId: string; sessionUrl: string }
  | { ok: false; code: 'missing-env' | 'invalid-input' | 'unauthorized' | 'forbidden' | 'rate-limit' | 'upstream-error' | 'network'; message: string };

export async function launchClaudeWebSession(input: LaunchInput): Promise<LaunchResult>;

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
| 429 | upstream rate-limit | `{ "error": "..." }` |
| 500 | env 未設定 | `{ "error": "ANTHROPIC_ROUTINE_* env が未設定です" }` |
| 502 | upstream 401/403/network/その他 5xx | `{ "error": "..." }` |

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
# dashboard/.env.local
ANTHROPIC_ROUTINE_TRIGGER_ID=trig_...        # P3 で発行されたトリガー ID
ANTHROPIC_ROUTINE_TOKEN=sk-ant-oat01-...     # P3 で発行されたトークン (1 度しか表示されないので注意)
```

Vercel 側にも同じキーを Production / Preview に設定する。

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/lib/types.ts` | `GitHubRepo` に `default_branch: string` 追加 | 既存 import 箇所はすべてフィールド追加のみで型エラーなし |
| `dashboard/app/layout.tsx` | `<Toaster />` (sonner) を <body> 末尾にマウント | 既存 UI に影響なし |
| `dashboard/app/page.tsx` | `<SessionLauncherFab>` を DashboardLayout の children 末尾に追加 | 既存レイアウトに視覚干渉なし（fixed positioning） |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/lib/routines-client.ts` | Routines API /fire を呼ぶ純関数 `launchClaudeWebSession` |
| `dashboard/__tests__/lib/routines-client.test.ts` | vitest で 6 ケースの単体テスト |
| `dashboard/app/api/sessions/launch/route.ts` | POST handler。body 検証 + routines-client 呼び出し（auth は middleware 任せ） |
| `dashboard/components/session-launcher-fab.tsx` | 右下 FAB ボタン + Dialog 開閉 state |
| `dashboard/components/session-launcher-dialog.tsx` | Dialog 中身：form + submit + 結果表示 |
| `dashboard/components/ai-elements/prompt-input.tsx` | P1 で shadcn add により自動生成（手書きしない） |
| `dashboard/components/ui/sonner.tsx` | P2 で shadcn add により自動生成 |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/components/dashboard-layout.tsx` | FAB は `<DashboardLayout>` の外側 / fixed positioning なので layout 自体には触れない |
| `dashboard/components/app-sidebar.tsx` | サイドバー UI は既存のまま流用（リポジトリ選択ロジックを再利用するだけ） |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `docs/REFERENCE/claude-code-web-session-creation.md` | Routines API の正確なエンドポイント / ヘッダ / レスポンス契約と既知の制約 |
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
Gate B: Routines API ラッパーとエンドポイント（Gate A 完了後）
Gate C: FAB と Launcher Dialog の UI 構築（Gate A, B 完了後）
Gate D: 動作検証（Gate C 完了後）
```

### Gate A: 基盤準備

> 型拡張・Toaster 配線。後続の API・UI が依存する土台を整える。

- [ ] **A1**: [SIMPLE] GitHubRepo 型に default_branch を追加
  > **Review A1**: _未記入_
- [ ] **A2**: [SIMPLE] dashboard/app/layout.tsx に <Toaster /> をマウント
  > **Review A2**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: Routines API ラッパーとエンドポイント

> 純関数の Routines クライアントと、env を読む Next.js Route Handler を実装する。

- [ ] **B1**: [TDD] dashboard/lib/routines-client.ts で Routines API /fire を呼ぶ純関数を実装
  > **Review B1**: _未記入_
- [ ] **B2**: POST /api/sessions/launch route handler
  > **Review B2**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: FAB と Launcher Dialog の UI 構築

> 右下 FAB → Dialog → PromptInput → 起動・結果表示の UI 層を組み上げ、page.tsx に統合する。

- [ ] **C1**: components/session-launcher-fab.tsx (右下固定 FAB ボタン)
  > **Review C1**: _未記入_
- [ ] **C2**: components/session-launcher-dialog.tsx (Dialog 中身: フォーム + 送信 + 結果表示)
  > **Review C2**: _未記入_
- [ ] **C3**: [SIMPLE] dashboard/app/page.tsx に SessionLauncherFab をマウント
  > **Review C3**: _未記入_

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: 動作検証

> ブラウザでハッピーパスとエラーパスを通し、想定どおりに動くことを確認する。

- [ ] **D1**: ブラウザでハッピーパス + エラーパスを手動検証
  > **Review D1**: _未記入_

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| Routines API がベータ (`experimental-cc-routine-2026-04-01`) | 仕様変更で `/fire` シグネチャや response 形が変わる可能性 | `lib/routines-client.ts` を 1 箇所に閉じ、変更時は型・テストごと差し替えやすくしている。ベータヘッダは旧 2 バージョンまで互換維持されるため、変更検知後 1-2 週間は猶予あり |
| トークン漏洩 | 任意ユーザーが claude.ai/code 上で個人アカウントとしてセッションを作れてしまう | env のみで保管・クライアント側に出さない（Route Handler 経由でしか触れない）。トークン値は P3 の控えと secret store のみ。Regenerate 手順を README 化 |
| ポップアップブロック | window.open がブラウザ設定でブロックされ新規タブが開かない | Dialog 内に sessionUrl を残し、Copy / Open ボタンから再アクセス可能にする |
| ZDR 組織での利用不可 | Zero Data Retention 有効組織では cloud session 自体が使えず 403 などが返る | エラーメッセージで原因を明示。ZDR 組織での利用は仕様外と README に明記 |
| デフォルトブランチ縛り | フィーチャーブランチで作業したいユースケースに非対応 | Issue #10018 が解消されたらブランチ select UI を追加（次フェーズ）。当面はプロンプト本文に「`git checkout foo` を実行して」と書いてもらう運用 |
| ai-elements の API 変更 | shadcn registry から取り込んだコンポーネントが将来仕様変更される | コンポーネントはコピーされてリポに入るため、registry 側変更は自動追従しない。アップデート時のみ手動再 add で対応 |
