# MCPとCLIの使い分け

確認日: 2026-10-08。機能やオプションは変わるため、利用時は現行の公式文書とインストール済みCLIの`--help`を優先する。

## 公式が説明する役割

- [Devin MCP](https://docs.devin.ai/work-with-devin/devin-mcp)は、外部AI/IDEからCloudセッションを作成・検索・操作し、メッセージ・イベント・添付を取得する公式サービス。`https://mcp.devin.ai/mcp`のStreamable HTTPが推奨され、旧`/sse`は非推奨。公開リポジトリを検索するDeepWikiのMCPとは異なる。
- [Devin CLI](https://docs.devin.ai/cli)は、ローカルのファイルや環境で作業する対話型の開発エージェント。CloudのKnowledge・Playbooks・Secretsを、ローカルでも同じように使えるとは扱わない。
- [Cloud CLI](https://docs.devin.ai/cli/cloud)では`devin --cloud`により独立VMのCloudセッションを端末から操作できる。Webで作ったセッションもID/URLで再開できるため、CLIはローカル専用ではない。
- [Commands & Flags](https://docs.devin.ai/cli/reference/commands)には、1回の応答を出力する`-p`、ファイルからの依頼読込、セッション再開、会話の書き出しがある。ACP対応のエディタやIDE向けには`devin acp`がある。ACPは標準入出力でJSON-RPCを使う継続対話のプロトコルで、MCPとは異なる。

参照した公式文書は「単一PRならMCP、広い作業ならCLI」という規則を示していない。本スキルでの使い分けを、MCPとCLIの優劣を定めた公式推奨として説明しない。

## 本スキルでの使い分け

CodexがCloudのDevinへ指示し、成果を取得する場合はMCPを既定にする。引数が定義されたツールで状態を取得し、cursorで履歴の続きを読めるためである。リポジトリ数や改修規模だけで接続方法を決めない。作業を分割するかは、責務・依存・レビューできる成果を基準に判断する。

未pushのファイル、手元だけの開発環境、実行プロセス等をDevinに直接扱わせる必要があれば、ローカルCLIを使う。手元にあるファイルでも、Cloudへの転送にはその作業についての許可が必要である。PRの作成にMCPを使うことは必須ではない。

MCPで今回の操作ができず、CLIを利用できるならCloud CLIを代替候補にする。送信前に同じセッションへつながることを確認し、成果の保存場所を変えない。ターミナルを閉じてもCloudの作業は残るため、タイムアウトだけで停止したと判断しない。

継続的なイベントや操作の許可応答を厳密に扱う必要があり、`-p`とセッション再開では足りない場合はACP対応を検討する。Codexが自動でACPクライアントになるわけではない。スキル作成や作業委譲だけの依頼で、専用クライアントや常駐の接続プロセスを追加しない。

## ローカルCLIの確認範囲

Devin CLI `3000.11.3`のバージョン表示とhelpで、`--cloud`、`-p`、`--prompt-file`、`--resume`、`--export`、`acp`、`cloud drs`を確認した。CLIの認証、実装ジョブの実行、Cloudの版選択、操作の許可処理、PR作成・レビュー結果の取得は、この確認では実証していない。MCPの接続確認には[既存の接続手順](../../devin-browser-pr/references/mcp-and-resume.md)を使う。
