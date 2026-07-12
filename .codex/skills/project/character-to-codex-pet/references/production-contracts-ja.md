# 制作ゲートと成果物契約

## Gate 1: 正準承認

- `canonical-base.png`: ユーザーが承認した高解像度の正準画像
- `canonical-cell.png`: `192x208`、足元203px前後、スプライト高約190pxの生成用サイズ基準
- どちらも上書きせず、承認元と日時をmanifestに残す

## Gate 2: 3状態パイロット

対象は`idle`、`running-right`、`jumping`。

1. 各行を正準画像、正準セル、元画像、配置ガイド付きで生成する。
2. `preprocess_chroma_rows.py`で`decoded-clean/`へ透明化する。
3. `stable-slots`でパイロットフレームを抽出する。
4. `normalize_pet_geometry.py --states idle,running-right,jumping`を通常モードで実行する。
5. 補正倍率が上限を超えた行は再生成する。
6. `idle→jumping→idle`遷移を確認する。

パイロット合格前に残り6状態を生成しない。

## Gate 3: 全状態ジオメトリ

損失なしの抽出PNGを入力とし、次を満たす。

- 通常身長比: `idle`の0.95〜1.05
- 通常補正倍率: 0.90〜1.12
- ジャンプ補正倍率: 1.15以下
- ジャンプ最大身長比: 0.92以上
- ジャンプ最小横幅比: 0.88以上
- ジャンプ上下幅: 8〜16px、標準10px
- 静止系足元幅: 4px以下
- 左右移動足元幅: 12px以下

新規制作で上限を超えたら再生成する。`--allow-large-correction`は既存資産修復に限定する。

## 既存ペットの修復契約

- 元runと正式配置済みペットを直接編集しない。`<run>-repair-<番号>`の兄弟runを作る。
- 正常な行はバイト列または損失なしセルとして保持し、不合格行全体だけを再生成する。
- `canonical-cell.png`、生成プロンプト、decoded行、抽出PNGが欠けている場合は、修復runへ再構築してから作業する。
- 完成WebPは正常行の保存元としてだけ使える。新しいジオメトリ正規化の入力には、再構築した損失なしPNGフレームを使う。
- `--allow-large-correction`を使った既存成果物も、遷移GIFまたはアプリで縮小が残れば再生成する。
- 修復候補もpreview IDで確認し、正式IDの差し替えはアプリ内承認後だけ行う。

## Gate 4: 透明境界

全生成行を非破壊前処理する。

```bash
python "$SKILL_ROOT/scripts/preprocess_chroma_rows.py" \
  --input-dir <run>/decoded \
  --output-dir <run>/decoded-clean \
  --report-json <run>/qa/chroma-preprocess.json \
  --states all
```

`decoded/`を残し、透明な四隅、RGBA、元寸法維持、デスピル、1pxエッジ収縮を検証する。

## Gate 5: 状態遷移

```bash
python "$SKILL_ROOT/scripts/render_transition_previews.py" \
  --frames-root <run>/frames-normalized \
  --output-dir <run>/qa/transitions \
  --report-json <run>/qa/transitions.json
```

必須遷移:

- `idle→jumping→idle`
- `idle→failed→idle`

実寸と3倍拡大の両方を確認する。

## Gate 6: 仮配置と正式反映

候補作成:

```bash
python "$SKILL_ROOT/scripts/package_pet_safely.py" stage \
  --spritesheet <run>/final/spritesheet.webp \
  --candidate-dir <run>/candidate-package \
  --pet-id <id> \
  --display-name <name> \
  --description <description> \
  --run-summary <run>/qa/run-summary.json
```

候補の一時配置:

```bash
python "$SKILL_ROOT/scripts/package_pet_safely.py" preview \
  --candidate-dir <run>/candidate-package \
  --run-summary <run>/qa/run-summary.json
```

候補は`<pet-id>-candidate`として表示され、正式IDを上書きしない。

アプリ確認後の正式反映:

```bash
python "$SKILL_ROOT/scripts/package_pet_safely.py" promote \
  --candidate-dir <run>/candidate-package \
  --run-summary <run>/qa/run-summary.json \
  --confirm-in-app-accepted
```

ロールバック:

```bash
python "$SKILL_ROOT/scripts/package_pet_safely.py" rollback \
  --pet-id <id> \
  --run-summary <run>/qa/run-summary.json
```

## 保持契約

アプリ内承認まで保持する:

- `pet_request.json`、`imagegen-jobs.json`、`prompts/`
- `references/canonical-base.png`、`canonical-cell.png`、元画像、配置ガイド
- `decoded/`、`decoded-clean/`、抽出フレーム、正規化フレーム
- 全QA成果物、候補パッケージ

正式承認後も保持する:

- 正準画像と正準セル
- 最終WebP、validation、geometry report、chroma report
- contact sheet、状態別GIF、遷移GIF
- run summary、acceptance記録、正式配置先とバックアップ先
