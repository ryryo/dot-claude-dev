---
name: character-to-codex-pet
description: 既存キャラクター画像を、承認制でピクセルアートの正準画像へ変換し、3状態パイロット、クロマ前処理、状態間ジオメトリ検証、9状態生成、遷移QA、仮配置、アプリ内確認、ロールバック可能な正式配置まで行う。キャラクターからCodexペットを作る依頼に加え、ジャンプで小さくなる、状態ごとに身長が変わる、足元が跳ねる、クロマ縁が出る、アニメーションを修復したい依頼で使用する。
---

# 既存キャラクターからCodexペットを作る

既存画像をいきなり全状態へ展開しない。承認済みの正準画像と`192x208`の正準セルを固定し、`idle`・`running-right`・`jumping`の3状態パイロットで生成品質を証明してから残りを作る。アプリ内確認が終わるまで中間素材を保持する。

## 依存スキル

- 最初に `${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md` を最後まで読み、通常は組み込み`image_gen`を使う。
- `hatch-pet`のインストール済みパス、または `${CODEX_HOME:-$HOME/.codex}/vendor_imports/skills/skills/.curated/hatch-pet` を探し、対象`SKILL.md`を最後まで読む。
- 生成は`imagegen`、行準備・抽出・合成・基本検証は`hatch-pet`、このスキルのスクリプトは正準セル、クロマ前処理、状態間ジオメトリ、遷移QA、安全配置を担当する。
- `SKILL_ROOT`はこの`SKILL.md`を含むディレクトリの絶対パスとして扱い、同梱スクリプトは`$SKILL_ROOT/scripts/...`で実行する。

## 絶対ルール

- ユーザーが対象を特定して明示的に承認するまで、基準画像を正準化しない。
- 正準画像、正準セル、元画像、状態別レイアウトガイドを各行生成へ添付する。テキストだけで行を生成しない。
- 生成行でカメラのズーム、引き、キャラクター自体の縮小によって動きを表現させない。
- 行ごとのクロマ前処理を必須とし、元の`decoded/`を上書きしない。
- フレーム単位で身長を揃えない。状態行ごとに共通倍率を1つだけ使い、屈みや足開きなどのポーズ差を維持する。
- 通常1.12倍、ジャンプ1.15倍を超える補正が必要なら、その行を再生成する。既存資産の修復だけは`--allow-large-correction`を明示できる。
- 状態単体GIFだけで完成判定しない。`idle→jumping→idle`と`idle→failed→idle`を必ず確認する。
- アプリ内確認前に`prompts/`、`decoded/`、透明化済み行、抽出フレーム、manifestを削除しない。
- 正式ペットを直接上書きしない。候補パッケージを作り、ユーザーのアプリ内承認後にバックアップ付きで昇格する。
- 問題がある場合は最小の行だけを修復する。
- 現行契約は9状態、8列×9行、`1536x1872`だけとする。追加行や別バージョンを推測せず、Codex App側の契約を別途確認できた場合だけ拡張する。

既存ペットを修復する場合は元runを直接変更せず、兄弟repair runを作る。正常行はそのまま保持し、不合格行全体だけを再生成する。詳細は[production-contracts-ja.md](references/production-contracts-ja.md)の修復契約に従う。

## 進捗表示

次のゲートを表示し、常に1つだけを進行中にする。

1. 入力とキャラクター固定条件を確定する。
2. ピクセルアート基準画像を作り、承認を得る。
3. 正準セルと3状態パイロットを検証する。
4. 残り6状態を生成する。
5. 全状態を前処理・正規化・合成・QAする。
6. 候補をアプリで確認する。
7. 正式反映し、必要なら中間素材を整理する。

## 実行手順

### 1. 入力とrunを準備する

参照画像、ペット名、ID、説明、維持する顔・体型・配色・服装・模様・小物、削除可能な背景・文字・影、ピクセル密度を確定する。判断できる項目は推定し、短く報告する。

`hatch-pet`の`prepare_pet_run.py`を`pixel`スタイルで実行する。生成された`pet_request.json`、`imagegen-jobs.json`、プロンプト、レイアウトガイドを正とする。

### 2. 基準画像を承認する

既存画像を編集対象とする`style-transfer`として、[prompts-ja.md](references/prompts-ja.md)の基準画像契約を使う。候補は別ファイルで保存し、`192x208`相当でも顔と輪郭が読めるか確認する。

承認された画像を`references/canonical-base.png`へ固定する。次に次のスクリプトでセル寸法の正準画像を作る。

```bash
python "$SKILL_ROOT/scripts/prepare_canonical_cell.py" \
  --input <run>/references/canonical-base.png \
  --output <run>/references/canonical-cell.png \
  --report-json <run>/qa/canonical-cell.json
```

`canonical-cell.png`を全行の生成入力へ追加する。

### 3. 3状態パイロットを通す

最初に`idle`、`running-right`、`jumping`だけを生成する。各行へ正準画像、正準セル、元画像、状態別レイアウトガイドを添付する。

生成後、[production-contracts-ja.md](references/production-contracts-ja.md)のパイロット工程を実行する。

1. `preprocess_chroma_rows.py`で非破壊の透明化・デスピルを行う。
2. `hatch-pet`で3行だけを`stable-slots`抽出する。
3. `normalize_pet_geometry.py`を通常モードで実行する。
4. 大幅補正、身長、足元、ジャンプ幅のハードゲートを通す。
5. パイロットのコンタクトシートと遷移GIFを目視する。

1件でも不合格なら該当行を再生成する。パイロットが通るまで残りを作らない。

### 4. 残りを生成する

`running-right`が左右反転に安全なら専用スクリプトで`running-left`を派生する。文字、ロゴ、左右固有模様、小物方向、光源の意味が壊れる場合は個別生成する。

続けて`waving`、`jumping`以外の未生成行、`failed`、`waiting`、`running`、`review`を生成する。各行は独立した`imagegen`呼び出しにする。

サブエージェントへ委任する場合、許可が曖昧なら開始前に確認する。同時生成は最大2行、各担当は1行だけを扱い、親がmanifest、正準画像、合成、修復を管理する。

### 5. 全状態を最終化する

全行へクロマ前処理を行い、`stable-slots`で抽出する。抽出した損失なしPNGフレームを入力として`normalize_pet_geometry.py`を実行する。完成WebPを再入力に使わない。

正規化後フレームからアトラス、検証JSON、コンタクトシート、状態別GIFを作る。さらに`render_transition_previews.py`で状態遷移GIFを作る。[qa-ja.md](references/qa-ja.md)を全項目確認し、HighまたはMediumがあれば該当行だけ修復する。

### 6. 仮配置してアプリ確認する

`package_pet_safely.py stage`でrun内に候補パッケージを作る。この段階では`${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>`を変更しない。

`package_pet_safely.py preview`で`<pet-id>-candidate`として一時配置し、次を実機確認する。正式IDは変更しない。

- idleからjumpingへ切り替わってもキャラクター自体が縮小しない。
- ジャンプ幅が大きすぎない。
- failedで屈んだときはポーズ分だけ自然に小さくなる。
- 左右移動の向き、歩容、身長、足元が自然である。
- クロマ縁、クリップ、状態切り替え時のサイズポップがない。

確認結果を`acceptance.json`とrun summaryへ記録する。未確認の成果物は「暫定完成」と報告し、完成扱いにしない。

### 7. 正式反映とロールバック

ユーザーがアプリ内で承認した後だけ、次を実行する。

```bash
python "$SKILL_ROOT/scripts/package_pet_safely.py" promote \
  --candidate-dir <run>/candidate-package \
  --confirm-in-app-accepted
```

既存ペットは`${CODEX_HOME:-$HOME/.codex}/pets/.backups/`へ退避される。問題があれば`rollback`を実行する。

正式承認後に限り中間素材を整理する。正準画像、正準セル、最終WebP、検証、ジオメトリレポート、コンタクトシート、状態別GIF、遷移GIF、run summary、候補受付記録は残す。

## 完了条件

- [production-contracts-ja.md](references/production-contracts-ja.md)の全ハードゲートを通過している。
- 正準画像と正準セルが保存されている。
- 3状態パイロット合格後に残りを生成している。
- 全9状態で同一性、ピクセル密度、状態意味、身長、足元、透明境界が合格している。
- 状態単体GIFと状態遷移GIFを確認している。
- アプリ内承認が記録されている。
- 正式配置先とバックアップ先を報告している。
