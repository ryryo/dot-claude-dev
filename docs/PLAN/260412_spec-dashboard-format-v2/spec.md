# Spec ↔ Dashboard フォーマット v2 移行

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

---

## 概要

`/dev:spec` が生成する仕様書と dashboard の間に生じているフォーマット衝突を、tasks.json schema v2 の導入と sync スクリプトによる spec.md 自動生成機構によって解消する。シングルモードを廃止してディレクトリモード一本化し、完了チェックの二重持ち問題を構造的に不可能にする。

## 背景

### 現状の問題

1. **二重フォーマット維持コスト** — spec.md（人間向け markdown）と tasks.json（機械向け）の両方に情報があり、dashboard は spec.md を正規表現で 300 行パースしている（`dashboard/lib/plan-parser.ts`）
2. **完了チェックのドリフトリスク** — spec.md のチェックボックスと tasks.json の状態を Claude が同時更新する必要があり、片方を忘れると進捗表示が壊れる
3. **シングル / ディレクトリモード分岐の複雑性** — Gate/Todo 数で出力形式が変わるため、`/dev:spec-run` / dashboard / spec-sync agent がそれぞれ 2 系統のロジックを持っている

### 問題の本質

mutable な progress state を immutable な narrative と同じ markdown に埋め込んでしまっているのが根本原因。この2つを1枚の markdown に同居させているため、dashboard が narrative から機械可読情報を掘り返すハメになっている。

### 解決の方向性

- **tasks.json を真として拡張** — dashboard が現在 body から拾っている全情報（summary, gate description, todo description, steps[], review 結果）を tasks.json に集約する
- **spec.md の「タスクリスト」セクションを自動生成化** — `<!-- generated:begin/end -->` マーカー領域内を sync スクリプトが tasks.json から再生成。spec-run は tasks.json のみ更新し、マークダウン更新は構造的に不要にする
- **シングルモード廃止** — 全て ディレクトリモード一本化
- **後方互換** — 既存 112 PLAN は触らない。dashboard / spec-run は schemaVersion 判定でフォールバック

### なぜ skill-scoped PostToolUse hook か

propagation の構造上、`.claude/skills/dev/` と `.claude/hooks/dev/` はシンボリックリンクで全プロジェクトに配信されるが、`.claude/settings.json` はプロジェクトごと生成（`create-settings-json.sh` は既存をスキップ）。既存プロジェクトにも自動伝播させるには、フックをスキル frontmatter に宣言する必要がある。前例: `.claude/.backup/skills/dev/developing/SKILL.md` が PostToolUse hook を skill-scoped で定義済み。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1 | スキーマバージョン識別 | tasks.json のトップレベルに `schemaVersion: 2` を配置。未定義/<2 は v1/レガシーと判定 | JSON.parse 後の 1 行チェックで済む。metadata 内は既存と衝突 |
| 2 | シングルモード | **廃止**。`/dev:spec` は常にディレクトリモードで出力 | 二重実装を消し、dashboard/spec-run/spec-sync の分岐を減らす |
| 3 | generated 領域 | spec.md の `## タスクリスト` セクション配下（依存関係図・Gate 見出し・Todo チェックリスト・Review blockquote）を全て generated。レビューステータス節と残存リスク節は人間編集領域のまま | 「タスクリスト節全体」が最も分割点が少なく、差分が minimum になる |
| 4 | sync 発火条件 | `/dev:spec-run` の SKILL.md frontmatter に PostToolUse hook を宣言（matcher: `Edit|Write|MultiEdit`）。hook script が tool_input.file_path を見て tasks.json 以外は exit 0 | skill-scoped なので propagation 問題なし。フィルタは hook 側で |
| 5 | generated マーカー不在時 | stderr に warning 出して exit 0（スキップ） | 既存 v1 仕様書や手編集中の spec.md を壊さない安全側動作 |
| 6 | status / progress 更新責任 | `/dev:spec-run` が `steps[].checked` を書き換える際に同一 write で `status` / `progress` も再計算して書き込む。sync script は tasks.json に一切触らない | hook の再発火ループを構造的に防ぐ |
| 7 | sync script の実装言語 | Node.js（`.mjs`, ESM, `node --test` ビルトイン使用） | JSON parsing + markdown 生成は bash より node が安全。Node 18+ は dot-claude-dev の前提環境 |
| 8 | sync script の配置 | ロジック本体は `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs`、hook wrapper は `.claude/hooks/dev/sync-spec-md-hook.sh` | skill 本体と紐付くロジックは skill ディレクトリに、既存の `commit-check.sh` と同じパターンで hook は `.claude/hooks/dev/` |
| 9 | dashboard 後方互換 | `fetchPlanFiles` は dir entry に対し `tasks.json` を先に試し、`schemaVersion >= 2` なら JSON 直読み（`plan-json-loader.ts`）、それ以外は既存 `plan-parser.ts` にフォールバック | 既存 112 PLAN は無変更のまま `plan-parser.ts` で引き続き読まれる |
| 10 | `plan-parser.ts` の扱い | レガシー用に温存。削除は全 PLAN 自然減後 | 移行強制を避け、レガシー PLAN を壊さない |
| 11 | spec-template.md（シングル用） | **削除** | 新規 `/dev:spec` は使わなくなるためデッドコード |
| 12 | PlanFile 型の共通化 | dashboard の `PlanFile` 型は既存のまま共通表示用として維持。v2 JSON → `PlanFile` 変換関数を `plan-json-loader.ts` に新設 | dashboard UI を一切触らずに済む |
| 13 | `[TDD]` ラベル | tasks.json `todos[].tdd: true` は現状通り。steps[] 構造には影響しない（Step 1 IMPL + Step 2 Review は tdd の有無にかかわらず一定） | 既存 `/dev:spec-run` の判定ロジックを維持 |
| 14 | Review 未記入時の格納 | `steps[1].checked: false` かつ `steps[1].review: null` | review オブジェクト自体は結果記入時にのみ作られる |
| 15 | `impl` の構造化 | v2 では `impl` を flat string から**構造化オブジェクト**に変更。`{ goal, prerequisites?, steps?, content?, diff?, constraints?, testCases?, scenarios?, verify, failureRecovery?, notes? }` の各フィールドに意味ごとに分離。外部ファイル化しない（tasks.json 内に集約を維持） | AI が markdown 見出し（`## 目的` / `## 手順` 等）を文字列パースする必要がなくなる。各フィールドに直接アクセスでき、`\n` エスケープも content 以外では不要に |
| 16 | `content` フィールド廃止 | verbatim コードを JSON に埋め込まない。代わりに `steps` + `constraints` で記述的に仕様を伝え、AI が実装時にコードを生成する。どうしても literal が必要な例外ケースのみ `\n` 文字列を許容 | JSON でコードを表現すると `\n` / `\"` エスケープが不可避で、行配列にしても見た目が悪い。AI にとって descriptive な仕様 → コード生成の方が自然（AI ネイティブ）。verbatim コピペは人間向けパターン |
| 17 | impl の必須 / 推奨フィールド | 必須は `goal` + `verify` のみ。条件付き推奨（`tdd: true` → `testCases`、`affectedFiles` に create → `steps` or `content` 等）は spec-sync が**警告レベル**でチェック（エラーにしない） | hard constraint を増やすと `/dev:spec` 生成時の柔軟性を殺す。必須を最小にし、推奨は warning で報告して agent が自判断で補完する余地を残す |
| 18 | 現 260412 仕様書の扱い | v1 のまま完走させる。v2 dogfooding（自身の tasks.json を v2 変換）は Gate F 完了後に独立タスクとして別途作成 | Gate A-E は v1 spec-run で実行される前提。途中で schema を変えると実行基盤が壊れる。v2 完成後に dogfooding する方が安全かつ検証価値が高い |

## アーキテクチャ詳細

### データフロー

```
[/dev:spec]
    └─ tasks.json v2 + spec.md（generated 領域は空 or 初期状態）を write
         │
         │  ※ この初回 write で hook が発火し、空 → 初期状態のタスクリストが生成される
         ▼
    spec.md（タスクリスト節が tasks.json の初期状態から自動生成）

[/dev:spec-run]（v2 モード）
    └─ Step 4 UPDATE: tasks.json を Edit
         ├─ steps[].checked を true に
         ├─ steps[review].review に結果オブジェクト
         └─ status / progress を再計算して同時更新
              │
              │  PostToolUse hook 発火
              ▼
    sync-spec-md-hook.sh
         ├─ tool_name が Edit/Write/MultiEdit か
         ├─ file_path が tasks.json で終わるか
         ├─ 同階層に spec.md があるか
         └─ node sync-spec-md.mjs {tasks.json path}
              │
              ▼
    sync-spec-md.mjs
         ├─ tasks.json を読む（schemaVersion >= 2 確認）
         ├─ spec.md を読む
         ├─ <!-- generated:begin --> ... <!-- generated:end --> を検索
         │    └─ なければ warning + exit 0
         └─ マーカー間を tasks.json から再生成した markdown で置換

[dashboard fetchPlanFiles]（dir entry 時）
    ├─ tasks.json を fetch 試行
    │    ├─ 成功 && schemaVersion >= 2 → plan-json-loader.ts で PlanFile に変換
    │    ├─ 成功 && schemaVersion < 2 → spec.md にフォールバック
    │    └─ 404 → spec.md にフォールバック
    └─ spec.md を fetch → plan-parser.ts（レガシー）
```

### tasks.json schema v2 全文

```json
{
  "schemaVersion": 2,
  "spec": {
    "slug": "example-feature",
    "title": "サンプル機能",
    "summary": "ラベル付きアイテムを登録・検索できるようにする",
    "createdDate": "2026-04-12",
    "specPath": "spec.md"
  },
  "status": "not-started",
  "reviewChecked": false,
  "progress": { "completed": 0, "total": 6 },
  "preflight": [
    { "id": "P1", "title": "", "command": "", "manual": false, "reason": "" }
  ],
  "gates": [
    {
      "id": "Gate A",
      "title": "データ層のセットアップ",
      "description": "スキーマ・リポジトリ層の整備",
      "dependencies": [],
      "passCondition": "全 Review 結果記入欄が埋まり、総合判定が PASS であること"
    }
  ],
  "todos": [
    {
      "id": "A1",
      "gate": "Gate A",
      "title": "[TDD] スキーマ定義とマイグレーション",
      "description": "items テーブルを定義し migration を生成",
      "tdd": true,
      "dependencies": [],
      "affectedFiles": [
        { "path": "db/schema/items.ts", "operation": "create", "summary": "items テーブル定義" }
      ],
      "impl": {
        "goal": "items テーブルを定義し migration を生成する",
        "steps": [
          "db/schema/items.ts に drizzle-orm の sqliteTable で items テーブルを定義",
          "pnpm db:generate で migration 生成",
          "pnpm db:migrate で適用"
        ],
        "constraints": [
          "カラム: id (integer PK autoIncrement), name (text notNull), createdAt/updatedAt (integer timestamp notNull)",
          "drizzle-orm/sqlite-core を使用"
        ],
        "verify": "pnpm tsc --noEmit がエラー 0"
      },
      "relatedIssues": [],
      "steps": [
        { "kind": "impl",   "title": "Step 1 — IMPL",   "checked": false },
        { "kind": "review", "title": "Step 2 — Review", "checked": false, "review": null }
      ]
    }
  ],
  "metadata": {
    "createdAt": "2026-04-12T00:00:00Z",
    "totalGates": 1,
    "totalTodos": 1
  }
}
```

#### impl 構造化オブジェクトのスキーマ

```json
{
  "goal": "string — 必須。このタスクの達成目標",
  "prerequisites": "string | string[] — 前提条件（依存 Todo の状態等）",
  "steps": ["string — 実行手順。単純なステップは string で列挙"],
  "diff": "string | string[] — v1→v2 等の差分解説",
  "constraints": ["string — 守るべき制約・invariant"],
  "testCases": [
    { "name": "string", "input": "string?", "expected": "string", "note": "string?" }
  ],
  "scenarios": [
    { "name": "string", "setup": "string | string[]?", "action": "string | string[]", "expected": "string | string[]" }
  ],
  "verify": "string | string[] — 必須。検証コマンドまたは手順",
  "failureRecovery": [
    "string — 症状と対応を記述",
    { "symptom": "string", "action": "string" }
  ],
  "notes": "string | string[] — 補足事項"
}
```

**必須**: `goal` + `verify`。他は全て optional（Todo の性質に応じて使用）。

**条件付き推奨**（spec-sync が警告レベルでチェック）:

| 条件 | 推奨フィールド |
|---|---|
| `tdd: true` | `testCases` |
| `affectedFiles` に create あり | `steps` + `constraints` |
| Gate が E2E / 検証系 | `scenarios` |
| 他 Gate に依存する後段 Todo | `prerequisites` |

#### v1 → v2 の差分

| v1 | v2 | 備考 |
|---|---|---|
| — | `schemaVersion: 2` (top-level) | 判定用 |
| `spec.slug`, `spec.title`, `spec.specPath` | 同左 + `spec.summary`, `spec.createdDate` | dashboard カード表示 |
| — | `status` (top-level) | PlanStatus 文字列 |
| — | `reviewChecked` (top-level) | 人間レビュー完了フラグ |
| — | `progress: { completed, total }` (top-level) | 進捗バー |
| `gates[].id`, `gates[].title` | 同左 + `gates[].description` | Gate カード表示 |
| `todos[].id`, `title`, `impl` 等 | 同左 + `todos[].description`, `todos[].steps[]` | dashboard 表示 + チェック状態格納 |
| `todos[].impl: string` | `todos[].impl: ImplObject` | flat string → 構造化オブジェクト（決定 #15） |
| — | `todos[].steps[]` | 各 Todo 固定 2 要素（impl + review） |
| `todos[].status: "pending"` | **削除** | `steps[].checked` の集計に置き換え |

### Step / Review オブジェクトの構造

```json
{
  "kind": "impl",
  "title": "Step 1 — IMPL",
  "checked": false
}
```

```json
{
  "kind": "review",
  "title": "Step 2 — Review",
  "checked": true,
  "review": {
    "result": "PASSED",
    "fixCount": 0,
    "summary": "スキーマ整合性 OK"
  }
}
```

`review.result` は `PASSED | FAILED | SKIPPED | IN_PROGRESS` のいずれか。未記入時は `checked: false, review: null`。

### status / progress の算出ルール

dashboard の現行 `determineStatus` と同じロジックを JSON 側で維持する:

```
total     = sum of all steps across all todos
completed = count of steps where checked == true
progress  = { completed, total }

status:
  - total == 0                                   → "not-started"
  - completed == 0                               → "not-started"
  - 0 < completed < total                        → "in-progress"
  - completed == total && reviewChecked == false → "in-review"
  - completed == total && reviewChecked == true  → "completed"
```

**更新責任**: `/dev:spec-run` が `steps[].checked` を更新する際、同一 Edit で `status` と `progress` も再計算して書き込む。

### generated マーカーと spec.md の構造

```markdown
# {タイトル}

## Gate 0: 準備 ...
## 概要 ...
## 背景 ...
## 設計決定事項 ...
## アーキテクチャ詳細 ...
## 変更対象ファイルと影響範囲 ...
## 参照すべきファイル ...

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

{gates の dependencies から生成}

### Gate A: {title}

> {description}（あれば）

- [ ] **A1**: {title}
  > **Review A1**: _未記入_

**Gate A 通過条件**: {passCondition}

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク
```

### sync-spec-md.mjs の仕様

#### CLI 引数

```
node sync-spec-md.mjs <tasks-json-path>
```

- `tasks-json-path`: 絶対パスまたは cwd からの相対パス
- 引数なしの場合は exit 1 + usage をstderr

#### 動作

1. `tasks-json-path` を読み込み JSON パース失敗時は stderr warning + exit 0
2. `schemaVersion >= 2` でなければ stderr warning + exit 0（レガシー skip）
3. 同階層の `spec.md` を検索。なければ stderr warning + exit 0
4. `spec.md` 内で `<!-- generated:begin -->` と `<!-- generated:end -->` を両方検索
5. どちらか欠落していれば stderr warning + exit 0（安全側スキップ）
6. マーカー間を `generateTaskListSection(tasksJson)` の出力で置換
7. `spec.md` を in-place write
8. tasks.json は**一切書き換えない**（ループ防止）

#### 純関数 `generateTaskListSection(tasksJson)` の出力

```markdown
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: データ層
  └→ Gate B: API（Gate A 完了後）
```

### Gate A: データ層のセットアップ

> スキーマ・リポジトリ層の整備

- [ ] **A1**: [TDD] スキーマ定義とマイグレーション
  > **Review A1**: _未記入_
- [x] **A2**: [TDD] リポジトリ層の実装
  > **Review A2**: ✅ PASSED — 整合性確認

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること
```

チェックボックスは `steps[].checked` が全て true なら `[x]`、一つでも false なら `[ ]`（Todo 単位表示）。Review 行は `review.result` に応じてフォーマット:

| review 状態 | 出力 |
|---|---|
| `review == null` | `> **Review {id}**: _未記入_` |
| `review.result == "PASSED"` | `> **Review {id}**: ✅ PASSED` + （fixCount > 0 時）` (FIX {n}回)` + （summary あれば）` — {summary}` |
| `review.result == "FAILED"` | `> **Review {id}**: ❌ FAILED — {summary}` |
| `review.result == "SKIPPED"` | `> **Review {id}**: ⏭️ SKIPPED — {summary}` |
| `review.result == "IN_PROGRESS"` | `> **Review {id}**: ⏳ IN_PROGRESS` |

### hook wrapper の仕様

`.claude/hooks/dev/sync-spec-md-hook.sh`:

```bash
#!/bin/bash
# PostToolUse hook: tasks.json の Edit/Write を検知して sync-spec-md を起動
# 発火条件を満たさない場合は silently exit 0

set -e
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
case "$TOOL_NAME" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
[ -z "$FILE_PATH" ] && exit 0

# tasks.json で終わらなければスキップ
case "$FILE_PATH" in
  */tasks.json) ;;
  *) exit 0 ;;
esac

# 同階層に spec.md がなければスキップ
SPEC_DIR=$(dirname "$FILE_PATH")
[ ! -f "$SPEC_DIR/spec.md" ] && exit 0

# sync-spec-md を起動
SYNC_SCRIPT="${CLAUDE_PROJECT_DIR:-.}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs"

# skill がシンボリックリンクなので $CLAUDE_PROJECT_DIR 配下から解決
if [ ! -f "$SYNC_SCRIPT" ]; then
  # 共有ディレクトリへのフォールバック
  SYNC_SCRIPT="${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs"
fi

if [ -f "$SYNC_SCRIPT" ]; then
  node "$SYNC_SCRIPT" "$FILE_PATH" >&2 || true
fi

exit 0
```

- hook 失敗を常に exit 0 で吸収（spec-run フローを止めない）
- stderr 出力は Claude Code のログに流れる
- `CLAUDE_PROJECT_DIR` 配下でスクリプトを解決、symlink 先の共有ディレクトリ経由でも動作

### dashboard `fetchPlanFiles` の分岐

```typescript
if (entry.type === 'dir') {
  const tasksJsonPath = `${entry.path}/tasks.json`;
  const specPath = `${entry.path}/spec.md`;

  // 1. tasks.json を試す（v2 対応）
  try {
    const content = await fetchFileContent(owner, repo, tasksJsonPath);
    const parsed = JSON.parse(content);
    if (typeof parsed?.schemaVersion === 'number' && parsed.schemaVersion >= 2) {
      return loadPlanFromTasksJson(parsed, specPath, projectName);
    }
    // v1 tasks.json: spec.md にフォールバック
  } catch (error) {
    if (!isFileNotFoundError(error)) throw error;
    // 404: spec.md にフォールバック
  }

  // 2. レガシー spec.md
  try {
    const content = await fetchFileContent(owner, repo, specPath);
    return parsePlanFile(content, specPath, projectName);
  } catch (error) {
    if (isFileNotFoundError(error)) return null;
    throw error;
  }
}
```

### `loadPlanFromTasksJson` の責務

`dashboard/lib/plan-json-loader.ts` に新設:

```typescript
export function loadPlanFromTasksJson(
  tasksJson: TasksJsonV2,
  specPath: string,
  projectName: string
): PlanFile
```

変換ルール:

- `PlanFile.title` ← `tasksJson.spec.title`
- `PlanFile.summary` ← `tasksJson.spec.summary`
- `PlanFile.createdDate` ← `tasksJson.spec.createdDate`
- `PlanFile.reviewChecked` ← `tasksJson.reviewChecked`
- `PlanFile.status` ← `tasksJson.status`
- `PlanFile.progress` ← `{ ...tasksJson.progress, percentage: Math.round(completed/total*100) }`
- `PlanFile.gates` ← tasksJson.gates を走査、各 gate に属する todos を tasksJson.todos からフィルタして紐付け
- `PlanFile.todos` ← flat list
- 各 `Todo.steps` ← `tasksJson.todos[].steps[]` を dashboard の `Step` 型に変換:
  - `Step.checked` ← `steps[].checked`
  - `Step.kind` ← `steps[].kind`
  - `Step.title` ← `steps[].title`
  - `Step.description` ← `todos[].description`（Todo description を Step description に流用、既存 UI の表示に合わせる）
  - `Step.hasReview` / `reviewFilled` / `reviewResult` / `reviewFixCount` ← review kind の step から `review` オブジェクトを展開
- `PlanFile.rawMarkdown` ← `''`（v2 は markdown を保持しない。既存コードが raw を使う箇所がないか要確認、ある場合は空文字で互換）

### v2 サンプル fixture の構成

`.claude/skills/dev/spec/references/examples/sample-v2/` 配下に以下を配置し、リファレンス文書 / sync スクリプトの E2E テスト入力 / dashboard 表示確認の共通基点として利用する。

- **規模**: 2 Gate × 合計 4 Todo 程度の最小ケース
- **網羅するシナリオ**:
  1. **未着手**: `steps[*].checked: false`, `review: null`
  2. **進行中**: IMPL のみ checked、Review は IN_PROGRESS
  3. **PASSED with fix**: `review.result: "PASSED"`, `fixCount: 2`, summary あり
  4. **FAILED / SKIPPED**: それぞれ blockquote レンダリングを全分岐カバー
- **`status` / `progress` の 4 状態**: fixture を手動編集して `not-started` / `in-progress` / `in-review` / `completed` を切り替え可能にし、F3 の検証に使用
- **検証後の復元**: F3 で手動編集する際はブランチを汚さないよう検証後に `git checkout` で fixture を戻す（手順は F3 impl に明記）

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `.claude/skills/dev/spec/SKILL.md` | シングルモード廃止、Step 6 削除、Step 7 を v2 schema 対応に更新、完了条件更新 | 新規 `/dev:spec` の挙動が変わる |
| `.claude/skills/dev/spec/references/templates/tasks.template.json` | v2 schema へ全面更新 | `/dev:spec` の出力が v2 化 |
| `.claude/skills/dev/spec/references/templates/spec-template-dir.md` | generated マーカー追加、タスクリスト節の記述簡略化 | 新規 spec.md の雛形が変わる |
| `.claude/skills/dev/spec/agents/spec-sync.md` | v2 schema 対応（steps[] 整合性、generated マーカー存在確認、Review blockquote 削除） | Step 10 の整合性チェック動作が変わる |
| `.claude/skills/dev/spec-run/SKILL.md` | frontmatter に PostToolUse hook 追加、Step 2 を schemaVersion 判定に変更、v2/v1/シングル 3 分岐 | spec-run 起動時の判定と実行時の更新対象が変わる |
| `.claude/skills/dev/spec-run/references/execution.md` | Step 4 UPDATE を v2/v1 分岐、v2 は tasks.json のみ更新 | v2 仕様書の実行フローが変わる |
| `.claude/skills/dev/spec-run/references/codex-execution.md` | Step 4 UPDATE を v2/v1 分岐（execution.md と同じロジック） | Codex モードでの v2 実行フロー |
| `dashboard/lib/github.ts` | `fetchPlanFiles` の dir 分岐に tasks.json schemaVersion 判定を追加 | dashboard 表示ロジックが v2/v1 対応 |
| `dashboard/lib/types.ts` | `TasksJsonV2` 系の型を追加（`PlanFile` 型は維持） | dashboard の型のみ拡張 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `.claude/skills/dev/spec/references/templates/tasks-schema-v2.md` | v2 schema の全フィールド説明、初期値、更新責任者表、サンプル JSON |
| `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | sync スクリプト本体（pure 関数 `generateTaskListSection` + CLI エントリポイント） |
| `.claude/skills/dev/spec-run/scripts/__tests__/sync-spec-md.test.mjs` | sync-spec-md の Node.js 組み込みテスト（`node --test`） |
| `.claude/hooks/dev/sync-spec-md-hook.sh` | PostToolUse hook wrapper |
| `dashboard/lib/plan-json-loader.ts` | v2 JSON → `PlanFile` 変換関数 |
| `dashboard/__tests__/plan-json-loader.test.ts` | plan-json-loader の vitest テスト |
| `.claude/skills/dev/spec/references/examples/sample-v2/spec.md` | v2 サンプル fixture（spec 側、generated マーカー込み） |
| `.claude/skills/dev/spec/references/examples/sample-v2/tasks.json` | v2 サンプル fixture（tasks 側、4 シナリオを網羅する小規模データ） |

### 削除するファイル

| ファイル | 理由 |
| -------- | ---- |
| `.claude/skills/dev/spec/references/templates/spec-template.md` | シングルモード廃止に伴いデッドコード |

### 変更しないファイル（温存）

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/lib/plan-parser.ts` | レガシー v1 PLAN のフォールバックパス |
| `dashboard/__tests__/plan-parser*.test.ts` | 既存テストの回帰検知 |
| `docs/PLAN/**/*` （既存 112 PLAN） | 後方互換で温存。移行しない |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `docs/spec-dashboard-format-review.md` | 検討経緯と Option 比較。なぜ v2 に至ったかの背景 |
| `.claude/skills/dev/spec/SKILL.md` | 改修対象。現行のシングル/ディレクトリ分岐ロジック |
| `.claude/skills/dev/spec/references/templates/tasks.template.json` | 改修対象。現行 v1 schema |
| `.claude/skills/dev/spec/references/templates/spec-template-dir.md` | 改修対象。現行 spec.md 雛形 |
| `.claude/skills/dev/spec/agents/spec-sync.md` | 改修対象。現行整合性チェックロジック |
| `.claude/skills/dev/spec-run/SKILL.md` | 改修対象。現行起動フロー |
| `.claude/skills/dev/spec-run/references/execution.md` | 改修対象。現行 Step 4 UPDATE ロジック |
| `.claude/skills/dev/spec-run/references/codex-execution.md` | 改修対象。Codex 版 Step 4 |
| `.claude/.backup/skills/dev/developing/SKILL.md` | skill-scoped PostToolUse hook 宣言の**前例**。frontmatter 構文の参考 |
| `.claude/hooks/dev/commit-check.sh` | 既存 hook script の**前例**。stdin JSON payload の扱い方、exit code の規約 |
| `dashboard/lib/plan-parser.ts` | 温存対象。フォールバックパスの参照、型と `determineStatus` ロジックの参考 |
| `dashboard/lib/github.ts` | 改修対象。`fetchPlanFiles` の現行分岐 |
| `dashboard/lib/types.ts` | 改修対象。`PlanFile` 型の現行定義 |
| `dashboard/__tests__/plan-parser.test.ts` | 既存テスト構造の参考（vitest 使用、fixture 作成パターン） |
| `docs/PLAN/260411_spec-run-worktree-mode/tasks.json` | 現行 v1 tasks.json の**実例**。impl フィールドの粒度・書式の参考 |
| `scripts/setup-claude.sh` | propagation 確認用。symlink 対象ディレクトリの一覧 |

## タスクリスト

### 依存関係図

```
Gate A: Schema 基盤
  └→ Gate B: /dev:spec skill 改修
       └→ Gate C: sync-spec-md スクリプト実装
            └→ Gate D: /dev:spec-run skill 改修
                 └→ Gate E: dashboard 改修
                      └→ Gate F: E2E 検証
```

### Gate A: Schema 基盤

> tasks.json v2 の型定義・テンプレート・スキーマドキュメント・サンプル fixture を揃える

- [x] **A1**: dashboard/lib/types.ts に TasksJsonV2 系の型を追加
  > **Review A1**: ⏭️ SKIPPED (docs only)
- [x] **A2**: tasks.template.json を v2 形式に全面更新
  > **Review A2**: ⏭️ SKIPPED (docs only)
- [x] **A3**: tasks-schema-v2.md（スキーマドキュメント）を新規作成
  > **Review A3**: ⏭️ SKIPPED (docs only)
- [x] **A4**: v2 サンプル fixture 新規作成（後続 TDD / E2E の共通入力）
  > **Review A4**: ⏭️ SKIPPED (docs only)

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: /dev:spec skill 改修

> シングルモード廃止、SKILL.md・テンプレート・spec-sync agent を v2 対応に更新

- [x] **B1**: spec/SKILL.md からシングルモード分岐削除 + Step 7 を v2 schema 対応に更新
  > **Review B1**: ⏭️ SKIPPED (docs only)
- [x] **B2**: spec-template-dir.md に generated マーカー追加 + spec-template.md 削除
  > **Review B2**: ⏭️ SKIPPED (docs only)
- [x] **B3**: spec/agents/spec-sync.md を v2 schema 対応に更新
  > **Review B3**: ⏭️ SKIPPED (docs only)

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: sync-spec-md スクリプト実装

> tasks.json → spec.md の generated 領域を再生成するスクリプトと hook wrapper

- [x] **C1**: [TDD] sync-spec-md.mjs 本体実装 + node --test テスト
  > **Review C1**: ✅ PASSED — 11 tests all pass, manual fixture test confirms 5 review states
- [x] **C2**: sync-spec-md-hook.sh（PostToolUse hook wrapper）実装
  > **Review C2**: ✅ PASSED — syntax check OK, all 4 manual test scenarios pass

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: /dev:spec-run skill 改修

> frontmatter hook 宣言、schemaVersion 判定、Step 4 UPDATE の v2/v1 分岐

- [ ] **D1**: spec-run/SKILL.md frontmatter に PostToolUse hook 追加 + ステップ 2 を schemaVersion 判定に変更
  > **Review D1**: _未記入_
- [ ] **D2**: execution.md の Step 4 UPDATE を v2/v1 分岐に更新
  > **Review D2**: _未記入_
- [ ] **D3**: codex-execution.md の Step 4 UPDATE を v2/v1 分岐に更新
  > **Review D3**: _未記入_

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate E: dashboard 改修

> plan-json-loader の新設と fetchPlanFiles の schemaVersion 分岐

- [ ] **E1**: [TDD] plan-json-loader.ts 実装 + vitest テスト
  > **Review E1**: _未記入_
- [ ] **E2**: github.ts の fetchPlanFiles を schemaVersion 分岐に改修
  > **Review E2**: _未記入_
- [ ] **E3**: 既存 plan-parser テストの動作確認 + dashboard 全体ビルド確認
  > **Review E3**: _未記入_

**Gate E 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate F: E2E 検証

> v1 レガシーパスの回帰なし、A4 で作成した fixture を使った sync hook 通しチェック、dashboard 新旧並行表示の実ブラウザ確認

- [ ] **F1**: 既存 v1 PLAN が dashboard で引き続き表示されることを確認（レガシーパス回帰）
  > **Review F1**: _未記入_
- [ ] **F2**: チェック同期 E2E（A4 fixture を手動 Edit → hook 発火 → spec.md 再生成を 4 シナリオで検証）
  > **Review F2**: _未記入_
- [ ] **F3**: dashboard 表示 E2E（v2 fixture と既存 v1 PLAN の並行表示、schemaVersion 分岐の実動作）
  > **Review F3**: _未記入_

**Gate F 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| 既存 v1 PLAN のレガシーパスが将来破綻する | dashboard 表示エラー | `plan-parser.ts` とテスト 3 本を温存。CI で回帰検知 |
| sync-spec-md の generated マーカー欠落を silent skip にしたため、新規 v2 仕様書で sync が効いていないことに気づきにくい | spec.md が古いまま残る | hook 発火時に stderr で「generated マーカーが見つからないためスキップ」と出力。`/dev:spec` の完了条件に「spec.md に generated マーカーが存在する」を追加 |
| PostToolUse hook の skill-scoped 宣言が期待通り動かない環境（Claude Code のバージョン差） | spec-run フローで sync が効かない | Gate F の F2 で通しチェック。フォールバックとして global Stop hook でも sync を呼ぶ選択肢を将来検討（現状は skill-scoped のみ） |
| 新旧混在プロジェクトで tasks.json が v1 のまま存在する場合、`fetchPlanFiles` が v1 tasks.json を読んで無視し spec.md にフォールバック → 2 回フェッチでレート制限に近づく | GitHub API レート制限 | fallback のログを dashboard のサーバログに出して頻度を監視。将来必要なら v1 tasks.json をキャッシュして短絡 |
| `plan-json-loader.ts` の型変換で既存 `PlanFile` との互換性が崩れる箇所がある（特に `description` / `rawMarkdown`） | dashboard UI で undefined 表示 | E1 の TDD で既存 UI 使用箇所を走査し、必須フィールドを空文字で埋める |
| sync-spec-md が tasks.json を書き換えるバグが混入すると hook 再発火で無限ループ | CPU 暴走 | C1 のテストで「sync 実行後 tasks.json が byte-level で不変」をアサート |
