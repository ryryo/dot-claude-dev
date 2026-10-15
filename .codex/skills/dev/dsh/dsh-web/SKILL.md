---
name: dsh-web
description: "DeepSeek HarnessのWeb版・公式Desktop版の会話や設定を操作する。対象インスタンスを特定し、認証済みHTTP RPCまたはアプリ画面で読取・依頼・追記・中断を行う。既存チャットの操作をheadlessの別実行と取り違えない。"
---

# DSH Web / Desktop 操作

DeepSeek Harnessの対象インスタンスへ接続し、会話を読み、依頼された操作を行う。ユーザーが利用しているWeb版・Desktop版を優先し、認証済みRPCが利用できる場合は付属ヘルパーを使う。画面操作を指定された場合はその指定を優先する。Desktopの認証経路が得られない場合はアプリ画面を使う。

## この利用者の実行設定

2026-10-14、利用者は「今後も全部フルアクセスになるように、スキルもそうしておいて」と明示した。以後、この利用者向けに作成・実行するDSHセッションは `danger-full-access` を使い、対象Host/profileの新規セッションの既定値も同じにする。この継続許可について再確認しない。後の明示的な制限・停止は優先する。

作成・再開前に実カタログと設定を読み、[実行権限と新規セッションの既定値](references/operations.md#実行権限と新規セッションの既定値)の正規RPCで適用する。既存セッションには個別適用が必要なので、送信前に `permissions.currentValue` を確認する。OSファイル権限や認証保護は変更せず、作業範囲・公開・課金等の許可は元依頼に従う。

## 接続を選ぶ

| 目的 | 経路 |
| --- | --- |
| 起動中のdsh webの会話を読む・操作する | 同じwebのHTTP RPC。付属の `scripts/dsh_web.py` を使う |
| 公式Desktop版の会話を読む・操作する | [Desktopの接続と管理](references/desktop.md)を読む。同じHostの認証済みRPC、またはアプリ画面 |
| Desktop版を起動する・プラグインを管理する | アプリの起動・プラグイン画面。CLIで管理する場合は同梱CLIと `desktop` profile |
| webを立ち上げる | `dsh web --help` で現行オプションを確認し、既存プロセスとポートを確認して起動する |
| webとは別に単発実行する | `dsh headless`。既存webの操作として使わない |
| 独立した組込ランタイムを扱う | `dsh sdk` のstdio JSON-RPC。既存webへ接続するコマンドではない |

WSLからWindowsのDesktop版を操作する場合は、先に[WSLからWindows Desktopへ接続する](references/windows-desktop-wsl.md)を読む。Windows側のPythonから同じRPCヘルパーを実行できる。WSLのloopbackへの接続失敗や画面操作ツールの初期化失敗だけで、CLI経路がないと判断しない。

Windows DesktopからWSL内のプロジェクトへ新規スレッドを作成・再開する場合は、同資料の[WSLでの作業開始](references/windows-desktop-wsl.md#dsh内の開発コマンドをwslで実行する)も適用する。最初の依頼へ同梱ヘルパーの実パス・distribution・Linux作業場所と開始確認を含め、WSLでの実行成功を確認してから開発を始める。これはこのスキル経由の起動手順であり、Desktopの標準シェルを変更する設定ではない。

Web版の初回接続・起動・401の解消には[接続と認証](references/connection.md)を読む。以下のRPC操作は対象Hostへの認証済み接続がある場合に使う。RPCは内部の型付きインターフェースであり、公開REST APIとしての互換性を前提にしない。バージョンが違う、引数が拒否される、未記載の操作を行う場合は、対象ランタイムの `typert.host.js` と型定義を確認する。

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

送信だけ、調査だけ、実装と回収まで等、依頼された終了点を守る。スキルを作成・確認する依頼から実装ジョブを起動しない。モデルや権限は利用者の指定・継続許可に従い、送信の都合だけで変更しない。`session/selectModel` はprofileの既定値保存も伴う。

## その他の操作

ワークスペース、ファイル、設定、モデル、質問への回答、端末、job、添付の操作は[読取と操作](references/operations.md)の対応表から、該当するインストール済みcontrollerを調べる。非streamのRPCは `call METHOD --args-file FILE` で実行できる。generated descriptorのwire引数名を保ち、すべてを `request` に包まない。

最終報告には対象チャットのcredentialを含まないURL（Desktopでリンクが得られない場合はタイトル・ID・cwd）と、取得・受理・実行・完了のうち確認できた状態を示す。操作記録にはID、cwd、receipt、必要なcursorを残し、起動tokenやcookieは残さない。
