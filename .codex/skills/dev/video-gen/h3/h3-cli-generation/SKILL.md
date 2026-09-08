---
name: h3-cli-generation
description: MiniMax H3のmanifest queueをBrowser操作なしで診断、事前検証、明示承認後の逐次生成、endpoint・worker監視、output保存、動画検査、再開、取消、warm終了までCLIで安全に実行する。openreel-storyboardでH3動画を生成する、複数manifestを流す、既存runをresume/status/cancelする、GPU割り当てやCLI生成障害を復旧する依頼に使う。
---

# MiniMax H3 CLI Generation

`/Users/ryryo/dev/openreel-storyboard`で、Web版API Labと同じCloudflare gateway APIを使う`pnpm h3`を操作する。RunPodへ直接送信する別経路やBrowser操作を通常導線にしない。

## 実行フロー

1. repositoryへ移動し、`pnpm h3 doctor`を実行する。gateway、Cloudflare認証、warm管理、`output/`、ffprobe、ffmpegの結果を確認する。続けて`pnpm h3 warm status --runtime <runtime>`でendpoint `min/max`、worker数、Job数、準備stage、無進展時間、再配置回数を確認する。これらは生成Jobを作らない。
2. `pnpm h3 validate --queue <absolute-or-repository-relative-path>`を実行する。順序、runtime、mode、比率、尺、profile、seed、参照数、保存先をユーザー依頼と照合する。これは生成Jobを作らない。
3. 課金前に、対象queue、Job数、runtime、profile、尺、保存先、分かる範囲の最大費用をユーザーへ提示する。対象と条件を含む明示承認がなければ止める。
4. 承認済みの場合だけ`pnpm h3 run --queue <path> --yes`を実行する。CLIを終了せず、warm準備、Job ID、進捗、保存、H.264／解像度／尺／全frame decode、warm終了まで監視する。
5. 完了した各MP4の絶対pathを随時報告する。全件完了時はrun stateとwarm `off`を確認する。

## 安全契約

- `validate`、`doctor`、`status`を課金承認なしで使ってよい。`run --yes`は承認後だけ使う。
- `resume`は既に承認された同じrunのledgerとmanifest digestが一致する場合だけ使う。別queueや変更済みmanifestへ流用しない。
- SIGINT後、status障害、保存失敗、decode失敗では新しいJobを送信しない。`pnpm h3 status --run <run-id>`で状態を確認してから復旧する。
- `submission_unknown`では自動再送しない。provider側でJob作成有無を確定できるまで止める。重複課金を避けることを優先する。
- `cancel`は進行中Jobを明示取消する依頼がある場合だけ使う。SIGINTで暗黙にcancelしない。
- CLIが正常完了した場合はwarmが自動で`off`へ収束する。中断や不明状態ではwarmを残すため、Jobがないと確認後に`pnpm h3 warm end --runtime <runtime>`を使う。
- warm停止時のendpointは`min=0/max=0`、準備・生成中は`min=1/max=1`を正常値とする。準備中に0/0なら割り当て開始失敗として診断し、新しいrunを作らない。
- warm準備は一律15分で切らない。最新logまたはstage/worker変化をheartbeatとし、無進展上限を`allocating` 既定15分、`image_loading` 20分、`model_cache` 30分、`runtime_initializing` 10分とする。割り当て診断で一時的に延長する場合はprivate runtimeの`MINIMAX_H3_ALLOCATION_STALL_MINUTES`（1〜120）だけを変更し、テストの時刻期待値を書き換えない。現在の準備開始より前から残る非ready workerは再利用せず、warmを最大1回だけ再配置する。代替準備も失敗したら停止し、無限retryしない。
- Job送信後の`in_queue`と`in_progress`はwarm準備タイマーへ混ぜない。同じJob IDを監視し、providerの20分実行上限または明示的なterminal stateを待つ。
- warm状態取得の一時的な5xxは短く再試行し、準備stageと同一Job IDを保持する。loopback gatewayからHTTP応答が返る場合は、5xxでもgateway processの到達性は成立しているため、同じportへ二重起動しない。
- CLIとgatewayの観測が矛盾する場合だけRunPod MCPでendpointとworkerを読み取る。RunPod MCPや直接APIから生成Jobを送らない。
- credential、token、secretを引数、ログ、ledger、回答へ書かない。

## 進捗形式

人が監視する通常実行では標準表示を使う。自動処理や証拠採取では、pnpmのscript bannerを混ぜないため`pnpm --silent h3 <command> --jsonl`を使う。JSONLの各行は`schemaVersion: 1`を持つ。

## 復旧

失敗または中断時は[recovery.md](references/recovery.md)を読み、run ledgerを正本に同じJob IDから復旧する。API pollingやqueue制御を独自scriptへ再実装しない。

Browserは、API Lab固有UIの回帰確認、手動入力のデバッグ、画面表示の依頼が明示された場合だけ使う。

CLIとWeb UIの責務を拡張するときは[parity.md](references/parity.md)を読み、生成の正本、復旧性、可観測性をCLIへ置く。UI専用のFixtureや画面回帰を無理にCLIへ複製しない。

`pnpm h3`とgatewayの観測が矛盾するときだけ[runpod-mcp-diagnostics.md](references/runpod-mcp-diagnostics.md)を読み、記載された読み取り専用toolへ限定する。MCPサーバーの全tool仕様をスキルへ転載しない。
