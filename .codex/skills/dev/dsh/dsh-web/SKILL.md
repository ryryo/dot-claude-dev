---
name: dsh-web
description: "DeepSeek Harnessのdsh webをCLI・HTTP RPCで操作する。起動、会話の検索・状態・履歴・回答の読取、新規チャット、依頼・追記・中断、ワークスペースや設定の操作に使う。起動中のwebへの操作をheadlessの別実行と取り違えない。"
---

# dsh web 操作

DeepSeek Harnessの既存webサーバーへ接続し、対象の会話を読み、依頼された操作を行う。通常はCLIと認証済みRPCを使う。dshの画面操作を指定された場合はその指定を優先する。

## 接続を選ぶ

| 目的 | 経路 |
| --- | --- |
| 起動中のdsh webの会話を読む・操作する | 同じwebのHTTP RPC。付属の `scripts/dsh_web.py` を使う |
| webを立ち上げる | `dsh web --help` で現行オプションを確認し、既存プロセスとポートを確認して起動する |
| webとは別に単発実行する | `dsh headless`。既存webの操作として使わない |
| 独立した組込ランタイムを扱う | `dsh sdk` のstdio JSON-RPC。既存webへ接続するコマンドではない |

初回の接続・起動・401の解消には[接続と認証](references/connection.md)を読む。RPCはweb内部の型付きインターフェースであり、公開REST APIとしての互換性を前提にしない。バージョンが違う、引数が拒否される、未記載の操作を行う場合は、インストール済みパッケージの `typert.host.js` と型定義を確認する。

## 会話を読む

1. `list` または `search` で会話ID・タイトル・cwdを特定する。既存会話の確認のために `session/create` を呼ばない。
2. `status SESSION_ID` で実行状態と完全なprojectionを取得する。会話一覧のcached projectionを現在の状態と混同しない。
3. `read SESSION_ID` で保存済みの履歴・回答を読む。返る `throughSeq` を固定し、`hasMore` がある場合は `nextBeforeSeq` で必要な過去分を遡る。本文・tool結果が必要なら `--raw` またはファイル出力を使う。
4. 質問・完了・失敗の判断には、状態と実際のメッセージ、turn終了を合わせて確認する。`running:false` だけでは成功とは言えない。モデルの最後の回答と、実物の差分・試験結果も区別する。

具体的なコマンド、履歴の構造、状態の読み方は[読取と操作](references/operations.md)を読む。付属ヘルパーの読取は保存済みイベントのsnapshotであり、生成途中の文字は含まない。live streamが必要な場合は同資料のRemote muxの経路を使う。

## 依頼・追記・中断

- 新規チャットの依頼なら `new` でcwdを指定し、IDを受け取って `prompt` する。既存チャットの続きなら、その履歴と未処理の指示を読んでから同じIDへ送る。履歴を引き継ぐforkは新規の空会話と区別する。
- 依頼本文には目的、対象ディレクトリ、編集範囲、合意済み設計、検証条件、終了点を含める。実装依頼を送る間は同じ対象を並行編集しない。
- `new` と `prompt` はそれぞれ別のreceiptファイルを指定する。ヘルパーは送信前にsession IDまたはprompt request IDを保存する。同じ操作の再試行では同じreceiptと同じ引数・本文を使い、応答不明を新規IDで再送しない。
- `accepted:true` は受理の証拠。実行開始・回答・成果の完成は `status` と `read` で別に確認する。ユーザーメッセージの `source.rpcId` がpromptのrequest IDに対応する。
- 通常の追記は `queue`、実行中の方向修正は `steer`。中断、保留指示の編集・削除、モデル・権限・設定の変更は、依頼された対象と範囲に合わせて実行する。中断しても未処理のqueueは削除されない。
- 質問待ちでは質問本文・call IDを読み、専用の `userQuestions/answer` を使う。通常promptのqueueを質問への回答として扱わない。

送信だけ、調査だけ、実装と回収まで等、依頼された終了点を守る。スキルを作成・確認する依頼から実装ジョブを起動しない。モデルや権限を送信の都合で変更しない。`session/selectModel` はprofileの既定値保存も伴う。

## その他の操作

ワークスペース、ファイル、設定、モデル、質問への回答、端末、job、添付の操作は[読取と操作](references/operations.md)の対応表から、該当するインストール済みcontrollerを調べる。非streamのRPCは `call METHOD --args-file FILE` で実行できる。generated descriptorのwire引数名を保ち、すべてを `request` に包まない。

最終報告には対象チャットのcredentialを含まないURLと、取得・受理・実行・完了のうち確認できた状態を示す。操作記録にはID、cwd、receipt、必要なcursorを残し、起動tokenやcookieは残さない。
