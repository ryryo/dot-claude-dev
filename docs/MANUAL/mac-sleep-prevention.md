# Mac スリープ防止（蓋閉じ対応）

AI 作業中に MacBook の蓋を閉じてもスリープさせないためのツール。`caffon` / `caffoff` の 2 本のコマンドで構成される。

---

## なぜ `caffeinate` ではなく `pmset` か

Apple Silicon Mac の **clamshell sleep（蓋閉じスリープ）** は、以下いずれかの条件が揃わない限り `caffeinate` コマンドでは防げない:

- 外部ディスプレイ接続
- 電源（AC アダプタ）接続
- 外部キーボード/マウス接続

本ツールはいずれも無い前提（バッテリー駆動・裸の MacBook）で動作させるため、唯一確実な手段である `sudo pmset -a disablesleep 1` を採用している。

---

## ⚠️  警告：熱・バッテリー・ハードウェア

蓋を閉じた状態での高負荷作業（AI エージェント・ビルド・動画エンコード等）は **物理的に** 以下を引き起こす:

- **熱ごもり**：MacBook はキーボード面が主な放熱経路。閉じると放熱できずサーマルスロットリング発生
- **バッテリー劇消耗**：充電なしで数時間の高負荷 → バッテリー 0 到達が非常に早い
- **バッテリー劣化加速**：高温での深い放電はバッテリー寿命を縮める

**推奨される使い方**:

- 短時間（1〜2h）のスポット利用に限定する
- 可能な限り AC 電源を繋ぐ
- 重い作業は蓋を開けた状態で行い、移動時だけ本ツールを使う

セーフガードとして **2 時間** または **バッテリー 20%** で自動解除するが、それまでの熱負荷は防げない点を理解して使用すること。

---

## インストール

```bash
cd ~/dev/dot-claude-dev/scripts/mac-sleep-prevention
./install.sh
```

これで `~/.local/bin/caffon` と `~/.local/bin/caffoff` にシンボリックリンクが張られる（PATH に `~/.local/bin` が含まれている前提）。

### 残骸検出警告を有効化（推奨）

`.zshrc` の末尾に以下を追加:

```bash
source ~/dev/dot-claude-dev/scripts/mac-sleep-prevention/zshrc-snippet.sh
```

シェル起動時に `pmset disablesleep=1` が残ったまま caffon が動いていない場合、警告が表示される。

---

## 使い方

### スリープ防止を有効化

```bash
caffon
```

- sudo パスワードの入力を求められる（`sudo pmset -a disablesleep 1` のため）
- そのまま端末に常駐する。経過時間・残時間・バッテリー % をリアルタイム表示
- この状態で蓋を閉じても Mac はスリープしない
- **端末を閉じない** こと（閉じると caffon が死に、disablesleep=1 が残留する）

### 解除方法

3 通り:

1. **Ctrl+C**（caffon が動いている端末で）
2. **別端末から `caffoff`**（caffon に SIGTERM を送る）
3. **自動**（タイムアウト 2h / バッテリー 20% 以下）

いずれの場合も `sudo pmset -a disablesleep 0` が実行され macOS 通知が飛ぶ。

---

## セーフガード仕様

| トリガー         | 閾値    | 挙動                                        |
| ---------------- | ------- | ------------------------------------------- |
| タイムアウト     | 2 時間  | 自動解除して caffon 終了                    |
| バッテリー低下   | ≤ 20%   | 自動解除して caffon 終了                    |
| Ctrl+C / SIGTERM | 即時    | trap で `pmset disablesleep 0` を必ず実行   |

閾値を変更したい場合は [caffon.sh](../../scripts/mac-sleep-prevention/caffon.sh) 先頭の `TIMEOUT_SEC` / `BATTERY_THRESHOLD` を編集する。

---

## 動作確認手順

実際に蓋を閉じてスリープしないことを確認する最も簡単な方法：

**端末 1：caffon を起動**
```bash
caffon
```

**端末 2：タイムスタンプ付きの無限カウントを起動**
```bash
while true; do echo "$(date)"; sleep 5; done
```

その後、**電源を抜いて蓋を閉じ** 数分放置する。蓋を開けたとき端末 2 のログが継続して出力されていれば、蓋閉じ中もスリープせずに動作していたことが確認できる。

- カウントスクリプトは CPU 負荷がほぼゼロなので熱問題なく長時間テスト可能
- ログが途切れている場合（スリープが発生した場合）はタイムスタンプのギャップで判定できる

確認後は Ctrl+C で caffon を停止すること。

---

## トラブルシューティング

### disablesleep=1 が残留した（端末を閉じてしまった等）

手動復旧:

```bash
sudo pmset -a disablesleep 0
rm -f /tmp/caffon.pid
```

確認:

```bash
pmset -g | grep ' sleep'
# → sleep 1 (バッテリー駆動時) もしくは sleep 0 (AC 電源時) なら正常
```

### `caffon` 起動時に「既に実行中」と言われる

```bash
# 本当に動いているかを確認
ps -p "$(cat /tmp/caffon.pid)"

# 動いていなければ pid ファイルを削除
rm /tmp/caffon.pid
```

### sudo パスワードを何度も聞かれる

caffon はループ内で `sudo -v` を呼び timestamp を延長している。デフォルトで 5 分の timestamp。あまりに頻繁に聞かれる場合は `/etc/sudoers` の `timestamp_timeout` を確認。

---

## 関連ファイル

- [caffon.sh](../../scripts/mac-sleep-prevention/caffon.sh) — スリープ防止の本体
- [caffoff.sh](../../scripts/mac-sleep-prevention/caffoff.sh) — 停止コマンド
- [install.sh](../../scripts/mac-sleep-prevention/install.sh) — シンボリックリンク配置
- [zshrc-snippet.sh](../../scripts/mac-sleep-prevention/zshrc-snippet.sh) — 残骸検出
