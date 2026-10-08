# CLIの対話と再開

ローカル実行かCloud実行かを先に確定する。[公式commands](https://docs.devin.ai/cli/reference/commands)と実際の`devin --help`を照合し、未掲載のJSON出力flagやresumeの意味を推測しない。

## 前提と編集先

`command -v devin`、`devin --version`、`devin --help`を確認する。認証が必要なら`devin auth status`で確認し、保存済み認証を再利用する。MCPのサービスユーザー認証とCLI loginは別で、片方の成功から他方を成功としない。必要なlogin・導入が未完なら具体的な不足を示す。キー・tokenをprompt、引数、export、Gitへ書かない。

ローカルの作業開始時は実ディレクトリ、branch、HEAD、status、所有ファイルを固定する。CodexとDevinが同じファイルを同時に編集せず、Devin処理中はCodexが関連コードの読取や別の所有範囲を進める。他者のWIPを渡された成果と混ぜない。repoが共有mainを指定している場合はその場所を保持し、勝手にbranch切替やworktree作成を行わない。

## 一回の依頼と同じセッションでの修正

次は確認済みflagsを使う例。`task-prompt.md`は今回の契約を入れた非公開の作業ファイル、`conversation.json`は会話exportであり、共有repoに自動commitしない。実行ツールの`workdir`で編集場所を指定する。

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

print processが完了することと、Cloudの実装ジョブが完了することを区別する。長時間処理は実行ツールのsession IDを保持し、新しいDevinプロセスを重ねず出力の続きを取得する。送信結果が不明ならsession一覧・保存済み履歴・MCPで照合する。通常の再試行は同じsessionの具体的な失敗修正に限定し、同じ失敗を新規ジョブや権限拡大で繰り返さない。

## Permissionとworkspace trust

[公式permissions](https://docs.devin.ai/cli/reference/permissions)とインストール版の設定を読む。`accept-edits`でもshell実行は別に確認され、`smart`も全操作の自動許可ではない。無人実行で止まることを理由に`dangerous`/`bypass`、workspace trust無効化、全体allowを既定にしない。

今回許可された編集パス・必要なコマンドに応じ、既存のscope付きallowまたはACPで扱えるpermission応答を使う。実行中の質問をCodexが確認でき、元の許可があるならその範囲内で回答する。組織のdeny/askを迂回しない。永続的な全体設定を、単発作業の確認を減らすために変更しない。

`--sandbox`はprocess境界であり、すべてのedit/writeや外部送信を同じ境界に閉じ込めると仮定しない。sandbox・permission modeの組合せは現行helpと公式文書を確認する。

## Cloudとローカルの移動

[`/handoff`と`/pickup`](https://docs.devin.ai/cli/cloud)は実行場所やPR branchを切り替え得る。同じCloudセッションをCLIで読むこととは異なる。移動が必要な場合だけ、元の許可、ローカルWIP、repo契約を確認して使う。Cloud CLIの作成・再開だけで共有treeをcheckoutしない。

`devin acp`は[ACP host向けのprotocol server](https://docs.devin.ai/cli/reference/commands)で、普通の対話コマンドではない。APIとして使うなら初期化・session作成/読込・stream・permission応答・終了を扱えるclientが必要。今回のスキルにはそのclientを実装していない。
