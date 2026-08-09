# Main review contract

## 1. Product frame review

Product frameを実装案から独立して検査する。
このreviewのownerと最終判断者は常にmainである。subagentへ委譲できるのは正本探索と事実収集だけで、story、UX、通常導線、画面構成の判断は委譲しない。

| 観点 | 必須確認 |
| --- | --- |
| Source precedence | 最新要求、foundational workflow、user story、UX、計画、Lab/fixtureの関係と矛盾が解決済み |
| Normal journey | 利用者、開始状態、上流入力、判断、完了状態が一続き |
| Provenance | 上流で確定した値を再入力・複製・黙った既定値で置換しない |
| Path class | normal、optional、fallback、technical substrate、Lab-onlyを混同しない |
| Human decision | import、生成成功、selection、approvalが必要な箇所で分離される |
| Recovery | failure、cancel、reload、staleで既存成果を失わず復帰できる |

normal、exception、recoveryの3 scenarioで反証する。未解決decision、source矛盾、通常導線の欠落があれば`draft`を維持する。

## 2. Implementation plan review

- 各schema field、API mutation、state transition、主要UIをstory/invariantへtraceする。
- 実装都合だけのshadow state、再入力form、Lab/fixture制約、暗黙default、自動approvalを探す。
- technical substrateを完成UXとして扱っていないか確認する。
- migration、ownership、security、failure、browser acceptanceが通常journeyを保つか確認する。

Product frameと矛盾したら局所修正で隠さず、全体判定を`plan-reopened`にする。

## 3. Task diff review

- `git status --short`、`git diff --name-only`、allowed pathの実diffを確認する。
- report、排他的scope、既存変更の保持を照合する。
- hardcode、fixture専用分岐、不要なfallback、過剰抽象化、未解決判断の混入を探す。
- worker commandをmainが再実行し、異なるnegative caseを少なくとも1件確認する。
- user-facing UI、文言、UX判断、API/domain/state contractがdiffへ混入した場合は、たとえtestが通っても原則`rejected`とする。

```text
Task ID:
Decision: accepted | corrected-by-main | rejected | blocked
Story / UX findings:
Diff integrity:
Independent verification:
Main corrections:
Residual risk:
```

## 4. Whole-user-journey review

task-local test成功だけで合格にしない。実dataと実画面で次を確認する。

- 通常CTAが上流成果物から始まり、fallbackやuploadより強い。
- 継承値、override、例外操作がproduct frameどおりに区別される。
- loading、empty、blocked、running、failed、stale、completedから復帰できる。
- reload後もselection、artifact、job、review、Gateが復元される。
- keyboard、focus、読み上げ、狭幅、複数media再生制御が成立する。

```text
Overall decision: accepted | rework | plan-reopened
Normal journey evidence:
Exception / recovery evidence:
Regression evidence:
Residual risk:
```
