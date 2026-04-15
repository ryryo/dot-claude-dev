---
name: dev:fix-plan
description: |
  docs/PLAN 配下の計画書ファイル（tasks.json v2）のフォーマット不整合を検出・修正し、
  ダッシュボードでの表示問題を解決するスキル。

  スクリプトによる自動チェック（構造・整合性・パースシミュレーション）を第一手段とし、
  解決しない場合は LLM エージェントが原因を調査する。

  Trigger: 計画書が壊れた, プランの修正, 計画書のフォーマット直す, /dev:fix-plan, plan fix, plan broken, ダッシュボードに表示されない
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# fix-plan — 計画書ファイルのフォーマット修復（v2 対応）

`docs/PLAN` 配下の `tasks.json` (schemaVersion 2) に生じた
フォーマット不整合や値の不備を検出・修正するスキル。
**v1 (spec.md マークダウンパース) は対象外。**

## トリガー

- `/dev:fix-plan`
- 「計画書が壊れた」「プランの修正」「計画書のフォーマット直す」
- 「ダッシュボードにプランが表示されない」

## スクリプト一覧

| スクリプト | 役割 | 実行コマンド |
| --- | --- | --- |
| `scripts/validate-tasks-json.mjs` | 構造 + 整合性の 20 項目チェック。タイポ検出付き | `node scripts/validate-tasks-json.mjs <tasks.json>` |
| `scripts/fix-tasks-json.mjs` | progress / status / metadata の自動修復。`--dry-run` で確認のみ | `node scripts/fix-tasks-json.mjs <tasks.json> [--dry-run]` |
| `scripts/simulate-dashboard-parse.mjs` | ダッシュボードと**同じパーサー** (plan-json-loader.ts) をローカル実行 | `npx tsx scripts/simulate-dashboard-parse.mjs <plan-dir>` |
| `scripts/check-spec-sync.mjs` | spec.md の generated 領域と tasks.json の差分検出 | `node scripts/check-spec-sync.mjs <tasks.json>` |

## エージェント

| ファイル | 役割 |
| --- | --- |
| `agents/dashboard-visibility-debug.md` | スクリプトで解決しなかった場合の LLM による原因調査手順 |

## 実行フロー

### Step 1: 対象プランの特定

1. ユーザーがパスを指定している場合 → そのプランを作業対象とする
2. 指定がない場合 → `docs/PLAN/*/tasks.json` を Glob で一覧し、AskUserQuestion で対象を選択

### Step 2: validate スクリプトの実行

```bash
node .claude/skills/dev/fix-plan/scripts/validate-tasks-json.mjs docs/PLAN/{対象}/tasks.json
```

20 項目のチェック結果を確認:
- 全て PASS → Step 3 へ
- FAIL あり → Step 4 へ

### Step 3: simulate スクリプトの実行

ダッシュボードと同じパース処理をローカルで再現:

```bash
npx tsx .claude/skills/dev/fix-plan/scripts/simulate-dashboard-parse.mjs docs/PLAN/{対象}
```

- エラーなく表示される → パース自体は正常。ダッシュボード側の問題の可能性
- エラーが発生 → エラーメッセージから原因を特定

### Step 4: fix スクリプトで修復

validate / simulate で検出した問題のうち、自動修復可能なもの:

```bash
# 確認のみ
node .claude/skills/dev/fix-plan/scripts/fix-tasks-json.mjs docs/PLAN/{対象}/tasks.json --dry-run

# 実行
node .claude/skills/dev/fix-plan/scripts/fix-tasks-json.mjs docs/PLAN/{対象}/tasks.json
```

修復対象:
- `progress.total` / `progress.completed` の再計算
- `status` の再導出
- `metadata.totalGates` / `metadata.totalTodos` の再計算

### Step 5: タイポの手動修正

validate でタイポが検出された場合（例: `"done"` → `"completed"`）は Edit で修正する。
スクリプトが出力する候補を参考にする:

```
#4 status value: got "done", expected one of: ... (did you mean "completed"?)
#10 steps structure: T1 step "...": kind="implementaton" (did you mean "impl"?)
```

### Step 6: spec.md の再同期

```bash
node .claude/skills/dev/fix-plan/scripts/check-spec-sync.mjs docs/PLAN/{対象}/tasks.json
```

差分があれば:

```bash
node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs docs/PLAN/{対象}/tasks.json
```

### Step 7: 修復結果の確認

1. validate スクリプトを再実行して全項目 PASS を確認
2. simulate スクリプトを再実行してパース結果が正しいことを確認
3. 最終サマリーを報告

### Step 8: スクリプトで解決しない場合

`agents/dashboard-visibility-debug.md` を読み、記載された調査手順に従う。
主な調査観点:
- GitHub 上のファイル確認（未 push など）
- GitHub API レスポンスのパース確認
- ダッシュボード側のフィルタリング（日付 / リポジトリ / サイズ）
- フロントエンド レンダリング

## 参照ソース

スクリプトが判定の正とするファイル。必要に応じて Read する:

- `dashboard/lib/plan-json-loader.ts` — v2 パーサー
- `dashboard/lib/types.ts` — TasksJsonV2 型定義
- `.claude/skills/dev/spec/references/templates/tasks.template.json` — v2 テンプレート
- `dashboard/lib/github.ts` — GitHub API クライアント
