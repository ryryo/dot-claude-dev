# 検収

委任前に`git status --short`と`git branch --show-current`を記録する。既存の変更はユーザーまたは先行workerの作業として扱い、元に戻さない。

## 共通

- planの`policy_id`、work kind、difficulty、execution route、理由、owner、model/reasoningが`task-routing.json`と一致する。
- worker reportと実際のdiff・command結果・task contractが一致する。
- planning / progress、branch、remote、未許可のlockfileやgenerated fileを変更していない。
- main Codexがacceptanceに必要な検証を再実行する。

## Cursor実装

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

- difficultyが`low`または`medium`で、`cursor_required_conditions`をすべて満たす。
- 設計、shared contract、public schema、migration、中央storeを変更していない。
- diffが分離済みwrite scope内に収まり、既存変更を消していない。
- 既存pattern、参照実装、sampleのどれを使ったか確認できる。
- focused verificationがacceptanceを直接確認している。
- 範囲外判断が必要になったtaskを無理に完了扱いしていない。

## Codex subagentの補助workstream

- `allowed_work_types`のいずれかに該当し、利用する具体的な利益がplanにある。
- source diffがなく、write scopeが`none`である。
- model / reasoning、prompt、起動引数、reportが一致し、silent fallbackがない。
- 報告がevidence、conclusion、uncertainty/counterexamples、recommendationを含む。
- main Codexが主要evidenceを確認し、採用・棄却・保留を判断する。
- subagentの報告だけで設計、実装、完了判定を決めていない。

## UI / UX

- surface、user flow、既存pattern、主要state、interaction/accessibility、verificationがtask contractと一致する。
- product flow、複数surface state、重要interaction判断はmainが所有している。
- Cursor taskは固定済みcontractに従う局所UI実装に限定されている。
- subagent taskはread-onlyのUI調査、比較、audit、レビューに限定されている。
- product-level visual verificationをmainが確認し、behavior/data correctnessの検証と混同していない。

範囲外の変更はworker由来と断定できるものだけmainが修正する。ユーザーまたは別workerによる変更の可能性がある場合は戻さず、未検収として扱う。

検収後はmain Codexだけがplanのstatus、integration batch、decision logを更新できる。
