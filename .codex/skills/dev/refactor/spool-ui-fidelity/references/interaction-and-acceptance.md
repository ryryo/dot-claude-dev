# 操作別の比較・検収条件

旧 `spool-flow/.codex/skills/project/magnific-node-fidelity/SKILL.md` の操作・完了条件を、旧Flow→新Spoolの比較へ引き継ぐ。今回対象となる操作だけ適用し、非該当と未観測を分ける。以下は全ノードへ機能を追加する一覧ではない。

## 根拠と探索の入口

既存の画像・動画・一覧表は観測日、対象状態、未確認範囲を確認し、関係する動作を今回のライブ画面で再確認する。参照ソースは実装方法の根拠であり、実画面を観測した証拠にはしない。画面に到達できなければ、資料・コードで確定できることを進め、実操作が必要な部分を未確認として残す。

実際のrepo配置から次の資料を探し、対象部分だけ読む。旧資料の採用範囲を、そのまま新Spoolの承認済み仕様とは扱わない。

| 調べること | 入口 |
| --- | --- |
| 元スキルと過去の操作・寸法 | 旧Flowの `.codex/skills/project/magnific-node-fidelity/SKILL.md`、`docs/REFERENCE/magnific-spaces-live-ui-audit.md` |
| 旧モデル設定・ポート | 旧Flowの `docs/REFERENCE/magnific-spaces-live-node-options.md`、`magnific-spaces-frontend-ports.md` |
| 旧側の採用範囲・Assistant/List | 旧Flowの `docs/REFERENCE/spool-flow-initial-reproduction-scope.md`、`spool-flow-assistant-local-prototype.md` |
| 保存・履歴・復元 | 旧Flowの `docs/REFERENCE/magnific-storage-recovery-audit.md`と現行の保存設計 |
| 旧UIとCLI | 旧Flowの `apps/canvas/src/features/workflow/`、`features/assistant/`、`features/local-storage/`、`.codex/skills/project/local-workflow-cli/` |
| 新側の採用技術・移植要件 | 対象Spool checkoutの `docs/REFERENCE/technology-stack.md`、内部資料の `docs/REFERENCE/260926_spool-oss-ui-alternatives.md`と対象ノード設計 |
| 新UIと共通操作 | 対象Spool checkoutの `packages/flow/src/browser/`、`packages/flow/src/core/`、`packages/contracts/`、実際の呼出元と近いテスト |
| 新CLI・保存/実行境界 | 対象Spool checkoutの `packages/cli/README.md`、`docs/architecture/interfaces.md`、`docs/architecture/local-host.md`と公開capabilities |

旧Listの探索例は `list-node.tsx`・`text-preview.tsx`・`media.tsx`・`workflow.css`。固定revisionの `.reference/` がある場合は関係するsource・consumer・testを確認する。新側で同名fileや旧構成を仮定せず、実際の呼び出し・状態管理・保存経路を追う。採用UIライブラリの利用・変更時は、その現行スキルや資料も参照する。

## 表示・編集・復帰

| 対象 | 保持する確認条件 |
| --- | --- |
| 入口・選択 | 新規作成直後、単/ダブルクリック、選択解除、複数選択、右クリック。どの操作が選択・編集・プレビューを開始するか |
| 名称 | 左上名称の単/ダブルクリック、編集開始時の全選択・cursor、Enter/外側クリックで確定、Escapeで取消。空欄・長い名前・IME変換中、本文編集/移動との競合。変更が表示名だけに保存され、内部ID・接続・結果を変えないこと。保存/再読込と必要なUndo/Redo。試した名前は元へ戻す |
| cursor・Canvas | 非編集/編集中、本文/子要素/ボタン上のcursor、文字選択、ドラッグ、パン、スクロールの違い。ポインターが写らない画像だけでcursorを合格にしない |
| 行内編集 | 編集を開始する行、フォーカス・キャレット、他の行の表示/操作可否、書式、IME、ショートカット、取消/確定。入力欄での操作がCanvasへ漏れないこと |
| プレビュー | 開く入口、メディア種別ごとの外形・本文幅・sidebar/footer、表示専用/編集可の違い。閉じる/Escape/外側クリック後の戻り先と下書き保持。List等では「選択→行内編集→拡大編集→閉じて下書きへ戻る→取消」と「保存→再読込で本文/書式を保持」を分ける |
| パネル内容 | ノード種別・モデル・接続入力の有無・実行状態ごとの項目、順序、初期値、候補、条件表示、disabled、補助文。ノード内設定・プレビュー詳細欄との役割を混同しない |
| パネル開閉 | 未選択からの単/ダブルクリック、設定ボタン、結果クリック、別ノード/別種別への選択切替、同じノードの再選択、空白クリック、閉じる/Escape後の選択と再表示。開始状態→操作→対象/開閉/内容を各ノードで記録する。他ノードの成功で代替しない |
| 寸法 | カード/各行の幅・高さ、余白、文字サイズ・行高・省略行数、角丸・枠・背景・ぼかし・toolbar位置。modal外形と本文幅を別に測る。過去のList値を別種別の正解へ転用しない |
| 接続と設定 | 入出力の型、ポート表示、接続後の変化、次ノード作成、設定変更の反映時点、保持/置換、選択した項目の次工程への受け渡し |
| 実行と結果 | 開始前、待機、実行中、完了、失敗、停止/再試行。操作可能範囲、前回結果の保持、Take/Listの作成と表示。有料生成は現在の許可・予算に従い、過去資料のcredit上限を再利用しない。生成なしの観測から先に進める |
| 保存 | 下書き/確定値の境界、取消後の元データ、本文/書式、保存/再読込、必要なUndo/Redoと履歴。表示だけの状態と保存される値を混ぜない |

パネルを変更した場合は、観測した契機に沿って「開く→設定を変更→別種別を選択→戻る→閉じる→再度開く」を対象に含める。前ノードの項目や値が残らず、正しいノードへ保存され、条件ごとの表示差が保たれることを確かめる。開閉時の幅、Canvasへの重なり/領域縮小、ノードの見え方とviewport移動も見る。panel要素の存在だけで合格にしない。

見た目は対象状態のstyle、操作はevent・状態遷移・確定/保存の責務に沿って直す。DOMを書き換えるだけの回避や、全ノードへの一括cursor指定で終わらせない。

## UIとCLIの同等性

保存される変更に対応するCLI command・field・公開範囲を確認する。フォーカス・cursor・パネル開閉のジェスチャーをCLIへ追加する要件にはしない。

- 旧側は `flow read` の `capabilities`、`control-contract.ts` の許可node/要求形式、`control-operations.ts` の設定検証と編集処理で照合する。入口は `scripts/flow-control.mjs` → `dev/control/plugin.ts` → `control-client.ts` → `workspace-session.ts`。
- 新側は現CLIの `capabilities`・`read` とcommand schema、共通operationの受付・保存経路で照合する。新側へ旧専用command名や構成を移さない。資料の古い対応表、UIにあること、共有関数を呼ぶことだけでCLI対応/同等性を判定しない。
- 同じ初期値からUI/CLIを操作し、確定値、入力制約/正規化、ID・接続・結果の保持、保存、必要なUndo/Redoを比較する。別契約なら差分または衝突として扱い、無条件に同じ履歴方式を新設しない。
- 既存対応の回帰と、元から未対応のnode/設定/実行を区別する。回帰は修正し、未対応は明記して新規対応の範囲を判断する。DB直接更新や無制限の文書置換で迂回しない。
- CLI経路を変える場合、分離fixtureで実CLIの `read → apply相当の公開更新 → read/UI表示 → 保存・再読込` を確認する。履歴、draft拒否、古いrevision、再送は影響するものを選ぶ。共通APIのunit成功と実CLI往復を区別する。

旧側の近いテスト例は `control-operations.test.ts`・`dev/control/plugin.test.ts`・`e2e/local-control.spec.ts` と `playwright.local-control.config.ts`。これらは比較と保証範囲の参照であり、新側の検証は対象checkoutの既存fixture/helperへ置く。表示のみの修正でCLI全件を走らせない。

## 反映と完了

状態遷移を変更したら、近いE2Eのfixture/helperで操作から必要な保存・再読込・復帰まで検証する。通常幅と1024pxで再撮影・目視し、変更に必要な型チェック・lint・既存テストと共有部品の影響確認を行う。fixture成功と実providerでの生成成功を区別し、低リスクな余白/cursorの修正にCSS文字列一致テストを足さない。

利用者が開いている確認用タブへの反映を確認する。反映されない場合は、origin・checkout・配信build・HMR/watch・読み込まれたstyleを照合する。reload前に未保存の本文・書式を保護し、beforeunloadでreloadが成立していない場合を見逃さない。下書きを勝手に確定/破棄せず、共有サーバーも無条件に再起動しない。必要な再起動は所有者・起動設定と現在の許可を確認する。

対象状態と操作の一致、必要な保存/回帰検証、利用者向け実画面の反映を完了根拠にする。届かない実画面や未許可の生成は残件にし、完全再現とは報告しない。報告には実画面/画像、CLI対応経路と結果/未対応、テストの成功/失敗/skip、意図的差分と未確認を含める。新しい実測は既存REFERENCEの対象箇所へ観測日・条件とともに追補し、過去観測と区別する。通常修正で独自のStory・PLAN・EVIDENCE一式を自動作成しない。
