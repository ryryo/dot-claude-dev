# AIモーショングラフィックス語彙・演出設計リファレンス

## 目的

MiniMax H3向けプロンプトで、モーショングラフィックスの語彙を「エフェクト名の羅列」ではなく、観測可能な演出設計へ変換するための共通リファレンス。

```text
伝達目的 → 主カテゴリ → 具体語彙 → 観測可能な動作文
```

語彙を全投入しない。各ビートでは主動作を1つ、補助語彙を必要最小限だけ選ぶ。`dynamic`、`cinematic`、`professional` のような抽象語を、方向、距離、順序、着地、保持状態を表す具体語で置き換える。この資料は演出語彙が未確定、抽象的、または組み合わせ提案が必要な場合に使い、利用者が具体的な動きを固定している場合はその指定を優先する。

## 出典と扱い

以下のXスレッド内に掲載されたEffect Dictionary、頻出50語、8レイヤー、18カテゴリを、H3プロンプト向けに再構成したもの。

- https://x.com/ponzponz15/status/2089224411736100980
- https://x.com/ponzponz15/status/2089152588935803100
- https://x.com/ponzponz15/status/2089152585869722077

★の多さは投稿者の優先度・頻出度の目安であり、測定済みの市場統計やH3の成功率ではない。◆は特徴的・検索価値の高い表現を示す編集上の印である。モデルの再現性を保証する資料として扱わない。

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
Required: [OBJECT] performs one [PRIMARY ACTION] with [TIMING], then settles into [COMPLETED STATE] and holds.
Optional Dynamics: The action uses [DYNAMICS] and fully settles before the hold.
Optional Transition: The completed owner becomes [TRANSITION] into the next beat.
Optional Finish: Preserve [TEXTURE] under [CAMERA], synchronized to [RHYTHM].
```

### 弱い指定と強い指定

```text
弱い: kinetic typography, motion graphics, energetic

強い: The Japanese headline enters one word at a time from below with a fast vertical mask reveal. Each word briefly overshoots its final scale, settles with a restrained spring, and holds fully readable before the entire text block becomes a shape-wipe into the next scene.
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
- `TRANSFORMATION`と`TRANSITION`を混同していない。
- Texture、Light、Distortionを目的なく重ねていない。
- 「全部のカテゴリを使う」構成になっていない。
- 選択した語彙がSKILL.mdのH3モード別ゲートを壊していない。
