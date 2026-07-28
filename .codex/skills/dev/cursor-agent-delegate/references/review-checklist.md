# 検収

委任前に`git status --short`と`git branch --show-current`を記録する。既存の変更はユーザーまたは先行workerの作業として扱い、元に戻さない。

## 共通

- planの`policy_id`、work kind、difficulty、execution route、理由、owner、model/reasoningが`task-routing.json`と一致する。
- worker reportと実際のdiff・command結果・task contractが一致する。
- planning / progress、branch、remote、未許可のlockfileやgenerated fileを変更していない。
- main Codexがacceptanceに必要な検証を再実行する。

## Cursor実装

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

- difficultyが`low`または`medium`で、`cursor_required_conditions`をすべて満たす。
- 設計、shared contract、public schema、migration、中央storeを変更していない。
- diffが分離済みwrite scope内に収まり、既存変更を消していない。
- 既存pattern、参照実装、sampleのどれを使ったか確認できる。
- focused verificationがacceptanceを直接確認している。
- 範囲外判断が必要になったtaskを無理に完了扱いしていない。

## Codex subagentの補助workstream

- `allowed_work_types`のいずれかに該当し、利用する具体的な利益がplanにある。
- source diffがなく、write scopeが`none`である。
- model / reasoning、prompt、起動引数、reportが一致し、silent fallbackがない。
- 報告がevidence、conclusion、uncertainty/counterexamples、recommendationを含む。
- main Codexが主要evidenceを確認し、採用・棄却・保留を判断する。
- subagentの報告だけで設計、実装、完了判定を決めていない。

## UI / UX

`Planning policy`が`UI / UX contract: required`のときだけ適用する。

### 所有

- UI-FとUI-Iがmain所有で、Cursorにもsubagentにも渡っていない。
- Cursor taskは、UI-Fが値を確定した後の局所surface実装に限定されている。
- subagent taskはread-onlyのUI調査、比較、audit、レビューに限定され、`Mode: edit`を持たない。
- product flow、複数surface state、重要interaction判断はmainが所有している。
- product-level visual verificationをmainが確認し、behavior/data correctnessの検証と混同していない。

### task受け入れ時（`UI: surface`のtask）

**目視の前にscanを実行する。** UI-F F7で確定したS1〜S5をtaskのwrite scopeへmainが再実行し、worker reportの数値と一致することを確認する。

| # | 不合格条件 |
| --- | --- |
| S1 | design system componentを1つもimportしていないUI fileが、記録済み例外以外に存在する |
| S2 | F1に対応componentがある要素を素の`<button> <select> <input> <textarea>`で新規追加している |
| S3 | F2のallowlist外の色指定（生palette色、hardcoded hex/rgb/oklch、禁止側legacy token）がある |
| S4 | CSS frameworkが実際に出力しないutility classを書いている（classはあるがCSSが出ない＝無音で消える） |
| S5 | i18n基盤があるのに表示文字列を直書きしている |

加えて次を確認する。

- 利用者向けlabelに内部ID、enum識別子、schema field名、例外message原文が出ていない。
- F3で他taskが所有すると決めた共通surfaceを再実装していない。
- F6の配置方針から外れるsurfaceを新設していない。
- 範囲外の判断が必要になった箇所で、workerが黙って進めず停止して報告している。

### UI-I受け入れ時

- I1の横断比較表が**1つの表**として作られ、surfaceごとに節を分けていない。
- 比較軸（primary / secondary / destructive action、error、success、loading、empty、disabled、承認surfaceの構造、密度、配置）がすべて`yes`である。
- `no`の軸がある場合、`## UI foundation`の意図的な差分へ**事前に**記録されている。事後の追認は不合格。
- S1〜S5をUI変更範囲**全体**へ再実行し、0件（または記録済み例外のみ）である。task単位で通っていても統合後に再実行する。
- F6の同時表示の組み合わせを実際に発生させて確認している。
- F6の全themeと全viewportでI1の各軸が成立している。
- UI-Iのstatusが`done`か`blocked`であり、`deferred`になっていない。
- 検出済みのUI違反を後追い修正taskへ移してplanを`done`にしていない。

範囲外の変更はworker由来と断定できるものだけmainが修正する。ユーザーまたは別workerによる変更の可能性がある場合は戻さず、未検収として扱う。

検収後はmain Codexだけがplanのstatus、integration batch、decision logを更新できる。
