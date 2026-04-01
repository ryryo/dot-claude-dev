# Codex Developer — 汎用プロンプトテンプレート

Codex モードで汎用タスクをプラグインの `task` コマンドに委任する際のプロンプトテンプレート。
TDD 以外のタスク（コンポーネント作成、設定、ユーティリティ等）に使用する。
Claude オーケストレーターがこのテンプレートの `{変数}` を埋めて `.tmp/` に書き出し、`task` コマンドに渡す。

## 実行コマンド

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --prompt-file .tmp/codex-prompt.md
```

- `--write`: ワークスペースへの書き込みを許可
- `--prompt-file`: テンプレートをファイル経由で渡す

### 並列実行（独立ファイルが複数の場合）

```bash
# ファイルごとに別プロンプトを作成し並列実行
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --background --prompt-file .tmp/codex-prompt-1.md
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --write --background --prompt-file .tmp/codex-prompt-2.md
# 完了待ち
node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" status --wait
```

## フォールバック

- task が失敗した場合: `--resume-last` でコンテキストを保持したリトライ（最大3回）
- 3回失敗: Claude が直接実装

## プロンプトテンプレート

```xml
<task>
以下の仕様に基づいて実装してください。

## 仕様
{仕様書の Todo IMPL 内容}

## プロジェクト情報
{プロジェクトの技術スタック、ディレクトリ構造の要約}

## 関連コード
{参照すべきファイルの内容を要約 — 10,000文字以内に収める}
</task>

<structured_output_contract>
完了時に以下を返してください:
1. 変更したファイル一覧
2. 実装の要約（1-2文）
3. 検証結果（ビルド・テスト実行の結果）
</structured_output_contract>

<default_follow_through_policy>
確認や質問は不要。具体的なコード実装まで自主的に完了すること。
不明点は最も合理的でリスクの低い解釈を採用して進めること。
</default_follow_through_policy>

<completeness_contract>
タスクを完全に解決してから停止すること。
実装途中で止めない。ビルドエラーやテスト失敗がある場合は修正まで行うこと。
</completeness_contract>

<verification_loop>
実装完了前に以下を検証すること:
- コードが仕様の要件を満たしているか
- ビルドが通るか
- 既存テストが壊れていないか
検証に失敗した場合、最初の結果ではなく修正版を返すこと。
</verification_loop>

<action_safety>
変更は指定されたタスクのスコープに厳密に限定すること。
git commit は行わない（オーケストレーターが行う）。
既存コードの構造・命名規則・スタイルに合わせること。
仕様に記載されていない機能は追加しない。
関係のないリファクタリングやクリーンアップは行わない。
{仕様書の設計決定事項があれば追記}
</action_safety>
```

## テンプレート変数の埋め方

| 変数 | 取得元 | 注意事項 |
|------|--------|----------|
| `{仕様書の Todo IMPL 内容}` | 仕様書の対象 Todo の IMPL セクション | そのまま引用 |
| `{プロジェクトの技術スタック...}` | CLAUDE.md + package.json 等 | 簡潔に要約 |
| `{参照すべきファイルの内容を要約}` | 仕様書の「参照すべきファイル」を Read | 10,000文字以内。超える場合は型定義に絞る |
| `{設計決定事項}` | 仕様書の設計決定事項セクション | あれば `<action_safety>` に追加 |

## コンテキストサイズの目安

| サイズ | 判定 | 対応 |
|--------|------|------|
| < 2,000文字 | 最適 | そのまま使用 |
| 2,000-10,000文字 | 許容 | 不要な部分を削除して使用 |
| > 10,000文字 | 要圧縮 | 関数シグネチャ・型定義・インターフェースに絞る |
