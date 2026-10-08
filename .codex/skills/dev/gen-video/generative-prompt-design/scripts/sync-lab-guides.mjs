#!/usr/bin/env node

import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const skillDirectory = path.resolve(scriptDirectory, "..");
const referenceDirectory = path.join(skillDirectory, "references");
const { mode, sourceRoot } = parseArguments(process.argv.slice(2));
const repositoryRoot = sourceRoot
  ? await validateRepositoryRoot(sourceRoot)
  : await findRepositoryRoot(process.cwd());

const [personData, shotData, coreData] = await Promise.all([
  import(pathToFileURL(path.join(repositoryRoot, "experiments/virtual-influencer-lab/public/person-prompt-data.mjs")).href),
  import(pathToFileURL(path.join(repositoryRoot, "experiments/virtual-influencer-lab/public/shot-prompt-data.mjs")).href),
  import(pathToFileURL(path.join(repositoryRoot, "experiments/virtual-influencer-lab/public/prompt-dictionary-core.mjs")).href),
]);

const { PROMPT_COLLECTION_SCOPE: personScope, PROMPT_ENTRIES: personEntries, PROMPT_PATTERNS: personPatterns } = personData;
const { PROMPT_ENTRIES: shotEntries, PROMPT_PATTERNS: shotPatterns, PROMPT_SCENARIO_PATTERNS: scenarioPatterns } = shotData;
const bodyEntries = selectEntries(personEntries, ["body"]);
const faceEntries = selectEntries(personEntries, ["face"]);
const skinHairEntries = selectEntries(personEntries, ["skin-hair"]);
const poseEntries = selectEntries(personEntries, ["pose-motion"]);
const continuityEntries = selectEntries(personEntries, ["reference-continuity"]);
const situationEntries = selectEntries(shotEntries, ["self-capture", "other-person-capture", "shot-context"]);
const captureEntries = selectEntries(shotEntries, ["capture-realism"]);

const outputs = new Map([
  ["design-contract.md", renderDesignContract()],
  ["positive-reconstruction.md", renderPositiveReconstruction()],
  ["prompts/person-reference-and-outfit.md", renderPatternReference({
    title: "人物と参照の設計パターン",
    sourcePaths: ["experiments/virtual-influencer-lab/public/person-prompt-data.mjs"],
    scope: personScope.description,
    patterns: personPatterns,
  })],
  ["prompts/young-adult-woman-body.md", renderEntryCatalog({ title: "若い成人女性：体型語彙", scope: personScope.description, entries: bodyEntries })],
  ["prompts/young-adult-woman-face.md", renderEntryCatalog({ title: "若い成人女性：顔立ち語彙", scope: personScope.description, entries: faceEntries })],
  ["prompts/young-adult-woman-skin-hair.md", renderEntryCatalog({ title: "若い成人女性：肌・髪・化粧語彙", scope: personScope.description, entries: skinHairEntries })],
  ["prompts/young-adult-woman-pose-motion.md", renderEntryCatalog({ title: "若い成人女性：姿勢・動作語彙", scope: personScope.description, entries: poseEntries })],
  ["prompts/reference-continuity.md", renderEntryCatalog({ title: "参照素材と連続性の語彙", scope: "参照素材の責務分離と連続性の方法は被写体を問わず利用できる。人物固有の顔・体型語彙は、それぞれの対象範囲を守る。", entries: continuityEntries })],
  ["prompts/shot-situation-camera-and-space.md", renderShotDesignReference({
    title: "状況・カメラ・空間の撮影設計パターン",
    sourcePaths: ["experiments/virtual-influencer-lab/public/shot-prompt-data.mjs"],
    patterns: shotPatterns,
  })],
  ["prompts/shot-scenario-playbooks.md", renderScenarioReference(scenarioPatterns)],
  ["prompts/influencer-shot-situations.md", renderEntryCatalog({
    title: "SNS撮影状況の語彙",
    entries: situationEntries,
    workflow: [
      ...shotData.PROMPT_PAGE_GUIDANCE.philosophy.flow.map(({ title, detail }) => ({ title, detail })),
      { title: "必要な語彙", detail: "閉じた撮影状況を英語Promptへ正確に移すため、このカタログから必要な表現だけを選ぶ。" },
    ],
  })],
  ["prompts/capture-realism.md", renderEntryCatalog({ title: "撮影らしさとカメラ表現の語彙", entries: captureEntries })],
]);

if (mode !== "--write" && mode !== "--check") {
  console.error("Usage: node sync-lab-guides.mjs --write|--check [--source-root /absolute/path/to/influencer-studio]");
  process.exitCode = 2;
} else if (mode === "--write") {
  await mkdir(referenceDirectory, { recursive: true });
  for (const [fileName, contents] of outputs) {
    const outputPath = path.join(referenceDirectory, fileName);
    await mkdir(path.dirname(outputPath), { recursive: true });
    await writeFile(outputPath, contents, "utf8");
    console.log(`wrote ${fileName}`);
  }
} else {
  const stale = [];
  for (const [fileName, expected] of outputs) {
    let actual = "";
    try {
      actual = await readFile(path.join(referenceDirectory, fileName), "utf8");
    } catch {
      stale.push(fileName);
      continue;
    }
    if (actual !== expected) stale.push(fileName);
  }
  if (stale.length) {
    console.error(`Generated prompt references are stale: ${stale.join(", ")}`);
    process.exitCode = 1;
  } else {
    console.log(`Generated prompt references are current: ${outputs.size}`);
  }
}

function renderDesignContract() {
  return generatedText(`
# 生成Promptの設計契約

この契約は完成Promptの要約ではない。利用者が欲しい画面から逆算し、参照素材、物理空間、人物または物体、撮影、時間の責務を衝突なく閉じるための作業票である。語彙を選ぶ前に記入し、成果を左右する欄が空なら完成文へ進まない。

## 1. 事実・要求・仮説を混ぜない

- 観測した事実: 参照素材や既存成果物から直接見えること。遮蔽部分や画角外は含めない。
- 維持する成果: 次稿でも必要な観測可能な結果。旧Promptの文面をそのまま維持条件にしない。
- 原因仮説: 未達を生んだ上流原因。事実と断定せず、成果物との因果で説明する。
- 今回の設計判断: 新しい状況を成立させるために決めること。
- 破棄する旧前提: 新設計と競合するため次稿へ持ち込まない前提。
- 合格条件: 画像、動画、音でYES / NOを判定できる結果。

## 2. 完成前に埋める欄

~~~text
利用者が得たい画面:
維持する成果:

参照素材の権限:
- 素材 → 許可する属性 → 優先順位 → 転写しない属性 → 見えないため未確定の属性

被写体の契約:
- 固有形状 → 表面・髪・衣装の構造 → 接地・重心 → 表情・視線

空間の契約:
- 場所の用途 → 建築上のつながり → 区画 → 家具・小物の利用者と用途 → 通路 → 光源

撮影の契約:
- 撮影者 → カメラの起点 → 高さ・距離・画角 → 切り取り → 前景・中景・後景

時間の契約（動画のみ）:
- [Shot] → 区画 → 初期状態 → きっかけ → 被写体の反応 → 記録画面の反応 → 終了フレーム

破棄する旧前提:
成果物での合格条件:
生成先へ渡す境界: 画像/動画、尺、比率、参照数、文字数など
DESIGN_STATUS: PASS / REBUILD / BLOCKED
PROVIDER_HANDOFF_READY: YES / NO
~~~

静止画では「時間の契約」を一つの観測瞬間へ置き換える。直前に何が起き、どこへ力が掛かり、その瞬間に手足・衣装・小物・視線がどう落ち着いているかを一枚へ閉じる。動画では初期状態から終了フレームまでを尺内の順序として閉じる。

## 3. 欄同士をつなぐ

各合格条件には、それを生む上流の欄が必要である。

- 「同じ人物に見える」なら、顔・髪・体型の参照権限とショット間の優先順位が必要。
- 「自然なカフェに見える」なら、店の用途、客席区画、家具の用途、通路、光源が必要。
- 「ヒップが前景で大きく見える」なら、固有体型とは別に、支持面、骨盤の向き、最接近点、カメラ高、距離、画角、切り取りが必要。
- 「声掛けでポーズが生まれる」なら、声を聞ける初期状態、聞く間、身体反応、記録画面の追従、自然に落ち着く終了フレームが必要。
- 「背景が簡潔に見える」なら、禁止物の一覧ではなく、場所を説明する大きな面、用途を示す少数の機能物、主役より低い情報密度が必要。

一つの要望を一つの形容詞へ押し込まない。被写体の固有形状、衣装構造、ポーズと接地、カメラによる見え方は別々に設計し、最後に一画面へ結ぶ。

## 4. 参照素材の権限

参照素材は「一枚一役」と機械的に狭めず、素材ごとに許可する属性集合を決める。複数素材が同じ属性を供給するときは優先順位を決める。見えない部分を補完するときは観測事実ではなく設計判断として記録する。

衣装では、色や名称より先に、前身頃と後身頃、開口部、肩紐の起点と終点、袖ぐり、脇線、層の重なり、素材、身体への沿い方、裾を観察する。正面に見える線を、根拠なく背面線や追加の肩紐として重ねない。

## 5. 空間と撮影

同じ場所を複数ショットで使うなら、各ショットへ家具を足して場所を似せるのではなく、先に一つの平面を作る。人物がどの区画へ移り、カメラがどこからどこへ移るかを決める。素材や色の反復だけを同一場所の根拠にしない。

画面外の撮影者を詳しく人物化する前に、記録画面で見える変化へ翻訳する。カメラの持ち主、初期構図、きっかけ、被写体の画面内移動、パン・ティルト・移動・傾き、行き過ぎ、回復後の終了フレームを順に決める。

## 6. 合否判定

DESIGN_STATUSは次で判定する。

- PASS: 必要な欄が埋まり、欄同士の競合がなく、全合格条件を成果物で判定できる。
- REBUILD: 現在の情報で設計を戻せば解消できる未成立または競合がある。
- BLOCKED: 成果を左右する参照素材または利用者判断がなく、合理的な仮定では結果が分岐する。

Promptに希望語が書かれていることはPASSの根拠にならない。生成先の形式、尺、比率、参照上限などが未確定でも設計自体はPASSにできるが、その場合はPROVIDER_HANDOFF_READYをNOにする。DESIGN_STATUSがREBUILDまたはBLOCKEDの間は生成サービス固有形式へ変換しない。
`);
}

function renderPositiveReconstruction() {
  return generatedText(`
# 肯定的再構築

## 原則

生成Promptの実質的な修正は、旧文へ「禁止」「追加」「変更」を重ねる編集ではない。実成果物の症状を観察し、その症状を生んだ上流の状況、参照権限、物理構造、出来事、撮影を作り直す。望む画面が、禁止文を読まなくても新しい状況から自然に一つへ定まる状態を目標にする。

否定表現を一切使わないという規則ではない。参照素材から転写しない属性、権利・安全境界、生成サービス固有の禁止欄には使える。しかし人物数、背景、家具、ポーズ、構図、カメラの成立を否定文へ依存させない。

## なぜ追記修正が失敗するか

「鏡を出さない」「ソファを追加」「カメラを低くする」「脚を大きくする」は、画面に現れた症状だけを指す。生成モデルは、その背後にある店の用途、家具の接続、人物の接地、カメラと被写体の距離を同時には再設計しない。そのため旧状況と新しい命令が競合し、別の不自然さとして現れる。

修正単位は語句ではなく、意味が閉じる範囲で決める。家具を変えるならその家具を使う人物、隣接区画、通路、カメラ位置まで。ポーズを変えるなら支持面、重心、自由な手足、衣装との接触、見える身体関係まで戻る。

同じ成果物で複数の未達が見つかっても、原因系が異なるものを一つの診断へまとめない。空間の整合性、衣装構造、人物のポーズ、カメラによる遠近は、それぞれ独立して原因と合格条件を閉じる。各部分契約が成立した後でだけ、一つの完成Promptへ統合する。

## 実務手順

### 1. 成果物を観察する

旧Promptを先に直さない。画像または動画を見て、期待との差を位置、接地、前後関係、画面占有、切り取り、動作順、保持時間、音として書く。

悪い診断: 「背景がうるさい」「ポーズが弱い」「タンクトップがおかしい」

使える診断:

- 壁面に用途の読めない小物が五つあり、人物の輪郭より先に目へ入る。
- ヒップと近い太ももが上体より小さく、最接近点が画面中央より奥にある。
- 前身頃のU字開口部へ、起点と終点の説明できない線が交差している。

### 2. 維持する成果を観測結果で固定する

同じ顔、衣装の色、自然な表情など、既に成立した成果を列挙する。旧Promptの段落や語句をそのまま保存対象にしない。原因を含む文章を保存すると、新設計へ競合が再流入する。

### 3. 因果を上流へたどる

次の順に「この画面を直接決めているものは何か」をたどる。

1. 観測結果: 画面のどこに何が、どの大きさ・順序で見えるか。
2. 撮影: カメラの持ち主、高さ、距離、画角、切り取り、移動。
3. 被写体の状態: ポーズ、接地、重心、手足の役割、視線、動作。
4. 物理状況: 場所の用途、区画、家具の用途、通路、光源。
5. 参照権限: どの素材がどの属性を供給し、何を供給しないか。

最初に矛盾する層が修正の起点である。下流の形容詞で上流の欠落を隠さない。

### 4. 影響範囲を広げる

| 起点 | 必ず一緒に再設計する範囲 |
| --- | --- |
| 場所・家具の用途 | 場所全体の用途、平面、隣接区画、人物動線、全ショットのカメラ位置、同一場所の可視根拠 |
| カメラ位置・距離・画角 | 構図、切り取り、前景・中景・後景、ポーズの見え方、終了フレーム |
| ポーズ・支持面 | 接地点、重心、自由な手足、衣装との接触、身体の前後関係、カメラから見える輪郭 |
| 衣装構造 | 全ショット共通の前後面、開口部、縁の接続、肩紐、袖ぐり、層、素材、裾、身体露出 |
| 人物・参照素材の責務 | 全素材の許可属性、優先順位、転写しない属性、遮蔽された未知、ショット間の同一性 |
| きっかけ・動作順 | 初期状態、聞く／気づく間、被写体の反応、記録画面の反応、保持、音声 |
| 誤字・正確な台詞・スキーマのみ | 該当箇所だけ。生成内容と因果が変わらないことを確認 |

### 5. 競合する旧前提を明示的に破棄する

新しい状況と両立しない旧前提を「破棄する旧前提」へ移す。完成Promptに破棄一覧を大量投入するためではなく、書き手が無意識に再利用しないための作業である。

例: 「同じ壁材なら同じ店舗に見える」「理想構図ごとに家具を独立配置してよい」「前景不足は体型語を強めれば直る」。

### 6. 用途と因果から肯定形を作る

欲しい物を直接足すのではなく、それが必要になる利用者、用途、支持関係、出来事を決める。

- 背景を簡潔にする: 静かなラウンジ区画として、大きな壁面、連続する座面、窓光、カップ用の小さな脇テーブルだけで場所の用途が読めるようにする。
- 画面内を一人にする: 画面外の撮影者が背面カメラで一人の主役を追い、最初から主役だけを記録画面へ置く。
- ポーズを作る: 声掛けを聞ける初期姿勢、身体を支える面、重心移動、手の置き場、最後に落ち着く形を連続させる。
- 背景情報量を下げる: 主役を第一の情報層、場所を説明する大きな面を第二層、行動に必要な機能物を一つの第三層にする。奥ほど輪郭密度と鮮明さを下げる。

### 7. 反実仮想で監査する

完成前に次を問う。

- 否定文を外しても、望む人物数・背景・家具・構図になるか。
- 被写体を消しても、家具配置と通路だけで場所の用途を説明できるか。
- カメラ語を消しても、人物の接地と重心は物理的に成立するか。
- 体型語を平均的に戻しても、前景と後景の大小関係は撮影設計だけで残るか。
- 一つのショットを平面図へ戻したとき、前後のショットからそこへ移動できるか。
- 参照素材を一枚ずつ外したとき、失われる属性を一意に説明できるか。

一つでもNOなら、NOを生んだ上流欄へ戻る。否定文を増やさない。

## 実例1: 三つのカフェ構図を一つのラウンジ区画から作る

### 症状

各ショットへ窓、木製テーブル、ソファを個別に置いたため、同じ色調でも別々の店に見える。最後のショットだけソファ前提へ変えたので、前のショットの家具用途とつながらない。

### 保持する成果

同じカフェ内で、窓辺の立位、カップを持つ着座、角のソファへ腰掛ける三つの撮影場面が連続すること。人物、衣装、ポーズの細部はこの空間契約の判定対象にしない。

### 上流原因

店の用途と平面を決める前に、ショットごとの理想構図から家具を置いた。家具の利用者、用途、通路、隣接区画が決まっていないため、共通の色や素材だけが同一店舗の根拠になった。

### 肯定的な再構築

場所を、窓沿いから壁の角まで造作ソファが続く小さなカフェラウンジ区画として先に決める。座面の縫い目、低い木製台座、窓からの光が一方向へ連続する。カップを置く小さな丸い脇テーブルは通常着座位置の腕が届く横にあり、人物の正面や通路を塞がない。角の深い座席にはテーブルを置かず、斜めに腰掛けられる余白がある。

- [Shot 1]: 窓側のソファ端の横で立つ。座面端と木製台座が画面下へ入り、次の着座位置が同じ方向に見える。
- [Shot 2]: 同じ座面へ一席分移り、脇テーブルからカップを取る。座面の縫い目、台座、窓光が[Shot 1]から連続する。
- [Shot 3]: 壁沿いにもう一席進んだ角へ腰掛ける。脇テーブルは前の席の用途物なのでこの画角には入らず、角の座面と壁沿いの余白を使う。

### 合格条件

- 三ショットで座面、台座、光方向の連続が二つ以上読める。
- 脇テーブルはカップを置く席の横にだけあり、角の座席や通路を塞がない。
- 各ショットの人物位置とカメラ位置を一つの平面上へ置ける。
- 家具の用途と店舗の連続性を、人物の体型やポーズの成否と分けて判定できる。

## 実例2: ヒップの前景強調を体型語の追加で直さない

### 症状

人物の体型とソファへの着座は成立しているが、カメラが遠く、近いヒップと太ももが上体より小さい。ラフで意図した、ヒップラインから近い脚へ続く大きな前景形状になっていない。

### 保持する成果

人物固有の体型、ソファ角への斜め座り、上体を起こした自然な表情。カフェの平面と家具用途は別の空間契約ですでに確定しているものとして扱う。

### 上流原因

「ヒップを強調する」という評価語を人物の体型へ足し、前景の大小関係を作る支持面、骨盤の向き、近い脚、カメラ高、距離、画角、切り取りを閉じていない。

### 肯定的な再構築

骨盤と遠い手のひらを角の座面へ接地し、その支持で上体を起こす。骨盤をカメラへ近い側へ回し、近い膝を曲げて太ももを画面下へ送る。座面高の近距離カメラをヒップの斜め前へ置き、近いヒップを下中央の最接近点、近い太ももを右下の最大形状、上体と顔を左上の小さい後景にする。人物固有の体型は別に維持し、遠近による大小関係を体型語へ依存させない。

### 合格条件

- 骨盤と支える手が座面へ接地し、上体の重さを説明できる。
- 近いヒップと太ももが上体より大きく見える。
- 近い太ももが画面下端または右下端へ達する。
- 体型を平均的な記述へ置き換えても、前景と後景の大小関係が撮影設計だけで残る。
- 店舗の家具配置を変更せず、このポーズとカメラの部分契約だけを評価できる。

## 実例3: タンクトップの謎の二重線を衣装構造から直す

### 症状

前面の開口部へ、背面の襟ぐりまたは追加の肩紐のような線が重なり、前身頃と背面の境界が読めない。

### 弱い修正

「二重線を禁止」「余計な肩紐を削除」とだけ書く。これでは、どの線が正しく、どこからどこへ接続するかが未定義のままである。

### 肯定的な再構築

観測できる前身頃を一枚の布面として決める。前面には低く広いU字開口部が一つあり、細い縁取り一本が左右の肩へ連続する。内側に実際に見える別色の肩紐がある場合だけ別層として記録する。脇線、袖ぐり、裾、素材の伸び、胸とウエストへの沿い方を接続する。髪や腕で隠れた背面は未知として残し、前面へ新しい線として投影しない。

胸元の見え方は、開口部の深さだけで決めない。人物固有の胸郭と胸部、左右の間隔、衣装の張力、姿勢、カメラ角度を別々に設計し、最後に一画面へ結ぶ。

### 合格条件

- 前身頃が一枚の連続した布面として読める。
- U字開口部とその縁取りが一組だけ読める。
- 各肩紐の起点・終点・所属する層を説明できる。
- 遮蔽された背面構造が根拠のない前面線として現れない。

## 実例4: 背景の違和感を物体名の禁止一覧で直さない

### 症状

鏡、スイッチ、空調、配管、非常口表示など、用途や設置関係の読めない小物が壁へ散り、人物より高い輪郭密度を作っている。

### 上流原因

「カフェらしい詳細」を物体数で表現し、場所の用途、建築面、情報の優先順位を決めていない。

### 肯定的な再構築

静かな客席区画として、漆喰壁、窓、連続する座面、木製台座という大きな面で場所を作る。人物の行動に必要なカップと脇テーブルだけを機能物として置く。設備を描く必要がある場合は、建築上自然な位置と用途を持つものだけを背景の低い情報層へ置く。奥ほどコントラスト、輪郭密度、鮮明さを下げる。

### 合格条件

- 最初に人物の顔と身体の輪郭、次に場所の大きな面、最後に機能物が読める。
- 背景の各物体について、その利用者または建築上の用途を説明できる。
- 背景物の有無を個別の禁止語に依存しない。

## 最終判定

次がすべてYESならDESIGN_STATUSをPASSにできる。

1. 症状を成果物の観測関係として記録した。
2. 維持する成果と破棄する旧前提を分けた。
3. 最初に矛盾する上流層を特定した。
4. 影響範囲の状況全体を肯定形で再構築した。
5. 否定文を外しても望む画面が自然に成立する。
6. 合否をPromptの語句ではなく成果物で判定できる。

一つでもNOなら、完成Promptを整える前に該当する上流欄へ戻る。
`);
}

function renderPatternReference({ title, sourcePaths, patterns, scope }) {
  const lines = ["# " + title, "", "## 正本", "", ...sourcePaths.map((sourcePath) => "- `" + sourcePath + "`"), ""];
  if (scope) lines.push("## 対象範囲", "", ordinaryJapanese(scope), "");
  for (const pattern of patterns) lines.push(...renderPattern(pattern));
  return generated(lines);
}

function renderShotDesignReference({ title, sourcePaths, patterns }) {
  const philosophy = shotData.PROMPT_PAGE_GUIDANCE.philosophy;
  const imageSpace = shotData.PROMPT_PAGE_GUIDANCE.imageSpace;
  const lines = [
    "# " + title, "",
    "この資料は、撮影語彙を選ぶ前に、撮る理由から終了フレームまでを一つの物理状況として閉じるために使う。", "",
    "## 状況から組み立てる順序", "",
    philosophy.introduction, "",
    ...philosophy.flow.map(({ title: stepTitle, detail }, index) => `${index + 1}. **${stepTitle}**: ${ordinaryJapanese(detail)}`),
    "6. **終了フレーム**: 出来事とカメラの反応が落ち着いた後、何がどこに見えるかを確定する。", "",
    "## 記録画面を閉じる六段階", "",
    "画面外の物理を詳述する前に、生成結果で直接観測できる六項目を埋める。撮影者の身体運動を考えた場合も、最後に記録画面の変化へ翻訳してから生成先へ渡す。", "",
  ];
  for (const branch of imageSpace.ownershipBranches) {
    lines.push("### " + branch.title, "");
    for (const row of branch.rows) {
      const detail = row.label === "Promptの開始点" ? "`" + row.detail + "`" : ordinaryJapanese(row.detail);
      lines.push(`- **${row.label}**: ${detail}`);
    }
    lines.push("");
  }
  const sequenceLabels = new Map([
    ["camera ownership", "カメラの持ち主"],
    ["initial recorded composition", "初期の記録画面"],
    ["visible trigger", "画面で見えるきっかけ"],
    ["image-space response", "記録画面の反応"],
    ["overshoot", "行き過ぎ"],
    ["recovery / end frame", "回復／終了フレーム"],
  ]);
  for (const [index, item] of imageSpace.sequence.entries()) {
    const detail = item.label === "camera ownership" ? "`" + item.detail + "`" : ordinaryJapanese(item.detail);
    lines.push(`${index + 1}. **${sequenceLabels.get(item.label) ?? ordinaryJapanese(item.label)}**: ${detail}`);
  }
  lines.push("", "### 尺の目安", "");
  for (const item of imageSpace.durationBudget) lines.push(`- **${item.duration}**: ${ordinaryJapanese(item.detail)}`);
  lines.push("", ordinaryJapanese(imageSpace.calibrationNote), "", "## 同期した設計パターン", "", "正本:", ...sourcePaths.map((sourcePath) => "- `" + sourcePath + "`"), "");
  for (const pattern of patterns) lines.push(...renderPattern(pattern));
  return generated(lines);
}

function renderPattern(pattern) {
  return [
    "## " + pattern.title, "",
    "- ID: `" + pattern.id + "`",
    ...(pattern.subjectScope ? ["- 対象: `" + pattern.subjectScope + "`"] : []),
    "- 使う場面: " + ordinaryJapanese(pattern.whenToUse),
    "- 要約: " + ordinaryJapanese(pattern.summary), "",
    "### 構造", "", ...pattern.structure.map(({ label, detail }) => "- `" + label + "`: " + ordinaryJapanese(detail)), "",
    "### Promptのひな型", "", "```text", pattern.template, "```", "",
    "### 注意", "", ...pattern.cautions.map((caution) => "- " + ordinaryJapanese(caution)), "",
    "適用上の限界: " + ordinaryJapanese(pattern.evidenceNote), "",
    "用途: **" + mediumLabel(pattern) + "**",
    "",
  ];
}

function renderEntryCatalog({ title, entries, scope, workflow }) {
  const lines = ["# " + title, "", "同期件数: " + entries.length, ""];
  if (scope) lines.push("## 対象範囲", "", ordinaryJapanese(scope), "");
  if (workflow?.length) {
    lines.push("## 語彙を選ぶ前の手順", "", "このカタログは撮影設計の最後の段階で使う。次の順序を閉じてから、個別の語彙を選ぶ。", "");
    for (const [index, item] of workflow.entries()) lines.push(`${index + 1}. **${item.title}**: ${ordinaryJapanese(item.detail)}`);
    lines.push("");
  }
  const commonCautions = repeatedCautions(entries);
  if (commonCautions.length) lines.push("## カタログ共通の注意", "", ...commonCautions.map((caution) => "- " + ordinaryJapanese(caution)), "");
  for (const [category, categoryEntries] of groupBy(entries, (entry) => entry.category)) {
    lines.push("## " + category, "");
    for (const [slot, slotEntries] of groupBy(categoryEntries, (entry) => entry.slot)) {
      lines.push("### `" + slot + "`", "");
      for (const entry of slotEntries) {
        lines.push("#### " + entry.en, "", "- ID: `" + entry.id + "`", "- subcategory: " + ordinaryJapanese(entry.subcategory), "- 日本語: " + ordinaryJapanese(entry.ja));
        if (entry.aliases.length) lines.push("- aliases: " + entry.aliases.map((alias) => "`" + alias + "`").join(", "));
        lines.push("- Prompt phrase: `" + entry.phrase + "`", "- 用途: **" + mediumLabel(entry) + "**");
        if (entry.incompatibleWith.length) lines.push("- 同時使用を避けるID: " + entry.incompatibleWith.map((id) => "`" + id + "`").join(", "));
        for (const caution of entry.cautions) if (!commonCautions.includes(caution)) lines.push("- 注意: " + ordinaryJapanese(caution));
        lines.push("");
      }
    }
  }
  return generated(lines);
}

function repeatedCautions(entries) {
  const counts = new Map();
  for (const entry of entries) for (const caution of entry.cautions) counts.set(caution, (counts.get(caution) ?? 0) + 1);
  return [...counts].filter(([, count]) => count > 1).map(([caution]) => caution);
}

function renderScenarioReference(patterns) {
  const lines = ["# 撮影シナリオ集", "", "同期件数: " + patterns.length, ""];
  for (const pattern of patterns) {
    lines.push(...renderPattern(pattern), "### ショット構成", "");
    for (const shot of pattern.shotOutline ?? []) lines.push("- " + shot.label + " **" + shot.title + "**: " + ordinaryJapanese(shot.detail));
    lines.push("");
  }
  return generated(lines);
}

function mediumLabel(item) {
  return coreData.MEDIA_APPLICABILITY_LABELS[coreData.mediaApplicability(item)];
}

function ordinaryJapanese(value) {
  return String(value)
    .replace(/\bfront-camera\b/giu, "前面カメラ")
    .replace(/\brear-camera\b/giu, "背面カメラ")
    .replace(/\bcamera\b/giu, "カメラ")
    .replace(/\bpose\b/giu, "ポーズ")
    .replace(/(?<!\[)\bshot\b/giu, "ショット")
    .replace(/\bcrop\b/giu, "切り取り")
    .replace(/\blens gaze\b/giu, "レンズへの視線")
    .replace(/\bpreview gaze\b/giu, "プレビュー確認の視線")
    .replace(/\blens\b/giu, "レンズ")
    .replace(/\bmodel\b/giu, "モデル")
    .replace(/\bframe\b/giu, "フレーム")
    .replace(/\bscene\b/giu, "シーン")
    .replace(/\bangle\b/giu, "角度")
    .replace(/\bsection\b/giu, "セクション")
    .replace(/\bslot\b/giu, "欄")
    .replace(/\bgaze\b/giu, "視線")
    .replace(/\bpreview\b/giu, "プレビュー")
    .replace(/\bscreen\b/giu, "画面")
    .replace(/\bnoise\b/giu, "ノイズ")
    .replace(/\bphone\b/giu, "スマートフォン")
    .replace(/\bdevice\b/giu, "端末")
    .replace(/\bpixel\b/giu, "ピクセル")
    .replace(/\bvilla\b/giu, "ヴィラ")
    .replace(/\bpool\b/giu, "プール")
    .replace(/\bunderwater\b/giu, "水中")
    .replace(/\bselfie\b/giu, "セルフィー")
    .replace(/\bforeground\b/giu, "前景")
    .replace(/\bbackground\b/giu, "背景")
    .replace(/\bfocus\b/giu, "焦点")
    .replace(/\bexposure\b/giu, "露出")
    .replace(/\bmotion\b/giu, "動き")
    .replace(/\bidentity\b/giu, "同一性")
    .replace(/\bprofile\b/giu, "横顔")
    .replace(/\bsnapshot\b/giu, "スナップ")
    .replace(/\blayout\b/giu, "レイアウト")
    .replace(/\bruntime\b/giu, "実行時間");
}

function selectEntries(entries, categories) {
  const allowed = new Set(categories);
  return entries.filter(({ category }) => allowed.has(category));
}

function groupBy(items, keyFor) {
  const groups = new Map();
  for (const item of items) {
    const key = keyFor(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
}

function generated(lines) {
  return "<!-- Generated by scripts/sync-lab-guides.mjs. Do not edit directly. -->\n" + lines.join("\n").trim() + "\n";
}

function generatedText(contents) {
  return "<!-- Generated by scripts/sync-lab-guides.mjs. Do not edit directly. -->\n" + contents.trim() + "\n";
}

async function findRepositoryRoot(startDirectory) {
  let candidate = path.resolve(startDirectory);
  while (true) {
    try {
      await access(path.join(candidate, "experiments/virtual-influencer-lab/public/person-prompt-data.mjs"));
      return candidate;
    } catch {
      const parent = path.dirname(candidate);
      if (parent === candidate) throw new Error("Run this script from influencer-studio or pass --source-root /absolute/path/to/influencer-studio.");
      candidate = parent;
    }
  }
}

function parseArguments(args) {
  let mode;
  let sourceRoot;
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === "--write" || argument === "--check") {
      if (mode) throw new Error("Choose exactly one of --write or --check.");
      mode = argument;
      continue;
    }
    if (argument === "--source-root") {
      sourceRoot = args[index + 1];
      index += 1;
      if (!sourceRoot) throw new Error("--source-root requires a path.");
      continue;
    }
    if (argument.startsWith("--source-root=")) {
      sourceRoot = argument.slice("--source-root=".length);
      if (!sourceRoot) throw new Error("--source-root requires a path.");
      continue;
    }
    throw new Error(`Unknown argument: ${argument}`);
  }
  return { mode, sourceRoot };
}

async function validateRepositoryRoot(candidate) {
  const root = path.resolve(candidate);
  await access(path.join(root, "experiments/virtual-influencer-lab/public/person-prompt-data.mjs"));
  await access(path.join(root, "experiments/virtual-influencer-lab/public/shot-prompt-data.mjs"));
  return root;
}
