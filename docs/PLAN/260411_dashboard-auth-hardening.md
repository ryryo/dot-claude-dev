# Dashboard Authentication Hardening

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> Codex / サブエージェントの sandbox 制限（ネットワーク不可 / ワークスペース外書き込み不可 / 対話不可）により、以下のいずれかに該当する処理のみを列挙する:
> - **ネットワーク必須**: `npm/pnpm/yarn/bun/pip install`、`uv sync`、`npx create-*`、`git clone`、`curl`、リモート API 呼び出し 等
> - **ワークスペース外書き込み**: `brew install`、`apt install`、`cargo install`、`~/.zshrc` 編集 等
> - **対話必須**: `gh auth login`、`gcloud auth login`、OAuth フロー、パスワードプロンプト 等
>
> これらは `/dev:spec-run` 実行時に Claude main session が先に実行する。

- [ ] **P1**: **[手動]** `DASHBOARD_COOKIE_SECRET` を `dashboard/.env.local` に設定し、デプロイ先環境変数にも同じ値を登録する

---

## 概要

PLAN Dashboard の共有パスワード認証を hardening し、セッションクッキーからのオフライン辞書攻撃を防ぎつつ、`/api/auth` への総当たりを軽減する。

## 背景

現状のダッシュボード認証は `DASHBOARD_PASSWORD` からそのままセッション署名鍵を導出しており、cookie が漏えいすると攻撃者がオフラインでパスワード候補を照合できる。また、`/api/auth` には試行回数制限がなく、共有パスワードに対するブルートフォース耐性が低い。個人利用のシンプルさは維持しつつ、最小限の変更で脆弱性を下げる必要がある。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | セッション署名鍵 | `DASHBOARD_COOKIE_SECRET` を新設し、cookie HMAC 鍵はこの値からのみ導出する | ログインパスワードと署名鍵を分離し、cookie からのオフライン推測を防ぐ |
| 2   | パスワード用途 | `DASHBOARD_PASSWORD` はログイン照合にのみ使う | 認証要素の責務分離 |
| 3   | レート制限方式 | `app/api/auth/route.ts` から呼ぶ module-local の best-effort レートリミッタを追加する | 追加インフラなしで現状より強い抑止を入れられる |
| 4   | レート制限単位 | クライアント識別子は `x-forwarded-for` の先頭 IP を優先し、取れない場合は `user-agent`、どちらもなければ `unknown` | Vercel / ローカルの双方で扱いやすい |
| 5   | 閾値 | `10分で5回失敗` したら `15分ブロック` | 個人ダッシュボード向けに十分強く、実装も単純 |
| 6   | ブロック時レスポンス | `429` + `Retry-After` ヘッダ + JSON エラー本文を返す | UI とログの両方で扱いやすい |
| 7   | 成功時処理 | 正常ログイン時は対象クライアントの失敗履歴をクリアする | 正常利用者の巻き込みを減らす |
| 8   | UI 表示 | ログイン画面は `401` と `429` を区別して表示する | 利用者に待機が必要な状態を伝える |
| 9   | テスト方針 | 純粋ロジックは Vitest で TDD、route/UI は既存パターンに沿った統合寄りテストで確認する | shared logic の回帰を抑えつつ実装コストを抑える |

## アーキテクチャ詳細

### 認証データフロー

```text
[Login Page]
   |
   | POST /api/auth
   v
[Auth Route]
   |
   +--> identifyClient(request)
   |
   +--> getRateLimitState(clientKey)
   |      |
   |      +--> blocked -> 429 + Retry-After
   |
   +--> verifyPassword(password)
          |
          +--> fail -> recordFailure(clientKey) -> 401
          |
          +--> success -> clearFailures(clientKey)
                          -> createSessionCookie()
                          -> Set-Cookie: dashboard-session=timestamp.signature
```

### セッション鍵の分離

現在:

```text
DASHBOARD_PASSWORD
  -> SHA256("cookie-secret:" + password)
  -> cookie HMAC key
```

変更後:

```text
DASHBOARD_PASSWORD
  -> verifyPassword() のみ

DASHBOARD_COOKIE_SECRET
  -> SHA256("cookie-secret:" + secret)
  -> cookie HMAC key
```

### レートリミッタの状態

`dashboard/lib/login-rate-limit.ts` に module-local `Map<string, AttemptState>` を持つ。

```ts
interface AttemptState {
  failures: number
  firstFailureAt: number
  blockedUntil: number | null
}
```

### クライアント識別

```ts
clientKey =
  first(request.headers.get("x-forwarded-for")) ??
  request.headers.get("user-agent") ??
  "unknown"
```

### レート制限の判定ルール

```text
WINDOW_MS = 10 * 60 * 1000
MAX_FAILURES = 5
BLOCK_MS = 15 * 60 * 1000

1. blockedUntil > now         -> blocked
2. firstFailureAt が window 外 -> failures をリセット
3. 失敗ごとに failures++
4. failures >= MAX_FAILURES   -> blockedUntil = now + BLOCK_MS
5. 成功時                     -> state 削除
```

### API 応答

失敗:

```json
{ "error": "パスワードが正しくありません" }
```

レート制限:

```json
{
  "error": "試行回数が多すぎます。しばらく待ってから再試行してください。",
  "retryAfter": 900
}
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/lib/auth.ts` | cookie 署名鍵の導出元を `DASHBOARD_COOKIE_SECRET` に分離 | 高 |
| `dashboard/app/api/auth/route.ts` | レート制限判定、`429` 応答、成功時クリア処理を追加 | 高 |
| `dashboard/app/login/page.tsx` | `429` 応答の表示分岐を追加 | 中 |
| `dashboard/.env.example` | `DASHBOARD_COOKIE_SECRET` を追加 | 小 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/lib/login-rate-limit.ts` | ログイン試行制限の純粋ロジック |
| `dashboard/__tests__/auth.test.ts` | cookie secret 分離の回帰テスト |
| `dashboard/__tests__/login-rate-limit.test.ts` | レートリミッタのユニットテスト |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/proxy.ts` | cookie 検証の呼び出し位置自体は変えず、`lib/auth.ts` 側で新 secret を使う |
| `dashboard/app/api/repos/route.ts` | 認証後のデータ取得ロジックに変更は不要 |
| `dashboard/app/api/plans/route.ts` | 同上 |
| `dashboard/lib/github.ts` | GitHub API クライアントは今回の hardening 対象外 |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `dashboard/lib/auth.ts` | 現行の cookie 生成・検証ロジック確認 |
| `dashboard/app/api/auth/route.ts` | 現行ログイン API の分岐確認 |
| `dashboard/app/login/page.tsx` | 現行ログイン UI のエラーハンドリング確認 |
| `dashboard/proxy.ts` | cookie 検証の利用箇所確認 |
| `dashboard/__tests__/github.test.ts` | dashboard 配下の Vitest 記述パターン確認 |
| `dashboard/.env.example` | 既存の環境変数記述スタイル確認 |
| `docs/PLAN/260409_dashboard-auth.md` | 初期認証仕様の設計意図確認 |
| `docs/PLAN/260409_dashboard-web-deploy/spec.md` | Vercel / 環境変数前提の確認 |

## タスクリスト

### 依存関係図

```text
Gate A: 認証責務の分離
├── Todo A1
└── Todo A2

Gate B: ログイン試行制限（Gate A 完了後）
├── Todo B1
└── Todo B2
```

### Gate A: 認証責務の分離

#### Todo A1: [TDD] cookie 署名鍵をログインパスワードから分離する

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/auth.ts`, `dashboard/__tests__/auth.test.ts`
  - **内容**: cookie 署名鍵を `DASHBOARD_COOKIE_SECRET` から導出し、`DASHBOARD_PASSWORD` はログイン照合専用にする
  - **実装詳細**:
    - `deriveSecret()` を cookie 用 secret 専用ロジックに変更し、`process.env.DASHBOARD_COOKIE_SECRET` を読む
    - 未設定時の失敗モードを明示する。`createSessionCookie()` は設定不備を throw、`verifySessionCookie()` は fail-closed で `false`
    - `verifyPassword()` は現状通り `DASHBOARD_PASSWORD` のみを比較対象にする
    - テストでは「同じ password でも cookie secret を変えると署名が変わる」「cookie secret 未設定時にセッション生成が失敗する」を確認する
    - 実装は既存の Web Crypto パターンを維持し、`node:crypto` へ戻さない
  - **理由**: パスワードと cookie 署名鍵を分離しない限り、cookie 漏えい時のオフライン推測リスクが残る
  - **検証方法**: `cd dashboard && npm test -- auth`
  - **[TDD]**: auth helper は入出力が明確で Vitest で検証可能
  - **依存**: なし

- [ ] **Step 2 — Review A1**
  > **Review A1**:
  > - 判定:
  > - 指摘:

#### Todo A2: 環境変数定義と運用前提を更新する

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/.env.example`
  - **内容**: `DASHBOARD_COOKIE_SECRET` を追加し、既存 `DASHBOARD_PASSWORD` との役割分担を明記する
  - **実装詳細**:
    - `.env.example` に `DASHBOARD_COOKIE_SECRET=your_random_secret_here` を追加
    - コメントで「パスワードとは別のランダム値」「cookie 署名専用」であることを書く
    - `GITHUB_TOKEN` / `DASHBOARD_PASSWORD` の既存記法に合わせる
  - **理由**: 実装だけ分離しても、運用者が同じ値を再利用すると hardening 効果が落ちる
  - **検証方法**: `cd dashboard && rg -n "DASHBOARD_COOKIE_SECRET|cookie 署名" .env.example`
  - **依存**: Todo A1

- [ ] **Step 2 — Review A2**
  > **Review A2**:
  > - 判定:
  > - 指摘:

**Gate A 通過条件**: cookie 署名鍵が `DASHBOARD_COOKIE_SECRET` のみから導出され、環境変数の役割分離がコードと `.env.example` に反映されていること。

### Gate B: ログイン試行制限

#### Todo B1: [TDD] login rate limiter を追加する

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/login-rate-limit.ts`, `dashboard/__tests__/login-rate-limit.test.ts`
  - **内容**: login 試行失敗回数を管理し、一定回数超過でブロックする純粋ロジックを追加する
  - **実装詳細**:
    - `getClientKey(headers)`, `getRateLimitState(clientKey, now)`, `recordFailure(clientKey, now)`, `clearFailures(clientKey)` を export する
    - `WINDOW_MS=10分`, `MAX_FAILURES=5`, `BLOCK_MS=15分` を定数化する
    - module-local `Map` を使い、window 外の stale state は適宜リセットする
    - テストでは「window 内で 5 回失敗すると blocked」「window 外で失敗回数がリセット」「成功で state が消える」を確認する
  - **理由**: route 内に直接ロジックを書くと回帰テストが難しくなるため、純粋ロジックとして切り出して固める
  - **検証方法**: `cd dashboard && npm test -- login-rate-limit`
  - **[TDD]**: レート制限ロジックは純粋関数で明確に検証可能
  - **依存**: Gate A

- [ ] **Step 2 — Review B1**
  > **Review B1**:
  > - 判定:
  > - 指摘:

#### Todo B2: auth route と login UI にレート制限を統合する

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/app/api/auth/route.ts`, `dashboard/app/login/page.tsx`
  - **内容**: `/api/auth` にレート制限を適用し、UI で `429` を区別表示する
  - **実装詳細**:
    - route 冒頭で clientKey を算出し、blocked 中なら `429` と `Retry-After` を返す
    - パスワード不一致時は `recordFailure()` を呼び、閾値超過時は次回以降 block されるようにする
    - 成功時は `clearFailures(clientKey)` を呼んで state を解放する
    - レート制限時の JSON は `error` と `retryAfter` を返す
    - login page は `response.status === 429` の場合、待機を促す文言を表示する。`401` の既存文言は維持する
    - 手動検証では `curl` で連続失敗 -> `429`、成功ログイン -> カウンタ解放、の 2 系統を確認する
  - **理由**: API だけ制限しても UI が区別表示できないと、通常の認証失敗と見分けがつかず運用で混乱する
  - **検証方法**:
    - `cd dashboard && npm run dev`
    - `curl -i -X POST http://127.0.0.1:3000/api/auth -H 'Content-Type: application/json' --data '{"password":"wrong"}'`
    - 閾値超過後に `429` と `Retry-After` が返ることを確認する
  - **依存**: Todo B1

- [ ] **Step 2 — Review B2**
  > **Review B2**:
  > - 判定:
  > - 指摘:

**Gate B 通過条件**: `/api/auth` が失敗回数を追跡して `429` を返せること、およびログイン UI がブロック状態を区別表示できること。

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| module-local レート制限は分散インスタンス間で共有されない | Vercel の複数インスタンスでは厳密な global 制限にならない | 将来必要になれば Redis / Upstash など外部ストアに移行する |
| 共有パスワード方式自体は単一要素認証のまま | パスワード漏えい時は全利用者に影響 | 今回は被害軽減に留め、必要時は OAuth / IdP 導入を別仕様で行う |
| `DASHBOARD_COOKIE_SECRET` の運用が甘いと hardening 効果が落ちる | 弱い secret の再利用で防御が弱くなる | Preflight でランダム値設定を必須化し、`.env.example` に役割を明記する |
