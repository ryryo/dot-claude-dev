# Web漫画画像用・改変プロンプト

このファイルは、`github-devlog-manga` の `build-manga-prompt.ts` に埋め込まれていた漫画作成プロンプトの構造と制約を維持し、LP・Webサイト掲載画像に必要な箇所だけを変更したものとする。画像生成時は全文を読み、該当案件の入力変数、原稿、掲載箇所、キャスト、参照画像を埋めて使う。短く要約した別プロンプトへ置き換えない。

主な変更は次の点だけとする。

1. 入力をGit diffからLP・Webサイトの原稿、画像計画、掲載箇所へ変更する。
2. ナノン固定ではなく、案件の既存キャスト、人物リファレンス、キャラクターシートを使う。
3. Discord投稿やKAMUI API前提を外し、`$imagegen`で実生成して目視確認する。
4. コマ数はAI自律決定を基本にしつつ、ユーザー指定やLP掲載枠がある場合は`panel_count`を優先する。
5. 既定の画像比率はLP差し込み用の`4:3`とし、指定があればそれに従う。
6. 配色固定はせず、対象ページや参照画像になじませる。

## 入力変数

```text
【入力変数: 画像の目的】
掲載セクションでこの漫画が担う役割。例: 読者共感、違和感の発見、サービス理解、Before/After。

【入力変数: 原稿・背景情報】
LP原稿、画像計画、読者の悩み、人物関係、サービス上の重要な事実。

【入力変数: 登場キャスト】
既存キャスト、人物リファレンス、キャラクターシート、各キャストの役割。

【入力変数: text_mode】
include または none。未指定は include。

【入力変数: aspect_ratio】
明示指定、実際の掲載枠、4:3の順で決める。未指定かつ掲載枠不明は4:3。

【入力変数: panel_count】
ユーザー指定があればそれを使う。未指定は漫画AIがストーリー内容に基づいて最適なコマ数を決める。ただしLP差し込みでは1〜4コマを標準とする。
```

ここから下は画像生成AIと制作エージェントへの指示であり、画像内には表示しない。この指示文、見出し、例文、ルール説明を画像内テキストとして使わない。

## 背景情報の作成

元のGitHub開発ログ漫画では、diffから漫画AIに渡す「網羅的な変更サマリー」を作成していた。LP・Web用途でも同じ考え方を使い、画像生成前に必要なら次を整理する。

- 原稿や画像計画の内容を読み、漫画が扱う題材を特定する。
- 題材は、媒体や作業ファイルではなく、読者が体験する問題、違和感、変化、理解の対象にする。
- この段階では完成したストーリーや物語を作り込みすぎない。
- 端的な要約だけで済ませず、漫画のセリフや場面に変換しやすい背景情報を書く。
- 読者の悩み、人物の役割、状況、処理の流れ、サービス上の判断、誤解されやすい点を省略しない。
- 価格、統計、契約条件、保証、出典などの正確性が重要な情報は、漫画内に描くかではなく、HTMLへ残す情報として分離する。
- 数値や条件を漫画内へ入れる場合は、ユーザーまたは原稿で確定済みの短い表現だけにする。

## キャスト選択

元のGitHub開発ログ漫画では、題材に応じてナノン系列からキャラクターを選んでいた。LP・Web用途では、次の順で選ぶ。

1. 画像計画やキャスト表で指定された人物を使う。
2. 人物リファレンスやキャラクターシートがある人物を優先する。
3. 既存キャストで代替できる場合は、新しい人物を増やさない。
4. どうしても新しい人物が必要な場合だけ、役割、登場理由、外見の固定点を明確にする。

キャスト数の目安:

- 1人: 主人公の悩み、違和感、気づきをシンプルに見せる。
- 2人: 対話、質問、説明役と聞き手、顧客と担当者を見せる。
- 3人: 会議、チーム、複数視点が必要な場合だけ使う。

AI、システム、記事、検索、サービスは人物化せず、画面、書類、アイコン、小道具として表す。

## 画像生成プロンプト本体

次の構造を維持して、案件固有の内容を埋める。

```text
[Output Format]
- Generate ONE single image containing manga panels
- Panel count should be determined by AI based on story content, unless panel_count is explicitly specified
- The image must work as an LP or website visual, not as a long standalone comic

[Visual Style]
- Style: High quality Japanese Manga
- Speech bubbles: Japanese vertical text, top-to-bottom, when text_mode is include
- Color: Full color unless the user explicitly asks for monochrome
- Tone: clean, readable business manga suited for LP and website use
- Avoid overly comedic, overly dramatic, poster-like, photorealistic, or isometric-diagram styles unless explicitly requested

[Layout Requirements]
- Panel Count: Use panel_count if specified. If unspecified, choose the optimal panel count based on story content
- Panel Arrangement: Choose optimal layout that best conveys the narrative
- Panel Layout: Use the best practice of Japanese manga panel layout, including the "逆Z字型" reverse Z-pattern when it fits, creating a layout where the eye can read naturally
- Panel Flow: Logical progression using Japanese manga reading order, right-to-left and top-to-bottom where appropriate
- Panel Borders: Clear and distinct borders between each panel
- Panel Layout Techniques: Actively use panel techniques including 変形コマ, 断ち切りコマ, and 枠線の無いコマ only when they improve the story and do not hurt LP readability
- LP Readability: Important faces, expressions, speech bubbles, and story beats must remain readable on desktop and mobile

[Image Context]
- Image 1: Character Image 1 (キャスト名 or 参照画像名)
- Image 2: Character Image 2 (キャスト名 or 参照画像名)
- Add only the reference images actually needed for the manga

[Story Context]
Please create an explanatory comic based on the following LP or website content.

# Mandatory Requirements
- Dialogue must be in Japanese vertical writing when text_mode is include.
- Each line of dialogue in speech bubbles must be compact within 2 lines.
- Background information is purely context and cannot be directly pasted as dialogue.
- Abstract the content and translate it into natural dialogue or visible actions.
- If text_mode is none, draw no dialogue, captions, signs, UI text, or small decorative text.
- Keep the same character identity across all panels.
- Do not invent achievements, testimonials, awards, guarantees, or customer records.

# Roles of Each Character
- [Character 1]'s Role: （キャストの役割）
- [Character 2]'s Role: （キャストの役割）

# Article Content
（LP原稿、画像計画、背景情報、避ける誤解、掲載箇所）
```

## 文字の扱い

`text_mode: include`では、セリフと短い地の文を使ってよい。ただし、背景情報をそのままセリフへ貼り付けない。漫画として自然な会話、短い反応、短い気づきへ抽象化する。

`text_mode: none`では、吹き出し、看板、画面内文章、端の小文字を含め、画像内へ文字を描かない。人物の表情、視線、手元、小道具、コマ順だけでストーリーが読めるようにする。

## 最終確認

- 元のプロンプト構造である `[Output Format]`、`[Visual Style]`、`[Layout Requirements]`、`[Image Context]`、`[Story Context]`、`Mandatory Requirements`、`Roles of Each Character`、`Article Content` を維持しているか。
- 1枚の漫画画像になっているか。
- コマ数がストーリー内容または指定された`panel_count`に合っているか。
- 逆Z字型、右から左、上から下の流れが破綻していないか。
- コマ枠、変形コマ、断ち切りコマ、枠線なしコマが読みやすさを壊していないか。
- 日本語縦書きのセリフが崩れていないか。
- 背景情報の長文をそのままセリフにしていないか。
- キャストの同一性が全コマで保たれているか。
- LP本文や案件固有の制約と矛盾していないか。
