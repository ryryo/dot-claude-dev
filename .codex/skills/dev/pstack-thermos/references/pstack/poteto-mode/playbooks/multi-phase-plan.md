> [Codexでの実行条件](../../../execution.md)に従う。委譲と実行は利用者の許可範囲で行う。

### 複数段階・複数PRの計画

成果は、責任者が確認欄ごとに実行し、利用者が根拠を監査できる計画である。この手順では実装しない。

1. 一、二ファイルで方針が明白なら計画を省くと伝えて止める。
2. 未決の問いは [試作](prototype.md)で調べ、ブランチ・SHA・画像を付録Aへ残す。実行では決められない製品・好みの判断だけ選択肢付きで尋ねる。
3. 許可された調査担当または直接の調査で、ファイル、慣例、テストコマンド、入口を集める。大きな本文を埋め込まず参照先を持つ。
4. 下の雛形をコピーし、すべての変数を埋める。指定がなければ作業保存先の `docs/` へ置く。見出しと小区分の順を保ち、PRごとに独立した証拠を持たせる。実行手順は `autopilot-full.md`、`autopilot-stack.md` の選択規則に従う。継続した大規模開発は `orchestrate.md`。
5. `technical-writing` と `unslop` で整える。本文は実行手順、付録は説明と参照に分ける。
6. `node <skill-root>/scripts/pstack/poteto-mode/check-plan.mjs <plan.md>` を実行し、指摘を直す。日本語と元の英語雛形を受け付ける。山括弧の変数名は検査の識別子であり、完成する計画には残さない。
7. パスと検査出力を返して止める。計画への明示的な実行指示を受けてから、記された手順で実行する。

検証規則は「テストだけでは検証は完了しない。単体・実動作・性能の確認欄がすべて埋まって初めてPRを検証済みとする。」。各検証区分の先頭に記す。実動作はPR headで十組を行い、場面、保存画像、合格条件を一組一欄にする。少なくとも一組は同じ重要場面をtrunkとheadで比較する。trunkに機能がなければその事実を記録し、新規動作と利用者が待つ終了状態を確かめる。存在しない基準結果を作らない。

性能も両側で同じ指標を出し、trunkの基準を先に測って交互に実行する。比較場面が違うなら比率を宣言せず、新規処理と終了状態へ絶対上限を設ける。操作が変わるPRは画像と動画による本人確認を採用前に行う。操作を変えないPRは `**本人確認。** なし。<PR id> は本人確認の対象外。` とし、その区分に確認欄を置かない。

操作手段は対象で選ぶ。ブラウザ・Electron・Web、CLI・TUI、モバイルに合う利用可能なスキルを探す。`control-ui` や `control-cli` はホストに存在する場合だけ使う。二面に触れるPRは両方を検証する。操作機能がなければ付録Cへ不足を記し、各実動作の駆動方法は具体的に書く。

````markdown
# <Program>の計画

<導入説明>

## 読み方

一つの確認欄が一つの作業単位を表す。各確認欄は根拠を明示する。子の確認欄は親の下位手順である。根拠が存在するときだけ確認欄を埋める。根拠はファイル、ログ、画像、テストの実行結果、SHAなど。本文は実行手順、付録は説明と記録である。

実行には `<skill-root>/references/pstack/poteto-mode/playbooks/<execution playbook>.md` を使う。<採用担当と本人確認を待つPR>

テストだけでは検証は完了しない。単体・実動作・性能の確認欄がすべて埋まって初めてPRを検証済みとする。

## 全体の確認項目

### 実行の準備

- [ ] 手順とこの計画を利用者へ示して止まる。明示的な実行指示を受けてから始める。
- [ ] 実行指示後、目的を記録する。<目的と終了条件>
- [ ] 配置済みスキルのルートから次のパスと版を解決し、監査のたびに読む。
  - [ ] `<skill-root>/references/pstack/poteto-mode/playbooks/<execution playbook>.md`
  - [ ] `<skill-root>/references/pstack/swarm/guide.md`
  - [ ] `<control skill path>`
  - [ ] `<skill-root>/references/pstack/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `<skill-root>/references/pstack/<each other leaf skill the program uses>`
- [ ] 作業中の30分ごとの監査期限を記録する。未来の無人起床には対応する自動化機能と明示的な予約依頼が必要。機能がなければ不足を報告する。
- [ ] 監査では実行手順と目的を読み直し、逸脱を修正する。進行中の担当を実際の成果で確認する。停滞担当の停止と編集所有の解除を確認してから置換する。未報告のPR作成、準備完了SHA、検証開始・終了、判定、採用、停滞への対処、障害の追加・解消、本人判断だけを短い状況報告として伝える。変化がなければ同じ報告を繰り返さない。監査のたび、報告した事項または変化なしを判断ログへ記す。
- [ ] 保留・停止の指示を受けたら全担当へ新規書き込み停止を伝える。

### 担当の開始

- [ ] 各PRへ実行手順が指定する全工程を持つ責任者を割り当てる。
- [ ] 依存PRは親の採用後に始める。積む手順の場合だけ親ブランチをbaseにする。<PR ids>
- [ ] 編集範囲を守る。<PR id or class> は `<glob>` だけを編集する。
- [ ] 操作を変える <PR ids> は画像と動画を会話で提示し、本人の確認を待ってから採用する。

### 各PRの操作

- [ ] forgeを一度解決する。既定は `gh`。`command -v origin` が成功し対象repoを解決できる場合だけ `origin pr` を一貫して使う。fallbackを記録する。`gt` は必須にしない。
- [ ] 許可された公開状態で `origin pr create --status open --base <base-branch>` または `gh pr create --base <base-branch>`。子PRは親ブランチをbaseにする。
- [ ] PR向けpushの前にrepoのlintと型検査を一回実行し、hookを有効にしてpushする。
- [ ] コミット前に利用可能な不要表現・不要コードの整理スキル、レビュー前に `no-comments` を使う。
- [ ] Bugbotとセキュリティレビューを `<skill-root>/references/pstack/poteto-mode/bugbot-triage.md` に従い扱う。
- [ ] 準備完了の報告と監視前に現在のtrunkへrebaseする。修正中はその基点を保つ。以後は採用準備、`git merge-tree` の競合、trunk由来のCI失敗の場合だけ再実行する。

### 各PRの判定と採用

- [ ] 準備完了SHAとpatchが変わる各pushで `swarm` を実行する。検査一組、下記の実動作十組、性能一組、差分と検証記録を異なる観点で読む監査二組以上を含める。主担当は採用前に記録を読む。
- [ ] 全担当が `PASS` の場合だけ問題なしとする。注記扱いでも実欠陥は責任者へ返す。新SHAには新しい判定が必要。ただし [採用手順](<skill-root>/references/pstack/poteto-mode/playbooks/shipping.md)のpatch-id規則で再利用できる結果を除く。
- [ ] <採用順とpatch-idの規則>

### 各実動作担当の起動

各担当へ正確なPR headの専用worktree、状態、ポート、保存先を用意する。自動分離を仮定しない。利用可能な並列枠内で順番に実行する。`<skill-root>/references/execution.md` に従う。

- [ ] `<head SHA>` の専用worktreeを準備しHEADと絶対パスを記録する。親の共有ツリーをcheckout・resetしない。
- [ ] <起動コマンドと準備完了の信号>
- [ ] <操作コマンドと読み取り診断>
- [ ] 画像を `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` へ保存し、報告へパスを付ける。

## <Task as a verb phrase> (<PR id>)

**依存先。** <PR id, or None.>

**対象ファイル。**

- [ ] 編集 `<file path>`。
- [ ] 作成 `<file path>`。
- [ ] 削除 `<file path>`。

**実装。**

- [ ] <One change. Name the symbol and the file.>

**観測結果。**

- [ ] <One observable result, with the exact log line or screen state.>

**単体検証。** テストだけでは検証は完了しない。単体・実動作・性能の確認欄がすべて埋まって初めてPRを検証済みとする。

- [ ] <Test file and the case it gains.> 実行 `<command>`。

**実動作検証。** テストだけでは検証は完了しない。単体・実動作・性能の確認欄がすべて埋まって初めてPRを検証済みとする。 PR headで `<swarm workers model>` による実動作10組を起動手順に従って行う。

- [ ] 組1。trunkとheadで <the same load-bearing scenario> を実行する。trunkに機能がなければ記録し、<the behavior the diff adds plus the end state the user waits for> を検証する。画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組2。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組3。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組4。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組5。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組6。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組7。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組8。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組9。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。
- [ ] 組10。<Scenario.> 画像保存 `<slug>.png`。合格条件 <predicate>。

**性能検証。** テストだけでは検証は完了しない。単体・実動作・性能の確認欄がすべて埋まって初めてPRを検証済みとする。

- [ ] 指標。<両側の指標と新規処理・終了状態>
- [ ] 測定。<The command or procedure, run at trunk and at the head, interleaved. Both sides must produce the metric.>
- [ ] 基準。trunkの <value> を先に記録する。
- [ ] 判定。<不合格になる数値と比較不能な場合の絶対上限>

**本人確認。** 採用前に利用者が確認する。

- [ ] 組 <n> の画像を `<media path>/<pr-id>-review-<slug>.png` へコピーする。
- [ ] 分離した実行環境で変更の30〜60秒の動画を撮り、`<media path>/<pr-id>-review.mp4` へ保存する。
- [ ] 画像と動画を会話で示す。採用準備完了で止まり、利用者の承認を待つ。

**採用。**

- [ ] 正確なhead SHAで主担当の問題なし判定。
- [ ] Bugbot対応済み。
- [ ] 判定後、現在のtrunkへrebaseしてpatch-id不変を確認。
- [ ] <誰がどの順に採用するか>

## 全体の終了

- [ ] 全確認欄に根拠がある。
- [ ] 実行手順が指定する報告を利用者へ返す。

## 付録A。試作の証拠

<試作で解決した問い・ブランチ・SHA・成果物と未証明の問い>

## 付録B。退けた案

<比較案と不採用理由>

## 付録C。リスク

<リスク・対応PR・監視内容>

## 付録D。参照先

<編集前の資料・howとinterrogateの対象PR・判断記録>
````

返答には計画パス、PRの依存関係、本人確認が必要なPR、試作の証明済み・未証明の範囲、検査出力を示す。

コード変更のレビューは [レビューの進行](../../../review.md)へ進む。計画・設計の反証と、実動作・性能の検証は、それぞれの対象に応じて行う。
