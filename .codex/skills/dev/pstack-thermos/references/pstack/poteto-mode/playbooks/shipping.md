[Codexでの実行規則](../../../execution.md)に従う。担当は親の設定を継承し、書き手の作業場所を分離する。採用・公開・定期実行は利用者の許可範囲で行う。

# 独立検証したPRを下から採用する

`babysit.md` の後半として、許可された範囲の採用を行う。検証済みの連続区間だけを扱う。

1. 経路をGitHub CLIまたは利用できるOriginへ固定する。Graphiteを必須にしない。一PRに一人の実装していない独立担当を置き、parentとheadの実際の操作面を比較する。判定は `PASS`・`PASS+NOTES`・`FAIL` とし、許可された投稿でそのPRへ記録する。CIやbotの承認を独立判定としない。
2. 最下段の未採用PRから進み、最初の不合格または未判定で止める。PASSとPASS+NOTESは通過するが、未検証の下段を飛び越えない。採用可能な上限と列を止める理由を示す。
3. 判定時のhead SHA、base SHA、baseからheadの安定した `git patch-id` を残し、採用直前のpatchと照合する。rebaseやbase変更でSHAが変わった場合も判定が現patchに対応するか確認する。
4. 差がテスト・資料・lintだけの場合、各担当が使ったビルドを判定時SHAで二回、現headで一回作る。元の二回にも出る差や埋め込まれたSHAだけを雑音として、差ごとにファイルと理由を判定する。雑音だけならその担当の結果を維持し、変更レビューと検査を更新する。ビルド成果のないdev server等の結果は再利用せず再実行する。その他のpatch変化は独立検証し直す。同じpatchでも現headでmergeabilityとCIを再確認する。コミット文の一致や古いSHAの緑表示で代用しない。
5. 現trunkをfetchし、最下段の検証済みブランチだけ必要に応じ正確なtipへrebase・pushし、baseをtrunkへ変更する。push後にpatchを再確認する。子のbase変更、auto-merge、採用を先に行わない。
6. 今採用できる最下段だけsquashで採用する。検査待ちで利用者が採用可能時の自動採用を依頼した場合だけ、そのPR一つへauto-mergeを設定する。採用を確認するまで次を準備しない。
7. GitHubの `autoMergeRequest` は一PRへの依頼に過ぎず、Originの設定、子のqueue、判定の有効性、列の安全性を証明しない。選んだ経路の実状態を確認し、取得できなければ不明とする。
8. 採用ごとにtrunkをfetchして採用SHAが含まれることを確認し、固定した下から上の一覧から採用済みを除く。新しい先頭のbase・head・検査・patch-idを確認する。自動retargetを仮定しない。独立作業は別に採用する。
9. Originはviewとchecksのwatch後にPRを読み直す。GitHubは `<skill-root>/scripts/pstack/poteto-mode/watch-pr/watch-pr --queued-stack --stack-prs <bottom>` をイベント通知として使い、起動ごとに `gh pr view <pr> --json state,mergedAt,mergeStateStatus,statusCheckRollup,autoMergeRequest` を読む。READYだけで採用済みとせず、mergedAtかMERGEDを確認する。
10. 採用されずCLOSED、auto-merge待ちでない必須検査のFAILURE・CANCELLED、auto-merge待ちでないUNSTABLE・DIRTYを失敗として診断する。検査中や自動採用設定中のBLOCKEDを即失敗としない。babysitのWAITING/merge-queue終了条件をここへ流用しない。現セッションで監視し、将来の監視は明示依頼と永続機能を要する。停止の原因を調べる前に列を変更しない。
11. 検証済み区間を採用したら止める。次の未検証PRを延長するには独立検証を新たに行う。

区間と上限、各PRの判定と担当、設定した自動採用と確認方法、実際の採用、次の不足を報告する。

コード変更のレビューは [レビューの進行](../../../review.md)へ進む。計画・設計の反証と、実動作・性能の検証は、それぞれの対象に応じて行う。
