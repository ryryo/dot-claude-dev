# ダッシュボード パスワード認証

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

PLAN ダッシュボードに共有パスワードによる簡易認証を追加し、第三者がアクセスできないようにする。

## 背景

ダッシュボードは現在認証なしで公開されており、URL を知っている誰でもアクセス可能。GitHub Token を使って非公開リポジトリの情報を表示するため、最低限のアクセス制御が必要。OAuth や外部 IdP は過剰なので、環境変数に設定した共有パスワード + Cookie セッションで保護する。

## 設計決定事項

| #   | トピック             | 決定                                                  | 根拠                                             |
| --- | -------------------- | ----------------------------------------------------- | ------------------------------------------------ |
| 1   | 認証方式             | 共有パスワード（環境変数）+ httpOnly Cookie            | 最小コストで十分なセキュリティ                   |
| 2   | セッション管理       | HMAC-SHA256 署名付き Cookie（有効期限 7 日）          | JWT ライブラリ不要、Node.js crypto のみで実現    |
| 3   | 保護範囲             | 全ルート（`/login` と `/api/auth` を除く）            | API ルートも保護して直接アクセスを防止           |
| 4   | パスワードハッシュ   | timingSafeEqual で比較                                | タイミング攻撃を防止                             |
| 5   | Cookie 名            | `dashboard-session`                                   | 用途が明確                                       |
| 6   | 追加依存             | なし（Node.js 標準 crypto のみ）                      | 依存を増やさない方針                             |

## アーキテクチャ詳細

### 認証フロー

```
[Browser] --GET /--> [Middleware]
                        |
                  Cookie あり？ ──Yes──> HMAC 検証 ──Valid──> Next Response (通過)
                        |                              |
                       No                           Invalid
                        |                              |
                        └──────── 302 /login <─────────┘

[Login Page] --POST /api/auth--> [Auth API]
                                      |
                              パスワード一致？
                              /            \
                           Yes              No
                            |                |
                    Set-Cookie +         401 JSON
                    302 / redirect
```

### Cookie 構造

```
Value: "{timestamp}.{hmac_hex}"
HMAC = SHA256(COOKIE_SECRET, timestamp)
```

- `COOKIE_SECRET`: `DASHBOARD_PASSWORD` から派生（`SHA256("cookie-secret:" + password)`）
- 検証時: timestamp が 7 日以内 && HMAC が一致

### 環境変数

| 変数名               | 必須 | 説明                     |
| -------------------- | ---- | ------------------------ |
| `DASHBOARD_PASSWORD` | Yes  | ダッシュボードのパスワード |

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル         | 変更内容                          | 影響                   |
| ---------------- | --------------------------------- | ---------------------- |
| `.env.example`   | `DASHBOARD_PASSWORD` 追加         | ドキュメント的変更のみ |

### 新規作成ファイル

| ファイル                | 内容                                     |
| ----------------------- | ---------------------------------------- |
| `middleware.ts`         | Cookie 検証 + リダイレクト Middleware     |
| `lib/auth.ts`           | Cookie 生成・検証のユーティリティ        |
| `app/login/page.tsx`    | パスワード入力フォーム                   |
| `app/api/auth/route.ts` | POST: パスワード検証 + Cookie 設定       |

### 変更しないファイル

| ファイル                  | 理由                                   |
| ------------------------- | -------------------------------------- |
| `app/page.tsx`            | Middleware で保護するため変更不要       |
| `app/api/repos/route.ts`  | Middleware で保護するため変更不要       |
| `app/api/plans/route.ts`  | Middleware で保護するため変更不要       |
| `next.config.ts`          | Middleware はルートに置くだけで動作する |

## 参照すべきファイル

### コードベース内

| ファイル              | 目的                                 |
| --------------------- | ------------------------------------ |
| `app/layout.tsx`      | 全体レイアウト・フォント定義の確認   |
| `app/page.tsx`        | 既存の UI パターン確認               |
| `app/error.tsx`       | エラー UI パターン確認               |
| `.env.example`        | 既存の環境変数定義確認               |
| `lib/utils.ts`        | cn() ユーティリティの確認            |

## タスクリスト

### 依存関係図

```
Gate A: パスワード認証実装
├── Todo 1: lib/auth.ts（認証ユーティリティ）
├── Todo 2: app/api/auth/route.ts（認証API）← Todo 1
├── Todo 3: middleware.ts（認証Middleware）← Todo 1
├── Todo 4: app/login/page.tsx（ログインページ）← Todo 2
└── Todo 5: .env.example 更新 + 動作確認
```

### Gate A: パスワード認証実装

#### Todo 1: 認証ユーティリティ作成 (lib/auth.ts)

- [x] **Step 1 — IMPL**
  - **対象**: `lib/auth.ts`（新規作成）
  - **内容**: Cookie の生成・検証ロジックを実装
  - **実装詳細**:
    - `import { createHmac, timingSafeEqual, createHash } from "node:crypto"`
    - 定数: `COOKIE_NAME = "dashboard-session"`, `MAX_AGE = 7 * 24 * 60 * 60`（7日）
    - `getSecret()`: `process.env.DASHBOARD_PASSWORD` から `SHA256("cookie-secret:" + password)` でシークレット派生。未設定時は throw
    - `createSessionCookie()`: `Date.now()` の timestamp と HMAC を `.` で結合した値を返す
    - `verifySessionCookie(value: string)`: timestamp と HMAC を分割、期限チェック（MAX_AGE 以内）、HMAC 検証（timingSafeEqual）。成功で `true`
    - `verifyPassword(input: string)`: `DASHBOARD_PASSWORD` と timingSafeEqual で比較。Buffer 長が異なる場合も固定時間で比較
  - **依存**: なし

- [x] **Step 2 — Review A1**
  > **Review A1**: ✅ PASSED (FIX 2回)
  > - Web Crypto API に書き換え（Edge Runtime 互換）
  > - 異なる長さの入力でも固定時間比較を保証

#### Todo 2: 認証 API ルート作成 (app/api/auth/route.ts)

- [x] **Step 1 — IMPL**
  - **対象**: `app/api/auth/route.ts`（新規作成）
  - **内容**: POST でパスワードを受け取り、Cookie を設定してリダイレクト
  - **実装詳細**:
    - `import { NextResponse } from "next/server"`
    - `import { verifyPassword, createSessionCookie, COOKIE_NAME, MAX_AGE } from "@/lib/auth"`
    - POST handler:
      1. `request.json()` から `{ password }` を取得
      2. `verifyPassword(password)` で検証
      3. 失敗 → `NextResponse.json({ error: "パスワードが正しくありません" }, { status: 401 })`
      4. 成功 → `NextResponse.json({ ok: true })` に `Set-Cookie` ヘッダー追加: `COOKIE_NAME=createSessionCookie(); Path=/; HttpOnly; SameSite=Lax; Max-Age=MAX_AGE`。本番環境では `Secure` も付与
  - **依存**: Todo 1

- [x] **Step 2 — Review A2**
  > **Review A2**: ✅ PASSED (FIX 1回)
  > - 不正JSON/空ボディで400を返すバリデーション追加

#### Todo 3: 認証 Middleware 作成 (middleware.ts)

- [x] **Step 1 — IMPL**
  - **対象**: `middleware.ts`（プロジェクトルートに新規作成）
  - **内容**: 全リクエストで Cookie を検証し、未認証なら `/login` にリダイレクト
  - **実装詳細**:
    - `import { NextResponse } from "next/server"` / `import type { NextRequest } from "next/server"`
    - `import { verifySessionCookie, COOKIE_NAME } from "@/lib/auth"`
    - `middleware(request: NextRequest)`:
      1. Cookie から `COOKIE_NAME` を取得
      2. `verifySessionCookie()` で検証
      3. 有効 → `NextResponse.next()`
      4. 無効 → `NextResponse.redirect(new URL("/login", request.url))`
    - `export const config = { matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"] }`
      - `/login`, `/api/auth`, Next.js 内部アセットを除外
  - **依存**: Todo 1

- [x] **Step 2 — Review A3**
  > **Review A3**: ✅ PASSED (FIX 1回)
  > - `_next/*` 全体を除外するよう matcher 修正（HMR等の開発時リクエスト対応）
  > - P1（/login未作成）は Todo 4 で対応予定のため設計意図通りと判定

#### Todo 4: ログインページ作成 (app/login/page.tsx)

- [x] **Step 1 — IMPL**
  - **対象**: `app/login/page.tsx`（新規作成）
  - **内容**: パスワード入力フォームを作成
  - **実装詳細**:
    - `"use client"` コンポーネント
    - 状態: `password`, `error`, `loading`
    - UI: 既存の Card/Badge コンポーネントを活用。中央寄せレイアウト（`error.tsx` のパターン参考）
      - タイトル「PLAN Dashboard」
      - パスワード input（type="password"）
      - 送信ボタン「ログイン」
      - エラー表示エリア
    - Submit handler:
      1. `fetch("/api/auth", { method: "POST", body: JSON.stringify({ password }) })`
      2. 成功 → `window.location.href = "/"`（フルリロードで Middleware を再評価）
      3. 失敗 → `setError("パスワードが正しくありません")`
    - スタイル: 既存の Tailwind テーマ・フォント変数を使用。ダークモード対応（既存と同等）
  - **依存**: Todo 2

- [x] **Step 2 — Review A4**
  > **Review A4**: ✅ PASSED
  > - P2（ハイドレーション前のフォーム送信）は内部ツールのため設計意図通りと判定

#### Todo 5: 環境変数設定 + 動作確認

- [x] **Step 1 — IMPL**
  - **対象**: `.env.example`（変更）
  - **内容**: `DASHBOARD_PASSWORD` を追記
  - **実装詳細**:
    - `.env.example` に `DASHBOARD_PASSWORD=your_password_here` を追加
    - `.env.local` にも実際のパスワードを設定（コミットしない）
  - **依存**: なし

- [x] **Step 2 — Review A5**
  > **Review A5**: ⏭️ SKIPPED (docs only)

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク                             | 影響       | 緩和策                                         |
| ---------------------------------- | ---------- | ---------------------------------------------- |
| パスワードが弱い場合のブルートフォース | 不正アクセス | 運用で強いパスワードを設定。将来的にレート制限追加可 |
| Cookie シークレットがパスワード依存  | パスワード変更時に全セッション無効化 | 意図的な設計（パスワード変更 = 強制ログアウト） |
| HTTPS 未使用環境での Cookie 傍受     | セッション盗取 | 本番は Vercel (HTTPS) 前提。`Secure` フラグ付与 |
