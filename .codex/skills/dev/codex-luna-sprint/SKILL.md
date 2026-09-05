---
name: codex-luna-sprint
description: "永続的な計画・taskと段階検収が必要な実装Sprintに使う。Astra／SolがStory・UX・契約を確定し、完全固定済みの機械的leafだけをLunaへ任意委譲する。"
---

# Codex Luna Sprint

Lunaを前提に計画しない。mainが利用者の通常体験を理解・反証してから実装を設計する。user story、UX、画面構成、利用者向け文言、domain/API contract、状態遷移の判断は、難易度に関係なくmainから移さない。Lunaには既に確定した契約を機械的に実装・検査できるleafだけを任意委譲する。

## 適用と正本

main CodexがAstraでもSolでも同じ契約を使う。モデル設定は自動で変更しない。会話内で完結する通常のleaf分担には[codex-luna-task-split](../codex-luna-task-split/SKILL.md)を使い、Sprintを作らない。

既存のStory台帳とPLANがある場合はそれらを正本とし、Product frameとImplementation planは対象条件・未解決判断・taskへの対応を持つ作業資料にする。契約本文や進捗を二重管理せず、正本のpathとsectionを参照する。Story／PLANの作成・意味変更には[develop-user-story](../develop-user-story/SKILL.md)を適用する。独立レビューとmainの採否判断は両立し、main責任を理由に独立Gateを省略しない。

同じ対象成果・現在契約・判定質問・証拠が変わらず、必要な役割分離を満たす既存レビューがある場合は、mainが対応を確認して結果を再利用する。不足する観点だけを確認し、同じGateをSprint名で繰り返さない。契約が変わった場合は影響Gateを再開する。

## 1. 事実を観察する

解決策を作る前に、最新要求、過去の合意、repositoryとStoryを確認し、対象成果の判断に必要な通常導線、画面、実data、API/schema、Lab/prototype/fixtureを調べる。存在しない要素を追加要件にしない。既存実装を`production normal path`、`fallback`、`technical substrate`、`Lab/fixture only`へ分類する。この段階ではUI、API、schema、Luna taskを確定しない。

## 2. Product frameを確定する

`scripts/init_sprint.sh --slug <slug> --workspace <workspace>`でSprintを作り、`product-frame.md`を`draft`から埋める。既存Sprintの再開では再生成せず、現在の資料を使う。

- 利用者、開始状態、達成結果、通常storyと、契約に存在するoptional/fallback、失敗復旧、reload後の継続。
- 上流から継承する値と、新しく判断する値。
- UX invariant、Lab/fixture限定制約、source precedence、未解決decision。
- normalと、契約に存在するexception、recoveryの代表journey。

契約に適用するUX invariantだけを反証する。継承すべき上流成果物がある場合は再入力・再uploadを通常入口にせず、手元の素材を取り込む製品ではuploadを通常入口にできる。Lab制約を製品制約へ持ち込まない。人の承認が必要な導線では生成成功と承認を分け、例外導線がある場合は通常操作との優先度を確認する。

Product frame reviewはmainが[main-review.md](references/main-review.md)に従って行う。read-only subagentを使う場合も、正本の所在・現行挙動・矛盾候補の収集に限り、user storyやUXの採否判断を依頼しない。不一致や未解決decisionがあれば`draft`のままにし、architectureへ進まない。

## 3. Implementation planを導出する

Product frameを`confirmed`にした後だけ、`implementation-plan.md`へ実装設計を記入・確定する。生成直後の空のdraft雛形は、この開始条件を満たしたことを意味しない。対象に存在するarchitecture、API/schema、data flow、state transition、migration、security、failure、test、browser acceptanceを各story/invariantへtraceする。既存PLANで確定済みの項目は正本を参照する。

- 実装上便利なだけのdomain field、shadow state、既定値を追加しない。
- 通常journeyを成立させない縦切りは完成UXでなく`technical substrate`と記録する。
- 下位の実装都合でproduct frameを書き換えない。矛盾時は`plan-reopened`へ戻す。

Implementation planも別reviewを通し、`confirmed`後にだけtaskへ分解する。

## 4. 全taskをmain担当で分解する

最初は全taskを`main-codex`にする。各taskへuser story、UX invariant、normal-path上の位置、source、scope、side effect、oracle、受入条件を書く。[task-contract.md](references/task-contract.md)のRouting registryを読む。Worker promptは実際に委譲する場合だけ読む。

次をすべて満たすleafだけ`luna_sprint_worker`へ移す。

1. product/architecture判断が残らない。
2. I/O、error algebra、positive/negative caseが完全にfixedで、利用者向け文言やinteractionを含まない。
3. 排他的write scopeとstrong oracleがある。
4. localで可逆で、棄却しても全体設計が壊れない。
5. contract作成と独立検収を含めても分担利益がある。
6. 独立、または先行依存が完了しており、実行中のtask間調整が不要である。
7. workerと適用先の指示がその実行を許可している。

user story、UX invariant、画面構成、presentational component、利用者向け文言、accessibility contract、shared schema、migration、API/domain contract、API mutation、state transition、security、課金、provider、integration、実browser acceptanceはmainが所有する。Luna候補は原則としてpure function、parser/serializer、固定済みrequest/response adapter、fixture builder、table-driven behavior test、機械的codemodに限る。候補0件は正常で、`tasks.md`へmain-only理由を記録する。利用可能な`luna_sprint_worker`がなければmainが実行し、別agentやmodel overrideで代替しない。

UIの表示順・強弱・文言・keyboard/focusを含む作業はmainが所有する。固定済みAPI adapterの指定項目は[task contract](references/task-contract.md#routing-registry)で確認し、Lunaに残る仕事が機械的写像だけの場合に限る。

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

worker報告を主張として扱い、mainが実diff、focused test、独立negative caseを確認する。task判定は`accepted`、`corrected-by-main`、`rejected`、`blocked`、全体判定は`accepted`、`rework`、`plan-reopened`とする。taskが全件通っても、契約上必要な代表journeyが通常入口から完走しなければGateを合格させない。UIを含む成果は実画面、その他は公開interfaceや実成果物で確認し、不要なUIを検証のために作らない。

## 7. 完了報告

- Product frameとImplementation planのreview結果。
- main-only taskとLunaへ移したleaf、その理由。
- agent identity、worker検証、main独立検証、task判定。
- Whole-user-journeyの証拠、全体判定、残リスク。
