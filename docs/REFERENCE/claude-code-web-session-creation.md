# ダッシュボードから Claude Code Web セッションを作成できるか — 技術調査

調査日: 2026-04-15（初版）/ 2026-04-15 改訂 2（API 制約を実証検証して修正）
目的: 自前ダッシュボード上の Prompt Input フォームから、Claude Code Web (claude.ai/code) のセッションを起動できるかを確認する。

---

## 結論

**「fire 時にユーザーが 1 リポジトリを指定して単発セッションを起動する」要件は、現行の Routines API では実現できない。**

- Routines API (`/fire` エンドポイント) は 2026-04-14 に公開された外部起動用公式手段ではあるが、ルーチンは **作成時に対象リポジトリを固定バインド** する設計。
- `/fire` のリクエストボディは `{text}` のみで、**repo を fire 時に指定するパラメータが存在しない**。
- 複数リポジトリをひもづけたルーチンを fire すると、**選択した全 repo に並列でセッションが fan-out** する（2026-04-15 実証: 3 repo 登録 → 1 fire → 共通サフィックスの `claude/*-xxxx` ブランチで 3 セッション同時生成）。
- 回避策として「repo ごとにルーチンを作成し、repo → trigger/token を 1:1 マップする」運用は理論上可能だが、ルーチン管理の公開 API は存在せず、repo 追加ごとに手動で claude.ai 上のルーチン作成 + トークン発行が必要で、多 repo 運用では非現実的。

**最終判断**: 現 API 仕様のまま「サイドバーで選んだ 1 repo に投げる」ダッシュボード UX を組むのは不適切。per-fire repo selection が API に入るのを待つか、UX を「fan-out ランチャー」に再設計する必要がある。

---

## 利用可能な経路

### ⚠️ 1. Routines API (唯一の公式起動経路だが要件適合しない)

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

### ✅ 2. CLI 経由 (補助的)

`claude --remote "<prompt>"` で cloud session を起動できる。サーバー側で CLI を spawn する設計も可能だが、依存が重く Claude アカウント認証を runtime にどう持ち込むかという運用課題もあるため、自前サーバーレス基盤からの利用は実装コストが高い。

### ❌ 3. URL パラメータ方式 (使えない)

`https://claude.ai/code?repo=...&prompt=...&branch=...` のような pre-fill URL を作る案は、Anthropic が **"not planned" として明示的に却下** している (Issue #19023, 2026-01-18 close)。

### ❌ 4. Claude Code Web 直接の REST セッション API (存在しない)

claude.ai/code の UI に表示されるセッションを直接作る一般公開 API は提供されていない。`platform.claude.com` の Managed Agents API (`/v1/sessions`) は別系統で、claude.ai/code 上には現れない。

---

## 設計上の制約

| 項目 | 制約 | 回避策 |
|---|---|---|
| **repo 指定（致命的）** | ルーチン作成時に repo を固定。`/fire` body に repo パラメータなし。multi-repo routine は fan-out 動作 | **現 API では根本的な回避不可**。repo ごとに 1 ルーチン + 1 トークンを用意して呼び分ければ理論上 1:1 起動は可能だが、ルーチン自体を作成する公開 API がなく手動作成が必要。多 repo 運用には非現実的 |
| **ブランチ指定** | ルーチンは常にデフォルトブランチからクローン (Issue #10018 で要望中・未実装) | プロンプト本文で `git checkout <branch>` を指示。cloud session 内で git は実行可能 |
| **プロンプト** | ルーチン作成時に保存されたプロンプトが主、`/fire` の `text` は「追加コンテキスト」扱い | ルーチン側を「以下の指示を実行せよ: $TEXT」のような薄いシェル状にしておき、実プロンプトを毎回 `text` で送る |
| **ステータス** | Research Preview。`experimental-cc-routine-2026-04-01` ベータヘッダ必須 | API shape は変わり得る。breaking change はベータヘッダ更新で通知される (旧 2 バージョンまで互換維持) |
| **トークン** | ルーチンごとに発行、画面で **1 度しか表示されない** | secret store に必ず保管。失くしたら Regenerate / Revoke で再発行 |
| **アカウント** | 個人 claude.ai アカウントに紐づく | commit / PR / Slack / Linear などコネクタ操作はそのユーザーの identity で実行される |
| **ZDR 組織** | Zero Data Retention 有効組織は cloud session 自体使用不可 | なし (組織ポリシー次第) |
| **レート制限** | アカウント単位の daily run cap あり、サブスク usage limit も共有 | extra usage で metered overage が可能 (Settings > Billing) |
| **ブランチ push** | デフォルトでは `claude/` プレフィックスのブランチにのみ push 可 | リポジトリごとに **Allow unrestricted branch pushes** を有効化すれば任意ブランチへ push 可 |
| **ルーチン管理 API** | ルーチン自身の CRUD（作成 / 削除 / repo 付替え）を行う公開 API なし | UI 手動操作のみ。多 repo 運用でのセットアップ自動化は不可 |

---

## 採れるアーキテクチャ案（どれも要件とは完全一致しない）

### 案 A: 1 Routine : 1 Repo マッピング（手動セットアップ型）

```
Dashboard (Web UI)
  [repo select]  ─┐
  [prompt入力]    │
        ↓        │ repo → (triggerId, token) を lookup
  POST /fire ────┘ (backend の env に JSON マップで保存)
        ↓
  Anthropic Routines API: /routines/{trig_per_repo}/fire
        ↓
  選択 repo 1 つに紐づいた Cloud Session 起動
```

- 長所: ユーザー目線のセマンティクスは正しい（選んだ repo に投げる）
- 短所: repo ごとにルーチンを claude.ai で手動作成、トークンを 1 つずつ発行、env に追記する運用が必要。ルーチン管理 API がないので自動化不可。多 repo では非現実的。

### 案 B: Fan-out ランチャー（並列投入型）

```
Dashboard (Web UI)
  [repo を複数選択]  ─┐
  [共通プロンプト]    │
        ↓          │
  POST /fire ──────┘ (事前作成した multi-repo ルーチン 1 個に fire)
        ↓
  N 個の Cloud Session が fan-out で同時起動
```

- 長所: ルーチン 1 個で済む。セットアップが軽い。
- 短所: 「1 repo に投げる」UX ではなくなる。用途は「全 repo に同じメンテ作業を一斉投入」など限定的。

### 案 C: Park（見送り）

per-fire repo selection が API に入る or ルーチン管理 API が公開されるまで、ダッシュボード側の実装を見送る。Anthropic 側に Issue を起票して watch。

---

ダッシュボード実装側で共通して必要なもの:
- バックエンド: `/fire` を叩くための HTTP クライアント (トークンを env / secret 経由で読む)
- フロントエンド: 起動後の session URL 表示 / 新規タブで開く UI
- 案 A の場合: repo → 資格情報を解決する層と、repo 追加時の手順書

---

## 既存ダッシュボードへの統合観点

本リポジトリ (`dot-claude-dev`) の dashboard にこの機能を載せるかは、上記 3 案のどれを採るかに依存する:

- **案 A を採る場合**: repo → `{triggerId, token}` マップを env に JSON で持つ。`/api/sessions/launch` は body の `repo` から対応するトークンを引いて `/fire` を呼ぶ。repo 追加手順は README 化必須。
- **案 B を採る場合**: サイドバーで選んだ複数 repo のうち登録済みのみを fire 対象にする。UI コピーと挙動を「全選択 repo に一斉起動」と明示する必要あり（想定誤りで 1 repo だけ呼ばれると思うユーザーが混乱する）。
- **案 C を採る場合**: コミットせず見送り。per-fire repo selection が API に追加されたタイミングで再評価。

共通で必要なインフラ:
- Routines トークン保管 (Vercel env var など)
- `/api/sessions/launch` のような薄い proxy エンドポイント (CORS と secret 保護)
- 起動後の session URL 表示 / 新規タブで開く

---

## 参考リンク

- [Use Claude Code on the web (公式ドキュメント)](https://code.claude.com/docs/en/claude-code-on-the-web)
- [Automate work with routines (公式ドキュメント)](https://code.claude.com/docs/en/routines)
- [Introducing routines in Claude Code (リリース告知, 2026-04-14)](https://claude.com/blog/introducing-routines-in-claude-code)
- [Issue #19023 — URL parameters for Claude Code Web (closed, not planned)](https://github.com/anthropics/claude-code/issues/19023)
- [Issue #10018 — Start sessions from non-default branches (open)](https://github.com/anthropics/claude-code/issues/10018)
- [Issue #29145 — VS Code 拡張向け URI handler (Web 版とは別件)](https://github.com/anthropics/claude-code/issues/29145)
