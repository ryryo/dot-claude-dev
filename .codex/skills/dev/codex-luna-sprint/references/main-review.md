# Main review contract

各段階で必要な節だけ読む。既存レビューの再利用は[SKILL.md](../SKILL.md)の「適用と正本」に従い、正本、対象成果、判定質問、証拠、役割分離の対応を確認する。再利用できない不足や変更だけをレビューする。

## 1. Product frame review

Product frameを実装案から独立して検査する。
このreviewのownerと最終採否判断者はmainである。補助調査のsubagentには正本探索と事実収集を依頼する。適用先やdevelop-user-storyが要求する独立reviewerは契約の成立を検査し、mainが指摘の採否と修正を判断する。StoryやUXの設計責任をworkerへ移さない。

| 観点 | 必須確認 |
| --- | --- |
| Source precedence | 最新要求、foundational workflow、user story、UX、計画、Lab/fixtureの関係と矛盾が解決済み |
| Normal journey | 利用者、開始状態、上流入力、判断、完了状態が一続き |
| Provenance | 上流で確定した値を再入力・複製・黙った既定値で置換しない |
| Path class | normal、optional、fallback、technical substrate、Lab-onlyを混同しない |
| Human decision | import、生成成功、selection、approvalが必要な箇所で分離される |
| Recovery | failure、cancel、reload、staleで既存成果を失わず復帰できる |

normalと、契約に存在するexception、recoveryの代表scenarioで反証する。表の観点も適用するものだけを確認し、存在しない承認・永続状態・復旧機能を要求しない。未解決decision、source矛盾、通常導線の欠落があれば`draft`を維持する。

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
- worker commandをmainが再実行し、異なるnegative caseを少なくとも1件確認する。以後は新しい変更・失敗・未確認の根拠がある範囲だけ検証する。
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

task-local test成功だけで合格にしない。対象契約に存在する次の観点だけを、通常入口から確認する。UIは実画面、メディアや生成物は実成果物、それ以外は公開interfaceで確認する。適用外の理由は短く示し、必要な実検証をmockや静的文字列で代用しない。

- 継承する上流成果物がある場合、通常CTAがその利用から始まり、不要な再uploadを要求しない。手元素材の取り込みが利用者の目的ならuploadが通常CTAでよい。
- 継承値、override、例外操作がproduct frameどおりに区別される。
- loading、empty、blocked、running、failed、stale、completedから復帰できる。
- 永続化が契約にある場合、対象のselection、artifact、job、review、Gateがreload後に復元される。
- UIでは対象のkeyboard、focus、読み上げ、狭幅を確認し、複数mediaを扱う導線では再生制御を確認する。

```text
Overall decision: accepted | rework | plan-reopened
Normal journey evidence:
Exception / recovery evidence:
Regression evidence:
Residual risk:
```
