# 公式の用途と本スキルの経路選択

確認日: 2026-10-08。機能・flagsが変わり得るため、利用時は現行公式文書とインストール版の`--help`を優先する。

## 公式が説明する役割

- [Devin MCP](https://docs.devin.ai/work-with-devin/devin-mcp)は、外部AI/IDEからDevinのCloudセッションを作成・検索・操作し、メッセージ・イベント・添付を取得する公式サービス。`https://mcp.devin.ai/mcp`のStreamable HTTPが推奨され、旧`/sse`はdeprecated。DeepWikiの公開repo検索だけのMCPとは異なる。
- [Devin CLI](https://docs.devin.ai/cli)は、ローカルのファイル・環境を扱う対話的なcoding agent。ローカルagentはCloudのKnowledge・Playbooks・Secretsを同じように使えるとは扱わない。
- [Cloud CLI](https://docs.devin.ai/cli/cloud)では`devin --cloud`により独立VMのCloudセッションを端末から操作できる。Webで作ったセッションもID/URLで再開できるため、CLIはローカル専用ではない。
- [Commands & Flags](https://docs.devin.ai/cli/reference/commands)には非対話の`-p`、prompt file、session resume、会話exportと、ACP対応host向けの`devin acp`がある。ACPは継続した構造化対話向けのstdio JSON-RPCで、MCPとは別のprotocol。

参照した公式文書は「単一PRならMCP、広い作業ならCLI」という規則を示していない。MCPとCLIの優劣を一般に定めた公式推奨として、本スキルの経路選択を説明しない。

## 本スキルの判断

外部agentであるCodexがCloudへの指示と成果回収を行う場合、型付きツール・状態・cursor履歴を使えるMCPを既定にする。Cloudに持ち込むrepo数や改修規模は経路選択の基準にしない。分割は責務・依存・レビュー可能な成果で決める。

手元の未pushファイル、手元だけのtoolchain、実行プロセス等をDevinに直接扱わせる必要があればローカルCLIを使う。ローカルにあることはCloud転送の許可ではなく、MCPを使うこともPR作成の必須条件ではない。

MCPで今回の操作ができず、CLIが既に利用できるならCloud CLIを代替候補にする。送信前に同じセッションへつながることを確認し、成果の所在を変えない。ターミナルを閉じてもCloud作業は残るため、タイムアウトで停止済みと決めつけない。

継続的なイベント・permission応答を厳密に扱う必要が生じ、単発`-p`と明示resumeで足りなければACP対応を検討する。Codexが自動的にACP clientになるわけではない。専用client・常駐bridgeを、単なるスキル作成や作業委譲から追加しない。

## 今回確認したローカルの範囲

Devin CLI `3000.11.3`のversionとhelpで`--cloud`、`-p`、`--prompt-file`、`--resume`、`--export`、`acp`、`cloud drs`を確認した。これはCLIの認証成功、実装ジョブ、Cloudの版選択、permission処理、PR作成・レビュー結果の取得を実証したものではない。MCPの接続確認は[既存の接続手順](../../devin-github-task/references/mcp-and-resume.md)を使う。
