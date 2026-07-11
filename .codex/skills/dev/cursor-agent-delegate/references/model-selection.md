# Codex subagent model の選定

worker 選定で Codex subagent を選んだ場合だけ読む。Cursor CLI で安全に完結する repository 内の低リスク task は先に `cursor-cli-agent` へ割り当てる。残った Codex subagent task の model と reasoning effort を決め、prompt、起動引数、最終報告へ同じ値を残す。

## 先に利用可能性を確認する

現在の subagent 起動 schema に表示される model override と reasoning effort を source of truth とする。この文書に値があっても、現在の schema にない model や reasoning effort は指定しない。ユーザー指定 model が利用可能なら優先する。

## 起動契約

Codex subagent の起動では `model` を省略せず、分割表で選んだ値を override に設定する。reasoning effort も同様に設定する。

```text
spawn_agent:
  agent_type: <explorer または worker>
  model: <選定 model>
  reasoning_effort: <選定 reasoning effort>
  message: <委任 prompt>
```

親 model の継承は、この skill で model 選定を行ったことにはしない。起動 schema が override を提供しない場合だけ継承し、その事実を報告する。

## 選定表

| Model | 位置づけ | 選ぶ作業 | 避ける作業 | 通常の reasoning |
| --- | --- | --- | --- | --- |
| `gpt-5.6-sol` | GPT-5.6 frontier。複雑な professional work、reasoning、coding を優先 | 難しい bounded implementation、複雑な debugging、複数制約を伴う algorithm、重大な security / correctness review | 単純な検索、機械的編集、大量の同型 task | `high`。特に難しい場合だけ `xhigh` 以上 |
| `gpt-5.6-terra` | intelligence と cost の balanced tier | 中程度の設計調査、複数情報の統合、一般的な review、テスト戦略、Cursor CLI では不足する推論 task | Cursor CLI で閉じる局所実装・定型調査、最難関の推論 | `medium`。複雑なら `high` |
| `gpt-5.5` | coding と professional work に強い frontier model | 深い research、設計比較、仕様の矛盾分析、長い文脈の統合、独立した批評・second opinion | 単純な局所編集、大量の定型 task、最新 GPT-5.6 coding 能力を優先する実装 | `high`。難しい research / review は `xhigh` |

## `gpt-5.6-sol` と `gpt-5.5` の使い分け

両方とも複雑な professional work に使えるため、task の中心で分ける。

- コードを書き、動作させ、難しい実装を完遂することが中心なら `gpt-5.6-sol`。
- 調べ、比較し、矛盾やリスクを言語化し、main Codex に判断材料を返すことが中心なら `gpt-5.5`。
- 同じ高リスク変更を独立 review する場合、実装 worker が `gpt-5.6-sol` なら review worker に `gpt-5.5` を使い、review perspective を分ける。
- model を変えるだけの重複 task は作らない。second opinion は失敗コストが高い場合だけ追加する。

この使い分けは、公式の能力説明を task orchestration 向けに具体化した skill 内の運用規則である。公式 docs は `gpt-5.6-sol` を complex reasoning / coding、`gpt-5.5` を coding / professional work に位置づけており、両者の用途を排他的には定義していない。

## 決定順序

1. repository 内の低リスク task を Cursor CLI で完結できるなら model を選ばず `cursor-cli-agent` に戻す。
2. Cursor CLI では不足する中程度の調査・review なら `gpt-5.6-terra`。
3. 最難関の coding / debugging / correctness 判断なら `gpt-5.6-sol`。
4. 深い research / 設計比較 / 独立批評なら `gpt-5.5`。
5. Codex subagent 内で判断できない場合は `gpt-5.6-terra` を既定にし、難易度が明確に高い場合だけ上げる。

## fallback

選定した model が現在の schema で利用できない場合、黙って置換しない。

| 選定 model | fallback 候補 |
| --- | --- |
| `gpt-5.6-sol` | coding 中心なら `gpt-5.6-terra`、research / review 中心なら `gpt-5.5` |
| `gpt-5.6-terra` | 複雑さが高ければ `gpt-5.6-sol`。低リスクで範囲限定できるなら `cursor-cli-agent` へ再選定 |
| `gpt-5.5` | `gpt-5.6-sol` |

fallback した model と理由を委任記録および最終報告に残す。適切な fallback がなければ main Codex が task を引き取る。

## 根拠

- `gpt-5.6-sol`: <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
- `gpt-5.6-terra`: <https://developers.openai.com/api/docs/models/gpt-5.6-terra>
- `gpt-5.5`: <https://developers.openai.com/api/docs/models/gpt-5.5>
