# RunPod MCP diagnostic routing

RunPod MCPはシェルコマンドではなく、RunPod REST v2またはGraphQLへ接続する構造化toolである。利用前に対象toolが現在のセッションでcallableか確認する。tool schemaはMCPサーバーを正本とし、この文書へ引数一覧を複製しない。

| 症状 | 読み取り専用tool | 確認する値 |
| --- | --- | --- |
| warm中の`min/max`が不明 | `mcp__runpod__get_endpoint` | endpoint ID、workers min/max、GPU pool、CUDA条件 |
| queueとworkerの全体状態を素早く照合 | `mcp__runpod__endpoint_health` | inQueue、inProgress、initializing、ready、throttled、unhealthy |
| `allocating`またはworker数が矛盾 | `mcp__runpod__list_endpoint_workers` | worker総数、initializing、throttled、unhealthy |
| worker 0が続きGPU供給不足か不明 | `mcp__runpod__get_capacity` | endpointと同じCUDA版・GPU候補ごとのstock。endpoint設定と同条件で照合する |
| endpoint設定変更後から割り当てが不安定 | `mcp__runpod__list_endpoint_releases` | CUDA・image・GPU条件の変更履歴、最新version、rollout状態 |
| workerはいるがreadyにならない | `mcp__runpod__stream_worker_logs` | image pull、model cache、container起動、crash loop |
| ledgerのJob状態とprovider表示が矛盾 | `mcp__runpod__get_job_status` | 同じendpoint IDとJob IDの最終状態 |
| 実行後の費用証拠が必要 | `mcp__runpod__get_billing` | 対象期間とendpointに限定した利用額 |

## 境界

- MCP結果は診断証拠として使い、run ledgerを直接編集しない。
- 生成、retry、cancel、purge、endpoint更新はMCPから行わない。
- provider Jobが存在する可能性がある場合、新しい`pnpm h3 run`を開始しない。
- 同じ診断を二度以上必要としたら、対応する読み取り機能を`pnpm h3`の公開commandへ追加する。
