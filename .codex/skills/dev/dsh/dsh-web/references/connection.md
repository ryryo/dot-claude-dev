# 接続と認証

この資料はWeb版の接続手順。公式アプリ版は先に[Desktopの接続と管理](desktop.md)を読み、対象Hostと認証経路が確認できた場合にだけ、ここで説明する共通のcookie交換・RPC契約を使う。

## 既存の起動先を特定する

ユーザーが指定したURL・ポート・プロセスを優先する。未指定なら、`command -v dsh`、`dsh --version`、`dsh web --help`、該当するlistenプロセスを確認する。既定のweb URLは `http://127.0.0.1:3080/` だが、これだけで対象を確定しない。既存インスタンスを操作したい依頼では、認証のために別webを起動しない。

起動が必要なら、既存の `DSH_HOME` とprofileを維持して、希望された作業ディレクトリから `dsh web` を実行する。execの長時間プロセス用sessionを保持し、listenと読取APIの応答を確認する。起動ログにはtoken付きURLが出るため、全文を報告・転載しない。起動オプションはインストール済みCLIのhelpで確認する。

web/headless/sdkは既存のsession保存先を使えるが、profileの構成・モデル設定は別。`headless --session-id` を実行中webの会話への接続手段として使うと、writerの所有と衝突する。既存webはそのwebのRPCで操作し、保存先や認証を別環境へコピーしない。

## 起動URLをcookieへ交換する

webは起動時に発行する `/?token=...` のアクセスで、署名付きHttpOnly cookieを発行し、tokenのないURLへredirectする。RPCとWebSocketはそのcookieで認証する。Host/Origin検査を通すだけでは認証にならない。

ヘルパーは次の入力のいずれかを使い、tokenとcookieをメモリ内でだけ扱う。

| 入力 | 内容 |
| --- | --- |
| `--auth-file /private/path/launch-url.txt` | 対象インスタンスの起動URLを一行だけ入れた既存の非公開ファイル |
| `DSH_WEB_AUTH_URL` | 対象インスタンスの起動URLが既に設定された環境変数 |
| `--launch-log /exact/path/launch.log` | 対象の起動ログが特定できる場合。`dsh web:` 行と指定baseに一致する最後の起動URLだけを抽出する |

tokenそのものをコマンド引数やコードへ書かない。ログ入力は、今回操作するwebを起動した既知のログに限定する。全会話履歴・認証ファイルを広く探索する手順にしない。適切な起動URLが得られなければ、接続に不足する情報を伝える。cookieの偽造、署名鍵の抽出、認証やOrigin検査の無効化で代替しない。

baseと認証URLは同じscheme・host・portである必要がある。ヘルパーは別originへのredirectを拒否する。TLS証明書検証も維持する。HTTP 401ならプロセスの再起動・認証期限・対象baseを確認し、そのインスタンスの現在の起動URLで再接続する。

## ヘルパーの使い方

スキルのディレクトリを `$DSH_SKILL`、確認済みのcredentialなしURLを `$DSH_BASE` と置いた例。これらは秘密情報ではない。

```sh
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" \
  --auth-file /private/path/launch-url.txt list
```

環境変数に認証URLが既にある場合は `--auth-file` を省略できる。新たに値を設定するために秘密情報を含むshellコマンドを表示しない。`--launch-log` を使う場合もログ内容をstdoutへ流さない。

Pythonの標準ライブラリのみを使う。RPCごとのtimeoutは既定30秒。helperは自動再送しない。新規作成・promptはreceiptを保存してから送るため、通信結果が不明な場合も同じidentityで再試行できる。

## 内部RPCの契約

`POST BASE/api/session/list` など、namespaceとmethodを `/` でつなぐ。dot表記ではない。`Content-Type: application/json`、`Origin: BASE`、認証済みcookieを送る。

```json
{
  "type": "client-request",
  "rpcId": "transport-call-uuid",
  "method": "session/list",
  "payload": {"args": {"_request": {}}}
}
```

HTTP 200でも `result.ok:false` は失敗。成功は `result.ok:true` の `result.value` を読む。transportの `rpcId` と、promptの重複防止用 `requestId` は別identity。引数エラーで送信方法を変更する場合もpromptのrequest IDを新しくしない。

## バージョンと一次資料

2026-10-13に `dsh 0.2.0-rc.2` のインストール済みコードと、起動中webへの実接続で契約を確認した。別バージョンでの互換性は未検証。

インストール先は環境ごとに調べる。`npm root -g` が実際に `dsh` を起動するNode環境のglobal rootか確認する。nodenv shimの場合は `nodenv which dsh`、解決されたentryのsymlink、package.jsonを辿る。対象は `@deepseek-ai/dsh` とその依存の `@deepseek-ai/dsh-api-*-controller`。特定のユーザー名やNodeバージョンのパスを固定しない。

各controllerの `lib/typert.host.js` がnamespace・method・引数名・schema・streamを示し、`lib/types/` とREADMEが意味を示す。gateway/client transportの契約は `dsh-api-gateway` と `dsh-client-connection` を参照する。

送信するargsのkeyはparameterの **wire**。nameはserver側の引数名なので、lookupでは一致しない場合がある。例えば `agent` は `agentId`、`workspaceFileScope` は `workspaceFileScopeId` をwireへ渡し、値はsession ID。serverのContextやAgentオブジェクトをJSONへ入れない。

公式一次資料:

- [CLIと実行モード](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md)
- [CLI reference](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)
- [webの起動・認証](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/web-app/README.md)
- [session controller](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/api/session-controller/README.md)

公開mainの資料とインストール済みコードが違う場合は、実際に起動しているバージョンの契約を使う。

helperの修正時のローカル検証:

```sh
python3 -B -m unittest discover -s "$DSH_SKILL/scripts" -p 'test_*.py'
```

認証cookie交換、RPC envelope、HTTP 200内の業務失敗、同じreceiptでの再試行、履歴cursor・本文・終了理由を検証する。テスト用のlocalhostサーバーとfake RPCを使い、実webへ新規会話・promptを送らない。
