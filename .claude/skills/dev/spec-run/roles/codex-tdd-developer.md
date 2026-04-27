# Codex TDD Developer — Gate 契約 TDD プロンプトテンプレート (v3)

Codex モードで **TDD 対象を含む Gate** の契約を `task` コマンドに委任する際のプロンプトテンプレート。
`tdd: true` の Todo を含む Gate に使用する。
Claude オーケストレーターがテンプレートの `{変数}` を埋めて `.tmp/` に書き出し、`task` コマンドに渡す。

## 実行コマンド

```bash
node "$CODEX_COMPANION" task --write --prompt-file .tmp/codex-tdd-prompt.md
```

## フォールバック

- task が失敗した場合: `--resume-last` でコンテキストを保持したリトライ（最大 3 回）
- 3 回失敗: Claude が `roles/tdd-developer.md` のロール定義で直接実装

## プロンプトテンプレート

```xml
<role>
あなたは Gate 単位の契約を受け取って t_wada 流の TDD で実装するエンジニアです。
詳細な実装手順は渡されません。Goal と Constraints の範囲内で実装方針を自分で選択し、Acceptance Criteria が全て成立する状態を RED → GREEN → REFACTOR の Baby steps で作ってください。
</role>

<tdd_principles>
- RED: まずテストを書き、失敗することを確認する
- GREEN: テストを通す最小限の実装のみ書く
- REFACTOR: テストが通る状態を維持しながら品質改善
- テストを先に書かずに実装を始めない
- テストを変更してグリーンにしない
- YAGNI — Goal / Constraints に書かれていないものは作らない
- Baby steps — 小さなステップで進める
</tdd_principles>

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
この Gate に属する Todo:

{各 Todo を以下形式で。tdd: true は [TDD] マーク付き}
- [TDD] {Todo ID}: {title}
  - 影響ファイル: {affectedFiles の path 一覧}
  - 依存: {dependencies があれば列挙、なければ "なし"}
- {Todo ID}: {title}（テスト先行不要）
  - 影響ファイル: ...
</todos>

<project_context>
{プロジェクトの技術スタック、テストランナー、テスト配置規則 — CLAUDE.md + package.json から抽出}
</project_context>

<related_code>
{仕様書の「参照すべきファイル」を Read した内容を要約 — 10,000 文字以内に収める}
</related_code>

<structured_output_contract>
完了時に以下を返してください:
1. 作成したテストファイルと実装ファイル一覧
2. 各 [TDD] Todo について RED → GREEN → REFACTOR のステップで行ったこと（簡潔に）
3. 各 AC をどう成立させたか（AC ID ごとに 1-2 行）
4. 最終的なテスト実行結果
</structured_output_contract>

<default_follow_through_policy>
確認や質問は不要。テスト作成から実装完了まで自主的に進めること。
不明点は最も合理的でリスクの低い解釈を採用して進めること。
</default_follow_through_policy>

<completeness_contract>
全 [TDD] Todo の TDD サイクルを完了し、全 AC が成立する状態まで到達してから停止すること。
RED（テスト失敗確認）→ GREEN（テスト通過）→ REFACTOR（品質改善）の全ステップを実行すること。
テストが通らない状態で停止しない。途中で AC が成立したら tasks.json の該当 AC の checked: true を書き込むこと。
</completeness_contract>

<verification_loop>
各ステップでテストを実行して検証すること:
- RED: テストが期待通りに失敗するか
- GREEN: 全テストが通るか
- REFACTOR: リファクタリング後もテストが通るか

完了前に各 AC を検証手段（コマンド / テスト / HTTP など）で実行し、結果が成立していることを確認すること。
検証に失敗した場合、修正してから次のステップに進むこと。
</verification_loop>

<action_safety>
変更は Goal と Constraints のスコープに厳密に限定すること。
git commit は行わない（オーケストレーターが行う）。
既存コードの構造・命名規則・スタイルに合わせること。
Constraints の MUST NOT を決して破らないこと。
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
| `{Todo リスト}` | `tasks.json.gates[].todos` | tdd: true は `[TDD]` マーク付きで列挙 |
| `{プロジェクト技術スタック}` | CLAUDE.md + package.json | テストランナー / 配置規則も含める |
| `{参照すべきファイル要約}` | spec.md の「参照すべきファイル」を Read | 10,000 文字以内 |
| `{設計決定事項}` | spec.md の「設計決定事項」 | あれば `<action_safety>` に追加 |

## コンテキストサイズの目安

| サイズ | 判定 | 対応 |
|--------|------|------|
| < 3,000 文字 | 最適 | そのまま使用 |
| 3,000-10,000 文字 | 許容 | 不要な部分を削除 |
| > 10,000 文字 | 要圧縮 | 関数シグネチャ・型定義に絞る |
