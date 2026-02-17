# team-opencode-plan -> team-plan リネーム + native 実行化 計画

## 注意書き

この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。各タスクの進捗状況を適切に管理し、完了したタスクにはチェックを入れること。

## 概要

`dev:team-opencode-plan` スキルを `dev:team-plan` にリネームし、計画フェーズ（ストーリー分析・タスク分解）を opencode 依存から native 実行（Claude Code が直接ツールで実行）に変更する。opencode は Phase 0-4 のタスクレビュー（Codex によるクロスチェック）でのみ使用する。

## 背景

現行の `team-opencode-plan` は全フェーズ（ストーリー分析、タスク分解、レビュー）で `opencode run` を使用している。これにより以下の問題が発生している:

1. **3層トークンコスト**: Lead + CC haiku + opencode 外部モデルの3層構造で計画フェーズを実行するのは過剰
2. **レイテンシ**: opencode run の起動オーバーヘッドが計画フェーズに不要な遅延を生む
3. **耐障害性**: opencode の障害がストーリー分析・タスク分解という基本作業にまで波及する
4. **名前の不整合**: 計画フェーズで opencode を使わなくなるのに `team-opencode-plan` という名前は不適切

改善提案書（`docs/PLAN/260214_team-opencode-improvement-proposals.md`）の提案1を基盤とし、ユーザー要望に基づきさらに踏み込んだ変更を行う。

## 変更内容

### 1. リネーム（全箇所統一）

| 対象 | 現在 | 変更後 |
|------|------|--------|
| スキルディレクトリ | `.claude/skills/dev/team-opencode-plan/` | `.claude/skills/dev/team-plan/` |
| スキル名（SKILL.md frontmatter） | `dev:team-opencode-plan` | `dev:team-plan` |
| トリガー | `dev:team-opencode-plan, /dev:team-opencode-plan, チーム計画` | `dev:team-plan, /dev:team-plan, チーム計画, team plan` |
| 計画出力先 | `docs/features/team-opencode/{YYMMDD}_{slug}/` | `docs/features/team/{YYMMDD}_{slug}/` |
| 初期化スクリプト内パス | `docs/features/team-opencode/` | `docs/features/team/` |

### 2. フェーズ構成の変更

| Phase | 現行 | 変更後 | 備考 |
|-------|------|--------|------|
| 0-0 | ワークスペース初期化 | ワークスペース初期化 | パス変更のみ |
| 0-1 | opencode モデル選択 | **廃止** | native 固定のため不要 |
| 0-2 | ストーリー分析（opencode run） | ストーリー分析（**native 実行**） | Claude Code が Glob/Grep/Read/Write で直接実行 |
| 0-3 | タスク分解（opencode run） | タスク分解（**native 実行**） | Claude Code が Glob/Grep/Read/Write で直接実行 |
| 0-4 | タスクレビュー（opencode codex 固定） | タスクレビュー（**opencode codex 固定を維持**） | 外部モデルによるクロスチェックの価値を維持 |

Phase 番号の付け替え:
- 0-0 → 0-0（変更なし）
- ~~0-1~~ → 廃止
- 0-2 → 0-1（ストーリー分析）
- 0-3 → 0-2（タスク分解）
- 0-4 → 0-3（タスクレビュー）

### 3. プロンプトテンプレートの変更方針

現行のプロンプトテンプレート（`references/prompts/*.md`）は opencode 向けに設計されている。native 実行では、これらをプロンプトとしてではなく「手順書」として Claude Code 自身が解釈・実行する。

#### story-analysis.md の変更

- opencode 向けの「Write the file ... with this structure」形式を、Claude Code が直接 Write ツールで実行する手順に変更
- 変数置換テーブルは維持（ただし opencode 経由でなく直接参照）
- コードベース探索指示を追加（opencode は自律的にファイル探索できたが、native ではリーダーが Glob/Grep/Read で明示的に探索する必要がある）

#### task-breakdown.md の変更

- 「Explore the codebase」セクションの指示を、Claude Code のツール（Glob/Grep/Read）での具体的な探索手順に変更
- `opencodePrompt` フィールドは**維持**（exec フェーズで引き続き opencode が使用するため）
- `{designSystemRefs}` の取得をリーダー自身が DESIGN.md やデザイントークンファイルから Read で取得する手順に変更

#### task-review.md の変更

- **変更なし**。引き続き opencode run -m openai/gpt-5.3-codex で使用

### 4. init-team-workspace.sh の変更

```diff
-WORKSPACE="docs/features/team-opencode/${DATE}_${SLUG}"
+WORKSPACE="docs/features/team/${DATE}_${SLUG}"
```

### 5. SKILL.md の構造変更（主要な差分）

- frontmatter: name, description, trigger を変更
- Phase 0-1（モデル選択）セクションを削除
- Phase 0-2 → 0-1: opencode run 呼び出しを native 実行手順に置き換え
  - プロンプトテンプレートを Read で読み込む（同様）
  - 変数置換する（同様）
  - `opencode run` の代わりに、Claude Code が自身のツールで直接実行
  - コードベース探索を Glob/Grep/Read で明示的に実施
  - story-analysis.json を Write で出力
- Phase 0-3 → 0-2: 同上のパターンでタスク分解を native 実行に変更
- Phase 0-4 → 0-3: opencode codex 固定を維持（変更なし、番号のみ変更）
- `$OC_MODEL` 変数の参照をすべて削除（Phase 0-3 でのみ codex 固定で使用）
- 「重要な注意事項」セクションの更新:
  - 「opencode コマンドは決め打ち」→ Phase 0-3 のみに限定
  - 「フォールバック禁止」→ Phase 0-3 のみに限定
  - 「計画も opencode 活用」→ 「計画は native 実行、レビューのみ opencode 活用」に変更
  - Phase 順序: 0-0 → 0-1 → 0-2 → 0-3 に更新

## 影響範囲

### 直接影響

| ファイル | 変更内容 |
|----------|----------|
| `.claude/skills/dev/team-opencode-plan/SKILL.md` | リネーム + フェーズ構成変更（ディレクトリ移動後は `team-plan/SKILL.md`） |
| `.claude/skills/dev/team-opencode-plan/scripts/init-team-workspace.sh` | 出力パス変更 |
| `.claude/skills/dev/team-opencode-plan/references/prompts/story-analysis.md` | native 実行向けに修正 |
| `.claude/skills/dev/team-opencode-plan/references/prompts/task-breakdown.md` | native 実行向けに修正 |
| `.claude/skills/dev/team-opencode-plan/references/prompts/task-review.md` | 変更なし（opencode 用のまま） |
| `.claude/skills/dev/team-opencode-plan/references/role-catalog.md` | 変更なし |
| `.claude/skills/dev/team-opencode-plan/references/templates/*.json` | metadata.ocModel フィールドの扱い検討 |
| `CLAUDE.md` | スキル一覧テーブル、コマンド一覧テーブルの更新 |

### 間接影響（team-opencode-exec）

| ファイル | 変更内容 |
|----------|----------|
| `.claude/skills/dev/team-opencode-exec/SKILL.md` | 計画入力元パス変更（`docs/features/team-opencode/` → `docs/features/team/`）、`dev:team-opencode-plan` への参照更新、計画選択 UI のディレクトリパス更新 |
| `CLAUDE.md` | exec スキルの説明文も `team-opencode-plan` → `team-plan` への参照を更新 |

### 既存計画データの扱い

`docs/features/team-opencode/` に既存の計画データがある場合:
- 既存データは移行しない（`team-opencode/` のまま残す）
- `team-opencode-exec` は旧パス（`team-opencode/`）と新パス（`team/`）の両方を検索する対応が必要（あるいは既存データが無ければ不要）

## 提案書の他の提案の扱い

| 提案 | 今回の対応 |
|------|-----------|
| **提案1（native 実行オプション）** | **今回の主題**。ただし「オプション」ではなく native 固定とし、モデル選択フェーズ自体を廃止 |
| **提案2（Teammate 間通信）** | **今回は対象外**。exec スキル側の改善であり、plan スキルとは独立。別途実施 |
| **提案3（テンプレートベースのチーム構成）** | **今回は対象外**。native 実行化の安定後に検討。plan スキルへの追加は容易（新規ファイル追加のみ）|
| **提案4（依存グラフベースのタスク実行）** | **不採用**。提案書の評価通り YAGNI |
| **提案5（Plan Approval ゲート）** | **今回は対象外**。exec スキル側の改善。task-list.json にフラグ追加するだけなので、別途実施可能 |

## タスクリスト

### Phase 1: ディレクトリ・ファイルリネーム
> ファイルシステム上の移動を先に実施し、以降の変更はすべて新パスで行う。

- [ ] ディレクトリ移動: `.claude/skills/dev/team-opencode-plan/` → `.claude/skills/dev/team-plan/`
- [ ] 既存の `docs/features/team-opencode/` の有無を確認し、移行方針を決定

### Phase 2: init-team-workspace.sh 修正

- [ ] 出力パスを `docs/features/team/` に変更
- [ ] 動作確認（dry-run でパス確認）

### Phase 3: プロンプトテンプレート修正

- [ ] `references/prompts/story-analysis.md` を native 実行向けに修正
  - opencode 用の指示構造を、Claude Code が直接実行する手順書に変換
  - 変数置換テーブルは維持
  - コードベース探索の具体的手順を追加
- [ ] `references/prompts/task-breakdown.md` を native 実行向けに修正
  - 「Explore the codebase」を Glob/Grep/Read での明示的探索に変更
  - `opencodePrompt` フィールドは維持（exec 用）
  - `{designSystemRefs}` 取得手順をリーダー自身の操作に変更
- [ ] `references/prompts/task-review.md` は変更なし（確認のみ）

### Phase 4: SKILL.md 書き換え

- [ ] frontmatter 更新（name, description, trigger）
- [ ] Phase 0-1（モデル選択）を削除
- [ ] Phase 0-2 → 0-1: ストーリー分析を native 実行に変更
  - opencode run 呼び出しをリーダー自身の Glob/Grep/Read/Write 操作に置換
  - プロンプトテンプレートは「手順書」として Read で読み込み、指示に従って実行
- [ ] Phase 0-3 → 0-2: タスク分解を native 実行に変更
  - 同上のパターン
  - コードベース探索をリーダーが明示的に実施する手順を記述
- [ ] Phase 0-4 → 0-3: 番号変更のみ（opencode codex 固定を維持）
- [ ] 「重要な注意事項」セクション更新
- [ ] `$OC_MODEL` 変数の参照を削除（Phase 0-3 は codex 固定を直接記述）
- [ ] 「必須リソース」テーブル更新（用途列の「opencode 用プロンプト」→「手順書」等）

### Phase 5: team-opencode-exec への影響対応

- [ ] `SKILL.md` の計画入力元パス更新（`docs/features/team-opencode/` → `docs/features/team/`）
- [ ] `dev:team-opencode-plan` への参照を `dev:team-plan` に更新
- [ ] 計画選択 UI のディレクトリ列挙パス更新
- [ ] 既存の `docs/features/team-opencode/` も検索対象に含めるか判断（後方互換）

### Phase 6: CLAUDE.md 更新

- [ ] 「チーム実行（Agent Teams + opencode）」セクション見出しの検討（exec は opencode のまま）
- [ ] `dev:team-opencode-plan` → `dev:team-plan` のスキル名・説明・トリガー更新
- [ ] コマンド一覧テーブルの `/dev:team-opencode-plan` → `/dev:team-plan` 更新
- [ ] exec スキルの説明文から `team-opencode-plan` への参照を `team-plan` に更新

### Phase 7: テンプレート JSON の微修正

- [ ] `task-list.template.json` の `metadata.ocModel` フィールドの扱い決定
  - exec で依然使用するため維持が妥当（exec 起動時にユーザーが選択する値のプレースホルダ）
- [ ] `story-analysis.template.json` は変更不要（確認のみ）

### Phase 8: 検証
> 全変更完了後の一貫性確認。

- [ ] 新パス `.claude/skills/dev/team-plan/` 以下の全ファイルが正しく配置されていることを確認
- [ ] SKILL.md 内の相対パス参照（`references/...`, `scripts/...`）が正しいことを確認
- [ ] `init-team-workspace.sh` を実行してワークスペースが `docs/features/team/` に作成されることを確認
- [ ] CLAUDE.md のスキル一覧・コマンド一覧に不整合がないことを確認
- [ ] team-opencode-exec の SKILL.md 内で `team-plan` への参照が正しいことを確認
- [ ] コードベース全体で `team-opencode-plan` の残存参照がないことを Grep で確認（exec の正当な参照を除く）
