# Desktopの接続と管理

公式Electron版が対象。コミュニティ版は起動方式・profile・認証が異なる場合があるため、その配布元の資料を確認する。

## 最初に読む公式資料

- [Desktop README](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md)：構成、Terminal command、Closing the window and quitting、Installation ownership。
- [同梱CLI](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md#bundled-command-runtime)：CLIとDesktop profileの管理。
- [Web Plugin Manager](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-plugin-manager/README.md)：アプリ内のプラグイン管理。

2026-10-13に公式資料とインストール済みmacOSアプリ `0.2.0-rc.2` の同梱コード・CLI helpを確認した。Desktopへの外部RPC接続・送信は未検証。公開masterと実物に違いがあれば、対象アプリの実装を優先する。

## 対象と接続経路

WSLからWindows版へ接続するときは[Windows Desktop / WSL](windows-desktop-wsl.md)を先に確認する。Windows側のPythonと既存RPCヘルパーを使う経路を調べてから、画面操作の必要性を判断する。

アプリのバージョン、起動プロセス、Hostのlisten、使用する `DSH_HOME` を確認する。アプリが閉じていれば通常のアプリ起動を使い、接続用の `dsh web` を別に立ち上げない。Desktop profileをCLIでbootしない。

DesktopはWebと同じ会話APIを使うが、画面は `dsh-app://app/` で、アプリがHostの起動URLをcookieに交換してHTTP・WebSocketへ認証を付ける。内部IPCはアプリ所有の起動・認証経路であり、外部エージェント用の公開操作APIではない。

確認した0.2.0-rc.2のDesktop Hostは既定ポート19387を指定していた。公開masterではOS割当ポートになっている。ポート番号だけで対象を決めず、3080のWeb版へ誤接続しない。

| 利用できる経路 | 操作 |
| --- | --- |
| 対象Desktop Hostの有効な起動URLが、明示された非公開ファイル・環境変数などで利用可能 | [Web共通の認証手順](connection.md)でcookieを交換し、同じHostに `dsh_web.py` で接続。まず読取で対象を確認する |
| アプリの認証情報を外部から利用する経路がない | 利用可能なアプリ操作ツールで画面を読み、対象チャットの選択・送信・結果確認を行う |

同梱CLIは起動中アプリへの接続コマンドではない。`headless --session-id` や独立SDK実行を既存Desktopチャットの操作に代用しない。認証のための秘密鍵・cookieの抽出や偽造、保護の無効化を行わない。`dsh-app://app/` はHTTPヘルパーのbaseに使えない。利用可能な認証経路と画面操作ツールがどちらもなければ、その不足を報告する。

認証済みRPCでは[共通の読取と操作](operations.md)を使う。画面操作では実際のUIを確認し、チャットのタイトル・cwdを照合してから送信する。応答不明時は履歴を確認し、送信済みの指示を二重に送らない。

## プラグインとCLI

起動中はアプリ内の「プラグイン」画面を使う。WebとDesktopが同じ `DSH_HOME` を使っても、プラグインの構成・有効化・依存パッケージは別profileなので、Web側の導入済みプラグインが自動で有効になるとは扱わない。

CLIでDesktopのプラグインを管理する場合は、初回起動でprofileを初期化し、アプリを完全終了してから**アプリ同梱CLI**を使う。npm版 `dsh` でDesktop profileを変更しない。アプリメニューの **Manage dsh Command…** でCLIを登録できるが、既存nodenv/npm版のPATH優先順位を確認し、登録を通常のチャット操作の前提にしない。

macOSでは同梱CLIを直接指定できる。実際のアプリ設置先を確認し、以下の `DSH_DESKTOP_CLI` を合わせる。

```sh
DSH_DESKTOP_CLI='/Applications/DeepSeek Harness.app/Contents/Resources/runtime/cli/bin/dsh'
"$DSH_DESKTOP_CLI" --version
"$DSH_DESKTOP_CLI" plugin --profile desktop list
"$DSH_DESKTOP_CLI" plugin --profile desktop add /absolute/path/plugin.tgz
"$DSH_DESKTOP_CLI" plugin --profile desktop remove @scope/plugin
```

`add` / `remove` は依頼された操作だけを行い、完了後にアプリを再起動して反映を確認する。

## ウィンドウと実行状態

ウィンドウを閉じる操作とアプリの完全終了を区別する。公式Desktopはウィンドウを閉じてもHostが動作を続ける。CLIでのprofile変更前にはプロセス終了を確認する。実行中のタスクがある場合、プラグイン更新の都合で無断終了しない。

`dsh://open` はウィンドウ表示用であり、チャットへの指示送信・読取・認証の代わりにはならない。データ保存先が同じでも、Web側への切替を同一のlive Agentへの接続とは扱わない。
