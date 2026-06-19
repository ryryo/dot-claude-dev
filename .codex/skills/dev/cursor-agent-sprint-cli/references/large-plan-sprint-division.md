# Large Plan Sprint Division

大きな実装計画や調査計画を Cursor CLI sprint の実行単位へ分割するための手順。

この option は実装ではなく分割設計を行う。入力計画の形式は固定しない。main Codex が計画の source of truth を特定し、sprint boundary を決める。Cursor CLI worker に計画全体の進行判断、完了判定、計画ファイル更新、commit/push は任せない。

特定の計画フォーマットを前提にしない。構造化された計画、Markdown の実装メモ、issue、PR description、Linear ticket、設計 doc、手元のチェックリスト、または会話内の指示だけで構成された大きな作業にも同じ考え方で分割する。

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
- 受け入れ条件。明示されていない場合は、ユーザー視点の完了条件と最小 verification を推定する。
- 影響範囲。read scope、write scope、外部 state、cross-repo、migration、UI surface、tests。
- 既に完了済みの部分と、未完了部分。
- ユーザー判断が必要な部分。

## B. sprint boundary 候補を作る

最初は入力計画に書かれている自然な単位を候補にする。milestone、phase、section、step、チェックリスト項目、機能領域など、計画内で使われている区切りから始める。

その後、次の観点で分割 / 結合 / main Codex 専有を判断する。

### 分割する条件

- 1 単位の中に複数の独立 write scope がある。
- schema / contract / env / route / UI / tests など、失敗時の原因を分けたい領域が混在する。
- 1 回の sprint で typecheck / test が長時間 broken になり、検収しづらい。
- Worker に任せられる局所 task と、main Codex が持つべき contract task が混ざっている。
- 外部 state を変える作業と、local code edit が混ざっている。

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
- write scope が重ならず、同じ local check でまとめて検証できる。
- contract が既に固まっていて、片方だけ完了しても有用な中間状態にならない。
- まとめても Cursor CLI worker に渡す task は小さく分離できる。

例:

```text
Input units: env docs update + local setup script update
  結合してよい: 同じ env contract を使い、同じ smoke check で検証できる
  結合しない: auth security contract と runtime repository migration
```

### main Codex 専有にする条件

- cross-repo source of truth、auth security、cookie domain、DB schema ownership、API contract を決める。
- source-of-truth 計画、progress、checklist、完了判定などを更新する。
- production secret、OAuth callback、deploy、remote migration など外部 state を変える。
- 複数 worker の成果を統合する。
- write scope が広すぎて Cursor CLI worker の `--yolo` に渡すと rollback 判断が難しい。
- ユーザー判断が必要な仕様を含む。

## C. 実行ステージと barrier を決める

全 sprint を順番に自動実行できるとは限らない。外部サービス設定、ユーザー判断、手動ログイン、production secret、OAuth callback、課金・権限確認、データ移行の実行許可など、main Codex だけでは進められない作業が途中に入ることがある。

分割案では sprint の列挙だけでなく、次のような実行ステージを作る。

```text
Stage 0: preflight / source-of-truth confirmation
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
- blocker が解消しない場合の fallback。skip、mock、local-only、plan update、作業停止など。

barrier がある場合、ユーザーに「今すぐ実行できる sprint group」と「ユーザー作業後に実行する sprint group」を分けて提示する。ユーザー作業を暗黙の前提にして sprint を開始しない。

## D. 分割表を書く

実装前に、ユーザーに短く分割案を提示する。長い計画の再説明ではなく、実行単位と理由だけを書く。

```text
Sprint Plan for <source-of-truth>

Stage 0 main-only: preflight / external state / shared contract
  reason: outside-local-state and source-of-truth decisions

Stage 1 sprint group: Phase A+B partial - shared config + foundation
  cursor-cli candidates:
    - T1 env parser behavior tests
    - T2 schema mapping tests
  main-owned:
    - cross-repo config contract

Barrier A user action: configure external callback
  needed before:
    - Stage 2 app integration smoke
  confirmation:
    - callback is visible in provider console or CLI/API readback passes

Stage 2 sprint group: Phase C split - repositories
  cursor-cli candidates:
    - T3 list/detail behavior tests + implementation
    - T4 artifact visibility behavior tests + implementation
  integration:
    - main Codex resolves shared helper contract
```

各 sprint に必ず書く。

- 対象 source-of-truth 単位。milestone / phase / section / step / checklist item / issue section など。
- まとめる理由、または分ける理由。
- main-owned task。
- Cursor CLI worker 候補。
- 禁止する write scope。
- sprint 完了時の最小 verification。
- 次 sprint へ渡す contract。
- barrier がある場合、必要なユーザー作業と完了確認方法。

## E. 1 sprint ずつ実行する

分割案を決めたら、一度に全 sprint を開始しない。現在の stage / sprint group だけを対象にし、必要ならその中の現在 sprint だけ `init_sprint.sh` で作り、`brief.md` / `tasks.md` を書く。

barrier に到達したら、その先の sprint を開始せず、ユーザーへ必要作業と確認方法を短く提示する。barrier が解消されたら、次の stage の sprint group に進む。

1 sprint の完了条件:

- 対象 sprint の diff が main Codex によって検収済み。
- sprint 内の required verification が実行済み、または未実行理由が明確。
- 次 sprint に必要な contract が `review.md` か最終報告に残っている。
- 元計画の完了判定や進捗更新は、必要なら main Codex が別途行う。

## F. 判断チェックリスト

sprint-cli に投げる前に確認する。

- [ ] この sprint は 1 から 3 個程度の integration batch に収まる。
- [ ] 各 Cursor CLI task の write scope が重ならない。
- [ ] worker が触ってよいファイルを絶対パスで書ける。
- [ ] source-of-truth 計画ファイル、commit、push、progress update を worker に任せていない。
- [ ] main Codex 専有の contract task と worker task が分かれている。
- [ ] sprint 完了後に通す最小検証が決まっている。
- [ ] ユーザー作業や外部 state が必要な barrier を越えて sprint を開始しようとしていない。
- [ ] 次 sprint が必要な場合、その入力 contract が明確。

このチェックリストを満たせない場合は、Cursor CLI sprint に分けず、main Codex が直接実装するか、source-of-truth 計画を更新してから進める。
