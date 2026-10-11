# Notesの検証例

この例は実在のアプリや導入済みのツールを保証しない。架空のNotesで、実入口と観測結果を結び付ける手順を示す。

## 前提

Notesを `http://127.0.0.1:4173` で使い捨て状態に起動する。`NOTES_DATA_DIR=/tmp/notes-verify-$RUN_ID` で同時実行を分離し、`Quarterly plan` と `Grocery list` を用意する。`control-notes` と `notes` をPATHへ置き、`control-notes doctor` でURL、データ保存先、build revisionを確認する。この検証が起動したinstanceだけを操作する。

## 操作と証拠

各手順は指定がなければ基準状態から始める。CSS位置よりARIA roleと名前を選ぶ。引用されたUI名とコマンドは実アプリの識別子なので変えない。ブラウザは `control-notes browser`、端末は `control-notes cli -- <command>`。変更後はfixtureを戻し、証拠は保持する。

利用者の操作と結果を記録する。UIはアプリの識別が見えるARIA snapshotと画像、CLIは命令、stdout、stderr、終了コード、保存変更は別の読み取り経路で示す。機能IDと入口を記す。到達不能は試した命令と不足前提を返す。別入口の成功で未実行の入口を検証済みにしない。

## 各機能の形式

H1と利用者に見える動作の一段落の後、H2を「下位機能」「利用者の入口」「control-notesでの操作」「注意点」の順に置く。操作区分は前提から始め、操作、正確な命令、結果を組にする。実装の内部事情ではなく、安定した入口と観測を記す。

[作成](create-note.md)はブラウザ・CLI、取消、保存を、[検索](search.md)はtoolbar・keyboard・CLI、一致、空、clearを扱う。
