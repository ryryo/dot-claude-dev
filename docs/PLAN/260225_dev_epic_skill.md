# dev:epic スキル作成計画

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。

## 概要

フィーチャー全体の設計・ストーリー分割を行う `dev:epic` スキルを新規作成し、`dev:story` / `dev:developing` に最小限の連携機能を追加する。

## 背景

現状の `dev:story` は個別ストーリーの分析→タスク分解を行うが、フィーチャー全体の設計・ストーリー分割の上位レイヤーがない。
`plan-doc` は汎用的な計画書作成だが、`docs/FEATURES/` のストーリー駆動開発フローとは統合されていない。

この2つを組み合わせ、**フィーチャーレベルの設計 → ストーリー分割 → 個別ストーリー詳細化** という階層を作る。

## 変更内容

### 1. 新規: `dev:epic` スキル

**出力ファイル**: `docs/FEATURES/{feature-slug}/` に以下を生成

| ファイル | 用途 |
|----------|------|
| `PLAN.md` | 人間用の設計ドキュメント（全体設計、背景、変更内容、影響範囲、ストーリー一覧、実行戦略） |
| `plan.json` | 構造化データ（stories配列、依存関係、優先度、メタデータ） |

**PLAN.md の構成**（plan-doc `.claude/commands/plan-doc.md` をベースに拡張）:
- 注意書き ← plan-doc 継承
- 概要 ← plan-doc 継承
- 背景 ← plan-doc 継承
- 変更内容 ← plan-doc 継承
- 影響範囲 ← plan-doc 継承
- **ストーリー一覧**（executionType・優先度・依存関係付き） ← dev:epic で追加
- 実行戦略付きタスクリスト（モデル選択基準・実行方式記法） ← plan-doc 継承

※ plan-doc の構成・記法をそのまま継承し、ストーリー一覧セクションのみ追加。plan-doc 側の改善にも追従しやすい。

**plan.json の構成**:
```json
{
  "feature": {
    "slug": "user-auth",
    "title": "ユーザー認証機能",
    "description": "..."
  },
  "stories": [
    {
      "slug": "login-form",
      "title": "ログインフォーム",
      "description": "...",
      "executionType": "developing",
      "priority": 1,
      "dependencies": [],
      "status": "pending"
    },
    {
      "slug": "oauth-dashboard-setup",
      "title": "OAuthプロバイダー設定",
      "description": "Google Cloud ConsoleでOAuthクライアントIDを作成し、リダイレクトURIを設定",
      "executionType": "manual",
      "priority": 2,
      "dependencies": [],
      "status": "pending"
    },
    {
      "slug": "env-config",
      "title": "環境変数設定ファイル追加",
      "description": ".env.exampleにOAuth関連の環境変数を追加",
      "executionType": "coding",
      "priority": 2,
      "dependencies": [],
      "status": "pending"
    },
    {
      "slug": "social-login",
      "title": "ソーシャルログイン",
      "description": "...",
      "executionType": "developing",
      "priority": 3,
      "dependencies": ["login-form", "oauth-dashboard-setup", "env-config"],
      "status": "pending"
    }
  ],
  "metadata": {
    "createdAt": "260225",
    "status": "active"
  }
}
```

**executionType の定義**:

| executionType | 意味 | 実行方法 |
|---------------|------|----------|
| `manual` | ユーザーが手動で実行 | ダッシュボード設定、外部サービス操作など。PLAN.md に手順を記載 |
| `developing` | dev:developing で実装 | dev:story → task-list.json → dev:developing のフルフロー |
| `coding` | AI で通常コーディング | dev:story 不要。直接コーディングで対応 |

analyze-epic エージェントが各ストーリーの executionType を判定する基準:
- **developing**: ビジネスロジック、UI、テスト可能な機能 → TDD/E2E/TASK 分類が意味を持つもの
- **manual**: 外部サービスの操作、GUI での設定、人間の判断が必要なもの
- **coding**: 設定ファイル追加、定型的なコード変更など、タスク分解するほどでもないもの

**ワークフロー**:
1. ユーザーからフィーチャーの要件を聞き取る
2. **analyze-epic.md（opus）** にTask委譲 — 全体設計 + ストーリー分割の内容を生成
3. **resolve-feature-slug.md（haiku）** にTask委譲 — 既存 `docs/FEATURES/*/` との重複チェック
4. AskUserQuestion で feature-slug をユーザーが最終確定
5. **init-feature-workspace.sh** を実行 — `docs/FEATURES/{feature-slug}/` ディレクトリ作成 + plan.template.json コピー
6. オーケストレーターが PLAN.md と plan.json を **Write** で保存
7. ユーザーに確認 → 承認後、dev:story で個別ストーリーを詳細化

**生成の責務**:
- analyze-epic エージェント: PLAN.md と plan.json の **内容** を生成して返す
- オーケストレーター（SKILL.md）: エージェントの出力を受けて **Write** でファイル保存

### 2. 既存変更: `dev:story` の最小変更

**変更箇所と詳細**:

#### 2a. SKILL.md の Step 1 冒頭に plan.json チェック追加

Step 1 の最初に以下の分岐を追加:

```
plan.json チェック:
1. ユーザーが feature-slug を指定 or 引数で渡している場合:
   → docs/FEATURES/{feature-slug}/plan.json を Read
2. plan.json が存在する場合:
   a. feature-slug は確定済み → resolve-slug の feature 部分をスキップ
   b. plan.json の stories 配列から executionType: "developing" かつ未完了のストーリーを AskUserQuestion で選択
   c. 選択された story 情報を analyze-story のコンテキストとして渡す
   d. story-slug は plan.json の slug を使用 → resolve-slug の story 部分もスキップ可
3. plan.json が存在しない場合:
   → 従来通りの動作（変更なし）
```

#### 2b. analyze-story.md に plan コンテキスト受け取り追加

- プロンプトに「plan.json から渡されたストーリー情報がある場合、それをベースに詳細化する。スコープは plan.json の description と整合させること」を追記

#### 2c. resolve-slug.md のスキップ条件追加

- plan.json 経由で feature-slug / story-slug が既に確定している場合、該当部分の候補生成・選択をスキップする指示を追記

#### 2d. decompose-tasks.md に planPath 書き込み追加

- plan.json が存在する場合、生成する task-list.json の `context.planPath` に `docs/FEATURES/{feature-slug}/PLAN.md` のパスを含めるよう指示を追記

### 3. 既存変更: `dev:developing` の最小変更

**変更箇所と詳細**:

#### 3a. SKILL.md の Phase 2 冒頭に planPath 参照指示を追加

以下の一文を Phase 2 の冒頭（各ワークフロー共通の前提として）に追記:

```
task-list.json の context.planPath が存在する場合、設計判断やスコープ確認が
必要な際にそのパスを Read して全体計画を参照すること。
特に以下の場面で有用:
- 実装方針に迷った場合
- スコープの境界が不明確な場合
- 他ストーリーとの依存関係を確認したい場合
```

### 4. コンテキスト連携: planPath フィールド

dev:story の decompose-tasks エージェントが task-list.json を生成する際、plan.json が存在する場合は `context.planPath` に PLAN.md へのパスを記録する。

```json
{
  "context": {
    "planPath": "docs/FEATURES/user-auth/PLAN.md",
    "description": "..."
  }
}
```

### 5. 新規: コマンドファイル

`/dev:epic` で呼び出すためのコマンドファイルを作成:

**`.claude/commands/dev/epic.md`**:
- dev:story.md / dev:developing.md と同じ形式
- dev:epic スキルを発火するエントリポイント

## 影響範囲

| ファイル | 変更種別 | 詳細 |
|----------|----------|------|
| `.claude/skills/dev/epic/SKILL.md` | **新規作成** | オーケストレーター定義 |
| `.claude/skills/dev/epic/agents/analyze-epic.md` | **新規作成** | フィーチャー分析 + ストーリー分割 |
| `.claude/skills/dev/epic/agents/resolve-feature-slug.md` | **新規作成** | 既存 feature との重複チェック |
| `.claude/skills/dev/epic/scripts/init-feature-workspace.sh` | **新規作成** | ディレクトリ初期化 |
| `.claude/skills/dev/epic/references/templates/plan.template.json` | **新規作成** | plan.json の雛形 |
| `.claude/commands/dev/epic.md` | **新規作成** | `/dev:epic` コマンド定義 |
| `.claude/skills/dev/story/SKILL.md` | **微修正** | Step 1 冒頭に plan.json チェック分岐追加 |
| `.claude/skills/dev/story/agents/analyze-story.md` | **微修正** | plan コンテキスト受け取り追記 |
| `.claude/skills/dev/story/agents/resolve-slug.md` | **微修正** | plan.json 経由時のスキップ条件追記 |
| `.claude/skills/dev/story/agents/decompose-tasks.md` | **微修正** | planPath を context に含める指示追記 |
| `.claude/skills/dev/developing/SKILL.md` | **微修正** | Phase 2 冒頭に planPath 参照指示追加 |
| `CLAUDE.md` | **更新** | スキル一覧・コマンド一覧に dev:epic 追加 |

## タスクリスト

### Phase 1: 設計・テンプレート準備
> 並列実行可能

- [ ] plan.json のスキーマ設計 `[BG:haiku:Explore]` — 既存 story-analysis.json / task-list.json との整合確認
- [ ] PLAN.md テンプレート設計 — plan-doc の構成をベースに feature 向けにカスタマイズ

### Phase 2: dev:epic スキル作成

- [ ] SKILL.md 作成 — ワークフロー定義（Step 1〜7）、エージェント委譲ルール、ゲート条件
- [ ] analyze-epic.md エージェント作成 — フィーチャー分析 + ストーリー分割ロジック、PLAN.md / plan.json の内容生成
- [ ] resolve-feature-slug.md エージェント作成 — 既存 feature との重複チェック（resolve-slug.md ベース）
- [ ] init-feature-workspace.sh 作成 — ディレクトリ作成 + plan.template.json コピー
- [ ] plan.template.json 作成
- [ ] `.claude/commands/dev/epic.md` 作成 — `/dev:epic` コマンド定義

### Phase 3: dev:story 最小変更

- [ ] SKILL.md の Step 1 冒頭に plan.json チェック分岐追加（2a の内容）
- [ ] analyze-story.md に plan コンテキスト受け取り追記（2b の内容）
- [ ] resolve-slug.md に plan.json 経由時のスキップ条件追記（2c の内容）
- [ ] decompose-tasks.md に planPath を context に含める指示追記（2d の内容）

### Phase 4: dev:developing 最小変更

- [ ] SKILL.md の Phase 2 冒頭に planPath 参照指示追加（3a の内容）

### Phase 5: 統合・ドキュメント

- [ ] CLAUDE.md にスキル追加（スキル一覧テーブル + コマンド一覧テーブル）
- [ ] 動作確認（dev:epic → dev:story → dev:developing の一気通貫フロー）

## リスク・考慮事項

- **plan.json と story-analysis.json の情報重複**: plan.json はフィーチャーレベルの粗い情報（slug, title, description, priority, dependencies）、story-analysis.json はストーリーレベルの詳細情報（scope, acceptanceCriteria 等）と棲み分ける
- **dev:story 単体利用の互換性**: plan.json がない場合は従来通り動作するようにガード条件を入れる。全ての変更箇所で「plan.json が存在しない場合 → 従来通り」の分岐を明記
- **plan.json の status 管理**: dev:developing が Phase 3 で task-list.json の metadata.status を "completed" に更新する既存の仕組みに合わせ、dev:story 側でも story 完了時に plan.json の該当 story の status を更新する処理を入れる（dev:story の最後 or dev:developing の Phase 3 に追加）。ただし初回リリースでは保留し、手動更新で運用可能
- **resolve-slug との責務分担**: dev:epic の resolve-feature-slug.md と dev:story の resolve-slug.md は似た処理。resolve-feature-slug.md は resolve-slug.md をベースに feature 部分のみに特化させ、コードの重複を最小化する
