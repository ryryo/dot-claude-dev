---
name: dev:front-end-refactor-loop
description: |
  front-end-design-patterns を使い、指定されたフロントエンド範囲に対して
  サブエージェント調査（必要時は複数スコープに分割した独立 fresh audit） →
  メインセッション修正 → 必要時のみ性能計測 → simple-add → 再調査を
  NO_FINDINGS まで繰り返す、機能変更なしの内部リファクタリングループ。

  Trigger:
  front-end-refactor-loop, front-end-design-patterns リファクタリングループ,
  フロントエンドリファクタリングループ, Reactリファクタリングループ,
  サブエージェントでフロントエンド調査, NO_FINDINGSまでリファクタ,
  性能計測つきフロントエンドリファクタ
user-invocable: true
---

# front-end-refactor-loop

指定されたフロントエンド範囲を、`front-end-design-patterns` の観点で反復的に整理する。
このスキルはパターン知識を重複して持たず、探索・判定・修正・必要時の性能計測・コミット・再探索のループ制御だけを担う。

## コア原則

- まず `.claude/skills/dev/front-end-design-patterns/SKILL.md` を読む。
- パターン選定や判断根拠は `front-end-design-patterns` に従う。
- 機能変更、UI仕様変更、公開 API 変更、データ形式変更、イベント順変更、外部 API 呼び出し変更をしない。
- 目的は内部的な責務分離、render hot path、stable dependency、derived state、module boundary、lazy loading、不要再計算などの改善に限定する。
- 調査は毎回 **新しいサブエージェント** に委譲する。前回のサブエージェントを再利用しない。
- 広い対象や応答遅延・BLOCKED が起きやすい対象では、単一サブエージェントに固執せず、独立した複数サブエージェントへスコープ分割する。
- メインセッションは、サブエージェントが見つけた具体的な対象を実装・検証・コミットする。
- 性能計測は常時必須にしない。性能影響があり得るリファクタリングだけ、Performance Measurement Gate を通す。

## 入力の確定

ユーザーから以下を読み取る。

- 対象範囲: route / component / directory / feature 名
- 変更禁止条件: 機能、UI、公開 API、データ形式、既存挙動
- 検証条件: 既存の lint / typecheck / test / build / browser check
- コミット方針: 原則、各修正ループの最後に `simple-add`

対象範囲が曖昧で危険な場合だけ質問する。合理的に特定できる場合は止まらず進める。

## 全体フロー

1. Fresh Audit をサブエージェントへ委譲する。
2. Findings をメインセッションで採否判定し、性能影響の有無を分類する。
3. 性能影響があり得る場合だけ Performance Measurement Gate を設計する。
4. 必要なら一時 instrumentation で before 計測する。
5. メインセッションで挙動維持のリファクタリングを実装する。
6. Performance Measurement Gate 対象なら after 計測し、計測コードを削除する。
7. typecheck / lint / test / build / browser check を実行する。
8. `git diff --check` と `git status --short` を確認し、`simple-add` する。
9. ループレポートを作り、次の Fresh Audit へ戻る。
10. `NO_FINDINGS` 到達後に最終検証と Final Report を作る。

## Fresh Audit

毎回、新しいサブエージェントを起動し、read-only 調査を依頼する。
2ループ目以降も、前回結果の確認だけに寄せず、対象範囲を改めて網羅的に読むよう明記する。

### 監査トポロジー

対象が広い、依存関係が複数領域にまたがる、単一サブエージェントの応答が遅い、または `BLOCKED` / 形式崩れ / 親セッションの完了報告を返すなど監査品質が不十分な場合は、Fresh Audit を複数の独立サブエージェントに分割する。

分割を使う目安:

- route / component / shared hook / integration / media 処理など、責務境界が複数ある。
- lazy import、SSE、canvas / image / video、large object state、list/grid など、異なる性能コストが混在する。
- 1 本の監査が長時間返らない、`BLOCKED` だけで理由がない、または `NO_FINDINGS` 以外の応答形式が曖昧。
- 過去ループの文脈を引きずって、最新 clean HEAD の read-only 監査として信用しにくい。

分割ルール:

- 各サブエージェントは **新規・read-only・独立** にする。前回サブエージェントは閉じるか、完了判定から除外する。
- サブエージェントごとに責任範囲を重ならない程度に切る。例: LP editor、media/video、Codex/SSE、dashboard route、cross-cutting。
- 各プロンプトの冒頭で `git rev-parse --short HEAD` と `git status --short` を確認させ、期待する latest clean HEAD と一致しなければ `BLOCKED: baseline mismatch` で止めさせる。
- 親セッションの長い文脈が監査を汚す場合は、最小コンテキストの独立 agent を使い、対象 repo path、期待 HEAD、read-only 制約、調査範囲、出力形式だけを渡す。
- 完了判定に使えるのは、最新 clean HEAD を確認したうえで対象範囲を調査し、指定形式で返した結果だけ。`BLOCKED`、形式崩れ、親セッションの要約、古い HEAD の結果は採用しない。
- どれか 1 本でも actionable finding を返したら、その Fresh Audit round は未達扱いにする。修正・検証・コミット後、全スコープを最新 clean HEAD から再監査する。
- 最終完了には、分割した **全スコープ** の最新 fresh audit が `NO_FINDINGS` であることを要求する。

サブエージェントへのプロンプト雛形:

```text
`<repo path>` で read-only の調査を行ってください。ファイル編集とコミットは禁止です。

目的: `.claude/skills/dev/front-end-design-patterns` を使い、`<target scope>` に対して
挙動を変えない内部的なフロントエンドリファクタリング対象を独立に調査してください。
観点は container/presentational boundary、pure selectors/hooks、render hot path、
stable dependencies、derived state、module boundary、lazy loading/code splitting、
不要な再計算の回避です。機能挙動は変えてはいけません。

重要: これは fresh audit として扱ってください。過去のサブエージェント findings や
前回ループの出力を前提にしないでください。現 HEAD のコードを開き直し、関連ファイルを
改めて読み込んで調査してください。過去に報告された問題はすでに直っている可能性があります。
現在の HEAD に残っている具体的な対象だけを報告してください。

2ループ目以降の場合: 最初に、前回ループで触ったファイルが同種の
behavior-preserving refactor 問題をまだ残していないかだけを軽く sanity check してください。
その後が主作業です。`front-end-design-patterns` の観点を使い、前回とは違う角度も含めて、
対象範囲全体を fresh かつ網羅的に再調査してください。狭い regression check にしないでください。

対象範囲:
- <files/directories/routes>
- 対象画面に直接関係する場合だけ shared hooks/types も含める。

出力形式:
- 変更する価値のある問題がない場合は、正確に `NO_FINDINGS` と書き、何を調査したかを短く添える。
- 問題がある場合は、影響度順に findings を列挙する。各 finding には file path と line reference、
  なぜ問題か、安全に挙動維持で直せる refactor target を含める。
- 各 finding に `performance_sensitive: yes/no` を付ける。
- `performance_sensitive: yes` の場合は、影響し得るコストを
  render count / commit duration / recomputation / bundle size / canvas or image sync work /
  list or grid update / queue or timer churn のどれかで短く示す。
- 広い好みや一般論は避け、変更する価値がある具体的な対象だけを報告する。
- product/UI の挙動変更は実行・提案しない。
```

分割監査用の追記例:

```text
Expected baseline:
- `git rev-parse --short HEAD` は `<expected short sha>` であること。
- `git status --short` は空であること。
一致しない場合は `BLOCKED: baseline mismatch` とだけ報告して停止してください。

このサブエージェントの担当範囲:
- <scope name>
- <files/directories>

Final response must be exactly:
Baseline: HEAD <short-sha>
Status: clean
NO_FINDINGS

If and only if you find actionable issues, replace `NO_FINDINGS` with numbered findings.
```

## Triage

`NO_FINDINGS` の場合:

- 単一監査なら最終検証を実行する。
- 分割監査なら、全スコープが最新 clean HEAD で `NO_FINDINGS` を返していることを確認してから最終検証を実行する。
- 作業ツリーが clean であることを確認する。
- Final Report を作って完了する。

Findings がある場合:

- メインセッションで全件を確認する。
- 機能変更を伴う提案は採用しない。採用しない場合は理由を記録する。
- 採用できる具体的な refactor target は、同一ループ内で全て修正する。
- 各 finding を `performance-sensitive` または `non-performance-sensitive` に分類する。
- 分類はサブエージェント出力を参考にするが、最終判断はメインセッションで行う。

## Performance Measurement Gate

この Gate は **必要な場合だけ** 実行する。リファクタリングのたびに常時実行しない。

### Gate を通す条件

以下のいずれかに該当する場合は、原則として一時 instrumentation で before / after を測る。

- render 回数、React commit duration、state churn に影響しそうな変更
- state / context / selector / memo / callback / component boundary の変更
- list / grid / card / table / canvas / image preview / hover / drag / queue update / timer に関わる変更
- route split / lazy import / bundle size に関わる変更
- large object state、large data URL、image encode/decode、canvas `getImageData` / `putImageData` / `toDataURL` に関わる変更
- レポートで「速くなる」「再描画が減る」「bundle が分離される」と主張する変更

### Gate を省略してよい条件

以下だけの変更なら、通常は計測なしでよい。

- 型定義整理、命名整理、局所的なファイル分割
- runtime behavior がほぼ変わらない責務整理
- テスト追加、dead code 削除、import 整理
- 文言や軽微なスタイル整理
- 性能改善を主張しない保守性中心の変更

### 計測ルール

- 計測コードは一時差分にする。コミットしない。
- 可能なら before と after を同じ操作手順・同じ fixture / stub / mock で測る。
- 実 API 呼び出し、課金、外部副作用は避ける。dev-only fixture / stub を優先する。
- React の `<Profiler>`、`performance.mark/measure`、browser automation、build output など、対象に合う最小の計測を使う。
- 計測対象は仮説に合わせて絞る。全画面を重く計測しない。
- after 計測後、必ず instrumentation を削除し、`git status --short` で一時差分が残っていないことを確認する。
- 計測できない場合は、理由と代替検証、未実測リスクを記録する。

### 推奨計測項目

| 対象 | 主な指標 |
|---|---|
| render hot path | render count、commit duration、対象外 component の再描画数 |
| selector / derived state | 再計算回数、commit duration、不要 state update の有無 |
| list / grid / card | 更新対象以外の item render 数、interaction ごとの commit duration |
| queue / timer | tick ごとの render count、対象外 item render 数、state churn |
| canvas / image | `getImageData` / `putImageData` / encode 回数と duration、stroke 中の同期処理 |
| route split / lazy import | route chunk、lazy chunk、shared chunk、initial chunk 混入 |

## 修正

修正時のルール:

- 既存の component API、state 管理、routing、CSS、test helper に合わせる。
- 大きな抽象化や依存追加は避ける。
- 変更範囲は、サブエージェント finding とその直接周辺に絞る。
- memo / callback / selector / lazy import は、実際の更新範囲や再計算を狭める場合だけ使う。
- 既存挙動を変えない。表示文言、イベント順、送信 payload、保存形式、URL、外部 API 呼び出しは維持する。
- Performance Measurement Gate 対象のループでは、修正前後の測定手順を途中で変えない。

## 検証

各修正ループ後に、変更内容に合う検証を実行する。

優先順:

1. typecheck
2. 対象ファイル lint
3. 対象テスト
4. 必要に応じて build / browser check
5. Performance Measurement Gate 対象なら after 計測結果と計測コード削除確認

検証できない場合は、理由と未検証リスクを明記する。

## simple-add

検証が通ったら、ループごとに `simple-add` を実行してコミットする。

- コミット前に `git diff --check` と `git status --short` を確認する。
- Performance Measurement Gate で追加した一時 instrumentation は、`simple-add` 前に必ず削除する。
- 計測レポート用のメモをファイルに残す場合は、ユーザーが明示した場合だけコミット対象にする。明示がなければ会話上のレポートに留める。
- unrelated なユーザー変更は含めない。
- simple-add が使えない環境では、同等の最小 git add / commit を行い、その理由を報告する。
- コミット後、次の Fresh Audit へ戻る。

## Loop Report

各修正ループの simple-add 後に、そのループでのリファクタリングレポートを短く作る。
読んだ人が「何が変わったか」「どの front-end-design-patterns 観点に基づくか」「実測または期待される性能効果は何か」「何で安全性を確認したか」を対応づけて追える形にする。

レポート作成ルール:

- 事実と推定を分ける。実測していない性能効果は「見込み」「期待」と明記し、数値を断定しない。
- Performance Measurement Gate を実施した場合は、before / after の値、操作手順、fixture / stub、計測コード削除確認を含める。
- Gate を省略した場合は、なぜ省略したかを 1 行で書く。
- 変更はユーザーが判断しやすい粒度にまとめる。ファイル差分を羅列せず、責務・更新経路・hot path 単位で説明する。
- 各変更に `front-end-design-patterns` の観点を紐づける。
- 性能効果は、render 範囲縮小、再計算削減、bundle/load 分離、state churn 低減、large object state 回避など、どのコストに効くかを書く。
- 安全性は検証コマンド、対象テスト、`NO_FINDINGS`、挙動維持のために触らなかった範囲で示す。
- 残リスクは隠さない。未実測の効果、ブラウザ未確認、プロファイル未実施などは明記する。

推奨フォーマット:

```markdown
## ループ別リファクタリングレポート

### 概要
- 対象: <対象範囲>
- ループ: <番号>
- 調査結果: <findings summary>
- コミット: <hash/message>
- 挙動変更: 意図していない

### 変更内容
| 領域 | 変更内容 | front-end-design-patterns の観点 | 性能・保守性への効果 |
|---|---|---|---|
| <file/feature> | <責務単位の変更> | <観点> | <実測済み or 期待。未測定なら expected と明記> |

### Performance Measurement Gate
- 判定: <実施 / 省略>
- 理由: <performance-sensitive 判定 or 省略理由>
- 手順: <操作、fixture、stub、browser/build/profiler>
- 結果: <before/after table or 未実施理由>
- 一時計測コード: <削除済み / なし>

### 検証
- Typecheck: <command/result>
- Lint: <command/result>
- Tests: <command/result>
- Browser/build/profile: <実施結果 or 未実施理由>

### 挙動維持
- 維持したもの: <UI/API/payload/data format/event behavior など>
- 変更していないもの: <意図的に触らなかった範囲>

### 残リスク
- <未実測・未検証・将来プロファイル推奨など>
```

## Final Report

全ループ完了後、つまり最新サブエージェントが `NO_FINDINGS` を返し、最終検証と作業ツリー clean 確認が済んだら、大まとめの Final Report を作る。
Final Report は loop report の単純な貼り合わせではなく、全体の改善ストーリー、対象範囲ごとの変化、適用した pattern 群、実測済み効果と期待効果を整理する。

Final Report 作成ルール:

- まず全体結論を短く書く。`NO_FINDINGS` 到達、挙動変更なし、検証結果を先に示す。
- 変更を loop 順ではなく、機能領域 / パターン / 性能コストの観点で再分類する。
- どの `front-end-design-patterns` 観点をどこに適用したかをまとめる。
- 性能効果は「実測済み」と「期待される改善」を分ける。実測なしなら改善量を数値化しない。
- Performance Measurement Gate を実施した loop と省略した loop を分けて記録する。
- コミット一覧を含める。各コミットがどの改善グループに対応するかを短く書く。
- 最後に残リスクと、必要なら次に測るべき profiler / browser / bundle 検証を示す。

推奨フォーマット:

```markdown
## 最終フロントエンドリファクタリングレポート

### 全体概要
- 対象: <対象範囲>
- 結果: <N> 回の fresh audit loop 後に NO_FINDINGS
- 挙動変更: 意図していない
- 検証: <typecheck/lint/test/build/browser summary>
- 性能計測: <実施した Gate 数 / 省略した理由 summary>

### 改善テーマ
| テーマ | 変更領域 | front-end-design-patterns の観点 | 効果 |
|---|---|---|---|
| <例: render hot path isolation> | <対象> | <観点> | <実測済み or 期待。未実測なら expected と明記> |

### 実測済み性能結果
| 対象 | 手順 | before | after | 判断 |
|---|---|---:|---:|---|
| <render/bundle/canvas/etc> | <measurement procedure> | <値> | <値> | <解釈> |

### 未実測だが期待される改善
| 対象 | 期待される効果 | 未実測理由 |
|---|---|---|
| <target> | <expected effect> | <why not measured> |

### 変更領域
| 領域 | 主な変更 | なぜ安全・高速・保守しやすいか |
|---|---|---|
| <route/component/hook> | <大きな変更点> | <効果と挙動維持理由> |

### ループ履歴
| ループ | 調査結果 | Performance Gate | コミット | 検証 |
|---|---|---|---|---|
| 1 | <findings summary> | <実施/省略> | <hash/message> | <passed commands> |

### パターン適用範囲
- Container/presentational boundary: <適用箇所 or 該当なし>
- Pure selectors/hooks: <適用箇所 or 該当なし>
- Render hot path isolation: <適用箇所 or 該当なし>
- Stable dependencies: <適用箇所 or 該当なし>
- Derived state / recomputation cleanup: <適用箇所 or 該当なし>
- Module boundary / lazy loading: <適用箇所 or 該当なし>

### 検証詳細
- <commands and results>

### 挙動維持
- 維持した UI/API/payload/data format/event behavior: <summary>
- 意図的に変更しなかった範囲: <summary>

### 残リスク / 追加計測候補
- <未実測の性能効果、ブラウザ未確認、Profiler 推奨など>
```

## Freshness Guard

2ループ目以降は特に以下を守る。

- 前回ループの変更適用状況は最初に軽く sanity check させる。ただし、これは主作業ではなく、「前回修正が同種の問題を残していないか」の確認に限定する。
- 主作業は、`front-end-design-patterns` の観点を改めて使った対象範囲全体の網羅的 fresh re-audit にする。
- 2ループ目以降は、前回とは違う観点も含めて container/presentational、pure selectors/hooks、render hot paths、stable dependencies、derived state、module boundaries、lazy loading/code splitting、不要再計算などを再チェックさせる。
- 「前回 findings が直ったか」だけを確認させない。
- サブエージェントに、現 HEAD の対象範囲を再読込して新しい探索をさせる。
- プロンプトには前回の修正内容を必要以上に渡さない。必要なら touched files / commit hash 程度に留める。
- メインセッションは過去 findings に固執せず、最新サブエージェント出力だけを次の修正対象にする。
- Performance Measurement Gate の実施有無も毎ループで改めて判定する。前回測ったから今回も不要、または前回不要だったから今回も不要、とは扱わない。
- 分割監査を使った場合、1 スコープの `NO_FINDINGS` だけで完了扱いにしない。全スコープが同じ最新 clean HEAD を確認した `NO_FINDINGS` を返しているかを完了条件にする。

## 完了条件

- 最新サブエージェント、または分割監査の全スコープが `NO_FINDINGS` を返している。
- 各 `NO_FINDINGS` は同じ最新 clean HEAD と空の `git status --short` を確認済みである。
- 最終検証が通っている、または未実施理由が明確。
- Performance Measurement Gate 対象の一時 instrumentation が残っていない。
- 修正済みループは `simple-add` 済み。
- 作業ツリーが clean。
- 最終報告に Final Report を含め、実施した検証、最後のサブエージェント結果、コミット有無、性能計測の実施/省略理由を含める。
