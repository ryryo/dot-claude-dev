# レポート雛形

main Codex が loop ごと、最終完了時に使う報告雛形。

## ループレポート

```markdown
## ループ別リファクタリングレポート

### 概要
- 対象: <対象範囲>
- ループ: <番号>
- 調査結果: <findings summary>
- コミット: <hash/message または未作成理由>
- 挙動変更: 意図していない

### 変更内容
| 領域 | 変更内容 | 参照した pattern 観点 | 性能・保守性への効果 |
|---|---|---|---|
| <file/feature> | <責務単位の変更> | <観点> | <実測済み or expected。未測定なら expected と明記> |

### 性能計測ゲート
- 判定: <実施 / 省略>
- 理由: <performance-sensitive 判定 or 省略理由>
- 手順: <操作、fixture、stub、browser/build/profiler>
- 結果: <before/after table or 未実施理由>
- 一時計測コード: <削除済み / なし>

### 検証
- Typecheck: <command/result>
- Lint: <command/result>
- Tests: <command/result>
- Browser/build/profile: <実施結果 or 未実施理由>

### 挙動維持
- 維持したもの: <UI/API/payload/data format/event behavior など>
- 変更していないもの: <意図的に触らなかった範囲>

### 残リスク
- <未実測・未検証・将来 profile 推奨など>
```

## 最終レポート

```markdown
## 最終フロントエンドリファクタリングレポート

### 全体概要
- 対象: <対象範囲>
- 結果: <N> 回の新規監査ループ後に NO_FINDINGS
- 挙動変更: 意図していない
- 検証: <typecheck/lint/test/build/browser summary>
- 性能計測: <実施したゲート数 / 省略した理由 summary>

### 改善テーマ
| テーマ | 変更領域 | pattern 観点 | 効果 |
|---|---|---|---|
| <例: render hot path isolation> | <対象> | <観点> | <実測済み or expected。未実測なら expected と明記> |

### 実測済み性能結果
| 対象 | 手順 | before | after | 判断 |
|---|---|---:|---:|---|
| <render/bundle/canvas/etc> | <measurement procedure> | <値> | <値> | <解釈> |

### 未実測だが期待される改善
| 対象 | 期待される効果 | 未実測理由 |
|---|---|---|
| <target> | <expected effect> | <why not measured> |

### 変更領域
| 領域 | 主な変更 | なぜ安全・高速・保守しやすいか |
|---|---|---|
| <route/component/hook> | <大きな変更点> | <効果と挙動維持理由> |

### ループ履歴
| ループ | 調査結果 | 性能計測ゲート | コミット | 検証 |
|---|---|---|---|---|
| 1 | <findings summary> | <実施/省略> | <hash/message> | <passed commands> |

### パターン適用範囲
- Container / presentational boundary: <適用箇所 or 該当なし>
- Pure selectors / hooks: <適用箇所 or 該当なし>
- Render hot path isolation: <適用箇所 or 該当なし>
- Stable dependencies: <適用箇所 or 該当なし>
- Derived state / recomputation cleanup: <適用箇所 or 該当なし>
- Module boundary / lazy loading: <適用箇所 or 該当なし>

### 検証詳細
- <commands and results>

### 挙動維持
- 維持した UI/API/payload/data format/event behavior: <summary>
- 意図的に変更しなかった範囲: <summary>

### 残リスク / 追加計測候補
- <未実測の性能効果、ブラウザ未確認、Profiler 推奨など>
```
