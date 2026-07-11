# 検収

委任前に `git status --short` と `git branch --show-current` を記録する。既存変更はユーザーまたは先行 worker の作業として扱い、元に戻さない。

worker 完了後に確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

- 変更が write scope 内で、既存変更を消していない。
- planning / progress、branch、remote、lockfile など禁止対象を変更していない。
- worker report、実際のdiff、planのtask contractが一致する。
- Codex subagent の選定 model / reasoning、起動引数、report が一致する。fallback の理由が記録されている。
- main Codex が必要な検証を再実行し、goal と受け入れ条件を満たしている。

範囲外変更は、worker 由来と断定できるものだけ main Codex が修正する。ユーザーまたは別 worker の変更の可能性があれば戻さず、成果を未検収として扱う。

検収後、main Codexだけがplanのstatus、integration batchの結果、decision logを更新する。検証前に`done`へ進めない。
