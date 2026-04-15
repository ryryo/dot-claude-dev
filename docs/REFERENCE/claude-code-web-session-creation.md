# ダッシュボードから Claude Code Web セッションを作成できるか — 技術調査

調査日: 2026-04-15
目的: 自前ダッシュボード上の Prompt Input フォームから、Claude Code Web (claude.ai/code) のセッションを起動できるかを確認する。

---

## 結論

**技術的に可能。** Anthropic が 2026-04-14 にリリースした **Routines API (`/fire` エンドポイント)** が、外部システムから Claude Code Web セッションを起動するための公式手段となる。

ただし「ダッシュボードからブランチ + 任意プロンプトを送る」要件には設計上の制約があるため、回避策が必要。

---

## 利用可能な経路

### ✅ 1. Routines API (推奨・正攻法)

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

返ってきた `claude_code_session_url` をブラウザで開けばそのまま Claude Code Web のセッションがリアルタイムで動いている。

#### ダッシュボード側の典型フロー

1. 事前に「汎用エージェント」ルーチンを 1 個作成（API トリガー有効化、トークンを発行・保管）
2. ダッシュボード UI でユーザーが「ブランチ名 + プロンプト」を入力
3. バックエンドが `/fire` に POST。`text` フィールドに `Branch: foo\n\nTask: <prompt>` のようにまとめて詰める
4. レスポンスの `claude_code_session_url` をダッシュボードに表示、または新規タブでリダイレクト

### ✅ 2. CLI 経由 (補助的)

`claude --remote "<prompt>"` で cloud session を起動できる。サーバー側で CLI を spawn する設計も可能だが、依存が重いため Routines API のほうがクリーン。

### ❌ 3. URL パラメータ方式 (使えない)

`https://claude.ai/code?repo=...&prompt=...&branch=...` のような pre-fill URL を作る案は、Anthropic が **"not planned" として明示的に却下** している (Issue #19023, 2026-01-18 close)。

### ❌ 4. Claude Code Web 直接の REST セッション API (存在しない)

claude.ai/code の UI に表示されるセッションを直接作る一般公開 API は提供されていない。`platform.claude.com` の Managed Agents API (`/v1/sessions`) は別系統で、claude.ai/code 上には現れない。

---

## 設計上の制約

| 項目 | 制約 | 回避策 |
|---|---|---|
| **ブランチ指定** | ルーチンは常にデフォルトブランチからクローン (Issue #10018 で要望中・未実装) | プロンプト本文で `git checkout <branch>` を指示。cloud session 内で git は実行可能 |
| **プロンプト** | ルーチン作成時に保存されたプロンプトが主、`/fire` の `text` は「追加コンテキスト」扱い | ルーチン側を「以下の指示を実行せよ: $TEXT」のような薄いシェル状にしておき、実プロンプトを毎回 `text` で送る |
| **ステータス** | Research Preview。`experimental-cc-routine-2026-04-01` ベータヘッダ必須 | API shape は変わり得る。breaking change はベータヘッダ更新で通知される (旧 2 バージョンまで互換維持) |
| **トークン** | ルーチンごとに発行、画面で **1 度しか表示されない** | secret store に必ず保管。失くしたら Regenerate / Revoke で再発行 |
| **アカウント** | 個人 claude.ai アカウントに紐づく | commit / PR / Slack / Linear などコネクタ操作はそのユーザーの identity で実行される |
| **ZDR 組織** | Zero Data Retention 有効組織は cloud session 自体使用不可 | なし (組織ポリシー次第) |
| **レート制限** | アカウント単位の daily run cap あり、サブスク usage limit も共有 | extra usage で metered overage が可能 (Settings > Billing) |
| **ブランチ push** | デフォルトでは `claude/` プレフィックスのブランチにのみ push 可 | リポジトリごとに **Allow unrestricted branch pushes** を有効化すれば任意ブランチへ push 可 |

---

## 推奨アーキテクチャ

```
┌──────────────────────┐         ┌────────────────────────────┐
│ Dashboard (Web UI)   │         │ Anthropic Cloud            │
│                      │         │                            │
│  [ブランチ選択]      │         │  ┌──────────────────────┐  │
│  [プロンプト入力]    │  POST   │  │ Routine (汎用)       │  │
│       ↓              │ ─/fire→ │  │ - prompt: $TEXT 実行 │  │
│  POST /fire          │         │  │ - API trigger ON     │  │
│  body: {             │         │  └──────┬───────────────┘  │
│   "text":            │         │         ↓ session 起動      │
│    "Branch: foo\n\n  │         │  ┌──────────────────────┐  │
│     Task: ..."       │         │  │ Cloud Session        │  │
│  }                   │         │  │ (claude.ai/code)     │  │
│       ↓              │ ←────── │  └──────────────────────┘  │
│  session_url を表示  │         │                            │
└──────────────────────┘         └────────────────────────────┘
```

事前準備:
1. claude.ai/code/routines で「汎用エージェント」ルーチンを 1 個作成
2. 保存プロンプトは「以下の指示を実行せよ。`Branch:` 行があれば最初に `git checkout <branch>` を実行」のような薄いシェル
3. 対象リポジトリを登録、必要なら **Allow unrestricted branch pushes** を有効化
4. API trigger を追加し、トークンを発行・ダッシュボードのバックエンド secret store に保管

ダッシュボード実装側で必要なもの:
- バックエンド: `/fire` を叩くための HTTP クライアント (トークンを env / secret 経由で読む)
- フロントエンド: ブランチ選択 UI (リポジトリの branch 一覧は GitHub API から取得) + プロンプト入力欄 + 起動後の session URL 表示

---

## 既存ダッシュボードへの統合観点

本リポジトリ (`dot-claude-dev`) の dashboard は既に GitHub API キャッシュを持っているため、ブランチ一覧表示は流用可能。新規追加が必要なのは:

- Routines トークン保管 (Vercel env var など)
- `/api/launch-session` のような薄い proxy エンドポイント (CORS と secret 保護)
- フォーム UI (ブランチ select + prompt textarea + 送信ボタン)
- 起動後の session URL 表示 / 新規タブで開く

---

## 参考リンク

- [Use Claude Code on the web (公式ドキュメント)](https://code.claude.com/docs/en/claude-code-on-the-web)
- [Automate work with routines (公式ドキュメント)](https://code.claude.com/docs/en/routines)
- [Introducing routines in Claude Code (リリース告知, 2026-04-14)](https://claude.com/blog/introducing-routines-in-claude-code)
- [Issue #19023 — URL parameters for Claude Code Web (closed, not planned)](https://github.com/anthropics/claude-code/issues/19023)
- [Issue #10018 — Start sessions from non-default branches (open)](https://github.com/anthropics/claude-code/issues/10018)
- [Issue #29145 — VS Code 拡張向け URI handler (Web 版とは別件)](https://github.com/anthropics/claude-code/issues/29145)
