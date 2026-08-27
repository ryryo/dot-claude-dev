---
name: h3-article-image-video-production
description: 記事LPの画像や既存動画について、動画化の必要性、追加素材、H3表現、モーショングラフィックス、尺、生成後の修正方針を記事文脈と実配置から判断し、制作・レビュー・採用まで進める。記事内メディアのH3動画化、新規カット設計、失敗候補のブラッシュアップ、Lab更新で使う。単体リール広告だけの企画には使わない。
---

# H3記事画像動画化

記事内の一素材を派手に動かすことではなく、その掲載位置で不足している理解を映像で補う。個別の成功例を固定レシピにせず、次の判断ループを毎回回す。

`記事内の役割を特定 → 伝達不足を診断 → 表現手段を選択 → 素材不足を補完 → 生成 → 実配置で評価 → 失敗原因を分類 → 次の一手を選択`

## 守ること

- 対象画像だけで判断せず、記事全体、前後の文章、実際の掲載サイズ、既存Labと素材一覧を先に確認する。
- 動きが意味を増やさない場合は、静止画維持を正式な結論にできる。
- ○×、矢印、「でも」、痛み表現、追加画像、5秒尺などを既定値にしない。伝達機能と不足の診断から選ぶ。
- 最新のユーザー指示を古いカタログや過去案より優先する。明示された文言、効果、制作主体、生成サービスは、変更許可が出るまで固定条件として引き継ぐ。
- 技術的に生成できたことと採用を分ける。採用はユーザーの明示承認後だけ記録する。
- ユーザーが計画、診断、レビューだけを依頼した場合は生成やLab更新まで拡張しない。
- 有料生成は事前検証後、承認された条件で一件ずつ行う。自動再試行や無断の尺・解像度・サービス変更をしない。

## 必要な参照を選ぶ

全参照を毎回読む必要はない。現在の判断に必要なものを読む。

- 動画化の可否、記事内役割、表現クラス、尺を決めるときは [editorial-decision-loop.md](references/editorial-decision-loop.md) を読む。
- 既存素材で足りるか、追加画像や参照フレームが必要か、H3モードを決めるときは [source-frame-and-reference-strategy.md](references/source-frame-and-reference-strategy.md) を読む。
- モーショングラフィックス、文字、記号、追従効果の要否を決めるときは [visual-language-and-motion-strategy.md](references/visual-language-and-motion-strategy.md) を読む。
- 候補をレビューし、局所修正・再設計・再生成・採否を決めるときは [diagnosis-and-refinement-loop.md](references/diagnosis-and-refinement-loop.md) を読む。
- スキル自体を更新・回帰検証するときだけ [behavioral-fixtures.md](references/behavioral-fixtures.md) を読む。通常の記事動画制作では読み込まない。

## ワークフロー

### 1. 文脈と現在地を調査する

最初に次を確認する。

- 記事全体と対象箇所の前後
- 対象メディアの実表示サイズ、縦横比、無音・自動再生・ループ条件
- 記事全体の編集テンポと、対象カットの局所的な役割
- 既存画像、動画、切り出せる区間、商品・人物・様式の参照
- Labの一覧、詳細、設計契約、prompt、manifest、review、採否状態
- ユーザーが承認した要素、却下理由、最新の修正指示

LP全体がすでに担う導入、説明、CTAまで一カットへ詰め込まない。既存動画は全尺利用だけでなく、有効区間の切り出しも候補にする。

### 2. Article Video Briefを確定する

生成方法を考える前に、次を短く記録する。

```markdown
## Article Video Brief
- placement:
- article_role:
- audience_change: 読者に起こしたい理解・感情・行動
- motion_value: 静止画では不足し、時間表現で増える意味
- single_message: 実サイズ・無音でも一目で伝える一つの内容
- video_owns: 動画が担う情報
- page_owns: 前後本文やCSSへ任せる情報
- fixed: 文言、商品形状、人物、効果、サービスなど変更不可の条件
- flexible: 変更可能な条件
- forbidden: 起こしてはいけない転写、物理、表現、主張
- success_observation: 合格時に画面上で観察できる状態
```

`motion_value` を具体的に説明できなければ、静止画維持または別媒体を検討する。

### 3. Production Decisionを作る

関連する参照を読み、次を確定する。

```markdown
## Production Decision
- media_decision: keep-static | reuse-video | edit-existing | generate-video
- expression_class: 観察 | 実演 | 状態変化 | 比較 | 構造説明 | 感覚可視化 | 文章転換 | 文字主体 | hybrid
- source_plan: 再利用、抽出、編集、ラフ、追加生成の範囲と理由
- source_gaps: 状態、構図、同一性、形状、追従基準、連続性、品質、様式
- visual_language: 実写、商品動作、図解、文字、補助効果の責務
- motion_graphics: noneまたは必要な伝達機能と最小の表現手段
- ownership: H3内、HTML/CSS、後編集の担当。ただしユーザー指定を優先
- beats: 認識、主動作、変化・比較、読解、結果、必要な静止・ループ
- duration: ビートから求めた尺と根拠
- h3_mode: n/a | T2VA | I2VA | FL2VA | L2VA | Ref2VA
- reference_authority: 各参照が支配する要素と転写禁止要素
- preflight_acceptance: 有料生成前に満たす観察可能な条件
```

5秒を固定しない。単一動作の暫定候補にはできるが、複数ビートを収めるために意味を削らない。

### 4. 専門スキルへ接続して制作する

編集判断はこのスキルで保持し、専門的な生成規約だけを既存スキルへ委ねる。

生成経路は、現在のユーザーによる明示指定、既存カットに保存されたprovider設定、標準H3経路の順で決める。古い実行記録を最新指定より優先しない。

- 媒体選択を記事LP全体で再検討する: `article-lp-decoration`
- 画像生成の保存・候補・review規約: `imagegen-core` と `imagegen`
- 自然な人物・生活写真: `generate-t2i-natural-photo`
- 構図や物理関係の構造ラフ: `generate-storyboard-rough`
- 失敗promptを意味設計から組み直す: `generative-prompt-design`
- H3のモード別構文: `h3-prompt-writing`
- 文字、図形、追従効果、画面転換: `h3-motion-graphics-prompt-writing`
- 標準H3 CLIのdoctor、validate、run、resume: `h3-cli-generation`
- Magnificが明示されたi2v: `magnific-i2v-core`。標準H3経路へ無断で置換しない。
- 単体リール広告が依頼の中心: `h3-reel-ad-prompt-writing`

promptはProduction Decisionの翻訳物として作る。promptの都合で記事内役割や固定条件を変えない。

### 5. 実配置でレビューし、次の一手を決める

生成物単体の技術検査に加え、記事の実サイズと前後文脈で確認する。問題を「なんとなく悪い」で終わらせず、原因層と戻り先を特定する。

```markdown
## Review Diagnosis
- placement_checked:
- observed_facts:
- passed:
- problems: 症状、原因層、重大度、根拠
- hypothesis: 次回に検証する一つの仮説
- change: 次回変更する変数
- preserve: 承認済み・合格済みで維持する要素
- return_to: brief | expression | source | reference | prompt | generation | integration
- next_action: recommend-adoption | local-revise | redesign | add-source | regenerate | reject
- known_approved_deviation:
```

局所不良なら一つの変数を直す。企画、素材、参照設計が壊れている場合は上流へ戻る。要求された要素を削除して問題を隠さない。別案はズーム量の差ではなく、構図、主動作、時間構造、伝達方式の少なくとも一つを構造的に変える。

### 6. 状態と採用を同期する

Labを扱う場合は、概ね次の状態を区別する。

`inventory → brief → source_ready → prompt_ready → validated → generated → reviewed → adopted | rejected`

採用後に新しい修正指示が出たら `revising` とし、診断した戻り先から再開する。ユーザーが明示的に許容した設計との差は、欠陥として消さず `known_approved_deviation` に残す。一覧、詳細、設計契約、review、採否表示を同じ判断へ同期する。

候補数や進捗数のように変化する値を説明文へ固定せず、Labの状態データから表示する。現行候補と採用候補は見つけやすくし、破損・却下候補は主表示から外すか折り畳む。
