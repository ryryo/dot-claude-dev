---
name: dev:spec-run
description: 仕様書（docs/PLAN/{YYMMDD}_{slug}/）の実行プロトコル。Gate 単位で契約（Goal/Constraints/AC）を実装エージェントに渡し、AC ベースで完了を判定する。Trigger: 仕様書を実行, /dev:spec-run, 計画書の実行
---

## 起動フロー

### ステップ 1: 仕様書の特定

対象が会話の文脈や Gate 0 から明確な場合はステップ 2 へ進む。それ以外は:

1. `docs/PLAN/*/spec.md` を Glob で検索し、更新日順でソートする
2. 上位 5 件を AskUserQuestion で提示する（最新を推奨マーク付き）
3. ユーザーが選択した仕様書を対象とする

### ステップ 2: schemaVersion 検証

`tasks.json` を Read し、`schemaVersion === 3` を確認する。

- `schemaVersion === 3` → 続行
- それ以外 / `tasks.json` 不在 → エラー報告して中断（v1/v2/シングルモードは v3 化以降は非対応）

### ステップ 3: 実行準備

spec.md の「参照すべきファイル」と tasks.json を並列 Read し、以下を把握する:

- `gates[]` 全体（id, title, summary, dependencies, goal, constraints, acceptanceCriteria, todos, review, passed）
- `preflight[]`
- `progress` / `status` / `reviewChecked`

実装エージェント側にも同じ tasks.json を渡せるよう、Gate 単位での切り出し方を確認しておく。

### ステップ 4: 実行モード + worktree 選択

AskUserQuestion で **2 つの質問を同時に** 聞く（1 tool call）:

**質問 1: 実行モード**

- **Claudeモード** — Claude Code が各 Gate を直接実装する
- **Codex モード** — デフォルトで各 Gate を Codex プラグイン（`task --write`）に委任する。VERIFY は native `codex review` CLI（複雑さに応じてスキップ or 1回 or 3回並列）

**質問 2: worktree 使用**

- **使わない（Recommended）** — 現 cwd で直接作業する
- **使う** — `feature/{slug}` の worktree 内で作業し、全 Gate 通過後にローカル `--no-ff` マージ + cleanup を自動実行

「使う」を選択した場合は `references/worktree-setup.md` を **今すぐ Read** し、記載された手順を完了させてからステップ 5 へ進む。

### ステップ 5: 実行プロトコルの読み込みと実行

選択したモードの参照ファイルを Read し、その手順に従って実行する。

- **Claudeモード** → `references/execution.md`
- **Codex モード** → `references/codex-execution.md`

Preflight フェーズは必ず Claude main session で実行する（sandbox 制約のため）。

---

## Gate 通過条件

各 Gate について:

1. **全 Acceptance Criteria が `checked: true`** であること
2. **`gates[].review.result === "PASSED"`**（または SKIPPED 適用条件を満たす）であること
3. 上記が満たされたら `gates[].passed = true` を書き込み、`progress` / `status` を再計算する

## 結果の記録

### Preflight 完了時

`tasks.json` の `preflight[].checked = true` を書き込む。spec.md の Preflight チェックリストは PostToolUse hook により自動更新される。

### Gate 完了時

`tasks.json` のみ更新。spec.md は PostToolUse hook で自動再生成される。hook が未発火の環境では明示的に実行する:

```bash
node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs <tasks.json-path>
```

更新内容の例:

```json
{
  "gates": [
    {
      "id": "A",
      "acceptanceCriteria": [
        { "id": "A.AC1", "description": "...", "checked": true },
        { "id": "A.AC2", "description": "...", "checked": true }
      ],
      "review": { "result": "PASSED", "fixCount": 0, "summary": "OK" },
      "passed": true
    }
  ],
  "progress": {
    "gatesPassed": 1,
    "gatesTotal": 3,
    "currentGate": "B",
    "currentGateAC": { "passed": 0, "total": 4 }
  },
  "status": "in-progress"
}
```

### status / progress の算出ルール

```
gatesTotal     = gates.length
gatesPassed    = gates.filter(g => g.passed === true).length
currentGate    = 最初の passed=false の Gate.id（全 passed なら null）
currentGateAC  = currentGate の AC のうち checked の数 / 総数

status:
  - gatesTotal == 0                                 → "not-started"
  - gatesPassed == 0 && currentGateAC.passed == 0   → "not-started"
  - gatesPassed < gatesTotal                        → "in-progress"
  - gatesPassed == gatesTotal && !reviewChecked     → "in-review"
  - gatesPassed == gatesTotal && reviewChecked      → "completed"
```

## 全 Gate 通過後の完了処理

全 Gate の `passed === true` を確認し、実行完了を宣言する。未コミットの変更があればコミットする。

**Codex モードの場合**: 一時プロンプトファイルを削除する。

```bash
rm -f .tmp/codex-*.md
```

### worktree 運用の確認（ステップ 4 で worktree を選択した場合のみ）

worktree を使っていない場合はスキップし「人間レビュー確認フロー」へ進む。

AskUserQuestion でマージと人間レビューの順序を聞く:

- **先にマージ（Recommended）** — 人間レビューを後回しにして worktree を即マージ + cleanup
- **レビュー後にマージ** — レビュー OK 後に worktree をマージ + cleanup

#### 「先にマージ」を選択した場合

1. `references/worktree-teardown.md` を **今すぐ Read** し、記載された手順（マージ + cleanup）を完了させる
2. その後「人間レビュー確認フロー」に進む
3. レビュー NG の場合は base ブランチで fix-forward 対応する

#### 「レビュー後にマージ」を選択した場合

1. 「人間レビュー確認フロー」を実行する
2. OK になったら `references/worktree-teardown.md` を Read し手順を完了させる
3. NG の場合は worktree を残したまま修正ループに入る

### 人間レビュー確認フロー

spec.md に `## レビューステータス` セクションが存在し、未チェックの `- [ ] **レビュー完了**` 行がある場合のみ実行する。

`## レビューステータス` セクションは generated 領域の外（人間編集領域）。spec.md のチェックボックスを `[x]` に更新し、同時に `tasks.json` の `reviewChecked: true` を書き込み `status: "completed"` に再計算する。

1. AskUserQuestion でブラウザ動作確認を促す（実装内容に応じた確認ポイントを添える）
2. **OK / 確認済み**: spec.md と tasks.json を更新し、変更をコミット
3. **NG / 修正が必要**:
   - worktree が未 cleanup（「レビュー後にマージ」）→ worktree 内で修正ループ
   - worktree が cleanup 済み（「先にマージ」）→ base ブランチで fix-forward

セクションが存在しない場合はスキップ。

## 参照

### Claudeモード

- `references/execution.md` — Gate 実行プロトコル
- `roles/implementer.md` — 汎用実装ロール定義
- `roles/tdd-developer.md` — TDD 実装ロール定義

### Codex モード

- `references/codex-execution.md` — Codex Gate 実行プロトコル
- `roles/codex-developer.md` — Codex 汎用実装プロンプトテンプレート
- `roles/codex-tdd-developer.md` — Codex TDD 実装プロンプトテンプレート
- `references/codex-review-instructions.md` — codex review 用 focus テンプレート

### 共通

- `agents/reviewer-quality.md` — 品質・設計レビュワー
- `agents/reviewer-correctness.md` — 正確性・仕様適合レビュワー
- `agents/reviewer-conventions.md` — プロジェクト慣例レビュワー
