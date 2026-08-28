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
- **レビュー**: PR内の担当Story／Gateごとに判定質問を分け、成立可否に影響する範囲を探索する。指摘候補の採否と振り分け先を決める。意味を変更した別のStory／PLANは同じGateへ混ぜず、別のGateとして判定する。
- **検証**: 受け入れ条件ごとに自動テスト、実画面、外部サービス、復旧・再読込の必要性を判定して確認する。

ストーリーの追加・実装・検証で対象USが指定されていない場合は、依頼内容と台帳の優先度から一件に絞る。複数のUSを同じ実装範囲へ含めてよいのは、一つの利用者成果として分離できない場合だけである。

ただし、残る対象範囲全体のPLAN化、実行順の整理、並列可能なPLAN設計を求められた場合は、複数のUSを計画の入力にしてよい。この場合もUS同士を結合せず、条件ID単位の追跡を維持する。

ストーリーを新規作成した場合や、利用者から見える契約を意味的に変更した場合は、次工程へ進む前に3.1の独立レビューを通す。ここでいう契約には、タイトル、`きっかけ`、活動、目的、対象範囲、導線、受け入れ条件を含む。

PLANまたはplan setの実装・検証契約を作成した場合や、その意味を変更した場合は、4.1の独立レビューを通す。一方、進捗、実行担当、session、証拠へのlink、結果記録、誤字、書式だけの更新では、新しいGateを発生させない。

意味を変更した場合は、変更した条件ID、公開される状態・出力、依存から、担当Story／Gateの成立可否に影響する範囲をレビューする。別のStoryや後続Gateへは広げない。

## 出力文書の読みやすさ

このskillで新規作成または更新するストーリー台帳、PLAN、EVIDENCEなどの永続文書は、日本語で一読できる構造にする。短さを優先して必要な情報を削らない。

- 固有名詞、コード識別子、command、path、schema field、運用ラベルはそのまま使ってよい。それ以外の説明では不要な英単語を避け、同じ概念には同じ言葉を使う。
- 前提、判断、操作、例外、完了条件を一文へ詰め込まない。必要に応じて文や段落を分け、長い列挙や対応関係は箇条書きまたは表にする。
- 各節は目的または結論から始め、読み手が「何をするか」「なぜ必要か」「いつ完了か」を順に追える構成にする。
- 読みやすさのために、条件ID、Gate、責務、検証基準、停止条件、pathなど、実行や合否に必要な契約を省略・弱体化しない。既存templateやvalidatorの書式も保つ。

## 独立レビューの共通基盤

Story、PLAN、実装成果の独立レビューでは`$review-gate`を使う。確認範囲の作成、指摘を探索から隔離する方法、探索終了の証明、候補の採否、修正後の再確認、GO／NO-GOは同skillを正本とし、ここへ重複記載しない。

このskillが所有するのは、各Gateについて次を渡し、結果を開発状態へ反映することである。

- Gate固有の判定質問、条件ID、対象成果、通常導線と例外導線
- Story／PLAN／実装に固有の一次情報と、適用性を判断する候補
- 作成者、実装者、過去のレビュー担当との役割分離
- `later-gate`を`plan-input`、`implementation-risk`、`journey-risk`へ振り分ける規則
- Gate通過、失効、再開、`implemented`、`verified`の状態遷移

`plan-input`はStoryが成立し、PLANで実装・検証方法を決める項目に使う。`implementation-risk`はPLANが固定済みで、コードまたは自動検証が所有する名前付きGateとownerへhandoffする項目に使う。`journey-risk`は実装契約が成立し、実画面、実サービス、目視品質、費用を伴う確認だけが残る項目に使う。

`契約判断待ち`にできるのは、現在のGateに適用される既存契約同士が衝突し、どちらを正とするか決めないとGate質問へ答えられない場合だけである。名前付きの後工程、owner、handoff契約を示せない将来用途、改善案、一般的なhardeningは`非適用`とし、曖昧な後続作業やblockerへ送らない。

`$review-gate`は、レビュー確認一覧、指摘候補、再確認する単位を決める。このskillは、その結果から失効するStory／PLAN／実装Gateと、再通過する順序、Journey、状態を決める。

main Codexは、Review Briefより先にReview Inputを作る。`condition_ids`はBriefから逆算せず、次の順で決める。

1. 依頼本文から、対象Story／Gate／PLAN setを固定する。
2. 解決した`docs/USER_STORIES.md`から、対象Storyの条件IDを直接抽出する。
3. PLANを対象とする場合は、対象PLAN setが宣言する条件IDも別に抽出し、台帳に存在するか照合する。candidate PLANならその担当ID、Story完了を所有する統合PLANなら台帳の対象ID全件が正確な集合になる。
4. Story Gateでは台帳から抽出した対象ID、PLAN／実装Gateでは上の照合で確定したPLAN担当IDを、Review Inputの`condition_ids`に過不足なく渡す。

`current_contracts`、`handoffs`、`scope_seeds`も、依頼、台帳、PLAN、Gate質問からBriefとは独立に固定する。handoffには`id`、`gate`、`owner`、`contract`を持たせる。seedには`id`、`kind`、`source`、`contract`、`coverage_obligation`、`review_case_ids`を持たせ、condition seedには`condition_id`、handoff seedには`handoff_id`も付ける。

各対象条件IDはcondition seedで1回だけ所有させ、確認case IDは全seedを通じて一意にする。異なる到達経路は別のcase IDに分ける。Review BriefはReview Inputの契約、handoff、seed、caseのID集合と意味fieldをそのまま持ち、Brief側で追加、削除、改名、owner変更をしない。

main CodexはReview Briefを作る前に、Review Inputの全fieldを一次情報と照合する。これを正本照合Gateとする。validatorはReview InputとBriefの構造上の一致を確認できるが、Review Inputが台帳やPLANに意味上忠実かは判定できない。正本照合Gateとvalidator成功の両方がなければ、Review Inputが完全とは主張しない。

reviewerが不足を見つけた場合は自分で追加させず、mainが一次情報からReview InputとBriefを再固定する。revision 1ではReview Inputの`previous_brief_digest`を`null`、Briefの`review_case_migrations`を必ず`[]`とする。

Briefの意味を変える場合はrevisionを更新する。直前Briefを保持し、validatorが成功時に出力したそのcanonical JSON SHA-256をReview Inputの`previous_brief_digest`へ入れる。さらに、直前Briefの全caseを改名、分割、統合、追加、廃止、owner変更の理由付きで新Briefへ完全に対応付ける。ownerにはseedのID、kind、source、contract、coverage obligation、condition ID、handoff IDと、handoff seedに紐づくGate、owner、contractを含む。旧caseを黙って消さない。

同じBrief revisionでのscope再確定だけ、直前のscope baselineと必要な観測checkpointを使う。新経路に新caseが必要な場合は、同revisionでcaseを複製せずBrief revisionを更新する。Brief revisionを変えた場合は、scope、discovery、candidateを作り直し、前revisionの探索状態や証拠を再利用しない。candidate stageへscopeや探索結果を直接追加・変更しない。

main Codexは同じReview Inputを`--review-input`でscope／discovery／candidateの全validatorへ渡し、validatorを自身で実行する。Brief revision 2以降では、`previous_brief_digest`と一致する実際の直前Briefも全stageへ渡す。`$review-gate`の適用範囲Gate、探索完了Gate、指摘採用Gateの完了証明と三stageの成功が揃わないレビュー結果を受理しない。reviewerの自己申告やvalidator成功は、mainの正本照合Gateの代わりにしない。不足する結果は`HOLD`として扱い、指摘、修正、後工程、状態更新へ使わない。一件のblockerでNO-GO見込みになっても、探索完了Gateが通るまで修正指示や最終報告を出さない。

Review Input、Brief、manifest、checkpoint、digestは一時成果物とし、台帳、PLAN、EVIDENCEへ保存しない。branch、commit SHA、worktreeやsessionの識別子も入れない。恒久レビュー報告は依頼者が求めた場合だけ作るが、`previous_brief_digest`を永続文書へ移さない。

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

ストーリーをPLANや実装の入力として固定する前に、作成者とは別のエージェントを1名以上立ち上げ、`$review-gate`でレビューする。このGateの判定質問は、「PLANの入力として、利用者成果と合否が確定しているか」とする。

次の項目の適用性を判定し、適用されたものだけを監査する。

- `きっかけ`、活動、目的、対象範囲が、利用者側の一つの成果としてつながっているか。機能やPLANから逆算されていないか
- 各条件が一つの状況、操作、観測結果に分かれているか。具体例で合否を判定でき、目的と対象範囲を過不足なく覆っているか
- 明示された通常導線と例外導線に、利用者が観測する完了、失敗、保持、再試行の結果があるか
- 取消可能な操作では取消、状態を保持する契約では再読込／復元、利用者・領域を切り替える機能では切替の条件が欠けていないか
- 権限、プライバシー、外部状態、費用が利用者の操作結果を変える場合、その境界が観測可能な条件になっているか
- 同じ名前付き契約、全体不変条件、またはhandoffを共有する関連ストーリーとの重複、矛盾、順序依存、責務の隙間、対象外へ追い出した必須成果がないか

このGateで`fix-here`にできるのは、成果の混在、対象範囲の矛盾、観測できない条件、明示された導線の欠落、関連ストーリーとの契約衝突に限る。

API方式、保存方式、account固定、idempotency、upload手順、TOCTOU、内部retry、細かな障害分類などは実装機構である。初回のStory Gateでは、固定した利用者成果を実現するためにPLANで判断が必要な項目だけを`plan-input`へ送る。既存Storyの再レビューで、すでに固定されたPLAN、名前付き実装Gate、owner、handoff契約がすべて存在する場合だけ`implementation-risk`へ送ってよい。それ以外は`非適用`とする。技術上のリスクを理由に、利用者成果を増やしたり、別ストーリーへ分割したりしない。

main Codexは、`fix-here`だけをストーリー台帳へ反映する。後工程へ送る項目は受け入れ条件に追加せず、Review BriefまたはPLAN作成時の入力として引き継ぐ。その後、`$review-gate`の終了条件に従ってGateを閉じる。

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
- 複数の実行PLANの開始、並行lane、merge／Join Gate、external成果へのhandoffを所有するintegration／coordination PLANには、Mermaidの実行DAGと機械可読なParallelization Topology Gate manifestを必須とする。別のREADMEや進行PLANへのlink、文章だけの順序、PLAN一覧表だけでは代替しない。図には開始Gate、hard dependency、並行可能な分岐、merge point、条件付きfallback、外部停止Gate、最終Joinを示し、本文の開始条件・Gate・ownerと同じ名前で照合できるようにする。
- 対象USの受け入れ条件が確定してからPLANを作る。PLANの都合で条件を足したり弱めたりしない。
- 対象USと受け入れ条件をPLANから追跡可能にする。条件IDで参照する。
- Goal、制約、対象外、Phaseの完了状態、Gate、検証commandを実装前に固定する。
- ストーリーの導線と現在のrepositoryから、実際に到達する外部作用、権限、費用、永続状態、共有ownerをrisk triggerとして特定する。Gateと検証はそのtriggerへ対応させ、一般的なrisk一覧をPLANへ展開しない。
- 実装詳細や進捗ログをストーリー台帳へ書かず、PLANへ記録する。
- 有料サービス、実生成、deploy、外部データ変更などは明示承認を得るまで未完了にする。
- 実装中に契約変更が必要になった場合は、コードで迂回せずUSとPLANを先に見直す。

### 4.05 Parallelization Topology Gate

複数の実行PLANを作成または再編した場合は、4.1へ進む前に、integration／coordination PLANへ[並列実行可能なPLAN設計](references/parallel-plan-execution.md)のmanifestを置く。全実行lane、排他的write scope、外部状態、依存edge、最早waveを記録し、次を実行する。

```bash
python3 .codex/skills/dev/develop-user-story/scripts/validate_plan_topology.py <integration-or-coordination-plan>
```

同じfileや外部状態を必要とする事実は直列化の結論ではなく、このGateへ戻る入力である。`write scope縮小 -> 最小shared seamの先行固定 -> Join-only化 -> 真のhard dependency -> serialized exception`の順に検討する。shared seamの抽出自体が独立contract、local oracle、handoff、並行化利益を持たなければYAGNIに従い採用しない。writer重複を残すserialized exceptionは、critical pathへの影響と、scope縮小・shared seam・Join-onlyを採用しない理由をmanifestへ記録する。

Gateは、validator成功に加え、4.1の独立reviewerが全laneの記載漏れ、各edgeの必要性、manifest・Mermaid・本文の一致、並行化利益を現在のsource／ownerから確認したときだけPASSとする。validator成功だけ、作成者のcheckbox、`同じfileなので直列`という説明だけではPASSにしない。FAILまたは未確認なら実装を開始しない。

laneの追加・削除、write scope・外部状態・依存・shared contract・ownerの意味変更、直列edgeの追加、実装中に未記載の共有writerが判明した場合は本Gateと4.1を再開する。未分類のowner競合が判明した時点でproduction code編集を止め、manifest、DAG、影響PLANを先に更新する。進捗状態だけが変わりtopologyが同じ場合は再開しない。

### 4.1 PLAN独立レビューGate

PLANを実装の入力として固定する前に、作成者ともストーリーレビュー担当とも異なるエージェントを、1名以上立ち上げる。そのエージェントが、`$review-gate`でPLANをレビューする。

このGateの判定質問は、「別の実装者が、利用者契約を変えずに実装し、完了を再現可能な方法で検証できるか」とする。

レビュー担当には、次を一次情報として渡す。

- レビュー済みのストーリー台帳、PLAN template、対象PLAN
- 関連する実装、テスト、設計資料
- 再利用判定に使った、materialize済みsourceの採用候補
- 候補の利用側または統合点、関連テスト
- 調査対象外とした候補と、sourceを読めるかどうかに依存しない除外理由
- 複数PLANの場合はParallelization Topology Gate manifest、validator成功出力、Mermaid DAG、全実行PLANのwrite scope／外部状態

要約資料や、作成者が選んだ一つのファイルだけに入力を狭めない。作成者の採否結論も前提にしない。利用側が存在する選定capabilityは、検証の判定基準から利用側までの連鎖を少なくとも1本、独立に辿る。利用側が存在しない選定capabilityは、探索範囲、検索結果、適用先側の判定基準を独立に確認する。

複数のPLANを同時に作成または再編した場合は、進行PLANとすべての実行PLANを一つのplan setとして扱う。同じレビュー担当がplan set全体を横断して確認する。ファイルごとに別のGateを繰り返さず、依存関係とhandoffを含むplan set全体が固定された時点で、一度だけGateを通す。

次の項目の適用性を判定し、適用されたものだけを監査する。

- 全条件IDと各`例:`を、Phase、Gate、検証まで追跡できるか。PLANがストーリーを弱めたり、未確認の条件を完了扱いしたりしていないか
- 開始条件、依存関係、実装順、停止Gate、対象外が、現在のリポジトリ状態と整合しているか。実装者が新たな契約判断をせずに開始できるか
- 複数PLANの場合は、Topology Gate validatorが成功しているか。manifestに全laneがあり、閉路や不要な直列待ちがないか。同じファイル、generated file、lockfile、台帳、EVIDENCE、外部状態に同一waveの複数writerがいないか。各直列edgeは現在のsource／contract上のhard dependencyか。writer重複を残す例外はscope縮小、shared seam、Join-onlyを具体的に反証しているか。handoffを受ける統合担当が、同じレビュー済み契約と開始Gateで成果を検証できるか
- integration／coordination PLANの場合は、Mermaid DAGをrenderできるか。DAGが本文と同じ開始Gate、依存、並行lane、統合／Join Gate、fallback、外部停止Gate、最終担当を表しているか
- ストーリー台帳または既存実装で同じ契約を通ると確認できたroute、API、server function、background処理、session、cache、保存先が、実装責務と検証から漏れていないか
- projectが再利用候補を示す場合は、合理的な候補の固定sourceをmaterializeしているか。存在する最小capabilityの利用側、統合点、テスト、またはそれらが存在しないことを探索範囲付きで確認しているか。直接利用、部分copy、再実装を比較し、より狭く契約に適合する採用単位を見落としていないか
- materializeしていない候補を、sourceを読めないことだけで除外していないか。製品、root、engine全体の不適合だけを理由に、より小さな再利用候補まで除外していないか
- ストーリーで明示された通常導線と例外導線について、必要な実装責務と、再現可能な検証基準があるか
- テスト、typecheck、build、実画面Journey、実サービス、証拠を、適用されるリスク要因に応じて使い分けているか。mockや静的文字列一致で、必要な実検証を代用していないか
- 現在の導線が外部変更、課金、秘密情報、個人情報、破壊的変更を扱う場合は、その直前のGate、承認、停止条件、rollbackまたは安全な失敗状態があるか

このGateで`fix-here`にできるのは、次の問題に限る。

- 条件の追跡漏れ
- 現在のリポジトリでは実行できない開始条件
- 担当の衝突
- 未承認の外部作用
- 検証基準の欠落
- 採否の根拠にするsourceがmaterializeされていない
- 存在するとされた利用側またはテストを読めない
- 本文とDAGの契約が矛盾している

利用側またはテストが存在しない候補は、探索範囲と、それらが存在しないことを記録する。適用先側のparity／negative判定基準をPLANの検証基準として定められるなら、未確認扱いにしない。

関数構造、内部errorの分類、一般的な堅牢化、将来規模への対応、現在の導線から到達しない障害、別のUSの改善は、現在のPLANレビューの指摘や追加作業にしない。PLANレビュー担当は、新しい受け入れ条件を作らない。PLANで現在のストーリーを実現できない場合だけ、`契約判断待ち`として返す。

main Codexは、`fix-here`だけをPLANへ反映する。全条件を追跡できることを確認し、`$review-gate`の終了条件に従ってGateを閉じる。ストーリーレビュー担当とPLANレビュー担当は兼任させない。

### 4.2 PLANを完遂する

userが実行PLANに従った全実装を求めた場合は、そのPLAN全体だけを現在taskのscopeとする。進行PLANは実装scopeにせず、開始可能な実行PLANの選択、依存・状態・handoffの確認に使う。複数PLANではParallelization Topology Gateと4.1がPASSであることを最初に確認する。複数PLANを並行実行するときは、各laneのwrite scope、port、生成物、外部状態を衝突させない実行contextを計画外で割り当てる。同じcontextで直列実行できる場合は不要な分離を要求しない。最初の未完了項目から依存順に進め、各PhaseとGate、担当するJourney、証拠、handoffまで、未完了項目がなくなるか次の停止条件に当たるまで継続する。PhaseやGateを一つ終えたこと、作業量が多いこと、通常のテスト失敗や実装上の難しさだけを理由にuserへ返さない。

最初のtestまたはproduction codeを編集する前に、PLANで採用した候補、または契約・algorithmの根拠として実際に使う候補だけを再確認する。同一repository内候補はcurrent path、baseline、公開contract、関連testを、外部候補は参照sourceのpathとprovenance記録にある固定revision／versionとの一致を現在contextで一度確認する。manifest等がhidden pathを示す場合は明示pathまたはhidden探索を使い、素の全体検索の不一致をsource不存在扱いしない。どちらも存在すると記録したconsumer／testを辿り、再利用分類の前提が現行repositoryと一致することを確認する。consumer／testが存在しないと記録した候補では、その探索範囲と適用先側oracleを確認する。不採用候補は、除外根拠が変わった場合だけ4.0へ戻して再確認する。通常の実装不具合ごとに探索を繰り返さない。ただし、実画面・実service・実media等の観測が選定時のplatform／runtime前提を反証した場合、またはPLANにないclock、scheduler、queue、retry、resource lifecycle、serialization等の仕組みを独自実装しないと修正できないと判明した場合は、次の局所patch前に4.0の該当capabilityだけを再確認する。

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

PLAN内の実装項目と通常の自動検証が完了したら、実装後独立レビューGateを行う。実施時期は、`implemented`への更新や、最初の実画面Journey・実サービス検証より前である。実装者、ストーリーレビュー担当、PLANレビュー担当のいずれとも異なるエージェントを、1名以上立ち上げる。

このGateは、原則としてPLAN全体に対して1回だけ行う。追加の中間レビューを設けてよいのは、PLANが到達可能な高リスク境界と、その境界での判定質問を明示している場合だけである。既存PLANにこのGateがない場合や、GateがJourneyや状態更新より後ろに書かれている場合も、実装と自動検証の直後に行う順序を優先する。

このGateの判定質問は、「現在の変更と自動検証は、ストーリー台帳とPLANを満たしており、未実装を隠さずJourneyへ進めるか」とする。`$review-gate`を使い、レビュー済みのストーリー台帳とPLAN、実際のコード・テスト・設定、現在の変更、検証結果を一次情報として照合する。

次の項目の適用性を判定し、適用されたものだけを監査する。

- コードとテストは、担当する全条件IDと各`例:`で観測できる振る舞いを満たしているか。Journeyまたは実サービスの確認待ちと、未実装を混同していないか
- コード、テスト、設定、実際に変更または利用した公開インターフェースは、PLANの実装責務、制約、対象外、Gateと一致しているか。完了済みの項目には、実証できる根拠があるか
- PLANから漏れた受け入れ条件、実装都合の迂回、条件の弱体化、未確認の結果を成功扱いするfallbackがないか
- ストーリーとPLANに適用される通常導線、失敗、拒否、取消、再試行、再読込、復元、状態遷移、利用者・領域切替が、該当するコードと振る舞いのテストへ反映されているか
- `$review-gate`のレビュー確認一覧と、変更の性質に応じて選んだ確認方法に未確認の対象がないか。外部から渡された処理や共有リソースへの作用を含め、生成側と利用側の契約がfield単位で一致しているか
- テストは、公開インターフェースと再発条件を確認しているか。内部実装や静的文言だけを固定したり、未確認の実画面・実サービス結果を代用したりしていないか
- 現在の変更から到達できる範囲に、PLANにない外部副作用、未承認の費用、秘密情報・個人情報の露出、不要な依存、既存契約を破る性能退行がないか

このGateで`fix-here`にできるのは、担当条件または現在のGateを破る、再現可能な問題に限る。具体的には、契約違反、実装責務の欠落、誤った完了主張、到達可能な副作用、秘密情報の露出、回帰が該当する。

変更された行や優先度だけで、レビュー範囲を決めない。一方、新しい受け入れ条件、別のアーキテクチャ、一般的な堅牢化、将来規模への対応、現在の導線から到達しない障害は、現在の作業へ持ち込まない。PLANに書かれていなくても、現在の契約を明らかに破る問題はblockerにできる。ただし、「より良い設計にできる」という理由だけではGateを止めない。

`$review-gate`の適用範囲Gate、探索完了Gate、指摘採用Gateを順に通してから候補を統合する。既存のストーリー台帳とPLANの範囲内で直せる`fix-here`だけを、根本原因ごとに一括修正する。コード、PLAN、ストーリー台帳のどれを正とするかについて、現在の既存契約同士が衝突する不一致は、都合のよい一つへ合わせない。4.2の停止条件としてuserへ報告する。

Gateを判定する前に、全条件を「実装済み」「実装済み・Journey／実サービス待ち」「未実装」「契約判断待ち」の4種類に、根拠付きで分類する。

すべての条件が前2種類のどちらかになり、`$review-gate`による最終成果の確認を通過し、未解決のblockerもない場合に限ってGateを通す。`未実装`があれば`doing`のまま実装を続ける。`契約判断待ち`があれば4.2に従って停止する。

このGateで確認するのは、コード・テストと契約の整合である。実画面Journey、実サービス、目視品質、費用を伴う検証の代わりにはならない。Gate通過後、コードと必要な自動テストが成立した状態を`implemented`とする。自動テストとレビューが成功しただけでは`verified`にしない。

Gate通過後に、レビュー対象だった実装成果物、外部構成・状態、PLANまたはストーリー台帳の契約を意味的に変更した場合は、その変更の影響範囲にあるGateを失効させる。実装成果物には、コード、テスト、設定、schema／migration、依存、コンテンツ、prompt、静的・生成アセット、デプロイ済みの外部設定を含む。

変更後は、まず台帳とPLANからReview Inputの条件ID、現在契約、handoff、seed、caseを再導出し、正本照合Gateを再実行する。保持した直前Briefに対するvalidator出力のdigestをReview Inputへ入れ、同じ`review_id`のBrief revisionを更新する。直前Briefの全caseを新Briefへ完全に対応付けた後、scope、discovery、candidateを新Briefから作り直す。前revisionの状態、証拠、reviewer完了を引き継がない。

再レビュー後は、関係するJourneyだけを再開する。別のStoryや後続Gateまで、全面的な再レビューの対象にはしない。ただし、最終変更後のレビューを通らないまま`implemented`または`verified`へ進めてはならない。

レビューとJourneyの実結果を契約どおり記録するだけなら、Gateは失効しない。これには、状態の更新、条件のチェック欄、検証欄、証拠へのlink、PLANの進捗チェック欄、結果ログが含まれる。ただし、未確認の結果を完了扱いする変更や、記録に見せかけて契約の意味を変える更新は、失効対象とする。

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
