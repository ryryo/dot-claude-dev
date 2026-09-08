# CLI / Web UI / RunPod responsibility

## CLIを正本にする機能

- manifest queueの検証、digest固定、逐次送信
- endpoint `min/max`、worker、Job、準備stage、停滞、再配置の監視
- run ledger、同一Job IDからの再開、保存再試行、取消
- `output/`への1本ごとの保存、ffprobe、全frame decode
- warm開始から終了、queue・worker・時間課金の停止確認
- Job ID、実行時間、費用、採用pathを持つrun record

## 次に追加するCLI候補

必要なユーザーストーリーが発生した順に実装する。

1. 明示的なwarm start / extend
2. 既存provider Job IDのrun ledgerへの安全な取り込み
3. run履歴一覧と未完了run検出
4. provider費用・queue delay・execution timeの記録
5. 同条件contact sheetと同期比較動画の生成

## Web UIに残す機能

- Fixtureによる入力・画面状態遷移の回帰確認
- 手入力とmanifest表示のデバッグ
- 最近のJobや生成結果の視覚的確認
- Browser操作が明示された場合の対話的運用

## RunPod MCPの境界

CLIとgatewayの観測が矛盾する場合に、endpoint設定、worker一覧、worker log、billingを読み取る。生成、retry、cancel、endpoint変更は通常のCLI契約を迂回するため使わない。CLIに欠ける読み取り機能が反復して必要なら、先にCLIの公開commandへ追加する。
