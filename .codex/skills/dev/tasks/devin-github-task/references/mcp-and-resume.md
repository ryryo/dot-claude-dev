# 公式MCPの接続と同じチャットでの再開

## 接続の確認

公式Streamable HTTP endpointは `https://mcp.devin.ai/mcp`。接続設定・認証情報の作成や保存は利用者が依頼した場合に行い、ツールが要求する操作時確認は守る。サービスユーザーは対象組織だけに限定する。PATを使う場合は `X-Org-Id` が必要。鍵を共有repo、スキル、コマンド引数、ログやスクリーンショットへ残さない。

サービスユーザーの組織範囲・役割・有効期限は作成前の具体的な設定と作成後の一覧で確認する。Memberは読取専用とは扱わず、選べる役割名だけで既存セッションへの実効アクセスを断定しない。期限は利用者の指定を尊重し、Neverを共通の既定値にしない。保存済みの資格情報を再利用できるなら接続試験のたびに発行し直さない。

macOSでは [Keychainヘッダーhelper](../scripts/keychain_headers.py) を `http_headers_helper` に指定できる。通常実行は認証ヘッダーを標準出力へ返すため、人が見る確認では `--check` を使い、ヘッダー本体をツール出力へ転記しない。`--check` の成功はローカルのキー取得・形式確認であり、Devin側の認証成功ではない。環境変数で接続する場合は `bearer_token_env_var` を使う。

設定への登録、認証付きの実読取、新しく起動したCodexクライアントのツール読込、現在のデスクトップチャットからの実呼出しは別々に確認する。`mcpServerStatus/list` の `authStatus=unknown` だけで失敗と判定せず、既存セッションの実読取で認証を確かめる。新しいクライアントでの成功や設定変更だけで、実行中チャットへの反映・自動再開まで検証済みと扱わない。反映が未確認の間は許可されたブラウザー経路を使える。

認証前でも `initialize` と `tools/list` が成功する場合がある。初期化結果のサーバー名がDeepWikiでも、実ツール一覧を照合する。既存セッションに `devin_session_interact` の `action=get` を実行し、返却ID・タイトル・状態を画面と比較して初めてセッション読取成功とする。`get_messages` も確認する。接続試験で新規作業、ダミーPR、作業再開メッセージを送らない。

## 状態取得と送信

ツール名と引数は実際の `tools/list` を優先する。2026-10-08の実取得では次を確認した。

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
