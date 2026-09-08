---
name: h3-reel-ad-prompt-writing
description: 粗い商品・サービス・店舗情報と人物、商品、店舗などの参照素材から、MiniMax H3向け縦型リール広告の企画、Aロール／Bロール構成、T2VA・I2VA・FL2VA・L2VA・Ref2VAプロンプト、15秒超のedited・AV latent continuous・hybrid長尺方式、編集テロップ、音声設計、結合指示を作成または監査する。ECの商品販売、サロン・飲食・小売・教室などの予約・来店・問い合わせ広告、UGC風広告、商品実演、体験レポート、募集・限定告知に使う。細かな絵コンテではなく、ざっくりした入力から広告構成も考える必要があるときに使う。動画生成の実行や広告配信には使わない。
---

# MiniMax H3 リール広告プロンプト

粗い依頼を、完成リールの粗い構成、H3生成単位、編集レイヤー、監査結果へ変換する。人物が語るAロールと、その内容を商品・施術・店舗体験で裏付けるBロールの反復を基本にする。

## 必ず読む資料

作業前に次を読む。

1. `../h3-prompt-writing/SKILL.md`
2. 選んだH3モードに対応する `../h3-prompt-writing/references/base-en.txt` または `../h3-prompt-writing/references/ref-en.txt`
3. `../h3-motion-graphics-prompt-writing/SKILL.md`
4. `../h3-motion-graphics-prompt-writing/references/motion-graphics-core.md`
5. `references/reel-ad-core.md`
6. `references/reel-creative-patterns.md`
7. `references/h3-reel-assembly.md`
8. `references/reel-ad-audit.md`

`long_form_strategy` が `continuous` または `hybrid` の場合だけ `references/h3-latent-continuation.md` を追加で読む。

商材に応じて次のどちらか1本を追加で読む。ECと店舗の両方を扱う案件だけ2本とも読む。

- 商品販売・通販: `references/ecommerce-product-sales.md`
- 店舗・対面サービス: `references/local-store-service.md`

キネティック文字、商品ヒーロー、フラット説明、コラージュが主表現になる生成単位だけ、モーショングラフィックススキルの対応リファレンスを追加で読む。

## 1. 企画契約を固定する

入力から次を抽出する。結果が大きく変わる不足だけを質問し、それ以外は明示した仮定で進める。

- 商材と事実として確認できる特徴
- 視聴者と、その人が置かれている状況
- 主目的を1つ: 認知、販売、予約、来店、問い合わせ、保存、フォロー
- 視聴後の行動を1つ
- 使用できる人物、商品、店舗、場所、動画、音声
- 正確に維持する商品外観、人物同一性、表示文字、台詞
- 価格、割引、期間、在庫、実績、効果、注意書きの承認済み情報
- 尺、比率、音声方針、避ける表現
- 15秒超の場合の希望方式: `auto`、`edited`、`continuous`、`hybrid`

未指定時は10秒、9:16、`long_form_strategy: auto`を採用する。15秒超では目標完成尺と各H3生成尺を分けて管理する。未確認の価格、効能、口コミ、限定数、営業時間、所在地を補完しない。

## 2. 企画パターンと基本編集文法を選ぶ

`reel-creative-patterns.md` から主パターンを1つ選び、必要な場合だけ副パターンを1つ併用する。

既定の流れは次とする。

1. `Speaker Hook`: 人物が悩み、疑問、意外性、募集内容を直接語る。
2. `Product Proof`: 商品、施術、店内、手元、素材、利用場面で直前の発言を裏付ける。
3. `Speaker Context`: 違い、理由、安心材料、反論への回答を短く語る。
4. `Proof Sequence`: 必要ならBロールを2本以上続け、工程や複数の証拠を見せる。
5. `Speaker or Product CTA`: 人物、商品、店舗、エンドカードのうち最も自然な主役で行動を促す。

機械的な交互配置にはしない。Bロールを続けた方が理解や説得力が高い場合は続ける。人物素材がない、商品世界観が主役、モーショングラフィックス主体の場合は商品・文字中心へ切り替える。

10秒の初期配分は `人物フック 0–2秒 → 商品証拠 2–5秒 → 人物説明 5–7秒 → 商品またはCTA 7–10秒` とし、内容量に応じて調整する。

## 3. 参照素材とH3モードを決める

参照素材ごとに「使う属性」「無視する属性」「登場する生成単位」を決める。

- 参照なし: T2VA
- 単一画像を正確な開始フレームにする: I2VA
- 開始と終了を正確に固定する: FL2VA
- 終了フレームだけを固定する: L2VA
- 複数の人物・商品・店舗・作風・動画・音声を参照する、または参照とキーフレームを併用する: Ref2VA

複数画像があるだけでRef2VAにせず、役割のある素材だけを採用する。Ref2VAでは入力順と `<Subject N>`、`<Picture N>`、`<Video N>`、`<Audio N>` を完全に一致させる。

## 4. 長尺方式と生成単位を決める

15秒以下は原則1本にまとめる。15秒を超える場合、利用者の明示指定を優先し、`auto`では次の順で方式を決める。

- `edited`: 画角、場所、役割、人物、商品が切り替わる、Aロール／Bロールを編集する、または複数Ref2VA素材が必要な通常のリール広告。
- `continuous`: 同一人物、同一商品、同一場所、同一カメラのワンテイク、連続トーク、歩行、組立など、時間履歴の保持が目的の区間。
- `hybrid`: 連続トークや連続動作の区間と、独立したRef2VA BロールやCTAが混在する広告。

15秒を超えるだけで`continuous`を選ばない。FL2VA＋任意のQwen参照画像1枚という前提を満たせない区間は`edited`へ戻す。複数参照を必要とする案件全体を、無理に1枚の合成参照へ押し込まない。利用者が`continuous`を指定しても前提を満たせない場合は、実行可能と装わず、阻害条件と`edited`または`hybrid`の代案を返す。

方式決定後、次を守る。

- 各H3生成単位は2〜15秒、通常6〜10秒とする。
- 独立生成は原則3ショット以内とし、意味の切れ目で分割する。
- `continuous`の単位には同じ`continuation_group`を割り当て、`Start`の後へ`Continue`を並べる。
- `hybrid`ではlatentを共有する単位と`Independent`単位を明確に分ける。
- 話者の説明と対応する証拠映像を、可能なら同じ単位か隣接単位へ置く。
- UGC調の独立単位はhard cutを優先する。
- 正確な連続性が必要な接続だけ、終了／開始キーフレームまたはAV latent継続を使う。

`continuous`ではStartへFirst FrameとLast Frame、Continueへ前の完全なAV latentと新しいLast Frameを割り当てる。プロンプトは`continues speaking`、`continues the same motion`のように前状態の継続を明示し、人物、衣装、場所、カメラを新しい場面として再定義しない。

各生成単位のH3本文は英語で書き、画面に見える文字と日本語の台詞は原文を維持する。`Independent`と`Start`は選んだ公式H3モードのフィールド順と時刻表記を守る。`Continue`は新しいFirst Frameを持つFL2VAとして偽装せず、continuation workflow用の3つのH3 core fieldsを所定順で書き、Last Frameはノード入力として別記する。

## 5. 文字と音声を分離する

H3へ焼き込む文字は、動きそのものが演出になる短いフックまたはタイトルに限定する。商品ラベルは参照外観として保持する。

次は原則として編集レイヤーへ出す。

- 会話字幕と長い説明文
- 価格、割引、日付、在庫、営業時間
- 注意書きと免責
- 正確性が必要なCTA、URL、アカウント名
- 常設バナーとカウントダウン

単発生成ではH3の会話、SFX、BGMを使える。`edited`の複数生成では音の継ぎ目を避けるため、各クリップは会話またはSFX中心とし、長いナレーションと共通BGMは編集レイヤーへ出す。`continuous`のnative AV latentは声、room tone、動作音の時間履歴に使い、広告用BGMと長いナレーションはpost-editを既定にする。重要な台詞、CTA、不可逆な商品動作を継続クリップの境界付近へ置かない。音声参照がある場合だけ、定義した役割の範囲でRef2VAの音声参照を使う。

## 6. 出力する

次の順序で返す。

1. `Creative Contract`: 目的、対象者、CTA、目標完成尺、生成尺、比率、パターン、`long_form_strategy`、continuation group、正確な尺の確定方法、使用可能な事実、仮定
2. `Rough Reel Structure`: 時間帯、Aロール／Bロール、役割、主役だけを示す粗い構成
3. `Reference Map`: 入力順、H3ラベル、役割、保持属性、無視する属性、使用単位
4. `H3 Generation Units`: 単位番号、continuation group、`Start / Continue / Independent`、H3モード、生成尺、前latent、First/Last Frame、共通参照、stitch role、公式形式の完成プロンプト。stitch roleはcontinuation groupの中間だけ`Stitch Ready`、現在の最終だけ`Final Clip`とし、`Independent`は`N/A`にする
5. `Edit Overlay Sheet`: 正確な文言、表示区間、配置目的、焼き込み／編集レイヤー区分
6. `Assembly and Audio`: 結合順、転換、共通BGM、SFX、ナレーション、最終保持。`continuous`または`hybrid`ではH3 Infinite実行表と依存確認も含める
7. `Audit`: `PASS`、または問題点と修正版

利用者がプロンプトだけを求めた場合も、必要な参照順と重大な仮定を省略しない。監査依頼では問題を列挙するだけで終わらず、修正版一式を返す。

## 7. 完了前に監査する

`reel-ad-audit.md` に従い、少なくとも次を確認する。

- Aロールの発言とBロールの証拠が対応する。
- 冒頭3秒以内に対象者、商材、利益のいずれかが伝わる。
- 主要人物、商品、CTAが9:16のUIセーフゾーンから外れない。
- 商品と人物の同一性、参照ラベル、表示文字が全単位で一貫する。
- 各H3単位が2〜15秒で、タイムスタンプが昇順である。
- 15秒超の方式が素材と連続性の目的に合い、各continuation groupが独立生成と混在していない。
- `continuous`のモデル、Video/Audio VAE、解像度、前latent、head context、stitch roleが一貫する。
- 最終完成尺をhandover解析前の確定値として断定していない。
- 台詞、字幕、価格、注意書きが重複または矛盾しない。
- 複数生成のBGMやナレーションが不自然に途切れない。
- 最終CTAが読める状態で保持される。
- 未確認の広告主張や個人属性への断定がない。

成果物はH3投入可能なプロンプトと編集設計までとし、生成プロバイダー操作、動画編集の実行、広告入稿、法的適合の保証は行わない。
