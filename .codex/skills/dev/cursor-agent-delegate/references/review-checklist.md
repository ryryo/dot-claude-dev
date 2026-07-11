# 検収チェックリスト

worker の結果を受け入れる前に main Codex が確認する。

## 委任前

```bash
git status --short
git branch --show-current
```

既存の未コミット変更はユーザーまたは先行 worker の作業として記録し、元に戻さない。

## 委任後

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

- 変更ファイルが許可した write scope 内に収まっている。
- 同じファイルが複数 worker に割り当てられていない。
- `docs/PLAN`、progress file、branch、remote、lockfile が明示的な許可なく変更されていない。
- 既存の未コミット変更が消されていない。
- worker の final report が実際の diff と一致している。
- 分割時に選んだ model / reasoning effort、起動時の override、final report の値が一致している。
- model が fallback された場合、利用不能または task 再評価の理由が記録されている。
- worker が実行した検証と結果を確認できる。
- main Codex が必要な検証を再実行している。
- goal と受け入れ条件を満たしている。
- Codex subagent の提案は根拠と repository context を main Codex が確認している。

## 範囲外変更がある場合

1. diff と registry / report を確認して変更元を判断する。
2. worker が作ったと明確に判断できる範囲外変更だけを main Codex が修正する。
3. ユーザーまたは別 worker の変更の可能性がある場合は勝手に戻さない。
4. 変更元を分離できなければ、その成果を未検収として扱う。

## 受け入れ条件

scope、diff、report、verification が揃った場合だけ採用する。planning / progress 更新、完了判定、commit、push、PR は main Codex の責任とする。
