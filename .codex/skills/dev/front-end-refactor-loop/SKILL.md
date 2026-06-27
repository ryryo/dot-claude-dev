---
name: front-end-refactor-loop
description: |
  指定されたフロントエンド範囲に対して、同梱の front-end-design-patterns 参照を使った新規監査、Cursor CLI sprint への安全な局所委譲、main Codex による採否判定・修正・検証・必要時の性能計測・コミットを NO_FINDINGS まで反復する。機能変更なしの React / Vue / JavaScript リファクタリング、描画ホットパス整理、依存安定化、派生 state 整理、component 境界分離、bundle / lazy loading 改善、サブエージェント調査つきフロントエンドリファクタリングで使う。起動語: front-end-refactor-loop, フロントエンドリファクタリングループ, Reactリファクタリングループ, Vueリファクタリングループ, NO_FINDINGSまでリファクタ, Cursor CLIでフロントエンドリファクタ
---

# front-end-refactor-loop

指定されたフロントエンド範囲を、挙動変更なしで反復的に整理する。main Codex がループ制御、採否判定、統合、検証、最終報告を担当し、read-only 監査や安全に分離できる局所実装だけを `cursor-agent-sprint-cli` 経由で Cursor CLI worker に渡す。

## 絶対ルール

- このスキル配下以外の既存スキル資産を参照しない。必要な設計パターン資料は、このスキルの `references/front-end-design-patterns/` から読む。
- `cursor-agent-sprint-cli` は `WORKSPACE/.codex/skills/dev/cursor-agent-sprint-cli` をパス参照して使う。
- Cursor CLI worker に commit、push、PR 作成、branch 切替、sprint 完了判断、最終報告、進行管理ファイルの任意更新を任せない。
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

`decision-matrix.md` で候補を 1 から 4 件に絞り、必要な個別 reference の `Original Skill Metadata` と `original-skill-body` を読む。

## 起動前確認

ユーザー指示から以下を確定する。危険な曖昧さがない限り、質問で止まらず既存コードから推定する。

- 対象範囲: route、component、directory、feature、関連 hook / store / utility。
- 変更禁止条件: 機能、UI、公開 API、データ形式、保存形式、外部通信、イベント順。
- 検証条件: `typecheck`、lint、test、build、browser check、既存 fixture。
- コミット方針: 原則として修正ループごとに `dev:simple-add` 相当の最小コミットを行う。ユーザーがコミット不要と明示した場合はコミットしない。

最初に repository context を読む。

```bash
git status --short
git branch --show-current
```

あわせて `AGENTS.md`、`package.json`、対象ファイル、周辺利用箇所、既存 test、build / lint / typecheck script を確認する。

## Sprint 初期化

1 回の refactor run につき 1 つの sprint directory を使う。

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
3. `cursor-agent-sprint-cli` の preflight を実行する。
4. 新規監査を read-only worker task として投げる。広い対象は複数 scope に分割する。
5. main Codex が findings を採否判定し、`performance_sensitive` を分類する。
6. 安全に分離できる局所変更だけ Cursor CLI worker に実装委譲する。shared contract や境界判断は main Codex が持つ。
7. 性能計測ゲート対象なら before / after を同じ手順で測り、一時計測コードを削除する。
8. main Codex が diff、write scope、挙動維持、検証結果を確認する。
9. 検証後、コミット方針に従って `dev:simple-add` 相当で最小コミットを行う。
10. 最新 clean HEAD から次の新規監査を実行する。
11. 全対象 scope が同じ最新 clean HEAD で `NO_FINDINGS` を返したら最終検証と最終レポートを行う。

## 新規監査

新規監査は毎 round 新しい worker task として実行する。前回 worker の文脈を再利用しない。

監査 task は原則 read-only にする。対象が広い場合は、route、component、shared hook、state、media、bundle などで scope を分け、各 worker の担当範囲を重ねすぎない。

監査 worker には以下を必ず渡す。

- repository 絶対パス。
- expected HEAD と `git status --short` の期待値。
- read-only 制約。
- 対象範囲。
- 読むべき pattern reference の候補。
- このスキル配下以外の既存スキル資産を参照しない制約。
- 出力形式と `NO_FINDINGS` の完了条件。

完了判定に使えるのは、同じ最新 clean HEAD を確認し、対象範囲を fresh に読み直し、指定形式で返した結果だけ。`BLOCKED`、形式崩れ、古い HEAD、親セッションの要約、範囲外の一般論は採用しない。

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
- コミット、最終検証、最終報告。
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

検証できない場合は、理由、代替確認、残リスクを report に書く。

## 完了条件

- 最新 round の全監査 scope が同じ clean HEAD で `NO_FINDINGS` を返している。
- 採用した指摘が実装・検収・検証済みである。
- 性能計測ゲート対象の一時計測コードが残っていない。
- 修正済み loop はコミット方針どおり処理済みである。
- 作業ツリーが clean、またはユーザー由来の unrelated 変更だけが残っている。
- 最終レポートに対象範囲、loop 履歴、適用した pattern、検証結果、性能計測の有無、残リスクを含めている。
