---
name: develop-user-story
description: repository直下またはproject-localのユーザーストーリー台帳を製品契約の正本として、ストーリーの追加・精緻化、関連PLANの作成・実行、TDD実装、Journey検証、証拠記録、状態更新を一貫して行う。Use when adding or refining a user story, planning or implementing work identified by a US ID, resuming its development, or verifying whether its acceptance criteria are genuinely complete.
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
- **検証**: 受け入れ条件ごとに自動テスト、実画面、外部サービス、復旧・再読込の必要性を判定して確認する。

ストーリーの追加・実装・検証で対象USが指定されていない場合は、依頼内容と台帳の優先度から一件に絞る。複数USを同じ実装scopeに入れるのは、一つの利用者成果として分離不能な場合だけにする。ただし、残scope全体のPLAN化、実行順の整理、並列可能なPLAN設計を求められた計画操作では、複数USを計画入力としてよい。この場合もUSを結合せず、条件ID単位の追跡を維持する。

ストーリーを新規作成または利用者契約を意味的に変える精緻化（例: タイトル、`きっかけ`、活動、目的、scope、導線、条件）をした場合は3.1、PLANまたは複数PLANの進行契約を作成・意味的に更新（例: Goal、scope、制約、対象外、条件追跡、依存、開始条件、実装順、実装責務、write scope、handoff、統合owner、検証oracle、rollback、Gate、完了条件）した場合は4.1の独立レビューを、次工程へ進む前に必ず通す。

## 独立レビュー共通規則

レビュー担当は作成過程を継承しない新規contextで起動する。sub-agentを使う場合は`fork_turns: none`相当とし、適用される指示、一次情報、対象artifact、関連artifact、判断に必要な既存実装だけを明示的に渡す。作成者の会話履歴、結論、想定する正解、懸念点の一覧を渡して追認させない。

レビュー担当は共有fileを編集せず、指摘ごとに重要度、根拠、破綻する具体的scenario、最小修正案を返す。指摘がない場合も、確認した一次情報、監査項目ごとの判断、反証した代表scenario、残余riskを返す。「問題なし」だけの回答や監査項目を省略した回答はGate通過に使わず、同じ担当へ不足分を再依頼する。

main Codexは各指摘を採用または理由付きで棄却する。指摘の採用によりartifactを意味的に変更した場合は、変更項目を問わず同じ担当へ差分を再確認させる。誤字とformatだけの修正は再確認不要とする。重大指摘を棄却する場合は根拠を同じ担当へ一度だけ再確認させ、担当が重大指摘を維持した場合はuser判断までGateを保留する。reviewerが解消または重大度低下に同意して、未解決の重大指摘がない状態をGate通過とする。

不足回答の補完、採用修正の差分確認、棄却理由の再確認を合わせ、同一Gateでreviewerへ自動follow-upするのは2回までとする。上限後も必須の回答形式を満たさないか重大指摘が残る場合は、Gateを通さずuserへ判断を求める。

独立エージェントを利用できない場合は自己レビューで代替せず、その事実をuserへ伝え、次工程へ進む前に判断を求める。レビュー報告用の恒久fileは、userが求めた場合だけ作る。

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
- 通常導線だけでなく、対象となる失敗、再試行、cancel、reload、復元を記載する。
- 共通ルールを各USへ複製しない。固有の条件だけを記載する。
- 着手前は`todo`、実行中は`doing`とする。外部条件により進められない場合だけ理由を添えて`blocked`とする。

受け入れ条件は次の形で書く。ここが弱いと、実装したものを追認するだけのレビューになる。

- 1条件は、1つの状況、1つの操作、1つの観測できる結果で書く。読点や「かつ」で複数操作を束ねた条件は分割する。
- 条件IDを`US-XX-01`形式で付け、末尾へ連番追加する。既存IDの意味を変えず、意味が変わる場合は新IDを追加する。
- 各条件へ`例:`を1つ以上付け、枚数、秒数、file名、model名、表示文言の要点など具体値を書く。具体例を書けない条件は、まだ合意できていないとみなす。
- 値が未確定なら`例: 未確定（決めるべき値）`と書き、その条件をチェックしない。値を推測で埋めない。
- 「成立する」「正しく」「適切に」「安全に」「うまく」「〜など」「〜等」を条件へ書かない。失敗したと客観的に言えない条件は条件ではない。
- 失敗、再試行、再生成、reloadの条件は、失敗の名前ではなく、利用者が見る内容と保持される対象で書く。
- 実装名、内部型、内部ID、file pathを条件へ書かない。それらはPLANが持つ。
- 受け入れ条件が10件を超えたら、複数の利用者成果が混ざっていないか確認して分割を検討する。

validatorが条件を追跡できるよう、条件行を`- [ ] \`US-XX-01\` ...`、具体例をその直下の`  - 例: ...`で記載する。検証の`未確認条件`は未チェック条件IDを過不足なく列挙し、残件がなければ`なし`と書く。PLAN／EVIDENCEから参照する条件IDは台帳に存在するものだけにする。

### 3.1 ストーリー独立レビューGate

ストーリーをPLANや実装の入力として固定する前に、作成者とは別のエージェントを1名以上立ち上げ、共通規則に従って少なくとも次を反証させる。

- `きっかけ`、活動、目的、対象範囲が利用者側の一つの成果としてつながり、機能やPLANから逆算されていないか
- 通常導線だけでなく、対象となる失敗、拒否、cancel、retry、reload、復元、利用者・領域の切替が欠けていないか
- 各条件が一つの状況・操作・観測結果に分かれ、具体例で合否を判定でき、目的・対象範囲を過不足なく覆うか
- 関連ストーリーとの重複、矛盾、順序依存、責務の隙間、対象外へ追い出した必須成果がないか
- 権限、privacy、外部状態、費用、複数利用者・複数領域など、このストーリー固有の失敗条件を落としていないか

main Codexは採用した指摘をledgerへ反映し、共通規則に従ってGateを閉じる。

## 4. PLANを作成・実行する

PLANが必要な場合は、ledgerと同じproject scopeにあるPLAN templateを使う。repository直下台帳では`docs/PLAN/_TEMPLATE.md`、project-local台帳では同階層の`_PLAN_TEMPLATE.md`を優先する。候補が複数または存在しない場合は独自形式を作る前に確認する。

- PLANの単位はUS、受け入れ条件の個数、技術layer、Phase、実行環境ではなく、独立してhandoffできる一つのmerge可能な成果で決める。checkout、branch、worktree、session、agentは実行時の割当であり、PLANの意味契約へ固定しない。
- 一つのUSを複数PLANへ写像してよく、一つのPLANが複数USの条件を扱ってもよい。candidate PLANは担当条件を実装してもUS完了を主張せず、統合・Journey・外部検証を所有するPLANが最終状態を更新する。
- 分割候補ごとに、明示した開始条件、排他的write scope、handoff成果、localで再現できる検証oracle、統合owner、並行化の実益があるかを確認する。一つでも成立しない候補は、別PLANにせず同じPLANのPhaseへ戻す。条件数が多いことだけを分割理由にしない。
- 複数PLANが必要と判断した場合は、[並列実行可能なPLAN設計](references/parallel-plan-execution.md)を読み、対象scopeの実行PLAN群と進行PLANを一度の計画操作で作る。一枚作るたびに次のUSや次のPLANをuserへ選ばせず、未確定の製品判断だけを質問する。
- 進行PLANは依存graph、直列／並列lane、各PLANの状態、baseline、merge順、統合・外部状態owner、次に開始可能なPLANを管理する。実行割当が必要なら任意・非契約の管理情報として記録し、PLANの再review理由にしない。実装taskやPhaseを個別PLANと重複記載しない。各実行PLANは自分のread／write scope、Goal、条件ID、開始Gate、handoff、focused検証、停止条件だけを自己完結して持つ。
- 複数の実行PLANの開始、並行lane、merge／Join Gate、external成果へのhandoffを所有するintegration／coordination PLANには、Mermaidの実行DAGを必須とする。別のREADMEや進行PLANへのlink、文章だけの順序、PLAN一覧表だけでは代替しない。図には現在baseline、hard dependency、並行可能な分岐、merge point、条件付きfallback、外部停止Gate、最終Joinを示し、本文の開始条件・Gate・ownerと同じ名前で照合できるようにする。
- 対象USの受け入れ条件が確定してからPLANを作る。PLANの都合で条件を足したり弱めたりしない。
- 対象USと受け入れ条件をPLANから追跡可能にする。条件IDで参照する。
- Goal、制約、対象外、Phaseの完了状態、Gate、検証commandを実装前に固定する。
- 実装詳細や進捗ログをストーリー台帳へ書かず、PLANへ記録する。
- 有料サービス、実生成、deploy、外部データ変更などは明示承認を得るまで未完了にする。
- 実装中に契約変更が必要になった場合は、コードで迂回せずUSとPLANを先に見直す。

### 4.1 PLAN独立レビューGate

PLANを実装の入力として固定する前に、ストーリーレビュー担当とも作成者とも別のエージェントを1名以上立ち上げ、共通規則に従って少なくとも次を反証させる。レビュー担当にはレビュー済みledger、PLAN template、PLAN、関連実装・テスト・設計資料を一次情報として渡す。複数PLANを同時作成・再編した場合は、進行PLANと全実行PLANを一つのplan setとして同じreviewerが横断reviewする。ファイルごとに別Gateを繰り返さず、依存graphとhandoffを含むplan set全体が固定された時点で一回通す。

- 全条件IDと各`例:`がPhase、Gate、検証へ追跡でき、PLANがストーリーを弱めたり未確認の条件を完了扱いしたりしていないか
- 開始条件、依存関係、実装順、停止Gate、対象外が実際のrepository状態と整合し、別PLANや将来機能との間に隙間がないか
- plan setに閉路、不要な直列待ち、同一file／generated file／lockfile／台帳／EVIDENCE／外部状態の複数ownerがなく、各candidateのhandoffを統合ownerが同じbaselineで検証できるか
- integration／coordination PLANのMermaid DAGがrender可能で、本文と同じbaseline、直列／並列lane、merge／Join Gate、fallback、外部session、最終ownerを表し、図と文章のどちらにも未記載のedgeがないか
- UI routeだけでなく、API、server function、background処理、session、cache、保存先など、同じ契約を通るsurfaceが保護・検証範囲から漏れていないか
- normal pathに加え、失敗、拒否、cancel、retry、reload、復元、利用者・領域切替の実装責務と検証oracleがあるか
- test、typecheck、build、実画面Journey、実service、証拠がリスクに応じて分かれ、mockや静的文字列一致を実検証の代用にしていないか
- 外部変更、課金、secret、個人情報、rollback、運用負荷、YAGNI上の過剰実装に対する境界があるか

main Codexは採用した指摘をPLANへ反映し、全条件を追跡できることを確認して共通規則に従ってGateを閉じる。ストーリーレビュー担当とPLANレビュー担当を兼任させない。

### 4.2 PLANを完遂する

userが実行PLANに従った全実装を求めた場合は、そのPLAN全体だけを現在taskのscopeとする。進行PLANは実装scopeにせず、開始可能な実行PLANの選択、依存・状態・handoffの確認に使う。複数PLANを並行実行するときは、各laneのwrite scope、port、生成物、外部状態を衝突させない独立した実行contextへ割り当てる。実行contextには別agent／session、branch、worktreeなどを選べるが、どれもPLANの前提ではない。同じcontextで直列実行できる場合は不要な分離を要求しない。最初の未完了項目から依存順に進め、各PhaseとGate、担当するJourney、証拠、handoffまで、未完了項目がなくなるか次の停止条件に当たるまで継続する。PhaseやGateを一つ終えたこと、作業量が多いこと、通常のテスト失敗や実装上の難しさだけを理由にuserへ返さない。

PLAN内のscopeと権限で安全に解決できる失敗は、原因を調査し、必要な修正と検証を行って続行する。次のいずれかでは、迂回実装や暗黙の契約変更を行う前に停止する。

- ledger、PLAN、適用指示、実repository、外部仕様が衝突し、Goal、scope、受け入れ条件、実装・検証契約の意味変更が必要になる
- 続行に未承認の外部変更、課金、秘密情報、破壊的・不可逆な操作、userだけが決められる製品判断が必要になる
- 必須のdependency、credential、外部状態が利用できず、安全な範囲の確認とPLAN内の代替手段を尽くしても先へ進めない
- PLANが要求する検証oracleを成立させられず、条件を弱める、testを外す、未確認結果を完了扱いする以外に通過方法がない

停止時は、受け入れ条件やGateを弱めず、隠れたfallbackや別仕様で通したことにしない。完了を実証した項目だけをcheckedにし、停止したPLAN項目／Gate、衝突の証拠、安全に試した解決、続行に必要な承認・判断または契約変更、完了済みと未完了の範囲をuserへ報告する。仕様変更が必要な場合は最小の変更案を示すが、userの判断前にledgerやPLANへ反映しない。

## 5. TDDで実装する

1. 対象の条件IDまたは再発防止したい失敗を表すテストを先に追加し、意図した理由で失敗することを確認する。条件へ書いた`例:`をそのままテストの入力と期待値にする。
2. 現在の契約を成立させる最小限の実装を行う。
3. focused testから上位のtypecheck、build、統合テストへ検証範囲を広げる。
4. 見落とし、反例、状態遷移、失敗時のデータ保持、隠れた外部コストを点検する。

### 5.1 実装後独立レビューGate

PLAN内の実装項目と通常の自動検証が完了した後、`implemented`への更新と最初の実画面Journey・実service検証の前に、実装者、ストーリーレビュー担当、PLANレビュー担当のいずれとも別のエージェントを1名以上立ち上げる。既定ではPLAN全体に対してこのGateを1回行い、PLANが高riskな中間レビューを明示した場合だけ追加する。既存PLANにこのGateがないか、Journey・実service・`implemented`／`verified`更新より後ろに書かれていても、この順序を優先して実装・自動検証の直後へ割り込ませる。レビュー担当は共通規則の新規contextで、レビュー済みledgerとPLAN、実際のcode・test・設定、diff、検証結果を一次情報として三者照合する。

レビュー担当には少なくとも次を反証させる。

- codeとtestが、全受け入れ条件IDと各`例:`の観測可能な振る舞いを満たすか。自動検証では確認できずJourneyまたは実service待ちの条件と、未実装の条件を混同していないか
- code、test、設定、route、API、server function、background処理、保存先が、PLANの実装責務・制約・対象外・Gateと一致し、checked項目に実証可能な根拠があるか
- PLANから漏れた受け入れ条件、PLANどおりでも利用者目的を満たさない実装、実装都合の迂回、条件の弱体化、隠れたfallbackがないか
- normal pathだけでなく、対象となるfailure、reject、cancel、retry、reload、復元、状態遷移、利用者・領域切替がcodeとbehavior testへ反映されているか
- testが公開interfaceと再発条件を確認し、内部実装や静的文言だけを固定していないか。未確認の実画面・実service結果をtestで代替していないか
- 計画外の外部副作用、secret・個人情報の露出、不要なdependency、将来機能の先回り、運用・performance costを持ち込んでいないか

既存のledgerとPLANの範囲内で直せる指摘はmain Codexが実装・test・進捗へ反映し、同じ担当へ差分を再確認させる。code、PLAN、ledgerのどれを正とするかで契約判断が必要な不一致は、都合のよい一つへ合わせず4.2の停止条件としてuserへ報告する。全条件を「実装済み」「実装済み・Journey／実service待ち」「未実装」「契約判断待ち」の4つへ根拠付きで分類する。前2分類だけになり、未解決の重大指摘がない場合に限ってGateを通す。`未実装`は`doing`のまま実装を続け、`契約判断待ち`は4.2に従って停止する。

このGateはcode・testと契約の整合を確認するもので、実画面Journey、実service、目視品質、費用を伴う検証の代用ではない。Gate通過後、codeと必要な自動testが成立した状態を`implemented`とする。自動testとレビューの成功だけで`verified`にしない。

Gate通過後に、review対象だった実装成果物または外部構成・状態を変更するか、PLAN／ledgerのGoal、scope、受け入れ条件、実装・検証契約を意味的に変更した場合は、原因を問わず実装後レビューGateを失効させる。実装成果物にはcode、test、設定、schema／migration、dependency、content、prompt、静的・生成asset、deploy済み外部設定を含む。同じ担当による最終差分レビューと影響を受ける自動検証を通してからJourneyを再開し、影響を受けるJourneyも再実行する。最終変更後のレビューを通らないまま`implemented`または`verified`へ進めない。

レビューとJourneyの実結果を契約どおり記録するだけの状態遷移、条件checkbox、検証欄、証拠link、PLANの進捗checkbox・結果ログはGateを失効させない。ただし、未確認結果を完了扱いする変更や、記録に見せかけて契約の意味を変える更新は失効対象とする。

## 6. Journeyを検証する

恒久的なverification briefは作らない。検証前に`/tmp`または実行中PLANへ、対象USに必要な次の項目だけを記載する。

- 開始状態と利用者の目的
- normal pathと完了点
- 中間の判断・状態遷移
- exception、failure、cancel、retry、staleのうち対象となるもの
- reload、再起動、Back、再訪のうち対象となるもの
- keyboard、狭幅、アクセシビリティのうち対象となるもの
- 外部サービス、費用、権限、必要な証拠

UIを含むUSは通常入口から実画面で確認する。外部サービスや課金が受け入れ条件に含まれる場合は、利用者の明示承認後に実行する。未実施の検証をmockやfixtureで代替して完了扱いにしない。

## 7. 状態と証拠を更新する

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
