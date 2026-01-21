# TASKラベル追加計画書

## 概要

TDD/PLAN分岐に加え、第3のカテゴリ「TASK」を追加する。
環境セットアップ、設定、インフラ構築など、テストやUI検証が不要なタスクを扱う。

## 背景・課題

現在の分類では以下のタスクが適切に分類できない：

| タスク例 | TDD? | PLAN? |
|----------|------|-------|
| 開発環境セットアップ | ❌ テスト対象ではない | ❌ UI確認不要 |
| ESLint/Prettier設定 | ❌ | ❌ |
| CI/CDパイプライン構築 | ❌ | ❌ |
| パッケージインストール | ❌ | ❌ |
| ドキュメント作成 | ❌ | ❌ |

## 解決策

### 新しい分類体系

```
タスクを分析
    ↓
入出力が明確に定義できる？
    ├─ YES → TDD（テスト駆動）
    └─ NO → 視覚的確認が必要？
              ├─ YES → PLAN（agent-browser検証）
              └─ NO → TASK（実行→動作確認→完了）
```

### 3つのワークフロー比較

| ラベル | 検証方法 | ワークフロー | 対象 |
|--------|----------|--------------|------|
| TDD | 自動テスト | RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT | ロジック、バリデーション |
| PLAN | agent-browser | IMPL→AUTO→CHECK→COMMIT | UI/UX、視覚的要素 |
| TASK | コマンド実行確認 | EXEC→VERIFY→COMMIT | セットアップ、設定、インフラ |

## TASKワークフロー詳細

### フェーズ

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

```
✓ 変更をコミット
✓ 適切なコミットメッセージ
```

**コミットプレフィックス**:
- `chore:` - 設定、依存関係
- `ci:` - CI/CD関連
- `docs:` - ドキュメント

## TODO.md表記

### ラベル形式

```markdown
- [ ] [TASK][EXEC] {タスク名}
- [ ] [TASK][VERIFY] {確認内容}
```

### 使用例

```markdown
## セットアップフェーズ

- [ ] [TASK][EXEC] Vite + React + TypeScript プロジェクト初期化
- [ ] [TASK][EXEC] Vitest インストール・設定
- [ ] [TASK][EXEC] ESLint + Prettier 設定
- [ ] [TASK][VERIFY] npm run dev / test / lint が動作することを確認

## 機能実装フェーズ

- [ ] [TDD][RED] デッキ生成のテスト作成
- [ ] [TDD][GREEN] デッキ生成の実装
...
```

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `.claude/rules/workflow/tdd-plan-branching.md` | TASK分類の追加 |
| `.claude/skills/dev/story-to-tasks.md` | TASKラベル生成対応 |
| `.claude/skills/dev/developing.md` | TASKワークフロー追加 |
| `CLAUDE.md` | ワークフロールール表の更新 |

## TASK判定基準

### TASKになるもの

- 開発環境セットアップ
- パッケージのインストール・設定
- Linter/Formatter設定
- CI/CDパイプライン構築
- デプロイ設定
- ドキュメント作成・更新
- リファクタリング（機能変更なし）
- ファイル整理・リネーム

### TASKにならないもの

- ビジネスロジック → TDD
- バリデーション → TDD
- UIコンポーネント → PLAN
- ユーザー操作フロー → PLAN

## 実装順序

1. `tdd-plan-branching.md` にTASK分類を追加
2. `developing.md` にTASKワークフローを追加
3. `story-to-tasks.md` のタスク生成ロジックを更新
4. `CLAUDE.md` のドキュメントを更新
5. タロットデモアプリで検証

## 検証方法

タロットデモアプリのセットアップフェーズで検証：

```markdown
## Story 0: 開発環境セットアップ（TASK）

- [ ] [TASK][EXEC] Vite + React + TypeScript 初期化
- [ ] [TASK][EXEC] Vitest + Testing Library 設定
- [ ] [TASK][EXEC] ESLint + Prettier 設定
- [ ] [TASK][VERIFY] 開発サーバー起動確認
- [ ] [TASK][VERIFY] テスト実行確認
```
