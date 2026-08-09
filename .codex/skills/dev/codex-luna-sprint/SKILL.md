---
name: codex-luna-sprint
description: "main Codexがrepositoryと利用者の制作体験を先に調査し、user story・UX invariant・通常導線・画面構成を自ら反証・確定した後、implementation planと全taskをmain担当で作る。Lunaには確定済みのpure logic、parser/serializer、fixture、table test、機械的adapter等だけを任意委譲し、ユーザーストーリー・UX・文言・状態遷移を考えさせない。Story-first planning、排他的write scope、疑義前提review、Whole-user-journey検収を伴う実装Sprintに使う。Trigger: codex-luna-sprint、Luna worker sprint、Lunaへ限定委譲、安価なCodex subagentへ安全に分割。"
---

# Codex Luna Sprint

Lunaを前提に計画しない。mainが利用者の通常体験を理解・反証してから実装を設計する。user story、UX、画面構成、利用者向け文言、domain/API contract、状態遷移の判断は、難易度に関係なくmainから移さない。Lunaには既に確定した契約を機械的に実装・検査できるleafだけを任意委譲する。

## 1. 事実を観察する

解決策を作る前にrepository、最新要求、過去の合意、foundational workflow、user story、画面UX、実data、API/schema、Lab/prototype/fixtureを読む。既存実装を`production normal path`、`fallback`、`technical substrate`、`Lab/fixture only`へ分類する。この段階ではUI、API、schema、Luna taskを確定しない。

## 2. Product frameを確定する

`scripts/init_sprint.sh`でSprintを作り、`product-frame.md`を`draft`から埋める。

- 利用者、開始状態、達成結果、通常story、optional/fallback、失敗復旧、reload後の継続。
- 上流から継承する値と、新しく判断する値。
- UX invariant、Lab/fixture限定制約、source precedence、未解決decision。
- normal、exception、recoveryの代表journey。

最低限、上流値を再入力させない、uploadや内部設定を通常CTAにしない、Lab制約をdomain制約にしない、import/生成成功と人間の承認を分離する、例外操作を常時主表示しない、を反証する。

Product frame reviewはmainが[main-review.md](references/main-review.md)に従って行う。read-only subagentを使う場合も、正本の所在・現行挙動・矛盾候補の収集に限り、user storyやUXの採否判断を依頼しない。不一致や未解決decisionがあれば`draft`のままにし、architectureへ進まない。

## 3. Implementation planを導出する

Product frameを`confirmed`にした後だけ`implementation-plan.md`を作る。architecture、API/schema、data flow、state transition、migration、security、failure、test、browser acceptanceを各story/invariantへtraceする。

- 実装上便利なだけのdomain field、shadow state、既定値を追加しない。
- 通常journeyを成立させない縦切りは完成UXでなく`technical substrate`と記録する。
- 下位の実装都合でproduct frameを書き換えない。矛盾時は`plan-reopened`へ戻す。

Implementation planも別reviewを通し、`confirmed`後にだけtaskへ分解する。

## 4. 全taskをmain担当で分解する

最初は全taskを`main-codex`にする。各taskへuser story、UX invariant、normal-path上の位置、source、scope、side effect、oracle、受入条件を書く。[task-contract.md](references/task-contract.md)を全文読む。

次をすべて満たすleafだけ`luna_sprint_worker`へ移す。

1. product/architecture判断が残らない。
2. I/O、error algebra、positive/negative caseが完全にfixedで、利用者向け文言やinteractionを含まない。
3. 排他的write scopeとstrong oracleがある。
4. localで可逆で、棄却しても全体設計が壊れない。
5. review負担がmain実装より小さい。

user story、UX invariant、画面構成、presentational component、利用者向け文言、accessibility contract、shared schema、migration、API/domain contract、API mutation、state transition、security、課金、provider、integration、実browser acceptanceはmainが所有する。Luna候補は原則としてpure function、parser/serializer、固定済みrequest/response adapter、fixture builder、table-driven behavior test、機械的codemodに限る。候補0件は正常で、`tasks.md`へmain-only理由を記録する。

「小さいUI leafだから」「既存画面に合わせるだけだから」は委譲理由にならない。ユーザーに見える順序、強弱、文言、empty/error/stale表現、keyboard/focusを含む時点でmain taskである。API adapterは、HTTP method/path、request/response schemaとfield mapping、validation/coercion、auth/authorization/ownership（不要ならmainが`N/A`と明記）、success status、error algebra/body、idempotency、mutation/side-effect semanticsのすべてをmainが完全指定し、Lunaに残る作業が機械的写像だけの場合に限り候補になる。

## 5. Lunaへ限定contractを渡す

計画全文を渡さず、`prompts/Txx.md`へtask-local contractを抽出する。

- 絶対pathと該当sectionのsource-of-truth。
- mainが抽出した固定済みI/O、error algebra、positive/negative table。Lunaへproduct frameの解釈を要求しない。
- 禁止するproduct/UX/schema/API/state判断、排他的scope、停止条件。
- worker verificationと、それと異なるmain oracle。

「自然なUXを考える」「既存コードに合わせて適切に設計する」「適切なAPIを作る」のような未知判断を依頼しない。UI/UX、文言、domain/API/state判断が途中で必要になった時点で変更せずmainへ返す。contract矛盾、scope競合、外部副作用が必要な場合も停止する。正本Custom Agentは`luna_sprint_worker`とし、model/reasoningを上書きしない。

## 6. 四段階でreviewする

1. Product frame review。
2. Implementation plan review。
3. Luna task diff review。
4. Whole-user-journey review。

worker報告を主張として扱い、mainが実diff、focused test、独立negative caseを確認する。task判定は`accepted`、`corrected-by-main`、`rejected`、`blocked`、全体判定は`accepted`、`rework`、`plan-reopened`とする。taskが全件通っても、代表journeyが上流入力から実画面で完走しなければGateを合格させない。

## 7. 完了報告

- Product frameとImplementation planのreview結果。
- main-only taskとLunaへ移したleaf、その理由。
- agent identity、worker検証、main独立検証、task判定。
- Whole-user-journeyの証拠、全体判定、残リスク。
