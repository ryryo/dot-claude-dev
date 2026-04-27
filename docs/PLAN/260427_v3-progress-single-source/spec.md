# tasks.json `progress` / `metadata` を gates 由来の derive 値に一本化する

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

---

## 概要

tasks.json schemaVersion 3 の `progress` ブロックと `metadata` ブロックを廃止し、すべて `gates[]` から動的に計算する設計に統一する。同時に dashboard サイドバーの「現 Gate AC 進捗」集計を `status === "in-progress"` プランのみに限定する。

## 背景

### 現状の問題

1. **症状**: 全 Gate 完了済みプランのカードが「AC 0/0」と表示され、レビュー待ちなのに進捗ゼロに見える
2. **直接原因**: `tasks.json` の `progress.currentGateAC` が `{ passed: 0, total: 0 }` で書かれており、loader がそれを素直に表示している
3. **根本原因**: `progress` ブロックは `gates[]` から完全に導出可能な denormalized state なのに、`tasks-schema-v3.md` 上では `/dev:spec-run` が手動で同期する設計になっている。「全 passed のとき何を書くべきか」が schema で未定義のため、LLM agent が判断して 0/0 を選んだ
4. **同じ問題が `metadata` にも存在**: `totalGates` / `totalTodos` も `gates[]` から導出可能。今は偶然合っているだけで、いずれズレる

### 解決方針

> **`gates[]` を唯一の真実 (Single Source of Truth) とし、`progress` / `metadata` は dashboard ローダー側で動的計算する。tasks.json には保持しない。**

副次効果:
- LLM agent は AC を check off するだけでよく、派生値の同期不要
- 新しい派生指標は loader / UI 側で自由に追加できる
- 全完了時の表示は数値ハック不要で UI 側ロジックで決定できる
- 検証 AC をすべて grep / vitest / Node スクリプトで機械化できる

### スコープ外（あえて含めないこと）

- v1 / v2 tasks.json の扱い（既に v3 へ移行済み、別案件）
- `status` フィールドの扱い（現状維持。Gate 通過時の人間ハンドオフが必要なため stored が妥当）
- `reviewChecked` の扱い（現状維持。人間判断のフラグなので stored が妥当）

## 設計決定事項

| #   | トピック                          | 決定                                                                                          | 根拠                                                                                                                                                       |
| --- | --------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `progress` の保存方法             | tasks.json に保持しない。dashboard loader が `gates[]` から都度計算する                       | denormalized state を排除し、source of truth を `gates[]` に一本化                                                                                         |
| 2   | 全 Gate 完了時の AC 表示          | **最後の Gate の AC** を 5/5 形式で表示 (`currentGate: null`, `currentGateAC = lastGate AC`)  | "0/0" は「何もやっていない」と誤読される。全完了プランは「最後にクリアした Gate の AC が満点」を見せるのが直感的                                           |
| 3   | 未着手・空状態の AC 表示          | **最初の Gate の AC** を 0/N 形式で表示                                                       | 着手前は「最初にぶつかる検証ハードル」を見せるのが UI として有用                                                                                           |
| 4   | sidebar 集計の対象                | `status === "in-progress"` のプランのみ                                                       | 全完了 / 未着手プランの 0 値が混ざると分子分母の意味が薄れる。sidebar の「現 Gate AC 進捗」は **進行中作業の負荷** を測る指標として再定義                  |
| 5   | `metadata` ブロック               | 完全撤去（型・template・既存ファイル全部）                                                    | `createdAt` は `spec.createdDate` で代替、`totalGates` / `totalTodos` は配列長で導出可能。同じ denormalized 問題                                           |
| 6   | 既存 tasks.json の扱い            | Node.js migration script で `progress` / `metadata` キーを削除。spec.md は hook で再生成      | dashboard は loader 側で吸収するので急がないが、将来のノイズと混乱を除去                                                                                   |
| 7   | 型レベルの撤去                    | `TasksJsonV3Progress` / `TasksJsonV3Metadata` 型を `dashboard/lib/types.ts` から削除          | 型レベルでも denormalized state を表現しないことで、将来の誤用を防ぐ                                                                                       |
| 8   | 検証の機械化                      | 各 Gate の AC をすべて `grep` / `vitest` / `bun run` / `jq` で判定可能な形式に統一            | LLM 判断のばらつきを排除し、Codex モード / 自動レビューでも同一結果を再現できる                                                                            |
| 9   | `PlanProgress` 型は維持           | dashboard の `lib/types.ts` の `PlanProgress` は loader が computeProgress 結果を保持するため | UI 側 contract は変えない（card / table / sidebar の props 互換性維持）                                                                                    |

## アーキテクチャ詳細

### Before（現状）

```
tasks.json
├── progress: { gatesPassed, gatesTotal, currentGate, currentGateAC }  ← LLM が手動同期 ❌
├── metadata: { createdAt, totalGates, totalTodos }                    ← LLM が手動同期 ❌
└── gates[]: [...]
        │
        ▼
   loader: convertProgress(tasksJson.progress)  ← 書かれた値を素直に渡す
        │
        ▼
   PlanFile.progress  ← 壊れた値が UI に届く（"AC 0/0" バグ）
```

### After（目標形）

```
tasks.json
├── spec / status / reviewChecked / preflight                          (人間判断 stored)
└── gates[]: [...]                                                     ← Single Source of Truth ✅
        │
        ▼
   loader: computeProgress(gates)                                      ← 純粋関数で都度計算
        │
        ▼
   PlanFile.progress                                                   ← 常に正しい
        │
        ▼
   UI:
   ├── card / table: plan.progress.currentGateAC をそのまま表示          (5/5 表示自動)
   └── sidebar: computeSidebarStats(plans) で in-progress のみ集計
```

### 関数仕様

#### `computeProgress(gates: Gate[]): PlanProgress`

```typescript
function computeProgress(gates: Gate[]): PlanProgress {
  const gatesTotal = gates.length;
  const gatesPassed = gates.filter((g) => g.passed).length;

  // 空 (gates なし)
  if (gatesTotal === 0) {
    return { gatesPassed: 0, gatesTotal: 0, currentGate: null,
             currentGateAC: { passed: 0, total: 0 } };
  }

  // 全完了 → 最後の Gate を表示用に使う (5/5 表示)
  if (gatesPassed === gatesTotal) {
    const last = gates[gatesTotal - 1];
    return {
      gatesPassed,
      gatesTotal,
      currentGate: null,
      currentGateAC: {
        passed: last.acceptanceCriteria.filter((ac) => ac.checked).length,
        total: last.acceptanceCriteria.length,
      },
    };
  }

  // 一部完了 or 全未通過 → 最初の passed=false の Gate
  const current = gates.find((g) => !g.passed)!;
  return {
    gatesPassed,
    gatesTotal,
    currentGate: current.id,
    currentGateAC: {
      passed: current.acceptanceCriteria.filter((ac) => ac.checked).length,
      total: current.acceptanceCriteria.length,
    },
  };
}
```

#### `computeSidebarStats(plans: PlanFile[])`

```typescript
interface SidebarStats {
  totalGates: number;
  passedGates: number;
  totalCurrentAc: number;       // in-progress プランのみの合計
  passedCurrentAc: number;      // in-progress プランのみの合計
  inProgressCount: number;      // ラベル表示用
}

function computeSidebarStats(plans: PlanFile[]): SidebarStats {
  const inProgress = plans.filter((p) => p.status === 'in-progress');
  return {
    totalGates:      plans.reduce((s, p) => s + p.progress.gatesTotal, 0),
    passedGates:     plans.reduce((s, p) => s + p.progress.gatesPassed, 0),
    totalCurrentAc:  inProgress.reduce((s, p) => s + p.progress.currentGateAC.total, 0),
    passedCurrentAc: inProgress.reduce((s, p) => s + p.progress.currentGateAC.passed, 0),
    inProgressCount: inProgress.length,
  };
}
```

### tasks.json の最終形（v3 改訂版）

```jsonc
{
  "schemaVersion": 3,
  "spec": { ... },                  // 不変
  "status": "in-progress",          // 不変（人間ハンドオフ用）
  "reviewChecked": false,           // 不変
  "preflight": [ ... ],             // 不変
  "gates": [ ... ]                  // 不変（todos / AC / review / passed をすべて含む）
  // ↓ 削除
  // "progress": { ... }
  // "metadata": { ... }
}
```

### 依存関係（Gate 順）

```
A (loader derive)
├── B (UI + sidebar)
├── E (型撤去)
└── C (skill / template / schema 改訂)
        └── D (既存 tasks.json migration script)
```

実装推奨順序: **A → B → E → C → D**
（A 後は B / E / C / D が並列可能だが、D は C の新 template に依存しないので末尾で十分）

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル                                                      | 変更内容                                                                                                                | 影響                                            |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `dashboard/lib/plan-json-loader.ts`                           | `convertProgress` 削除 → `computeProgress(gates)` 純粋関数で置換                                                        | dashboard すべて                                |
| `dashboard/lib/types.ts`                                      | `TasksJsonV3Progress` / `TasksJsonV3Metadata` 削除 / `TasksJsonV3.{progress,metadata}` プロパティ削除                  | dashboard ビルド全域                            |
| `dashboard/app/page.tsx`                                      | sidebar 集計を `computeSidebarStats` 呼び出しに置換 / 表示文言調整                                                      | sidebar 表示のみ                                |
| `.claude/skills/dev/spec/references/templates/tasks.template.json` | `progress` / `metadata` ブロック削除                                                                                    | 新規 /dev:spec 実行時                           |
| `.claude/skills/dev/spec/references/templates/tasks-schema-v3.md` | `progress` / `metadata` セクション削除 + 「dashboard 側で動的計算」と注記                                              | 仕様書ドキュメント                              |
| `.claude/skills/dev/spec/SKILL.md`                            | Step 6 の `progress` / `metadata` 初期化指示削除                                                                         | /dev:spec の生成挙動                            |
| `.claude/skills/dev/spec/agents/plan-reviewer.md`             | `progress` 検証チェック削除                                                                                              | レビュー出力                                    |
| `.claude/skills/dev/spec-run/SKILL.md`                        | `progress` / `status` 同期更新責務の記述削除（status の更新責務は維持）                                                  | /dev:spec-run の挙動                            |
| `docs/PLAN/260427_dashboard-v3-migration/tasks.json` ほか v3 | migration script で `progress` / `metadata` キーを削除                                                                  | 既存 1 ファイル + 今後増える v3 ファイル        |

### 新規作成ファイル

| ファイル                                                       | 内容                                                                                       |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `dashboard/lib/page-stats.ts`                                  | `computeSidebarStats` 純粋関数                                                             |
| `dashboard/__tests__/page-stats.test.ts`                       | `computeSidebarStats` の vitest（in-progress only / 空 / 混在ケース）                      |
| `.claude/skills/dev/spec/scripts/migrate-progress.mjs`         | 既存 v3 tasks.json から `progress` / `metadata` を削除する Node.js script (--dry-run 対応) |
| `.claude/skills/dev/spec/scripts/__tests__/migrate-progress.test.mjs` | migration script の vitest（in-memory JSON で動作検証）                                    |

### 変更しないファイル

| ファイル                                                                  | 理由                                                                                                                           |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `dashboard/lib/github.ts`                                                 | `isV3TasksJson` は `schemaVersion === 3` のみチェック。`progress` / `metadata` の有無に依存しない                              |
| `dashboard/components/plan-card.tsx`                                      | `plan.progress.currentGateAC` をそのまま表示しており、loader 側で正しい値が来れば自動で 5/5 表示になる                          |
| `dashboard/components/plan-table.tsx`                                     | 同上                                                                                                                           |
| `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs`                    | spec.md generated 領域生成は `gates[]` 起点なので影響なし（要確認: `progress` / `metadata` 参照がないこと）                      |
| `dashboard/lib/types.ts` の `PlanProgress`                                | UI が依存する内部 contract。loader がこの型に詰めて UI に渡す。型は変えない                                                    |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル                                                       | 目的                                                                                       |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `dashboard/lib/plan-json-loader.ts`                            | 既存 loader 実装。Gate A で書き換え対象                                                    |
| `dashboard/lib/types.ts`                                       | `PlanProgress` / `Gate` / `TasksJsonV3*` 型定義。Gate A / E で操作                         |
| `dashboard/lib/github.ts` (160-170 行目)                       | `isV3TasksJson` の検証ロジック。変更不要を確認するため                                     |
| `dashboard/app/page.tsx`                                       | Gate B で sidebar 集計を置換                                                               |
| `dashboard/__tests__/plan-json-loader.test.ts`                 | Gate A で computeProgress テスト追加                                                       |
| `.claude/skills/dev/spec/references/templates/tasks-schema-v3.md` | 現行 schema 仕様書。Gate C で改訂                                                          |
| `.claude/skills/dev/spec/references/templates/tasks.template.json` | tasks.json 雛形。Gate C で `progress` / `metadata` 削除                                    |
| `.claude/skills/dev/spec/SKILL.md` (Step 6, 117 行目近辺)      | Gate C で `progress` 初期化指示を削除                                                      |
| `.claude/skills/dev/spec/agents/plan-reviewer.md` (77 行目)    | Gate C で `progress` チェックを削除                                                        |
| `.claude/skills/dev/spec-run/SKILL.md` (29 / 66 / 84-121 行目) | Gate C で `progress` 更新責務を削除                                                        |

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク                                                                                          | 影響                                                                       | 緩和策                                                                                                                       |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 古い v3 tasks.json に `progress` フィールドが残ったまま、新 loader が無視 → 視覚的混乱          | tasks.json を直接読む人が「なぜ progress が反映されない？」と混乱する可能性 | Gate D の migration script で全削除する。spec.md にも「progress / metadata は廃止」を明記                                    |
| `status` フィールドが手動同期で残るので、`status: "in-progress"` だが実際は全 Gate passed のケース | sidebar 集計から漏れる可能性                                               | 短期: status の更新責務は `/dev:spec-run` に残し既存運用継続。長期課題として `status` も derive 化を検討（本スコープ外）       |
| 既存テスト（`plan-json-loader.test.ts`）が古い `progress` フィールド前提のフィクスチャを持つ可能性 | テストが落ちる                                                             | Gate A の Todo で fixture を更新                                                                                             |
| `sync-spec-md.mjs` が `progress` / `metadata` を参照していた場合、Gate D 実行で spec.md 再生成が壊れる | 既存 spec.md の generated 領域が消える                                     | Gate D 実装前に sync-spec-md.mjs を Read して `progress` / `metadata` 参照がないことを確認。あれば同 Gate で修正を含める      |

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: dashboard loader を gates[] から derive 化する
Gate B: UI 全完了表示 + sidebar 集計を進行中プランのみに限定（Gate A 完了後）
Gate C: skill / template / schema から `progress` と `metadata` を撤去する（Gate A 完了後）
Gate D: 既存 v3 tasks.json から `progress` / `metadata` を一括削除する migration script（Gate A, C 完了後）
Gate E: dashboard 型から `TasksJsonV3Progress` / `TasksJsonV3Metadata` を撤去（Gate A 完了後）
```

### Gate A: dashboard loader を gates[] から derive 化する

> plan-json-loader が tasks.json の `progress` を読まず、`gates[]` から `computeProgress` で都度計算するようにする

**Goal**: `dashboard/lib/plan-json-loader.ts` に純粋関数 `computeProgress(gates: Gate[]): PlanProgress` を実装し、`convertProgress(tasksJson.progress)` 呼び出しを置換する。空 / 全完了 / 一部完了 / 全未通過の 4 状態すべてで一貫した結果を返す — `progress` を tasks.json と二重管理する denormalized state を排除し、`gates[]` を Single Source of Truth として確立する。これにより全完了プランで起きていた 'AC 0/0' 表示バグが構造的に消え、今後 LLM agent が同期を間違えても dashboard 側に影響が出なくなる

**Constraints**:
- ✅ MUST: `computeProgress(gates)` を `dashboard/lib/plan-json-loader.ts` 内の純粋関数として実装する（副作用なし、入力 gates のみに依存）
- ✅ MUST: gates が空配列のとき `{ gatesPassed: 0, gatesTotal: 0, currentGate: null, currentGateAC: { passed: 0, total: 0 } }` を返す
- ✅ MUST: 全 Gate `passed === true` のとき `currentGate: null` かつ `currentGateAC` は最後の Gate の `acceptanceCriteria` の checked/total（5/5 表示要件）
- ✅ MUST: 全 Gate `passed === false` のとき `currentGate` は最初の Gate の id、`currentGateAC` は最初の Gate の AC
- ✅ MUST: 一部 passed のとき `currentGate` は最初の `passed === false` の Gate.id、`currentGateAC` はその Gate の AC
- ✅ MUST: `loadPlanFromTasksJson` から `convertProgress(tasksJson.progress)` 呼び出しを削除し `computeProgress(gates)` に置換する
- ✅ MUST: tasks.json 側の `progress` フィールドを参照しない（読まない）
- ✅ MUST: vitest テスト `dashboard/__tests__/plan-json-loader.test.ts` に computeProgress の 4 ケース（empty / 全未通過 / 一部通過 / 全通過）を追加する
- ❌ MUST NOT: `tasksJson.progress` を if 分岐で読む (どんな fallback も含めて)
- ❌ MUST NOT: `dashboard/lib/types.ts` から `TasksJsonV3Progress` / `TasksJsonV3Metadata` 型をこの Gate で削除する（Gate E の責務）
- ❌ MUST NOT: `dashboard/lib/types.ts` の `PlanProgress` 型を変更する（UI 側 contract 互換性維持）
- ❌ MUST NOT: isV3TasksJson の検証を変更する（`schemaVersion === 3` のみで十分）

**Acceptance Criteria**:
- [x] **A.AC1**: `cd dashboard && bunx vitest run __tests__/plan-json-loader.test.ts` が GREEN で、computeProgress の 4 ケース（gates 空 / 全未通過 / 一部通過 / 全完了）すべてのテストが含まれる
- [x] **A.AC2**: `grep -nE 'convertProgress|tasksJson\.progress' dashboard/lib/plan-json-loader.ts` が 0 ヒット
- [x] **A.AC3**: `cd dashboard && bun run lint` が 0 errors
- [x] **A.AC4**: `cd dashboard && bun run build` が成功（型エラー 0）
- [x] **A.AC5**: dashboard 起動後、`docs/PLAN/260427_dashboard-v3-migration/` の PLAN カードに「AC 5/5」（または該当 Gate の最終 AC 充足数）が表示される（手動）

**Todos** (2):
- **A1**: [TDD] `computeProgress(gates)` 純粋関数を実装し、4 状態のケースで vitest テストを書く — `dashboard/lib/plan-json-loader.ts`, `dashboard/__tests__/plan-json-loader.test.ts`
- **A2**: [SIMPLE] `convertProgress` を削除し `loadPlanFromTasksJson` 内の呼び出しを `computeProgress(gates)` に置換 — `dashboard/lib/plan-json-loader.ts`

**Review**: ✅ PASSED — computeProgress 純粋関数導入により Single Source of Truth 化。reviewer-correctness PASS。手動確認で完了プランの AC 6/6 表示を確認

### Gate B: UI 全完了表示 + sidebar 集計を進行中プランのみに限定

> plan-card / plan-table の 5/5 表示を loader 経由で自動化し、sidebar の現 Gate AC 進捗を `status === in-progress` プランのみで集計するロジックを純粋関数に抽出する

**Goal**: `dashboard/lib/page-stats.ts` に `computeSidebarStats(plans)` を新設し、`app/page.tsx` の sidebar 集計を置換する。in-progress プランのみを対象とする集計ロジックを vitest で検証する — 全完了 / 未着手プランの 0 値が混ざると分子分母の意味が薄れるため、sidebar の「現 Gate AC 進捗」を「進行中作業の負荷」を測る指標として再定義する。集計ロジックを純粋関数として抽出することで vitest で機械検証可能にする

**Constraints**:
- ✅ MUST: `dashboard/lib/page-stats.ts` を新規作成し `computeSidebarStats(plans: PlanFile[]): SidebarStats` を export する
- ✅ MUST: SidebarStats 型は `{ totalGates, passedGates, totalCurrentAc, passedCurrentAc, inProgressCount }` を含む
- ✅ MUST: `totalCurrentAc` / `passedCurrentAc` は `plan.status === 'in-progress'` のプランのみを集計対象とする
- ✅ MUST: `totalGates` / `passedGates` は全プランを集計対象とする（Gate 進捗は overall を見せたい）
- ✅ MUST: `app/page.tsx` の既存 sidebar 集計コード（`totalCurrentAc` / `passedCurrentAc` / `acProgress` 計算）を `computeSidebarStats` 呼び出しに置換する
- ✅ MUST: sidebar の表示ラベルを「現 Gate AC 進捗（進行中 N 件）」のように in-progress 件数を併記する
- ✅ MUST: `dashboard/__tests__/page-stats.test.ts` を新規作成し、(1) 全プラン in-progress / (2) 全プラン completed / (3) 混在 / (4) 空配列 の 4 ケースを vitest で検証する
- ✅ MUST: percent 計算 (`overallProgress` / `acProgress`) は呼び出し側 (`app/page.tsx`) で `computeSidebarStats` の戻り値から derive する。`SidebarStats` 型は raw な分子分母 (`totalGates` / `passedGates` / `totalCurrentAc` / `passedCurrentAc` / `inProgressCount`) のみを返す
- ❌ MUST NOT: `currentGateAC.total === 0 のとき非表示` のような数値ハックを残す
- ❌ MUST NOT: sidebar 集計を `app/page.tsx` 内に inline で書き戻す（純粋関数として抽出する）
- ❌ MUST NOT: `plan-card.tsx` / `plan-table.tsx` の AC 表示ロジックを変更する（loader 由来で自動的に正しい値が届く）
- ❌ MUST NOT: `SidebarStats` 型に percent (`overallProgress` / `acProgress`) フィールドを含める

**Acceptance Criteria**:
- [x] **B.AC1**: `cd dashboard && bunx vitest run __tests__/page-stats.test.ts` が GREEN で、全 in-progress / 全 completed / 混在 / 空 の 4 ケースすべてのテストが含まれる
- [x] **B.AC2**: `grep -n 'computeSidebarStats' dashboard/app/page.tsx` がヒットし、旧 inline 集計（`totalCurrentAc` / `passedCurrentAc` の reduce）が削除されている
- [x] **B.AC3**: `cd dashboard && bun run lint` が 0 errors
- [x] **B.AC4**: `cd dashboard && bun run build` が成功
- [ ] **B.AC5**: dashboard 起動後、in-review プラン（260427_dashboard-v3-migration）のカードに「AC 5/5」が表示されている（手動）
- [ ] **B.AC6**: dashboard 起動後、sidebar の「現 Gate AC 進捗」の分母が in-progress プランの AC 総数に一致し、in-progress 件数のラベルが併記されている（手動）

**Todos** (2):
- **B1**: [TDD] `computeSidebarStats(plans)` 純粋関数を `dashboard/lib/page-stats.ts` に新設し vitest で 4 ケース検証 — `dashboard/lib/page-stats.ts`, `dashboard/__tests__/page-stats.test.ts`
- **B2**: `app/page.tsx` の sidebar 集計を `computeSidebarStats` 呼び出しに置換 + 表示ラベル調整 — `dashboard/app/page.tsx`

**Review**: _未記入_

### Gate C: skill / template / schema から `progress` と `metadata` を撤去する

> /dev:spec / /dev:spec-run skill が `progress` / `metadata` を生成・更新しないように template / schema doc / SKILL.md / plan-reviewer agent を改訂する

**Goal**: 新規 /dev:spec が `progress` / `metadata` を含まない tasks.json を生成し、/dev:spec-run が `progress` を更新しないようにする。schema doc にも「dashboard で動的計算」を明記する — 二度と denormalized state を書き込ませないため。LLM agent の責務を最小化し、検証チェックを grep 系で機械化する

**Constraints**:
- ✅ MUST: `.claude/skills/dev/spec/references/templates/tasks.template.json` から `progress` ブロックと `metadata` ブロックを完全削除する
- ✅ MUST: `.claude/skills/dev/spec/references/templates/tasks-schema-v3.md` の「progress オブジェクト（ハイブリッド）」セクションと「metadata オブジェクト」セクションを削除し、代わりに「`progress` / `metadata` は dashboard で動的計算（tasks.json には保持しない）」を簡潔に記述する
- ✅ MUST: tasks-schema-v3.md の「更新責任者表」から `progress` / `metadata` 行を削除（status は維持）
- ✅ MUST: tasks-schema-v3.md のサンプル完全版 JSON から `progress` / `metadata` を削除
- ✅ MUST: `.claude/skills/dev/spec/SKILL.md` の Step 6（117 行目近辺）から `progress: { gatesPassed: 0, ... }` 初期化指示を削除
- ✅ MUST: `.claude/skills/dev/spec/SKILL.md` の Step 6（120 行目近辺）から `metadata.createdAt` / `metadata.totalGates` / `metadata.totalTodos` 初期化指示を削除
- ✅ MUST: `.claude/skills/dev/spec/SKILL.md` の完了条件から `metadata` / `progress` 関連項目を削除（あれば）
- ✅ MUST: `.claude/skills/dev/spec/agents/plan-reviewer.md` の Step 5 構造チェックから `progress` 形式チェック（77 行目）と `metadata.totalGates` / `metadata.totalTodos` 一致チェック（80 行目）の両方を削除する
- ✅ MUST: `.claude/skills/dev/spec-run/SKILL.md` の Gate 通過条件・結果記録セクション（29 / 66 / 84-105 / 107-121 行目近辺）から `progress` 更新責務の記述を削除する。`status` の更新責務は維持する
- ✅ MUST: `.claude/skills/dev/spec-run/SKILL.md` の `## status / progress の算出ルール` セクション（107-121 行目近辺）を `## status の算出ルール` に改名し、progress 計算行（`gatesTotal = ...` / `gatesPassed = ...` / `currentGate = ...` / `currentGateAC = ...`）のみ削除する。status の状態遷移条件（`gatesTotal == 0 → not-started` 等）は現行のまま維持する
- ❌ MUST NOT: 「metadata は廃止予定」のような中途半端な記述を残す（完全撤去）
- ❌ MUST NOT: `status` フィールドの更新責務を消す（`status` は人間ハンドオフ用に残る）
- ❌ MUST NOT: `reviewChecked` 関連の記述を消す
- ❌ MUST NOT: v1 / v2 への参照を増やす

**Acceptance Criteria**:
- [ ] **C.AC1**: `jq 'has("progress") or has("metadata")' .claude/skills/dev/spec/references/templates/tasks.template.json` が `false`
- [ ] **C.AC2**: `grep -nE 'TasksJsonV3Metadata|metadata\.createdAt|metadata\.totalGates|metadata\.totalTodos' .claude/skills/dev/spec/ .claude/skills/dev/spec-run/ -r` が 0 ヒット
- [ ] **C.AC3**: `grep -nE '## progress|## metadata|progress オブジェクト|metadata オブジェクト' .claude/skills/dev/spec/references/templates/tasks-schema-v3.md` が 0 ヒット
- [ ] **C.AC4**: `grep -n 'dashboard で動的計算' .claude/skills/dev/spec/references/templates/tasks-schema-v3.md` がヒット（新セクションが追加されている）
- [ ] **C.AC5**: `grep -nE 'progress.*再計算|progress.*更新' .claude/skills/dev/spec-run/SKILL.md` が 0 ヒット
- [ ] **C.AC6**: `.claude/skills/dev/spec/SKILL.md` の完了条件 `[ ] tasks.json の schemaVersion が 3 である` が残っており、`progress` / `metadata` 関連の完了条件は存在しないこと（grep で確認）
- [ ] **C.AC7**: `grep -nE 'metadata\.totalGates|metadata\.totalTodos' .claude/skills/dev/spec/agents/plan-reviewer.md` が 0 ヒット
- [ ] **C.AC8**: `grep -nE 'gatesTotal|gatesPassed|currentGateAC' .claude/skills/dev/spec-run/SKILL.md` が 0 ヒット（status 状態遷移の状態名のみ残る）

**Todos** (5):
- **C1**: [SIMPLE] tasks.template.json から `progress` / `metadata` ブロックを削除 — `.claude/skills/dev/spec/references/templates/tasks.template.json`
- **C2**: tasks-schema-v3.md の `progress` / `metadata` セクションを削除し、動的計算注記に置換 — `.claude/skills/dev/spec/references/templates/tasks-schema-v3.md`
- **C3**: [SIMPLE] dev:spec/SKILL.md Step 6 から `progress` / `metadata` 初期化指示を削除 — `.claude/skills/dev/spec/SKILL.md`
- **C4**: [SIMPLE] plan-reviewer.md から `progress` 検証チェック削除 — `.claude/skills/dev/spec/agents/plan-reviewer.md`
- **C5**: dev:spec-run/SKILL.md から `progress` 更新責務を削除（`status` は維持） — `.claude/skills/dev/spec-run/SKILL.md`

**Review**: _未記入_

### Gate D: 既存 v3 tasks.json から `progress` / `metadata` を一括削除する migration script

> Node.js スクリプトを作成し、`docs/PLAN/*/tasks.json` のうち `schemaVersion === 3` のファイルから `progress` / `metadata` キーを削除する（dry-run 対応、spec.md 再生成込み）

**Goal**: `.claude/skills/dev/spec/scripts/migrate-progress.mjs` を作成し、--dry-run / 実行モード切替で v3 tasks.json から `progress` / `metadata` を削除する。実行後 `sync-spec-md.mjs` を呼び出して spec.md を再生成する — 既存 v3 tasks.json に書かれた値が今後の混乱の元になるため一度クリーンアップする。スクリプトを idempotent にして将来の v3 ファイル増加にも対応できるようにする

**Constraints**:
- ✅ MUST: `.claude/skills/dev/spec/scripts/migrate-progress.mjs` を Node.js (ESM) で作成
- ✅ MUST: コマンドライン引数: `[--dry-run] [<glob>]`。glob 省略時は `docs/PLAN/*/tasks.json` をデフォルト
- ✅ MUST: 対象ファイルごとに JSON.parse → `schemaVersion === 3` のみ処理（それ以外はスキップしてログ）
- ✅ MUST: `progress` / `metadata` キーを削除した結果を JSON.stringify (indent 2) で書き戻す
- ✅ MUST: `--dry-run` モードでは書き込まず、変更予定ファイル一覧と diff サマリのみ出力
- ✅ MUST: 実行モードでは各ファイル更新後に `node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs <tasks.json-path>` を子プロセスで呼び出し spec.md を再生成
- ✅ MUST: `.claude/skills/dev/spec/scripts/__tests__/migrate-progress.test.mjs` を vitest で作成し、(1) v3 ファイル → progress/metadata 削除、(2) v2 ファイル → スキップ、(3) progress/metadata なし v3 ファイル → 変更なし（idempotent）の 3 ケースを in-memory で検証
- ✅ MUST: 実行モードで全 v3 PLAN（現時点 2 件: 260427_dashboard-v3-migration / 260427_v3-progress-single-source）に適用する
- ✅ MUST: `sync-spec-md.mjs` を Read して `progress` / `metadata` を参照していないことを事前確認する。参照があれば同 Gate で除去する
- ❌ MUST NOT: `schemaVersion < 3` のファイルに対してキー削除を実行する
- ❌ MUST NOT: `gates` / `spec` / `status` / `reviewChecked` / `preflight` / `schemaVersion` を変更する
- ❌ MUST NOT: バックアップなし破壊的書き込み（dry-run でない実行は git diff で差分が見える状態で行う前提）

**Acceptance Criteria**:
- [ ] **D.AC1**: `bunx vitest run .claude/skills/dev/spec/scripts/__tests__/migrate-progress.test.mjs` が GREEN で、3 ケース（v3 削除 / v2 スキップ / idempotent）すべてのテストが含まれる
- [ ] **D.AC2**: `node .claude/skills/dev/spec/scripts/migrate-progress.mjs --dry-run` を実行すると、対象 v3 ファイル一覧と削除予定キーが標準出力に出る（書き込みは発生しない）
- [ ] **D.AC3**: 実行モード適用後、`for f in $(find docs/PLAN -name tasks.json); do grep -l '"schemaVersion": 3' "$f"; done | xargs jq 'has("progress") or has("metadata")'` が全 false
- [ ] **D.AC4**: 実行後 `git status docs/PLAN/*/spec.md` で spec.md の generated 領域も同期更新されていることが確認できる（少なくとも対象ファイルの mtime が更新されている、または diff が出る）
- [ ] **D.AC5**: dashboard を再起動後、移行後 v3 PLAN（progress フィールドなし）が引き続き正常表示される（手動）
- [ ] **D.AC6**: `grep -nE '"progress"|"metadata"' .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` が 0 ヒット（事前確認、または該当 Gate での修正完了）

**Todos** (2):
- **D1**: [TDD] `migrate-progress.mjs` 本体（--dry-run 対応）と vitest テスト 3 ケース — `.claude/skills/dev/spec/scripts/migrate-progress.mjs`, `.claude/skills/dev/spec/scripts/__tests__/migrate-progress.test.mjs`
- **D2**: 全 v3 tasks.json に migration を適用 + spec.md 再同期確認 + sync-spec-md.mjs の事前確認 — `docs/PLAN/260427_dashboard-v3-migration/tasks.json`, `docs/PLAN/260427_v3-progress-single-source/tasks.json` ほか

**Review**: _未記入_

### Gate E: dashboard 型から `TasksJsonV3Progress` / `TasksJsonV3Metadata` を撤去

> `dashboard/lib/types.ts` から denormalized state 型を削除し、`TasksJsonV3` interface から `progress` / `metadata` プロパティを除去する

**Goal**: `TasksJsonV3Progress` / `TasksJsonV3Metadata` interface を削除し、`TasksJsonV3` interface から該当プロパティを除去する。残存参照を grep で 0 にする — 型レベルでも denormalized state を表現しないことで、将来の誤用を防ぐ。loader が gates derive しているため UI には影響しない

**Constraints**:
- ✅ MUST: `dashboard/lib/types.ts` から `TasksJsonV3Progress` interface を削除
- ✅ MUST: `dashboard/lib/types.ts` から `TasksJsonV3Metadata` interface を削除
- ✅ MUST: `dashboard/lib/types.ts` の `TasksJsonV3` interface から `progress` / `metadata` プロパティを削除
- ✅ MUST: `dashboard/` 配下の `TasksJsonV3Progress` / `TasksJsonV3Metadata` / `tasksJson.progress` / `tasksJson.metadata` 参照を grep で 0 になるまで除去する
- ✅ MUST: `PlanProgress` 型は維持する（loader が computeProgress 結果を保持する内部型）
- ✅ MUST: `cd dashboard && bun run build` が 0 errors
- ✅ MUST: `cd dashboard && bun run lint` が 0 errors
- ✅ MUST: `cd dashboard && bunx vitest run` が全 GREEN
- ❌ MUST NOT: `PlanProgress` 型を変更する
- ❌ MUST NOT: 互換用の deprecated alias 型（`type TasksJsonV3Metadata = unknown` 等）を残す
- ❌ MUST NOT: loader を再修正する（Gate A の責務）

**Acceptance Criteria**:
- [ ] **E.AC1**: `grep -nE 'TasksJsonV3Progress|TasksJsonV3Metadata' dashboard/ -r` が 0 ヒット
- [ ] **E.AC2**: `grep -nE 'tasksJson\.progress|tasksJson\.metadata' dashboard/ -r` が 0 ヒット
- [ ] **E.AC3**: `cd dashboard && bun run build` が成功（型エラー 0）
- [ ] **E.AC4**: `cd dashboard && bun run lint` が 0 errors
- [ ] **E.AC5**: `cd dashboard && bunx vitest run` が全テスト GREEN
- [ ] **E.AC6**: dashboard を起動して既存 v3 PLAN（progress 残存 / 削除済み 両方）が正常に表示される（手動）

**Todos** (1):
- **E1**: [SIMPLE] types.ts から `TasksJsonV3Progress` / `TasksJsonV3Metadata` interface を削除し、`TasksJsonV3` から該当プロパティを除去（残存参照は E.AC1/AC2 の grep で検証） — `dashboard/lib/types.ts`

**Review**: _未記入_

<!-- generated:end -->
