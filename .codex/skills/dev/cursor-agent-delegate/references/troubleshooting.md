# Cursor CLI の例外処理

この文書は通常フローでは読まない。submit または monitor の結果から、worker task ではなく Cursor CLI 自体の疎通問題だと判断した場合だけ使う。

## 最初の対応

- 追加の Cursor CLI worker 投入を止める。
- 失敗した task の `stderr_tail`、exit code、result JSON を確認する。
- prompt、test、実装上の失敗と CLI 疎通失敗を区別する。

preflight に進む条件:

- `cursor` command が見つからない、または `cursor agent` が起動できない。
- login、status、model list、`composer-2.5-fast` に関する CLI-level error が出る。
- JSON result が生成されず、prompt 内容ではなく CLI 起動の問題と判断できる。
- 複数 task が同種の CLI-level error で失敗する。

## 疎通を確認する

条件を満たした場合だけ実行する。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"

"$SKILL_DIR/scripts/run_cursor_delegate.sh" \
  --workspace "$WORKSPACE" \
  --preflight
```

preflight は `cursor agent --version`、login status、model list、read-only smoke JSON を確認する。通常の worker task、task graph、投入前 checklist には含めない。

## 判断する

- preflight が成功した場合: 元の stderr と prompt を見直し、必要なら失敗 task だけ再投入する。
- preflight が失敗した場合: Cursor CLI の復旧を無制限に繰り返さず、main Codex が直接引き取るか Codex subagent へ切り替える。
- model が見つからない場合: model を自動変更しない。`composer-2.5-fast` を使えない事実をユーザーへ報告する。
- login が必要な場合: main Codex が認証情報を扱わず、ユーザー操作が必要な blocker として報告する。

## worker task の失敗

CLI 疎通が正常なら preflight を使わない。次を確認して main Codex が修正、再委任、棄却を判断する。

- prompt の goal と write scope が矛盾していないか。
- worker が forbidden path を必要として停止していないか。
- verification failure が既存不具合か worker の変更によるものか。
- timeout 後も process が生きているか。
- final report と実際の diff が一致しているか。

再投入する場合も、同じ task を理由なく繰り返さない。原因を修正してから 1 task 単位で再投入する。
