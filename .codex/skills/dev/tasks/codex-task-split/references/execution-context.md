# 共通の実行条件・起動先・正式化

通常/大規模の権限・実ツール・モデル・環境・正本更新・Git操作の正本。担当scopeと判断経路は呼出元が持つ。成果配送は[delivery](delivery.md)、復旧と工程終了は[execution-loop](execution-loop.md)、検収は[main-review](main-review.md)へ分け、同じ手順の別版を維持しない。本書の記述自体は実行許可ではない。

## 1. 許可を引き継ぐ

実利用者指示・承諾済み計画から、対象、開始、独立chat作成、通信先、モデル/推論、Worktree/開始元、commit、公開、外部実行を確認する。スキル呼出し・提案・雛形から開始許可を作らない。承諾済み分担案は含まれる担当/worker作成と必要往復をその範囲で引き継ぐ。

同じ対象・設定・操作の許可は継続し、局所修正・検収・次工程ごとに取り直さない。個別の禁止/停止/保留は優先する。他chatの通知や一般的助言を新しい許可にも既存許可の取消しにも読み替えない。読取・送信・編集・統合・archive・課金は別で、鍵の存在は課金承認ではない。

## 2. モデルと起動方式

起動側は現在のchatを使い、新担当は利用者指定を優先する。未指定なら確認できた起動者と同じ実モデルIDを案にする。workerは指定/合意済み設定を使い、未指定の提案ではgpt-6-luna/maxを候補にできる。全taskへの起動義務ではない。

モデルIDと対応推論値は実hostのツール定義/一覧で確認し、表示名や自己紹介から推測しない。推論は局所low/medium、複数箇所high、契約横断xhigh、特に難しい矛盾maxを目安とし、選んだモデルの対応値と既合意を優先する。利用不能な設定/方式を別モデル・CLI・custom agent・spawn_agentへ黙って代替しない。独立chatとsubagentは別である。

修正/再開は同thread・既認可設定を維持する。送信時のmodel/thinkingは変更が必要かつ許可された場合以外省略し、道具が必須なら記録済み設定を使う。localが既定で、Worktreeは実指示/承諾済み案の指定範囲だけ。親がWorktreeにいること自体は子のWorktree許可ではない。

## 3. 実ツールを確認して起動する

実行時の露出schemaと効果を正本とする。名前が違えば同じ認可操作か照合し、存在しない引数を捏造しない。道具がなければ未実行と不足を示す。

正式な起動側ID/hostと実cwdを実chat情報や環境変数で確認する。workerの直接の報告先は指示元PM、PMの所属は呼出元の役割契約で確定する。起動元/source_thread_idだけで上位・報告先を作らない。

list_projects等で実repo/hostとprojectIdを照合する。localは指定workspace、Worktreeは指定開始元のrepoを確認する。create_threadが対応する場合は確認済みprojectId・model/thinkingと以下のenvironmentを使う。これは対応時の入力対応表であり全clientの保証ではない。

| 承認された起動条件 | 対応schemaでのenvironment |
| --- | --- |
| 指定なし/local | `{ type: "local" }` |
| Worktree、開始元未指定 | `{ type: "worktree" }`。実projectの既定branchから開始 |
| Worktreeとbranch/ref指定 | `{ type: "worktree", startingState: { type: "branch", branchName: <指定値> } }` |
| 指定checkoutの許可済みWIPを含める | `{ type: "worktree", startingState: { type: "working-tree" } }`。参照checkoutと含む変更を確認 |

target.type/projectIdなどは実schemaに従う。branchNameへ任意SHAを入れれば動くと仮定しない。未存在branchのonMissing/create-branchは、その正確な名前と作成許可がある場合だけ。既存WTは登録projectのlocalとして選べるかを確認し、任意cwd/ref引数を作らない。create_worktreeによる呼出chatへのattachは、新担当起動/cwd移動とは別。

作成前に呼出元の組立て済み本文と引数の対象・許可・設定・境界・配送経路を照合する。新workspaceが未確定ならrepo/project/開始元と返却後の確認を渡す。作成後は作業IDに正式thread/host・返却タイトル・実方式/設定・cwd/HEADを対応させ、wait_threads等の実状態で起動確認する。複数は実上限内でまとめcursorを引き継ぐ。

pending clientThreadIdを送信/待機先にせず、作成結果不明は一覧/履歴で解決してから再試行する。実設定と本文が違えば、品質と方式を分けて既成果を保持し、該当範囲を訂正する。数合わせの再起動はしない。created-thread表示は実際に成功した正式IDだけ使う。

list/read/wait等は必要な実turn・差分・状態へ絞る。completedはturn終了で採用/元ID完了ではない。commentaryが親を起こすと仮定せず、短間隔pollを常設しない。成果の自動/手動配送・必要相談・結果不明はdeliveryに従う。送信成功、親再開、検収は別。

## 4. 正本・編集と実行環境

AGENTSとREADME/実CLI helpから唯一の正本、生成表示、revision/lock/更新手順を特定する。他projectのcommand/status/optionsを流用しない。正本が読めなければ着手可能/全scope完了と断定しない。workerは共有正本を更新せず、PMが元task/check/evidence/handoffを実CLIで更新する。

実着手でclaim/in_progress相当を更新し、予約を着手済みにしない。移管は旧編集/書込終了・新担当の読取受領を確認してprojectのtransfer手順で行う。二重claim、owner横取り、依存削除、手編集迂回をしない。正当なblockには必要能力・供給者・解除条件・次工程を残す。

I/C/V等の意味はproject契約に従い、独立開発、部品成果、実能力受入、main採用、原条件/必要levelの充足を区別する。表示不一致は手編集差分を保存し、修復が依頼内なら正当なCLI生成を使う。

port・DB/物理保存・registry・profile・依存/生成物・テスト資源の専用化はproject手順を使う。共有正本をWTごとに複製せず、Git外state・鍵・Cookie・個人profileをGitや相談資料へ含めない。

## 5. 検収後の正式化とcommit

検収はmain-review、commit可否/commandは実承認とproject契約に従う。既承認のdev:simple-add等は実在手順を読んでその範囲で行い、毎回再承認を求めない。未承認を許可済みにしない。

検収済み成果を機能/責務単位でまとめ、必要前提やpatch/lockの組を揃える。既採用・後続版の成果を再commitしない。共有index/stage/commitは順番を調整し、他担当の未完・無関係な差分を巻き込まない。古いbranch全文で上書きせず意味差分を調停する。不要な行単位の所有追跡は課さない。

製品と非公開計画は指定repoへ分け、push/PR/公開/archive/課金は各許可範囲で行う。workerは原則未commitで渡す。コード採用・CLI・commit・必要配送の実施済みと残工程を区別し、途中成功を全成功としない。

## 6. 停止とarchive

停止の送信だけで終了済みにせず、編集と書込processを確認する。git clean -fdx、reset --hard、強制WT削除、未知ownerのlock除去を回収手段にしない。

Git inventoryとmanaged attachment一覧は別で、空一覧だけで成果不存在としない。archiveはexact identityKeyとprimary/pinned/shared等の制限、ignored stateの保護、現clientでのchat/WT効果を確認し、明示許可の対象だけ。自動/一括archiveを既定にしない。

## 7. 契約版の切替

文書更新だけで既存担当を作り直さない。適用projectが選ぶ現行契約の実在参照と版を確認し、安全な編集/回収境界で変更点と再開工程を引き継ぐ。許可・scope・設定・品質修正履歴・有効な証拠を保持する。未配置のGitHub版や古いpromptを現clientの現行契約とみなさない。

構造移管まで明示された場合だけ呼出元の移管契約を使う。新担当の読取、旧編集/書込終了、正当な所有移管と受領後に新担当が編集する。複数IDや残WIPを無担当にせず、claim・未回収・採用版・証拠・履歴・配送先の実対応を引き継ぐ。project契約と新構造の衝突は必要変更として分け、スキル読込みだけで上書きしない。
