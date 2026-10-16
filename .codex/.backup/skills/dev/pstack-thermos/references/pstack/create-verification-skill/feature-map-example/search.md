# メモを検索する

題名と本文で探し、結果を開き、結果なしと検索不能を分ける。

## 下位機能

`search-open`、`search-match`、`search-open-result`、`search-empty`、`search-clear`、`search-cli`。

## 利用者の入口

Searchボタン、入力欄外で/、`notes search <query>`。

## control-notesでの操作

前提。Notesとdoctorが正常。Quarterly planの本文はDraft budget。

- Search notes dialogが開く。 操作 `control-notes browser click --role button --name "Search"`。
- 入力欄外の/で同じdialogが開き、文字が入らない。 操作 `control-notes browser press --key "/"`。
- quarterlyでQuarterly planだけが見える。 操作 `control-notes browser fill --role searchbox --name "Search notes" --value "quarterly"`。
- budgetで本文一致の抜粋が見える。 操作 `control-notes browser fill --role searchbox --name "Search notes" --value "budget"`。
- 結果を開くとdialogが閉じて題名が表示される。 操作 `control-notes browser click --role link --name "Quarterly plan"`。
- volcanoで検索完了後No matching notesが見える。 操作 `control-notes browser fill --role searchbox --name "Search notes" --value "volcano"`。
- Clear searchで入力が空になりRecent notesへ戻る。 操作 `control-notes browser click --role button --name "Clear search"`。
- 終了0、JSONにQuarterly planの一件。 操作 `control-notes cli -- notes search "quarterly" --format json`。
- 終了0、JSONは[]。 操作 `control-notes cli -- notes search "volcano" --format json`。
- 画像とARIAにNotes、検索語、結果が見える。 操作 `control-notes browser snapshot --aria --path artifacts/search/results.aria.txt`、`control-notes browser screenshot --path artifacts/search/results.png`。

## 注意点

入力中の/は文字入力。固定sleepではなく結果か空statusを待つ。Include archivedなしではarchiveを除く。CLIは--format json。結果を開いたら次の検索前に再度dialogを開く。
