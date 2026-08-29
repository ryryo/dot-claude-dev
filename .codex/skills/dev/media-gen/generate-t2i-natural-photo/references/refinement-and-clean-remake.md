# 局所修正とクリーン再構築

既存画像を入力にする処理を、目的で分ける。指定箇所の内容変更は局所修正、画像全体の破損した高周波情報を作り直す処理はクリーン再構築、構図を保った人物の顔・体型変更は人物再現である。

## 注釈による局所修正

入力は現在の採用画像と、その同一画像へ線・矢印・文章を重ねた注釈ガイドの2枚にする。

- 現在画像は人物、衣装、ポーズ、crop、カメラ、照明、未指定領域の唯一の視覚基準。
- 注釈ガイドは場所と修正内容だけを示し、線、矢印、文字、枠自体は描画しない。
- 指定領域だけを修正し、肌、髪、布、edge、surfaceを直近周辺と同じtexture scale、light response、color response、sharpness、capture characterで再構築する。
- 指示されていない美形化、美肌化、平滑化、sharp化、restyleを行わない。
- 未指定領域まで顔や構図が動く場合は採用せず、現在画像から再試行する。

## クリーン再構築

ガビガビ、jagged/doubled edges、halo、oversharpening、noisy micro-detail、反復編集残り、plastic skin、noisy fabricを除く場合は`ai-clean-remake`を使う。

- 元画像をReference 1に残し、人物、顔、髪、表情、衣装、ポーズ、手、小物、背景、光、カメラ、配置、crop、aspect ratio、styleの唯一の基準にする。
- 元画像の意味と意匠は使うが、壊れたpixel、halo、jaggy、noise、pseudo-textureはコピーしない。
- Superpixel、Depth、coarse structure、30-color mapは低情報量の補助制御に限定し、元画像の代わりにしない。
- 肌は控えめな毛穴、産毛、色調差、自然な陰影遷移、髪は不均一な毛束と後れ毛、布は現実の織りスケールで新しく再構築する。
- 曖昧な細部は発明せず保守的に作り直す。リアル感のためのノイズ、ぼけ、手ブレ、低解像度を追加しない。
- upscale、sharpen、denoise、patchとして処理せず、同じ画像のfresh renderとして作る。

実行方法、control map、候補比較、保存規則は`ai-clean-remake`を正本とする。

## 元資料からの再生成

生成結果の内容や撮影感そのものが違う場合は、局所修正やクリーン再構築へ逃げず、元の顔、髪、体型、衣装、背景、構図資料から新しく生成する。失敗画像や直前候補を次の参照へ混ぜない。参照役割を保ったまま、外れた工程だけを具体化する。
