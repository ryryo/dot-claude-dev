# 母艦の構築と共有スキル

既存母艦へ接続するだけなら[日常操作](operations.md)を使う。ここは新規母艦・端末追加・欠けた構成の修正用。環境固有の版・machine・service・repo commitは非公開の構築資料に記録する。

## Instaboxで作成する

`templates --json`、`usage --json`、`create --help`で実際の枠とオプションを読む。保持する開発母艦には`run`でなく`create`を使う。共通OS依存の準備は、必要な内容を確認したローカルの`bootstrap.sh`へまとめ、`--setup-file`で作成と接続する。例：

```sh
instabox create --name dev-host --template agent-browser --user dev \
  --no-vault --secrets none --meta purpose=development-host \
  --setup-file ./bootstrap.sh --json
```

scriptはsandboxの通常ユーザー・HOMEで実行される。OS導入には必要箇所でsudoを使い、秘密やdevice認証の待機をscriptへ入れない。現行setupにはサイズ・時間制限があり、失敗してもmachineが残る。返ったIDとsetup結果を保存し、失敗時はそのmachineを診断する。DSHやnative buildまで10分以内に押し込まず、後続は既存machineのexec／jobsで進める。

HOMEは`instabox exec MACHINE -- printenv HOME`で確認する。今回の`--user dev`は`/data/home`であり、`/data/home/dev`を推測して作らない。作業rootは`/data/dev`へ統一した。

## ランタイムとGit

プロジェクトのNode／pnpm pinと修正版を確認し、mise等で同じNodeをCodexとDSHへ使う。今回の検証基準はNode 26.12.1／pnpm 12.1.0／Codex CLI 0.164.0／DSH 0.2.1-rc.3。これは検証基準であって将来の最新版指定ではない。

- OS依存は対象のnative moduleで必要なものを入れる。今回使ったものはgit、gh、openssh-server、build-essential、python3、python3-venv、pkg-config、lsof、procps、util-linux、ffmpeg、libsecret-1-dev、libdbus-1-dev、rsync、ripgrep。
- CLI導入前は`umask 022`。miseのNode binと`~/.local/bin`をlogin shellだけでなく非対話SSHにも通す。今回のbashでは`.bashrc`の早期returnより前が必要だった。systemdにも固定NodeのPATHを明示する。
- npmがDSHの必要なinstall scriptを抑止した場合、失敗したnative依存を特定する。今回の固定版では`npm rebuild --global @deepseek-ai/dsh-subprocess-local node-pty koffi protobufjs --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,protobufjs`で成功した。全体の制限解除ではなく必要な対象を指定する。
- GitHub CLI、Codex CLIは母艦自身の正規device flowで本人がログインする。`gh auth setup-git`とrepo取得を確認する。Git identityは本人の指定または既存設定に合わせる。
- ソースはGit clone、またはcommit済みGit bundleを公式cpで運び、remoteを正規URLへ設定する。ローカルの未commit変更・制作state・認証ファイルは一括搬入しない。

## 共有symlinkを末端まで確認する

今回の配置は以下。製品／内部資料の3repoに加え、共有スキルの依存としてdsh-pluginsも必要。

```text
/data/dev/
  spool/.codex/skills/dev -> /data/dev/dot-claude-dev/.codex/skills/dev
  spool-internal/.codex/skills/dev -> /data/dev/dot-claude-dev/.codex/skills/dev
  dot-claude-dev/.codex/skills/dev/dsh/dsh-web/references/
    desktop-mcp -> ../../../../../../../dsh-plugins/.codex/skills/dsh-desktop-mcp
    session-layout -> ../../../../../../../dsh-plugins/.codex/skills/dsh-session-layout
  dsh-plugins/
```

各製品repoの`.claude/skills/dev`もdot-claude-devの`.claude/skills/dev`へ向ける。Codex用とClaude用は別treeなので、同名のDSHスキルが双方にあるとは仮定しない。既存設定の全setup scriptを動かしてhooks等まで変更せず、足りないリンク／依存だけ整える。既存ディレクトリや異なるリンクがある場合、`ln -sfn`で盲目的に置き換えない。

確認例はファイルの存在と解決先の読取のみ。Spoolとspool-internalの両入口から行う。

```sh
instabox exec MACHINE --stdin --json -- python3 - <<'PY'
from pathlib import Path
import json
rows = []
for repo in ('spool', 'spool-internal'):
    dev = Path('/data/dev') / repo / '.codex/skills/dev'
    for tail in ('dsh/dsh-web/SKILL.md',
                 'dsh/dsh-web/references/desktop-mcp/SKILL.md',
                 'dsh/dsh-web/references/session-layout/SKILL.md'):
        p = dev / tail
        rows.append({'path': str(p), 'exists': p.is_file(), 'resolved': str(p.resolve())})
print(json.dumps(rows))
raise SystemExit(0 if all(r['exists'] for r in rows) else 1)
PY
```

さらに末端スキルの相対参照先（MCP packageのREADME、配置スクリプト等）も実在確認する。dsh-pluginsは正本のソース配置であり、母艦のweb profileへDesktop専用MCPをインストールする意味ではない。

## DSH HostとDesktop

DSHのLinux Hostは通常ユーザーの`web` profileへ固定版Remoteを導入し、既存のsystemd unitで常駐させる。今回の成功例：

```sh
dsh plugin --profile web add -w ds-harness-remote@0.5.18
dsh plugin --profile web add -w \
  @ryryo/dsh-codex-oauth@file:/data/dev/.incoming/ryryo-dsh-codex-oauth-0.3.7.tgz \
  --ignore-scripts
```

後者のtarballは正規配布物とSHAを確認してから使う。pnpm 12.1.0では裸のtarball path指定が失敗し、`NAME@file:ABSOLUTE_PATH`で導入できた。profileのlockが参照するtarballは導入後も保持する。版が違う場合はそのpluginのREADMEとインストール済みCLIの契約を読む。

unitは実際のHOMEと固定NodeのbinをPATHへ入れ、`dsh --profile web --no-open --host 127.0.0.1`を起動する。今回の`WorkingDirectory`は`/data/dev/spool`。web profileをRemote Hostにすることと、手元をWebブラウザー版へ変更することは別。サービス名とunit全文は構築資料を正本にし、変更時は既存会話を確認する。

RemoteのHost操作許可は母艦側へ、手元Macは接続Clientとして設定する。DSHモデル認証はCodex CLI認証と別に確認し、元のモデル・権限を維持する。モデルがcatalogに不足する場合は正規settings APIとrevisionを使い、認証を含まない必要なモデル定義だけを設定する。今回のモデル／effortを無条件の新規環境既定値にしない。

会話・workspaceの作成や表示確認は[dsh-web](../../../dsh/dsh-web/SKILL.md)を使う。新しい空会話や実promptの送信を、接続診断の必須条件にしない。

## Codex Desktopと追加端末

CodexのSSH接続登録は[OpenAIのRemote connections](https://learn.chatgpt.com/docs/remote-connections#connect-to-an-ssh-host)と利用アプリの接続画面で行う。新しい仕様確認にはopenai-docsスキルを使う。既存のTailscale OpenSSH aliasとLinuxの実ディレクトリを登録し、Appのproject情報と母艦のapp-server／cwdを照合する。handoffや新規worktreeは接続登録の代用にしない。

Instabox gatewayをSSH先に使うこともできる。`ssh-config MACHINE`が生成するHost blockは既存aliasと衝突しないよう確認して登録し、短期証明書は`ssh-cert MACHINE`で更新する。Tailscale方式を使っている既存環境を、構築の都合だけでgateway方式へ移行しない。

Tailscaleは複数端末から安定した通常SSH先を共有するために使っている。公式CLIのexec／jobs／cp／port-forwardと、DSH Remote自体はTailscale前提ではない。追加Mac／Windowsも本人の端末で認証・SSH設定を作り、Macの認証ストアや秘密鍵をコピーしてセットアップしない。接続する端末の違いだけで共通テストを全件再実行せず、その端末固有の接続・表示を確認する。

一次資料：[Instabox CLI](https://instabox.sh/docs/cli.md)、[SSH](https://instabox.sh/docs/ssh.md)、[Remote導入](https://github.com/liguobao/ds-harness-remote/blob/v0.5.18/docs/installation.md)。今回の実値・画面・検証結果は非公開構築資料を参照する。
