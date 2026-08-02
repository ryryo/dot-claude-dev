# Large Plan Sprint Division

大きな実装計画や調査計画を Cursor CLI sprint の実行単位へ分割するための手順。

この option は実装ではなく分割設計を行う。main Codex が計画の source of truth とsprint boundaryを決める。判断が固定済みで独立完結し、write scopeを隔離でき、検証oracleがあり、局所棄却できるtaskをCursor CLI workerへ委任する。Cursor CLI workerの範囲はtask-localなsource writeとverificationとし、計画全体の進行判断、完了判定、計画ファイル更新、commit/pushはmainが所有する。

特定の計画フォーマットを前提にしない。構造化された計画、Markdown の実装メモ、issue、PR description、Linear ticket、設計ドキュメント、手元のチェックリスト、または会話内の指示だけで構成された大きな作業にも同じ考え方で分割する。

## A. 入力計画の形式を判定する

まず、何が source of truth かを確認する。

- 構造化された計画ディレクトリまたは計画ファイル
- 単一 Markdown の実装計画
- issue / PR / Linear ticket などの外部タスク説明
- 会話内に貼られた作業計画
- 既存コードとユーザー指示だけで構成される大きめの作業

形式ごとに読む対象を決める。

- 構造化された計画: 目次、タスク一覧、仕様、関連資料、進捗ファイル
- 単一 Markdown: 見出し、チェックリスト、依存関係、受け入れ条件
- issue / ticket: 本文、コメント、リンク先の仕様、関連 PR / code
- 会話内計画: ユーザーの最新指示、明示された制約、未解決の判断事項
- コード起点: `AGENTS.md`、`package.json`、関係する entrypoint、module、test、config

次を抽出する。

- 作業単位の候補。milestone、phase、section、step、epic、checklist item、feature area など名前は問わない。
- 依存関係。先に決める contract、後続が使う helper、schema、API boundary、routing、state など。
- 受け入れ条件。明示されていない場合は、ユーザー視点の完了条件と最小検証を推定する。
- 影響範囲。read scope、write scope、外部 state、cross-repo、migration、UI surface、tests。
- 既に完了済みの部分と、未完了部分。
- ユーザー判断が必要な部分。

## B. sprint boundary 候補を作る

最初は入力計画に書かれている自然な単位を候補にする。milestone、phase、section、step、チェックリスト項目、機能領域など、計画内で使われている区切りから始める。

その後、次の観点で sprint boundary を調整する。

### 分割する条件

- 1 単位の中に複数の独立 write scope がある。
- schema / contract / env / route / UI / tests など、失敗時の原因を分けたい領域が混在する。
- 1 回の sprint で typecheck や test が長時間失敗したままになり、検収しづらい。
- Cursorに分離できる独立taskと、それ以外の結合作業が混ざっている。
- 外部 state を変える作業と、ローカルのコード編集が混ざっている。

例:

```text
Input unit: Runtime repository migration
  Sprint R1: schema/query foundation (main + focused worker)
  Sprint R2: list/detail repository
  Sprint R3: artifact visibility repository
  Sprint R4: job lifecycle repository
  Sprint R5: authz/connection repository
```

### 結合してよい条件

- 片方がもう片方の小さな前提変更で、分けると検証が重複する。
- write scope が重ならず、同じローカルの確認作業でまとめて検証できる。
- contract が既に固まっていて、片方だけ完了しても有用な中間状態にならない。
- まとめてもCursor CLI workerに渡すtaskは独立性と検証oracleを維持できる。

例:

```text
Input units: env docs update + local setup script update
  結合してよい: 同じ env contract を使い、同じ smoke check で検証できる
  結合しない: auth security contract と runtime repository migration
```

### Cursor 委任を決める

次をすべて満たすtaskをCursor候補にする。

- decision stateがfixed、または選択肢とtie-break ruleがbounded。
- implementation independenceがindependent、またはmain Gateでstagedへ分解済み。
- allowed pathが排他的で、他の作業とwrite scopeが重ならない。
- focused test、fixture、typecheck、build、snapshot、dry-run等の再現可能なoracleがある。
- local diffとして棄却できるか、共有artifactのexclusive ownershipとrollbackがある。
- 既存pattern、参照実装、sample、fixture、testのいずれかを直接使える。

complexityはprompt量、timeout、verification強度へ反映する。auth/crypto/retry/provider等のrisk modifierには、mainが固定するinvariant、negative case、real secretやproduction stateを使わないoracle、局所rollbackを必須controlとして設定する。controlを満たす実装はCursor、満たせない実装はmainが所有する。

未解決判断または結合実装を含むtaskは、`main: 判断・contract・oracle固定`、`Cursor: 参照駆動の独立実装shard`、`main: risk検証・統合`へ分割する。分割で同じsourceの往復編集が増える、またはcontext再構築と検収costが実装costを上回る場合はmainが一貫して所有する。

## C. 実行ステージと barrier を決める

全 sprint を順番に自動実行できるとは限らない。外部サービス設定、ユーザー判断、手動ログイン、production secret、OAuth callback、課金・権限確認、データ移行の実行許可など、main Codex だけでは進められない作業が途中に入ることがある。

分割案では sprint の列挙だけでなく、次のような実行ステージを作る。

```text
Stage 0: source-of-truth confirmation
Stage 1: sprint group 1 - local foundation
Barrier A: user config - OAuth callback registration
Stage 2: sprint group 2 - app integration after callback exists
Barrier B: user decision - choose rollout policy
Stage 3: sprint group 3 - verification and cleanup
```

barrier には必ず書く。

- 誰が行うか。user / main Codex / external owner。
- 何を完了する必要があるか。
- 完了確認方法。画面での確認、CLI readback、env presence、API smoke など。
- barrier 前に進められる sprint と、barrier 後でなければ進められない sprint。
- blocker が解消しない場合の fallback。skip、mock、local-only、計画更新、作業停止など。

barrier がある場合、ユーザーに「今すぐ実行できる sprint group」と「ユーザー作業後に実行する sprint group」を分けて提示する。ユーザー作業を暗黙の前提にして sprint を開始しない。

## D. 分割表を書く

実装前に、ユーザーに短く分割案を提示する。長い計画の再説明ではなく、実行単位と理由だけを書く。

```text
Sprint Plan for <source-of-truth>

Stage 0 main: sprint boundary と依存関係を確認
  reason: Cursor に渡す独立 task を抽出する

Stage 1 sprint group: Phase A+B partial - shared config + foundation
  cursor-cli candidates:
    - T1 env parser behavior tests
    - T2 schema mapping tests
  routing basis:
    - fixed decision / independent / isolated write / strong oracle / local reversible
  main:
    - Cursor 委任条件を満たさない残りの作業

Barrier A user action: configure external callback
  needed before:
    - Stage 2 app integration smoke
  confirmation:
    - callback is visible in provider console or CLI/API readback passes

Stage 2 sprint group: Phase C split - repositories
  cursor-cli candidates:
    - T3 list/detail behavior tests + implementation
    - T4 artifact visibility behavior tests + implementation
  main:
    - Cursor task と write scope が重なる残りの作業
```

Cursor CLI preflight は stage 0、分割表、task graph に事前配置しない。submit / monitor が CLI 疎通問題で失敗した場合だけ、復旧用の途中処理として差し込む。

各 sprint に必ず書く。

- 対象 source-of-truth 単位。milestone / phase / section / step / checklist item / issue section など。
- まとめる理由、または分ける理由。
- main Codex が実行する残りの task。
- Cursor CLI worker 候補。
- 各候補のdecision state、independence、side-effect scope、verification oracle、complexity。
- 禁止する write scope。
- sprint 完了時の最小検証。
- 次 sprint へ渡す contract。
- barrier がある場合、必要なユーザー作業と完了確認方法。

## E. 1 sprint ずつ実行する

分割案を決めたら、一度に全 sprint を開始しない。現在の stage / sprint group だけを対象にし、必要ならその中の現在 sprint だけ `init_sprint.sh` で作り、`brief.md` / `tasks.md` を書く。

barrier に到達したら、その先の sprint を開始せず、ユーザーへ必要作業と確認方法を短く提示する。barrier が解消されたら、次の stage の sprint group に進む。

1 sprint の完了条件:

- 対象 sprint の diff が main Codex によって検収済み。
- sprint 内の必須検証が実行済み、または未実行理由が明確。
- 次 sprint に必要な contract が `review.md` か最終報告に残っている。
- 元計画の完了判定や進捗更新は、必要なら main Codex が別途行う。

## F. 判断チェックリスト

sprint-cli に投げる前に確認する。

- [ ] この sprint は 1 から 3 個程度の統合バッチに収まる。
- [ ] 各 Cursor CLI task の write scope が重ならない。
- [ ] worker が触ってよいファイルを絶対パスで書ける。
- [ ] source-of-truth 計画ファイル、commit、push、進捗更新を worker に任せていない。
- [ ] Cursor CLI taskはdecisionがfixed/bounded、independenceがindependent/staged、write scopeがisolated、oracleがstrong/限定可能なpartial、side effectがlocal/shared reversibleである。
- [ ] execution routeを判断状態、独立性、write scope、oracle、副作用と可逆性から決め、complexityを実行量と検証強度へ反映した。
- [ ] risk modifierがあるtaskは、main固定invariant、negative case、real secret/production state禁止、main再検証が具体化されている。
- [ ] sprint 完了後に通す最小検証が決まっている。
- [ ] ユーザー作業や外部 state が必要な barrier を越えて sprint を開始しようとしていない。
- [ ] 次 sprint が必要な場合、その入力 contract が明確。

このチェックリストを満たせない場合は、Cursor CLI sprint に分けず、main Codex が直接実装するか、source-of-truth 計画を更新してから進める。
