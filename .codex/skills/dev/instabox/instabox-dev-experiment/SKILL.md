---
name: instabox-dev-experiment
description: "Instaboxを開発母艦にし、手元のCodexとDSH Desktopから同じLinux上のリポジトリで開発する。母艦の初期構築、接続、日常のジョブ・転送、休止からの復帰と診断に使う。"
---

# Instabox 開発母艦

コード、Codexの実行側、DSH Host、開発サーバーと試験stateをInstaboxへ置き、手元のMac／WindowsはDesktopアプリ・入力・承認・レビュー・ブラウザー確認に使う。この構成の母艦構築、接続、日常運用を担当する。

## 既存母艦から始める

元依頼と既存の非公開構築資料から、対象machine、SSH alias、リポジトリのroot、DSH service／profileを特定する。Spool環境では隣接するspool-internalの`docs/OPERATIONS/linux-development-host.md`が実値と構築記録の正本。日常操作のためにVMやDSHを作り直さない。

1. `instabox version`、`get MACHINE --json`で版と状態を確認する。CLI未導入・認証・作成・停止の基本は[instabox-core](../instabox-core/SKILL.md)を使う。
2. 自動休止からの作業再開には`instabox wake MACHINE`を使う。手動休止／停止の再開を依頼された場合は`resume`／`start`。復帰後は既存プロセスとjobを照合する。
3. 短い診断・コマンドは`instabox exec --json`、切断後も追跡する有限のbuild/testは`exec --background`と`jobs`。コードの編集・Git・検証は母艦で行う。
4. Codexは登録済みのSSHプロジェクト、DSH DesktopはRemoteで対象Linux Hostとworkspaceを選ぶ。接続済みの表示だけで実行cwdを判定せず、Linuxのpathを照合する。

コマンド・復旧の具体例は[日常操作](references/operations.md)。新規構築、端末追加、欠けた依存の整備には[構築と共有スキル](references/setup.md)を読む。

## 使う構成

| 対象 | この構成での扱い |
| --- | --- |
| Instabox | 母艦の管理・実行・転送は公式CLIを使う。自前の起動管理やジョブ台帳を先に作らない |
| 通常SSH | Codex Desktopの接続先。既存環境のTailscale上のOpenSSHを維持し、CLI操作にはInstabox gatewayも使う |
| DSH | Linuxの既存`web` profileをHostとして常駐し、手元は公式Desktop＋ds-harness-remoteを使う |
| Node | プロジェクトで固定した修正版をCodex／DSHで共用する。実不具合がないのに別runtimeを追加しない |
| Gitと共有設定 | 同じ親へ作業repoとdot-claude-dev、そのスキルが参照するdsh-plugins等を置く。リンク元から末端まで確認する |
| ブラウザー確認 | `instabox port-forward`で必要なloopback portを手元へ転送する。公開URLが必要な依頼だけ`port publish`を使う |

DSHの会話・モデル・接続先の操作には[dsh-web](../../dsh/dsh-web/SKILL.md)、Remote表示中のHost選定には[Remote Host](../../dsh/dsh-web/references/remote-host.md)を使う。Mac側のDesktop MCPが表示先のLinuxへ自動で切り替わるとは扱わない。

作業時間が確定し、その間だけ軽い定期送信を維持する依頼には[instabox-work-session](../instabox-work-session/SKILL.md)を使う。無期限のkeepaliveや、休止・復帰の反復を構築時に追加しない。

## 構築・変更の検収

- 接続経路、実効ユーザー／HOME／PATH、NodeとCLIの版、Git取得、共有スキルの解決、DSH serviceを実際の母艦で確認する。`exec`と非対話SSHの両方で、テンプレートの旧CLIではなく指定版が選ばれることを見る。
- Codex CLI、GitHub、Remoteアカウント、DSHモデルproviderは別の認証。正規フローで必要なものを確認し、接続断を一律に再ログインで直さない。
- ランタイム変更時は対象repoの正規ランナーで必要な型・lint・テスト・buildとnative依存を確認する。DesktopのHost選択・workspace・モデル表示はその画面で確認する。実promptや課金APIを確認していなければ送信成功とは報告しない。
- VM復帰、DSHサービス稼働、既存会話の続行は別々に確認する。日常の再開で意図的にVMを停止したり、Goalや停止中の仕事を自動再開したりしない。
- 認証ストア・制作DB・未commit差分を丸ごと転送しない。既存の共有main、担当差分、モデル・権限、他のジョブを保つ。母艦の開発運用とSpool製品の実行場所を混同しない。

結果は既存の構築資料へ、使える接続先、実行と検証結果、未確認、残したサービス・ジョブを追記する。machineの実効休止設定は都度読み、特定プランの上限をスキルへ固定しない。
