# React References

この index はエージェントが参照候補を探索するための目次。個別ファイルをユーザーに選ばせるための一覧ではない。
実装判断では、必要な reference の `Original Skill Metadata` と `original-skill-body` を読む。

| Category | Original skill | 主な使用場面 | File |
|---|---|---|---|
| Data Fetching | `react-data-fetching` | cache、deduplication、optimistic update、parallel loading を設計するとき | [react-data-fetching.md](react-data-fetching.md) |
| Design | `ai-ui-patterns` | chat、assistant、streaming UI など AI-driven React UI を作るとき | [ai-ui-patterns.md](ai-ui-patterns.md) |
| Design | `compound-pattern` | tabs、accordion、dropdown など関連 component の implicit shared state が必要なとき | [compound-pattern.md](compound-pattern.md) |
| Design | `hoc-pattern` | auth、logging、data fetching など cross-cutting concern を複数 component に渡したいとき | [hoc-pattern.md](hoc-pattern.md) |
| Design | `hooks-pattern` | shared stateful logic、side effect、subscription を custom hook に抽出したいとき | [hooks-pattern.md](hooks-pattern.md) |
| Design | `presentational-container-pattern` | view と data fetching / business logic を分離したいとき | [presentational-container-pattern.md](presentational-container-pattern.md) |
| Design | `react-2026` | 新規 React app や modern stack への更新で tool / routing / state 方針を選ぶとき | [react-2026.md](react-2026.md) |
| Design | `react-composition-2026` | component API、shared UI library、prop-heavy component を現代的に設計したいとき | [react-composition-2026.md](react-composition-2026.md) |
| Design | `render-props-pattern` | rendering logic を function prop で柔軟に共有したいとき | [render-props-pattern.md](render-props-pattern.md) |
| Performance | `react-render-optimization` | 不要再レンダリング、memoization、state design、sluggish UI を診断するとき | [react-render-optimization.md](react-render-optimization.md) |
| Rendering | `client-side-rendering` | SEO より interactivity が中心の React UI を client で描画するとき | [client-side-rendering.md](client-side-rendering.md) |
| Rendering | `incremental-static-rendering` | static page を full rebuild なしで定期更新したいとき | [incremental-static-rendering.md](incremental-static-rendering.md) |
| Rendering | `progressive-hydration` | server-rendered page の非重要 section の JS を遅延したいとき | [progressive-hydration.md](progressive-hydration.md) |
| Rendering | `react-selective-hydration` | streaming SSR と hydration priority を組み合わせたいとき | [react-selective-hydration.md](react-selective-hydration.md) |
| Rendering | `react-server-components` | server data access だけで client JS が不要な component を扱うとき | [react-server-components.md](react-server-components.md) |
| Rendering | `server-side-rendering` | SEO、初期表示、per-request HTML が必要な React app を扱うとき | [server-side-rendering.md](server-side-rendering.md) |
| Rendering | `static-rendering` | build time に pre-render できる cacheable page を扱うとき | [static-rendering.md](static-rendering.md) |
| Rendering | `streaming-ssr` | HTML streaming で TTFB / FCP を改善したいとき | [streaming-ssr.md](streaming-ssr.md) |
