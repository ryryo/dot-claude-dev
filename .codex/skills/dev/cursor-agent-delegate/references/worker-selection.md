# ワーカー選定

ワーカーは main Codex が選ぶ。目的、担当範囲、編集してよい範囲、検証方法が明確になるまでワーカーを選ばない。

## ワーカー種別

| Worker | 任せる作業 | 任せない作業 |
|--------|------------|--------------|
| `codex-subagent` | 複雑な domain logic、algorithm、状態遷移、設計比較、risk analysis、難しい review、test strategy | 最終統合、完了判定、commit、push、PR |
| `cursor-agent` | 局所実装、pure function、adapter、schema、validator、unit test、既存 pattern に沿う編集 | 曖昧な仕様、横断的な state/routing/auth/migration、深い architecture 判断 |
| `main-codex` | orchestration、scope 判断、最終 review、統合、progress 更新、commit、PR | 安全に委任できる並列作業 |

## 判断ルール

- 速度より深い推論が重要なタスクは `codex-subagent` を使う。
- タスクが範囲限定で、機械的に実装しやすく、command で検証しやすい場合は `cursor-agent` を使う。
- 要件が曖昧、次の local step が結果待ち、または最終統合判断が必要な場合は `main-codex` に残す。
- ワーカーが編集するファイルが重ならない場合だけタスクを分割する。同じファイルを編集する可能性があるなら分割しない。
- この skill では Git worktree を使わない。1 つの repository workspace を使い、worker ごとに編集してよい file を明示する。
- ワーカーの出力は、main Codex が review するまで信用しない。

## Codex subagent prompt の要件

含める内容:

- 担当 file または担当責務。
- 編集を許可するかどうか。
- 他の worker が動いている可能性。無関係な変更を戻したり上書きしたりしないこと。
- 最初に読む path と関連制約。
- 検証 command または期待する review output。
- 最終報告形式。

実装作業を依頼する場合は、列挙したファイルだけを編集し、変更ファイルを final report に書くよう伝える。

## Cursor Agent prompt の要件

[delegation-prompt-template.md](delegation-prompt-template.md) を使う。短い実装と command verification で判断できるタスクを優先して Cursor Agent に任せる。
