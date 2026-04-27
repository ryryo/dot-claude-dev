# Codex Developer — Gate 契約プロンプトテンプレート (v3)

Codex モードで **Gate 単位の契約** を `task` コマンドに委任する際のプロンプトテンプレート。
TDD 以外の Gate に使用する。
Claude オーケストレーターがテンプレートの `{変数}` を埋めて `.tmp/` に書き出し、`task` コマンドに渡す。

## 実行コマンド

```bash
node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-prompt.md
```

- `--write`: ワークスペースへの書き込みを許可
- `--prompt-file`: テンプレートをファイル経由で渡す

### 並列実行（独立 Gate / 独立 Todo の場合）

```bash
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-1.md
node "$CODEX_COMPANION" task --write --background --prompt-file .tmp/codex-prompt-2.md
node "$CODEX_COMPANION" status --wait
```

## フォールバック

- task が失敗した場合: `--resume-last` でコンテキストを保持したリトライ（最大 3 回）
- 3 回失敗: Claude が `roles/implementer.md` のロール定義で直接実装

## プロンプトテンプレート

```xml
<role>
あなたは Gate 単位の契約を受け取って自律的に実装するエンジニアです。
詳細な実装手順は渡されません。Goal と Constraints の範囲内で最も合理的な方針を自分で選択し、Acceptance Criteria が全て成立する状態を作ってください。
</role>

<gate_contract>
## Gate ID
{Gate ID}

## Goal
**What**: {gate.goal.what}
**Why**:  {gate.goal.why}

## Constraints
**MUST**:
{gate.constraints.must の各項目を箇条書き}

**MUST NOT**:
{gate.constraints.mustNot の各項目を箇条書き}

## Acceptance Criteria（全て成立させること）
{gate.acceptanceCriteria の各項目を `- [AC.ID] description` 形式で}
</gate_contract>

<todos>
この Gate に属する Todo（粒度の合意と影響範囲の明示）:

{各 Todo を以下形式で}
- {Todo ID}: {title}
  - 影響ファイル: {affectedFiles の path 一覧}
  - 依存: {dependencies があれば列挙、なければ "なし"}
</todos>

<project_context>
{プロジェクトの技術スタック、ディレクトリ構造の要約 — CLAUDE.md + package.json から抽出}
</project_context>

<related_code>
{仕様書の「参照すべきファイル」を Read した内容を要約 — 10,000 文字以内に収める}
</related_code>

<structured_output_contract>
完了時に以下を返してください:
1. 変更したファイル一覧
2. 各 AC をどう成立させたか（AC ID ごとに 1-2 行）
3. 検証結果（実行したコマンド + 出力の要約）
</structured_output_contract>

<default_follow_through_policy>
確認や質問は不要。Goal と Constraints の範囲内で最も合理的でリスクの低い解釈を採用して、具体的なコード実装まで自主的に完了すること。
</default_follow_through_policy>

<completeness_contract>
全 AC が成立する状態まで完全に到達してから停止すること。
実装途中で止めない。ビルドエラーやテスト失敗がある場合は修正まで行うこと。
途中で AC が成立したら tasks.json の該当 AC の checked: true を書き込むこと。
</completeness_contract>

<verification_loop>
完了前に各 AC を検証手段（コマンド / テスト / HTTP など）で実行し、結果が成立していることを確認すること。
検証に失敗した場合、最初の結果ではなく修正版を返すこと。
</verification_loop>

<action_safety>
変更は Goal と Constraints のスコープに厳密に限定すること。
git commit は行わない（オーケストレーターが行う）。
既存コードの構造・命名規則・スタイルに合わせること。
Constraints の MUST NOT を決して破らないこと。
関係のないリファクタリングやクリーンアップは行わない。
{仕様書の設計決定事項があれば追記}
</action_safety>
```

## テンプレート変数の埋め方

| 変数 | 取得元 | 注意事項 |
|------|--------|----------|
| `{Gate ID}` | `tasks.json.gates[].id` | そのまま |
| `{gate.goal.what}` / `{gate.goal.why}` | `tasks.json.gates[].goal` | そのまま引用 |
| `{gate.constraints.must / mustNot}` | `tasks.json.gates[].constraints` | 各項目を箇条書き |
| `{gate.acceptanceCriteria}` | `tasks.json.gates[].acceptanceCriteria` | id + description を箇条書き |
| `{Todo リスト}` | `tasks.json.gates[].todos` | id / title / affectedFiles / dependencies |
| `{プロジェクト技術スタック}` | CLAUDE.md + package.json | 簡潔に要約 |
| `{参照すべきファイル要約}` | spec.md の「参照すべきファイル」を Read | 10,000 文字以内。超える場合は型定義に絞る |
| `{設計決定事項}` | spec.md の「設計決定事項」 | あれば `<action_safety>` に追加 |

## コンテキストサイズの目安

| サイズ | 判定 | 対応 |
|--------|------|------|
| < 3,000 文字 | 最適 | そのまま使用 |
| 3,000-10,000 文字 | 許容 | 不要な部分を削除して使用 |
| > 10,000 文字 | 要圧縮 | 関数シグネチャ・型定義・インターフェースに絞る |
