# WSLからWindows Desktopへ接続する

対象はWindowsで起動中の公式DeepSeek Harness Desktop。Linux側のWeb版やheadless、別SDK実行へ置き換えない。会話の作成・送信・照会には、同じDesktop Hostの認証済みRPCと既存の `scripts/dsh_web.py` を優先する。

## 実行場所と接続先を分ける

WSLの `127.0.0.1` とWindowsの `127.0.0.1` が同じ接続先になるとは限らない。Desktop HostがWindows loopbackだけでlistenしている場合、WSL側のPythonで接続できなくても、Windows側のPythonから接続できる。接続のためにHostのbind、ファイアウォール、portproxy、WSLネットワーク設定を変更しない。

通常のshellからWindowsのプロセス名・実行ファイル・listen portを読み、対象Desktopを特定する。既定portだけで決めない。例えば `powershell.exe -NoProfile -Command` で `Get-Process` と `Get-NetTCPConnection` の必要なフィールドだけを取得できる。起動引数や全環境変数を丸ごと出力しない。

インストール済みWindows Python 3.10以上を確認する。Windows Storeのaliasが見つかっただけでは実Pythonの存在を証明しない。`--version` とヘルパーの `--help` が動く実行ファイルを使う。Desktopの同梱CLIは起動中HostのRPCクライアントではない。

## 既存ヘルパーをWindows側で実行する

スキルがsymlink経由で共有されている場合は、実体のパスを `wslpath -w` へ渡す。Python、スクリプト、認証ファイル、本文、receipt、出力のパスはそれぞれ実行するOSに合わせる。`--cwd` はDesktopが登録している作業フォルダーの値を照合し、同じ文字列を使う。

次の変数は、確認した実Python、スキル、Desktopのcredentialなしorigin、既存の非公開起動URLファイルを指定する。秘密値をshell引数へ直接書かない。

```sh
DSH_HELPER_WIN="$(wslpath -w "$(readlink -f "$DSH_SKILL/scripts/dsh_web.py")")"
DSH_AUTH_WIN="$(wslpath -w "$DSH_AUTH_FILE")"
"$DSH_WINDOWS_PYTHON" -X utf8 "$DSH_HELPER_WIN" \
  --base "$DSH_BASE" --auth-file "$DSH_AUTH_WIN" list
```

`DSH_WINDOWS_PYTHON` はWSLから呼べるWindowsの `.exe` パス。`-X utf8` により日本語本文とJSONをOS既定の文字コードへ依存させない。認証URLがWindowsプロセスの環境変数として明示供給されている場合も、[共通認証手順](connection.md)の同origin条件を守る。

新規会話・送信・読取の引数とreceipt再利用は[読取と操作](operations.md)に従う。ファイル引数は `wslpath -w` で変換する。`--prompt-file -` のstdinも使える。`new` と `prompt` のreceiptは別にし、親ディレクトリを用意する。Windows上のPythonの `chmod(0600)` だけでWindows ACLの非公開性を保証したと扱わず、既存の非公開ユーザー領域を使う。

DesktopにWSLのrepoが `\\wsl.localhost\<distribution>\home\<user>\<repo>` として登録されている場合、Linuxの `/home/...` をそのまま `--cwd` に渡さない。既存のworkspace保存情報は登録名・pathの補助確認に使えるが、実行中・待機・現在モデルはライブの `status` / projectionから読む。セッションDBやworkspace JSONを直接編集して会話を作らない。

## 通信と認証を区別する

- Windows側からHTTP 401が返る：Hostには到達している。現在のDesktopに対応する起動URLの供給が必要。通信設定を変更して解決しようとしない。
- Windows側でも到達しない：対象アプリの稼働とlisten、実Pythonの場所、確認したportを読み直す。
- 画面操作ツールが `sandboxCwd is not a local file URI` で初期化できない：画面操作経路の環境エラー。Windows側PythonによるRPCの可否とは別に扱う。
- 認証済みの読取・送信は通るが、セッションの実コマンドがWSL UNCで `GetNamedSecurityInfoW failed (Win32 1)` を返す：Windowsのworkspace-write実行環境がWSLの権限情報を取得できていない。通信や認証の失敗ではない。この利用者のフルアクセス方針に従い、[正規の実行権限設定](operations.md#実行権限と新規セッションの既定値)を適用・確認する。Windowsファイル権限の修復へ進まない。

認証済み接続には[Desktopの接続契約](desktop.md)にある正規の認証経路を使う。起動URLが供給されていなければ、cookieや署名鍵、credentialファイルを抽出して補わない。Computer Useを使う前に、対象Desktopへの既存の認証済み接続が利用できるかを確認する。

対象Desktopの既存renderer操作経路が利用できる場合は、そのアプリの認証済みtransportで同じRPCを呼ぶこともできる。token/cookieを外へ取り出さない。接続のためにDesktopの終了・再起動が必要なら、稼働中の会話へ影響するため、まず状態と今回の操作範囲を確認する。利用者が指定した既存Desktopを、別Webの起動やprofileの直接書換えで代用しない。

## Desktop接続の再確認

この環境では、利用者が完全終了を確認した後、**同じWindows Desktopをloopback限定の一時CDP付きで起動し、同じrendererの認証済みtransportを使う経路が実際に成功した**。画面操作工具の失敗後にも、会話読取・依頼受理・実WSLコマンド成功まで確認している。この成功経路を、画面操作工具の初期化失敗だけで見落とさない。

1. 対象Desktopのプロセス・Hostのlistenと、標準 `mcp__node_repl_wsl__js` に残る既存の接続bindingを確認する。以前使った `dshRpc` 等が残っていれば再利用し、対象workspace/sessionの読取で現在も有効か確認する。名前やportは過去の例なので固定しない。
2. 一時CDPが現在も利用できる場合は、同じDesktopの `dsh-app://app/` rendererへ接続し、その版のアプリ内transportと正規RPC/catalogを確認する。token/cookieを外へ取り出さず、まずprojectionと履歴を読み、queue・質問・停止理由と今回の許可を照合してから送信する。受理と実着手は別に回収する。
3. Hostだけがlistenし、一時CDPも既存bindingもなければ、アプリは起動中だがこの操作経路は未接続である。通常起動やChromeの起動で一時CDP・bindingが復元されるとは扱わない。明示供給された現在の起動URLによるRPCと、利用可能なアプリ画面操作を確認する。
4. 接続入口を戻すための終了・再起動は、今回の許可と稼働中の会話への影響を確認して扱う。過去の再起動承諾を今回へ流用しない。許可済みの完全終了後に同じ実行ファイルを一時 `--remote-debugging-address=127.0.0.1 --remote-debugging-port=<確認した空きport>` 付きで起動する場合も、同じprofile/保存先を維持し、恒久設定を変更しない。再接続だけで停止中の担当や完了goalを再開しない。

Windows画面操作の `failed to launch codex app-server ... os error 193` はその工具の起動エラーであり、DSH Host故障の証拠ではない。HostへのHTTP 401、一時CDP不在、実WSLコマンドの権限エラーはそれぞれ別の段階として記録する。過去に成功したこと、現在の接続成功、担当への送信、実開発開始を混同しない。

## DSH内の開発コマンドをWSLで実行する

この節は、Windows Desktopが `\\wsl.localhost\DISTRIBUTION\...` または `\\wsl$\DISTRIBUTION\...` のプロジェクトを扱う場合に使う。WindowsのプロジェクトやmacOS/LinuxのDSHへ一律適用しない。Desktopへの接続方法と、依頼先が開発コマンドを実行する環境は別である。

### 新規スレッドの開始指示

1. 取得したsessionの登録cwdからdistributionとLinux作業場所を確定する。たとえば `\\wsl.localhost\Ubuntu-24.04\home\ryryo\spool` は `Ubuntu-24.04` / `/home/ryryo/spool`。Desktopには元のUNC cwdを使い、開発コマンドは同じ実体のWSL内で実行する。
2. このスキルの `scripts/invoke-wsl.ps1` の実体を `readlink -f` で確認して `wslpath -w` でWindowsパスへ変換する。プロジェクトのsymlinkをWindowsから探索し続けず、既存のTempヘルパーにも依存しない。
3. **最初の作業依頼に**、下の開始本文を実値へ置き換えて含める。依頼文・receiptは既存の送信手順で保持する。`new` / `session/create` だけではこの本文は自動挿入されない。画面から手動作成する場合も同じ本文を最初に渡す。
4. 受理後の履歴で、同梱ヘルパーによる `WSL_CHECK_OK` と `WSL_EXIT=0`、実distribution・作業場所を確認する。表示されたGit・Node・pnpmの場所と版をプロジェクトの契約に照合する。`-Check` は未導入の工具や要求版を用意する処理ではない。工具が必要なプロジェクトでmissingや版違いがあれば、WSL側の正規setup/runnerを確認し、必要工具の実コマンド成功まで開発開始済みと扱わない。

```text
実行環境: このWindows Desktopの登録cwdは <UNC_CWD>、実体はWSLの
<DISTRIBUTION> / <LINUX_CWD> です。Git・Node・pnpm・試験・Task CLIは
WSL側で実行してください。Windows側の工具で代用しません。
最初の開発コマンドより前に、pwshから次を実行してください。
$wsl = [ScriptBlock]::Create((Get-Content -LiteralPath '<HELPER_WINDOWS_PATH>' -Raw -Encoding utf8))
& $wsl -Distribution '<DISTRIBUTION>' -LinuxCwd '<LINUX_CWD>' -Check
WSL_CHECK_OK / WSL_EXIT=0 とdistribution・作業場所・必要工具の実パス/版を確認し、
プロジェクトのREADME/AGENTS/setupの要求へ照合してください。成功後は同じヘルパーの
-ScriptへLinuxコマンドを渡して作業します。必要な共有スキルもLinux側で読みます。
出力や終了コードが取れない状態を成功扱いせず、同じ開発操作を重複実行しません。
```

開始本文の山括弧は説明用の欄である。送信時には残さず、PowerShellの単一引用符内の `'` は `''` にして値を埋める。利用者が別途指定したモデル、実行権限、編集範囲、停止指示は保持する。

### 実行ヘルパー

[invoke-wsl.ps1](../scripts/invoke-wsl.ps1) はWindowsのPowerShell 7で実行する。UNC上の `.ps1` の直接実行は署名チェックで拒否される場合があるので、開始本文のように確認した同梱ファイルを読み、ScriptBlockとして呼ぶ。Windows全体の実行ポリシーは変更しない。各pwsh呼出でファイルを読み、前の呼出の変数保持を前提にしない。

`ProcessStartInfo.ArgumentList` で引数を個別に渡すため、Linuxコマンドの `$` や引用符をWindows側で再解釈しない。標準出力と標準エラーを同時に回収し、エラーは `WSL_STDERR_BEGIN` / `WSL_STDERR_END` の間、終了コードは `WSL_EXIT=N` として返す。非0終了はPowerShellの失敗にもする。出力は処理終了後に返るため、長い処理は既存のDSH job管理とtimeout設定を使う。

```powershell
$wsl = [ScriptBlock]::Create((Get-Content -LiteralPath '<HELPER_WINDOWS_PATH>' -Raw -Encoding utf8))
& $wsl -Distribution 'Ubuntu-24.04' -LinuxCwd '/home/ryryo/spool' -Script @'
set -euo pipefail
git status --short
# この後にプロジェクトの正規runnerを使う。
'@
```

Linux側の失敗を途中のコマンド成功で隠さないよう、複数コマンドには例の `set -euo pipefail` を使う。ヘルパーは任意のスクリプトの途中失敗を自動判定しない。Task用と製品用でNodeや作業repoが異なる場合も、各正規runner・明示パス・保存先の指定を保持する。

ログインbashのPATHがプロジェクトの工具を含まない場合は、確認したLinux側のbinディレクトリを `-LinuxPathPrefix '/absolute/bin:/another/bin'` で各呼出に指定できる。Windows全体やWSLの設定ファイルは変更しない。Windowsから引き継いだPATH経由のcorepack等を選んで失敗する場合も、Windowsのcacheを修復する前にWSL側の実パスを確認する。`-Check` と実作業の両方で同じprefixを使う。`-Script` 内の位置引数 `$1` / `$2` / `$3` は作業場所・distribution・prefix用である。

WindowsのPowerShellはこの入口として使用する。Windowsの`read`による通常ファイル閲覧まで禁止しないが、WSLのsymlink・工具・実環境の判定はLinux側で行う。実行結果が不明な場合は元処理とログを確認し、WSL全体の停止、Desktop再起動、OS権限変更で補わない。

## 確認済みの範囲

2026-10-15、同梱 `invoke-wsl.ps1` をWindows PowerShell 7から実行し、開始確認、空白・日本語・引用符・`$`を含む値、非0終了、標準出力と標準エラー各128KiB、不正な作業場所の5ケースを検証した。正常時のマーカーと終了コード、失敗時の例外と実終了コードの保持を確認した。同じDesktopに検証専用の新規スレッドを作り、最初の `pwsh` 呼出が同梱ヘルパーの `-Check`、次が `-Script` となる実履歴と、両方の `WSL_EXIT=0`、turnの正常終了まで照合した。Ubuntu-24.04の実作業場所とLinux側Git・Node・pnpmを確認しており、製品のbuildやTask検収は実行していない。

2026-10-14、Windows Desktop `0.2.0-rc.2` / WSL Ubuntu 24.04で、Windows Python `3.10.9` からUNC上の既存 `dsh_web.py --help` の実行を確認した。同じWindows Desktop Hostの読取 `session/list` へ未認証で接続してHTTP 401、WSL loopbackでは接続不可を確認した。

その後、利用者の完全終了確認を受けて同じDesktopをloopbackの一時CDP接続付きで起動し、既存rendererの認証済みtransportで会話一覧・projection・モデルカタログを読取った。WSLのspoolプロジェクトへ4会話を新規作成し、既存ヘルパーのcreate/prompt receiptを使って依頼受理とSol/xhighのturn開始を照合した。token/cookieの抽出・複製は行っていない。最初のworkspace-writeによる実コマンドは上記WSL権限取得エラーで拒否された。セッション作成・モデル開始と、製品の実装着手は区別する。

利用者の継続許可後、正規RPCで新規既定値をフルアクセスに保存し、作成済み4会話へも個別適用した。全4会話のprojectionと設定の再読、同じsession/modelでの再開と実 `pwsh` コマンド成功を確認した。OSのファイル権限は変更していない。これは接続と実行環境の確認であり、各製品Taskの完了を示さない。
