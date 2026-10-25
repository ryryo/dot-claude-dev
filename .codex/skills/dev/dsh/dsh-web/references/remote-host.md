# Desktopに表示したRemote Hostの接続と操作

手元の公式DSH Desktop＋ds-harness-remoteから、Linux等の既存DSH Hostを開く構成用。画面を描くClientと、会話・workspace・モデル・実行を所有するHostを区別する。Remote表示中も元の同じHost／sessionを操作し、別webやheadlessを新規起動しない。

## 操作先を先に合わせる

1. 画面のRemote Host名、workspaceの実path、必要ならsession IDを確認する。ローカルDesktopの同名workspaceと、Linuxの`/data/dev/...`は別物。
2. MCPを使うなら、そのendpointがどのHostに接続するかを照合する。現行`@ryryo/dsh-desktop-mcp`は`desktop` profileと同じOSユーザーのloopbackに結び付く。`runtime: existing-desktop`はMac側Hostへの接続成功を示し、画面で選んだRemoteへ追従する証拠ではない。
3. Remote Host自身の既存webに正規アクセスできる場合は、そのLinux上で同梱`dsh_web.py`を使う。同じHostのRPCであり、手元のDesktopをWeb版へ置き換える操作ではない。画面操作を指定された場合はDesktopのRemote画面を使う。
4. 読取でHostのworkspace／cwd・session IDを照合してから書き込む。MCPへの送信が結果不明なら、RPCへ切り替えて同じ指示を新IDで送らない。

母艦の起動・SSH・serviceの準備は[Instabox開発母艦](../../../instabox-dev-experiment/SKILL.md)。非InstaboxでもこのHost選定と同じRPC契約を使える。

## 母艦上の認証済みRPC

既存の起動URLを[接続と認証](connection.md)に従ってcookieへ交換する。URLをMacへコピーせず、SSH／Instabox execからLinux内で実行できる。次は今回のserviceとhelper配置で、**現在稼働しているPIDの既知unitログだけ**から起動URLをメモリに読み、session一覧のID・title・cwdだけを最大20件表示する例。

```sh
instabox exec MACHINE --stdin --json -- python3 - <<'PY'
import json, re, subprocess, sys
sys.path.insert(0, '/data/dev/dot-claude-dev/.codex/skills/dev/dsh/dsh-web/scripts')
from dsh_web import Client
unit = 'spool-dsh.service'
pid = subprocess.check_output(
    ['systemctl', 'show', unit, '--property=MainPID', '--value'], text=True).strip()
if not pid.isdigit() or int(pid) == 0:
    raise SystemExit('Target DSH service is not running')
log = subprocess.check_output(
    ['sudo', '-n', 'journalctl', '-u', unit, '_PID=' + pid, '--no-pager', '-o', 'cat'], text=True)
urls = [url for line in log.splitlines() if 'dsh web:' in line
        for url in re.findall(r'http://127\.0\.0\.1:3080/\?token=[A-Za-z0-9_-]+', line)]
if not urls:
    raise SystemExit('No current launch URL for the specified Host')
client = Client('http://127.0.0.1:3080', urls[-1])
result = client.rpc('session/list', {'_request': {}})
print(json.dumps([{k: row.get(k) for k in ('sessionId', 'title', 'cwd')}
                  for row in result['items'][:20]], ensure_ascii=False))
PY
```

unit・port・helper pathは対象Hostの実値へ合わせる。sudo権限がなければ、本人が利用できるそのHostの起動ログ／非公開auth-fileまたは正規Remote画面を使う。cookie・署名鍵・モデル資格情報の抽出や保護の無効化で補わない。例外処理でもlog全文・起動URLを出さない。

会話の読取・作成・送信・待機は[読取と操作](operations.md)のhelperを使う。新規作成／promptのreceiptは対象machine・Host・sessionに対応する保存先へ置き、応答不明は同じreceiptで照合する。`Client.rpc`を直接使う上の例は読取用であり、再送管理のないprompt送信用には広げない。

## 認証とモデルはHostごとに確認する

| 対象 | 確認すること |
| --- | --- |
| Remoteアカウント | Desktop Clientが正しいアカウントへログインし、対象Hostを選べる |
| 母艦のRemote登録 | そのLinux Hostが登録・Onlineになり、許可された操作を受けられる |
| Codex CLI | 母艦の`codex login status`。DSH providerへのサインイン成功とは別 |
| DSHモデルprovider | 母艦自身の正規認証status、route設定、`session/modelCatalog`と失敗一覧 |

provider statusにアカウント情報が含まれる場合、必要なsignedIn／routeConfigured等だけを報告する。device codeは現在進行中の正規フローのものだけを使い、期限切れのcodeを繰り返し入力させない。Remote接続の成功とモデル推論の成功も区別する。

モデル設定を依頼された場合は、対象Hostの実カタログと`settings/describe`でnamespace・revisionを読み、公開APIで更新して再読取する。必要なら公開のモデル定義だけを渡し、Macの認証・Fast設定・権限をまとめてコピーしない。接続・読取の依頼だけで既定モデルを変えない。

## 切断からの復帰

母艦の休止／稼働→既存DSH service→Remote HostのOnline→Desktopの選択先・認証→workspace／sessionの順に確認する。Linuxのserviceが稼働していれば、Client側の再接続中表示だけで再インストール・VM再起動を行わない。

今回の復帰時には、Desktop側Remoteのローカル認証無効を確認し、正規Sign out→同じGitHubで再ログイン→既存Host選択で復旧した。これは該当エラー時の実例で、すべての切断への必須手順ではない。モデル認証や稼働中の会話を診断のために消さない。復帰後は同じsessionを読み、停止中の仕事を無条件で再投入しない。

確認基準：2026-10-25、DSH 0.2.1-rc.3／ds-harness-remote 0.5.18／Linux web profileとMac Desktop。[Remote実装と導入](https://github.com/liguobao/ds-harness-remote/blob/v0.5.18/docs/installation.md)、[Desktop MCP実装](../../../../../../../dsh-plugins/packages/dsh-desktop-mcp/src/host.ts)を参照。別版では利用中の実装・型で照合する。
