# 検収 checklist

main Codex は、worker の結果を受け入れる前に必ず検収する。

## 委任前

実行して記録する。

```bash
git status --short
git branch --show-current
```

既存の未コミット変更は、ユーザーまたは先行 worker の作業として扱う。戻してはいけない。

## 委任後

実行する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

確認する。

- 変更ファイルが許可した編集範囲内に収まっている。
- 並列実行の場合、同じ変更ファイルが複数 worker に割り当てられていない。
- worker が、明示的に許可されていない `docs/PLAN`、`tasks.json`、進捗ファイル、commit、branch、remote、package lockfile を変更していない。
- 既存の未コミット変更を戻していない。
- worker の final report が、実際の差分、理由、検証結果と一致している。
- 元の goal に対して必要な挙動が完了している。
- 検証コマンドが成功している。失敗している場合は、理由が具体的で受け入れ可能である。
- `mac-ide-applescript` transport では、model 選択は Cursor IDE 側の状態であり、プログラムからは検証できないと報告する。
- `mac-ide-cdp` transport では、選択に使った target id、title、URL、workspace/thread hint を記録する。これらは CDP の識別情報なので英語表記のまま扱う。
- Codex subagent の場合は、要約、変更ファイル、判断理由を確認してから統合する。

## 範囲外変更

許可範囲外のファイルが変更されていた場合:

1. log と diff を確認してから判断する。
2. 範囲外変更が worker によるものだと明確で、安全に戻せる場合だけ main Codex が修正してよい。
3. ユーザーまたは別 agent の作業である可能性がある場合は、変更前にユーザーへ確認する。
4. 広範囲に破壊的な command は使わない。

## 受け入れ条件

diff、scope、report、verification がそろってから受け入れる。planning/progress 更新、最終 PASS 判定、commit、PR は main Codex の責任である。
