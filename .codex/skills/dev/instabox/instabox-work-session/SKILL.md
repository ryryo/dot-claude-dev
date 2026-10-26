---
name: instabox-work-session
description: "作業する数時間だけInstabox母艦へ軽い定期送信を行う専用Codexチャットを作る。依頼に合わせた期限と間隔で同じチャットを使い、終了後は停止する。スキルの編集・説明だけでは起動しない。"
---

# Instaboxの期限付き作業セッション

操作PCに専用チャットを一件作り、そのチャットのheartbeatで母艦へ軽い単発コマンドを送る。基本操作は[instabox-core](../instabox-core/SKILL.md)、母艦の接続・復旧は[instabox-dev-experiment](../instabox-dev-experiment/SKILL.md)を使う。

## 開始する

1. 対象の母艦、期間、間隔を依頼から決める。未指定なら2時間・10分間隔を目安にする。開始時にタイムゾーン付きの終了日時を確定し、以後「現在から2時間」などに計算し直さない。
2. 既存の維持用チャット・heartbeatを確認し、対象と作業時間が一致すれば再利用する。利用者が新規チャットでの開始を依頼した場合だけ`create_thread`を使う。スキルの作成・編集・説明依頼では開始しない。
3. 新規作成は操作PCのローカルチャット（`target.type=projectless`）とし、`create_thread`へ`model="gpt-6-luna"`・`thinking="medium"`を指定する（GPT-6 Luna／推論レベル「中」）。継続するheartbeatもこの設定を使う。母艦が休止すると実行できなくなるため、母艦自身に維持役を置かない。
4. 下記の内容を依頼へ渡す。子チャットは同じチャットのheartbeatを正規の`automation_update`で一件設定し、初回の単発送信と登録結果を確認する。親はその結果を一度確認し、チャットの場所・終了日時・間隔を報告する。

## 専用チャットへ渡す内容

- 母艦名、CLIの場所、確定した終了日時とタイムゾーン、送信間隔。
- 毎回まず期限を確認し、期限内なら次のコマンドを一回実行する。`MACHINE`は対象の母艦名へ置き換える。

  ```sh
  instabox exec MACHINE --timeout 10 --json -- /usr/bin/true
  ```

- 同じチャットのheartbeatを使い、既存の設定があれば更新する。新しいチャット・automationを繰り返し作らず、自分でsleepループ、daemon、cron、サブエージェントを起動しない。
- 終了日時に達した場合、中止依頼が来た場合、対応が必要な失敗が起きた場合は、そのheartbeatを停止する。期限を自動延長しない。休止・停止からの復帰や再起動を反復せず、hard runtimeとcooldownに従う。終了時に母艦や開発サービスを停止しない。
- 成功のたびに報告せず、終了・失敗・本人の操作が必要なときだけ知らせる。通知設定は利用者の意向に合わせてtoolの専用fieldで扱う。

