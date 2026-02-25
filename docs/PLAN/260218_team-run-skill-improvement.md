# team-run SKILL.md 改善計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

## 概要

`dev:team-run` の SKILL.md を **オーケストレータ（~100行）+ 参照ファイル分割** に再構成する。
単純圧縮ではなく、dev:developing パターン（SKILL.md + agents/*.md）を踏襲し、
詳細コンテキストは **Read() で必要なタイミングに読み込む参照ファイル** に分離する。

```
SKILL.md（~100行）← オーケストレータ：フロー制御 + FORBIDDEN + ゲート
  │
  ├── Read("references/agent-prompt-template.md")       ← 既存：Teammate プロンプトテンプレート
  ├── Read("references/role-catalog.md")                ← 既存：ロール定義
  ├── Read("references/teammate-spawn-protocol.md")     ← 新規：スポーン手順の詳細
  ├── Read("references/error-handling.md")              ← 新規：エラー対応の詳細
  ├── scripts/setup-worktree.sh                         ← 既存
  └── scripts/cleanup-worktree.sh                       ← 既存
```

**なぜ分割か（圧縮との違い）:**
- 圧縮: 情報を捨てる → コンテキスト喪失 → 実行精度低下
- 分割: 情報を必要なタイミングで Read() → コンテキスト維持 + SKILL.md の注意力向上

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

### ファイル一覧

| ファイル | 操作 | 説明 |
|----------|------|------|
| `SKILL.md` | **全面書き換え** | 525行 → ~100行のオーケストレータ |
| `references/teammate-spawn-protocol.md` | **新規作成** | Teammate スポーンの詳細手順（変数置換、cwd、needsPriorContext 等） |
| `references/error-handling.md` | **新規作成** | エラー対応・エスカレーション手順の詳細 |
| `references/agent-prompt-template.md` | 変更なし | Teammate プロンプトテンプレート |
| `references/role-catalog.md` | 変更なし | ロール定義 |
| `scripts/setup-worktree.sh` | 変更なし | Worktree セットアップ |
| `scripts/cleanup-worktree.sh` | 変更なし | Worktree クリーンアップ |
| `README.md` | 変更なし | hooks 設定ガイド |

### 変更1: SKILL.md → オーケストレータに再構成

**SKILL.md に残すもの（~100行）:**
- ⛔ FORBIDDEN テーブル（F1-F5）
- Teammate スポーン呼び出しパターン（1行の Read() 参照）
- Step 1-7 の DO: 命令 + ゲート: 停止条件
- エラーハンドリングの Read() 参照

**FORBIDDEN セクション（冒頭配置）:**

| ID | 禁止 | 正しい方法 |
|----|------|------------|
| F1 | Lead がコード編集・実装コード調査 | Teammate に委譲 |
| F2 | TeamCreate 前に Teammate スポーン | 必ず Step 3 完了後 |
| F3 | Worktree セットアップのスキップ | 必ず Step 2 で実行 |
| F4 | テンプレートのキャッシュ・即興生成 | 毎回 Read 必須 |
| F5 | taskPrompt 欠損タスクの実行 | STOP して dev:team-plan で修正案内 |

**Teammate スポーン呼び出し（SKILL.md 側）:**
```
protocol = Read("references/teammate-spawn-protocol.md")
→ protocol に従って Teammate をスポーン
```
dev:developing の `Read("agents/{agent}.md") → Task(...)` パターンと同じ。
SKILL.md には呼び出し1行のみ。詳細は参照ファイルに委譲。

**各 Step の形式:**
```
### Step N: タイトル

DO:
1. 具体的な命令1
2. 具体的な命令2

ゲート: 条件を満たさなければ次に進まない
```

### 変更2: references/teammate-spawn-protocol.md（新規）

現行 SKILL.md の Step 4-1 から抽出。Teammate スポーン時に Read() で読み込む。

**含める内容（~60行）:**
- プロンプト構築手順（6ステップ）
  1. agent-prompt-template.md を Read（毎回必須）
  2. role-catalog.md から role_directive 取得
  3. story-analysis.json から customDirective + fileOwnership 取得
  4. task-list.json から description, inputs, outputs, taskPrompt 取得
  5. テンプレート変数の置換ルール（変数一覧参照）
  6. 作業ディレクトリ指定 + needsPriorContext 対応
- Task() 呼び出しの具体的なパラメータ
  - model: opus（全ロール共通）
  - run_in_background: true
  - subagent_type: "general-purpose"
- レビュー系ロール（reviewer, tester）の Subagent パターン
- Plan Approval フローの詳細（requirePlanApproval: true 時）
- Self-claim Protocol の参照案内（→ agent-prompt-template.md に記載済み）
- Teammate 間メッセージプロトコル

**なぜ分離するか:** Teammate スポーンは最も複雑な手順であり、SKILL.md に残すと
注意力が分散する。Read() で必要時に読み込むことで、スポーン時のコンテキストを最大化。

### 変更3: references/error-handling.md（新規）

現行 SKILL.md のエラーハンドリングセクションから抽出。

**含める内容（~40行）:**
- エラーパターンテーブル（状況 → 対応 → エスカレーション基準）
- Teammate 遅延・失敗時のエスカレーション手順
  1. SendMessage で状況確認（5分無応答後）
  2. 再スポーン（さらに5分無応答後）
  3. AskUserQuestion でユーザーに報告（3回リトライ失敗後）
- hooks 関連（TeammateIdle / TaskCompleted の検証内容）
- Wave 完了判定の詳細チェックリスト

### 変更4: 現行 SKILL.md から削除する内容

以下は参照ファイルに既にあるか、新規参照ファイルに移動:

| 現行の内容 | 移動先 |
|-----------|--------|
| Plan Approval 詳細 | → teammate-spawn-protocol.md |
| Self-claim Protocol 詳細 | → agent-prompt-template.md に記載済み |
| Teammate 間メッセージプロトコル | → teammate-spawn-protocol.md |
| hooks 詳細説明 | → README.md に記載済み + error-handling.md |
| エスカレーション手順詳細 | → error-handling.md |
| モデル選択戦略テーブル | → 「全ロール opus」1行に圧縮 |
| レビュー・フィードバック詳細（5-2～5-7） | → SKILL.md 内で簡潔化（Read 不要な程度） |

## 影響範囲

| ファイル | 変更 | 影響 |
|----------|------|------|
| `SKILL.md` | 全面書き換え | 525行 → ~100行オーケストレータ |
| `references/teammate-spawn-protocol.md` | 新規作成 | ~60行。Teammate スポーン詳細 |
| `references/error-handling.md` | 新規作成 | ~40行。エラー対応詳細 |
| `references/agent-prompt-template.md` | なし | テンプレートそのまま |
| `references/role-catalog.md` | なし | ロール定義そのまま |
| `scripts/*.sh` | なし | スクリプトそのまま |
| `README.md` | なし | hooks ガイドそのまま |
| `CLAUDE.md` | なし | スキル説明そのまま（名称・トリガー変更なし） |

## タスクリスト

### Phase 1: 分析（完了）

- [x] 現行 SKILL.md の全文読み込みと問題箇所の特定
- [x] dev:story / dev:developing の成功パターン分析
- [x] 参照ファイル（template, catalog, scripts）の内容確認

### Phase 2: 実装（完了）

- [x] `references/teammate-spawn-protocol.md` 新規作成（~60行）
- [x] `references/error-handling.md` 新規作成（~40行）
- [x] `SKILL.md` 全面書き換え（525行 → ~174行オーケストレータ、frontmatter 50行含む）

### Phase 3: 検証（完了）

- [x] 新旧対照確認: 現行の全ステップ・ゲートが新構成で網羅されているか → 全110+項目網羅確認済み
- [x] 各参照ファイルの Read() パスが正しいか確認 → 全6パス一致確認済み

## 新 SKILL.md の設計案

### 構造（~100行 + frontmatter ~50行）

```
---
(frontmatter: ~50行 - hooks 含む、現行ベース)
---

# dev:team-run（~3行）
  1文の概要 + 引数説明

## ⛔ FORBIDDEN（~10行）
  F1-F5 テーブル（禁止 | 正しい方法）

## Teammate スポーン（~8行）
  Read("references/teammate-spawn-protocol.md") への委譲パターン
  ※ dev:developing の Read("agents/{agent}.md") → Task(...) と同じ

## Step 1: 計画選択 + Pre-flight（~12行）
  DO: 引数 or Glob → Read → AskUserQuestion → 8フィールド検証
  ゲート: Pre-flight 全合格

## Step 2: Git Worktree セットアップ（~10行）
  DO: git status → git push/pull → setup-worktree.sh → ブランチ確認
  ゲート: $WORKTREE_PATH 有効 + 正しいブランチ

## Step 3: チーム作成 + タスク登録（~10行）
  DO: TeamCreate → TaskCreate × N → blockedBy 設定 → TaskList 確認
  ゲート: TeamCreate 成功 + 全タスク登録。以降 Delegate mode

## Step 4: Wave 実行ループ（~15行）
  DO: 各 Wave で →
    実装系: Read("references/teammate-spawn-protocol.md") に従ってスポーン
    レビュー系: Task(subagent_type: "general-purpose") で Subagent
  VERIFY: 全タスク completed + outputs 存在 + コミットあり
  → 次 Wave / 全完了 → Step 5

## Step 5: レビュー・フィードバック（~10行）
  DO: 改善候補集約 → AskUserQuestion → fix タスク → 再レビュー（最大3回）
  ゲート: ユーザー承認 or 3ラウンド超過

## Step 6: PR + クリーンアップ（~8行）
  DO: git push → gh pr create → cleanup-worktree.sh
  ゲート: PR URL 取得

## Step 7: 結果集約 + TeamDelete（~8行）
  DO: 結果テーブル → metadata.status 更新 → SendMessage shutdown → TeamDelete()

## エラーハンドリング（~3行）
  Read("references/error-handling.md") + 1行サマリ
```

### 設計原則

1. **オーケストレータ + 参照ファイル分離** — SKILL.md はフロー制御のみ。詳細は Read() で必要時に読み込む
2. **dev:developing パターン踏襲** — `Read("agents/{agent}.md") → Task(...)` と同じ構造
3. **DO: + ゲート: 形式統一** — 各ステップが命令 + 停止条件で構成
4. **FORBIDDEN を冒頭に** — 最も重要な制約が最初に読まれる
5. **テーブル形式を活用** — 散文よりテーブルの方が LLM の遵守率が高い
6. **情報ゼロロスの分割** — 圧縮（情報削除）ではなく分割（情報再配置）
