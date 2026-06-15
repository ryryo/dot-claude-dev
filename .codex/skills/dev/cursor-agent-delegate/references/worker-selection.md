# worker の選定

worker を選ぶのは main Codex の役割。goal・担当範囲・編集してよい範囲・検証方法が明確になるまで worker を割り当てない。

## worker の種別

| Worker | 任せる作業 | 任せない作業 |
|--------|------------|--------------|
| `codex-subagent` | 複雑な domain logic・algorithm・状態遷移・設計比較・risk analysis・難しい review・test strategy | 最終統合、完了判定、commit、push、PR |
| `cursor-agent` | 局所実装・pure function・adapter・schema・validator・unit test・既存パターンに沿う編集 | 曖昧な仕様、横断的な state / routing / auth / migration、深いアーキテクチャ判断 |
| `main-codex` | orchestration・scope 判断・最終 review・統合・progress 更新・commit・PR | 安全に委任できる並列作業 |

## 判断ルール

- 速度より深い推論が重要なタスクには `codex-subagent` を使う。
- タスクが範囲限定で機械的に実装しやすく、コマンドで検証しやすい場合は `cursor-agent` を使う。
- 要件が曖昧、次の local ステップが結果待ち、または最終統合の判断が必要な場合は `main-codex` で扱う。
- worker の編集対象ファイルが重ならない場合だけタスクを分割する。同じファイルを編集する可能性があるなら分割しない。
- このスキルでは Git worktree を使わない。1 つの repository workspace を使い、worker ごとに編集してよいファイルを明示する。
- worker の出力は、main Codex が review するまで信頼しない。

## Codex subagent prompt に含める内容

- 担当ファイルまたは担当責務
- 編集を許可するかどうか
- 他の worker が並列で動いている可能性があること。無関係な変更を元に戻したり上書きしたりしないこと
- 最初に読むパスと関連する制約
- 検証コマンド、または期待する review の出力内容
- 最終報告の形式

実装作業を依頼する場合は、指定したファイルだけを編集し、変更したファイルを final report に記載するよう伝える。

## Cursor Agent prompt に含める内容

[delegation-prompt-template.md](delegation-prompt-template.md) を使う。短い実装とコマンド検証で判断できるタスクを優先して Cursor Agent に割り当てる。
