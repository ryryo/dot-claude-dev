# 日常操作と復旧

対象名・root・serviceは既存の構築資料から読む。以下の`spool-dev`・`/data/dev/spool`・`spool-dsh.service`は今回の母艦で確認した値。別母艦ではその実値へ合わせる。

## 状態確認から作業再開

```sh
instabox get spool-dev --json
instabox wake spool-dev
instabox exec spool-dev --cwd /data/dev/spool --json -- node --version
instabox exec spool-dev --json -- systemctl is-active spool-dsh.service
instabox exec spool-dev --json -- codex login status
```

`wake`は自動休止した機械を起こす。手動休止／停止を維持するので、本人がその母艦の再開を依頼した場合だけ`resume`／`start`を使う。getの状態照会と、exec／files／SSHなど実際のアクセスによる起動を区別する。休止理由と進行中operationを見て、変更要求を重ねない。

`exec --json`のプロセス終了コードと`exitCode`・`timedOut`・`truncated`を読む。HTTP成功や空stdoutだけを成功としない。母艦内の短い診断は、SSH設定が壊れていてもInstaboxのexecから実行できる。

## 長いbuild/test

今回のSpoolなら、正規ランナーを公式background jobとして起動する。

```sh
instabox exec --background spool-dev --cwd /data/dev/spool --json -- \
  .codex/scripts/worktree-env.sh test:ci
```

返った`jobId`とmachine・cwd・目的を記録してから、実値を`JOB_ID`へ設定する。

```sh
instabox jobs logs spool-dev "$JOB_ID" --json
instabox jobs wait spool-dev "$JOB_ID" --timeout 30s --json
```

waitのtimeoutはジョブを止めない。必要なら後で同じjobを確認する。起動応答が不明なら`jobs ls spool-dev --json`で照合し、同じbuildを新規投入しない。`jobs logs -f`も可能だが、エージェントが長時間のblocking followを常用しない。DSHの起動ログにはtokenがあるので、そのログをそのままjobsやチャットへ流さない。

jobはVM内のprocess groupと`~/.instabox/jobs/`の記録であり、VM停止を越える外部schedulerではない。DSHのGoalや会話を`exec --background`へ勝手に置き換えない。常駐DSHはsystemd、有限のbuild/testはjobsに分ける。`jobs kill`は指定した自分のjobだけへ使う。

## 転送とGit

commit済みの通常共有は母艦自身のGit認証でclone／fetchする。ローカルcommitの初回搬入が必要ならGit bundleを一時ファイルへ作り、公式cpで送る。未commit差分、DB、認証を丸ごと同期する代用にはしない。

```sh
instabox cp /private/staging/source.bundle spool-dev:/data/dev/.incoming/source.bundle
instabox cp spool-dev:/data/dev/host-setup-logs/check.json ./check.json
```

`/private/staging`等は用意済みの一時保存先の例であり、存在するファイルと宛先を先に確認する。cpは片側だけ`MACHINE:PATH`、ディレクトリには`-r`、不足する宛先親の作成は`-p`。Git内のpushはtrackedのみが既定で、新しいファイルを含める`--all`は対象を確認して使う。削除済みファイルの同期はcpに任せず、今回削除した具体的なpathだけを別に扱う。

2026-10-25のCLI a41fa974ではfile stream転送になっており、旧CLIの32 MiB制限を理由にrsyncを必須にしない。転送上限・除外・上書きの意味は現行の`cp --help`／`push --help`で確認する。

## 手元ブラウザーへの非公開転送

```sh
instabox port-forward spool-dev 16006:16006
```

既定で手元の127.0.0.1へ転送し、終了時はこの転送だけを閉じる。Tailscale設定や公開portの追加は不要。サービスの初回認証URLを使う場合、originとportを維持し、tokenを資料へ書かない。Spoolは正規ランナーの`host:build`・`host --open`と通常の認証を使い、Vite portの転送だけで操作できると扱わない。公開が必要な依頼だけ`port publish`を検討する。

## 接続不良の切り分け

| 観測 | 次の確認・対応 |
| --- | --- |
| Tailscale／SSH／DSHが同時に消えた | Instaboxのgetで休止・停止・operationを確認。再開後にプロセスとjobsを照合 |
| execは通るが通常SSHが失敗 | guestのsshd、Tailscale、SSH alias・鍵・host key。gateway経由の`instabox ssh`も使える |
| gatewayの短期証明書が期限切れ | `instabox ssh-cert MACHINE`。Tailscaleの通常SSHの鍵とは別 |
| SSHは通るがDSHが見えない | 指定service・profile・listenとRemoteのHost状態。既存DSHの再起動前に稼働中会話を確認 |
| Desktopだけ再接続中 | [Remote Host](../../../dsh/dsh-web/references/remote-host.md)でClient認証・Host選択・workspaceを確認 |
| Codex CLIはログイン済み、DSHモデルは未認証 | DSH側のprovider認証を確認。CLI認証ファイルをコピーしない |
| skill入口は開くが子参照が欠ける | [共有symlinkの確認](setup.md#共有symlinkを末端まで確認する)。dot-claude-devと隣接依存を両方見る |

restartはハングしたVMをpower-cycleする復旧手段。ファイルは残るがmemory／processを失い、未flushの書込が失われ得る。単なるRemote切断への初手にしない。実効idle/max-run条件、利用量とcooldownはget／usageと現行資料で確認する。

一次資料：[CLI](https://instabox.sh/docs/cli.md)、[SSHとport-forward](https://instabox.sh/docs/ssh.md)、[休止と復帰](https://instabox.sh/docs/machines.md)。コマンド契約は2026-10-25にa41fa974のhelpと照合した。
