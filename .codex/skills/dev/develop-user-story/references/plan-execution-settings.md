# PLANの推奨実行設定

PLANを新規作成するとき、または既存PLANの実行責務を意味的に変更するときに読む。推奨設定は、PLANを実行するtaskの開始値を示す。製品契約、実行権限、Gate、検証水準の代わりにはしない。

## 1. PLAN冒頭へ記録する

タイトルの直下へ、次の4項目を置く。

```markdown
- 推奨モデル: `gpt-5.6-sol`
- 推奨推論レベル: `xhigh`
- 選定理由: 複数の状態遷移と共有ownerを統合し、失敗・復旧を横断検証する長期実行であるため。
- 設定見直し条件: PLAN分割で統合責務がなくなる、または推奨model／推論レベルが実行環境で利用できなくなる場合。
```

modelは実行環境で選べる正確なIDを使う。`latest`、`flagship`、`高め`のように実行時の値が一意にならない書き方はしない。推論レベルは、記載したmodelが現在対応する値だけを使う。

## 2. 選定の原則

modelと推論レベルは別々に決める。modelは必要な能力と費用の均衡、推論レベルはPLAN内に残る判断の難しさで選ぶ。

PLANの長さ、条件数、変更file数だけで引き上げない。次を一次情報にする。

- 実装前に残る設計判断と、判断同士の結合度
- 通常導線、状態遷移、失敗・復旧、並行laneの相互作用
- 認証、権限、client／tenant分離、永続状態、外部作用、課金、破壊的操作の到達可能性
- focused testや型検査だけで判定できるか、実画面・実service・複数sourceの統合判断が必要か
- 誤った判断をlocalで容易に戻せるか、共有状態や利用者成果へ波及するか

最も難しい仮想ケースではなく、PLANが実際に所有する通常導線と到達可能な失敗条件で決める。未承認の外部作用や未確定の製品判断は推論レベルを上げて突破せず、既存の停止Gateを守る。

## 3. modelを選ぶ

GPT-5.6 familyが利用可能な環境では、次を開始点にする。別familyしか選べない場合も、同じ能力区分を現在のmodelへ写像する。

| model | 適用するPLAN |
| --- | --- |
| `gpt-5.6-luna` | 判断が固定済みで、排他的write scope、localで可逆な変更、強いoracleを持つ機械的なleaf。費用または大量処理を優先する場合 |
| `gpt-5.6-terra` | 契約と停止条件が固定された通常の製品実装。複数stepやtool利用はあるが、局所的な判断と再現可能な検証で完了できる場合 |
| `gpt-5.6-sol` | architecture、複数componentの状態遷移、security／分離、複雑な再利用判断、integration、弱いまたは高価なoracleを含む専門的な作業 |

進行PLAN、candidate、integration、external PLANで同じ設定を一律に複製しない。各fileが所有する作業だけを評価する。candidateが`luna`または`terra`でも、複数handoffと最終Joinを所有するintegration PLANは`sol`になり得る。

## 4. 推論レベルを選ぶ

`medium`を均衡の取れた既定値とし、具体的な理由がある場合だけ上下させる。

| 推論レベル | 適用するPLAN |
| --- | --- |
| `low` | 判断がほぼ固定済みで、短いtool chain、局所変更、強い自動oracleを持ち、速度を優先する場合 |
| `medium` | 通常の複数step実装。契約、scope、停止条件が明確で、品質・速度・費用の均衡を取る場合 |
| `high` | 複数component、非自明な状態遷移、失敗・復旧、参照sourceの適用判断など、hard reasoningが必要で遅延より品質を優先する場合 |
| `xhigh` | 複数の難しい判断が相互依存する長期のagentic作業。integration、security／分離、共有・外部状態、弱いoracleのうち複数を横断し、探索と反証が完了に直結する場合 |
| `max` | 最難関のquality-first作業で、`xhigh`との代表的な比較または過去の同種実行により追加推論の利益を説明できる場合。根拠がなければ`xhigh`を上限にする |

PLAN実行は計画、tool利用、検証を含むため、推奨値に`none`を使わない。高い推論レベルは自動的な品質保証ではない。指示が衝突している、停止条件が弱い、tool範囲が開放的という問題は、推論レベルではなくPLAN契約を修正して解消する。

## 5. 記録と見直し

`選定理由`には表のlabelを写すだけでなく、そのPLANに存在する判断負荷、失敗影響、oracleを一文で書く。`設定見直し条件`には「必要に応じて」ではなく、次のような具体的な変化を書く。

- candidateを統合する責務が加わる
- client／tenant分離や外部状態を通る新しい到達経路がscopeへ入る
- 実画面結果が前提を反証し、scheduler、queue、retry、resource lifecycle等の再設計が必要になる
- PLAN分割により判断が固定されたleafだけになる
- 推奨modelまたは推論レベルを現在の実行環境で選べなくなる

推奨より低い設定で実行しても、Gate、検証、停止条件を弱めない。設定差によって契約を完遂できない場合は、未確認の結果を完了扱いせず停止する。推奨設定だけを変更してもPLAN独立レビューGateは失効しないが、scope、risk、role、実装・検証責務が変わった場合は`SKILL.md`の規則どおり影響Gateを再開する。

## 6. 設計根拠

この基準は、2026-08-29時点のOpenAI公式資料を、PLAN実行向けに具体化したものである。

- [Model guidance](https://developers.openai.com/api/docs/guides/latest-model): `medium`をbalanced starting point、`low`をlatency-sensitive、`high`／`xhigh`を追加推論で品質向上が見込める作業、`max`を最難関のquality-first作業として扱う。高い設定を自動的に最善とせず、代表taskで比較する。
- [Models](https://developers.openai.com/api/docs/models): GPT-5.6 Solを複雑なreasoning／coding、Terraを能力と費用の均衡、Lunaを費用重視・大量処理向けとして扱う。

model family、対応推論レベル、実行環境の選択肢が変わった場合は、OpenAI公式資料を再確認し、この表を固定事実として使い続けない。
