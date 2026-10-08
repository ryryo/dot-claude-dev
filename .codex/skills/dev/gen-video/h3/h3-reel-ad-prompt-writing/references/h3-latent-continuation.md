# H3 AV latent継続

同一ショット、連続動作、連続トークなど、前クリップの時間履歴を保持する価値がある区間だけに使う。通常のAロール／Bロール編集や複数Ref2VA参照には使わない。

## 能力と前提

- 最初のクリップはH3 FL2VAでFirst FrameとLast Frameから生成する。
- Continueは前クリップのレンダリング済み最終画像ではなく、完全な映像＋音声latentとhandover metadataを直接使う。
- 各Continueは新しいLast Frameと任意のQwen参照画像1枚を受け取る。
- 同じH3 diffusion model、Qwen encoder、Video VAE、Audio VAE、解像度、基本sampling設定をチェーン全体で使う。
- seedは単位ごとに変えられる。連続性の主因はseedではなくAV latent contextである。
- 対応する`H3Continuous*`カスタムノードが実行環境に導入済みであることを確認する。

添付されたワークフローはFL2VAモデル＋任意のQwen参照画像1枚であり、複数素材のRef2VA latent continuationを保証しない。複数人物、商品、店舗、作風を個別参照する必要がある区間は`edited`または`hybrid`の`Independent`単位にする。

## チェーンを設計する

同じlatentを共有する単位へ安定した`continuation_group` IDを付ける。各単位は次を持つ。

| 項目 | 内容 |
| --- | --- |
| Unit | 生成単位番号 |
| Group | continuation group ID |
| Role | `Start`または`Continue` |
| Duration | H3へ要求する生成尺 |
| Previous latent | Continueが読む前単位の完全なAV latent |
| First Frame | Startだけに指定 |
| Last Frame | 各単位の目標終端 |
| Shared reference | 任意のQwen参照画像1枚 |
| Stitch role | 中間は`Stitch Ready`、現在の最終は`Final Clip` |
| Boundary reserve | 末尾から避ける重要な台詞、CTA、動作 |

チェーンを後から延長する場合、それまでの最終単位を`Final Clip`から`Stitch Ready`へ変更し、新しい最終単位だけを`Final Clip`にする。

## Startを記述する

Start実行表へ次を書く。

- First Frame
- Clip 1のLast Frame
- 任意の共通参照画像
- Clip 1プロンプト
- 解像度と生成尺
- 完全なAV latent、handover metadata、`head_context_frames=0`の保存先

Start後に映像をデコードし、終端のfreeze、理想handover位置、H3の時間位相に整合するcutoffを解析する。表示用に末尾をtrimしても、次の継続元には完全な未trim AV latentを保存する。

## Continueを記述する

Continue実行表へ次を固定値として書く。

- `context_frames = 22`
- `handover_mode = auto`
- `alignment_mode = phase_aligned_extended`
- 前単位の完全なAV latentとhandover metadata
- 新しいLast Frame
- Startと同じ共通参照、model、VAE、解像度

Continueは公式5モードへ新規に割り当て直す単位ではなく、前AV latentを入力するカスタムcontinuation実行である。新しいFirst Frameや架空の`Picture 1`を追加しない。プロンプト本文は次の3フィールドをこの順で出力し、新しいLast Frameはノード入力として実行表へ分離する。

```text
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

Startは通常のFL2VAなので、First FrameとLast Frameのalignment instructionに続けて同じ3フィールドを書く。実行環境がContinue用に追加wrapperを要求する場合は、導入済みworkflowの実入力契約を確認し、未確認のwrapperを創作しない。

位相整合のため、実際に再利用される先頭contextは22フレームより長くなる場合がある。Continueが返す`actual_head_context_frames`をSaveとStitchの両方へ渡し、推定値で置き換えない。

Continueのプロンプトは前状態を継続する。

```text
She continues speaking from the previous segment...
The camera continues the same slow forward motion...
His right hand completes the same folding action...
The room tone and movement continue without a reset...
```

`A new scene begins`のような再開始、人物・衣装・場所の再設計、Last Frameへ早く静止する強い指示を避ける。

## Handoverとtrim

H3がLast Frameへ収束する末尾にはfreezeや不安定なtailが生じ得る。Auto Handoverは次を決める。

- freeze開始位置
- 視覚的に安全な理想終端
- latent時間位相に整合する終端
- 次へ渡さないtailフレーム

freezeが見つからない場合も、fallbackで終端の安全余白を除外して位相整合位置を選ぶ。重要な台詞、CTA、商品動作を各クリップ末尾へ置かず、trimされても意味が欠けない余白にする。

- `Stitch Ready`: 再利用head contextとhandover後のtailを除去する中間クリップ。
- `Final Clip`: 再利用head contextだけを除去し、最終Last Frameへの着地を保持する最終クリップ。
- `Full`: trimしない検査・保存用途。完成映像の通常出力には使わない。

映像と音声は同じtrim範囲を使う。

## Seamless Join

既定の結合設定を実行表へ書く。

- Safe Tail Bridge: 最大2フレーム
- context-aligned video crossfade: 4フレーム
- audio de-click crossfade: 15 ms
- boundary luminance match: OFF

Safe Tail Bridgeは、位相整合cutoffと安全な理想終端の間にある有効な実フレームを最大2枚保持し、次クリップ冒頭から同数をskipする。freeze安全境界を越えず、音声境界を移動せず、総尺を増やさない。映像blendは短く保ち、ghostingが見える場合はフレーム数を減らす。輝度補正は明るさのdriftを作る場合があるため既定で使わない。

## 音声を設計する

AV latentは声、room tone、動作音の時間履歴を継続できる。ただしtrimとjoinがあるため、重要な一文を境界越しに分割しない。各単位内で台詞を完結させ、末尾は自然な呼吸、room tone、継続可能な動作音にする。

広告用BGM、長いナレーション、正確な音量調整はpost-editを既定にする。各クリップで別のBGMを生成して直接連結しない。

## 尺を扱う

目標完成尺とH3生成尺を分離する。

```text
estimated final duration
= sum(snapped generation durations)
- reused head contexts
- intermediate tail trims
- joined overlap
```

実際のhead contextとtail trimは生成後の解析まで確定しない。15秒、30秒などの正確な納品尺は、最終MP4の実尺を測定し、安定区間または独立Bロールをpost-editで調整する。生成前に確定尺を保証しない。

## Saved Chain

クリップを別々に生成する場合、番号付きの完全なAV latent、handover metadata、実際のhead context長を保存する。Saved Chain stitcherは同じVideo/Audio VAEで1クリップずつデコードし、小さな境界bufferだけを保持して最終MP4を書く。これによりRAM/VRAMのピークを全クリップ一括decodeより抑えられるが、保存latentのディスク使用量はチェーン長に応じて増える。

## 実行不能条件

次の場合、`continuous`を実行可能と案内しない。

- `H3ContinuousStartV11`、`H3ContinuousContinueV11`、handover、save、stitch系カスタムノードの導入を確認できない。
- カスタムノード実装または対応workflowが利用環境にない。
- チェーン内でmodel、VAE、解像度を統一できない。
- 必須の複数Ref2VA素材を単一Qwen参照へ安全にまとめられない。
- 前単位の完全なAV latentまたはhandover metadataが失われている。

このスキルは実行表とプロンプトを作るだけで、カスタムノードの存在、互換性、成果品質を保証しない。
