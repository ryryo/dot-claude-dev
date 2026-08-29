# Review Gate manifest

manifestは、細かな反例を総当たりする台帳ではない。現在Gateを別の根本原因から壊し得る少数の独立観点を固定し、全観点を一巡したことを確認するための一時JSONである。

レビュー中は、次のファイルだけを保持する。

1. 正本から固定した最小Review Input
2. 探索前に固定したReview Brief
3. 適用範囲Gateを通過したscope baseline
4. 探索完了Gateを通過したdiscovery baseline
5. 指摘採用Gateで使うcandidate manifest

これらはStory、PLAN、EVIDENCEへ保存しない。branch、commit SHA、worktree、sessionの識別子も入れない。IDは前後空白のない文字列とし、同じ配列内で重複させない。

このschema導入前にscope／discovery baselineを固定済みの論理レビューは、旧形式のまま増分再確認を完了できる。新しく始める`initial`レビューでは、以下の成果物分類と`coverage point`を省略できない。schema更新だけを理由に進行中レビューを全面再開しない。

## 最小Review Input

Review Inputは、依頼、Story、PLANなどの正本とBriefの間に置く小さな照合面である。caseやseedの台帳は作らない。

```json
{
  "review_id": "review-us05-gate-d",
  "condition_ids": ["US-05-01"],
  "current_contracts": ["candidate-state", "renderer-handoff"],
  "target_artifacts": [
    {
      "id": "artifact-candidate",
      "source": "candidate implementation and tests"
    },
    {
      "id": "artifact-story",
      "source": "docs/USER_STORIES.md"
    }
  ],
  "handoffs": [
    {
      "id": "handoff-journey",
      "gate": "Journey",
      "owner": "integration",
      "contract": "renderer-handoff"
    }
  ]
}
```

- `review_id`: このGateレビューの論理ID
- `condition_ids`: 対象Storyの条件ID。条件IDを持たないGateでは空配列でよい
- `current_contracts`: 現在成立させる名前付き契約。1件以上必要
- `target_artifacts`: 判定対象となる成果物。PRでは実差分の全file、PR以外では実装、文書、外部状態などを重複なく列挙する
- `handoffs`: 現在Gateから既存の後工程へ渡す境界

Briefの`review_id`、契約集合、handoff集合と意味fieldはReview Inputに完全一致させる。Briefの`kind: condition` surfaceでは`source`に条件IDを入れ、その集合を`condition_ids`と完全一致させる。

validatorはこの対応を検査するが、Review Input自体が正本へ意味上忠実かはmain Codexが確認する。

## Review Brief

main CodexがReview Input、差分、参照実装などから観点を固定し、次の形でBriefへ記録する。reviewerの指摘や改善案から逆算しない。

```json
{
  "review_id": "review-us05-gate-d",
  "review_cycle": "initial",
  "target": "US-05の現在成果",
  "gate_question": "Candidate Gate Dを次工程へ渡してよいか",
  "current_contracts": ["candidate-state", "renderer-handoff"],
  "handoffs": [
    {
      "id": "handoff-journey",
      "gate": "Journey",
      "owner": "integration",
      "contract": "renderer-handoff"
    }
  ],
  "artifact_coverage": [
    {
      "artifact_id": "artifact-candidate",
      "classification": "surface",
      "surface_ids": ["surface-adapter"]
    },
    {
      "artifact_id": "artifact-story",
      "classification": "surface",
      "surface_ids": ["surface-condition", "surface-journey-handoff"]
    }
  ],
  "catalog_check": {
    "upstream_trace": "条件と観測結果からadapter producerまで遡った",
    "downstream_trace": "変更surfaceからsession stateとhandoff consumerまで辿った",
    "independent_root_check": "state transitionとhandoff以外の独立原因がないか探索前に見直した"
  },
  "target_surfaces": [
    {
      "id": "surface-condition",
      "kind": "condition",
      "source": "US-05-01",
      "contract": "candidate-state"
    },
    {
      "id": "surface-adapter",
      "kind": "changed-surface",
      "source": "candidate adapter",
      "contract": "candidate-state"
    },
    {
      "id": "surface-journey-handoff",
      "kind": "handoff",
      "source": "Gate DからJourneyへ渡す値",
      "contract": "renderer-handoff",
      "handoff_id": "handoff-journey"
    }
  ],
  "review_dimensions": [
    {
      "id": "dimension-state-transition",
      "contract": "candidate-state",
      "surface_ids": ["surface-condition", "surface-adapter"],
      "causal_path": "入力からadapterを経て公開状態へ届く経路",
      "stop_boundary": "shared rendererへ渡す直前まで",
      "probe": {
        "kind": "counterexample",
        "description": "失敗後の再試行で旧状態が混ざる操作列"
      },
      "coverage_points": [
        {
          "id": "point-state-origin",
          "role": "origin",
          "description": "失敗後の再試行入力とcandidate-state契約"
        },
        {
          "id": "point-state-mechanism",
          "role": "mechanism",
          "description": "adapterが所有する現行stateと旧処理の退役"
        },
        {
          "id": "point-state-observation",
          "role": "observation",
          "description": "公開session stateに旧値が混ざらないこと"
        }
      ]
    },
    {
      "id": "dimension-render-handoff",
      "contract": "renderer-handoff",
      "surface_ids": ["surface-journey-handoff"],
      "causal_path": "session receiptからrenderer handoffへ届く経路",
      "stop_boundary": "実ブラウザJourneyは後続Gate",
      "probe": {
        "kind": "direct-evidence",
        "description": "handoff payloadと現在契約を照合する"
      },
      "coverage_points": [
        {
          "id": "point-handoff-origin",
          "role": "origin",
          "description": "renderer-handoff契約とsession receipt"
        },
        {
          "id": "point-handoff-mechanism",
          "role": "mechanism",
          "description": "handoff payload生成"
        },
        {
          "id": "point-handoff-observation",
          "role": "observation",
          "description": "後工程へ渡す公開payload"
        }
      ]
    }
  ]
}
```

### handoffs

後工程へ既に存在する引き渡しだけを書く。各項目は`id`、`gate`、`owner`、`contract`を持ち、`contract`は`current_contracts`に含める。宣言した各handoffには、対応する`kind: handoff` surfaceと、そのsurfaceを参照する観点を少なくとも一つ作る。

### target_surfaces

レビュー対象を構成する条件、全体不変条件、変更面、handoff境界を書く。

- `id`: surface ID
- `kind`: `condition`、`invariant`、`changed-surface`、`handoff`のいずれか
- `source`: Story、PLAN、実装面など、根拠となる一次情報
- `contract`: このsurfaceが守る現在契約
- `handoff_id`: `kind: handoff`だけで必須。`handoffs`にあるIDを使う

対象Storyの条件、変更経路が影響し得る全体不変条件、実際の変更面、既存handoffを正本と照合する。validatorはIDの対応を検査できるが、実差分のsurfaceをmain Codexが漏らさず列挙したかまでは判定できない。

### artifact_coverage

Review Inputの`target_artifacts`を一つずつ分類する。

- `surface`: 現在契約へ届く。対応する`surface_ids`を1件以上指定する
- `excluded`: 現在契約や到達経路へ入らない。`reason`を必須とし、`surface_ids`は空にする

全成果物をちょうど1回分類する。分類の目的はfileごとのcase表を作ることではなく、未確認の差分を暗黙に落とさないことである。

### catalog_check

深い探索より前に、条件からproducerへ遡る確認、変更surfaceからconsumerへ進む確認、別の根本原因が欠けていないかの確認を一度ずつ記録する。具体的な指摘や修正案はここへ書かない。

### review_dimensions

一つの観点は、一つの独立した根本原因を調べる単位である。入力値、時刻、file、browser、event順の違いだけで観点を分割しない。

- `id`: 観点ID
- `contract`: この観点が答える現在契約
- `surface_ids`: 因果経路の入口となるsurface ID。1件以上必要
- `causal_path`: 契約から生成側、状態や外部作用、利用側、観測結果までの経路
- `stop_boundary`: 現在Gateで探索を止める境界
- `probe.kind`: `counterexample`または`direct-evidence`
- `probe.description`: 観点を判定できる代表反例または直接証拠
- `coverage_points`: 因果経路を構成する入口`origin`、仕組み`mechanism`、出口`observation`

各surfaceと各current contractは、少なくとも一つの観点から参照する。異なる契約のsurfaceを同じ観点へ混ぜない。

各観点には3種類のroleを最低1件ずつ置く。同じownerと同じ開始・前進・失敗・退役経路を持つ仕組みはまとめてよい。ownerまたは退役経路が異なるstate、resource、非同期処理は別の`mechanism`にする。入力値、時刻、操作順などのcase差は`coverage point`にしない。

`review_cycle`は初回を`initial`、同じ論理レビューの再確認を`rereview`とする。

Review Briefの意味を変更するのは、`target`、`gate_question`、契約、対象surface、因果経路、停止境界、観点集合、handoffが変わる場合である。意味不変の文言修正ではBriefを書き換えず、固定済みbaselineをそのまま再利用する。Gate質問や対象成果そのものが別物になる場合は、新しい`review_id`で`initial`レビューを開始する。

## 共通manifest

scope、discovery、candidateは、次のfieldを共通で持つ。

```json
{
  "review_id": "review-us05-gate-d",
  "review_mode": "full",
  "change_impacts": [],
  "state": "scope-fixed",
  "dimension_scopes": [
    {
      "dimension_id": "dimension-state-transition",
      "classification": "applicable",
      "evidence": "現在の編集導線から公開状態まで到達する"
    },
    {
      "dimension_id": "dimension-render-handoff",
      "classification": "applicable",
      "evidence": "現在Gateがrenderer向けpayloadを生成する"
    }
  ]
}
```

- `review_id`: Briefと完全一致させる
- `review_mode`: 初回または全面探索は`full`、局所的な再確認は`incremental`
- `change_impacts`: 再確認する観点と理由。`full`では必ず空配列
- `state`: stageごとの状態
- `dimension_scopes`: Briefの全観点をちょうど1回分類する

`dimension_scopes.classification`は`applicable`または`not-applicable`とする。どちらにも直接根拠を`evidence`へ書く。`not-applicable`には`reason`も必要である。

条件、全体不変条件、handoffを含む観点は`not-applicable`にできない。`changed-surface`だけを参照する観点は、現在導線から到達しない直接根拠がある場合に限り`not-applicable`にできる。少なくとも一つの観点を`applicable`にする。

incrementalでは、直前scope baselineの`dimension_id`、`classification`、`evidence`、`reason`をそのまま使う。到達根拠を差し替えない。

## 適用範囲Gate

scope manifestは`state: scope-fixed`とする。`dimension_results`、`reviewers`、`finding_candidates`はまだ置かない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  /tmp/review-scope.json
```

成功したJSONをscope baselineとして保持する。探索中に別の根本原因を調べる必要が分かった場合は、candidateへ直接足さず、Briefの観点を更新して`full`のscope Gateからやり直す。

## 探索完了Gate

discovery manifestはscope baselineをそのまま保ち、`state: discovery-complete`、`dimension_results`、`reviewers`を加える。

```json
{
  "dimension_results": [
    {
      "dimension_id": "dimension-state-transition",
      "status": "satisfied",
      "evidence_mode": "executed",
      "result_source": "fresh",
      "probe_result": "代表反例では公開状態が分裂しなかった",
      "evidence": "対象testと実装経路を確認した",
      "guarantee": "現在のadapterからsession stateまで",
      "reviewer_id": "reviewer-main",
      "coverage_results": [
        {
          "point_id": "point-state-origin",
          "status": "satisfied",
          "evidence": "再試行入力と契約を照合した"
        },
        {
          "point_id": "point-state-mechanism",
          "status": "satisfied",
          "evidence": "現行stateの更新と旧処理の退役を確認した"
        },
        {
          "point_id": "point-state-observation",
          "status": "satisfied",
          "evidence": "公開stateに旧値が残らないことを実行確認した"
        }
      ]
    },
    {
      "dimension_id": "dimension-render-handoff",
      "status": "satisfied",
      "evidence_mode": "static",
      "result_source": "fresh",
      "probe_result": "handoff payloadが現在契約と一致した",
      "evidence": "producer、consumer、契約testを照合した",
      "guarantee": "現在Gateが所有するhandoff境界まで",
      "reviewer_id": "reviewer-main",
      "coverage_results": [
        {
          "point_id": "point-handoff-origin",
          "status": "satisfied",
          "evidence": "session receiptを確認した"
        },
        {
          "point_id": "point-handoff-mechanism",
          "status": "satisfied",
          "evidence": "payload生成を静的に確認した"
        },
        {
          "point_id": "point-handoff-observation",
          "status": "satisfied",
          "evidence": "handoff出力を契約testで確認した"
        }
      ]
    }
  ],
  "reviewers": [
    {
      "id": "reviewer-main",
      "status": "completed"
    }
  ]
}
```

各`applicable`観点に結果をちょうど1件作る。`not-applicable`観点には結果を作らない。一件目が`violated`でも、残りの観点をすべて記録するまでこのGateは通らない。

- `status`: `satisfied`、`violated`、`unverified`
- `evidence_mode`: `executed`、`static`、`existing`
- `result_source`: 初回確認は`fresh`。再確認で影響のない観点は`carried-forward`
- `probe_result`: Briefの代表確認で観測した結果
- `evidence`: 直接確認した内容
- `guarantee`: 証拠が保証する範囲
- `reviewer_id`: `completed` reviewerのID
- `coverage_results`: Briefで固定した全`coverage point`の結果。`point_id`、`status`、直接根拠`evidence`を持つ

各観点の全`coverage point`を過不足なく確認する。一つでも`violated`なら観点も`violated`、`violated`がなく`unverified`が残れば観点も`unverified`、すべて`satisfied`の場合だけ観点を`satisfied`にする。これにより、代表例が一つ通っただけで同じ観点の別owner／別退役経路まで成立扱いにすることを防ぐ。

続行できないreviewerは`status: reassigned`と`transferred_to`を持たせ、`transferred_to`は`completed` reviewerを指す。`unverified`は探索結果として残せるが、合否に必要な証拠が不足しているためcandidate GateはHOLDになる。`unverified`をfindingのroutingへ変換しない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage discovery \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  --scope-baseline /tmp/review-scope.json \
  /tmp/review-discovery.json
```

## 指摘採用Gate

candidate manifestはdiscovery baselineの`review_id`、`review_mode`、`change_impacts`、`dimension_scopes`、`dimension_results`、`reviewers`を変更せず、`state: candidate-sorted`と`finding_candidates`だけを加える。

各候補は`id`、`routing`、`dimension_ids`、`reason`を持つ。routingは次の4種だけである。

- `fix-here`: `violated`観点を参照する。現在契約を増やさずに直す範囲を`minimal_fix_boundary`へ書く
- `later-gate`: `satisfied`観点を参照し、Briefにある`handoff_id`を持つ。そのhandoff surfaceを確認する観点を少なくとも一つ参照する
- `contract-decision`: `violated`観点を参照する。`conflicting_contracts`に2件以上の現在契約を指定し、各契約の観点と`reachable_scenario`を持つ
- `not-applicable`: `satisfied`観点を参照し、現在の指摘や修正へ採用しない理由を残す

すべての`violated`観点を、`fix-here`または`contract-decision`の候補へちょうど1回まとめる。同じ観点とroutingの候補を重複させない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage candidate \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  --scope-baseline /tmp/review-scope.json \
  --discovery-baseline /tmp/review-discovery.json \
  /tmp/review-candidate.json
```

## 修正後の局所再確認

契約、surface、handoff、観点、scope分類が変わらない修正後レビューは`review_mode: incremental`にする。実際に影響を受ける観点だけを`change_impacts`で再開する。

現在Briefは`review_cycle: rereview`とする。直前Briefは書き換えずに保持する。

```json
{
  "review_mode": "incremental",
  "change_impacts": [
    {
      "id": "impact-adapter-fix",
      "cause": "target-change",
      "reason": "adapter修正がsession stateまでの経路を変えた",
      "surface_ids": ["surface-adapter"],
      "dimension_ids": ["dimension-state-transition"]
    }
  ]
}
```

`cause`は次の2種である。

- `target-change`: 実装や成果の変更がsurfaceへ届く。`surface_ids`を1件以上、実際に影響する観点を`dimension_ids`へ書く。同じsurfaceを参照していても影響しない観点は、`unaffected_dimensions`へ`dimension_id`と`unaffected_reason`を書いて再開しない
- `review-gap`: 前回の観点内に探索不足が見つかった。再開する既存観点を`dimension_ids`へ書く。新しい観点が必要なら`full`へ戻る

同じsurfaceまたは影響観点を複数のimpactへ重複させない。一つの観点を、別impactで影響ありと非影響、または`target-change`と`review-gap`の両方に分類しない。複数の変更理由が同じ観点へ届く場合は一つのimpactへまとめる。

文言、証拠記録、validator、schemaだけの変更ではレビューを再開せず、固定済みのBriefとbaselineをそのまま保持する。その変更を表す`change_impacts`は作らない。

影響観点の`dimension_results`は`result_source: fresh`で作り直す。影響のない観点は、直前discoveryのstatus、証拠、保証範囲、担当を変えずに`result_source: carried-forward`と`carry_forward_reason`を加える。

incrementalでは全stageに、同じ`review_id`の直前Briefと直前discovery baselineを渡す。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage discovery \
  --review-input /tmp/review-input-current.json \
  --brief /tmp/review-brief-current.json \
  --scope-baseline /tmp/review-scope-current.json \
  --previous-brief /tmp/review-brief-previous.json \
  --previous-discovery-baseline /tmp/review-discovery-previous.json \
  /tmp/review-discovery-current.json
```

incremental candidateで、`result_source: fresh`の観点から新しいfindingを採用する場合は、修正前にも存在した見逃しか、修正が生んだ回帰かを区別する。

- `origin: prior-review-miss`: 該当観点が`cause: review-gap`で再開されている
- `origin: change-regression`: 該当観点が`cause: target-change`で再開されている
- `origin_evidence`: 修正前の成果との比較根拠

初回`full`のfindingには`origin`と`origin_evidence`を付けない。

`carried-forward`の`violated`観点にある未修正findingは新規findingではないため、`origin`と`origin_evidence`を付けず、そのまま分類する。

契約、target、gate question、target surface、handoff、因果経路、停止境界、観点集合、scope分類のいずれかが変わる場合は`full`へ戻る。同じ論理レビューの全面再探索では`review_cycle: rereview`、非空の`full_review_reason`をBriefへ書き、全stageで直前Briefと直前discovery baselineを渡す。validatorはcatalogまたはscopeが実際に変わっていることも確認する。別のGate質問や別の対象成果へ移る場合は、新しい`review_id`で`initial`の`full`を開始する。

## validatorが保証しないこと

validatorが保証するのは、宣言済みの観点が各Gateで欠けず、局所再確認とcandidate分類が許可された状態遷移だけを行うことである。次はmain Codexが一次情報で判断する。

- Briefが正本の条件、契約、変更surface、handoffを意味上すべて含むか
- Review Inputの`target_artifacts`が実差分または実際の判定対象を過不足なく含むか
- 観点が本当に異なる根本原因であり、細かなcaseの分割ではないか
- `coverage point`が因果経路の実在する構成要素を覆い、異なるowner／退役経路を誤って一つへまとめていないか
- 因果経路、停止境界、証拠が事実か
- 言い換えではなく対象成果やGate質問の意味が変わっていないか
- `minimal_fix_boundary`が過剰実装を避ける実際の最小範囲か

validator成功だけをGOの根拠にしない。

廃止した`scope_seeds`、`review_case_migrations`、`scope_candidates`、`review_units`、`scope_tombstones`などのcase／migration fieldは追加しない。validatorもこれらを拒否する。
