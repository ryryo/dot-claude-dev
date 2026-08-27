# AIモーショングラフィックス語彙・演出設計リファレンス

## 目的

MiniMax H3向けプロンプトで、After Effects／モーショングラフィックスの頻出語彙を意味アンカーとして選び、用語だけでは決まらない情報だけを補って、短く観測可能な演出設計へ変換するための共通リファレンス。

```text
伝達目的 → 主カテゴリ → 意味アンカー → 未決定パラメータ → 完成状態
```

語彙を全投入しない。各ビートでは主動作を1つ、補助語彙を必要最小限だけ選ぶ。標準語彙を一般語へ言い換えて消さず、意味アンカーとしてプロンプトに残す。`dynamic`、`cinematic`、`professional` のような抽象語は、方向、順序、着地、保持状態を表す具体語へ置き換える。この資料は演出語彙が未確定、抽象的、語彙の組み合わせ提案、既存用語の変換または監査が必要な場合に使い、利用者が具体的な動きと用語を固定している場合はその指定を優先する。

## 出典と扱い

最初の3件に掲載されたEffect Dictionary、頻出50語、8レイヤー、18カテゴリを、H3プロンプト向けに再構成した。後半3件は、標準語彙を意味アンカーとして残し、未決定パラメータだけを補ったMiniMax H3の公開作例として参照した。

- https://x.com/ponzponz15/status/2089224411736100980
- https://x.com/ponzponz15/status/2089152588935803100
- https://x.com/ponzponz15/status/2089152585869722077
- https://x.com/onofumi_AI/status/2092528740475785520
- https://x.com/onofumi_AI/status/2092529049436606600
- https://x.com/onofumi_AI/status/2092529117912858993

★の多さは投稿者の優先度・頻出度の目安であり、測定済みの市場統計やH3の成功率ではない。◆は特徴的・検索価値の高い表現を示す編集上の印である。モデルの再現性を保証する資料として扱わない。

## Core meaning anchors

次は、広告、UI、タイポグラフィ、タイトルシーケンスで再利用しやすく、視覚的な含意が比較的明確な語彙である。中央列は用語を置いた時点で既に指定される意味、右列は必要な場合だけ補う未決定情報を示す。右列をすべて埋める必要はない。

| 意味アンカー | 語彙が既定で含意すること | 必要な場合だけ補うこと |
| --- | --- | --- |
| `trim paths` | ベクターパスに沿った線の段階的な描画 | 対象、開始位置、方向、outline後にfillするか |
| `animated stroke / draw-on` | 線または輪郭が経路に沿って現れる | stroke owner、描画順、完成後の状態 |
| `offset paths` | 輪郭を内側または外側へ複製・拡張する | 個数、間隔、内向き／外向き、最終形状 |
| `repeater animation` | 同じ図形を規則的に複製する | 個数、間隔、回転／スケール差、時間差 |
| `mask reveal` | マスク境界の移動で対象を露出する | mask owner、起点、方向、露出対象 |
| `track matte` | 別レイヤーの形状または輝度で表示を制御する | matte owner、alpha／luma、対象レイヤー |
| `travelling matte` | 動くマットの通過領域が連続的に露出する | 起点、方向、経路、通過後の完成状態 |
| `iris wipe` | 円形開口が拡大または縮小して画面を切り替える | 中心点、拡大／縮小、次状態 |
| `shape / color-block wipe` | 図形または色面が画面を覆って次へ渡す | wipe owner、方向、次配色、完了時刻 |
| `card flip` | 平面が軸回転し、薄いedge状態を経て表裏を切り替える | 水平／垂直軸、回転方向、裏面または次画面 |
| `column / strip shear` | 画面を帯へ分割し、帯ごとにずらすまたは傾斜移動する | 分割数、縦／横、方向、stagger、露出色 |
| `stagger / cascade` | 複数要素が時間差で同じ動作を行う | 対象順、時間差、進行方向、最後の着地 |
| `elastic overshoot` | 目標値を一度越え、反動して収束する | 対象プロパティ、振幅、収束時間 |
| `text / letterform morph` | 文字形状が別の文字形状へ連続変形する | 元文字、先文字、対応関係、完成時刻 |
| `shape morph` | 形状の輪郭やトポロジーが別形状へ連続変形する | source、target、変形中の体積／輪郭、着地 |
| `fragment and reassemble` | 要素が破片へ分解し、再集合して形を作る | fragment owner、破片方向、再構築対象 |
| `liquid wipe / liquid matte` | 液体的な境界が画面を通過して次状態を露出する | 液体の起点、流向、粘性、次状態 |
| `match cut / match move` | 共通する形、位置、方向、運動量でショットを接続する | 対応するsource／target、接続フレーム |
| `speed ramp / time remapping` | 動作速度を区間内で変化させる | 加減速点、ピーク速度、通常速度への復帰 |
| `frame hold / hit stop` | 一瞬停止して衝撃や情報を強調する | 停止対象、開始時刻、保持時間、解除後の動き |
| `2.5D parallax` | 深度レイヤー間に相対移動を作る | レイヤー順、カメラ方向、移動量、終了構図 |
| `microinteraction / button press` | UI入力に対して短い状態フィードバックを返す | trigger、押下変形、状態更新、確認音 |

### 意味アンカーの書式

```text
[OWNER] performs [MEANING ANCHOR]. Add only the unresolved [ORIGIN/AXIS],
[DIRECTION], [SEQUENCE], [NEXT STATE], and [COMPLETED STATE].
```

数値は分割数、順序、タイミング、収束など、生成結果の判定条件になる場合だけ使う。公開作例の値を別案件へ流用せず、精密に見せるためだけの任意値を発明しない。

```text
語彙だけ: card flip
無駄な重複: card flip that flips like a card
有効な補足: card flip around the vertical center axis; the outgoing frame compresses to a thin edge, then reveals the blush-pink next state
```

## 18カテゴリの最上位分類

各ショットで、どのカテゴリが主役なのかを1つ決める。複数カテゴリを使う場合も主従を明示する。

| カテゴリ | 役割 |
| --- | --- |
| Movement | 物体、文字、図形の移動 |
| Dynamics | easing、overshoot、bounce、inertiaなど動きの性格 |
| Reveal | 出現、消失、描画、マスク |
| Transition | シーン間の接続 |
| Transformation | morph、assemble、shatterなど形状変化 |
| Typography | 文字、単語、書体、レイアウトの運動 |
| Graphic Shapes | 円、線、矩形、パターンの運動 |
| Camera / Depth | ズーム、パン、視差、奥行き |
| Temporal | speed ramp、freeze、reverse、frame操作 |
| Distortion | glitch、warp、pixel、digital FX |
| Texture / Material | film、print、paper、chrome、glassなどの質感 |
| Light / Color | glow、flash、gradient、refractionなど |
| Particles / Organic | 粒子、液体、煙、炎、成長 |
| 3D / Simulation | 立体、布、剛体、柔体、物理感 |
| Composition | overlay、mask、split screen、layer構成 |
| UI / Data | microinteraction、数値、グラフ、フロー |
| Rhythm / Loop | beat sync、audio reactive、seamless loop |
| Impact / Emphasis | punch、hit、flash、shake、freeze |

## 機能から主カテゴリを選ぶ

先に「何を伝えるビートか」を決め、主カテゴリを1つ選ぶ。Texture、Light、Dynamicsは主目的を支える補助層として扱う。

| ビートの目的 | 主カテゴリ | 代表的な選択 |
| --- | --- | --- |
| 要素を見せる | Reveal | mask reveal、type-on、shape reveal |
| 位置や関係を説明する | Movement / Graphic Shapes / UI・Data | slide、stagger、line draw、counter |
| 状態や意味を変える | Transformation | shape morph、assemble、fragment and reassemble |
| 次の場面へ渡す | Transition | match cut、shape wipe、color-block wipe |
| 一点を強調する | Impact / Emphasis | scale punch、impact frame、hit stop |
| 質感や時代感を付ける | Texture / Material | halftone、film grain、paper grain、chrome |
| 最終状態を確定する | Composition / Lockup | centered lockup、aligned grid、stable end card |

### 主分類ごとの優先パレット

| 主分類 | 優先するカテゴリ | 控えめにするもの |
| --- | --- | --- |
| キネティックタイポグラフィ | Typography、Reveal、Dynamics、Rhythm | 強いCamera、文字確定後のDistortion |
| フラットイラスト説明広告 | Movement、Graphic Shapes、UI・Data、Composition | 写実的3D、複雑なCamera、無目的なParticles |
| 商品ヒーローCM | 3D・Material、Light・Color、Transformation、Impact | 商品を隠すOverlay、ラベルを歪めるMorph |
| グラフィックコラージュ／タイトル | Composition、Texture、Typography、Transition | 作風と矛盾する写実的3D、soft glow、gentle dissolve |

## プロンプトを作る8レイヤー

8レイヤーは全項目を埋めるチェックリストではなく、演出を分解する判断軸である。`OBJECT`、`MOTION`、`TIMING`は必ず決める。それ以外は、ビートの目的に必要な場合だけ使う。

1. `OBJECT`：何を動かすか。例：Japanese headline、product silhouette、orange circle。
2. `MOTION`：どう動かすか。例：vertical slide、orbit、shape build。
3. `TIMING`：いつ、どの順序で動かすか。例：one word at a time、fast stagger、hold after landing。
4. `TRANSFORMATION`：形をどう変えるか。例：scale punch、fragment and reassemble、text morph。
5. `TRANSITION`：次へどう繋ぐか。例：shape wipe、match cut、object pass。
6. `TEXTURE`：どんな質感か。例：halftone、paper grain、film grain、refractive glass。
7. `CAMERA`：視点をどうするか。例：locked orthographic、subtle push-in、2.5D parallax。
8. `RHYTHM`：音や反復とどう同期するか。例：beat-synchronized、click on landing、seamless loop。

### 変換テンプレート

```text
Required: [OBJECT] performs one [MEANING ANCHOR] with [TIMING], then settles into [COMPLETED STATE] and holds.
Optional Dynamics: The action uses [DYNAMICS] and fully settles before the hold.
Optional Transition: The completed owner becomes [TRANSITION] into the next beat.
Optional Finish: Preserve [TEXTURE] under [CAMERA], synchronized to [RHYTHM].
```

### 弱い指定と強い指定

```text
弱い: kinetic typography, motion graphics, energetic

強い: The Japanese headline uses a word-by-word vertical mask reveal from below. Each word uses one restrained elastic overshoot, settles fully readable, then the completed text block becomes a shape wipe into the next scene.
```

## 1ビートへの適用ルール

- Movement、Reveal、Transformation、Transition、Impactなどから主動作カテゴリを1つだけ選ぶ。例：`slide in`と`morph`を同時に主動作にしない。
- 必要な場合だけDynamicsを1つ、TextureまたはLightを1つ加える。
- Transitionは次ビートへの接続が必要な場合だけ加え、Transformationと混同しない。
- 既定の時間設計、可読ホールド、カメラ、音、終端規則は[モーショングラフィックス共通文法](motion-graphics-core.md)に従う。

## 頻出語彙の選択表

### Movement / Dynamics

`slide in/out`、`push in/out`、`rise up`、`drop in`、`drift`、`float`、`glide`、`snap into place`、`scatter`、`orbit`、`scale up/down`、`pop`、`pulse`、`squash and stretch`、`rotate`、`spin`、`wobble`、`ease in/out`、`overshoot`、`anticipation`、`bounce`、`spring`、`elastic`、`recoil`、`follow through`、`inertia`、`drag`、`stagger`、`cascade`、`wave`。

### Reveal / Transition

`fade`、`opacity reveal`、`mask reveal`、`wipe`、`shape reveal`、`track matte`、`crop reveal`、`type-on`、`word-by-word`、`character-by-character`、`draw-on`、`ink reveal`、`particle dissolve`、`noise dissolve`、`smoke reveal`、`cut`、`cross dissolve`、`slide transition`、`push transition`、`zoom transition`、`whip pan`、`motion blur transition`、`match move`、`match cut`、`shape transition`、`color block wipe`、`geometric wipe`、`full-screen typography transition`、`glitch transition`。

### Transformation / Typography

`shape morph`、`object morph`、`text morph`、`logo morph`、`icon morph`、`liquid morph`、`blob morph`、`metaball morph`、`fragment and reassemble`、`explode and rebuild`、`shatter and reform`、`fold/unfold`、`kinetic typography`、`full-screen typography`、`type choreography`、`beat-synced typography`、`typewriter`、`text stomp`、`letter scatter`、`variable font animation`、`text stretch`、`text warp`、`text liquify`、`text reflow`、`dynamic typesetting`、`marquee text`。

### Graphic Shapes / Camera / Depth

`shape build`、`shape burst`、`circle burst`、`ring expansion`、`concentric circles`、`line animation`、`trim paths`、`animated stroke`、`motion trail`、`speed lines`、`repeater animation`、`grid repeater`、`pattern shift`、`zoom in/out`、`pan`、`tilt`、`push in`、`pull out`、`2.5D parallax`、`layered depth`、`dolly`、`orbit camera`、`crane`、`fly-through`、`tunnel zoom`、`infinite zoom`、`camera shake`、`crash zoom`、`depth of field`、`focus pull`。

### Blur / Distortion / Temporal

`motion blur`、`directional blur`、`zoom blur`、`spin blur`、`directional smear`、`echo trails`、`ghost trails`、`afterimage`、`light trails`、`glitch`、`RGB split`、`chromatic aberration`、`channel offset`、`scanlines`、`VHS/CRT distortion`、`screen tear`、`datamosh`、`pixel sorting`、`dither`、`pixel stretch`、`warp`、`turbulent displace`、`ripple distortion`、`lens distortion`、`speed ramp`、`time remapping`、`freeze frame`、`frame hold`、`frame skip`、`reverse`、`time slice`、`posterized time`。

### Texture / Material / Light / Color

`film grain`、`noise`、`film dust`、`film scratches`、`light leak`、`35mm/16mm/Super 8 look`、`halftone`、`risograph`、`CMYK misregistration`、`xerox`、`paper grain`、`rough edge`、`hand-drawn jitter`、`scribble`、`glow`、`bloom`、`neon glow`、`lens flare`、`color flash`、`hue shift`、`animated gradient`、`iridescent gradient`、`refraction`、`refractive glass`、`holographic effect`、`chrome`、`liquid chrome`、`metallic`、`glass`、`inflatable 3D`、`soft-body 3D`。

### Particles / Organic / Composition / UI / Rhythm / Impact

`particle system`、`particle burst`、`particle emitter`、`particle trail`、`particle dissolve`、`particle assembly`、`liquid motion`、`liquid wipe`、`ink flow`、`fluid morph`、`smoke`、`fog`、`fire`、`water ripple`、`growth animation`、`motion collage`、`cutout animation`、`mixed-media motion`、`graphic overlay`、`masking`、`split screen`、`floating cards`、`microinteraction`、`button press`、`card expansion`、`counter animation`、`number count-up`、`bar chart growth`、`seamless loop`、`beat sync`、`audio-reactive`、`impact`、`punch`、`slam`、`flash`、`impact shake`、`shockwave`、`freeze frame`、`hit stop`。

## まず覚える50語

`kinetic typography`、`mask reveal`、`wipe`、`slide in`、`scale pop`、`fade`、`shape animation`、`shape morph`、`text morph`、`overshoot`、`bounce`、`elastic`、`spring`、`squash and stretch`、`stagger`、`cascade`、`trim paths`、`stroke reveal`、`type-on`、`word-by-word reveal`、`stomp typography`、`full-screen typography`、`motion blur`、`zoom blur`、`whip pan`、`zoom transition`、`shape transition`、`match cut`、`match move`、`parallax`、`push-in`、`camera shake`、`impact shake`、`speed ramp`、`freeze frame`、`particle burst`、`particle dissolve`、`liquid morph`、`blob animation`、`glitch`、`RGB split`、`chromatic aberration`、`film grain`、`halftone`、`animated gradient`、`glow`、`collage animation`、`editorial motion`、`seamless loop`、`beat-synced motion`。

## 特徴的な検索語

一般的な広告MGから外れた表現を研究するときだけ使う。

`infinite zoom`、`Droste effect`、`datamosh`、`pixel sort`、`slit scan`、`scanimation`、`motion scan`、`feedback loop`、`recursive frames`、`kaleidoscope`、`mirror tunnel`、`portal transition`、`impossible transition`、`continuous transformation`、`semantic match cut`、`forced-perspective transition`、`anamorphic typography`、`fluid typography`、`type as image`、`negative-space animation`。

## 語彙選択の最終チェック

- 利用者が固定した動きを、追加提案で上書きしていない。
- 選択した主分類と語彙の主従が一致している。
- 1ビートあたりの主動作カテゴリが1つである。
- `OBJECT + MOTION + TIMING`が観測可能な文になっている。
- 標準語彙を意味アンカーとして残し、一般語への長い言い換えで消していない。
- 意味アンカーの後ろが同義反復ではなく、owner、起点／軸、方向、順序、次状態、完成状態のいずれかを追加している。
- `TRANSFORMATION`と`TRANSITION`を混同していない。
- Texture、Light、Distortionを目的なく重ねていない。
- 「全部のカテゴリを使う」構成になっていない。
- 選択した語彙がSKILL.mdのH3モード別ゲートを壊していない。
