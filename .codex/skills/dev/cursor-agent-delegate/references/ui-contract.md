# UI契約

`Planning policy`の`UI / UX contract`が`required`のときだけ適用する。`not_applicable`のplanはこのファイルを読まない。

## 原則

planの任意記述欄は実行圧力で落ちる。UI品質を任意欄へ置かない。次の3箇所だけへ載せる。

1. **消せない実行単位**（gate task）— Status boardとtask graphに出るため省略できない
2. **task contractの`Forbidden`**— worker promptへ必ず転記される
3. **task contractの`Worker verification` / `Main verification`**— 実行可能なcommandとして残る

`Read scope`へdesign systemのpathを入れても義務にはならない。`Forbidden`と`Verification`へ書く。

## 3段構造

UI実装taskが**1つでもある**planは、次の3段をtask graphへ必ず入れる。

```
UI-F (foundation, main所有)
  └─> 各UI実装task (surface)
        └─> UI-I (integration, main所有)
```

UI実装taskが1つだけでも省略しない。1 surfaceでも既存design systemとの整合は必要であり、`UI-F`が無ければ`Forbidden`へ書く値が決まらない。

## UI-F: UI Foundation Gate

- Work kind: `design` / Difficulty: `high` / Execution route: `main` / Owner: `main-codex`
- 全UI実装taskの`Depends on`に入る
- 成果物はplanの`## UI foundation`節へ**具体値で**書き切る。抽象語で埋めない

repositoryを調査し、次の7つを確定する。値はrepository固有なので、このskillは形だけを定義し、値はUI-Fが埋める。

### F1. Component mapping

新規に作るUI要素ごとに、使用する既存componentを`import path`付きで固定する。既存componentが無い要素だけを「新規」とし、その所有taskを決める。

| UI要素 | 使用component (import path) | 新規作成 |
| --- | --- | --- |
| `<button / select / input / dialog / alert / tabs …>` | `<path>` | `no` / `yes → owner task` |

「既存design systemに従う」だけでは不足。**どのcomponentか**をpathで書く。

### F2. Token allowlist

使用してよい色・間隔・字送りのtoken名を列挙する。同義の別系統（legacy token、生palette色、hardcoded hex/rgb/oklch）を`禁止`側へ明記する。

| 用途 | 許可token | 禁止 |
| --- | --- | --- |
| 前景 / 背景 / 境界 / accent / success / warning / error / disabled | `<token>` | `<legacy token / 生palette / hardcoded>` |

repositoryに複数のtoken系統が同居している場合（移行途中など）、**新規コードがどちらを使うか**を1つに決める。両方許可しない。

### F3. 共通surface owner

複数taskが同じ意味のUIを作る箇所を先に洗い出し、**先に作るtask**を1つ決める。他taskはそれをimportする。

| 共通surface | 内容 | 所有task | 利用task |
| --- | --- | --- | --- |
| primary / secondary / destructive action | `<見た目とcomponent>` | `<task>` | `<tasks>` |
| error / refusal 表示 | | | |
| success / receipt / undo 表示 | | | |
| loading / empty / disabled | | | |
| 承認・確認surface（proposal / approval / confirm） | | | |

承認・確認surfaceが複数task間で共有される場合、これを最優先で固定する。ここが未固定だと、承認・提案・確認を扱う各taskがそれぞれ独自の承認UIを作り、同じ意味のbuttonが surface ごとに違う見た目になる。実際にこれが起きた事例がある。

### F4. Label policy

利用者向け表示に出してよい値と、出してはいけない値を決める。

- 出さない: 内部ID（UUID / clipId / targetId / requestId）、enum識別子の生表示、schema field名、例外message原文
- 出す場合の代替: 人が読める名前、序数、要約文
- 診断情報が必要な場合の置き場所: `data-*`属性、`title`、開発者向けpanelなど

### F5. i18n

repositoryにi18n基盤がある場合のみ。

- 追加先namespaceと対応locale
- 対象: 見出し、button、tooltip、`aria-label`、toast、empty / error / success / 承認 / receipt / undo
- 例外を認める箇所と理由（無い場合は`none`）
- **test側**: 表示文言でassertするtestを書かない。`data-testid`か`role`+安定keyで参照する

testが`getByRole("button", { name: "Apply" })`のように表示文言literalでassertすると、後からi18n化するときにtest修正を伴う負債になる。先に方針を決める。

### F6. Layout / theme / density

- 新規surfaceの配置方針（既存panel内 / dialog / overlay / banner）と、既存repositoryの多数派pattern
- 同時表示の上限と優先順位（複数の通知・承認surfaceが同時に出る条件）
- 対応theme（dark / light等）と、片方でしか検証しない場合の理由
- 対応viewportと文字密度

### F7. Static scan commands

**UI-Fの最重要成果物**。以降のtaskの`Worker verification`とUI-Iが実行する、repository固有のcommandを確定してplanへ書く。目視の前に機械で落とす。

最低限、次の5種を用意する。実際のcommandはrepositoryの言語・framework・path構成に合わせてUI-Fが書く。

| # | 検出対象 | 合格条件 |
| --- | --- | --- |
| S1 | 対象path配下でdesign system componentをimportしていないUI file | 0件、または理由付き例外list |
| S2 | 素の`<button>` `<select>` `<input>` `<textarea>`の新規追加 | 0件、または理由付き例外list |
| S3 | token allowlist外の色指定（生palette色、hardcoded hex/rgb/oklch、禁止legacy token） | 0件 |
| S4 | CSS frameworkが実際に生成しないutility class | 0件 |
| S5 | 表示文字列の直書き（i18n基盤がある場合） | 0件 |

S4について: token値がCSS変数などで、frameworkがopacity修飾子や派生値を解決できない組み合わせがあるrepositoryでは、classを書いてもCSSが出力されず**無音で消える**。UI-Fは対象classをframeworkに実際にbuildさせ、出力へ含まれるかを確認するcommandを用意する。目視でもtestでも検出できないため、scanが唯一の検出手段になる。

例外を認める場合は、planへ`path + 理由`で記録する。理由なしの例外を作らない。

## 各UI実装taskへ転記する固定block

UI実装task（`Work kind: implementation`かつ`UI: surface`）のcontractへ、次を**literalで**入れる。要約・言い換えをしない。worker promptへもそのまま転記する。

### Forbidden（既存のForbiddenへ追記する）

```text
- UI foundationのcomponent mappingに対応componentがある要素を、素の<button> <select> <input> <textarea>や独自実装で新規に作ること
- UI foundationのtoken allowlist外の色指定（生palette色、hardcoded hex/rgb/oklch、禁止側legacy token）
- UI foundationのF3で他taskが所有すると決めた共通surfaceの再実装
- 利用者向けlabelへの内部ID、enum識別子、schema field名、例外message原文の直接表示
- 表示文字列の直書き（i18n基盤がある場合）
- UI foundationのF6で決めた配置方針から外れるsurfaceの新設
```

### Worker verification（既存のverificationへ追記する）

```text
- UI foundation F7のS1〜S5を自taskのwrite scopeへ実行し、結果を報告する
- <focused test / build command>
```

### Final report（既存へ追記する）

```text
- 使用したcomponentとtokenの一覧
- S1〜S5の結果と、認めた例外があればpathと理由
- UI foundationから外れた箇所と、その理由
```

## UI-I: UI Design Integration Gate

- Work kind: `integration` / Difficulty: `high` / Execution route: `main` / Owner: `main-codex`
- 全UI実装taskの後段
- **surfaceを個別に確認するgateではない。surfaceを並置して差分を見るgateである**

各surfaceを個別に見る検収は各taskのAcceptanceが担う。UI-Iはtask-localなAcceptanceでは原理的に表現できない性質だけを見る。

### I1. 横断比較表

全surfaceを列に取り、同じ意味の要素が同じ見た目かを1つの表で確認する。**surfaceごとに節を分けない。分けると比較にならない。**

| 比較軸 | surface A | surface B | surface C | 一致 |
| --- | --- | --- | --- | --- |
| primary action | `<component / class>` | | | `yes / no` |
| secondary action | | | | |
| destructive action | | | | |
| error / refusal | | | | |
| success / receipt | | | | |
| loading | | | | |
| empty | | | | |
| disabled | | | | |
| 承認surfaceの構造 | | | | |
| 余白・字送り・密度 | | | | |
| 配置（panel / dialog / overlay / banner） | | | | |

`no`が1つでもあれば不合格。理由付きで意図的に変えている場合は、UI-Fの`意図的な差分`へ先に記録されていること。事後の追認を認めない。

### I2. 同時表示

F6で挙げた組み合わせを実際に同時発生させ、積み重なり・押し出し・重なり順・可読性を確認する。

### I3. Theme / viewport

F6で決めた全themeと全viewportで、I1の各軸が成立することを確認する。片方のthemeでしか見ないなら、その理由をplanへ記録する。

### I4. Scan

F7のS1〜S5をUI変更範囲**全体**へ実行し、0件（または記録済み例外のみ）を確認する。task単位のscanが通っていても、統合後に再実行する。

### I5. 合否

- **UI-Iは`deferred`にできない。`done`か`blocked`のみ**
- I1〜I4のいずれかが不合格ならplanは完了しない
- 検出済みの違反を「後追い修正task」へ移してplanを`done`にしない
- 修正を次planへ送る場合、UI-Iは`blocked`のままとし、planの完了判定を出さない

## 委任の制約

- UI-FとUI-Iはmain所有。Cursorにもsubagentにも委任しない
- Cursorへ委任できるのは、UI-Fが値を確定した後のsurface実装だけ。UI-F未完了のUI taskを起動しない
- subagentはUI調査・比較・auditのread-onlyに限る。UI実装を持たせない
- 複数UI surfaceのflowや情報設計の判断が必要になったtaskは、workerが判断せず停止してmainへ返す
