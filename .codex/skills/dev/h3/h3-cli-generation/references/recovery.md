# CLI recovery contract

Run ledgerは`/Users/ryryo/dev/openreel-storyboard/.codex/tmp/minimax-h3-runs/<run-id>.json`にある。直接編集せず、次の公開commandを使う。

| 状態・症状 | 操作 | 禁止事項 |
| --- | --- | --- |
| `paused`、一時的status失敗、SIGINT | `pnpm h3 status --run <id>`後、`pnpm h3 resume --run <id>` | queueを新規`run`しない |
| completed Jobの保存失敗 | 空き容量と保存先を直し、同じrunを`resume` | providerへ再submitしない |
| decode／解像度／尺検査失敗 | 元Job IDと保存対象を保持して原因を報告 | 次Jobを開始しない |
| `submission_unknown` | provider側で同じJobの有無を確認し、ユーザーへ報告 | `run`、自動retry、別seedでの代替生成をしない |
| `failed`／`timed_out` | provider errorと未送信queueを報告 | 自動resumeで再生成しない |
| 明示取消が必要 | `pnpm h3 cancel --run <id>` | SIGINTを取消として扱わない |
| Jobなし、warmが残存 | `pnpm h3 warm status --runtime <runtime>`後、`warm end` | active Jobを確認せず終了しない |
| `preparing`なのにendpointが`min=0/max=0` | `doctor`後、同じrunの`resume`でwarm開始を復旧 | 新しい`run`を作らない |
| `allocating`・worker 0・Job 0が設定済み上限（既定15分）まで無進展 | 自動再配置を1回だけ待ち、`warm status`で`min=1/max=1`と再配置回数を確認。診断用上限は`MINIMAX_H3_ALLOCATION_STALL_MINUTES`で変更する | テスト期待値の書き換え、2回目の手動retry、GPU条件の無断変更 |
| `image_loading`が20分無進展 | 最新log時刻を確認し、heartbeatが更新されなければ1回だけ再配置 | image pull中のlog更新を無視した固定時間停止 |
| `model_cache`が30分無進展 | model取得logのheartbeatを確認し、更新がなければ1回だけ再配置 | 大容量downloadの総経過時間だけで停止 |
| `runtime_initializing`が10分無進展 | ComfyUI起動logを確認し、更新がなければ1回だけ再配置 | 同じ非ready workerを繰り返し再利用 |
| 現在の準備開始より前から存在する非ready worker | stale workerとして1回だけ再配置 | `noProgressMinutes`が短いことだけを根拠に待ち続ける |
| 代替準備も同じstage上限を超過 | runを失敗停止し、provider供給不足または準備stageと未送信queueを報告 | 無限retry、別endpointへの無断送信 |
| Job送信後に`in_queue` / `in_progress` | 同じJob IDを監視し、providerのterminal stateまたは20分実行上限を待つ | warm準備stageとして再配置しJobを重複送信 |
| CLIとRunPodのworker表示が矛盾 | RunPod MCPでendpoint設定とworker一覧を読み取り照合 | MCPから生成Jobを送信 |
| gateway／認証エラー | `pnpm h3 doctor`を再実行 | credentialをログへ貼らない |
| local gatewayは応答するが上流が一時的に5xx | 同じgatewayを再利用し、warm statusを短く再試行 | 8787番へ別のwranglerを二重起動 |

`resume`はmanifestと参照素材のdigestを再検証する。`run_inputs_changed`なら、元runを再開せず差分を解消するか、新しい課金条件として改めて承認を取る。

`warm status`のworker表記は`initializing/ready/idle/running`、Job表記は`inProgress/inQueue`の順。停止中はendpoint `0/0`、warm中は`1/1`でなければ正常扱いしない。
