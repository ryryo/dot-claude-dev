# ダッシュボードから Claude Code Web セッションを作成できるか — 技術調査

調査日: 2026-04-15（初版）/ 2026-04-15 改訂 2（Routines API 制約を実証）/ 2026-04-15 改訂 3（`claude --remote` を発見し主経路に位置付け）
目的: 自前ダッシュボード上の Prompt Input フォームから、Claude Code Web (claude.ai/code) のセッションを起動できるかを確認する。

---

## 結論

**「fire 時に repo + branch + 任意プロンプトを指定して単発セッションを起動する」要件は、`claude --remote` CLI を使えば実現可能。Routines API では不可能。**

### 採用すべき経路: `claude --remote` CLI

- Anthropic 公式 CLI の `claude --remote "<prompt>"` が「**カレントディレクトリの GitHub remote をカレントブランチで** クローンして claude.ai/code 上に新規セッションを生成する」公式コマンド。
- 1 コマンド = 1 セッション（並列起動も可能）、repo / branch を呼び出し時に指定可能（cwd と current branch を使うため）。
- 公式記述: *"`--remote` works with a single repository at a time."*（[code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web)）
- ヘッドレス認証は `CLAUDE_CODE_OAUTH_TOKEN` 環境変数で対応（`claude setup-token` で発行、有効期限 1 年）。

### 不採用となった経路: Routines API

- Routines API (`/fire` エンドポイント) は 2026-04-14 に公開された外部起動用公式手段だが、ルーチンは **作成時に対象リポジトリを固定バインド** する設計。
- `/fire` のリクエストボディは `{text}` のみで、**repo を fire 時に指定するパラメータが存在しない**（[公式 API リファレンス](https://platform.claude.com/docs/en/api/claude-code/routines-fire) で確定）。
- 複数リポジトリをひもづけたルーチンを fire すると、**選択した全 repo に並列でセッションが fan-out** する（2026-04-15 実証: 3 repo 登録 → 1 fire → 共通サフィックスの `claude/*-xxxx` ブランチで 3 セッション同時生成）。
- 回避策として「repo ごとにルーチンを作成し、repo → trigger/token を 1:1 マップする」運用は理論上可能だが、ルーチン管理の公開 API は存在せず、repo 追加ごとに手動で claude.ai 上のルーチン作成 + トークン発行が必要で、多 repo 運用では非現実的。

### 最終判断

ダッシュボード実装は **`claude --remote` CLI を spawn する自前バックエンド** をベースに設計する。Vercel serverless では永続認証ファイルとファイルシステムが扱えないため、永続実行環境（Fly.io / Railway / VPS / dev 機など）が必須。Routines API ベースの旧計画 (`docs/PLAN/260415_dashboard-claude-web-trigger/`) は破棄して再設計する。

---

## 利用可能な経路

### ✅ 1. `claude --remote` CLI（採用経路）

公式 CLI (`@anthropic-ai/claude-code`) の `--remote` フラグで、カレントディレクトリの GitHub リポジトリ + カレントブランチをクローンして claude.ai/code 上にセッションを生成する。

```bash
# 単発セッション起動（current dir の repo + branch + プロンプトで）
claude --remote "Fix the failing tests in tests/auth/"

# 複数を並列で投げる
claude --remote "Fix the flaky test in auth.spec.ts"
claude --remote "Update the API documentation"
```

#### 主要な事実

| 項目 | 内容 |
| --- | --- |
| repo の指定方法 | カレントディレクトリの git remote を使う（呼び出し時にディレクトリを cd するだけで指定可能） |
| branch の指定方法 | カレントブランチを使う（呼び出し前に `git checkout <branch>` で切り替える） |
| repo per fire | 必ず 1 repo（複数 repo を 1 コマンドで投げることは不可） |
| 並列実行 | 各 `--remote` 起動は独立したセッションを作る。並列 OK |
| 認証 | claude.ai サブスクリプション OAuth、ヘッドレスは `CLAUDE_CODE_OAUTH_TOKEN` 環境変数 |
| GitHub access | 通常: GitHub App or `/web-setup` で連携。fallback: ローカルバンドル送信 (100MB 以下) |
| 戻り値 | セッション URL を含むテキスト出力（stdout 解析で URL を取得） |

#### ヘッドレス認証

`claude setup-token` を一度だけ対話的に実行 → 1 年有効な OAuth トークンが発行される → CI / Docker / 自前サーバーでは `CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...` で利用する。

#### 既知の制約

- **永続ファイルシステム必須**: Vercel serverless のような ephemeral 環境では `~/.claude/` の認証情報を毎リクエストで失うため不適。
- **Issue #28827**: 非対話モードでは OAuth トークンの自動 refresh が走らず、long-running daemon 内で ~10-15 分後に 401 になる事例あり。毎リクエスト spawn → exit する設計（fork-and-die モデル）なら回避可能。
- **GitHub Enterprise 非対応**（ローカルバンドルなら可）/ **GitLab・Bitbucket 非対応**（バンドル経由なら起動可だが push 不可）。

### ⚠️ 2. Routines API (要件適合しない)

事前に claude.ai 上で「ルーチン」を作成し、API トリガーを有効化してトークンを発行。外部から HTTP POST で起動する。

```http
POST https://api.anthropic.com/v1/claude_code/routines/{trig_id}/fire
Authorization: Bearer sk-ant-oat01-xxxxx
anthropic-beta: experimental-cc-routine-2026-04-01
anthropic-version: 2023-06-01
Content-Type: application/json

{"text": "<実行時に渡す追加コンテキスト>"}
```

レスポンス例:

```json
{
  "type": "routine_fire",
  "claude_code_session_id": "session_01HJKLMNOPQRSTUVWXYZ",
  "claude_code_session_url": "https://claude.ai/code/session_01HJKLMNOPQRSTUVWXYZ"
}
```

返ってきた `claude_code_session_url` をブラウザで開けばそのまま Claude Code Web のセッションが動いている。

#### 重要: ルーチンは repo を作成時に固定バインドする

- 新規ルーチン作成画面で「リポジトリを選択してください」は **必須項目**。repo を指定せずに保存不可。
- 複数 repo の選択は可能（タグ UI で任意個追加できる）。
- ただし `/fire` には repo 指定パラメータがなく、**fire 時にどの repo を対象にするかを呼び出し側が選ぶことはできない**。
- 結果として:
  - 1 repo 登録ルーチン → fire 1 回で 1 セッション
  - N repo 登録ルーチン → fire 1 回で **N セッション並列 fan-out**（2026-04-15 実証済み）

#### 実証データ（2026-04-15）

`dot-claude-dev generic agent` ルーチンに `ryryo/ai-codlnk.com` / `ryryo/dot-claude-dev` / `ryryo/lead-form` の 3 repo を登録して `/fire` を 1 回呼んだところ、共通サフィックス `cmcWL` を持つ 3 ブランチ (`claude/epic-heisenberg-cmcWL` / `claude/gallant-ritchie-cmcWL` / `claude/kind-hamilton-cmcWL`) で 3 セッションが同時に動き始めた。単一 fire ID から repo ごとに枝分かれしている。

#### このため「fire 時に repo 指定」は実現不能

`/fire` のリクエストに `repo` パラメータがあれば動的選択可能だが、現時点で Research Preview 仕様に該当フィールドは存在しない。

### ❌ 3. URL パラメータ方式 (使えない)

`https://claude.ai/code?repo=...&prompt=...&branch=...` のような pre-fill URL を作る案は、Anthropic が **"not planned" として明示的に却下** している (Issue #19023, 2026-01-18 close)。

### ❌ 4. Claude Code Web 直接の REST セッション API (存在しない)

claude.ai/code の UI に表示されるセッションを直接作る一般公開 API は提供されていない。`platform.claude.com` の Managed Agents API (`/v1/sessions`) は別系統で、claude.ai/code 上には現れない。

---

## 設計上の制約

### `claude --remote` CLI の制約

| 項目 | 制約 | 回避策 |
|---|---|---|
| **実行環境** | CLI spawn が必須。`~/.claude/` 配下の認証キャッシュ or `CLAUDE_CODE_OAUTH_TOKEN` 環境変数が参照できる永続 FS 環境が前提 | Fly.io / Railway / VPS / 手元マシン等の永続環境にバックエンドを配置。Vercel serverless 等 ephemeral 環境は不可 |
| **認証** | claude.ai サブスクリプション OAuth。対話ログイン前提 | `claude setup-token` を手元で 1 回実行 → 1 年有効な `sk-ant-oat01-...` を取得し `CLAUDE_CODE_OAUTH_TOKEN` に設定 |
| **OAuth refresh** | 非対話モードで refresh が走らず、long-running daemon 内で ~10-15 分後に 401 になる事例あり (Issue #28827) | 毎リクエスト spawn → exit する fork-and-die 設計にすれば回避可能 |
| **ブランチ指定** | カレントブランチを使う | 呼び出し前にバックエンド側で対象 repo を clone して `git checkout <branch>` |
| **GitHub access** | GitHub App 連携 or `/web-setup` か、100MB 以下のローカルバンドル送信のどちらか | バックエンドが repo を ephemeral clone → bundle として送る fallback が最も汎用的 |
| **セッション URL** | stdout にテキストで出力される | CLI の標準出力を正規表現でパースしてセッション URL を抽出 |
| **GitHub Enterprise** | 公式連携なし。ローカルバンドル経由ならセッション起動は可能だが push 不可 | 社内向けに必要なら別の経路を検討（本リポジトリのダッシュボードでは当面非対応） |
| **GitLab / Bitbucket** | 同上（セッション起動のみ、push 不可） | 同上 |
| **ブランチ push** | デフォルトでは `claude/` プレフィックスのブランチにのみ push 可 | リポジトリごとに **Allow unrestricted branch pushes** を有効化すれば任意ブランチへ push 可 |
| **アカウント** | 個人 claude.ai アカウントに紐づく | commit / PR / Slack / Linear などコネクタ操作はそのユーザーの identity で実行される |
| **ZDR 組織** | Zero Data Retention 有効組織は cloud session 自体使用不可 | なし (組織ポリシー次第) |

### Routines API の制約（参考: 不採用経路）

| 項目 | 制約 | 回避策 |
|---|---|---|
| **repo 指定（致命的）** | ルーチン作成時に repo を固定。`/fire` body に repo パラメータなし。multi-repo routine は fan-out 動作 | **現 API では根本的な回避不可**。repo ごとに 1 ルーチン + 1 トークンを用意して呼び分ければ 1:1 起動は可能だが、ルーチン自体を作成する公開 API がなく手動作成が必要。多 repo 運用には非現実的 |
| **ブランチ指定** | ルーチンは常にデフォルトブランチからクローン (Issue #10018) | プロンプト本文で `git checkout <branch>` を指示 |
| **プロンプト** | ルーチン側保存プロンプトが主、`/fire` の `text` は「追加コンテキスト」扱い | ルーチンを薄いシェル (`$TEXT` を流すだけ) にしておく |
| **ステータス** | Research Preview。`experimental-cc-routine-2026-04-01` ベータヘッダ必須 | ベータヘッダ更新で通知 (旧 2 バージョンまで互換) |
| **トークン** | ルーチンごとに発行、画面で **1 度しか表示されない** | secret store に保管。失くしたら Regenerate / Revoke |
| **ルーチン管理 API** | ルーチン自身の CRUD を行う公開 API なし | UI 手動操作のみ |

---

## 採れるデプロイ構成案（`claude --remote` ベース）

共通の処理フロー:

```
Dashboard FE (Web UI)
  [repo select]  ─┐
  [branch select] │
  [prompt入力]    │
        ↓        │
  POST /api/sessions/launch ─→ Backend (要永続 FS)
                                  ↓
                                1. 対象 repo を ephemeral clone
                                2. git checkout <branch>
                                3. CLAUDE_CODE_OAUTH_TOKEN を env に注入
                                4. claude --remote "<prompt>" を spawn
                                5. stdout から session URL を抽出
                                  ↓
                                { sessionUrl } を返す
        ↓
  新規タブで session URL を開く
```

### 案 S1: Fly.io / Railway 一体型（推奨）

FE + Backend を単一の永続コンテナで動かす。

- 長所: `~/.claude/` をコンテナボリュームで持てる。`CLAUDE_CODE_OAUTH_TOKEN` は env で注入。spawn モデルが素直に動く
- 短所: 永続ホストのコストが発生 (Fly.io 無料枠で収まる規模)
- 向き: 複数 repo を日常的に叩く本命運用

### 案 S2: Vercel FE + 外部 Worker

現ダッシュボードの Vercel デプロイは維持しつつ、`/api/sessions/launch` だけを外部 worker (Fly.io / Railway / Cloudflare Workers + 永続ストレージ持ち) にルーティングする。

- 長所: 既存の Vercel 資産 (auth middleware, 静的 build) を活かせる
- 短所: 2 ホストの構成管理、認証 cookie を worker まで渡すか署名付き内部 API にするかの設計が増える
- 向き: 段階移行期。S1 に踏み切る前の実験環境

### 案 S3: ローカル開発機専用

バックエンドをローカル (macOS / Linux) で常駐させ、ダッシュボードからは `http://localhost:<port>` を叩く。

- 長所: 追加インフラ不要。手元の `~/.claude/` 認証をそのまま利用可能
- 短所: 端末稼働中しか使えない。他端末・他人からアクセス不可
- 向き: 1 人運用 or PoC 段階

---

## 既存ダッシュボードへの統合観点

本リポジトリ (`dot-claude-dev`) の dashboard に載せる場合、案 S1 を採るのが最短:

- **バックエンド**: Fly.io / Railway 上の Next.js app に `/api/sessions/launch` Route Handler を追加。`@anthropic-ai/claude-code` を依存に含め、spawn で `claude --remote` を叩く
- **認証**: `CLAUDE_CODE_OAUTH_TOKEN` を env var に格納。`claude setup-token` は手元で 1 回実行して発行
- **repo のローカル作業ディレクトリ**: リクエスト毎に `/tmp/launches/<uuid>` に対象 repo を shallow clone → `git checkout <branch>` → そこを cwd にして spawn → 終了後に削除 (fork-and-die モデル)
- **GitHub token**: repo を clone するため、既存の `GITHUB_TOKEN` (ダッシュボード用) を流用するか、別途 deploy key / PAT を使う
- **UI**: 既存のサイドバー repo 選択を流用。branch は GitHub API (既存) から一覧取得してプルダウン化。プロンプト入力は shadcn の PromptInput、起動後は sonner toast で session URL をリンク表示
- **Routines 用 env (`ANTHROPIC_ROUTINE_TRIGGER_ID` / `ANTHROPIC_ROUTINE_TOKEN`)**: 旧計画で `.env.example` に追加済みだが、本設計では **不要**。新設計確定時に削除する

---

## 参考リンク

- [Use Claude Code on the web (公式ドキュメント)](https://code.claude.com/docs/en/claude-code-on-the-web)
- [Automate work with routines (公式ドキュメント)](https://code.claude.com/docs/en/routines)
- [Introducing routines in Claude Code (リリース告知, 2026-04-14)](https://claude.com/blog/introducing-routines-in-claude-code)
- [Issue #19023 — URL parameters for Claude Code Web (closed, not planned)](https://github.com/anthropics/claude-code/issues/19023)
- [Issue #10018 — Start sessions from non-default branches (open)](https://github.com/anthropics/claude-code/issues/10018)
- [Issue #29145 — VS Code 拡張向け URI handler (Web 版とは別件)](https://github.com/anthropics/claude-code/issues/29145)
