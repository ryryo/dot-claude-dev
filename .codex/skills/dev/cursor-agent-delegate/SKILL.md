---
name: cursor-agent-delegate
description: |
  事前設計が必要な中〜大規模作業についてrepositoryを調査し、依存関係・設計境界・複雑さ・判断の確定度・実装の独立性・副作用・検証oracle・実行主体・UI/UX契約・統合順・完了条件を持つsingle-md計画を `docs/PLAN/{YYMMDD}_{slug}.md` に作成して実行する。fixedまたはboundedな判断、独立した実装、排他的write scope、再現可能なoracle、可逆な副作用を備えた実装をheadless Cursor CLIへ委任する。Codex subagentは独立した調査・比較・監査・障害分析・レビューに限定する。Trigger: cursor-agent-delegate、Cursorで計画、worker委任計画、依存関係やUI受け入れを設計して実装
---

# cursor-agent-delegate

main Codexが計画、設計判断、worker選定、進捗管理、統合、最終検収を一貫して担う。

## 適用範囲

複数moduleやstageが絡み、実装前に依存関係、shared contract、統合順を固定する必要がある作業に使う。短期の局所作業には`cursor-agent-sprint-cli`、owner/modelやtask graphまで不要な永続チェックリストには`simple-plan`を使う。

## 参照先

- 計画template: [templates/plan.md](templates/plan.md)
- 実行主体・独立性・副作用・検証oracle・modelのsource of truth: [references/task-routing.json](references/task-routing.json)
- worker prompt: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLI操作: [references/operations.md](references/operations.md)
- 検収: [references/review-checklist.md](references/review-checklist.md)
- UI契約（UI影響がある場合のみ）: [references/ui-contract.md](references/ui-contract.md)

## Cursor能力の前提

Composer 2.5の適用範囲には、long-horizon task、multi-file change、数百tool call、testをoracleにしたfeature deletion/reimplementationを含める。Fast variantは発表上Standardと同じintelligenceとして扱う。[Composer 2.5](https://cursor.com/blog/composer-2-5)と[Composer model page](https://cursor.com/composer)を根拠とする。

Cursor実装には、固定contract、negative test、scope制限、mainによるdiff検収を必須とする。公称benchmarkの未達成caseと公式記事が報告するtraining時のreward hackingを、この検収要件へ反映する。

## 所有と委任

実行主体は判断の確定度、実装の独立性、write scope、検証oracle、副作用と可逆性から決める。complexityは工数、prompt量、timeout、検証強度へ反映する。Codex subagentは補助workstreamに限定する。

1. **main Codex所有**
   未解決のarchitecture/product/security判断、shared contractやstate ownershipの決定、反復調整が必要な結合実装、外部・不可逆state変更、統合、最終検収を扱う。
2. **Cursor実装**
   contractと判断がfixedまたは決定規則付きでbounded、実装がindependentまたはstaged、write scopeがisolatedまたはserializable、検証oracleがstrongまたは限定可能なpartial、副作用が可逆な実装を扱う。complexityは`low`、`medium`、`high`を対象とする。
3. **Codex subagentによる補助workstream**
   独立したコード調査、複数案・仮説の比較、read-only audit、test/log/障害原因分析、独立レビューだけを扱う。sourceを編集させず、mainが結果を要約・採否判断する。小さな調査や、前後の判断と密結合な分析はmainが直接行う。

Cursorが利用できない実装はmainが所有する。Codex subagentの範囲は補助workstreamに維持する。

auth、secret、crypto、crash/retry/lease、外部providerなどのrisk modifierには、mainが固定するinvariant、negative case、禁止副作用、real secretやproduction stateを使わないoracle、局所rollbackを必須controlとして設定する。controlを満たす実装はCursor、満たせない実装はmainが所有する。

未解決判断または結合実装を含むtaskは、次の所有境界へ分割する。

1. mainがcontract、invariant、acceptance oracle、integration boundaryを固定する。
2. Cursorが参照実装の適応、feature deletion/reimplementation、adapter、codec、validator、fixtureを分離scopeで実装する。
3. mainがrisk-specific verification、統合、最終acceptanceを行う。

分割で同じsourceの往復編集が増える、契約固定だけで実装がほぼ終わる、context再構築と検収costが利益を上回る場合は分割しない。

## UI / UX契約

まずplanの`Planning policy`で`UI / UX contract`を`required`か`not_applicable`に判定する。UI変更が1つも無いplanは`not_applicable`とし、以下と[ui-contract.md](references/ui-contract.md)を適用しない。planのUI節も削除する。

`required`の場合、UI品質を任意の記述欄に置かない。**任意欄は実行圧力で落ちる。** 実際に、旧構成で作られた30 taskのplanでは`- UI / UX:`欄の残存が0/30だった一方、workerの起動に必須な欄（Write scope、Forbidden、Verificationなど）は30/30残った。したがってUI規約は次の3箇所だけへ載せる。

1. **task graph上のgate task**（Status boardに出るため省略できない）
2. **task contractの`Forbidden`**（worker promptへ必ず転記される）
3. **task contractの`Worker verification` / `Main verification`**（実行可能なcommandとして残る）

`Read scope`へdesign systemのpathを入れても義務にはならない。読んでよい、と読み替えられる。

UI実装taskが1つでもあるplanは、次の3段をtask graphへ必ず入れる。詳細と各gateの中身は[ui-contract.md](references/ui-contract.md)に従う。

```
UI-F (UI Foundation Gate, main所有)
  └─> 各UI実装task (surface)
        └─> UI-I (UI Design Integration Gate, main所有)
```

- **UI-F**は全UI実装taskの前段。component mapping、token allowlist、共通surfaceのowner、label方針、i18n方針、layout/theme/density、そして**repository固有のstatic scan command**を具体値で確定し、planの`## UI foundation`節へ書き切る。これが未完了のUI実装taskを起動しない。
- **各UI実装task**は、ui-contract.mdの固定blockを`Forbidden`と`Worker verification`へliteralで転記する。要約・言い換えをしない。
- **UI-I**は全UI実装taskの後段。surfaceを個別に見るのではなく、**全surfaceを1つの比較表へ並置して差分を見る**。同一意味のaction・error・success・loading・empty・disabled・承認surface・密度・配置が一致するかを横断で確認する。目視の前にUI-Fが定めたstatic scanを変更範囲全体へ再実行する。
- UI-Iは`deferred`にできない。`done`か`blocked`のみ。検出済みの違反を後追いtaskへ移してplanを`done`にしない。

UI-FとUI-Iはmain所有で、Cursorにもsubagentにも委任しない。Cursorへ委任できるのはUI-Fが値を確定した後、product判断を増やさず独立したwrite scopeとvisual/behavior oracleを持つsurface実装である。subagentはUI調査、比較、audit、独立レビューのread-onlyに限る。参照UIがある場合、参照traceは`## Reference UI trace`へ分けて書き、`## UI foundation`のdesign system規約を置き換えない。viewport、theme、evidence形式はrepository固有の要件を優先する。

## 実行フロー

### 1. repositoryを調査する

目的、対象外、現状、設計境界、shared contract、UI影響、検証方法を確認する。task graphを左右する未解決事項は、追加調査またはユーザー確認で解消する。ここでUI影響の有無を判定し、`Planning policy`の`UI / UX contract`を確定する。

### 2. planを初期化する

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
"$SKILL_DIR/scripts/init_plan.sh" --workspace "$WORKSPACE" --slug <slug>
```

### 3. task graphと契約を設計する

[task-routing.json](references/task-routing.json)を読み、次の順で各taskを解決する。

1. non-delegable ownership boundary
2. decision state
3. implementation independence
4. write scope isolation
5. verification oracle
6. side-effect scopeとreversibility
7. complexityに応じたprompt量、timeout、検証強度
8. 必要な場合だけsupport workstream eligibility
9. execution surface availability

planへ`policy_id`、work kind、complexity、decision state、independence、side-effect scope、verification oracle、execution route、理由、owner、model/reasoning、read/write scope、acceptance、worker/main verificationを記録する。subagent taskには、並列化またはcontext隔離の具体的な利益と、mainが受け取る成果物を記録する。

`UI / UX contract: required`の場合は、UI実装taskを1つでも置く前にUI-FとUI-Iをtask graphへ追加し、Status boardの`UI`列を全taskへ埋める（`foundation | surface | integration | -`）。UI実装taskの`Depends on`にUI-Fを、UI-Iの`Depends on`に全UI実装taskを入れる。

### 4. 実行前レビューを行う

最初のworkerを起動する前に次を確認し、問題があればplanを修正する。

- 依存関係の循環、未確定contract、write scopeの重複
- 検証不能なacceptance、未設定のowner/model
- execution routeが判断状態、独立性、write scope、oracle、副作用と可逆性から決まり、complexityが実行量と検証強度へ反映されていること
- 未解決判断、結合write、弱いoracle、外部・不可逆副作用、最終統合がworkerへ流れていないこと
- Cursor taskが必要条件をすべて満たすこと
- subagent taskが許可用途に該当し、source writeを持たないこと

`UI / UX contract: required`のplanでは追加で次を確認する。

- UI-FとUI-Iがtask graphに存在し、依存関係が正しく張られていること
- UI-Fの成果物（component mapping、token allowlist、共通surface owner、label方針、i18n方針、layout/theme/density、static scan command）が抽象語でなく**具体値**でplanに書かれていること
- 全UI実装taskの`Forbidden`と`Worker verification`に、ui-contract.mdの固定blockがliteralで入っていること
- 共通surfaceを複数taskが独立に実装する構成になっていないこと
- static scan commandが実際に走ること（1回はmainが手元で実行して確認する）

### 5. task単位で実行する

dependenciesを満たしたtaskだけを実行する。Cursor promptとsubagent promptは[delegation-prompt-template.md](references/delegation-prompt-template.md)に従う。Cursor CLIは[operations.md](references/operations.md)で実行する。

Codex subagentを起動する場合は、planに記録したmodelとreasoning effortを起動引数へ設定する。subagentにはtask-localなsourceと契約だけを渡し、mainの結論を先に教えない。

### 6. 検収・統合する

[review-checklist.md](references/review-checklist.md)でdiff、検証結果、worker reportを照合する。mainだけがplanのstatus、decision log、統合結果を更新できる。subagentの報告は根拠であり、設計判断や完了判定そのものではない。

### 7. 完了を判定する

required taskの完了または理由付きdeferred、integration batchのacceptance、最終検証がすべてそろったときだけ完了とする。残存課題はriskまたはdeferred taskとして記録する。

`UI / UX contract: required`のplanでは、UI-Iの合格が完了の必要条件になる。UI-Iが不合格の項目を1つでも持つ間は、他taskが全て`done`でもplanを完了としない。UI-Iを`blocked`のまま残し、完了判定を出さない。**検出済みのUI違反を後追い修正taskへ移してplanを`done`にすることを禁止する。**

## 共通禁止事項

- workerにplan更新、完了判定、version control／remote操作を任せない。
- write scopeが重なるworkerを並列実行しない。
- worker reportだけで採否を決めず、既存の未コミット変更を戻さない。
- Cursor CLI preflightを通常taskにしない。CLI-level errorが起きた場合だけ実行する。
- Codex subagentにsource writeを与えない。`Mode: edit`のsubagent taskを作らない。実装が必要ならmainかCursorへ回す。
- UI-F未完了のままUI実装taskを起動しない。
- UI-FとUI-IをCursorまたはsubagentへ委任しない。
