---
name: architecture-refactor-loop
description: |
  コードベースまたは指定範囲を、main Codex 主導でアーキテクチャ上の満足条件まで段階的にリファクタリングする。フェーズ分け、/tmp/refactor-{projectname}.md の進捗記録、goal file 作成、各 goal ごとの委譲判定、実装、実動作確認、Codex 側レビュー、コミット、再監査を反復する。大規模リファクタ、責務分離、依存方向整理、モジュール境界整理、状態・副作用境界の改善、テスト容易性改善、コードベース全体の architecture cleanup で使う。起動語: architecture-refactor-loop, アーキテクチャリファクタリングループ, コードベースを満足できるまでリファクタ, フェーズ分けしてリファクタ, goal file リファクタ, /tmp/refactor 進捗
---

# architecture-refactor-loop

コードベースを一気に書き換えず、現状把握、フェーズ計画、goal file、委譲判定、実装、検証、Codex 側レビュー、コミット、再監査の単位で進める。main Codex が設計判断・採否・統合・レビュー・完了判定を持ち、分離できる局所作業だけを必要に応じて worker に委譲する。

## 絶対ルール

- main Codex がアーキテクチャ方針、委譲判定、統合、レビュー、コミット、完了判定を担当する。
- Cursor CLI worker は必須ではない。使う場合も、局所実装補助に限定する。
- Cursor CLI worker にレビュー、採否判断、完了判断、コミット、push、PR 作成、branch 切替を任せない。
- レビューは Codex 側で行う。可能なら Codex subagent に read-only fresh review を依頼し、難しければ main Codex が code-review stance で差分レビューする。
- 既存挙動、公開 API、保存形式、データ形式、schema、URL、イベント順、error semantics、外部副作用を意図なく変えない。
- 外部 state、production data、secret、remote migration、課金や権限に関わる操作は明示許可なしに行わない。
- 既存の未コミット変更を戻さない。関係がある場合は差分を読んで作業し、関係がなければ触らない。
- 「好みの整理」だけでは goal にしない。各 goal は具体的な architecture pain、受け入れ条件、検証方法を持つ。
- `/tmp` の進捗ファイルと goal file は作業管理用であり、ユーザーが明示しない限りコミットしない。

## 作業ディレクトリ

project name は repository basename を小文字英数字とハイフンに正規化して決める。

```bash
PROJECT_NAME="<repo-basename-normalized>"
REF_DIR="/tmp/refactor-$PROJECT_NAME"
PROGRESS_FILE="/tmp/refactor-$PROJECT_NAME.md"
GOALS_DIR="$REF_DIR/goals"
mkdir -p "$GOALS_DIR"
```

`PROGRESS_FILE` にはフェーズ、goal、委譲判定、検証、レビュー、コミット、残課題を追記する。`GOALS_DIR` には `G01_<slug>.md` のような goal file を作る。

`/tmp` が使えない環境では、理由を記録したうえで `.codex/tmp/{YYMMDD}_architecture-refactor-{projectname}/` を使う。

## Phase 0: 現状把握

まず repository を読む。必要な範囲に絞りつつ、architecture 判断に必要な入口は必ず確認する。

```bash
git status --short
git branch --show-current
```

読む対象の目安:

- `AGENTS.md`、README、package / build / test 設定。
- entrypoint、routing、CLI command、server handler、主要 module。
- domain / application / infrastructure / UI / adapter の境界。
- state、cache、DB、filesystem、network、time、random などの副作用境界。
- public API、schema、payload、event、error handling。
- 既存 test、fixture、mock、integration check。
- 依存方向、循環依存、巨大 module、重複 logic、暗黙 global state。

現状把握の結果を `PROGRESS_FILE` に短く書く。

```markdown
## 現状把握
- 対象:
- 主要 entrypoint:
- 検証コマンド:
- architecture pain:
- 守る contract:
- 既存未コミット変更:
```

## Discovery Gate

満足条件やフェーズ計画を作る前に、初回洞察が浅すぎないかを必ず確認する。最初に見つけた 1 つの問題だけを goal 化して終わってはいけない。

Discovery Gate では、少なくとも以下を `PROGRESS_FILE` に書く。

```markdown
## Architecture Map
- 実行入口:
- 主要データフロー:
- 主要 state owner:
- 副作用境界:
- public contract:
- 層 / module 境界:
- 依存方向:
- 検証境界:

## Architecture Finding Sweep
| 観点 | 確認した場所 | finding | severity | 対応 |
|---|---|---|---|---|
| 責務境界 | | | P0/P1/P2/P3/なし | goal/defer/なし |
| 依存方向 | | | P0/P1/P2/P3/なし | goal/defer/なし |
| state ownership | | | P0/P1/P2/P3/なし | goal/defer/なし |
| 副作用境界 | | | P0/P1/P2/P3/なし | goal/defer/なし |
| contract 保護 | | | P0/P1/P2/P3/なし | goal/defer/なし |
| test seam | | | P0/P1/P2/P3/なし | goal/defer/なし |
| 実行時リスク | | | P0/P1/P2/P3/なし | goal/defer/なし |
```

severity の目安:

- P0: 既存挙動、データ、安全性、ビルド、リリースを壊す恐れが高い。
- P1: architecture 上の主要な詰まりで、今後の変更を明確に危険または高コストにしている。
- P2: 分離・依存・検証性の悪さがあり、今回の scope で直す価値がある。
- P3: 好みや小規模整理に近く、他 goal のついででよい。

浅い計画として差し戻す条件:

- 実行入口、データフロー、state owner、副作用境界、public contract のいずれかを説明できていない。
- finding が 1 件だけで、他の観点を「なし」と判断した根拠がない。
- phase が 1 つだけで、検証基盤、境界整理、依存整理、状態・副作用、contract 保護、最終監査のどれを扱うかが見えていない。
- goal が実装手順だけで、どの architecture pain を解消するか書けていない。
- 「満足条件」が特定ファイルの修正完了だけになっている。

Discovery Gate を通すには、全観点で finding または「なし」の根拠を書き、P1 / P2 を goal 化するか、defer 理由を明示する。P3 だけが残る状態を最初の満足条件の候補にしてよい。

## 満足条件

「満足できるまで」を無限ループにしない。Phase 0 の後に、今回の完了条件を明示する。

満足条件は Discovery Gate の結果から作る。特定の 1 問題を直すだけの条件にしない。対象範囲に対して、どの architecture 観点を調べ、どの P1 / P2 を解消し、何を defer するかが分かる形にする。

満足条件の例:

- 対象範囲の P0 / P1 / P2 architecture finding が解消済み、または明示的に defer 済み。
- module boundary、依存方向、state ownership、副作用境界、test seam の主要な不整合が説明できる状態になっている。
- 変更した public contract がない、または明示承認された contract 変更だけである。
- 重要な goal ごとに実動作確認または代替検証が済んでいる。
- Codex 側レビューで blocking finding がない。
- 各 integration batch がコミット済みで、作業ツリーが clean、または unrelated なユーザー変更だけが残っている。

満足条件は `PROGRESS_FILE` に書く。途中で変更する場合は、理由と変更日を追記する。

## フェーズ計画

現状把握後に、3 から 7 個程度の phase に分ける。phase は成果物や境界で切る。

フェーズ計画は Discovery Gate の finding sweep から作る。1 つの目立つ問題だけを phase にしない。少なくとも「安全網または検証」「境界または依存方向」「最終監査」を含め、不要な phase は理由を付けて省く。

よく使う phase:

- Foundation: 検証基盤、characterization test、型境界、最小 safety net。
- Boundary: module / layer / package / route / adapter 境界の整理。
- Dependency: 依存方向、循環参照、barrel、shared utility の整理。
- State and Side Effects: state ownership、cache、I/O、timer、random、network 境界。
- Contract Preservation: public API、schema、payload、error semantics の保護。
- Cleanup: dead code、重複削減、命名、不要 compatibility の整理。
- Final Audit: 再監査、残課題 defer、最終検証。

phase ごとに goal 候補を作る。大きい goal は分割し、小さすぎる goal は同じ検証で安全に見られる単位へまとめる。

## Goal File Contract

各 goal file は `GOALS_DIR/Gxx_<slug>.md` に作る。goal file はその goal の実行契約であり、実装前に必ず書く。

```markdown
# Gxx: <goal title>

## 目的
<この goal で改善する architecture pain>

## 現状
- 対象:
- 問題:
- 守る既存挙動:

## 望む構造
- 責務境界:
- 依存方向:
- state / side effect ownership:
- test seam:

## 委譲判定
- owner: main-codex | codex-subagent-readonly | cursor-cli-worker | no-delegation
- 理由:
- read scope:
- write scope:
- 禁止範囲:
- worker を使う場合の検収方法:

## 実装方針
- steps:
- migration / compatibility:
- rollback risk:

## 受け入れ条件
- [ ] 既存挙動を変えない
- [ ] architecture pain が解消または明示的に defer されている
- [ ] 必要な test / typecheck / build / smoke が通る
- [ ] Codex 側レビューで blocking finding がない

## 検証
- command:
- 手動 smoke:
- 実行できない場合の代替確認:

## レビュー
- reviewer: main-codex | codex-subagent-readonly
- review focus:

## コミット
- commit unit:
- message draft:
```

ユーザーが `/goal` 実行を明示した環境では、goal file をそのまま `/goal` の入力単位として扱う。そうでない環境では、main Codex が goal file を読み、その契約に沿って直接実行する。

## 委譲判定ゲート

委譲判定は、goal 作成時と実行直前の 2 回行う。実行直前に状況が変わっていたら goal file と `PROGRESS_FILE` を更新する。

main Codex が直接担当する:

- architecture 方針、責務境界、依存方向、public contract を決める。
- 複数 module / layer にまたがる変更を統合する。
- 既存挙動や暗黙 contract の解釈が必要。
- migration、schema、API、auth、storage、routing、external state に関わる。
- 失敗時の rollback 判断が難しい。
- 既存未コミット変更に触れる。
- 検証方法が曖昧。

Codex subagent に委譲してよい:

- read-only の architecture audit。
- 設計案比較。
- diff review。
- test strategy / risk analysis。
- fresh review。

Cursor CLI worker に委譲してよい:

- write scope が明確で狭い。
- 他 task とファイル競合しない。
- contract 判断を含まない。
- acceptance と verification を具体的に書ける。
- main Codex が後で diff review できる。

Cursor CLI worker を使う場合は、`WORKSPACE/.codex/skills/dev/cursor-agent-sprint-cli` をパス参照し、そのスキルの preflight、prompt、monitor、diff 検収手順に従う。存在しない、preflight が通らない、または write scope を分離できない場合は使わない。

委譲しない:

- 分離できない。
- 判断が曖昧。
- 検証方法がない。
- worker に渡すほど小さくない、または危険。

## 実装ループ

各 goal は以下の順に進める。

1. goal file を読む。
2. 委譲判定ゲートを通す。
3. 実装前に必要な safety check または characterization test を作る。
4. main Codex または選定 worker が実装する。
5. main Codex が diff と write scope を確認する。
6. 必須検証を実行する。
7. Codex 側レビューを行う。
8. blocking finding があれば修正し、検証とレビューを繰り返す。
9. `PROGRESS_FILE` を更新する。
10. `dev:simple-add` 相当で commit する。ユーザーが commit 不要と明示した場合は commit しない。

検証の優先順:

1. focused test / characterization test
2. typecheck
3. lint
4. integration test
5. build
6. smoke / browser / CLI 実行

検証できない場合は、理由、代替確認、残リスクを `PROGRESS_FILE` と final report に書く。

## Codex 側レビュー

レビューは必ず Codex 側で行う。Cursor CLI worker の報告は参考情報であり、レビュー結果ではない。

レビュー観点:

- 既存挙動、public contract、error semantics を変えていないか。
- 依存方向が改善しているか。新しい循環依存や層越え依存を作っていないか。
- 責務境界が明確か。巨大 helper や曖昧な shared module に逃げていないか。
- state ownership と副作用境界が明確か。
- テスト容易性が上がっているか。単に mock が増えただけになっていないか。
- 変更範囲が goal の write scope に収まっているか。
- 未コミットのユーザー変更を戻していないか。
- 削除した code が本当に不要か。
- performance、concurrency、resource lifecycle に新しい risk がないか。

Codex subagent が使える場合は、重要 goal または phase 完了時に read-only fresh review を依頼してよい。依頼する場合も、採否判断は main Codex が行う。

## 進捗記録

`PROGRESS_FILE` は短く、実行判断に必要な情報だけを書く。

```markdown
# Refactor Progress: <project>

## 満足条件
- ...

## Phase Plan
| Phase | Goal | Owner | Status | Commit | Verification |
|---|---|---|---|---|---|

## Current Findings
- P0:
- P1:
- P2:
- Deferred:

## Activity Log
### <date> Gxx <title>
- 委譲判定:
- 変更:
- 検証:
- Codex review:
- commit:
- 残リスク:
```

`PROGRESS_FILE` は最終 report の材料にする。長い調査ログや思考過程を溜め込まない。

## 再監査と完了判定

phase 完了ごとに architecture audit を行う。audit は main Codex または Codex subagent の read-only review として行い、Cursor CLI worker には完了判定を任せない。

再監査で新しい P0 / P1 / P2 finding が出た場合:

- 今回の満足条件に含めるべきなら goal を追加する。
- 今回の scope 外なら理由を付けて deferred にする。
- 判断できないならユーザーに確認する。

完了時は最終検証を実行し、作業ツリーを確認する。

```bash
git status --short
```

## 最終報告

最終報告には以下を含める。

- 対象範囲。
- 満足条件に対する結果。
- phase / goal 一覧。
- main Codex が直接担当した設計判断。
- worker に委譲した task と、その検収結果。
- Codex 側レビュー結果。
- 実行した検証と結果。
- commit 一覧。
- deferred item と残リスク。

長い progress file の全文は貼らず、判断に必要な要約だけを書く。
