# 検収チェックリスト

worker の結果を受け入れる前に、main Codex が必ず確認する。

## 委任前

以下を実行して状態を記録する。

```bash
git status --short
git branch --show-current
```

既存の未コミット変更は、ユーザーまたは先行 worker の作業として扱う。元に戻さない。

## 委任後

以下を実行する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

以下を確認する。

- 変更されたファイルが、許可した編集範囲内に収まっている。
- 並列実行の場合、同じファイルが複数の worker に割り当てられていない。
- `docs/PLAN`・`tasks.json`・progress ファイル・commit・branch・remote・package lockfile が、明示的な許可なく変更されていない。
- 既存の未コミット変更が元に戻されていない。
- worker の final report が、実際の差分・理由・検証結果と一致している。
- 元の goal に対して必要な挙動が完了している。
- 検証コマンドが成功している。失敗している場合は、理由が具体的で受け入れ可能である。
- `mac-ide-applescript` transport を使った場合、model の選択は Cursor IDE 側の状態であり、プログラムからは検証できないと報告する。
- `mac-ide-cdp` transport を使った場合、選択に使った target id・title・URL・workspace/thread hint を記録する。
- Codex subagent の場合、要約・変更ファイル・判断の根拠を確認してから統合する。

## 範囲外の変更が混入していた場合

1. ログと diff を確認してから判断する。
2. 範囲外変更が worker によるものだと明確で、安全に戻せる場合だけ main Codex が修正してよい。
3. ユーザーまたは別の agent の作業である可能性がある場合は、変更前にユーザーへ確認する。
4. 広範囲に破壊的なコマンドは使わない。

## 受け入れ条件

diff・scope・report・verification がそろってから受け入れる。planning / progress の更新・最終 PASS 判定・commit・PR は main Codex の責任とする。
