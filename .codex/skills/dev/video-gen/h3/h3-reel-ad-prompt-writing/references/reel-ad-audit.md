# リール広告プロンプト監査

問題を検出したら、理由と影響を短く示し、同じ目的を満たす修正版へ置き換える。

## 企画監査

- 主目的とCTAが1つに絞られているか。
- 冒頭3秒以内に対象者、商材、利益のいずれかが分かるか。
- 選んだ企画パターンが提供素材と事実で成立するか。
- Aロールの発言ごとに、対応するBロールまたは観測可能な根拠があるか。
- Bロールが装飾だけにならず、情報を進めているか。
- 人物と商品を機械的に交互表示していないか。

## H3契約監査

- 各単位が2〜15秒か。
- モードと入力素材の役割が一致するか。
- 公式フィールド順、時刻表記、Shot番号が正しいか。
- タイムスタンプが昇順で尺内に収まるか。
- Ref2VAのラベルと実際の入力順が一致するか。
- 同一人物、商品外観、衣装、店舗の保持指定が単位間で一貫するか。
- カメラと被写体の主動作を同時に詰め込みすぎていないか。

## 文字監査

- 許可されていないコピー、価格、日付、名前、ロゴ、URLがないか。
- 日本語、句読点、改行、数字、通貨表記が原文どおりか。
- 会話全文を字幕と大テロップで重複表示していないか。
- 長文字幕、価格、注意書き、CTAがpost-editへ分離されているか。
- 主要文字が右端、上端、下端のUI領域へ寄っていないか。
- 表示完了後に読める保持時間があるか。

## 音声監査

- 台詞が映像内の話者、口の動き、時間帯と一致するか。
- SFXが商品操作、着地、切り替えの時刻に同期するか。
- 複数生成のBGM、ナレーション、room toneが不自然に途切れないか。
- 広告利用できると確認していないライセンス楽曲を指定していないか。
- 声や音声信号を、許可された参照範囲を超えて複製していないか。

## 長尺方式監査

- 15秒を超えるだけで`continuous`を選ばず、通常のカット編集、連続時間履歴、混在のどれが目的か説明できるか。
- `edited`、`continuous`、`hybrid`の選択が画角、場所、人物、商品、参照数と一致するか。
- `hybrid`でlatentを共有するcontinuation groupと`Independent`生成を混同していないか。
- `continuous`がFL2VA＋任意のQwen参照画像1枚という前提で成立するか。複数Ref2VA素材を暗黙に渡していないか。
- 同じcontinuation groupのmodel、Qwen encoder、Video VAE、Audio VAE、解像度、基本sampling設定が一致するか。
- StartだけにFirst Frameがあり、各Continueが前の完全なAV latent、handover metadata、新しいLast Frameを受け取るか。
- `context_frames=22`、`auto`、`phase_aligned_extended`が設定され、`actual_head_context_frames`をSaveとStitchへ渡すか。
- 中間単位が`Stitch Ready`、現在の最終単位だけが`Final Clip`か。
- `Independent`単位へ`Stitch Ready`または`Final Clip`を誤って付けていないか。
- 境界付近に重要な台詞、CTA、不可逆な商品動作がないか。
- 最終完成尺をhandover解析前の確定値として扱っていないか。
- 必要なカスタムノードの導入を確認できない場合、実行不能と明示しているか。

## 事実・広告表現監査

次を提供情報なしに追加しない。

- 価格、割引率、通常価格、送料、在庫、期間、限定数
- 売上、販売数、ランキング、満足度、口コミ、第三者評価
- 営業時間、所在地、資格、スタッフ数、設備
- 治療、完治、予防、必ず得られる美容・健康・収益結果
- Before/After、顧客体験、推薦コメント

個人の健康、身体、年齢、経済状態などを本人について断定する呼びかけを避ける。必要な免責や業種固有の法令確認を指摘するが、法的適合を保証しない。

## 完成監査

- 生成単位の順序と完成リールの時間が一致するか。
- カット点が台詞や重要動作を切断しないか。
- CTA直前に無関係な新情報が追加されていないか。
- 最終CTAと主役が安定しているか。
- `Creative Contract`、構成、プロンプト、編集シートの文字と事実が一致するか。

## 返却形式

問題がなければ `Audit: PASS` とする。問題がある場合は次の順で返す。

1. `Critical`: 尺、フィールド、参照、事実、権利、重大な文字誤り
2. `Major`: 構成、可読性、音切れ、同一性、CTA
3. `Minor`: リズム、冗長さ、弱い転換
4. `Corrected Output`: 問題を直した完成版一式

## 最新仕様の確認先

- Meta Reels ads: https://www.facebook.com/business/ads/facebook-instagram-reels-ads
- Instagram Reels ad specifications: https://www.facebook.com/help/instagram/546362593027755
- Meta advertising review: https://www.facebook.com/business/ads/review-policy-guidelines
- Meta Advertising Standards: https://www.facebook.com/policies/ads/
