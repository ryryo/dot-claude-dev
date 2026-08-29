# プロジェクトローカルMCP設定

## 方針

- 対象プロジェクトのルートに`.mcp.json`を置く。
- 対象プロジェクトに`.mcp.json`がない場合は、カレントワークスペース階層またはスキルの親プロジェクト階層にある最寄りの`.mcp.json`を初期設定として使う。
- このツールキットでは、ルートの`.mcp.json`をKamui MCP全体設定の正本として扱う。
- 対象プロジェクトに既存の`.mcp.json`がある場合は、既存の`mcpServers`へ必要モデルだけをマージする。
- 認証キーは設定JSONへ直接書かない。
- `.env.local`または環境変数の`KAMUI_CODE_PASS_KEY`を使う。
- `.env.local`を`.gitignore`へ追加する。

## 初期配置

`setup_mcp.py`と`generate.py`は、対象プロジェクトの`.mcp.json`を次の順序で用意する。

1. 対象プロジェクトに`.mcp.json`があれば、それを読み込む。
2. なければ、カレントディレクトリから上へたどって最初に見つかる`.mcp.json`を探し、見つからなければスキルの親ディレクトリから上へたどって探す。見つかった`.mcp.json`を対象プロジェクトの`.mcp.json`として保存する。
3. 選択されたi2vモデルのMCPサーバー設定を`references/models.json`から上書きマージする。

このリポジトリでは`/Users/ryryo/dev/kamui-mcp-toolkit/.mcp.json`が初期配置元になる。`run_ecosystem.py`や設定管理ツールでルート`.mcp.json`が更新されれば、このスキルの初期配置にも反映される。スキルを別プロジェクトへコピーする場合は、そのプロジェクトのルートに正本となる`.mcp.json`を置く。

`.env.local`:

```dotenv
KAMUI_CODE_PASS_KEY=
```

キーが未設定ならユーザー本人に入力してもらう。キーを表示、ログ保存、Git追加しない。

## 設定反映

Codexや他のMCPクライアントは`.mcp.json`追加後に再読み込みが必要な場合がある。このスキルの`generate.py`は同じ設定を使ってHTTP MCPを直接呼び出せるため、再起動前でも生成処理を継続できる。

## モデル更新

`references/models.json`の各モデルに次を追加する。

- 一意な`slug`
- MCPの`server_id`と`url`
- `submit/status/result`ツール名
- 画像、終了画像、解像度、長さ、比率、音声に対応するフィールド名
- 最低解像度と概算単価
- ループ対応可否

追加後は`setup_mcp.py --model <slug>`と`generate.py --dry-run`で検証する。実際の課金ジョブ前にMCPの`tools/list`と価格を再確認する。
