# 並列実行可能なPLAN設計

対象scopeが複数の独立成果へ分かれ、直列・並列の実行graphが必要な場合だけ読む。USは利用者契約、PLANは成果と実行内容の契約、進行PLANは依存graphの正本として分離する。実行主体や実行環境の識別子は計画外の管理情報とし、PLANへ記録しない。

## 1. 分割可否を先に判定する

実行PLANへ分ける候補は、次をすべて満たす場合だけ採用する。

1. 先行Gateと必要な開始状態を明示すれば、別の実行主体が追加の製品判断なしに開始できる。
2. 排他的write scopeを持ち、同じsource、generated file、lockfile、台帳、EVIDENCE、外部状態を別laneと同時変更しない。
3. 変更path、固定した公開interface、検証結果、外部操作結果など、統合ownerへ渡す成果が明確である。
4. focused test、typecheck、build、dry-runなど、handoff前にlocalで再現できる強いoracleがある。
5. merge、shared glue、生成物再生成、上位test、Journey、台帳更新を所有する統合先が一つに決まる。
6. 調整、merge、reviewの追加費用を上回る並行化または責務分離の実益がある。

条件数、技術layer、画面数、US境界だけで分割しない。同じstateやcommand/historyを連続変更する、同じfileを往復する、統合前に合否を判定できない候補は一つの実行PLANのPhaseにまとめる。

## 2. plan setを一度に作る

複数PLANが必要なら、一回の計画操作で次を揃える。

- 実行PLAN: 一つのmerge可能な成果をhandoffする契約。
- integration PLAN: 複数candidateのmerge、shared glue、生成物、上位検証、実装後review、Journey、台帳更新に実作業がある場合の実行PLAN。
- external PLAN: deploy、課金、外部データ変更など、別承認と単一ownerが必要な操作を分ける場合の実行PLAN。
- 進行PLAN: 上記PLANの依存、状態、統合順を管理するindex。実行割当は計画外で管理し、進行PLANは実装を所有しない。

integrationやexternalの作業が小さく独立成果を要しない場合は、別PLANを増やさず、既存の統合実行PLANへ含める。既存PLANを再編する場合は、検証済みの履歴を失わない。新しい実行入口を進行PLANへ一本化し、旧PLANを残すならarchive／supersededと明示して二重の正本を作らない。

実行PLAN名はUS IDや実行方式ではなく安定した成果名を使う。例: `YYMMDD_editor-shell.md`。成果名をfileのidentityとし、実行主体や実行環境はPLANの外で管理する。

## 3. 実行PLANの必須契約

[PLAN作成の共通契約](plan-workflow.md#成果と実装契約を固定する)に加え、複数PLANではroleを`candidate`、`integration`、`external`のいずれかにし、次の分担を明示する。

- 各実行PLANは担当条件ID、排他的write scope、開始Gate、handoff成果、受け取り先、focused検証、停止条件を自己完結して持つ。
- candidateは担当成果とlocal oracleの成立までを所有し、統合後Gate、実Journey、USの最終状態、共有進行PLANを更新しない。
- integration／external ownerは、必要なmerge、shared glue、生成物、lockfile、上位検証、Journey、台帳・EVIDENCE更新を引き受ける。review済み契約へ統合した結果から最終状態を更新する。

複数candidateの開始、merge、外部handoff、最終Joinを所有するintegration PLANは、自分が接続するedgeとGateをMermaidで示す。進行PLANへのlinkだけで代替せず、個別taskや台帳全体も複製しない。複数実行PLANを接続するintegration／coordination PLANには、次節以降のParallelization Topology Gate manifestも置く。

## 4. 進行PLANの必須契約

進行PLAN名は`YYMMDD_{scope}_execution.md`を既定とし、タイトル直下へ進行・coordination責務そのものに対する推奨model、推論レベル、選定理由、設定見直し条件を置く。各laneの設定はその実行PLANに記載し、全laneの最大値を進行PLANへ一律に写さない。その上で次だけを持つ。

1. 対象scope、開始Gate、全体完了条件、coordination owner。
2. Mermaid DAG。直列edge、並列lane、統合point、条件付きfallback、外部停止Gate、最終Joinを区別する。文章、一覧表、別fileへのlinkだけでは代替しない。
3. 次の列を持つPLAN台帳。

| lane | PLAN | role | 対象条件 | depends on | handoff先 | 状態 |
| --- | --- | --- | --- | --- | --- | --- |
| `<stable-id>` | `<path>` | `candidate/integration/external` | `<US-XX-NN>` | `<Gateまたはなし>` | `<lane>` | `planned/ready/active/handoff/merged/verified/blocked` |

4. source、generated file、lockfile、PLAN、台帳、EVIDENCE、外部状態のowner表。
5. candidateのmerge順、生成物再生成、上位検証、review、Journey、deployの順序。
6. 現在のready lane、停止理由、再開条件。進捗に応じて更新し、依存graphは依存契約が変わった場合だけ更新する。

並行実行時は、進行管理側がwrite scope、port、Wrangler state、生成物、外部状態を衝突させない実行contextを計画外で選ぶ。PLANには実行contextの方式や識別子を書かない。

個別PLANのPhase、command、詳細task、受け入れ条件本文を複製しない。条件IDとlinkで参照する。進行PLANの状態更新はcoordination／integration ownerだけが行い、candidate ownerはhandoff結果を返すだけにする。

## 5. Parallelization Topology Gate

### 5.1 直列化より先に境界を見直す

同じfile、generated file、lockfile、台帳、EVIDENCE、外部状態を複数成果が必要とする場合、その事実だけで成果全体を直列化しない。次の順で、現在の利用者契約を変えずに分離できるかを確認する。

1. 各成果のwrite scopeを、実際に必要なrelative pathまで狭める。
2. 両成果が必要とする最小の公開contractだけを、先行するshared seam成果として固定する。
3. shared file、generated file、台帳、EVIDENCEの更新を、候補実装後のJoinだけへ移す。
4. 上流成果がなければ下流成果を実装・検証できない真のhard dependencyだけをedgeにする。
5. それでも同じwriterを複数段階で必要とする場合だけ、serialized exceptionとしてcritical pathへの影響と1〜3を採用しない理由を残す。

shared seamは並列化のためだけに抽象化を増やす免罪符ではない。現在scopeで独立したcontract、handoff、local oracleがなく、追加調整費が並行化利益を上回るなら作らない。その場合も、直列化edgeを暗黙にせずmanifestで審査する。

### 5.2 機械可読manifest

複数実行PLANを接続するintegration／coordination PLANに、次のmarkerでJSONを1個だけ置く。Mermaidは人が読む実行図、manifestは衝突と最早waveを検査する正本であり、両方を本文のGate名・ownerへ一致させる。

````markdown
<!-- parallelization-topology:start -->
```json
{
  "schemaVersion": 1,
  "gate": "parallelization-topology",
  "integrationPlan": "docs/PLAN/YYMMDD_integration.md",
  "lanes": [
    {
      "id": "shared-seam",
      "plan": "docs/PLAN/YYMMDD_shared-seam.md",
      "section": "Phase A",
      "execution": "local",
      "writeScopes": ["apps/web/src/shared/**"],
      "externalStates": []
    },
    {
      "id": "candidate-a",
      "plan": "docs/PLAN/YYMMDD_candidate-a.md",
      "section": "Phase B",
      "execution": "local",
      "writeScopes": ["apps/web/src/feature-a/**"],
      "externalStates": []
    },
    {
      "id": "candidate-b",
      "plan": "docs/PLAN/YYMMDD_candidate-b.md",
      "section": "Phase B",
      "execution": "local",
      "writeScopes": ["apps/web/src/feature-b/**"],
      "externalStates": []
    }
  ],
  "edges": [
    {
      "from": "shared-seam",
      "to": "candidate-a",
      "classification": "shared-seam",
      "reason": "consumerは公開contract固定後に開始する",
      "evidence": "Gate Pのhandoff条件",
      "handoff": "review済みpublic interface"
    },
    {
      "from": "shared-seam",
      "to": "candidate-b",
      "classification": "shared-seam",
      "reason": "consumerは公開contract固定後に開始する",
      "evidence": "Gate Pのhandoff条件",
      "handoff": "review済みpublic interface"
    }
  ],
  "waves": [
    {"id": "wave-1", "lanes": ["shared-seam"]},
    {"id": "wave-2", "lanes": ["candidate-a", "candidate-b"]}
  ]
}
```
<!-- parallelization-topology:end -->
````

- `lanes`: 現在のplan setで実行する成果またはintegration Phaseを漏れなく列挙する。同じPLAN内の別Phaseは異なるlane IDと`section`で表せる。`plan`はrepository root内に実在し、`section`はそのPLAN本文の見出しと一致させる。fenced example内の見出しは契約に数えず、同じresolved PLAN／sectionを複数laneで所有しない。
- `execution`: `local`または`external`。外部laneは操作対象を`externalStates`へ1件以上書く。
- `writeScopes`: repository relativeのfile path、または末尾`/**`だけをwildcardとするdirectory scopeを使う。`*`を途中に含む曖昧なglob、絶対path、`..`は禁止する。sourceだけでなく、自PLAN、generated file、lockfile、台帳、EVIDENCEも実際に更新するlaneへ含める。
- `edges`: `hard-dependency`、`shared-seam`、`join`、`external-stop`、`serialized-exception`のいずれかへ分類し、`reason`、確認した`evidence`、渡す`handoff`を必須にする。
- `waves`: edgeから計算される最早waveを記録する。人員数や実行context都合で空いているlaneを後ろへ送らない。各laneは1 waveだけに置く。

writer重複をedgeで直列化する場合、そのedgeの`classification`は`serialized-exception`とし、次を追加する。

```json
{
  "resources": ["apps/web/src/shared/file.ts"],
  "criticalPathImpact": "candidate-bはcandidate-a完了まで開始できない",
  "alternatives": {
    "narrow-scope": "採用しない具体的理由",
    "shared-seam": "採用しない具体的理由",
    "join-only": "採用しない具体的理由"
  }
}
```

### 5.3 Gateの実行と判定

repository rootから次を実行する。

```bash
python3 .codex/skills/dev/develop-user-story/scripts/validate_plan_topology.py <integration-or-coordination-plan>
```

validatorは、manifestが1個だけであること、検証対象integration PLANとmanifest pathの一致、参照する各PLANとsection見出しの実在、symlink解決後もrepository root内にあること、lane／edge ID、relative write scope、DAGの閉路、最早waveとの一致、同一waveのwriter／外部状態衝突、writer重複を残す例外の代替案を検査する。成功出力にはlane数、local最大同時数、serialized exception数が出る。

validator成功に加え、次節のplan set reviewで全lane・依存・ownerの意味を確認できた場合だけGateをPASSにする。FAILまたは未確認なら実装を開始しない。

lane、write scope、外部状態、edge、shared contract、ownerを意味的に変えた場合、または実装中に未記載の共有writerが判明した場合は、production code編集を止めて本Gateとplan set reviewを再開する。進捗状態や実行contextだけの変更では再開しない。

## 6. plan set review

[PLAN独立レビューGate](plan-workflow.md#plan独立レビューgate)の役割分離に従い、同じreviewerが進行PLANと全実行PLANを一つのplan setとして確認する。共通契約に加え、次を反証する。

- 全条件IDに実装ownerと最終確認ownerがあり、重複・空白・未確認の完了扱いがない。
- Parallelization Topology Gateのvalidatorが成功し、全実行laneがmanifestにあり、graphに閉路、不要な直列待ち、未記載のmerge pointがない。
- Mermaidがrender可能で、図のedge、Gate名、fallback、外部lane、最終Joinが各PLAN本文と一致し、文章側だけ・図側だけに存在する依存がない。
- 並行laneのwrite scopeと外部状態ownerが排他的である。
- 直列edgeごとにsource／contract上の依存、handoff、evidenceがあり、writer重複を残す例外はscope縮小、shared seam、Join-onlyを具体的に棄却している。
- candidateが単独でUS完了を主張せず、review済みcontractへ統合した状態で上位test、review、Journeyが再実行される。
- 実行PLAN単体を新しい実行主体へ渡しても、開始条件、成果、禁止範囲、handoff先を推測せず実行できる。
- PLANの分割費用に見合う並行化利益があり、同じcodeを複数laneで二度実装しない。

意味変更を反映した場合は、影響する実行PLANだけでなく、依存、owner、条件追跡が変わる進行PLANも同じreviewerへ再確認させる。
