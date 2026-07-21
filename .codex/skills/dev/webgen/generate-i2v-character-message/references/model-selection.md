# モデル選択ガイド

## 目次

- 既定選択
- Seedance系の扱い
- Kling系の扱い
- 失敗時の切り替え

## 既定選択

ユーザーがモデルを指定しない場合は、`../kamui-i2v-core/references/models.json`で`enabled: true`のモデルを価格順に並べ、最低解像度の推定単価が最も安い1件を選ぶ。2026-07-20時点のカタログではSeedance 2.0 Miniが該当する。

複数モデルでの比較や高価なモデルの実行は、ユーザーが明示した場合だけ行う。

## Seedance系の扱い

Seedance 2.0 Fast / Mini / Standardは、4:3や480pを指定でき、固定カメラの条件を合わせやすい。ただし実写人物風の入力では、結果取得時に次のような拒否が出る場合がある。

```text
content_policy_violation
The images or videos provided may contain likenesses of real people or other private information that cannot be processed.
partner_validation_failed
```

この拒否が出た場合、同じ画像でSeedance系を再送しない。入力画像をメタデータ除去済みJPEGにしても同じ拒否が出ることがある。

## Kling系の扱い

Kling O3 StandardとKling V3 Standardは、Seedance以外の安価候補として扱う。実測では人物写真風入力で通った。

- Kling O3 Standard: 4:3入力に近い比率で出やすい。動きは比較的控えめ。
- Kling V3 Standard: 4:3直接指定は非対応だが入力画像準拠で4:3近辺の出力が得られた。表情やまばたきがやや大きめに出る場合がある。

## 失敗時の切り替え

1. `prepare_source.py`でメタデータ除去済みJPEGを作る。
2. Seedance系で肖像検証拒否が出たら、Kling O3 Standardを試す。
3. もう1本比較するならKling V3 Standardを試す。
4. それでも人物や手が崩れる場合は、入力静止画のポーズを単純化して再生成する。
