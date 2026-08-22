---
name: codex-luna-task-split
description: "5.6 Solの一つの作業に高推論の判断と低推論の実行が混在するとき、taskの種類やfile領域ではなく、判断の確定度、独立性、副作用、検証oracle、分担利益でmain CodexとLunaの担当を会話内で分ける。通常の機能開発、修正、refactor、test、設定、文書などで、Sprint用の計画・task・promptファイルを増やさず、完全固定済みのleafだけを安全にLunaへ分けたい場合に使う。Trigger: codex-luna-task-split、SolとLunaで作業分担、ファイルを作らないLuna運用、高推論と低推論の分離。"
---

# Codex Luna Task Split

main Codexが先に事実を調べ、未解決の判断を引き受ける。Lunaを前提に設計を歪めず、契約が完全に固定されたleafだけを任意で分担する。作業領域、file種別、行数、見かけの単純さをowner判定に使わない。このスキルの運用だけを理由にSprint、計画、task、prompt、進捗ファイルを作らない。

## 1. 作業を観察して候補へ切る

repository、適用される指示、最新要求、既存差分、関連実装とtestを確認する。最初は全taskをmain担当とし、利用者から観測できる成果を壊さない単位へ切る。別のproject ruleやユーザー要求がPLAN、user story、EVIDENCE等を必要とする場合は従うが、このスキル自身は追加要求しない。

高推論と低推論はtask名や実装対象ではなく、その時点で残る判断から決める。同じUI、backend、schema、Prompt、設定、test、文書でも、契約が未確定ならmain、完全に固定されていればLuna候補になり得る。逆にparserやfixtureでも、仕様解釈、trade-off、責務変更、弱い合否判定が残るならmainが担当する。

## 2. 五つの軸でownerを決める

各候補を次で分類する。

- **Decision state**: `fixed` | `bounded` | `unresolved`
- **Independence**: `independent` | `staged` | `coupled`
- **Side effect**: `local_reversible` | `shared_reversible` | `external_or_irreversible`
- **Verification oracle**: `strong` | `partial` | `weak`
- **Split benefit**: `positive` | `neutral` | `negative`

Split benefitは、mainがcontractを固定し、workerの成果を独立検収する費用まで含めて、main単独実装より時間・費用・並行性の実利が残る場合だけ`positive`とする。

次をすべて満たす一つのleafだけを`luna_sprint_worker`へ分ける。

1. Decision stateが`fixed`で、Lunaに推測、補完、選択を要求しない。
2. `independent`、または先行契約が完了した`staged`で、実行中に他taskとの調整を要しない。
3. Side effectが`local_reversible`で、排他的write scopeがある。
4. oracleが`strong`で、positive/negative caseと棄却条件を機械判定できる。
5. mainのcontract作成とdiff検収を含めてもSplit benefitが`positive`である。
6. `luna_sprint_worker`自身と適用先の指示が、その実行を許可している。

`bounded`または`unresolved`、`coupled`、共有・外部・不可逆な副作用、`partial`または`weak`なoracle、分担利益が非positiveのいずれかを含むtaskはmainが所有する。安全な候補が0件ならmain-onlyが正常である。利用可能な`luna_sprint_worker`がなければ、別agentやmodel overrideで代替せずmainが実行する。

mainは目的、制約、契約、例外、採否を確定する責任をLunaへ移さない。ただし、特定領域を一律にLuna禁止にはしない。mainが判断を完了し、上の条件とworker側の制約を満たすなら、その固定契約を同じ領域のコードや成果物へ機械的に反映する実行は候補にできる。

## 3. 会話内でtask contractを渡す

永続promptファイルを作らず、workerへ次のtask-local contractを直接渡す。計画全文の解釈をLunaへ依頼しない。

```text
Task ID: <一意なID>
Goal: <一つの固定済み成果物>
Workspace: <absolute path>
Source of truth: <absolute pathと該当箇所>
Fixed contract: <I/O、変換規則、exact behavior>
Forbidden decisions: <判断・変更してはいけない領域>
Decision state: fixed
Independence: independent | staged（完了済み依存を明記）
Side effect: local_reversible
Verification oracle: strong
Positive/negative cases: <機械判定できる例>
Write scope: <排他的なallowed paths>
Stop without changes when: <矛盾、未解決判断、scope競合、外部副作用>
Verification: <focused commandと期待結果>
Final report: <TASK_ID、変更file、検証結果、mainへ残した作業>
```

正本agent typeは`luna_sprint_worker`とし、modelやreasoning effortを上書きしない。一つのworkerには一つのleafだけを渡し、再委任、commit、push、branch変更、計画更新、外部サービス操作を禁止する。並行実行はwrite scopeと依存関係が独立している場合だけにする。

実装中に判断、契約矛盾、scope外変更、外部副作用が必要になった時点で、Lunaは変更せずmainへ返す。mainは不足した判断を確定して自分で実装するか、新しい固定contractとして改めて分担する。

## 4. mainが独立検収する

worker報告は完了証明ではなく主張として扱う。mainが実diff、scope外変更、focused test、少なくとも一つの独立negative caseを確認し、`accepted`、`corrected-by-main`、`rejected`、`blocked`を判定する。

worker testで覆えない上位の振る舞いは、mainが必要な実画面、実成果物、統合test、whole-user-journeyで確認する。全leafが通っても、利用者の成果が成立しなければ全体を完了にしない。

完了報告では、mainが所有した判断、Lunaへ分けたleafと理由、mainの独立検証、棄却・修正、残リスクを短く示す。
