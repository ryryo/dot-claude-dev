# worker と model の選定

plan内のtaskごとに、責任境界からownerを選ぶ。

| Worker | 選ぶtask |
| --- | --- |
| `main-codex` | shared contract、横断state / auth / routing / migration、integration、production操作、最終判断 |
| `cursor-cli-agent` | scopeを分離できる局所実装、adapter、validator、unit test、機械的変更、範囲限定の調査 |
| `codex-subagent` | 複雑なlogic / algorithm、設計比較、深い調査、risk analysis、難しいreview |

Cursor CLIで安全に完結するtaskをCodex subagentへ割り当てない。write scopeが重なるtaskはownerに関係なく並列化せず、dependencyまたはintegration batchで直列化する。

## Codex subagent model

| Model | 選ぶtask | 通常のreasoning |
| --- | --- | --- |
| `gpt-5.6-terra` | 中程度の設計調査、複数情報の統合、一般的なreview、テスト戦略 | `medium`、複雑なら`high` |
| `gpt-5.6-sol` | 難しいbounded implementation / debugging、algorithm、重大なcorrectness / security review | `high`、特に難しい場合だけ上げる |
| `gpt-5.5` | 深いresearch、設計比較、仕様矛盾の分析、独立review / second opinion | `high`、難しい分析は`xhigh` |

実装完遂が中心なら`gpt-5.6-sol`、調査・比較・批評が中心なら`gpt-5.5`、それ以外は`gpt-5.6-terra`を使う。modelを変えるだけの重複taskは作らない。

起動直前にsubagent schemaを確認し、利用できるmodel / reasoningだけを指定する。ユーザー指定は利用可能なら優先する。選定値が使えない場合は黙って置換せず、taskを別model、Cursor CLI、main Codexのいずれかへ割り当て直し、planへ理由を記録する。

Codex subagentはplanに書いた`model`と`reasoning_effort`を起動引数へ設定する。Cursor CLI modelは`composer-2.5-fast`固定。

Model references: [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [GPT-5.5](https://developers.openai.com/api/docs/models/gpt-5.5)
