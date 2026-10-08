# グラフィックコラージュ／タイトルシーケンス

## 選択条件

ポスター、雑誌、パルプ、ミッドセンチュリー、切り絵、シルエット、色面パネル、タイトル、タグライン、クレジットを中心に、作風そのものを強く見せる場合に選ぶ。

## 参照役割を分離する

参照画像や動画から何を使い、何を無視するかを明示する。

- Character reference: identity、silhouette、衣装、角や髪などの特徴
- Palette reference: 背景色、主色、アクセント色
- Typography reference: 書体カテゴリ、太さ、字間、配置比率
- Motion reference: cut rhythm、panel assembly、smoke trailなどの時間構造
- Composition anchor: 具体的な開始／終了フレームとして使う場合だけ指定

参照画像の人物だけを使う場合、背景、pose、compositionまで誤って固定しない。Ref2VAではこれらを別の `<Subject N>` として追跡する。

## 作風を操作可能にする

抽象的な作風名だけでなく、観測できる要素へ分解する。

- flat color-block panels
- hard-edged silhouettes
- limited palette
- halftone、paper grain、rough print edges
- smoke-trail or line-draw accents
- bold condensed title + smaller wide-tracked tagline

複合トーンは必要な場合だけ `60% smoky decadence / 40% wry charisma` のように主従を示し、互いに矛盾する品質語を並べない。

## モーションと転換

主役のシルエット、文字、色面から転換を作る。

- silhouette wipe
- color-block flash cut
- smoke-trail or line-draw wipe
- object or glass-clink match cut
- black-frame impact cut
- split-screen reconfiguration
- shape-matched iris

転換パレットから各カットに最適な1つを選ぶ。すべてを1本へ詰め込まない。soft dissolve、無目的なfluid morph、gentle fadeは、選択した作風と矛盾する場合に除外する。

## タイトルとクレジット

- 表示可能なtitle、tagline、role、nameを完全なallowlistにする。
- 各roleとnameを1回だけ表示する。
- タイトルは主書体、タグラインは副書体または字間で階層化する。
- 完成後0.9–1.3秒を目安に静止保持する。
- シルエットが文字の背後から現れる場合も、字形の輪郭を隠さない。

## カメラと音

コラージュ内のpanel motionを優先する。zoom punchやwhip-panを使う場合は、強いgraphic cutへ限定し、次の完成構図で停止させる。

音楽は作風に合う具体的な楽器編成と時間変化を書く。title slam、panel assembly、object match、final freezeへ短いimpactやwhooshを同期し、連続する大音量で階層を潰さない。

## 失敗条件

- 参照画像の背景、姿勢、構図まで無条件に複製する。
- 作風語だけが多く、色面、線、シルエット、文字の観測可能な指定がない。
- タイトル、タグライン、クレジットが同時に現れて読む順序がない。
- 転換が多すぎて、完成したタイトルの保持時間がない。
- コラージュなのに写実的3D、柔らかいgradient、不要なglowへ崩れる。

## 事例根拠

- https://x.com/koldo2k/status/2088029008994685392
