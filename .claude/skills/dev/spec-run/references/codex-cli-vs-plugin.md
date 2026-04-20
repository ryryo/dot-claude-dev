# Native Codex CLI vs codex-plugin-cc プラグイン

spec-run の Codex モードで使う2種類のインターフェースの違いと使い分け。

## 概要

| | Native Codex CLI | codex-plugin-cc companion |
|--|----------------|--------------------------|
| 呼び出し方 | `codex <subcommand>` | `node "$CODEX_COMPANION" <subcommand>` |
| インストール | `npm i -g @openai/codex` | Claude Code プラグイン |
| 主な用途 | コードレビュー（read-only） | タスク委任・レビュー実行の orchestration |

## コマンド比較

### review（コードレビュー）

| 目的 | コマンド | フォーカステキスト |
|------|---------|-----------------|
| 標準レビュー（VERIFY 推奨） | `codex review - < .tmp/focus.md` | stdin で渡す（長文 OK） |
| コミット指定 | `codex review --commit <SHA>` | 不可（排他的引数） |
| ブランチ比較 | `codex review --base <BRANCH>` | 不可（排他的引数） |
| 未コミット変更 | `codex review --uncommitted` | 不可（排他的引数） |
| 設計批判レビュー | `node "$CODEX_COMPANION" adversarial-review [focus text]` | inline 引数で渡す |

> **companion v1.0.2 変更**: `node "$CODEX_COMPANION" review` はフォーカステキストを廃止（built-in reviewer のみ）。カスタム指示付きレビューは native CLI（stdin）か `adversarial-review` を使う。

### task（実装委任）

companion 専用。native CLI には対応するコマンドなし。

```bash
# 通常実行
node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-prompt.md

# バックグラウンド並列実行
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-1.md
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-2.md
node "$CODEX_COMPANION" status --wait

# 修正（前回タスクを resume）
node "$CODEX_COMPANION" task --write --resume-last --prompt-file .tmp/codex-fix-prompt.md
```

## 出力フォーマットの違い

### Native `codex review` の出力

P1/P2/P3 ラベル付きテキストコメント:

```
[P1] auth token が localStorage に平文保存されている — XSS で漏洩リスク
[P2] エラーハンドリングが catch なしで undefined を返している
[P3] 変数名 `d` が意図を伝えていない
```

spec-run の PASS/FAIL 判定に直結（P1 あり → FAIL, P3 のみ → PASS）。

### Companion `adversarial-review` の出力

構造化 JSON:

```json
{
  "verdict": "approve",
  "summary": "No blocking issues found.",
  "findings": []
}
```

verdict は `approve` / `reject` の2値。spec-run の P1/P2/P3 ロジックとは別フォーマット。

## spec-run での使い分け

| ステップ | 使うコマンド | 理由 |
|---------|------------|------|
| Step 1 IMPL | `node "$CODEX_COMPANION" task --write --prompt-file` | 実装委任は companion のみ |
| Step 2 VERIFY | `codex review - < .tmp/focus.md` | フォーカステキスト + P1/P2/P3 判定が必要 |
| Step 3 FIX | `node "$CODEX_COMPANION" task --write --resume-last --prompt-file` | 前回タスクの resume が必要 |

`adversarial-review` は「設計判断を問い直す」用途。VERIFY（仕様適合確認）には native `codex review` が適切。

## companion サブコマンド一覧（v1.0.2）

```
setup [--enable-review-gate|--disable-review-gate]
review [--wait|--background] [--base <ref>] [--scope <auto|working-tree|branch>]
adversarial-review [--wait|--background] [--base <ref>] [--scope <auto|working-tree|branch>] [focus text]
task [--background] [--write] [--resume-last|--resume|--fresh] [--model <model>] [--effort <none|minimal|low|medium|high|xhigh>] [prompt]
status [job-id] [--all] [--json]
result [job-id] [--json]
cancel [job-id] [--json]
```

## Claude Code スラッシュコマンドとの対応

| スラッシュコマンド | companion 呼び出し | 備考 |
|-----------------|-----------------|------|
| `/codex:review` | `review`（フォーカスなし） | built-in reviewer のみ |
| `/codex:adversarial-review [text]` | `adversarial-review [text]` | 設計批判レビュー |
| `/codex:rescue` | `task --write` 相当 | バックグラウンドジョブ委任 |
| `/codex:status` | `status` | |
| `/codex:result` | `result` | |
| `/codex:cancel` | `cancel` | |
