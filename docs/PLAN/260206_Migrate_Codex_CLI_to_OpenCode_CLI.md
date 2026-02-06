# Codex CLI から OpenCode CLI への移行計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

## 概要
`.claude/skills/dev/` スキル内で使用しているCodex CLIの呼び出しを、OpenCode CLI（`opencode run -m openai/gpt-5.3-codex`）に移行する。

## 背景
- Codex CLIから OpenCode CLIへの移行が必要
- モデルも `gpt-5.2-codex` から最新の `gpt-5.3-codex` にアップグレード
- OpenCode CLIには `--sandbox` や `--full-auto` フラグが存在しないため、コマンド構文の変更が必要
- `docs/REFERENCE/opencode-cli.md` に新しいCLIのリファレンスが既に整備済み

## 変更内容

### 1. コマンド構文の変更
| 項目 | Before | After |
|------|--------|-------|
| CLI名 | `codex` | `opencode` |
| サブコマンド | `exec` | `run` |
| モデル指定 | `--model gpt-5.2-codex` | `-m openai/gpt-5.3-codex` |
| サンドボックス | `--sandbox read-only` | (削除: OpenCodeに該当フラグなし) |
| 自動実行 | `--full-auto` | (削除: OpenCodeに該当フラグなし) |
| stderr処理 | `2>/dev/null` | `2>&1` |

### 2. 環境変数の変更
| Before | After |
|--------|-------|
| `USE_CODEX=false` | `USE_OPENCODE=false` |

### 3. 用語の統一
| Before | After |
|--------|-------|
| Codex CLI | OpenCode CLI |
| Codex CLI協調 | OpenCode CLI協調 |
| Codexへの質問 | OpenCodeへの質問 |
| Codexからの所見 | OpenCodeからの所見 |
| Codexレビュー | OpenCodeレビュー |

### 4. エージェント名の修正（CLAUDE.md内）
CLAUDE.mdの「Codex使用エージェント」テーブルに古いエージェント名が残っている:
| Before | After |
|--------|-------|
| `post-impl-review` | `review-analyze` |
| `propose-improvement` | `propose-manage` |

## 影響範囲

### 変更対象ファイル（5ファイル）

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `.claude/skills/dev/story/agents/plan-review.md` | コマンド構文、用語、環境変数 |
| 2 | `.claude/skills/dev/feedback/agents/review-analyze.md` | コマンド構文、用語、環境変数 |
| 3 | `.claude/skills/dev/feedback/agents/propose-manage.md` | コマンド構文、用語、環境変数 |
| 4 | `.claude/skills/dev/story/SKILL.md` | 用語（Codex → OpenCode） |
| 5 | `CLAUDE.md` | セクション名、コマンド、エージェント名、環境変数、用語 |

### 影響を受けない箇所
- エージェントの実行フロー自体は変更なし
- プロンプトの内容（英語レビュー指示）は変更なし
- フォールバック時のチェックリストは変更なし
- 言語プロトコル（英語入力/日本語出力）は変更なし

## タスクリスト

### Phase 1: エージェントファイル更新（並列実行可能）
> 3ファイルは互いに独立しているため並列実行可能。

- [ ] `plan-review.md` のCodex → OpenCode移行 `[PARALLEL]`
  - frontmatter description内の「Codex CLI」→「OpenCode CLI」
  - 本文中の「Codex CLI」→「OpenCode CLI」
  - コマンド構文の変更（`codex exec ...` → `opencode run ...`）
  - stderr処理の変更（`2>/dev/null` → `2>&1`）
  - フォールバック条件の変更（`USE_CODEX=false` → `USE_OPENCODE=false`）
  - 「Codexからの所見」→「OpenCodeからの所見」
  - 「Codex CLIでレビュー」→「OpenCode CLIでレビュー」

- [ ] `review-analyze.md` のCodex → OpenCode移行 `[PARALLEL]`
  - 推奨モデル欄の「Codex呼び出し」→「OpenCode呼び出し」
  - コマンド構文の変更
  - stderr処理の変更
  - フォールバック条件の変更（`USE_CODEX=false` → `USE_OPENCODE=false`）
  - 「Codex利用不可時」→「OpenCode利用不可時」

- [ ] `propose-manage.md` のCodex → OpenCode移行 `[PARALLEL]`
  - 推奨モデル欄の「Codex呼び出し」→「OpenCode呼び出し」
  - コマンド構文の変更
  - stderr処理の変更
  - 「Codex利用不可時」→「OpenCode利用不可時」

### Phase 2: ドキュメント更新
> SKILL.mdとCLAUDE.mdはPhase 1の変更内容と整合させる必要がある。

- [ ] `SKILL.md`（dev:story）のCodex参照更新
  - Step 4のコメント「Codex CLI使用」→「OpenCode CLI使用」
  - Step 4セクション見出し「計画レビュー（Codex）」→「計画レビュー（OpenCode）」
  - 「Codexレビュー」→「OpenCodeレビュー」

- [ ] `CLAUDE.md` のCodex CLI協調セクション全面更新
  - セクション見出し「Codex CLI協調」→「OpenCode CLI協調」
  - 説明文の「Codex CLI」→「OpenCode CLI」
  - エージェント名テーブルの修正:
    - `post-impl-review` → `review-analyze`
    - `propose-improvement` → `propose-manage`
    - 用途の「dev:feedback Phase 0」→「dev:feedback Step 1」
    - 用途の「dev:feedback Phase 3」→「dev:feedback Step 3」
  - 「Codex使用エージェント」→「OpenCode使用エージェント」
  - 「Codex呼び出しパターン」→「OpenCode呼び出しパターン」
  - コマンド例の更新
  - 言語プロトコルの「Codexへの質問」→「OpenCodeへの質問」
  - フォールバック条件の更新（`USE_CODEX=false` → `USE_OPENCODE=false`）
  - 「Codex CLI」→「OpenCode CLI」（フォールバック説明）
  - 「Claude opusベースの分析」の記述は維持

### Phase 3: 検証
> 変更の一貫性を確認。

- [ ] 全ファイルでCodex/codex残留チェック `[BG:haiku:Explore]`
  - `grep -r "codex\|Codex\|USE_CODEX" .claude/skills/dev/ CLAUDE.md` で残留を確認
  - 意図的に残す箇所がないことを確認
- [ ] コマンド構文の整合性チェック
  - 全エージェントで `opencode run -m openai/gpt-5.3-codex` が統一されているか
  - `2>&1` が統一されているか
  - `USE_OPENCODE=false` が統一されているか

## リスク・考慮事項

| リスク | 影響度 | 対策 |
|--------|--------|------|
| OpenCode CLIが未インストールの環境 | 低 | フォールバック機構が既に存在（チェックリストベース手動分析） |
| `--sandbox read-only` 相当の安全機構がない | 低 | `opencode run` は非対話モードで実行され、書き込み操作は発生しない（プロンプトが分析・レビューのみ） |
| gpt-5.3-codex のレスポンス形式の差異 | 低 | プロンプトは自然言語であり、モデル間の互換性は高い |
