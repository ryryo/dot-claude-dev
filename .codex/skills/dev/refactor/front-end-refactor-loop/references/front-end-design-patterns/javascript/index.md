# JavaScript References

この index はエージェントが参照候補を探索するための目次。個別ファイルをユーザーに選ばせるための一覧ではない。
実装判断では、必要な reference の `Original Skill Metadata` と `original-skill-body` を読む。

| Category | Original skill | 主な使用場面 | File |
|---|---|---|---|
| Design | `command-pattern` | undo / redo、queued operation、invoker と executor の分離が必要なとき | [command-pattern.md](command-pattern.md) |
| Design | `factory-pattern` | object creation logic を一箇所へ集めたいとき | [factory-pattern.md](factory-pattern.md) |
| Design | `flyweight-pattern` | 大量の類似 object による memory cost を抑えたいとき | [flyweight-pattern.md](flyweight-pattern.md) |
| Design | `mediator-pattern` | 複数 component / module 間の直接依存を減らしたいとき | [mediator-pattern.md](mediator-pattern.md) |
| Design | `mixin-pattern` | inheritance なしで複数 object / class に behavior を追加したいとき | [mixin-pattern.md](mixin-pattern.md) |
| Design | `module-pattern` | JavaScript code を public / private boundary で整理したいとき | [module-pattern.md](module-pattern.md) |
| Design | `observer-pattern` | publish / subscribe や event-driven communication が必要なとき | [observer-pattern.md](observer-pattern.md) |
| Design | `prototype-pattern` | 多数の同種 object で method / property を共有したいとき | [prototype-pattern.md](prototype-pattern.md) |
| Design | `provider-pattern` | 深い component tree に共通 data を渡したいとき | [provider-pattern.md](provider-pattern.md) |
| Design | `proxy-pattern` | property access、validation、logging、access control を挟みたいとき | [proxy-pattern.md](proxy-pattern.md) |
| Design | `singleton-pattern` | 単一 instance で共有状態や coordinator を扱う必要があるとき | [singleton-pattern.md](singleton-pattern.md) |
| Performance | `bundle-splitting` | 大きな JavaScript bundle が initial load を悪化させているとき | [bundle-splitting.md](bundle-splitting.md) |
| Performance | `compression` | network transfer cost を gzip / brotli などで下げたいとき | [compression.md](compression.md) |
| Performance | `dynamic-import` | startup に不要な module を on-demand に分割したいとき | [dynamic-import.md](dynamic-import.md) |
| Performance | `import-on-interaction` | modal、picker、heavy widget などを interaction 後に読みたいとき | [import-on-interaction.md](import-on-interaction.md) |
| Performance | `import-on-visibility` | below-the-fold component を viewport 到達まで遅延したいとき | [import-on-visibility.md](import-on-visibility.md) |
| Performance | `js-performance-patterns` | hot path、loop、DOM operation、cache、data structure を最適化したいとき | [js-performance-patterns.md](js-performance-patterns.md) |
| Performance | `loading-sequence` | FCP / LCP / FID に関わる resource discovery と loading order を改善したいとき | [loading-sequence.md](loading-sequence.md) |
| Performance | `prefetch` | 次に必要になる可能性が高い resource を idle time に読みたいとき | [prefetch.md](prefetch.md) |
| Performance | `preload` | critical font、hero image、script などの発見が遅いとき | [preload.md](preload.md) |
| Performance | `prpl` | PWA や route-centric app の initial load と subsequent navigation を改善したいとき | [prpl.md](prpl.md) |
| Performance | `route-based` | route ごとに distinct feature set を分割したいとき | [route-based.md](route-based.md) |
| Performance | `static-import` | startup に必須な module を static analysis / tree shaking 可能に読みたいとき | [static-import.md](static-import.md) |
| Performance | `third-party` | analytics、ads、widget など third-party script が Core Web Vitals を悪化させているとき | [third-party.md](third-party.md) |
| Performance | `tree-shaking` | unused exports や barrel import による bundle bloat を減らしたいとき | [tree-shaking.md](tree-shaking.md) |
| Performance | `virtual-lists` | 数百〜数千件の list / table rendering が重いとき | [virtual-lists.md](virtual-lists.md) |
| Performance | `vite-bundle-optimization` | Vite build、dependency optimization、manual chunks、compression を調整したいとき | [vite-bundle-optimization.md](vite-bundle-optimization.md) |
| Rendering | `islands-architecture` | content-heavy page で一部だけ interactivity / hydration が必要なとき | [islands-architecture.md](islands-architecture.md) |
| Rendering | `view-transitions` | page transition や UI state change を View Transitions API で滑らかにしたいとき | [view-transitions.md](view-transitions.md) |
