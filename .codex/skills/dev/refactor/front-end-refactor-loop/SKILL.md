---
name: front-end-refactor-loop
description: "指定フロントエンド範囲のcomponent・state・render・loadingを監査し、挙動を保ってリファクタリングする。read-only監査にも対応する。"
---

# front-end-refactor-loop

指定されたフロントエンド範囲を、挙動変更なしで反復的に整理する。main Codex がループ制御、採否判定、統合、検証、最終報告を担当し、監査と実装を進める。独立した監査や局所実装は、分担利益があり実行環境で許可される場合にだけ委譲する。

## 絶対ルール

- 設計パターン資料は、このスキルの `references/front-end-design-patterns/` から読む。
- `cursor-agent-sprint-cli` は `WORKSPACE/.codex/skills/dev/cursor-agent-sprint-cli` をパス参照して使う。
- Cursor CLI worker にversion control／remote操作、sprint 完了判断、最終報告、進行管理ファイルの任意更新を任せない。
- 機能、UI 仕様、公開 API、データ形式、保存形式、URL、イベント順、外部 API 呼び出しを意図的に変えない。
- 既存の未コミット変更を戻さない。関係がある場合は差分を読んで作業し、関係がなければ触らない。
- worker の報告だけで採用しない。main Codex が必ず `git diff`、write scope、検証結果を確認する。
- 性能改善を主張する変更、render / state / bundle / canvas / list / queue に影響する変更では、必要に応じて性能計測ゲートを通す。

## 参照資料

必要になった時点で以下を読む。最初から全 reference を読み込まない。

- 設計パターンの入口: `references/front-end-design-patterns/decision-matrix.md`
- React 参照候補: `references/front-end-design-patterns/react/index.md`
- Vue 参照候補: `references/front-end-design-patterns/vue/index.md`
- JavaScript / bundle / loading 参照候補: `references/front-end-design-patterns/javascript/index.md`
- Worker 用プロンプト雛形: `references/prompt-templates.md`
- ループ報告雛形: `references/report-templates.md`

`decision-matrix.md` で現在の症状に必要な候補へ絞り、必要な個別 reference の `Original Skill Metadata` と `original-skill-body` を読む。

## Read-only audit mode

利用者が監査のみを依頼した場合、または呼出元スキルが`read-only audit mode`を指定した場合、この節をSprint初期化、Cursor preflight、実装委譲、修正loopより優先する。

- repositoryと指定scopeをfreshに読み、編集、Sprint／進捗file作成、テスト／build実行、Cursor CLI、Gitの状態変更、外部作用を行わない。
- 許容された既存差分を`git status --short`で確認し、baselineと現在差分の両方を監査する。
- `decision-matrix.md`から現在の症状に必要なreferenceを選び、選んだ個別referenceを読む。
- component／composition、hook／effect、context／selector／state、render／canvas／list、bundle／loading、accessibility、SSRのうちscopeへ適用する観点を一件目で止めずに一巡する。
- blanket memoization、行数だけの分割、未計測の性能主張、UI仕様変更、新dependencyをfindingへ昇格させない。
- audit agentは採否、goal化、実装、完了判定をせず、一回のfresh reportを返して停止する。

出力には次を含める。

1. 実際に確認したscopeとpath
2. 選択したpattern referenceと適用理由
3. findingごとのseverity、path／line、到達するrender／interaction経路、影響、最小修正境界、既存oracle、性能計測要否
4. 既に差分で直っている問題、却下／deferした候補と理由

追加のP0／P1／P2がなければ`NO_FINDINGS`とする。read-only audit modeはここで終了する。

## 起動前確認

ユーザー指示から以下を確定する。危険な曖昧さがない限り、質問で止まらず既存コードから推定する。

- 対象範囲: route、component、directory、feature、関連 hook / store / utility。
- 変更禁止条件: 機能、UI、公開 API、データ形式、保存形式、外部通信、イベント順。
- 検証条件: `typecheck`、lint、test、build、browser check、既存 fixture。
- 結果記録: 修正ループごとに変更path、採否、検証結果を記録する。

最初に repository context を読む。

```bash
git status --short
```

あわせて `AGENTS.md`、`package.json`、対象ファイル、周辺利用箇所、既存 test、build / lint / typecheck script を確認する。

## Sprint 初期化

Cursor CLI workerへ実際に委譲する場合だけ、[cursor-agent-sprint-cli](../../cursor-agent-sprint-cli/SKILL.md)を読み、1回のrunにつき1つのSprintを使う。main単独では会話内または既存PLANへscope、採用finding、検証結果を記録し、Sprint初期化を省略する。

```bash
WORKSPACE="$(pwd)"
SPRINT_SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-sprint-cli"
SPRINT_SLUG="frontend-refactor-<short-slug>"
"$SPRINT_SKILL_DIR/scripts/init_sprint.sh" --workspace "$WORKSPACE" --slug "$SPRINT_SLUG"
. "$WORKSPACE/.codex/tmp/$(date +%y%m%d)_$SPRINT_SLUG/sprint-env.sh"
```

`SPRINT_SKILL_DIR` が存在しない場合だけ、リポジトリ実体に合わせて絶対パスを確認する。`cursor-agent-sprint-cli` の scripts や templates はこのスキルへコピーしない。

`brief.md` には対象範囲、挙動維持制約、参照する pattern reference、検証コマンド、完了条件を書く。`tasks.md` には round、audit task、implementation task、main-owned task、write scope、禁止範囲、検証を記録する。

## 全体フロー

1. 対象範囲と検証条件を確定する。
2. `decision-matrix.md` から今回使う設計パターン reference を選び、必要な個別 reference を読む。
3. mainまたは許可されたread-only担当が固定scopeを監査する。Cursor委譲時も通常のpreflightは追加しない。
4. mainが全findingの採否と必要な性能計測を決め、完了条件を固定する。性能Gate対象は実装前にbaselineを測る。
5. 依存順に実装する。局所委譲する場合は排他的scopeとoracleを渡し、mainが検収する。
6. 性能計測が必要ならbefore／afterを同条件で測り、一時計測コードを削除する。
7. mainが差分、挙動維持、必要な検証を確認し、変更pathと結果を記録する。
8. 統合後に固定scopeをfreshに読み直して最終監査する。修正が必要なら影響範囲を再確認する。
9. 採用findingの解消、必要な検証、固定scopeの`NO_FINDINGS`が揃ったら報告する。

## 新規監査

初回と統合後の最終監査は、固定scopeの現在の実装を直接確認する。独立評価を行う場合は先入観を与えないfreshなread-only担当を使う。修正後の再確認では、既知のfindingと影響経路を引き継ぎ、根拠なしに全面監査を繰り返さない。

監査 task は原則 read-only にする。対象が広い場合は、route、component、shared hook、state、media、bundle などで scope を分け、各 worker の担当範囲を重ねすぎない。

監査 worker には以下を必ず渡す。

- repository 絶対パス。
- `git status --short`で許容する既存差分と、今回のread scope。
- read-only 制約。
- 対象範囲。
- 読むべき pattern reference の候補。
- 設計パターン資料はこのスキルの同梱referenceから選ぶこと。
- 出力形式と `NO_FINDINGS` の完了条件。

完了判定に使えるのは、開始時の差分と今回の採用修正をbaselineとして照合し、対象範囲をfreshに読み直し、指定形式で返した結果だけ。`BLOCKED`、形式崩れ、親セッションの要約、範囲外の一般論は採用しない。

## 指摘の採否

`NO_FINDINGS` でない場合、main Codex が全件を読む。

- 機能変更、UI 仕様変更、公開 API 変更、データ形式変更を含む提案は採用しない。
- 好みだけの抽象化、既存規約に合わない置き換え、大きな依存追加は採用しない。
- 採用する指摘は、変更範囲、挙動維持根拠、検証方法、性能計測要否を明確にする。
- 同一 round 内で安全に直せる指摘はまとめて直す。write scope が重なる作業を複数 worker に並列委譲しない。

## 実装委譲の基準

Cursor CLI worker に渡してよいもの:

- 単一 component / hook / utility の局所整理。
- テスト追加や fixture 追加。
- import 整理、型補助、純粋関数抽出。
- write scope を絶対パスで限定でき、他 task と重ならない変更。

main Codex が担当するもの:

- component API、routing、state / context、data fetching、bundle boundary などの contract 判断。
- 複数 worker 成果の統合。
- 性能計測ゲートの設計と結果判断。
- version control操作、最終検証、最終報告。
- write scope が広い変更、既存未コミット変更に接する変更。

## 性能計測ゲート

以下に該当する場合は、原則として before / after の最小計測を行う。

- render 回数、React commit duration、state churn に影響する。
- state / context / selector / memo / callback / component boundary を変える。
- list / grid / card / table / canvas / image preview / hover / drag / queue / timer に関わる。
- route split、lazy import、bundle size に関わる。
- large object state、large data URL、image encode / decode、canvas 同期処理に関わる。
- レポートで「速くなる」「再描画が減る」「bundle が分離される」と主張する。

型整理、命名整理、局所ファイル分割、dead code 削除、import 整理、性能改善を主張しない保守性中心の変更では省略してよい。省略した場合は理由を書く。

計測コードは一時差分にする。after 計測後に必ず削除し、`git status --short` と `git diff` で残っていないことを確認する。

## 検証

変更内容に合う最小検証を実行する。

優先順:

1. typecheck
2. 対象ファイル lint
3. 対象 test
4. build
5. browser check
6. 性能計測ゲートの after 計測

これは全件の実行順を強制するものではない。変更が影響する検証とrepository必須checkを選び、合格後は新しい変更や失敗がある場合だけ再実行する。

検証できない場合は、理由、代替確認、残リスクを report に書く。

許可範囲内の修正と検証は完了まで続ける。契約衝突、追加権限、必須証拠の取得不能がある場合は、その依存箇所だけを未確認として報告する。

## 完了条件

- 固定scopeの最終監査と必要な影響範囲の再確認で、未解決のP0／P1／P2がなく`NO_FINDINGS`となっている。
- 採用した指摘が実装・検収・検証済みである。
- 性能計測ゲート対象の一時計測コードが残っていない。
- 修正済みloopの変更path、採否、検証結果が記録済みである。
- 対象差分が採用修正と一致し、既存の利用者差分を保護している。今回の未コミット差分を残してよく、clean化のためのcommit・reset・削除を行わない。
- 最終レポートに対象範囲、loop 履歴、適用した pattern、検証結果、性能計測の有無、残リスクを含めている。
