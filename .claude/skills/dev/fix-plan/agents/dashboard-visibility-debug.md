# Agent: dashboard-visibility-debug

スクリプト群 (`validate`, `fix`, `simulate`) を実行しても
「ダッシュボードに表示されない / 表示が壊れている」原因が特定できない場合に、
LLM が原因を調査するための手順。

## 前提

以下のスクリプトを全て実行済みであること:

```bash
# 1. 構造・整合性チェック
node .claude/skills/dev/fix-plan/scripts/validate-tasks-json.mjs docs/PLAN/{対象}/tasks.json

# 2. ダッシュボードと同じパース処理のローカル再現
npx tsx .claude/skills/dev/fix-plan/scripts/simulate-dashboard-parse.mjs docs/PLAN/{対象}

# 3. 自動修復可能な項目の適用
node .claude/skills/dev/fix-plan/scripts/fix-tasks-json.mjs docs/PLAN/{対象}/tasks.json

# 4. spec.md 同期チェック
node .claude/skills/dev/fix-plan/scripts/check-spec-sync.mjs docs/PLAN/{対象}/tasks.json
```

スクリプトが全て PASS しているのにダッシュボードに表示されない場合、
以下の観点で調査する。

## 調査手順

### 1. GitHub 上のファイル確認

ダッシュボードは GitHub API から取得するため、ローカルとリモートで差異がないか確認する。

```bash
# 最新コミットが push されているか
git log --oneline origin/master -5 -- docs/PLAN/{対象}/

# GitHub API でディレクトリ内容を直接確認
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/contents/docs/PLAN/{対象}" | python3 -m json.tool
```

確認ポイント:
- `tasks.json` が GitHub 上に存在するか
- `tasks.json` の `size` が極端に大きくないか（GitHub Contents API は 1MB 制限）
- ディレクトリ内に予期しないファイルがないか

### 2. GitHub API レスポンスのパース確認

`github.ts` の `fetchPlanFiles` と同じ処理をシミュレートする。

1. `dashboard/lib/github.ts` を Read する
2. `tryLoadV2` の処理フロー (`fetchFileContent` → `JSON.parse` → `isV2TasksJson`) を確認
3. エラーが `isFileNotFoundError` として握り潰されていないか確認

```bash
# tasks.json の中身を GitHub API 経由で取得できるか
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/contents/docs/PLAN/{対象}/tasks.json" | \
  python3 -c "import json,sys,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode()[:200])"
```

### 3. ダッシュボード フィルタリング確認

ダッシュボード側のフィルタで除外されていないか、以下を確認する。

1. `dashboard/app/page.tsx` を Read する
2. 以下のフィルタ条件を確認:
   - **日付フィルタ**: `filterDays` (デフォルト30日) で `createdDate` が除外されていないか
   - **リポジトリ選択**: `selectedRepos` に対象リポジトリが含まれているか
   - **sizeBinFilter**: ヒストグラムフィルタで除外されていないか
3. Kanban カラムに `completed` が含まれているか:
   - `dashboard/components/kanban-board.tsx` の `COLUMNS` を確認

### 4. フロントエンド レンダリング確認

データは届いているが表示が壊れている場合。

1. ブラウザの DevTools で `/api/plans?repos=...` のレスポンスを確認
2. 対象プランがレスポンスに含まれているか
3. 含まれている場合 → カードコンポーネントの表示ロジックを確認:
   - `dashboard/components/plan-card.tsx` を Read
   - `progress.total === 0` の場合に表示が省略されていないか
   - `gates.length === 0` の場合のフォールバック

### 5. エッジケースの確認

- `tasks.json` のサイズが大きすぎて Vercel serverless function のレスポンスサイズ上限に達していないか
- `spec.md` の `rawMarkdown` が空文字の場合にフロントエンドでエラーにならないか
- `createdDate` のフォーマットが `YYYY-MM-DD` 以外（例: ISO 8601 with timezone）で日付フィルタが誤動作していないか

## 原因特定後の対応

- **tasks.json の問題** → `fix-tasks-json.mjs` で修復、または Edit で直接修正
- **spec.md の問題** → `sync-spec-md.mjs` で再同期、または Edit で直接修正
- **ダッシュボード コードのバグ** → `dashboard/` 配下の該当ファイルを Edit で修正
- **GitHub 同期の問題** → `git push` で反映
