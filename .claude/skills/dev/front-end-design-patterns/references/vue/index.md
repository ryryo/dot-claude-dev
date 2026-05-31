# Vue References

この index はエージェントが Vue の参照候補を探索するための目次。個別ファイルをユーザーに選ばせるための一覧ではない。
実装判断では、必要な reference の `Original Skill Metadata` と `original-skill-body` を読む。

| Category | Original skill | 主な使用場面 | File |
|---|---|---|---|
| Design | `components` | Vue SFC の markup / logic / style を component として整理したいとき | [components.md](components.md) |
| Design | `composables` | Composition API で shared reactive state、side effect、computed logic を抽出したいとき | [composables.md](composables.md) |
| Design | `container-presentational` | Vue component の view と data / business logic を分離したいとき | [container-presentational.md](container-presentational.md) |
| Design | `data-provider` | renderless component で data loading / providing を扱いたいとき | [data-provider.md](data-provider.md) |
| Design | `dynamic-components` | runtime 条件に応じて component を切り替えたいとき | [dynamic-components.md](dynamic-components.md) |
| Design | `provide-inject` | deeply nested component へ props drilling なしで data を渡したいとき | [provide-inject.md](provide-inject.md) |
| Design | `render-functions` | template ではなく JavaScript で render output を組み立てたいとき | [render-functions.md](render-functions.md) |
| Design | `renderless-components` | markup を持たず behavior / state だけを再利用したいとき | [renderless-components.md](renderless-components.md) |
| Design | `script-setup` | Vue 3 の Composition API を compile-time syntax で簡潔に書きたいとき | [script-setup.md](script-setup.md) |
| Design | `state-management` | component 間で application-level state を扱う必要があるとき | [state-management.md](state-management.md) |
| Performance | `async-components` | Vue component を非同期 load して initial bundle を下げたいとき | [async-components.md](async-components.md) |
