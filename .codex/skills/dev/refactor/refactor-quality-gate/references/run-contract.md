# Run Contract

`refactor-quality-gate`の一時manifestとstage遷移の正本である。manifestは`/tmp/refactor-quality-<project>/manifest.json`へ置き、永続成果物へcase台帳や実行識別子を転記しない。

## Stage

`stage`は次のいずれかとする。

1. `scoped`: scope、contract、artifact、独立観点を固定した。
2. `discovered`: 全適用観点を一巡し、finding候補を分類した。
3. `frozen`: P1／P2をgoalへ変換し、依存とownerを凍結した。
4. `implemented`: 全採用goalと実装batchの安全確認が完了した。
5. `reviewed`: 初回reviewまたは差分再reviewを記録した。
6. `complete`: 全完了条件を満たし、最新reviewが`GO`である。
7. `hold`: 自動続行しない停止状態である。

`hold`では`hold_reason`を必須とする。P0、契約判断、scope変更、回復後の再見逃し、安全に解消できない回帰はHOLD理由になる。

## Manifest Schema

```json
{
  "version": 1,
  "run_id": "editor-refactor-quality",
  "stage": "scoped",
  "hold_reason": "",
  "scope": {
    "target": "対象と固定境界",
    "current_contracts": ["selection結果を変えない"],
    "forbidden_changes": ["製品挙動や外部状態の禁止変更"],
    "verification": ["focused test", "full test", "typecheck"],
    "artifacts": [
      {
        "id": "surface-editor",
        "source": "src/editor",
        "classification": "surface",
        "dimension_ids": ["state-owner"]
      },
      {
        "id": "excluded-admin",
        "source": "src/admin",
        "classification": "excluded",
        "reason": "固定scope外",
        "dimension_ids": []
      }
    ]
  },
  "dimensions": [
    {
      "id": "state-owner",
      "category": "architecture",
      "question": "canonical stateのwriterは一つか",
      "contract": "selection結果を変えない",
      "causal_path": "input -> command -> store -> selector -> UI",
      "stop_boundary": "Editor providerの公開consumerまで",
      "probe": {
        "kind": "counterexample",
        "description": "stale commandが現在selectionを上書きしない"
      },
      "coverage_points": [
        {"id": "cp-origin", "role": "origin", "description": "入力event"},
        {"id": "cp-mechanism", "role": "mechanism", "description": "store update"},
        {"id": "cp-observation", "role": "observation", "description": "選択表示"}
      ],
      "status": "pending"
    }
  ],
  "findings": [],
  "goals": [],
  "implementation_batches": [],
  "review_cycles": [],
  "correction_batches": []
}
```

## Fields

### Scope artifact

- `classification`: `surface`または`excluded`
- `surface`: 一つ以上の有効な`dimension_ids`を持つ。
- `excluded`: 理由を持ち、`dimension_ids`は空にする。

`current_contracts`、`forbidden_changes`、`verification`、`artifacts`、`dimensions`は空にしない。各dimensionは少なくとも一つのsurface artifactから参照され、その`contract`は`current_contracts`の一つと一致しなければならない。各current contractも、少なくとも一つのdimensionから参照する。

### Dimension

- `category`: `architecture`、`frontend`、`test_portfolio`、`performance`、`contract`、`integration`
- `probe.kind`: `counterexample`または`direct_evidence`
- `coverage_points.role`: `origin`、`mechanism`、`observation`
- `status`: `pending`、`satisfied`、`violated`、`unconfirmed`

`discovered`以降で全dimensionを一巡する。`frozen`以降では`pending`と`unconfirmed`を残さない。

### Finding

```json
{
  "id": "F-01",
  "dimension_ids": ["state-owner"],
  "severity": "P2",
  "root_cause": "selectionのwriterが重複する",
  "evidence": "到達経路と反例",
  "disposition": "goal",
  "reason": "挙動維持の最小修正で解消できる"
}
```

- `disposition`: `stop`、`goal`、`defer`、`non_applicable`
- P0は`stop`とし、`frozen`以降へ進めない。
- P1／P2は`goal`とし、ちょうど一つのgoalから参照する。
- P3は`defer`または`non_applicable`とする。

### Goal

```json
{
  "id": "G-01",
  "kind": "architecture",
  "finding_ids": ["F-01"],
  "owner": "main",
  "write_scope": ["src/editor/state"],
  "forbidden_scope": ["public API", "storage schema"],
  "depends_on": [],
  "behavior_oracles": ["selection behavior test"],
  "retained_oracles": [],
  "performance_sensitive": false,
  "measurement_plan": "",
  "performance_acceptance": "",
  "performance_result": "not_applicable",
  "rejection_reason": "",
  "restoration_oracles": [],
  "status": "planned"
}
```

- `kind`: `architecture`、`frontend`、`test_portfolio`、`mixed`
- `owner`: `main`または`worker`
- `status`: `planned`、`in_progress`、`verified`、`rejected`
- dependencyは循環させない。
- `test_portfolio` categoryのdimensionへ結び付くfindingを含むgoalは、kindが`test_portfolio`または`mixed`のどちらでも一つ以上の`retained_oracles`を持つ。テスト削除・統合を含むfindingは必ずtest portfolio dimensionへ結び付ける。
- `performance_result`: `not_applicable`、`pending`、`pass`、`fail`
- `performance_sensitive: true`なら、実装前にmetric、workload、sample方法、baselineを含む`measurement_plan`と、baseline変動幅を考慮した`performance_acceptance`を凍結し、`performance_result`を`pending`にする。`implemented`以降は`pass`を必須とする。
- `performance_sensitive: false`なら計測fieldを空にし、`performance_result`を`not_applicable`にする。
- `rejected`は、review後のregressionを安全にforward-fixできずgoal変更を取り除いたHOLD状態だけに使う。非空の`rejection_reason`と一つ以上の`restoration_oracles`を必須とし、元の挙動へ戻ったこととregression解消を確認する。他statusでは両fieldを空にする。

### Implementation batch

```json
{"id": "B-01", "goal_ids": ["G-01"], "status": "verified"}
```

`status`は`planned`、`in_progress`、`verified`。配列順を実装順とする。各goalはちょうど一つのbatchへ含め、`depends_on`の全goalを必ず以前のverified batchで完了させる。同じbatch内の暗黙順序は認めない。`implemented`以降では各goalとbatchをverifiedにする。回帰のためrefactor変更を不採用にしてgoalが`rejected`になった場合は、元の挙動を復元して現在runを`hold`にする。

### Review cycle

```json
{
  "id": "R-01",
  "kind": "initial",
  "reopened_dimension_ids": ["state-owner"],
  "carried_dimension_ids": [],
  "basis_correction_batch_ids": [],
  "recovery_of_review_id": "",
  "candidates": [
    {
      "id": "RC-01",
      "dimension_ids": ["state-owner"],
      "classification": "fix_here",
      "origin": "initial",
      "root_cause": "cleanup順が逆転する",
      "status": "open"
    }
  ],
  "decision": "NO_GO"
}
```

- `kind`: `initial`、`incremental`、`recovery`
- `classification`: `fix_here`、`later_gate`、`contract_decision`、`non_applicable`
- candidate `origin`: `initial`、`regression`、`preexisting_miss`
- candidate `status`: `open`、`resolved`、`carried`
- `decision`: `pending`、`GO`、`NO_GO`、`HOLD`
- 最初かつ唯一の`initial`は、全dimensionを`reopened`へ含め、`carried`、`basis_correction_batch_ids`、`recovery_of_review_id`を空にする。candidate originは`initial`だけを使う。
- `incremental`は一つ以上の完了済み`basis_correction_batch_ids`を持ち、その全`affected_dimension_ids`を`reopened`へ含める。`recovery_of_review_id`は空にする。新しいcandidateは`regression`または`preexisting_miss`にする。
- `recovery`は`basis_correction_batch_ids`を空にし、最初の`preexisting_miss`を検出した先行incremental reviewを`recovery_of_review_id`へ記す。candidate originは`preexisting_miss`だけを使う。最初のmissを含むcorrectionより前に必ずこのcycleを完了する。
- `incremental`と`recovery`は、`reopened`と`carried`が重複せず、合わせて全dimensionを覆う。`reopened`は空にしない。
- candidateの`dimension_ids`は、そのcycleの`reopened`に含まれる観点だけを参照する。
- `carried`は以前の直接根拠と状態の再利用であり、`satisfied`を意味しない。既知の違反や未解決candidateをcarryしても完了条件は満たさない。
- `recovery`は一runにつき一回までとする。recovery後に別の`preexisting_miss`が現れたら最新decisionとstageを`HOLD`／`hold`にする。
- `reviewed`と`complete`では最新cycleの`decision`を`pending`にしない。

### Correction batch

```json
{
  "id": "C-01",
  "source_review_ids": ["R-01"],
  "candidate_ids": ["RC-01"],
  "affected_dimension_ids": ["state-owner"],
  "status": "verified"
}
```

`status`は`planned`、`verified`、`reverted`。`verified`はfocused oracleを通って差分再reviewへ渡せる状態、`reverted`は回帰を生んだ変更を取り除き、元の挙動を再確認した状態である。

- `source_review_ids`に含めたreviewの全`fix_here`を一batchへまとめる。recovery後のbatchは、検出元incrementalとrecoveryの両reviewをsourceにする。
- candidateはそのsource reviewに属する`fix_here`だけを参照し、同じcandidateを複数batchへ重複登録しない。同じsource reviewを複数correction batchへ分割しない。
- `affected_dimension_ids`はcandidate自身のdimensionに加え、実diffの因果経路が届く全dimensionを含める。
- incremental reviewはbasis correctionの全affected dimensionをreopenする。`reverted` batchも、revert差分の影響reviewを省略しない。
- `verified`または`reverted`になった全correctionは、source reviewより後のincremental reviewからbasisとして参照されなければならない。未reviewのcompleted correctionを残したまま最新decisionを`GO`、stageを`complete`、またはreview済み`hold`にしない。
- `complete`では全`fix_here`がresolvedで、`verified` correction batchへ含まれる。`reverted` batchのcandidateは未解決のままとし、別のverified correctionがなければ完了しない。

## Stage Invariants

- `scoped`: schema、参照整合性、dimension coverageを満たす。
- `discovered`: 全dimensionの監査結果が記録される。`unconfirmed`があればHOLDへ移る。
- `frozen`: P0がなく、P1／P2がgoalへ一対一で割り当てられ、全dimensionが`satisfied`または`violated`である。
- `implemented`: 全goalと実装batchがverifiedであり、performance-sensitive goalの結果が`pass`である。`rejected` goalを残したまま通過しない。採用goalが0件なら両collectionを空のまま通過できる。
- `reviewed`: 最初のcycleが全観点の`initial`であり、後続cycleが正しい差分partitionを持ち、最新decisionが確定している。
- `complete`: `implemented`の条件に加え、最新reviewが`GO`、全`fix_here`が解消済み、未解決`contract_decision`がない。
- `hold`: `hold_reason`がある。review historyが存在する場合は、全dimensionの監査完了、P0なし、初回review前のbatch、review／correctionの参照・順序整合性、最新reviewの`HOLD`を保つ。goalは`verified`または、復元証拠を持つ`rejected`にできる。recovery後の再見逃しは最新reviewを`HOLD`にし、別のHOLD理由があっても`regression` candidateを未解決で残さない。

## 禁止field

manifestのどの階層にも`branch`、`branch_name`、`commit`、`commit_sha`、`worktree`、`session`、`session_id`を保存しない。実行環境は一時情報であり、品質Gateのcontractではない。

## Validation

```bash
python3 scripts/validate_refactor_manifest.py /tmp/refactor-quality-<project>/manifest.json
```

成功時は`PASS: <run_id> (<stage>)`、失敗時は`ERROR: <path>: <message>`を返す。validatorのgreenだけで監査やreviewを代用しない。manifestは、全観点を一巡したことと差分再reviewのpartitionを機械的に検査する補助oracleである。
