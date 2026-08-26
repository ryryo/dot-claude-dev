# <Sprint 名>

## ユーザーの目的

<ユーザーが達成したい状態を 1 から 3 行で書く。>

## 範囲

- In:
  - <今回触る対象>
- Out:
  - <今回やらないこと>

## Repository Context（確認した前提）

- Workspace: `<absolute workspace path>`
- 初期状態: `<git status --short の要約>`
- 読んだもの:
  - `<path>`: <確認した事実>

## 制約

- worker にversion controlやremote操作を任せない。
- write scope が重なる task は並列化しない。
- 既存の未コミット変更を戻さない。
- Cursor CLI worker は `--yolo` で動くため、main Codex が diff と write scope を必ず検収する。
- <この sprint 固有の制約>

## Worker 方針

- Worker 種別: `cursor-cli-agent`
- Cursor CLI model: `composer-2.5-fast` 固定
- Cursor CLI command: `cursor agent --print --yolo --trust --workspace "$WORKSPACE" --model composer-2.5-fast --output-format json`
- main Codexを既定とし、decisionがfixed/bounded、independenceがindependent/staged、write scopeがisolated、oracleがstrong/限定可能なpartial、side effectがlocal/shared reversibleなtaskをCursor CLI workerへ委任する。
- complexityはprompt量、timeout、検証強度へ反映する。未解決判断または結合実装は、mainのGateと参照駆動の実装shardへ分割する。
- risk modifierがあるtaskは、mainがinvariantとnegative caseを固定し、real secret/production stateを使わない検証とmain再検証を定める。
- Cursor CLI preflight は task graph / 投入前 checklist に入れない。submit / monitor が CLI 疎通問題で失敗した場合だけ例外処理として実行する。

## 最小検証

- <focused test / typecheck / build / browser check など、リスクに見合う最小検証>

## 受け入れ条件

- <ユーザー視点で完了と言える観測可能な状態>
