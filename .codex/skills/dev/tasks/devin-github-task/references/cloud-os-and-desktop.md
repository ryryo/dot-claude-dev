# Devin CloudのOS環境とデスクトップ検証

OS固有の動作、実IME、GUI操作、保存・再起動・複数タブの検収を含むときに読む。単純な文書照合や環境非依存の単体試験で、全OS・録画を一律に要求しない。

## 確認した対応と出典

確認日：2026-10-08。Cognitionは2026-09-15にDevin CloudのmacOS対応を発表した。同記事は既存のLinux・Windows環境にも言及している。現在の公式Computer Use資料は、3 OSのデスクトップ操作に対応すると説明している。[macOS発表](https://devin.ai/blog/devin-gets-a-mac)、[Computer Use](https://docs.devin.ai/work-with-devin/computer-use)

CloudにはOSごとのVMとsnapshotがある。`runs-on`は`default`／`linux`、`macos`、`windows`に対応する。OS別のshell・package manager・配置に合わせて準備する。Windowsは公式資料上、提供が限定的。macOSのDedicated SaaSでは有効化の相談が必要な場合がある。提供・選択可能・起動成功・検証成功を区別する。[macOS環境](https://docs.devin.ai/onboard-devin/environment/macos-support)、[Windows環境](https://docs.devin.ai/onboard-devin/environment/windows-support)

2026-10-08の実画面では、新規セッションの「設定 → 仮想環境 → ホスト型」にUbuntu・macOS・Windowsが表示された。これは選択肢の観測で、macOS／WindowsのVM起動や実IME・WSL2の検証を済ませた証拠ではない。次回も現行UI・アカウントの利用可否を確認する。ボタン名は固定selectorではない。

## 作業に合わせてOSを選ぶ

| 必要な条件 | 選ぶ環境と確認 |
| --- | --- |
| 環境非依存の処理・Linux向け動作 | 既存Linux環境を利用。別OSの保証を含めない |
| macOSのIME・ショートカット・ブラウザ・ネイティブUI | macOSセッションを選び、実入力方式・対象アプリを確認。必要なGUI経路をComputer Useで操作する |
| Windowsのパス・プロセス・ブラウザ・ネイティブUI | Windowsセッションを選び、実shell・アプリ・権限の条件を確認する |
| WSL2とWindowsの連携 | Windows環境でWSL2の実在・起動・必要な連携を確認。Linux VMやGit Bashの成功をWSL2検収へ置き換えない |
| 同じ変更を複数OSで検収 | 同じPR/headで比較し、OS別の実施・結果・未確認を残す。検証のために同じ改修のPRを重複作成しない |

起動したVMでOS・arch・Node/pnpm/Git等の実版を取得する。macOSなら`sw_vers`と`uname -m`、WindowsならPowerShellのOS情報を使い、WSLが必要なら`wsl --status`・`wsl --list --verbose`等で確認する。ブラウザ、入力方式、GUI操作の可用性も実確認する。プリインストールの版は固定と仮定しない。

macOS環境にはChrome、Apple開発ツール等が用意されるが、必要なブラウザ・実日本語IMEの設定や動作を個別に確認する。iOS Simulatorの検証と物理端末の検証は別で、VM内の性能測定を実機性能へ換算しない。コンテナを多用する場合はmacOS VMのnested virtualization制限を考慮し、必要なOS検収を維持しながら実行経路を選ぶ。[macOSの構成・制限](https://docs.devin.ai/onboard-devin/environment/macos-support)

## snapshotと準備をOS別に扱う

Linuxの成功済みsnapshotや`apt-get`スクリプトをmacOS／Windowsへ流用しない。macOSは通常zsh・Homebrew、Windowsは通常Git Bashで、blueprintの`shell: powershell`も利用できる。プロジェクト指定版・固定lockfile・隔離stateを保持する。[macOS blueprint](https://docs.devin.ai/onboard-devin/environment/macos-support)、[Windows blueprint](https://docs.devin.ai/onboard-devin/environment/windows-support)

複数OSのblueprintは、OS別コマンドなら`---`で区切るYAML文書を使い、それぞれに`runs-on`を指定する。単一blockの`runs-on`リストは同じコマンドを各OSで実行するため、実際に共通化できる場合だけ使う。新しいOSでも共有スキルrepo・リンクを別途確認する。既存LinuxのActive設定を消さず、対象OSに必要な準備だけを採用する。[OSごとのsnapshot](https://docs.devin.ai/onboard-devin/environment/macos-support)

macOSセッションのsleep/wakeではディスク状態が保持される一方、稼働プロセスは再起動が必要。wake後にサーバーやwatcherが動いていると仮定せず、必要なプロセス・対象commit・隔離stateを確認する。[セッションのsleep/wake](https://docs.devin.ai/onboard-devin/environment/macos-support)

## Computer Useで実動作を確かめる

Computer UseはDevin自身のデスクトップでマウス・キーボード・画面を使う機能。CodexがDevinへ依頼するIAB操作とは別の層である。組織のDevin設定にComputer useの切替があり、変更には組織adminが必要。現状態を確認し、許可された設定変更だけを行う。検証の便宜だけで組織全体の権限・既定OS・承認設定を変更しない。[機能と有効化](https://docs.devin.ai/work-with-devin/computer-use)

Devinへ、対象アプリの起動方法、操作する経路、期待する保存前後の状態、失敗・復旧条件を具体的に伝える。必要なGUI検証が依頼範囲に含まれれば、自然言語で実行・録画を依頼するか、表示された「Test the app」等をクリックして進める。クリックを済ませたことと、対象headの実検証完了を区別する。全体のPre-approve testing設定を変える必要はない。[検証と録画](https://docs.devin.ai/work-with-devin/testing-and-recordings)

OS固有の入力を確かめるときは、本物の入力方式で操作する。`composition`イベントの注入だけを実IMEの検証にしない。macOSの⌘とWindows/LinuxのCtrl、アプリのfocus、別タブ、blur、保存中の追加入力等、対象条件に必要な交点を指定する。見た目だけでは保存・復旧・競合の成立を証明できないため、必要な保存結果・receipt・再起動後の状態も照合する。

Devinから、対象commit、OS/arch/ブラウザ/入力方式、実操作、期待と実際、必要なログ・保存状態、未実施と短い動画／画像を受け取る。録画を実際に視聴して対象操作を照合し、録画の存在だけで合格にしない。録画は主要経路の証拠であり、必要な失敗・競合試験やCIを置き換えない。[録画の工程・用途](https://docs.devin.ai/work-with-devin/testing-and-recordings)

## 更新するとき

OSやGUI機能の利用不能・仕様変更が見つかったときは、[公式資料索引](https://docs.devin.ai/llms.txt)から該当資料を再確認する。製品のCloud対応、アカウントでの提供、現在VMでの準備、実施した検収を分けて記録する。Devin Desktop／CLIの対応OSをCloud VM対応の証拠にせず、現在のUbuntuセッションだけを根拠にmacOS／Windowsの委譲を除外しない。
