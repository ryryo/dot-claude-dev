# team-run SKILL.md 改善計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

## 概要

`dev:team-run` の SKILL.md を 525行から約150行に圧縮し、LLM が全ステップを忠実に実行できるよう「DO: + ゲート:」形式に統一する。

## 背景

ユーザーが `/dev:team-run` を実行したところ、SKILL.md の指示がほぼ全て無視された。具体的な失敗:

1. TeamCreate が実行されなかった（Task ツールで直接エージェント起動）
2. Git Worktree が作成されなかった（メインリポジトリで直接作業）
3. agent-prompt-template.md が読まれなかった（テンプレートなしで汎用プロンプト使用）
4. Lead が直接コードを調査した（npm ls, package.json 読み込みなど Delegate mode 違反）
5. 計画の Pre-flight 検証がスキップされた
6. Wave 実行の構造が崩れた

### 根本原因

| # | 原因 | 影響 |
|---|------|------|
| 1 | SKILL.md が 525 行で長すぎる | LLM が全体を把握しきれず自己判断に陥る |
| 2 | 説明文（ドキュメント調）が多く命令文が少ない | 手順が曖昧に解釈される |
| 3 | 各ステップに明確な「DO:」「ゲート:」がない | ステップ飛ばしが発生 |
| 4 | FORBIDDEN ルールが文書末尾 | 目立たず無視される |
| 5 | Teammate スポーンのツール呼び出しパターンが曖昧 | Task 直打ちに退化 |

### 成功パターンの分析

`dev:story`（108行）と `dev:developing`（189行）は同様の構造で安定動作している。その共通パターン:

- 冒頭に「エージェント委譲ルール」を定義
- 各ステップが DO: 命令 + ゲート: 停止条件で統一
- テーブル形式で agent / model / type を即座に参照可能
- 「ゲート: X が存在しなければ次に進まない」で明確な停止条件

## 変更内容

### 対象ファイル

- **変更**: `.claude/skills/dev/team-run/SKILL.md`（525行 → 約150行）

### 変更なし（参照のみ）

- `references/agent-prompt-template.md`
- `references/role-catalog.md`
- `scripts/setup-worktree.sh`
- `scripts/cleanup-worktree.sh`
- `README.md`

### 具体的な変更点

#### 1. FORBIDDEN セクションを冒頭に配置

テーブル形式で禁止事項と正しい方法を対比:

| ID | 禁止 | 正しい方法 |
|----|------|------------|
| F1 | Lead がコード編集・実装コード調査 | Teammate に委譲 |
| F2 | TeamCreate 前に Teammate スポーン | 必ず Step 3 完了後 |
| F3 | Worktree セットアップのスキップ | 必ず Step 2 で実行 |
| F4 | テンプレートのキャッシュ・即興生成 | 毎回 Read 必須 |
| F5 | taskPrompt 欠損タスクの実行 | STOP して dev:team-plan で修正案内 |

#### 2. Teammate スポーンパターンを共通定義

dev:developing の「エージェント委譲ルール」に相当する共通パターンを定義:

```
1. Read("references/agent-prompt-template.md")  -- 毎回必須
2. Read("references/role-catalog.md") -> role_directive 取得
3. story-analysis.json -> customDirective, fileOwnership
4. task-list.json -> description, inputs, outputs, taskPrompt
5. テンプレート変数置換 + cwd: $WORKTREE_PATH
6. Task({ prompt: 構築済みプロンプト, model: "opus", run_in_background: true })
```

#### 3. Step 1-7 を DO: + ゲート: 形式に統一

各ステップの構造を以下に統一:

```
### Step N: タイトル

DO:
1. 具体的な命令1
2. 具体的な命令2

ゲート: 条件を満たさなければ次に進まない
```

#### 4. エラーハンドリングを1テーブルに圧縮

4パターンのみ:

| 状況 | 対応 |
|------|------|
| Teammate 無応答 10分 | 再スポーン（最大3回） |
| Worktree セットアップ失敗 | ユーザーに報告、手動対応案内 |
| Plan Approval 3回拒否 | 自動承認、リスク報告 |
| 3回リトライ失敗 | AskUserQuestion でユーザーに報告 |

#### 5. 削除する内容

参照ファイルに既にある、または不要な説明文:

- Plan Approval の詳細 → agent-prompt-template.md に記載済み
- Self-claim Protocol の詳細 → agent-prompt-template.md に記載済み
- Teammate 間メッセージプロトコルの詳細 → テンプレートで制御
- hooks の詳細説明 → README.md に記載済み
- エスカレーション手順の詳細 → テーブルで十分
- モデル選択戦略テーブル → 全ロール opus なので1行で済む
- 4-5 Teammate 間メッセージプロトコル → テンプレートに含まれている
- 5-2 ~ 5-7 レビュー・フィードバック詳細 → 簡潔なフローに圧縮

## 影響範囲

| ファイル | 変更 | 影響 |
|----------|------|------|
| `.claude/skills/dev/team-run/SKILL.md` | 全面書き換え | スキル本体の動作変更 |
| `references/agent-prompt-template.md` | なし | テンプレートはそのまま |
| `references/role-catalog.md` | なし | ロール定義はそのまま |
| `scripts/setup-worktree.sh` | なし | スクリプトはそのまま |
| `scripts/cleanup-worktree.sh` | なし | スクリプトはそのまま |
| `README.md` | なし | ドキュメントはそのまま |
| CLAUDE.md | なし | スキル説明はそのまま（名称・トリガー変更なし） |

## タスクリスト

### Phase 1: 分析

- [x] 現行 SKILL.md の全文読み込みと問題箇所の特定（この計画書で完了）
- [x] dev:story / dev:developing の成功パターン分析（この計画書で完了）
- [x] 参照ファイル（template, catalog, scripts）の内容確認（この計画書で完了）

### Phase 2: 設計

- [ ] 新 SKILL.md の構造設計（セクション構成・行数目安） `[BG:haiku:Explore]`

### Phase 3: 実装

- [ ] SKILL.md の書き換え（525行 → 約150行）

### Phase 4: 検証

- [ ] 新旧 SKILL.md の対照確認（全ステップ・ゲートが網羅されているか） `[BG:sonnet:Explore]`
- [ ] 行数・構造の最終チェック

## 新 SKILL.md の設計案

以下に、書き換え後の SKILL.md の構造案を示す。

### セクション構成（約150行）

```
---
(frontmatter: 約50行 - 現行と同じ)
---

# dev:team-run スキル（約5行）
  1文の概要

## FORBIDDEN（約10行）
  F1-F5 テーブル

## Teammate スポーンパターン（共通定義）（約15行）
  6ステップの手順

## Step 1: 計画選択 + Pre-flight（約15行）
  DO: + ゲート:

## Step 2: Worktree セットアップ（約10行）
  DO: + ゲート:

## Step 3: チーム作成 + タスク登録（約10行）
  DO: + ゲート:

## Step 4: Wave 実行ループ（約20行）
  DO: + ゲート:（Wave 完了判定含む）

## Step 5: レビュー・フィードバック（約15行）
  DO: + ゲート:

## Step 6: PR + クリーンアップ（約10行）
  DO: + ゲート:

## Step 7: 結果集約 + TeamDelete（約10行）
  DO: + ゲート:

## エラーハンドリング（約5行）
  4パターンのテーブル
```

### 設計原則

1. **各ステップは「DO: 番号付き命令リスト + ゲート: 停止条件」で統一** — dev:story / dev:developing と同じ形式
2. **説明文・理由・背景は削除** — LLM には「何をするか」だけ伝える
3. **FORBIDDEN を冒頭に** — 最も重要な制約が最初に読まれる
4. **Teammate スポーンパターンを共通定義** — Step 4 で参照するだけにする
5. **テーブル形式を活用** — 散文よりテーブルの方が LLM の遵守率が高い
6. **参照ファイルに委譲** — テンプレート詳細、ロール定義、スクリプト詳細は参照ファイルに既にある
