# 検収

委任前に`git status --short`と`git branch --show-current`を記録しておく。既存の変更はユーザーまたは先行workerの作業として扱い、元に戻さない。

worker完了後、次のコマンドで確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

- 変更がwrite scope内に収まっており、既存の変更を消していないこと。
- planning / progress、branch、remote、lockfileなど、禁止対象を変更していないこと。
- worker report、実際のdiff、planのtask contractが一致していること。
- planのrouting policy ID、Routing class、理由、owner/model/reasoningが`task-routing.json`と一致していること。
- Codex subagentで選定したmodel / reasoning、起動引数、reportが一致し、silent fallbackがないこと。
- UI taskはsurface、user flow、既存pattern、主要state、interaction/accessibility、verificationがtask contractと一致していること。
- UI taskはplanが要求するproduct-level visual verificationを、main Codexが確認していること。visual確認とbehavior/data correctnessの検証は互いに代用しない。
- main Codexが必要な検証を再実行し、goalと受け入れ条件を満たしていること。

範囲外の変更は、worker由来だと断定できるものだけmain Codexが修正する。ユーザーまたは別workerによる変更の可能性がある場合は戻さず、その成果を未検収として扱う。

検収後は、main Codexだけがplanのstatus、integration batchの結果、decision logを更新できる。検証が済むまでは`done`へ進めない。
