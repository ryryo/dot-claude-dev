---
name: develop-user-story
description: repository直下またはproject-localのユーザーストーリー台帳を製品契約の正本として、ストーリーの追加・精緻化、関連PLANの作成・実行、TDD実装、PR／Gateレビュー、Journey検証、証拠記録、状態更新を一貫して行う。Use when adding or refining a user story, planning, implementing, or reviewing work identified by a US ID or Gate, resuming its development, or verifying whether its acceptance criteria are genuinely complete.
---

# Develop User Story

リポジトリ固有のドメインを決め打ちせず、適用先の指示とストーリーから実装・検証契約を組み立てる。

## 1. 正本とledger pathを解決する

1. repository rootと適用される`AGENTS.md`を特定して全文を読む。
2. userが明示した`USER_STORIES.md` pathを最優先する。
3. 明示pathがなければ、指定PLANと同階層、その祖先、repository rootの`docs/USER_STORIES.md`の順に探す。候補が複数残る場合は勝手に選ばず確認する。
4. 解決したledgerを読み、対象US、全体ルール、状態、受け入れ条件を確認する。
5. `git status --short`で既存変更を確認し、他者の変更を上書きしない。
6. ledgerと同じscopeのPLAN／EVIDENCE、関連実装・テストを読む。
7. コードから判明する事実を調査し、利用者の目的やscopeを変える未確定事項だけを質問する。

`USER_STORIES.md`を製品契約、PLANを実装進捗、コードとテストを実装証拠、EVIDENCEを重要な実検証証拠として扱う。下位の都合が上位契約と矛盾する場合は、黙って契約を弱めない。

## 2. 操作を決める

- **追加・精緻化**: 利用者の成果、通常導線、例外・復旧、観測可能な受け入れ条件を確定する。
- **計画**: 受け入れ条件を、独立してhandoffできる成果へ写像する。単一成果なら通常PLAN、複数の独立成果へ分かれるなら実行PLAN群と進行PLANを作る。
- **実装**: 対象USとPLANの未完了項目を固定し、TDDで必要十分な縦切りを実装する。
- **レビュー**: PR内の担当Story／Gateごとに判定質問を分け、affected closureを探索して採否とroutingを決める。意味変更された別Story／PLANは同じGateへ混ぜず、別Gateとして判定する。
- **検証**: 受け入れ条件ごとに自動テスト、実画面、外部サービス、復旧・再読込の必要性を判定して確認する。

ストーリーの追加・実装・検証で対象USが指定されていない場合は、依頼内容と台帳の優先度から一件に絞る。複数USを同じ実装scopeに入れるのは、一つの利用者成果として分離不能な場合だけにする。ただし、残scope全体のPLAN化、実行順の整理、並列可能なPLAN設計を求められた計画操作では、複数USを計画入力としてよい。この場合もUSを結合せず、条件ID単位の追跡を維持する。

ストーリーを新規作成または利用者から見える契約を意味的に変える精緻化（例: タイトル、`きっかけ`、活動、目的、scope、導線、受け入れ条件）をした場合は3.1、PLANまたはplan setの実装・検証契約を作成または意味的に変更した場合は4.1の独立レビューを、次工程へ進む前に通す。進捗、実行担当、session、証拠link、結果記録、誤字、formatだけの更新は新しいGateを発生させない。意味変更時は、担当Story／Gateについて、変更した条件ID、surface、依存から成立可否が変わり得るaffected closureをreview対象にする。別Storyや後続Gateへは広げない。

## 独立レビュー共通手順

各Gateはartifact全体を広く改善する場ではなく、「次工程へ渡せるか」という一つの質問に答える場とする。担当User Storyの利用者成果・受け入れ条件と、現在のPhase／Gateが所有する成果・判定質問をreview scopeの正本にする。diffや技術領域だけで狭めず、その成立に必要なaffected closureを確認する一方、同じStory／Gateを破る到達scenarioを示せない候補は現在作業へ持ち込まない。

レビューは次の6工程を順に進める。各工程の完了条件を満たすまで次へ進まない。

### 工程1 — 対象を固定する

main Codexが一時的なReview Briefを作り、reviewerへ次を渡す。

- Gate固有の判定質問
- 対象artifactと変更箇所
- 固定済みのGoal、scope、対象外、条件ID
- 通常導線、明示済みの例外導線、実際に到達するrisk trigger
- 適用される指示、一次情報、関連artifact、判断に必要な既存実装
- 公開状態・出力contractを扱う場合、そのsurface、producer／consumerの入口、未実装consumerへ渡すreview済みcontract
- findingまたはriskの送り先となる次工程

Review Briefは恒久fileにしない。作成者の結論、想定する正解、懸念点一覧は渡さず、レビュー担当を作成過程から独立した新規contextで起動する。sub-agentを使う場合は`fork_turns: none`相当とする。

**完了条件:** 判定質問、scope、対象外、条件ID、到達導線、risk trigger、必要な一次情報、公開surfaceが特定されている。

### 工程2 — 探索を完了する

reviewerは共有fileを編集せず、Gateの監査項目を最初に分類する。

- **適用**: 担当Storyの成立に必要で、現在Gateが所有する到達可能な導線に該当する
- **後工程**: 同じ担当Storyの成立に必要だが、別artifactまたは明示済みの後続Gateが所有する
- **非適用**: 担当Storyと現在Gateの成立には不要である。finding、risk、deferred、taskへ昇格させない

failure、cancel、retry、reload、権限、privacyなどは適用性を考える候補であり、存在しない状態や操作まで増やさない。適用とした項目だけを監査する。

状態fulな変更、または公開状態・出力contractが複数componentにまたがる変更では、現在のStory／Gateに限定した一時的な状態・contract coverage表を作る。

- 行: 到達可能な開始状態、操作、終了結果、処理の割り込み順序。event streamやgestureで、更新が一度もないまま終了できるなら、その終了結果も一行にする。
- 列: 公開状態、返値、receipt、projection、event、外部から渡された処理や共有resourceへの作用、共有・永続状態。
- 各マス: 期待する不変条件とbehavior oracle。既存consumerがあればproducerからconsumerの前提までfield単位で照合する。consumerが後続Gateで未実装の場合だけ、review済みの明示handoff contractをconsumer側oracleにする。

現在Gateは、producerが生成するhandoff fieldの意味・形式・不変条件を所有する。後続Gateが所有するのはconsumer実装、配線、統合後の実動作、Journeyである。consumerが未実装であることだけを理由に、producerの誤った出力を後工程へ送らない。

外部から渡されたallocator／callbackの呼び出しや、共有queue／resourceの予約など、失敗時に巻き戻せない作用は、それ自体を表の観測列に含める。その作用より後にvalidationやnormalizationなどの失敗可能な処理が残る場合は、作用前に完了するか、staging／rollbackによってreject時の不変を保つことをbehavior oracleで確認する。

存在しない組合せは追加しない。空欄は未確認であり、test件数、領域名、内部assertで埋めない。複数reviewerを使う場合も技術領域だけで分割せず、main Codexが表全体のcompletion ownerとなる。少なくとも一つのreview scopeはproducerからconsumerまで横断する。

**完了条件:** main Codex自身のaffected closure監査、依頼した全reviewerのDiscovery、適用した状態表の全マスの確認が完了している。途中のfindingを共有する場合は「暫定・Discovery継続中」と明記し、この工程の完了扱いにしない。

### 工程3 — 候補を統合する

main Codexが全reviewerの候補を再評価し、`適用`または`後工程`だけを`fix-here`、`plan-input`、`implementation-risk`、`journey-risk`へroutingする。`非適用`はroutingしない。

現在Gateを止めるblockerは、次をすべて満たすものに限る。

1. 現在のGateとartifactが責任を持つ。
2. 固定済みの通常導線または明示された例外導線から到達できる。
3. 既存のGoal、scope、受け入れ条件、制約のいずれかを破る。
4. 一次情報と破綻する具体的scenarioで根拠を示せる。
5. 最小修正が新しい利用者成果、scope、製品判断を追加しない。

blockerには、破る契約、根拠、到達scenario、最小修正案を付ける。現在の契約を実現できない場合は`契約判断待ち`とする。main Codexはpriorityやreviewerの結論をそのまま採用せず、producerとconsumerの責務を分けたうえで採否を決める。blocker候補を棄却する場合は、その候補を挙げたreviewerへ、棄却根拠に事実誤認がないか一度だけ確認する。

**完了条件:** 全候補の適用性、owner、routingが決まり、根本原因と由来が重複排除され、未分類の候補がない。

### 工程4 — 修正を一括する

工程2と3が終わる前に最終修正指示を出さない。`fix-here`は根本原因ごとにまとめ、既存契約を変えない一つの修正batchとして現在artifactへ反映する。途中で共有した暫定findingだけを先に直してDiscovery完了とみなさない。

**完了条件:** `fix-here`がある場合は、全修正と直接回帰が同じbatchで反映され、必要な自動検証が完了している。`fix-here`がない場合は、修正不要と確認できている。

### 工程5 — 固定した最終成果を再レビューする

工程2の開始後に成果を意味的に変更した場合は、既知blockerの直接回帰を確認してから、独立性を満たす新規contextで固定した最終成果をreviewする。修正行や既知指摘だけに狭めず、同じStory／Gateのaffected closureをもう一度確認する。別Story、後続Gate、一般的なhardeningへは広げない。

工程2の開始後に意味変更がなければ、工程2で確認した成果を最終成果として扱い、同じreviewを繰り返さない。

最終成果レビューで新しい候補が見つかった場合は、修正へ直行せず工程3へ戻して採否とroutingを決める。`fix-here`として採用した場合は、工程4と工程5を順にやり直す。

同じ根本原因のfindingが分割して続く場合は局所patchを止め、関連する状態遷移または設計境界をまとめて見直してから工程4へ戻る。

**完了条件:** 既知反例と同scopeのaffected closureを一度に確認し、状態表に未確認の適用マスがなく、未解決blockerもない。

### 工程6 — Gateを判定する

適用項目の判断、blocker、後工程へ送るrisk、合否に必要な未確認事項、同scopeの残余riskをまとめ、Gate固有の判定質問へ明示的にYes／Noで答える。reviewer待ち、状態表の未確認マス、未分類候補、未解決blockerが一つでもあればGOにしない。「問題なし」だけの回答もGate通過に使わない。

初回の見逃しか修正由来かはfindingの採否条件にしない。独立エージェントを利用できない場合は自己レビューで代替せず、その事実をuserへ伝え、次工程へ進む前に判断を求める。レビュー報告用の恒久fileは、userが求めた場合だけ作る。

## 3. ストーリーを追加・更新する

解決したledgerの記入雛形と、「ストーリーの作り方」「受け入れ条件の書き方」に従う。

ストーリーは利用者側から作る。PLAN、実装、機能一覧からストーリーを逆算すると、実装したものを追認するだけの契約になる。

- ストーリーを先に確定し、PLANはそのストーリーから作る。既存PLANを要約してストーリーにしない。
- `きっかけ`へ、誰がどの場面で何に困ったか、どの依頼・観察から来たかを具体的に書く。ここを書けない場合は、利用者側の根拠がまだない。userへ確認するか、ストーリーにしない。
- 台帳の「利用者の活動」を先に更新し、そのストーリーがどの活動を進めるかを`活動`へ書く。活動に紐づかないストーリーは、利用の流れではなく機能を並べている疑いとして見直す。
- 新規IDは既存の最大番号に1を加える。欠番を埋め直したり既存IDを採番し直したりしない。
- タイトルを画面名、機能名、技術名にしない。利用者が達成する状態で書く。
- ストーリーはPLANの単位ではなく、利用者が一度で完了できる成果の単位で切る。ストーリーとPLANが常に1対1に並ぶ場合は切り直しを検討する。
- 利用者の目的には、やりたいことに加えて、それで得られる成果と避けられる困りごとを書く。成果が書けない場合は切り方を見直す。
- 例外条件を追加する前に、その操作が実際に失敗、再試行、cancel、reload、復元を持つかを判定する。該当するものだけ、利用者が観測する結果を記載し、一般的な失敗一覧を各ストーリーへ展開しない。
- 共通ルールを各USへ複製しない。固有の条件だけを記載する。
- 着手前は`todo`、実行中は`doing`とする。外部条件により進められない場合だけ理由を添えて`blocked`とする。

受け入れ条件は次の形で書く。ここが弱いと、実装したものを追認するだけのレビューになる。

- 1条件は、1つの状況、1つの操作、1つの観測できる結果で書く。読点や「かつ」で複数操作を束ねた条件は分割する。
- 条件IDを`US-XX-01`形式で付け、末尾へ連番追加する。既存IDの意味を変えず、意味が変わる場合は新IDを追加する。
- 各条件へ`例:`を1つ以上付け、枚数、秒数、file名、model名、表示文言の要点など具体値を書く。具体例を書けない条件は、まだ合意できていないとみなす。
- 値が未確定なら`例: 未確定（決めるべき値）`と書き、その条件をチェックしない。値を推測で埋めない。
- 「成立する」「正しく」「適切に」「安全に」「うまく」「〜など」「〜等」を条件へ書かない。失敗したと客観的に言えない条件は条件ではない。
- 適用された失敗、再試行、再生成、reloadの条件は、失敗の名前ではなく、利用者が見る内容と保持される対象で書く。
- 実装名、内部型、内部ID、file pathを条件へ書かない。それらはPLANが持つ。
- 受け入れ条件が10件を超えたら、複数の利用者成果が混ざっていないか確認して分割を検討する。

validatorが条件を追跡できるよう、条件行を`- [ ] \`US-XX-01\` ...`、具体例をその直下の`  - 例: ...`で記載する。検証の`未確認条件`は未チェック条件IDを過不足なく列挙し、残件がなければ`なし`と書く。PLAN／EVIDENCEから参照する条件IDは台帳に存在するものだけにする。

### 3.1 ストーリー独立レビューGate

ストーリーをPLANや実装の入力として固定する前に、作成者とは別のエージェントを1名以上立ち上げ、共通手順に従ってreviewする。このGateの判定質問は「PLANの入力として、利用者成果と合否が確定しているか」とする。

次の項目の適用性を判定し、適用されたものだけを監査する。

- `きっかけ`、活動、目的、scopeが利用者側の一つの成果としてつながり、機能やPLANから逆算されていないか
- 各条件が一つの状況、操作、観測結果に分かれ、具体例で合否を判定でき、目的とscopeを過不足なく覆うか
- 明示された通常導線と例外導線に、利用者が観測する完了、失敗、保持、再試行の結果があるか
- cancel可能な操作がある場合のcancel、状態を保持する契約がある場合のreload／復元、利用者・領域を切り替える機能での切替だけが欠けていないか
- 権限、privacy、外部状態、費用が利用者の操作結果を変える場合、その境界が観測可能な条件になっているか
- 関連ストーリーとの重複、矛盾、順序依存、責務の隙間、対象外へ追い出した必須成果がないか

このGateの`fix-here`は、成果の混在、scopeの矛盾、観測不能な条件、明示された導線の欠落、関連ストーリーとの契約衝突に限る。API方式、保存方式、account固定、idempotency、upload手順、TOCTOU、内部retry、細かな障害分類などの実装機構は、固定した利用者成果と到達可能なrisk triggerを成立させるために次artifactで判断が必要な場合だけ`plan-input`または`implementation-risk`へ送る。それ以外は`非適用`とする。技術riskを理由に利用者成果を増やしたり、別ストーリーへ分割したりしない。

main Codexは`fix-here`だけをledgerへ反映し、後工程へ送る項目は受け入れ条件に追加せずReview BriefまたはPLAN作成時の入力として引き継ぎ、共通手順に従ってGateを閉じる。

## 4. PLANを作成・実行する

PLANが必要な場合は、ledgerと同じproject scopeにあるPLAN templateを使う。repository直下台帳では`docs/PLAN/_TEMPLATE.md`、project-local台帳では同階層の`_PLAN_TEMPLATE.md`を優先する。候補が複数または存在しない場合は独自形式を作る前に確認する。

### 4.0 既存資産・参照実装の再利用判定

適用先の指示、ledger、template、REFERENCE、dependency管理、または現行repositoryが再利用候補を示す場合は、実装方式を固定する前に次を行う。REFERENCEや比較表は候補探索の入口であり、その要約だけを実source調査の代用にしない。materialize前に、利用者成果とoracle、license、platform／runtime、現在scopeから候補を絞ってよいが、sourceが現在読めないこと自体を調査対象外理由にしない。

- 同一repository内の合理的候補は、current path、baseline、owner、公開contract、関連testを現行treeで確認する。外部の合理的候補は、provenance記録にある固定revisionまたは解決済みversionを実際に読める状態へmaterializeし、記録された版との一致を確認する。外部sourceの取得や展開が現在の権限・環境でできなければ、要約だけで採否を確定したり再実装へ逃げたりせず停止する。未materializeで除外できるのは、license非互換、platform／runtime不適合、現在scopeに対応capabilityがない等、source可用性と独立した理由を、検証oracleに対応する最小capabilityまたは採用単位そのものへ適用して先に記録できる候補だけとする。製品／root／巨大engine全体だけの不適合は、portableなmodule／patternを読む前の除外理由として不十分である。
- repositoryのmanifest、catalog、REFERENCE、submodule一覧が示す候補を、素のcodebase検索に出ないことだけで不存在扱いしない。hidden directoryは通常の`rg`／`rg --files`から省かれ得るため、projectが示すpathを明示するか`rg --hidden`等で探索し、uninitializedなgitlinkや未materialize directoryはsource不在ではなく可用性未確認として扱う。
- 利用者成果と検証oracleに対応する最小capabilityへ範囲を絞り、名称が一致するprimitiveだけで終えず、存在する範囲で`primitive／domain -> consumer／adapter -> route／UI／job等の統合点 -> behavior test`を辿る。存在しないlayerはその事実を記録する。
- 同一repository内再利用、固定dependency、無改変／改変snapshot copy、契約・algorithm参照による再実装、不採用のうち適用可能な方式を比較する。製品全体、巨大engine、root dependencyを不採用にしても、現在のoracleを満たす狭いmoduleやpatternの部分移植まで同じ理由で棄却しない。
- 同一repository内候補はcurrent path、baseline、owner、公開contract、回帰oracleを記録する。外部候補はprovenance記録のpathとmaterializeしたsource pathを記録する。どちらも、実際に確認したconsumer／testまたは探索範囲付きの不存在、最小採用単位、現在のcontractへ接続する差分、持ち込まない依存・状態・機能、parity／negative oracleをPLANまたはその参照先へ記録する。外部sourceのrevision／version自体とlicense／provenanceはREFERENCE、EVIDENCE、noticeまたはdependency管理を正本とし、PLANには重複させない。

全候補やsource tree全体の一律精読は求めない。適用先が候補を示さず、現行実装と受け入れ条件からも再利用可能性がない場合は、その根拠を短く記録すればよい。

- PLANの単位はUS、受け入れ条件の個数、技術layer、Phase、実行環境ではなく、独立してhandoffできる一つの成果で決める。実行主体や実行環境の識別子は計画外の管理情報とし、PLANへ記録しない。
- 一つのUSを複数PLANへ写像してよく、一つのPLANが複数USの条件を扱ってもよい。candidate PLANは担当条件を実装してもUS完了を主張せず、統合・Journey・外部検証を所有するPLANが最終状態を更新する。
- 分割候補ごとに、明示した開始条件、排他的write scope、handoff成果、localで再現できる検証oracle、統合owner、並行化の実益があるかを確認する。一つでも成立しない候補は、別PLANにせず同じPLANのPhaseへ戻す。条件数が多いことだけを分割理由にしない。
- 複数PLANが必要と判断した場合は、[並列実行可能なPLAN設計](references/parallel-plan-execution.md)を読み、対象scopeの実行PLAN群と進行PLANを一度の計画操作で作る。一枚作るたびに次のUSや次のPLANをuserへ選ばせず、未確定の製品判断だけを質問する。
- 進行PLANは依存graph、直列／並列lane、各PLANの状態、開始Gate、統合順、統合・外部状態owner、次に開始可能なPLANを管理する。実行割当はPLANの外で管理し、実装taskやPhaseを個別PLANと重複記載しない。各実行PLANは自分のread／write scope、Goal、条件ID、開始Gate、handoff、focused検証、停止条件だけを自己完結して持つ。
- PLAN、進行PLAN、review metadataにはversion controlや実行環境の識別子、content digestを書かない。変更の同一性はpath、先行Gate、公開contract、検証結果で確認する。外部sourceの版・license provenanceが必要な場合は`docs/REFERENCE/`、`docs/EVIDENCE/`、noticeまたはdependency管理へ置き、PLANはそのpathだけを参照する。
- 複数の実行PLANの開始、並行lane、merge／Join Gate、external成果へのhandoffを所有するintegration／coordination PLANには、Mermaidの実行DAGを必須とする。別のREADMEや進行PLANへのlink、文章だけの順序、PLAN一覧表だけでは代替しない。図には開始Gate、hard dependency、並行可能な分岐、merge point、条件付きfallback、外部停止Gate、最終Joinを示し、本文の開始条件・Gate・ownerと同じ名前で照合できるようにする。
- 対象USの受け入れ条件が確定してからPLANを作る。PLANの都合で条件を足したり弱めたりしない。
- 対象USと受け入れ条件をPLANから追跡可能にする。条件IDで参照する。
- Goal、制約、対象外、Phaseの完了状態、Gate、検証commandを実装前に固定する。
- ストーリーの導線と現在のrepositoryから、実際に到達する外部作用、権限、費用、永続状態、共有ownerをrisk triggerとして特定する。Gateと検証はそのtriggerへ対応させ、一般的なrisk一覧をPLANへ展開しない。
- 実装詳細や進捗ログをストーリー台帳へ書かず、PLANへ記録する。
- 有料サービス、実生成、deploy、外部データ変更などは明示承認を得るまで未完了にする。
- 実装中に契約変更が必要になった場合は、コードで迂回せずUSとPLANを先に見直す。

### 4.1 PLAN独立レビューGate

PLANを実装の入力として固定する前に、ストーリーレビュー担当とも作成者とも別のエージェントを1名以上立ち上げ、共通手順に従ってreviewする。このGateの判定質問は「別の実装者が利用者契約を変えずに実装し、完了を再現可能に検証できるか」とする。レビュー担当にはレビュー済みledger、PLAN template、PLAN、関連実装・テスト・設計資料に加え、再利用判定に使ったmaterialize済みsourceの採用候補、consumer／統合点、関連test、調査対象外候補とsource可用性に依存しない除外理由を一次情報として渡す。要約資料や作成者が選んだ単一fileだけへ入力を狭めず、作成者の採否結論を前提にしない。consumerが存在する選定capabilityは検証oracleから連鎖を少なくとも1本独立に辿り、存在しないcapabilityは探索範囲・検索結果・適用先側oracleを独立に確認する。

複数PLANを同時作成・再編した場合は、進行PLANと全実行PLANを一つのplan setとして同じreviewerが横断reviewする。ファイルごとに別Gateを繰り返さず、依存graphとhandoffを含むplan set全体が固定された時点で一回通す。

次の項目の適用性を判定し、適用されたものだけを監査する。

- 全条件IDと各`例:`がPhase、Gate、検証へ追跡でき、PLANがストーリーを弱めたり未確認の条件を完了扱いしたりしていないか
- 開始条件、依存関係、実装順、停止Gate、対象外が現在のrepository状態と整合し、実装者が契約判断なしで開始できるか
- 複数PLANの場合だけ、閉路、不要な直列待ち、同一file／generated file／lockfile／台帳／EVIDENCE／外部状態の複数ownerがなく、handoffを統合ownerが同じreview済みcontractと開始Gateで検証できるか
- integration／coordination PLANの場合だけ、Mermaid DAGがrender可能で、本文と同じ開始Gate、依存、並行lane、統合／Join Gate、fallback、外部停止Gate、最終ownerを表すか
- ledgerまたは既存実装で同じ契約を通ることが確認できたroute、API、server function、background処理、session、cache、保存先が、実装責務と検証から漏れていないか
- projectが再利用候補を示す場合だけ、合理的候補の固定sourceがmaterializeされ、存在する最小capabilityのconsumer／統合点／testまたは探索範囲付きの不存在まで確認され、直接利用・部分copy・再実装の比較からより狭く契約適合する採用単位を落としていないか。未materializeの除外候補がsource可用性、または製品／root／engine全体だけの不適合を理由にしていないか
- ストーリーで明示されたnormal pathと例外導線について、必要な実装責務と再現可能な検証oracleがあるか
- test、typecheck、build、実画面Journey、実service、証拠が、適用されたrisk triggerに応じて分かれ、mockや静的文字列一致を実検証の代用にしていないか
- 現在の導線が実際に外部変更、課金、secret、個人情報、破壊的変更を扱う場合、その直前Gate、承認、停止条件、rollbackまたは安全な失敗状態があるか

このGateの`fix-here`は、条件追跡漏れ、現在のrepositoryでは実行不能な開始条件、owner衝突、未承認の外部作用、検証oracleの欠落、採否根拠にするsource未materialize、存在するとされたconsumer／testを読めない状態、本文とDAGの契約矛盾に限る。consumer／testが存在しない候補は、探索範囲と不存在を記録し、適用先側のparity／negative oracleをPLAN化できれば未確認扱いにしない。関数構造、内部error分類、一般的なhardening、将来のscale、現在の導線から到達しない障害、別USの改善は現在のPLAN reviewのfindingや追加作業にしない。PLAN reviewerは新しい受け入れ条件を作らず、PLANで現在のストーリーを実現できない場合だけ`契約判断待ち`として返す。

main Codexは`fix-here`だけをPLANへ反映し、全条件を追跡できることを確認して共通手順に従ってGateを閉じる。ストーリーレビュー担当とPLANレビュー担当を兼任させない。

### 4.2 PLANを完遂する

userが実行PLANに従った全実装を求めた場合は、そのPLAN全体だけを現在taskのscopeとする。進行PLANは実装scopeにせず、開始可能な実行PLANの選択、依存・状態・handoffの確認に使う。複数PLANを並行実行するときは、各laneのwrite scope、port、生成物、外部状態を衝突させない実行contextを計画外で割り当てる。同じcontextで直列実行できる場合は不要な分離を要求しない。最初の未完了項目から依存順に進め、各PhaseとGate、担当するJourney、証拠、handoffまで、未完了項目がなくなるか次の停止条件に当たるまで継続する。PhaseやGateを一つ終えたこと、作業量が多いこと、通常のテスト失敗や実装上の難しさだけを理由にuserへ返さない。

最初のtestまたはproduction codeを編集する前に、同一repository内候補はcurrent path、baseline、公開contract、関連testを、外部候補は参照sourceのpathとprovenance記録にある固定revision／versionとの一致を現在contextで一度確認する。manifest等がhidden pathを示す場合は明示pathまたはhidden探索を使い、素の全体検索の不一致をsource不存在扱いしない。どちらも存在すると記録したconsumer／testを辿り、再利用分類の前提が現行repositoryと一致することを確認する。consumer／testが存在しないと記録した候補では、その探索範囲と適用先側oracleを確認する。通常の実装不具合ごとに探索を繰り返さない。ただし、実画面・実service・実media等の観測が選定時のplatform／runtime前提を反証した場合、またはPLANにないclock、scheduler、queue、retry、resource lifecycle、serialization等の仕組みを独自実装しないと修正できないと判明した場合は、次の局所patch前に4.0の該当capabilityだけを再確認する。

再確認で再利用分類、source、採用単位、依存閉包、license／provenance、実装・検証責務を意味的に変える場合は、コードだけで切り替えずPLANを更新し、4.1を影響範囲について再度通す。既定PLAN内の予測済み実装で解消できる通常のdefectは再分類を発生させない。

PLAN内のscopeと権限で安全に解決できる失敗は、原因を調査し、必要な修正と検証を行って続行する。次のいずれかでは、迂回実装や暗黙の契約変更を行う前に停止する。

- ledger、PLAN、適用指示、実repository、外部仕様が衝突し、Goal、scope、受け入れ条件、実装・検証契約の意味変更が必要になる
- 続行に未承認の外部変更、課金、秘密情報、破壊的・不可逆な操作、userだけが決められる製品判断が必要になる
- 必須のdependency、credential、外部状態が利用できず、安全な範囲の確認とPLAN内の代替手段を尽くしても先へ進めない
- PLANが要求する検証oracleを成立させられず、条件を弱める、testを外す、未確認結果を完了扱いする以外に通過方法がない

停止時は、受け入れ条件やGateを弱めず、隠れたfallbackや別仕様で通したことにしない。完了を実証した項目だけをcheckedにし、停止したPLAN項目／Gate、衝突の証拠、安全に試した解決、続行に必要な承認・判断または契約変更、完了済みと未完了の範囲をuserへ報告する。仕様変更が必要な場合は最小の変更案を示すが、userの判断前にledgerやPLANへ反映しない。

## 5. TDDで実装する

### 5.0 テスト作成前の適格性判定

これは事後reviewではない。テストfileを編集する前に対象の合否を次へ分類し、自動テスト不適格ならtest diffを発生させない。分類が終わる前にREDを作らない。

- **自動テスト適格**: 外部から観測できる振る舞い、公開interface、状態遷移、失敗・復旧条件、protocol、保存形式、実際のアクセシビリティ契約。
- **自動テスト不適格**: 静的HTML、文言、見出しやsectionの並び、class、CSS token、style、layout、prompt本文、画像・映像の内容、デザイン性、目視品質。
- **混合**: 操作や状態遷移だけを自動テストへ分離し、静的内容と見た目は実画面・実成果物Journeyへ送る。

不適格な条件に、DOM要素・文字列・class・CSS値・assetの存在をproxyにしたテストを作らない。視覚条件を機械判定するためだけに`role`、`aria-label`、test idを追加し、アクセシビリティテストとして扱うことも禁止する。アクセシビリティ例外は、keyboard、focus、実際のaccessible name／stateなど、それ自体が利用者契約である場合だけ適用する。

reviewerやPLANがstrong oracleを求めても、projectのテスト境界を越える自動テストへ変換しない。自動テスト不適格な成果しかない変更ではREDを省略し、実画面または実成果物で合否を確認する。

1. 自動テスト適格な対象だけ、条件IDまたは再発防止したい失敗を表すテストを先に追加し、意図した理由で失敗することを確認する。条件へ書いた`例:`を、公開behaviorの入力と期待値として使える場合だけ利用する。
2. 現在の契約を成立させる最小限の実装を行う。
3. focused testから上位のtypecheck、build、統合テストへ検証範囲を広げる。自動テスト不適格な条件はこの成功件数へ含めない。
4. ストーリーとPLANで適用されたrisk triggerについて、見落とし、反例、状態遷移、失敗時のデータ保持、外部コストを点検する。現在の導線から到達しない一般的なriskまで実装を広げない。

### 5.1 実装後独立レビューGate

PLAN内の実装項目と通常の自動検証が完了した後、`implemented`への更新と最初の実画面Journey・実service検証の前に、実装者、ストーリーレビュー担当、PLANレビュー担当のいずれとも別のエージェントを1名以上立ち上げる。既定ではPLAN全体に対してこのGateを1回行い、PLANが到達可能な高risk境界と中間reviewの判定質問を明示した場合だけ追加する。既存PLANにこのGateがないか、Journey・実service・`implemented`／`verified`更新より後ろに書かれていても、この順序を優先して実装・自動検証の直後へ割り込ませる。

このGateの判定質問は「現在のdiffと自動検証がledgerとPLANを満たし、未実装を隠さずJourneyへ進めるか」とする。共通手順の工程1から工程6までを順に進め、レビュー済みledgerとPLAN、実際のcode・test・設定、diff、検証結果を一次情報として三者照合する。

次の項目の適用性を判定し、適用されたものだけを監査する。

- codeとtestが、担当する全条件IDと各`例:`の観測可能な振る舞いを満たすか。Journeyまたは実service待ちの条件と未実装を混同していないか
- code、test、設定、実際に変更または利用したsurfaceが、PLANの実装責務、制約、対象外、Gateと一致し、checked項目に実証可能な根拠があるか
- PLANから漏れた受け入れ条件、実装都合の迂回、条件の弱体化、未確認結果を成功扱いするfallbackがないか
- ストーリーとPLANで適用されたnormal path、failure、reject、cancel、retry、reload、復元、状態遷移、利用者・領域切替が、該当するcodeとbehavior testへ反映されているか
- 該当する変更では、共通手順の工程2で作る状態・contract coverage表に未確認の適用マスがなく、外部から渡された処理や共有resourceへの作用を含むproducerとconsumerのcontractがfield単位で一致するか
- testが公開interfaceと再発条件を確認し、内部実装や静的文言だけを固定せず、未確認の実画面・実service結果を代替していないか
- diffから直接到達する計画外の外部副作用、無承認の費用、secret・個人情報の露出、不要なdependency、既存契約のperformance退行がないか

このGateの`fix-here`は、担当条件または現在Gateを破る再現可能な契約違反、実装責務の欠落、誤った完了主張、到達可能な副作用・secret露出・回帰に限る。diffで変更された行やpriorityはscopeの条件にしない。新しい受け入れ条件、別のarchitecture、一般的なhardening、将来scale、現在の導線から到達しない障害は現在作業へ持ち込まない。PLANに記載がなくても現在の契約を明白に破る場合はblockerにできるが、より良い設計という理由だけでは止めない。

共通手順の工程3で採否を統合し、既存のledgerとPLANの範囲内で直せる`fix-here`だけを工程4で一括修正する。code、PLAN、ledgerのどれを正とするかで契約判断が必要な不一致は、都合のよい一つへ合わせず4.2の停止条件としてuserへ報告する。

Gate判定前に、全条件を「実装済み」「実装済み・Journey／実service待ち」「未実装」「契約判断待ち」の4つへ根拠付きで分類する。前2分類だけになり、共通手順の工程5を通過し、未解決blockerがない場合に限ってGateを通す。`未実装`は`doing`のまま実装を続け、`契約判断待ち`は4.2に従って停止する。

このGateはcode・testと契約の整合を確認するもので、実画面Journey、実service、目視品質、費用を伴う検証の代用ではない。Gate通過後、codeと必要な自動testが成立した状態を`implemented`とする。自動testとレビューの成功だけで`verified`にしない。

Gate通過後に、review対象だった実装成果物、外部構成・状態、PLAN／ledgerの契約を意味的に変更した場合は、その変更で成立可否が変わり得るaffected closureのGateを失効させる。実装成果物にはcode、test、設定、schema／migration、dependency、content、prompt、静的・生成asset、deploy済み外部設定を含む。変更箇所とaffected closureをReview Briefへ反映し、共通手順の工程1からやり直してから関係するJourneyだけを再開する。別Storyや後続Gateまで全面reviewへ戻さず、最終変更後レビューを通らないまま`implemented`または`verified`へ進めない。

レビューとJourneyの実結果を契約どおり記録するだけの状態遷移、条件checkbox、検証欄、証拠link、PLANの進捗checkbox・結果ログはGateを失効させない。ただし、未確認結果を完了扱いする変更や、記録に見せかけて契約の意味を変える更新は失効対象とする。

## 6. Journeyを検証する

Journeyは新しい要件や改善案を探索するreviewではなく、固定済み条件の具体例を実環境で観測する工程とする。恒久的なverification briefは作らない。検証前に`/tmp`または実行中PLANへ、対象USに必要な次の項目だけを固定する。

- 開始状態と利用者の目的
- normal pathと完了点
- 中間の判断・状態遷移
- exception、failure、cancel、retry、staleのうち対象となるもの
- reload、再起動、Back、再訪のうち対象となるもの
- keyboard、狭幅、アクセシビリティのうち対象となるもの
- 外部サービス、費用、権限、必要な証拠

UIを含むUSは通常入口から実画面で確認する。外部サービスや課金が受け入れ条件に含まれる場合は、利用者の明示承認後に実行する。未実施の検証をmockやfixtureで代替して完了扱いにしない。

Journeyでは固定した条件IDと`例:`ごとに、開始状態、操作、実際の観測結果、成功／失敗、未実施理由だけを判定する。固定した条件と異なる結果はその条件の失敗として扱う。途中で見つけた改善案、現在の条件から到達しない例外、別の利用者成果は現在のJourneyや後続taskへ追加しない。実結果から既存契約が実現不能と判明した場合だけ4.2の`契約判断待ち`へ戻す。

## 7. 状態と証拠を更新する

- 状態と証拠の更新はreviewではなく、固定済み条件と実際の検証結果を対応付ける記録工程とする。ここで新しい品質条件を追加しない。
- 全受け入れ条件を必要な検証水準で確認した場合だけ`verified`へ変更する。
- 条件をチェックする際は、その条件の`例:`を実際に確認したかで判断する。まとめて確認した印象でチェックしない。
- 自動テストだけで十分なUSは、その根拠を検証欄へ記録する。
- 実サービス、目視品質判断、費用、外部job、重要な失敗復旧を扱った場合は、ledgerと同じscopeの`EVIDENCE/_TEMPLATE.md`から証拠を作る。
- 証拠名は`EVIDENCE/YYMMDD_US-XX_{slug}.md`とし、成果物本体や秘密情報を文書へ埋め込まない。
- 実装後レビューで`未実装`と分類された条件があれば`doing`を維持する。全実装は成立しJourney／実serviceだけが未確認なら`implemented`、外部条件により進められない場合だけ`blocked`とし、検証の`未確認条件`へ条件IDを列挙する。

最後に次を実行する。

```bash
python3 .codex/skills/dev/develop-user-story/scripts/validate_story_ledger.py <resolved-ledger-path>
```

validatorは台帳の構文、条件ID、具体例、未確認条件、PLAN／EVIDENCE参照、EVIDENCE metadataを検査する。失敗した場合は、報告された台帳またはPLAN／EVIDENCEを修正して再実行する。検査を通すために条件IDを採番し直したり、未確認の条件をチェック済みにしたりしない。

完了報告では、対象US、到達状態、主要検証、証拠、未完了条件を短く示す。
