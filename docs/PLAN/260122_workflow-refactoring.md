# ワークフロー分類リファクタリング計画書

## 概要

1. **PLAN → E2E リネーム**: 「計画」ではなく「ブラウザ検証」という実態に合わせる
2. **TASK追加**: 環境セットアップ等、テストもUI検証も不要なタスク用の第3カテゴリ

## 背景・課題

### 課題1: PLANという名称の不適切さ

「PLAN」は「計画」を意味するが、実際に行っているのは：
- agent-browserでの視覚的検証
- E2E（End-to-End）的なユーザー操作フロー確認

→ **E2E** にリネームすることで実態と一致させる

### 課題2: 分類できないタスクの存在

| タスク例 | TDD? | PLAN(E2E)? |
|----------|------|------------|
| 開発環境セットアップ | ❌ テスト対象ではない | ❌ UI確認不要 |
| ESLint/Prettier設定 | ❌ | ❌ |
| CI/CDパイプライン構築 | ❌ | ❌ |
| パッケージインストール | ❌ | ❌ |
| ドキュメント作成 | ❌ | ❌ |

→ **TASK** カテゴリを追加

---

## 新しい分類体系

### 判定フロー

```
タスクを分析
    ↓
入出力が明確に定義できる？
    ├─ YES → TDD（テスト駆動）
    └─ NO → 視覚的確認が必要？
              ├─ YES → E2E（agent-browser検証）
              └─ NO → TASK（実行→動作確認→完了）
```

### 3つのワークフロー比較

| ラベル | 検証方法 | ワークフロー | 対象 |
|--------|----------|--------------|------|
| **TDD** | 自動テスト | RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT | ロジック、バリデーション |
| **E2E** | agent-browser | IMPL→AUTO→CHECK→COMMIT | UI/UX、視覚的要素 |
| **TASK** | コマンド実行確認 | EXEC→VERIFY→COMMIT | セットアップ、設定、インフラ |

---

## 変更1: PLAN → E2E リネーム

### ファイル名変更

| 現在のパス | 新しいパス |
|-----------|-----------|
| `.claude/rules/workflow/plan-cycle.md` | `.claude/rules/workflow/e2e-cycle.md` |
| `.claude/rules/workflow/tdd-plan-branching.md` | `.claude/rules/workflow/workflow-branching.md` |
| `.claude/skills/dev/story-to-tasks/agents/classify-tdd-plan.md` | `.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md` |
| `.claude/skills/dev/story-to-tasks/references/plan-criteria.md` | `.claude/skills/dev/story-to-tasks/references/e2e-criteria.md` |
| `.claude/skills/dev/developing/agents/plan-implement.md` | `.claude/skills/dev/developing/agents/e2e-implement.md` |
| `.claude/skills/dev/developing/agents/plan-verify.md` | `.claude/skills/dev/developing/agents/e2e-verify.md` |
| `.claude/skills/dev/developing/references/plan-flow.md` | `.claude/skills/dev/developing/references/e2e-flow.md` |

### 内容変更が必要なファイル

| ファイル | 変更内容 |
|----------|----------|
| `CLAUDE.md` | ワークフロールール表でPLAN→E2E |
| 上記リネーム対象ファイル | 内容中のPLAN→E2E置換 |
| `.claude/skills/dev/story-to-tasks/SKILL.md` | PLAN参照→E2E |
| `.claude/skills/dev/developing/SKILL.md` | PLAN参照→E2E |

### 変更しないファイル（「計画」の意味で使用）

以下は「計画（planning）」という意味でplanを使用しているため変更不要：

- `.claude/skills/meta-skill-creator/agents/plan-structure.md` - スキル構造の計画
- `.claude/skills/meta-skill-creator/schemas/structure-plan.json` - 構造計画スキーマ
- `.claude/skills/meta-skill-creator/schemas/update-plan.json` - 更新計画スキーマ
- `.claude/skills/meta-skill-creator/scripts/validate_plan.js` - 計画検証
- `docs/PLAN/` フォルダ - 計画書置き場
- `docs/SAMPLE/` 内のファイル - サンプル参照用

---

## 変更2: TASK追加

### TASKワークフロー

```
EXEC（実行）→ VERIFY（動作確認）→ COMMIT
```

#### EXEC（実行）

```
✓ コマンド実行
✓ ファイル作成・編集
✓ 設定変更
```

**例**:
- `npm init -y`
- `npm install vitest`
- `.eslintrc.js` 作成

#### VERIFY（動作確認）

```
✓ コマンドが正常終了するか確認
✓ 期待する出力が得られるか確認
✓ エラーがないか確認
```

**例**:
- `npm run dev` → サーバー起動確認
- `npm run lint` → エラー0件
- `npm run build` → 成功

#### COMMIT

**コミットプレフィックス**:
- `chore:` - 設定、依存関係
- `ci:` - CI/CD関連
- `docs:` - ドキュメント

### TODO.md表記

```markdown
- [ ] [TASK][EXEC] {タスク名}
- [ ] [TASK][VERIFY] {確認内容}
```

### TASK判定基準

**TASKになるもの**:
- 開発環境セットアップ
- パッケージのインストール・設定
- Linter/Formatter設定
- CI/CDパイプライン構築
- デプロイ設定
- ドキュメント作成・更新
- リファクタリング（機能変更なし）
- ファイル整理・リネーム

**TASKにならないもの**:
- ビジネスロジック → TDD
- バリデーション → TDD
- UIコンポーネント → E2E
- ユーザー操作フロー → E2E

---

## 変更対象ファイル一覧

### Phase 1: ファイルリネーム

```bash
# rules
git mv .claude/rules/workflow/plan-cycle.md .claude/rules/workflow/e2e-cycle.md
git mv .claude/rules/workflow/tdd-plan-branching.md .claude/rules/workflow/workflow-branching.md

# story-to-tasks
git mv .claude/skills/dev/story-to-tasks/agents/classify-tdd-plan.md .claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md
git mv .claude/skills/dev/story-to-tasks/references/plan-criteria.md .claude/skills/dev/story-to-tasks/references/e2e-criteria.md

# developing
git mv .claude/skills/dev/developing/agents/plan-implement.md .claude/skills/dev/developing/agents/e2e-implement.md
git mv .claude/skills/dev/developing/agents/plan-verify.md .claude/skills/dev/developing/agents/e2e-verify.md
git mv .claude/skills/dev/developing/references/plan-flow.md .claude/skills/dev/developing/references/e2e-flow.md
```

### Phase 2: 内容置換（PLAN → E2E）

| ファイル | 置換内容 |
|----------|----------|
| `CLAUDE.md` | `PLAN` → `E2E`, `plan-cycle` → `e2e-cycle`, `tdd-plan-branching` → `workflow-branching` |
| `.claude/rules/workflow/e2e-cycle.md` | タイトル・内容中のPLAN→E2E |
| `.claude/rules/workflow/workflow-branching.md` | 内容中のPLAN→E2E |
| `.claude/skills/dev/story-to-tasks/SKILL.md` | PLAN参照→E2E |
| `.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md` | 内容中のPLAN→E2E |
| `.claude/skills/dev/story-to-tasks/references/e2e-criteria.md` | 内容中のPLAN→E2E |
| `.claude/skills/dev/developing/SKILL.md` | PLAN参照→E2E |
| `.claude/skills/dev/developing/agents/e2e-implement.md` | 内容中のPLAN→E2E |
| `.claude/skills/dev/developing/agents/e2e-verify.md` | 内容中のPLAN→E2E |
| `.claude/skills/dev/developing/references/e2e-flow.md` | 内容中のPLAN→E2E |

### Phase 3: TASK追加

| ファイル | 変更内容 |
|----------|----------|
| `.claude/rules/workflow/workflow-branching.md` | TASK分類の追加 |
| `.claude/skills/dev/story-to-tasks/SKILL.md` | TASKラベル生成対応 |
| `.claude/skills/dev/story-to-tasks/agents/classify-tdd-e2e.md` | TASK分類ロジック追加 |
| `.claude/skills/dev/story-to-tasks/references/task-criteria.md` | **新規作成** |
| `.claude/skills/dev/developing/SKILL.md` | TASKワークフロー追加 |
| `.claude/skills/dev/developing/agents/task-execute.md` | **新規作成** |
| `.claude/skills/dev/developing/references/task-flow.md` | **新規作成** |
| `CLAUDE.md` | ワークフロールール表にTASK追加 |

### Phase 4: ドキュメント更新

| ファイル | 変更内容 |
|----------|----------|
| `docs/PLAN/tarot-demo-app.md` | PLAN→E2E、TASK追加 |

---

## 実装順序

1. **Phase 1**: ファイルリネーム（git mv）
2. **Phase 2**: 内容置換（PLAN → E2E）
3. **Phase 3**: TASK関連ファイル追加・更新
4. **Phase 4**: ドキュメント更新
5. **検証**: タロットデモアプリで3分類が正しく動作するか確認

---

## TODO.md使用例（更新後）

```markdown
## Story 0: 開発環境セットアップ

- [ ] [TASK][EXEC] Vite + React + TypeScript 初期化
- [ ] [TASK][EXEC] Vitest + Testing Library 設定
- [ ] [TASK][EXEC] ESLint + Prettier 設定
- [ ] [TASK][VERIFY] npm run dev / test / lint が動作することを確認

## Story 1: デッキ生成・シャッフル

- [ ] [TDD][RED] デッキ生成のテスト作成
- [ ] [TDD][GREEN] デッキ生成の実装
- [ ] [TDD][REFACTOR] リファクタリング

## Story 4: カードフリップ演出

- [ ] [E2E][IMPL] カードコンポーネント実装
- [ ] [E2E][AUTO] agent-browser検証
- [ ] [E2E][CHECK] lint/format/build
```

---

## 検証方法

タロットデモアプリで以下を確認：

1. **dev:story-to-tasks**: TDD/E2E/TASKラベルが正しく生成されるか
2. **dev:developing (TDD)**: RED→GREEN→REFACTORサイクルが回るか
3. **dev:developing (E2E)**: agent-browser検証が正しく動作するか
4. **dev:developing (TASK)**: EXEC→VERIFY→COMMITが回るか
5. **dev:feedback**: DESIGN.md更新と改善提案が生成されるか
