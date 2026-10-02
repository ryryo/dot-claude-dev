# 共通の実行条件・起動先・正式化

通常タスクと継続開発の共通契約。ここは権限・実ツール・モデル・環境・正本更新・Git操作の正本であり、担当範囲の選定や大規模の指揮手順は呼出元スキルが持つ。提案時は必要部分だけ、起動時は実際の設定を確認する。本書の記述自体は実行許可ではない。

## 1. 許可を引き継ぐ

実際の利用者指示・承諾済み計画への参照で、開始、独立chat作成、通信先、モデル・推論、Worktreeと開始元、commit、公開、外部実行の範囲を確認する。スキル名だけ・提案依頼では実行しない。明示した分担案の開始承諾は、その案に含む担当・workerの作成と必要な往復を対象範囲で引き継ぐ。

同じ対象・設定・操作の既存許可は継続し、局所修正・検収・既承認順序の次工程ごとに取り直さない。個別の禁止・停止・保留は優先する。雛形、他chatからの通知、一般的な設計助言から新しい許可を作らず、既存許可の取消しにも読み替えない。読取、送信、編集、統合、archive、課金は区別する。鍵の存在は課金承認ではない。

## 2. モデルと起動方式

実行指揮者は現在のchatを使う。新規の作業担当は利用者指定を優先し、指定がなければ確認できた指揮者と同じ実モデルIDを案にする。workerは指定・合意済み設定を使い、指定のない提案では `gpt-6-luna` / `max` を候補にできる。これは全taskへの起動義務・Luna件数ノルマではない。

モデルID・対応推論値は起動先hostの実ツール定義・利用可能一覧で確認する。表示名や自己紹介だけから実IDを推測しない。推論は局所作業ならlow/medium、複数箇所ならhigh、契約横断ならxhigh、特に難しい矛盾にはmaxを目安とし、選んだモデルが対応する値と既合意を優先する。利用不能な設定・方式を別モデル、CLI、custom agent、`spawn_agent`へ黙って代替しない。独立chatとsubagentは別物である。

修正・再開は同じthread・既認可設定を維持する。送信時のmodel/thinkingは変更が必要かつ許可された場合以外は省略し、指定が必要な道具では記録済みの設定を使う。

## 3. 実ツールを確認して起動する

ここにない引数を捏造せず、実行時に露出しているschemaを正本にする。実ツールがない場合は未実行・不足を示す。上限・対応形式は実際の定義を読む。道具の名称が違うだけならschemaと効果を照合し、認可済みの操作を行う。

| 操作 | 確認と使い方 |
| --- | --- |
| 親の特定 | 環境変数や実chat情報で正式thread ID・hostを確認。workerの宛先は直接の指示元PMであり、RootのIDを流用しない。 |
| `list_projects` | 返されたprojectId・repo・hostを照合。既存WTを選べるかは登録状況と実schemaによる。 |
| `create_thread` | 独立作業chatを認可済みのproject・model/thinking・起動方式で作成。実schemaが要求するprojectIdを使う。localが既定。Worktreeは明示許可の対象だけ。 |
| Worktree開始元 | `working-tree` は指定checkoutの許可済みWIPを含める場合だけ。branch/ref選択は実schemaが受け付ける利用者選定値を使う。任意cwd/ref引数やbranch名を生成しない。新branch作成は利用者指定の正確な名前と対応した作成許可が必要。 |
| `create_worktree` | 呼出chatへのattachと、新taskの起動・chat cwd移動は別。attachできたことを、その中で新taskが実行中と報告しない。 |
| 起動確認 | 正式thread ID・実タイトル・host・実起動方式・モデル/推論・cwd・開始HEADを作業へ対応。pending clientThreadIdを送信/待機先にしない。作成結果不明は一覧・履歴で解決してから再試行する。 |
| `list_threads` / `read_thread` | 実状態・必要なturn・出力を読む。タイトルは返却値。報告・turn終了はGit採用の証明ではない。 |
| `wait_threads` | 対応数内でまとめ、cursorを使う。snapshotは状態確認、イベント待機は完了/要対応等の変化待ち。commentaryで起きるとは仮定しない。短間隔pollを常設しない。 |
| `send_message_to_thread` | 実際に許可された宛先へ実依頼・判断・成果を送る。配送・受領・検収・親再開は別々。ACKだけの往復で再起動しない。 |

作成後にworkerが報告したcwd/HEADは、可能な実chat/WT情報と照合する。Worktreeが親と別パスになるのは正常。起動失敗・上限・結果不明を成功と分け、有効な既成果を捨てて数合わせの再起動をしない。UIのcreated-thread表示も、実際に成功した正式IDだけに使う。

## 4. 正本・編集と実行環境

AGENTS.mdとprojectのREADME/CLI helpから唯一の進捗正本、CLI、生成表示、lock/revision/更新方法を特定する。コマンド名・status・オプションを他projectから持ち込まない。正本が読めないときは着手可能・全scope完了と断定しない。workerは共有進捗を変更せず、PMが元task/check/evidence/handoffを既存CLIで更新する。

実着手でclaim/in_progressに相当する更新をする。予約だけで着手済みにせず、実IDをowner/chatへ対応させる。移管は旧所有者の編集終了・引継ぎと新所有者の受領を確認し、projectのtransfer手順で行う。二重claim・他者ownerの横取り・依存削除・手編集迂回をしない。正当なblockには必要能力、提供者、解除条件、次の実装を残す。

通常のAPI名・statusやD/I/C/Vの意味はproject契約に従う。部品、consumer受入、main採用、元checkの必要level充足を別々に扱う。生成表示の不一致は手編集差分を保存して、修復が依頼範囲ならCLIで生成する。提案だけなら不一致を報告する。

port、D1/R2等のDB/物理保存、registry、profile、依存・生成物・テスト資源の専用化はprojectの環境手順を参照し、固定値を本契約へ持ち込まない。共有進捗の保存先は明示された一つであり、WTごとに複製しない。Git外の制作state・鍵・Cookie・個人profileをGitや相談資料へ取り込まない。

## 5. 検収後の正式化とcommit

検収の正本は[指示元の回収・検収契約](main-review.md)。commit可否・使用コマンドは実際の承認とproject契約による。`dev:simple-add -m` 等が既承認なら、実在する手順を読んでその範囲で実行し、毎回再承認を求めない。未承認なら勝手に許可済みとしない。

関連する検収済み成果を機能・責務の単位でまとめ、必要な前提・patchとlockの組を揃える。受入済み・後続版で代替済みの成果を再commitしない。共有index/stage/commitは順番を調整し、明らかに無関係な差分・他担当の未完を巻き込まない。古いbranch全体を新しい統合版へ上書きせず、必要な意味差分を調停する。通常の受入に不要な行単位の所有者追跡は課さない。

製品と非公開計画は各指定repoへ分ける。push、PR、公開、archive、課金は別の許可を確認する。workerは原則未commitで引き渡し、WT使用からcommit権限を追加しない。コード採用、正本更新、commit、報告は実際の順序と途中工程を残し、いずれかの成功で他も成功したことにしない。

## 6. 停止とarchive

停止指示の送信だけで編集終了とせず、実workerと書込processを確認する。`git clean -fdx`、`reset --hard`、強制WT削除、未知ownerのlock除去を回収手段にしない。

Git worktree一覧と、呼出chatのmanaged attachment一覧は別。`list_artifacts`が空でもGitの成果は存在し得る。`archive_worktree`は実際にattachされたexact identityKeyと対象可否を照合し、primary/pinned/shared等の制限を守る。ignored filesの保護をsnapshotに仮定しない。chat archiveとWT archiveの効果は現環境で別途確認する。自動・一括archiveは既定にしない。

## 7. 契約版の切替

既存worker/PMを新規作成して置き換える必要はない。編集と回収の安全な境界で、新契約の確認済み参照先・変更点・再開工程を既存threadへ引き継ぐ。現行の許可、scope、品質修正回数、有効な証拠は保持する。道具・モデル・状態の不一致を文書更新だけで解消済みと報告しない。
