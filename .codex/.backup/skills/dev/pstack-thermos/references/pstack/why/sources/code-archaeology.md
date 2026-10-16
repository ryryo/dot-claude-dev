# Gitとリポジトリ内の履歴

commit、PR本文・レビュー、コメント、ADR、テスト、同時に変わったファイル、CHANGELOG、チケットIDを読む。コードへ直接結び付く資料だが、記録だけで全動機が残るとは限らない。

```bash
git log --follow --oneline -- <file>
git log -S '<exact_string_from_code>' -- <file>
git log -G '<regex>' -- <file>
git blame -L <start>,<end> <file>
git show <hash>
git log <old>..<new> -p -- <file>
git log -1 --format=%B <hash>
gh pr view <number> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews,files
rg -l -i 'architecture.decision' --glob '*.md'
rg -n -C2 '(TODO|FIXME|HACK|XXX|NOTE)' <target_file>
rg -l '<symbol>' --glob '*test*'
```

PRの問題説明、代案を論じたレビュー、制約のコメント、境界値のテスト、関連Issueを探す。squashで個別commitがなければPRへ戻る。「小さい整理」という題名でもdiffを読む。コピーされた慣例は元のcommitまでたどる。botの変更は通常、動機の説明に乏しい。関数名だけを作者の意図として引用しない。

返答には関係する短い引用、hash・PR・file:line、作者・日付、直接か間接かを付ける。
