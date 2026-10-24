# 読取と操作

以下は0.2.0-rc.2の契約。`args` はRPC envelopeの `payload.args` に入る。helperの接続オプションは[接続と認証](connection.md)を参照する。

Desktopの日常操作は[Desktop MCPスキル](desktop-mcp/SKILL.md)を優先する。この資料はWeb/RPC経路やMCPが提供しない操作を、対象版の公開APIと照合して扱うための参照資料。

## 会話の検索・状態

```sh
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" list
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" list --cwd /path/to/repo
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" search '探す本文'
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" status SESSION_ID
```

| RPC | args | 用途 |
| --- | --- | --- |
| `session/list` | `{"_request":{}}` | cwd、running、blank、agentAvailableとprojectionのhint。helperは一覧を短く表示する。全項目は `list --raw` |
| `session/search` | `{"request":{"query":"本文"}}` | 可視会話の本文検索。件数はbounded、`hasMore` を全件取得と扱わない |
| `session/projections` | `{"request":{"sessionId":"ID"}}` | Agentを起動しない完全なprojection。不存在はnull |
| `session/modelCatalog` | `{}` | 利用可能モデル、既定値、providerごとの失敗 |

本文検索はdeploymentのindex設定に依存する。`openAt "never"` で検索が無効な実例では、`session/search` がHTTP 200内の `gateway/internal` を返した。これは検索結果0件ではない。`list` のタイトル・cwdから候補を絞り、必要な会話を `read` する。検索のためだけにindexやprofile設定を変更しない。

`status` は一覧の実行状態に `session/projections` の完全なbaselineを合わせて返す。別々の読取なので、同時点の原子的snapshotとは扱わない。省略されたprojectionは未提供であり、空とは限らない。

- `running` は現在の実行状態、`agentAvailable` はlive Agentの有無。coldな会話も読める。
- `inbox.next-turn` / `inbox.next-step` は未処理の指示。空だけで完了とは言えない。
- `userQuestions.active` は回答待ちの質問。本文と選択肢は取得した構造を読む。
- `modelSelection.lastUsed` は使用済み、`next` は次の要求に使う選択。未実行の会話ではnullもある。
- `plan`、`todos`、`permissions`、`goal` 等は提供されるprojectionから読む。設定変更を伴うコマンドを読取代わりに呼ばない。

終了理由は履歴の `turn/end.data.reason` で確認する。例えば `{"kind":"error","error":{"message":"WebSocket error","code":"PI_AI_ERROR"}}` は停止した失敗であり、実装完了ではない。helperの既定表示もこのreasonを保持する。

## 履歴と回答の読取

```sh
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" read SESSION_ID --max-messages 20
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" read SESSION_ID \
  --through-seq 120 --before-seq 65 --max-messages 20
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" \
  --output /private/path/history.json read SESSION_ID --raw
```

`read` は初回に完全なprojectionの `asOfSeq` を取り、次のRPCへ `throughSeq` として渡す。古い一覧のcached watermarkを使わない。明示した `--through-seq` がある場合はそのcutを維持する。

```json
{
  "request": {
    "address": {"kind":"session","sessionId":"ID"},
    "throughSeq": 120,
    "beforeSeq": 65,
    "maxMessages": 20
  }
}
```

`session/page` はcut以前の連続したイベントを時系列順で返す。`beforeSeq` は排他的な上端、`maxMessages` はイベント件数ではなくメッセージの予算。返る `records` の最小event seqを次の `beforeSeq` とし、同じ `throughSeq` で遡る。helperは `nextBeforeSeq` を計算する。`hasMore:true` でcursorが下がらなければ繰り返さず、異常を確認する。空会話のcutは-1。

helperの既定表示はuser/assistantメッセージとturn境界を抽出し、本文のtext、非text partの種類、message ID、sourceのrequest ID、seq、surfaceOpを返す。tool呼出だけのassistantメッセージもあるため、最後のassistantイベントだけを最終回答と扱わない。失敗した `assistant/attempt` も成功回答と区別する。`--raw` はtoolの引数・結果やcompact streamを含む元のrecordsを保持する。大きな結果は `--output` で保存し、必要な箇所を読む。

編集・compaction等のsurfaceイベントは単なる追加とは限らない。`surfaceOp` と `sourceEventSeqs` を確認する。既定表示はUIのsurfaceを再構築しない。置換範囲が既読のwindowより古い場合はrawで過去分を取得して意味を確認する。

過去分の読取と新しい進捗の確認を分ける。進捗を再確認するときは新たな `status` / `read` で最新cutを取得する。生成途中の文字・リアルタイムのjob出力はHTTPのsnapshotに含まれない。

## 新規作成と送信

```sh
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" new \
  --cwd /path/to/repo --title '作業名' --receipt /private/path/create.json
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" prompt SESSION_ID \
  --prompt-file /private/path/request.txt --receipt /private/path/prompt.json \
  --time-zone Asia/Tokyo
```

`new` は最初のRPC前に新しい `session-UUID` をreceiptへ保存し、`session/create` の明示的IDによる冪等なcreate/adoptを使う。cwdが返った会話と一致することを一覧で確認し、指定された場合だけrenameする。再試行では同じreceiptを使う。別のcwd・タイトルを既存receiptに混ぜない。

`prompt` は読んだ対象IDへ、次の形式で送る。本文はUTF-8ファイルまたは `--prompt-file -` のstdin。標準ではqueue。

```json
{
  "request": {
    "sessionId": "ID",
    "requestId": "stable-prompt-uuid",
    "mode": "queue",
    "content": [{"type":"text","text":"依頼本文"}],
    "clientTimeZone": "Asia/Tokyo"
  }
}
```

receiptには接続先、ID、本文のSHA-256、mode、timezone、受理状態を保存する。本文とcredentialは保存しない。通信断後は同じreceipt・同じ本文で再試行する。既にacceptedなら再送せずreceiptを返す。dshも同一request IDの未処理・保存済みpromptを重複受理しない。

受理後は `status` と `read` で開始とuserメッセージを照合する。保存済みuserメッセージの `source.kind:"user"`、`source.rpcId` がrequest IDと一致する。履歴windowに見つからない場合は必要な過去分を遡り、直近ページにないだけで再送しない。

`user/message` はeventの `data` 自体がmessage。`assistant/message` は `data.message` にmessageを持つ。自動挿入されたinstructions/runtime contextもuser/messageとして記録されるので、helperの `sourceKind` またはrawのsourceを読んで人間のpromptと区別する。

## 変更・中断

未記載のmutationも、まず対象を読んで同じIDへ行う。以下は `call` で渡すargsの例。

| RPC | args | 意味 |
| --- | --- | --- |
| `session/rename` | `{"request":{"sessionId":"ID","title":"名前"}}` | タイトル変更 |
| `session/cancel` | `{"request":{"sessionId":"ID"}}` | active turnの中断受理。queueは保持 |
| `session/updateQueue` | `{"request":{"sessionId":"ID","itemId":"MESSAGE_ID","action":{"kind":"remove"}}}` | 取得した未処理項目を削除。editはcontent、steerはkindを指定 |
| `session/selectModel` | `{"request":{"sessionId":"ID","provider":"PROVIDER","model":"MODEL","reasoningEffort":"EFFORT"}}` | live Agentを再開してモデル変更。profile既定値の保存も伴う |

```sh
python3 "$DSH_SKILL/scripts/dsh_web.py" --base "$DSH_BASE" \
  call session/rename --args-file /private/path/rename-args.json
```

`call` は自動再送・mutationのreceipt作成をしない。変更の応答が不明なら現在値を読んで確認する。fork、archive、delete、設定や権限の変更を「接続修復」のために行わない。

## 質問への回答

`userQuestions.active` からcall ID、question ID、選択肢IDを取得する。`dsh-user-questions` の `userQuestions/answer` は次のwire argsを使う。値は今回読んだ質問に合わせる。

```json
{
  "agentId": "SESSION_ID",
  "callId": "TOOL_CALL_ID",
  "answer": {"answers": [{"id":"QUESTION_ID","selected":["OPTION_ID"],"custom":"任意の補足"}]}
}
```

既にsettled、期限切れ、別callへの回答を成功と扱わず、返るbooleanと最新projectionを確認する。実装上の質問には既存の合意から答え、未決の製品判断や追加権限は利用者の判断へ戻す。

## 設定・workspace・端末・job・添付

| 操作領域 | 調べる依存パッケージと経路 |
| --- | --- |
| 設定の読取と変更 | `dsh-api-settings-controller`。`settings/describe` はargs `{}`、秘密指定の値はredacted。updateは `{ns,patch,expectedRevision}`、replaceはsection、mutateはops。最新revisionとschemaを読んでから指定された値を変更する |
| credentialの接続状態 | 同controllerの `credentials/describe` は `{refs:["REF"]}`。状態のみ返す。設定変更はset/unsetの型を調べ、秘密値をstdoutや引数へ出さない |
| workspaceと会話の配置 | `dsh-api-workspace-controller`。create/rename、pin/unpin、archive/unarchive等。`workspace/follow` はstreamでbaselineを読む。HTTPの `workspace/list` は存在しない |
| ファイルの読取 | `dsh-api-workspace-files`。list/stat/read/readBytesは非stream、changesはstream。wire argsのscopeは `{workspaceFileScopeId:"SESSION_ID"}`。readの行範囲は `range:{offset:1,limit:20}`。一覧やEOF・version・上限を確認してページングする |
| 権限のカタログ | `dsh-permission-presets` の `permissionPresets/catalog` はargs `{}`。現在の権限はsession projectionで読む。カタログの取得は権限変更や個別操作の承認ではない |
| 端末 | `dsh-api-terminal-controller`。`terminal/list` は `{sessionId:"ID"}`。出力はfollow stream。write/create/close等は実行環境を変える操作 |
| 背景job | `dsh-api-job-controller`。`job/list` と `job/follow` はstream。killは `{request:{sessionId,jobId}}`。turn中断のcancelとjob killを取り違えない |
| 添付 | sessionのimage attachment read、別のfile-upload経路。promptのfile partはhost発行の `receiptId` を使う。ローカルパスをそのままreceiptに置き換えない |

設定の書込みはnamespaceのschema・現在値・revisionを読む。redactedなsecret値をplaceholderのままreplaceしない。conflictは再読取して意図した変更を再評価する。

## 実行権限と新規セッションの既定値

権限変更自体が元依頼または現在も有効な利用者の明示指示に含まれる場合だけ使う。スキルの利用や会話作成は、権限拡張・既定値変更への許可ではない。Desktop MCPはこれらを維持し、変更APIを公開しない。以下の `danger-full-access` はその値を指定された場合の例。既定値の変更と、作成済みセッションへの適用は別操作。どちらも対象Hostの認証済みRPCで行い、profileファイルやセッションJSONを直接書き換えない。

| RPC | args | 用途 |
| --- | --- | --- |
| `permissionPresets/catalog` | `{}` | selectableな値と `defaultPreset` を確認 |
| `settings/describe` | `{}` | `namespaces` 内の `ns: "permission"` のschema・value・revisionを取得 |
| `settings/update` | `{"ns":"permission","patch":{"defaultPreset":"danger-full-access"},"expectedRevision":REVISION}` | 指定Host/profileの今後の新規セッションに適用。既に同値なら不要 |
| `commands/execute` | `{"agentId":"SESSION_ID","line":"/permission danger-full-access","submittedAttachments":[]}` | 実在する対象セッションの権限を変更。既に同値なら不要 |

更新後は設定を再読し、対象セッションの完全projectionで `permissions.currentValue` が依頼された値と一致することを確認する。既存モデル・推論・保留指示を維持し、質問への明示回答や実再開の記録は別途行う。権限設定の成功だけで実コマンドや製品検収の成功にしない。

0.2.0-rc.2のWindows Desktop同梱 `dsh-permission-presets`、`dsh-commands`、`dsh-api-settings-controller` のREADME・generated descriptor・UI実装で照合した。`commands/execute` は `agentId` / `line` / `submittedAttachments` を直接渡し、`request` に包まない。`settings/update` は新規セッションの既定値を保存し、既存セッションの値を自動変更しない。

## live stream

`session/follow`、`session/control`、`workspace/follow`、job、端末のfollowは `BASE/api/remote.mux` のWebSocket carrierを使う。`call` は非stream RPC専用で、streamをHTTP POSTで購読しない。

streamが必要になったらインストール済み `dsh-client-connection` のREADME・ `lib/types/rpc*.d.ts` と、該当controllerのgenerated clientを読み、公式のRemoteConnection/muxを使う。同じ認証cookie・Originを維持する。session followのopening baselineとcursor、再接続時のgap修復、assistant-streamのattempt/revision/indexを扱う。自作の「seqが増えたら本文をappendする」簡易streamで置換や再接続を失わない。

通常の会話読取・進捗確認は付属helperのsnapshotで行える。実装委譲後のタイマー監視と補正は[SKILL.mdの定期監視](../SKILL.md#実装依頼後の定期監視)に従う。それ以外の長期監視や定期起動は、別途依頼された場合に設定する。
