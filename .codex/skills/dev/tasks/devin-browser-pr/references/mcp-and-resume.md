# 公式MCPの接続と同じチャットでの再開

## 接続の確認

公式Streamable HTTP endpointは `https://mcp.devin.ai/mcp`。接続設定・認証情報の作成や保存は利用者が依頼した場合に行い、ツールが要求する操作時確認は守る。サービスユーザーは対象組織だけに限定する。PATを使う場合は `X-Org-Id` が必要。鍵を共有repo、スキル、コマンド引数、ログやスクリーンショットへ残さない。

サービスユーザーの組織範囲・役割・有効期限は作成前の具体的な設定と作成後の一覧で確認する。Memberは読取専用とは扱わず、選べる役割名だけで既存セッションへの実効アクセスを断定しない。期限は利用者の指定を尊重し、Neverを共通の既定値にしない。保存済みの資格情報を再利用できるなら接続試験のたびに発行し直さない。

macOSでは [Keychainヘッダーhelper](../scripts/keychain_headers.py) を `http_headers_helper` に指定できる。通常実行は認証ヘッダーを標準出力へ返すため、人が見る確認では `--check` を使い、ヘッダー本体をツール出力へ転記しない。`--check` の成功はローカルのキー取得・形式確認であり、Devin側の認証成功ではない。環境変数で接続する場合は `bearer_token_env_var` を使う。

スキルの名称変更後は、新しい配置先のhelperを設定する。起動中のMCPクライアントが以前のパスを使う場合に備え、共有リポジトリの`devin-github-task/scripts`にはhelperへの互換リンクを残している。旧名のスキル定義は置かない。

設定への登録、認証付きの実読取、新しく起動したCodexクライアントのツール読込、現在のデスクトップチャットからの実呼出しは別々に確認する。`mcpServerStatus/list` の `authStatus=unknown` だけで失敗と判定せず、既存セッションの実読取で認証を確かめる。新しいクライアントでの成功や設定変更だけで、実行中チャットへの反映・自動再開まで検証済みと扱わない。反映が未確認の間は許可されたブラウザー経路を使える。

認証前でも `initialize` と `tools/list` が成功する場合がある。初期化結果のサーバー名がDeepWikiでも、実ツール一覧を照合する。既存セッションに `devin_session_interact` の `action=get` を実行し、返却ID・タイトル・状態を画面と比較して初めてセッション読取成功とする。`get_messages` も確認する。接続試験で新規作業、ダミーPR、作業再開メッセージを送らない。

## 状態取得と送信

ツール名と引数は実際の `tools/list` を優先する。2026-10-08の実取得では次を確認した。

### 組込スキルを使った新規セッション作成

2026-10-08の`devin_session_create`は、作成前に`managing-child-sessions`の呼出しを要求する。このスキルはDevin側の`<builtin>/managing-child-sessions`で呼び出せる。Codexへの原本配置を作成条件として追加せず、呼び出せるDevin側で前提を満たして作成する。

1. 利用者が依頼した新規作業の件数・独立性・所有範囲を確定する。管理に使える既存Devinセッションの最新履歴と子一覧を読み、未完作業や別の委譲と混ぜない。
2. Codexから`devin_session_interact(action="message")`で、そのDevinに`managing-child-sessions`の実際の呼出しと、指定した作業だけの作成を依頼する。親は作成・中継を担当し、製品の実装・採否判断や独自の追加委譲を行わない。対象repo・base・編集範囲・受入条件・成果物を各子のpromptへ全文で渡す。子は別VMであり、親の会話・ファイルを共有しない。
3. 親Devinは組込スキルを呼び、必要なintegrationを確認し、`devin_session_create`を実行する。独立した作業は1件につき1セッション、依存する作業は先行成果を確認してから作成する。返却されたID/URLと作成結果をCodexへ返す。結果が不明なら親の`child_session_ids`と履歴を照合し、同じ作成を繰り返さない。
4. Codexは返却IDで`get`・`get_messages`・`events`を実行し、対象・初期依頼・実行状態を確認する。以後の範囲内の指示はその子へ直接`message`を送る。直接操作の権限がなければ、親へ対象IDと送信本文を渡して中継し、子の受信履歴で確認する。権限があると推測して再作成しない。
5. 作成成功を確認したら、最初の進捗報告で各作業名を実際のセッションURLへのMarkdownリンクにして利用者へ提示する。URLは作成結果または`get`から取得し、対象ID・タイトルと照合する。親経由の場合も実装担当の各子を案内し、記録への保存や親URLの提示だけで済ませない。完了・PR作成まで待たない。会話URLは利用者とのチャットへ提示し、公開PR本文・footerへは載せない。

`skill_activated`イベントで呼出しを、作成結果と親の子一覧で実作成を、子への実読取・メッセージ受信でCodexからの対話をそれぞれ照合する。親の通知をCodexの自動再開と扱わず、親のarchiveが子にも及ぶことに注意する。組込スキルの呼出しができる場所が見つからない場合だけ、その不足を報告する。

2026-10-08の実作業では、親の`skill_activated`、指定2件の作成成功、親の子一覧、Codexから両方の`get`・`get_messages`・`events`、初期prompt全文の一致を確認した。子への直接`message`も成功した。これは作成・対話経路の実証であり、製品検証やPR採用の完了を示さない。公式MCP文書も外部clientによるセッション管理を説明しているが、組込スキルのCodex向け配布は前提としていない。

- `devin_session_interact`: `get` は複数IDの読取にも対応。`get_messages` は `first`・`after` によるcursorページング。取得したメッセージの時刻と次ページの有無を確認し、履歴先頭のページを最新の待機理由として扱わない。追加指示前に必要な後続ページを `after` で取得し、最後の指示・応答を照合する。`message` は既存セッションへの追加指示。`set_tags` は全置換なので、追加操作と混同しない。
- `devin_session_gather`: `session_ids` は `devin-` prefix付き。既定の待機300秒をそのまま使わず、`timeout_seconds` を60秒以内に指定する。時間切れは失敗や完了ではない。
- `devin_session_search`: 必要なID・期間・ページサイズで絞る。対象以外のセッションをまとめて操作しない。

`get` の `status` と `status_detail` を両方読む。`running` の詳細は `working`、`waiting_for_user`、`waiting_for_approval`、`finished` を区別する。休止・利用制限・エラー・不明状態を完了へ丸めない。PRができた場合はGitHubの実head・必須チェック・MERGEDを独立に照合する。Devinの状態や自己申告だけでマージ済み・元タスク完了としない。

同じ送信をMCPとブラウザで二重に行わない。送信結果が不明なら既存メッセージを読む。作成結果が不明なら検索・一覧で既存セッションを特定し、作成の再試行で重複ジョブを作らない。

`notify_on_response` はmessage引数に現れるが、Devin内での通知・再開を含む説明であり、外部Codexチャットの自動再開が保証されたとは扱わない。

## 再開と通知

利用者が監視を依頼した場合は、同じ対象の既存heartbeatを確認し、同じチャットの文脈で継続する。対象ID/URL、許可範囲、最新確認head、最後の送信、次の工程、証拠の保存先、終了条件をpromptへ含める。状態・最新メッセージID・PR headで変化を照合し、変化がない間は静かにする。入力待ちや範囲内の判断は元の依頼契約に従って解決し、待機表示だけで新しい作業を許可しない。

検証用の再開は既存セッションの読取に限定し、所定回数で終了する。通常監視は成果の採用・記録まで終了したら停止する。利用者の停止・削除依頼を復活させない。

Codexの非同期hookは休止中のチャットを起こさない。再開後に保存済みの引継ぎ情報を渡す必要がある場合だけ、短い `SessionStart` / `UserPromptSubmit` hookを追加する。外部待機のための長いhookやStop継続ループを作らない。初期導入では永続記録とheartbeat promptを使い、実際の情報欠落がなければhookを増やさない。

常設監視が必要ならREST APIの状態取得と受信箱を追加する。状態変化の重複防止、再起動後の回収、有限の再試行・backoffを設ける。MCP EventsはWork Cloud/dotsへの接続候補で、ローカルCodexへの適用を仮定しない。App Serverの `turn/start` は現在のデスクトップチャット・ブラウザ機能との接続を検証してから採用する。

## 公式資料

- [Devin MCP](https://docs.devin.ai/work-with-devin/devin-mcp)
- [認証](https://docs.devin.ai/api-reference/authentication)・[Get Session](https://docs.devin.ai/api-reference/v3/sessions/get-organizations-session)
- [Codex MCP設定](https://learn.chatgpt.com/docs/extend/mcp)・[Hooks](https://learn.chatgpt.com/docs/hooks)
- [チャットの定期再開](https://learn.chatgpt.com/docs/automations?surface=app)・[MCP Events](https://developers.openai.com/plugins/build/mcp-events)
