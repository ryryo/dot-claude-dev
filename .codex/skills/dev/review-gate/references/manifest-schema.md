# Review Gate manifest

Gateレビューでは、通常は一時的なJSONを四つ使って状態遷移を検証する。探索中に`applicable`を再分類する場合だけ、再分類直前のobservation checkpointを一つ追加する。

1. main Codexが探索前に固定するReview Brief
2. 適用範囲Gateを通過したscope baseline
3. 全確認単位の探索を終えたdiscovery baseline
4. 候補分類を終えた最終manifest

これらはレビュー中だけ保持し、Story、PLAN、EVIDENCEへ保存しない。branch、SHA、content digestも入れない。

## Review Brief

Review Briefはreviewerへ渡す前にmain Codexが固定し、reviewerに書き換えさせない。

- `target`: 対象成果と確認時点の状態
- `gate_question`: 現在のGate質問
- `current_contracts`: 現在のGateが成立させる既存契約とhandoff契約
- `handoffs`: 事前に決まっている`id`、`gate`、`owner`、`contract`
- `scope_seeds`: 条件、変更surface、全体不変条件、handoffから導いたcoverage seed

各seedは`id`、`kind`、`source`、`contract`、`coverage_obligation`、`review_case_ids`を持つ。確認caseはmain CodexがReview Briefで先に固定し、reviewerは追加・削除しない。`coverage_obligation`は次のいずれかとする。

- `must-applicable`: 少なくとも一つの`applicable`候補が必要。`condition`と`invariant`に使う
- `classify-only`: 到達経路の有無を分類すればよい。`changed-surface`に使う。変更箇所というだけで適用を強制しない
- `handoff-pair`: 同じseed、handoff、経路に`applicable`と`downstream`の両方が必要。`handoff`に使う

handoff seedには`handoff_id`も付ける。すべての現在契約とhandoffにseedが必要である。

## 適用範囲Gate

`scope_candidates`には、すべてのseedを対応付ける。各候補は一つの`seed_id`を持つ。

- `applicable`: `contract`、`reachable_path`、`path_id`、`boundary`、Review Brief由来の重複しない`review_case_ids`が必要。同じ確認caseを、異なる到達経路で確認してよい
- `downstream`: Review Briefの`handoff_id`と一致するGate、owner、handoff契約が必要。handoff面を確認する`applicable`候補も参照する
- `not-applicable`: `reason`と`boundary`が必要

handoff seedには、現在Gateがhandoff面を生成する`applicable`候補と、後工程を示す`downstream`候補の両方を作る。

`scope_gate`を`passed`、`state`を`scope-fixed`にし、main Codexが固定したReview Briefと一緒に検証する。成功したmanifestはscope baselineとして保持する。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --brief /tmp/review-brief.json \
  /tmp/review-scope.json
```

scope stageには`review_units`、`reviewers`、`finding_candidates`、`discovery_gate`、`candidate_gate`を置かない。探索中に新しい候補または再分類が必要になった場合は、直前baselineを保持したままscope Gateへ戻る。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage scope \
  --brief /tmp/review-brief.json \
  --previous-scope-baseline /tmp/review-scope-v1.json \
  --observation-checkpoint /tmp/review-observation.json \
  /tmp/review-scope-v2.json
```

新候補の追加だけなら`--observation-checkpoint`は不要である。新候補には`added_during_discovery: true`と`addition_reason`を付ける。

`applicable`を再分類する場合は、main Codexが再分類前のscope、確認単位、担当、状態、証拠を`state: discovery-in-progress`のobservation checkpointとして先に固定し、上のcommandで渡す。再分類するscopeの全確認caseをcheckpointへ一度ずつ含める。`scope_tombstones`へ、`id`、`scope_candidate_id`、`origin_review_unit_id`、`origin_review_case_id`、`previous_classification`、`status`、`evidence_mode`、`evidence`、`guarantee`、`reviewer_id`を残し、checkpointにある全単位を移す。validatorは両方向を照合する。candidate stageへscope候補を直接追加・変更しない。

## 探索完了Gate

scope baselineを複製し、次を追加する。

- `review_units`: 各単位は一つの`applicable`候補と、scope Gateで固定した一つの`review_case_id`だけを参照し、同じ`contract`と`path_id`を持つ
- `reviewers`: `completed`、またはmanifest内のcompleted担当へ移譲した`reassigned`
- `discovery_gate: passed`
- `state: discovery-complete`

確認単位には`reviewer_id`を付ける。`status`は`satisfied`、`violated`、`unverified`、`evidence_mode`は`executed`、`static`、`existing`のいずれかとする。scope Gateで固定した各確認caseに確認単位がちょうど一つあり、全単位をcompleted担当が確認していなければ通らない。自由記述の空白や言い換えで同じcaseを複製しても、`review_case_id`の重複として拒否する。

discovery stageには`finding_candidates`と`candidate_gate`を置かない。

```bash
python3 .codex/skills/dev/review-gate/scripts/validate_review_manifest.py \
  --stage discovery \
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
  --brief /tmp/review-brief.json \
  --scope-baseline /tmp/review-scope.json \
  --discovery-baseline /tmp/review-discovery.json \
  /tmp/review-final.json
```

最終manifestだけは標準入力から渡してもよい。validatorの成功は構造上の欠落がないことだけを保証する。契約、到達経路、境界、再分類、証拠の内容が事実かどうかは、main Codexが一次情報で確認する。

## 最小例

Review Brief:

```json
{
  "target": "対象成果と確認時点の状態",
  "gate_question": "現在のGate質問",
  "current_contracts": ["契約A"],
  "handoffs": [],
  "scope_seeds": [
    {
      "id": "SC1",
      "kind": "condition",
      "source": "条件A",
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
