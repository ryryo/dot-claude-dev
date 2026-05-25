# Decision Matrix

ユーザーに個別パターンを選ばせず、コードベースと症状から読む reference を絞るための表。
ここは入口であり、実装判断の根拠は個別 reference の `original-skill-body` に置く。

## Component Architecture / Refactoring

| 症状・依頼 | 優先して読む reference |
|---|---|
| shared stateful logic、form handling、subscription、side effect が複数 component に重複している | [react/hooks-pattern.md](react/hooks-pattern.md), [react/react-composition-2026.md](react/react-composition-2026.md) |
| prop drilling、関連 component 間の暗黙 state、tabs / accordion / dropdown の API 設計 | [react/compound-pattern.md](react/compound-pattern.md), [javascript/provider-pattern.md](javascript/provider-pattern.md) |
| view と data fetching / business logic が混ざっている | [react/presentational-container-pattern.md](react/presentational-container-pattern.md), [react/react-data-fetching.md](react/react-data-fetching.md) |
| render logic を caller 側で柔軟に差し替えたい | [react/render-props-pattern.md](react/render-props-pattern.md), [react/react-composition-2026.md](react/react-composition-2026.md) |
| auth、logging、feature flag など cross-cutting concern を共有したい | [react/hoc-pattern.md](react/hoc-pattern.md), [javascript/mediator-pattern.md](javascript/mediator-pattern.md) |
| object creation、command queue、undo / redo、event mediator など framework-agnostic な設計課題がある | [javascript/factory-pattern.md](javascript/factory-pattern.md), [javascript/command-pattern.md](javascript/command-pattern.md), [javascript/observer-pattern.md](javascript/observer-pattern.md), [javascript/mediator-pattern.md](javascript/mediator-pattern.md) |

## React Runtime Performance

| 症状・依頼 | 優先して読む reference |
|---|---|
| 入力が重い、不要再レンダリングが多い、state 設計や memoization を見直したい | [react/react-render-optimization.md](react/react-render-optimization.md) |
| 数百〜数千件の list / table で scroll jank や slow initial render がある | [javascript/virtual-lists.md](javascript/virtual-lists.md), [react/react-render-optimization.md](react/react-render-optimization.md) |
| hot path、loop、DOM operation、cache、data structure が重い | [javascript/js-performance-patterns.md](javascript/js-performance-patterns.md) |
| component state / derived state / context update の切り分けが必要 | [react/react-render-optimization.md](react/react-render-optimization.md), [react/hooks-pattern.md](react/hooks-pattern.md) |

## Data Fetching / Cache

| 症状・依頼 | 優先して読む reference |
|---|---|
| React で cache、deduplication、optimistic update、parallel loading を扱う | [react/react-data-fetching.md](react/react-data-fetching.md) |
| data fetching と presentation が混ざり testability が低い | [react/react-data-fetching.md](react/react-data-fetching.md), [react/presentational-container-pattern.md](react/presentational-container-pattern.md) |
| modern React stack 全体で routing / state / data fetching 方針を選びたい | [react/react-2026.md](react/react-2026.md), [react/react-data-fetching.md](react/react-data-fetching.md) |

## Bundle / Loading / Third-party

| 症状・依頼 | 優先して読む reference |
|---|---|
| 初期 JS が大きい、startup に不要な feature が initial bundle に入っている | [javascript/dynamic-import.md](javascript/dynamic-import.md), [javascript/bundle-splitting.md](javascript/bundle-splitting.md), [javascript/vite-bundle-optimization.md](javascript/vite-bundle-optimization.md) |
| modal、picker、editor、chart などを interaction 後に読みたい | [javascript/import-on-interaction.md](javascript/import-on-interaction.md), [javascript/dynamic-import.md](javascript/dynamic-import.md) |
| below-the-fold component や画像を viewport 到達まで遅延したい | [javascript/import-on-visibility.md](javascript/import-on-visibility.md), [javascript/loading-sequence.md](javascript/loading-sequence.md) |
| route ごとに code splitting したい | [javascript/route-based.md](javascript/route-based.md), [javascript/dynamic-import.md](javascript/dynamic-import.md) |
| preload / prefetch の使い分けが必要 | [javascript/preload.md](javascript/preload.md), [javascript/prefetch.md](javascript/prefetch.md), [javascript/loading-sequence.md](javascript/loading-sequence.md) |
| unused code、barrel import、tree shaking、manual chunks、Vite build を見直したい | [javascript/tree-shaking.md](javascript/tree-shaking.md), [javascript/vite-bundle-optimization.md](javascript/vite-bundle-optimization.md), [javascript/static-import.md](javascript/static-import.md) |
| analytics、ads、widget など third-party script が Core Web Vitals を悪化させている | [javascript/third-party.md](javascript/third-party.md), [javascript/loading-sequence.md](javascript/loading-sequence.md) |
| gzip / brotli など transfer compression を確認したい | [javascript/compression.md](javascript/compression.md), [javascript/vite-bundle-optimization.md](javascript/vite-bundle-optimization.md) |

## Rendering Strategy

| 症状・依頼 | 優先して読む reference |
|---|---|
| CSR / SSR / SSG / ISR のどれを使うべきか判断したい | [react/client-side-rendering.md](react/client-side-rendering.md), [react/server-side-rendering.md](react/server-side-rendering.md), [react/static-rendering.md](react/static-rendering.md), [react/incremental-static-rendering.md](react/incremental-static-rendering.md) |
| Streaming SSR、Selective Hydration、Progressive Hydration を扱う | [react/streaming-ssr.md](react/streaming-ssr.md), [react/react-selective-hydration.md](react/react-selective-hydration.md), [react/progressive-hydration.md](react/progressive-hydration.md) |
| React Server Components の境界、client JS 削減、server data access を判断したい | [react/react-server-components.md](react/react-server-components.md), [react/server-side-rendering.md](react/server-side-rendering.md) |
| content-heavy page で一部だけ interactivity が必要 | [javascript/islands-architecture.md](javascript/islands-architecture.md), [react/progressive-hydration.md](react/progressive-hydration.md) |
| page transition や UI state transition を滑らかにしたい | [javascript/view-transitions.md](javascript/view-transitions.md) |

## AI UI

| 症状・依頼 | 優先して読む reference |
|---|---|
| chat、assistant、streaming response、AI-driven UI を React で作る | [react/ai-ui-patterns.md](react/ai-ui-patterns.md), [react/react-data-fetching.md](react/react-data-fetching.md) |

## Review Mode

| レビュー観点 | 優先して読む reference |
|---|---|
| component API / composition の妥当性 | [react/react-composition-2026.md](react/react-composition-2026.md), [react/compound-pattern.md](react/compound-pattern.md), [react/hooks-pattern.md](react/hooks-pattern.md) |
| render performance regression | [react/react-render-optimization.md](react/react-render-optimization.md), [javascript/virtual-lists.md](javascript/virtual-lists.md) |
| bundle / loading regression | [javascript/dynamic-import.md](javascript/dynamic-import.md), [javascript/tree-shaking.md](javascript/tree-shaking.md), [javascript/vite-bundle-optimization.md](javascript/vite-bundle-optimization.md) |
| data fetching / cache regression | [react/react-data-fetching.md](react/react-data-fetching.md) |
| SSR / hydration regression | [react/server-side-rendering.md](react/server-side-rendering.md), [react/react-server-components.md](react/react-server-components.md), [react/react-selective-hydration.md](react/react-selective-hydration.md) |
