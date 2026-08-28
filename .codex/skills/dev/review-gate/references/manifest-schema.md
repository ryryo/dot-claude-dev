# Review Gate manifest

Gateレビューでは、通常は次の一時JSONを使って状態遷移を検証する。探索中に`applicable`を再分類する場合だけ、再分類直前のobservation checkpointを追加する。

1. 正本から固定するReview Input
2. Review Inputから固定するReview Brief
3. 適用範囲Gateを通過したscope baseline
4. 全確認単位の探索を終えたdiscovery baseline
5. 候補分類を終えた最終manifest

これらはレビュー中だけ保持し、Story、PLAN、EVIDENCEへ保存しない。`review_id`はレビュー内の論理IDである。branch、commit SHA、worktreeやsessionの識別子を入れない。content digestの例外は、Review Inputの`previous_brief_digest`とvalidator成功出力だけである。すべてのJSONで、IDと集合に入る文字列の前後空白を許さない。

## Review Input

Review InputはReview Briefより先に、依頼本文、Story、PLANなどの正本から作る。Briefへ書いた内容から逆算しない。

- `review_id`: 非空の文字列
- `condition_ids`: 対象条件IDの重複のない配列。条件IDを持たないGateでは空でよい
- `current_contracts`: 現在成立させる名前付き契約の重複のない非空配列
- `handoffs`: 事前に決まっているhandoffの全件
- `scope_seeds`: 条件、変更surface、全体不変条件、handoffから導いたseedと確認caseの全件
- `previous_brief_digest`: revision 1は`null`。revision 2以降は実際の直前Briefのcanonical JSON SHA-256

handoffは`id`、`gate`、`owner`、`contract`を持つ。seedは`id`、`kind`、`source`、`contract`、`coverage_obligation`、`review_case_ids`を持つ。condition seedには`condition_id`、handoff seedには`handoff_id`も付ける。すべてのIDと集合値は、前後に空白のない非空文字列とする。

Review Inputの各条件IDをcondition seedがちょうど1回覆い、確認case IDは全seedを通じて一意にする。すべての現在契約とhandoffにseedが必要である。coverage obligationは次を使う。

- `must-applicable`: conditionとinvariantに使う
- `classify-only`: changed-surfaceに使う
- `handoff-pair`: handoffに使う

改善案、将来用途、一般的なbest practiceは契約、handoff、seed、caseへ追加しない。main CodexはReview Inputを固定する前に、正本の条件、契約、handoff、seed、caseと全件照合する。validatorはこの意味上の忠実性を判定できない。Review Inputは全stageで`--review-input`に渡す。

## Review Brief

Review Briefはreviewerへ渡す前にmain Codexが固定し、reviewerに書き換えさせない。

- `review_id`: Review Inputと同じ論理ID
- `revision`: 1から始まる正の整数
- `target`: 対象成果と確認時点の状態
- `gate_question`: 現在のGate質問
- `current_contracts`: Review Inputと集合が完全に一致する契約
- `handoffs`: Review InputとID集合と各意味fieldが完全に一致するhandoff
- `scope_seeds`: Review InputとID集合、case集合、各意味fieldが完全に一致するseed
- `review_case_migrations`: revisionの間で確認caseを対応付ける配列

ここでいう意味fieldは、handoffの`gate`、`owner`、`contract`と、seedの`kind`、`source`、`contract`、`coverage_obligation`、`condition_id`、`handoff_id`、`review_case_ids`を指す。Brief側で追加、削除、改名、owner変更、契約変更をしない。reviewerにも変更させない。`coverage_obligation`の詳細は次のとおり。

- `must-applicable`: 少なくとも一つの`applicable`候補が必要。`condition`と`invariant`に使う
- `classify-only`: 到達経路の有無を分類すればよい。`changed-surface`に使う。変更箇所というだけで適用を強制しない
- `handoff-pair`: 同じseed、handoff、経路に`applicable`と`downstream`の両方が必要。`handoff`に使う

revision 1ではReview Inputの`previous_brief_digest`を`null`、Briefの`review_case_migrations`を必ず`[]`とし、`--previous-brief`は渡さない。

revision 2以降では、同じ`review_id`を持ち、`revision`がちょうど1小さい実際の直前Briefを全stageで`--previous-brief`に渡す。Review Inputの`previous_brief_digest`は、そのBriefに対してvalidatorが成功時に出力したcanonical JSON SHA-256と一致させる。形式は`sha256:<64桁の小文字16進数>`とする。成功出力のdigestは次のrevisionでだけ使う。

各migration rowは`previous_review_case_ids`、`current_review_case_ids`、`reason`を使う。各ID配列内に重複を持たせず、両方を同時に空にしない。直前Briefの全caseと現Briefの全caseは、それぞれ全rowを通じてちょうど1回現れる必要がある。

- 同じIDと同じownerを維持する場合だけ、`reason`を省略できる
- 改名、分割、統合は、旧新IDの対応と理由を残す
- 追加は`previous_review_case_ids: []`、廃止は`current_review_case_ids: []`とし、理由を残す
- 同じcase IDでもownerの意味fieldが一つでも変わる場合は、owner変更の理由を残す。ownerはseedの`id`、`kind`、`source`、`contract`、`coverage_obligation`、`condition_id`、`handoff_id`と、handoff seedに紐づくhandoffの`gate`、`owner`、`contract`で判定する

このmigrationは、旧caseが黙って消えることと、関係ないcaseが理由なく増えることの両方を防ぐ。

migrationのvalidator errorで修正するのは、保持した直前Briefではなく、現Briefの`review_case_migrations`である。

## 適用範囲Gate

scope、discovery、candidateの全manifest、およびobservation checkpointには、Briefと完全に一致する`review_id`と`brief_revision`を持たせる。

`scope_candidates`には、すべてのseedを対応付ける。各候補は一つの`seed_id`を持つ。

- `applicable`: `contract`、`reachable_path`、`path_id`、`boundary`、Review Brief由来の`review_case_ids`が必要
- `downstream`: Review Briefの`handoff_id`と一致するGate、owner、handoff契約が必要。handoff面を確認する`applicable`候補も参照する
- `not-applicable`: `reason`と`boundary`が必要

handoff seedには、現在Gateがhandoff面を生成する`applicable`候補と、後工程を示す`downstream`候補の両方を作る。`applicable`候補を1件以上持つseedでは、そのseedの各確認case IDを`applicable`候補全体でちょうど1回使う。`not-applicable`だけのchanged-surface seedではcaseを候補へ割り当てない。異なる到達経路を確認する場合は、Review InputとBrief revisionを更新し、経路ごとに別のcase IDを追加する。`path_id`も前後空白のないIDとする。

`scope_gate`を`passed`、`state`を`scope-fixed`にし、main Codexが固定したReview InputとBriefと一緒に検証する。main Codexはcommand実行前に、Review Inputが正本の全件と意味上一致することを自身で確認する。validator成功はこの正本照合の代わりにならない。成功したmanifestはscope baselineとして保持する。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  /tmp/review-scope.json
```

Brief revision 2以降では、digestと一致する実際の直前Briefも渡す。これはdiscoveryとcandidateでも必須である。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief-v2.json \
  --previous-brief /tmp/review-brief-v1.json \
  /tmp/review-scope-r2.json
```

scope stageには`review_units`、`reviewers`、`finding_candidates`、`discovery_gate`、`candidate_gate`を置かない。探索中に新しい候補または再分類が必要になった場合は、直前baselineを保持したままscope Gateへ戻る。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  --previous-scope-baseline /tmp/review-scope-v1.json \
  --observation-checkpoint /tmp/review-observation.json \
  /tmp/review-scope-v2.json
```

この`--previous-scope-baseline`は、Review InputとBriefが同じrevisionのままで行うscope再確定に限る。Brief revisionを更新した場合は、`--previous-brief`でdigestとcase migrationを検証し、scope baselineを新規に作る。前revisionのscope baselineは渡さない。新経路に新caseが必要な場合も、同revisionの候補追加ではなくBrief revisionを更新する。

Review Inputのseedとcaseを変えず、既存の`applicable`を再分類しない新候補の追加だけなら、`--observation-checkpoint`は不要である。新候補には`added_during_discovery: true`と`addition_reason`を付ける。

`applicable`を再分類する場合は、main Codexが再分類前のscope、確認単位、担当、状態、証拠を`state: discovery-in-progress`のobservation checkpointとして先に固定し、上のcommandで渡す。再分類するscopeの全確認caseをcheckpointへ一度ずつ含める。`scope_tombstones`へ、`id`、`scope_candidate_id`、`origin_review_unit_id`、`origin_review_case_id`、`previous_classification`、`status`、`evidence_mode`、`evidence`、`guarantee`、`reviewer_id`を残し、checkpointにある全単位を移す。validatorは両方向を照合する。candidate stageへscope候補を直接追加・変更しない。

## 探索完了Gate

scope baselineを複製し、次を追加する。

- `review_units`: 各単位は一つの`applicable`候補と、scope Gateで固定した一つの`review_case_id`だけを参照し、同じ`contract`と`path_id`を持つ
- `reviewers`: `completed`、またはmanifest内のcompleted担当へ移譲した`reassigned`
- `discovery_gate: passed`
- `state: discovery-complete`

確認単位には`reviewer_id`を付ける。`status`は`satisfied`、`violated`、`unverified`、`evidence_mode`は`executed`、`static`、`existing`のいずれかとする。scope Gateで固定した各確認caseに、`review_units`全体でちょうど1件の確認単位があり、全単位をcompleted担当が確認していなければ通らない。自由記述の空白や言い換えで同じcaseを複製しても、`review_case_id`の重複として拒否する。

discovery stageには`finding_candidates`と`candidate_gate`を置かない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage discovery \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  --scope-baseline /tmp/review-scope.json \
  /tmp/review-discovery.json
```

成功したmanifestはdiscovery baselineとして保持する。

## 指摘採用Gate

discovery baselineを複製して、候補の振り分けだけを追加する。

- `finding_candidates`: 候補がなければ空配列
- `candidate_gate: passed`
- `state: candidate-sorted`

候補の`routing`は次を使う。

- `fix-here`: `validity: valid`かつ`gate_effect: blocks`。`violated`の確認単位を参照する
- `later-gate`: `validity: valid`かつ`gate_effect: does-not-block`。事前に固定したdownstream候補とhandoff面の確認単位を参照する
- `contract-decision`: `validity: valid`かつ`gate_effect: blocks`。同じ`path_id`上の確認単位と、異なる既存契約を2件以上参照する
- `not-applicable`: `validity: invalid`かつ`gate_effect: does-not-block`

scope baselineとdiscovery baselineから、scope候補、tombstone、確認単位、状態、証拠、担当を追加・削除・変更しない。`violated`と`unverified`の確認単位は一つの`fix-here`または`contract-decision`へ統合する。同じ後工程候補、scope-outした違反、同じ確認単位と振り分けを重複登録しない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage candidate \
  --review-input /tmp/review-input.json \
  --brief /tmp/review-brief.json \
  --scope-baseline /tmp/review-scope.json \
  --discovery-baseline /tmp/review-discovery.json \
  /tmp/review-final.json
```

最終manifestだけは標準入力から渡してもよい。Brief revision 2以降では、discoveryとcandidateにもdigestと一致する`--previous-brief /tmp/review-brief-v1.json`を追加する。validatorの成功は、JSONの構造、Review InputとBriefの一致、caseの一意性、revisionとdigest、baseline間の不変性だけを保証する。Review Inputが正本の全件を正しい意味で表すかは保証しない。main Codexが正本照合Gateで確認する。この確認とvalidator成功の両方がなければ完全性を主張しない。

## 最小例

Review Input:

```json
{
  "review_id": "review-example",
  "condition_ids": ["US-01-01"],
  "current_contracts": ["契約A"],
  "handoffs": [],
  "scope_seeds": [
    {
      "id": "SC1",
      "kind": "condition",
      "condition_id": "US-01-01",
      "source": "US-01-01",
      "contract": "契約A",
      "coverage_obligation": "must-applicable",
      "review_case_ids": ["C1-normal"]
    }
  ],
  "previous_brief_digest": null
}
```

Review Brief:

```json
{
  "review_id": "review-example",
  "revision": 1,
  "target": "対象成果と確認時点の状態",
  "gate_question": "現在のGate質問",
  "current_contracts": ["契約A"],
  "handoffs": [],
  "review_case_migrations": [],
  "scope_seeds": [
    {
      "id": "SC1",
      "kind": "condition",
      "condition_id": "US-01-01",
      "source": "US-01-01",
      "contract": "契約A",
      "coverage_obligation": "must-applicable",
      "review_case_ids": ["C1-normal"]
    }
  ]
}
```

最終manifest:

```json
{
  "review_id": "review-example",
  "brief_revision": 1,
  "target": "対象成果と確認時点の状態",
  "gate_question": "現在のGate質問",
  "current_contracts": ["契約A"],
  "scope_gate": "passed",
  "discovery_gate": "passed",
  "candidate_gate": "passed",
  "state": "candidate-sorted",
  "scope_candidates": [
    {
      "id": "S1",
      "seed_id": "SC1",
      "classification": "applicable",
      "contract": "契約A",
      "reachable_path": "入力から観測結果までの経路",
      "path_id": "P1",
      "boundary": "現在の利用側まで",
      "review_case_ids": ["C1-normal"]
    }
  ],
  "review_units": [
    {
      "id": "R1",
      "scope_candidate_ids": ["S1"],
      "contract": "契約A",
      "reachable_path": "入力から観測結果までの経路",
      "path_id": "P1",
      "review_case_id": "C1-normal",
      "boundary": "現在の利用側まで",
      "status": "satisfied",
      "evidence_mode": "static",
      "evidence": "確認した一次情報",
      "guarantee": "この証拠が保証する範囲",
      "reviewer_id": "reviewer-1"
    }
  ],
  "reviewers": [{"id": "reviewer-1", "status": "completed"}],
  "scope_tombstones": [],
  "finding_candidates": []
}
```
