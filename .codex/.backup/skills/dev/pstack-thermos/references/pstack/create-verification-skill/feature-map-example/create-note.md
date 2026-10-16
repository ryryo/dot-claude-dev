# メモを作る

ブラウザかCLIから題名と本文を保存し、下書きを取り消し、別の画面で保存を確かめる。

## 下位機能

`create-open`、`create-save`、`create-cancel`、`create-cli`。

## 利用者の入口

New noteボタン、入力欄外でn、`notes create --title <title> --body <body>`。

## control-notesでの操作

前提。Notesとdoctorが正常。`Release checklist` がまだない。

- 空のフォームが開き、Titleへfocusする。 操作 `control-notes browser click --role button --name "New note"`。
- 題名と本文を入力するとSave noteが有効になる。 操作 `control-notes browser fill --role textbox --name "Title" --value "Release checklist"`、`control-notes browser fill --role textbox --name "Body" --value "Tag and publish"`。
- Note savedと題名が表示される。 操作 `control-notes browser click --role button --name "Save note"`。
- 一覧へ戻り再度開くと保存値を読める。 操作 `control-notes browser click --role link --name "All notes"`、`control-notes browser click --role link --name "Release checklist"`。
- Discard meを入力してCancelすると一覧に残らない。 操作 `control-notes browser click --role button --name "New note"`、`control-notes browser fill --role textbox --name "Title" --value "Discard me"`、`control-notes browser click --role button --name "Cancel"`。
- 終了0、JSONに新IDと題名がある。 操作 `control-notes cli -- notes create --title "CLI note" --body "Created from terminal" --format json`。
- 画像とARIAに保存した二件が見える。 操作 `control-notes browser snapshot --aria --path artifacts/create-note/list.aria.txt`、`control-notes browser screenshot --path artifacts/create-note/list.png`。

## 注意点

入力中のnは文字入力。保存時のtrim後の題名を確認する。成功statusだけでなく再度開く。作成した二件をfixture cleanupで消し、証拠は残す。
