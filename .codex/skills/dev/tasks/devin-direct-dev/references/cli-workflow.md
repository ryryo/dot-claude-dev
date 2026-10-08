# CLIの対話と再開

ローカルとCloudのどちらで実行するかを先に決める。[公式コマンド一覧](https://docs.devin.ai/cli/reference/commands)と実際の`devin --help`を照合する。記載のないJSON出力オプションや、セッション再開の動作を推測しない。

## 前提と編集先

`command -v devin`、`devin --version`、`devin --help`を確認する。認証が必要なら`devin auth status`で確認し、保存済み認証を再利用する。MCPのサービスユーザー認証とCLI loginは別で、片方の成功から他方を成功としない。必要なlogin・導入が未完なら具体的な不足を示す。キー・tokenをprompt、引数、export、Gitへ書かない。

ローカルで作業を始める際は、実ディレクトリ、branch、HEAD、status、担当ファイルを確定する。CodexとDevinは同じファイルを同時に編集しない。Devinが処理している間、Codexは関連コードを読むか、別の担当範囲を進める。他者が作業中の変更をDevinの成果と混ぜない。リポジトリが共有mainを指定している場合は、その場所を保つ。branch切替やworktree作成は勝手に行わない。

## 一回の依頼と同じセッションでの修正

以下は、確認済みのオプションを使う例である。`task-prompt.md`には今回の作業条件を書き、非公開の作業ファイルとして扱う。`conversation.json`は書き出した会話であり、共有リポジトリに自動でcommitしない。編集場所は実行ツールの`workdir`で指定する。

```sh
# ローカルの一回目
devin -p --prompt-file task-prompt.md --export conversation.json

# ローカルの同じセッションを明示して追加指示
devin -r LOCAL_SESSION_ID -p --prompt-file feedback.md --export conversation.json

# Cloudの一回目（必要なrepo/base等は依頼で明示し、実checkoutを照合）
devin --cloud -p --prompt-file task-prompt.md

# 既存Cloudセッションへの追加指示
devin --cloud -r CLOUD_SESSION_URL -p --prompt-file feedback.md
```

`-p`の一回の応答を取得し、ローカルなら返却されたID、export、必要なら`devin list --format json`を照合してsession IDを記録する。複数セッションがある環境で`-c`の「最後のセッション」を推測して再開しない。CloudはMCPのget/get_messagesでも同じIDの状態・応答を取得できる。CLI出力を構造化されたAPI応答や完全な履歴と決めつけない。

`-p`で起動したプロセスの終了と、Cloudの実装ジョブの完了を区別する。長時間処理では実行ツールのsession IDを保持し、出力の続きを取得する。新しいDevinプロセスを重ねて起動しない。送信結果が不明なら、セッション一覧・保存済み履歴・MCPで照合する。通常の再試行は、同じセッションで具体的な失敗を修正するために行う。同じ失敗を、新規ジョブや権限の拡大で繰り返さない。

## 操作の許可とworkspace trust

[公式permissions](https://docs.devin.ai/cli/reference/permissions)とインストール版の設定を読む。`accept-edits`でもshell実行は別に確認され、`smart`も全操作の自動許可ではない。無人実行で止まることを理由に`dangerous`/`bypass`、workspace trust無効化、全体allowを既定にしない。

今回許可された編集パスと必要なコマンドに応じて、対象範囲を指定した既存のallow設定、またはACPでの許可応答を使う。実行中の質問をCodexが確認でき、元の依頼で許可されていれば、その範囲内で回答する。組織のdeny/askを迂回しない。単発作業での確認を減らすために、永続的な全体設定を変更しない。

`--sandbox`はプロセスを隔離する。すべてのedit/writeや外部送信が、同じ範囲に制限されるとは仮定しない。sandboxとpermission modeの組合せは、現行のhelpと公式文書で確認する。

## Cloudとローカルの移動

[`/handoff`と`/pickup`](https://docs.devin.ai/cli/cloud)は実行場所やPR branchを切り替え得る。同じCloudセッションをCLIで読むこととは異なる。移動が必要な場合だけ、元の許可、ローカルWIP、repo契約を確認して使う。Cloud CLIの作成・再開だけで共有treeをcheckoutしない。

`devin acp`は、[ACP対応のエディタやIDEが使うプロトコルサーバー](https://docs.devin.ai/cli/reference/commands)である。通常の対話コマンドとして使わない。APIとして使うには、初期化、セッションの作成・読込、応答の受信、操作の許可応答、終了を扱えるクライアントが必要である。本スキルには、そのクライアントを実装していない。
