---
name: dsh-web
description: "DeepSeek HarnessのWeb版・公式Desktop版の会話を読む・操作する。Desktopはdsh_desktop MCPを優先し、Webは同じHostの認証済みHTTP RPCを使う。既存チャットをheadlessの別実行へ置き換えない。"
---

# DSH Web / Desktop 操作

DeepSeek Harnessの対象インスタンスへ接続し、会話を読み、依頼された操作を行う。Web版・Desktop版の明示や既存チャットの指定がなければ、公式Desktop版を既定にする。明示された接続先や既存チャットの継続はその指定を優先する。Desktopは登録済み `dsh_desktop` MCP、Webは付属RPCヘルパーを優先する。画面操作を指定された場合はその指定を優先する。

DesktopのMCPはモデル・既定モデル・承認ポリシー・sandbox設定を維持する。接続や送信の前提として `danger-full-access` や新規セッションの既定値を適用しない。権限・設定の変更自体を依頼された場合だけ、元依頼と対象版の公開APIに沿って別途扱う。RPCでの変更手順は[実行権限と新規セッションの既定値](references/operations.md#実行権限と新規セッションの既定値)を参照する。

## 接続を選ぶ

指定のない依頼はDesktopの経路から始める。ヘルパーの既定baseはWeb版の3080なので、DesktopへRPC接続するときは確認済みの同じDesktop Hostを明示する。接続できないことを理由にWeb版や別実行へ切り替えない。

| 目的 | 経路 |
| --- | --- |
| 起動中のdsh webの会話を読む・操作する | 同じwebのHTTP RPC。付属の `scripts/dsh_web.py` を使う |
| 公式Desktop版の会話を読む・操作する | `dsh_desktop` MCPを優先。[Desktop MCPスキル](references/desktop-mcp/SKILL.md)を読む。接続・未対応操作は[Desktopの接続と管理](references/desktop.md) |
| Desktop版を起動する・プラグインを管理する | アプリの起動・プラグイン画面。CLIで管理する場合は同梱CLIと `desktop` profile |
| webを立ち上げる | `dsh web --help` で現行オプションを確認し、既存プロセスとポートを確認して起動する |
| webとは別に単発実行する | `dsh headless`。既存webの操作として使わない |
| 独立した組込ランタイムを扱う | `dsh sdk` のstdio JSON-RPC。既存webへ接続するコマンドではない |

今回のDesktop MCPは公式0.2.1-rc.3のmacOS/Linux向けで、Windowsは未対応。WSLからWindowsのDesktop版を操作する場合は、先に[WSLからWindows Desktopへ接続する](references/windows-desktop-wsl.md)を読む。接続が失われた場合は同資料の[Desktop接続の再確認](references/windows-desktop-wsl.md#desktop接続の再確認)から既存rendererと認証済みRPCの可否を確認する。Windows側のPythonから同じRPCヘルパーを実行できる。WSLのloopbackへの接続失敗や画面操作ツールの初期化失敗だけで、CLI経路がないと判断しない。

Windows DesktopからWSL内のプロジェクトへ新規スレッドを作成・再開する場合は、同資料の[WSLでの作業開始](references/windows-desktop-wsl.md#dsh内の開発コマンドをwslで実行する)も適用する。最初の依頼へ同梱ヘルパーの実パス・distribution・Linux作業場所と開始確認を含め、WSLでの実行成功を確認してから開発を始める。これはこのスキル経由の起動手順であり、Desktopの標準シェルを変更する設定ではない。

Web版の初回接続・起動・401の解消には[接続と認証](references/connection.md)を読む。以下のRPC操作は対象Hostへの認証済み接続がある場合に使う。RPCは内部の型付きインターフェースであり、公開REST APIとしての互換性を前提にしない。バージョンが違う、引数が拒否される、未記載の操作を行う場合は、対象ランタイムの `typert.host.js` と型定義を確認する。

## DesktopをMCPで操作する

`dsh_desktop` のツールを見つけ、まず `dsh_status` で `runtime: existing-desktop` と対応版を確認する。以降は[Desktop MCPスキル](references/desktop-mcp/SKILL.md)を使う。同スキルと実装・導入手順の正本はdsh-pluginsリポジトリで管理し、ここにはリンクで組み込む。

会話の特定・履歴・プロジェクト指定作成・追送・管理・添付・質問/承認回答・予定実行・会話表示/分割は専用MCPツールを使う。新規会話は元依頼・cwdから対応するプロジェクトを選び、`dsh_list_workspaces` のpathを照合して `workspaceId` を指定する。既存会話の続きは同じsessionIdへ送る。`requestId` を持つ書込では事前にUUIDを保存し、受理後は待機して対象操作の完了を確認する。応答不明は同じIDで照合し、新IDの再送やRPC/画面からの同じ書込で迂回しない。

MCPツールが未接続なら[Desktopの接続と管理](references/desktop.md)で導入・登録を確認する。同梱bridge CLIが利用できれば同じHost・台帳へ接続できる。対応外・利用不能の操作はその不足を確認してから、依頼された範囲の認証済みRPCまたは画面操作を検討する。別Hostへの切替、権限変更、別DSHプロセスの起動を接続の代用にしない。

## Web / RPC経路で会話を読む

1. `list` または `search` で会話ID・タイトル・cwdを特定する。既存会話の確認のために `session/create` を呼ばない。
2. `status SESSION_ID` で実行状態と完全なprojectionを取得する。会話一覧のcached projectionを現在の状態と混同しない。
3. `read SESSION_ID` で保存済みの履歴・回答を読む。返る `throughSeq` を固定し、`hasMore` がある場合は `nextBeforeSeq` で必要な過去分を遡る。本文・tool結果が必要なら `--raw` またはファイル出力を使う。
4. 質問・完了・失敗の判断には、状態と実際のメッセージ、turn終了を合わせて確認する。`running:false` だけでは成功とは言えない。モデルの最後の回答と、実物の差分・試験結果も区別する。

具体的なコマンド、履歴の構造、状態の読み方は[読取と操作](references/operations.md)を読む。付属ヘルパーの読取は保存済みイベントのsnapshotであり、生成途中の文字は含まない。live streamが必要な場合は同資料のRemote muxの経路を使う。

## Web / RPC経路の依頼・追記・中断

- 新規チャットは、プロジェクト名を省略されても、通常は作業対象に対応するDSHのプロジェクト（ワークスペース）内へ作成する。対象は元依頼、現在の作業ディレクトリ、リポジトリの文脈から判断し、DSHの登録先と実際のcwdを照合する。複数候補があり特定できない場合だけ確認する。無関係なプロジェクトや「未分類」を既定にせず、既存の対応先があれば再利用する。
- RPCで新規作成する場合は `new` でcwdを指定し、IDを受け取って `prompt` する。cwdの指定だけでプロジェクトへの所属も設定されたとみなさず、[workspaceの操作](references/operations.md#設定workspace端末job添付)または対象プロジェクトの画面から所属を設定・確認する。既存チャットの続きなら、その履歴と未処理の指示を読んでから同じIDへ送る。履歴を引き継ぐforkは新規の空会話と区別する。
- 依頼本文には目的、対象ディレクトリ、編集範囲、合意済み設計、検証条件、終了点を含める。実装依頼を送る間は同じ対象を並行編集しない。
- `new` と `prompt` はそれぞれ別のreceiptファイルを指定する。ヘルパーは送信前にsession IDまたはprompt request IDを保存する。同じ操作の再試行では同じreceiptと同じ引数・本文を使い、応答不明を新規IDで再送しない。
- `accepted:true` は受理の証拠。実行開始・回答・成果の完成は `status` と `read` で別に確認する。ユーザーメッセージの `source.rpcId` がpromptのrequest IDに対応する。
- 通常の追記は `queue`、実行中の方向修正は `steer`。中断、保留指示の編集・削除、モデル・権限・設定の変更は、依頼された対象と範囲に合わせて実行する。中断しても未処理のqueueは削除されない。
- 質問待ちでは質問本文・call IDを読み、専用の `userQuestions/answer` を使う。通常promptのqueueを質問への回答として扱わない。

送信だけ、調査だけ、実装と回収まで等、依頼された終了点を守る。スキルを作成・確認する依頼から実装ジョブを起動しない。モデルや権限は利用者の指定・継続許可に従い、送信の都合だけで変更しない。`session/selectModel` はprofileの既定値保存も伴う。

## 複数セッション作成後の標準配置

複数セッションを作成した後は、追加の指定がなければ今回作成した ID を作成順に dsh-docking-layout で横並びに表示する。Desktopでは `dsh_list_desktop_windows` で対象clientIdを確認し、`dsh_arrange_sessions` の完了応答と画面を確認する。Webでは[セッション配置スキル](references/session-layout/SKILL.md)の付属スクリプトと表示確認手順を使う。配置対象として指定された既存会話も ID で渡せる。対象外の実行中会話を自動追加せず、既存配置と内部比率を保ち、再実行でタブや分割を重複させない。

これはセッション作成成功後の表示手順であり、Host の起動・認証・権限設定をやり直さない。配置のためにモデル・権限・sandbox を変更しない。今回は配置不要などの利用者指定や、適用先 AGENTS.md のリポジトリ固有の上書きは優先する。スキルとスクリプトの正本は dsh-plugins リポジトリで管理し、ここにはリンクで組み込む。

## 実装依頼後の定期監視

この利用者向けの実装委譲では、送信だけ・監視不要などの指定がなければ、タイマーによる監視と必要時だけの補正を完了まで行う。間隔の指定がなければ10分ごとを既定にする。Codexでは現在のチャットに紐づくheartbeat automationを使い、対象セッションが同じ既存の監視があれば更新して重複を避ける。スキルの編集や読取だけの依頼から監視を新設しない。

- タイマーには対象Host・セッションID・cwd・元の依頼全文またはその保存先・検証条件・終了点・既存の制約を残す。各回で最新の実行状態と実際の履歴を読み、必要な差分・試験結果を元の指示と照合する。経過時間だけで停滞と決めず、cached projectionだけで現在の状態や完了を断定しない。
- 正常進行・状態不変なら、DSHへの追記も利用者への定例通知も行わない。監視のためだけに不要な指示を送らない。
- 元の指示からの逸脱、失敗手法の反復、未完なのに停止、必要な検証の放置などを具体的に確認した場合だけ、根拠と戻るべき作業を同じDSHチャットへ簡潔に送る。この範囲の補正と合意済みの質問への回答は継続許可されている。実行中は `steer`、停止後は `queue`、専用の質問には回答APIを使う。送信前に直近履歴・未処理指示・前回の補正を確認し、送信後に受理を確認して記録する。
- 補正で製品要件・公開範囲・課金・権限を増やさず、モデルを切り替えない。DSHの実装中は同じ製品ファイルを並行編集しない。追加判断や利用者の操作が必要なら、その理由を具体的に知らせる。
- 完了報告後は実差分と検証結果を元の依頼に照合する。明確な不足があれば同じチャットへ返して監視を続ける。依頼範囲の完了を確認できたら、確認結果と検証上の限界を一度報告し、監視を停止する。Codexのheartbeatは `PAUSED` に更新する。長いsleepや短間隔pollでタイマーを代用しない。

## その他の操作

Desktopの日常操作はMCPを優先する。WebまたはMCPが提供しない操作では、[読取と操作](references/operations.md)の対応表から該当するインストール済みcontrollerを調べる。設定・モデル・権限の変更や端末操作はその操作自体が依頼された場合に扱う。非streamのRPCは `call METHOD --args-file FILE` で実行できる。generated descriptorのwire引数名を保ち、すべてを `request` に包まない。

最終報告には対象チャットのcredentialを含まないURL（Desktopでリンクが得られない場合はタイトル・ID・cwd）と、取得・受理・実行・完了のうち確認できた状態を示す。操作記録にはID、cwd、receipt、必要なcursorを残し、起動tokenやcookieは残さない。
