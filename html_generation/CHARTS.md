# HTML Chart Standards

> Chart embedding, figure theming, dashboard composition, and the interactive controls that ship inside generated HTML reports.

**ID** `html_generation/charts` · **Tier** Domain · **Version** 1.0
**Owns** chart-library embedding · figure theming contract · chart height rules · embedded JavaScript rules · cross-chart events · interactive controls · dashboard composition
**Defers to** offline-first · asset inlining · escaping · CSP · module structure → [STANDARDS.md](STANDARDS.md) · color + spatial tokens · container heights · z-index · motion → [THEMING.md](THEMING.md) · TypeScript typing · build config · lint → [typescript](../typescript/STANDARDS.md) · render + memory budgets → [performance](../performance/STANDARDS.md) · DOM assertion testing → [testing](../testing/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [THEMING.md](THEMING.md)

---

## Table of Contents

1. [Embedding](#1-embedding)
2. [Figure Theming](#2-figure-theming)
3. [Chart Height](#3-chart-height)
4. [Chart Configuration](#4-chart-configuration)
5. [Chart Selection](#5-chart-selection)
6. [Embedded JavaScript](#6-embedded-javascript)
7. [Cross-Chart Events](#7-cross-chart-events)
8. [Interactive Controls](#8-interactive-controls)
9. [Dashboard Composition](#9-dashboard-composition)
10. [Performance Budgets](#10-performance-budgets)
11. [Anti-Patterns](#11-anti-patterns)
12. [Checklist](#12-checklist)

---

## 1. Embedding

! The chart library is **inlined into the document**. There is no CDN, no `src`, no lazy load. This is the offline-first constraint from [STANDARDS.md](STANDARDS.md) §2 applied to charts.

| Output | Library embedding |
|---|---|
| Standalone chart page | Library embedded in full, `full_html` on |
| First figure in a multi-chart report | Library embedded once |
| Every subsequent figure in the same document | Library embedding **off** — emit the figure as a bare container `<div>` + init script |
| Figure inside a modal or lazily revealed panel | Library embedding off — it is already in the document |

Rules:

| Rule | Detail |
|---|---|
| Embed exactly once per document | Re-embedding multiplies file size by megabytes per chart |
| ✗ suppress embedding on a page with no prior figure | The chart renders as a blank div |
| Bundle choice | Use the smallest library bundle that covers the chart types actually rendered; ✗ full bundle when a partial one suffices |
| Version pinned | Library version is a pinned dependency — see [dependencies](../dependencies/STANDARDS.md) |
| Data is data | Figure data is serialized as JSON ([STANDARDS.md](STANDARDS.md) §8). ✗ host-language repr |

---

## 2. Figure Theming

Every figure is themed **before** it is embedded. An unthemed figure renders with library defaults — white background on a dark page.

Figure theming sets, from the theme registry ([THEMING.md](THEMING.md) §2):

| Figure property | Token |
|---|---|
| Paper background | `--surface` — the card the chart sits in, ✗ `--bg` |
| Plot background | `--surface` |
| Font color | `--text` |
| Axis tick / label color | `--text-muted` |
| Gridline color | `--border` |
| Template | Dark template for `dark`, light template for `light` and for the initial state of `device` |
| Autosize | On — the container decides the size (§3) |

Rules:

| Rule | Detail |
|---|---|
| ! Call before every embed | Theming applied at embed time, ✗ at figure construction time in engine code |
| ✗ height | Figure theming never sets a height (§3) |
| Categorical palette | Defined once in the theme registry; series colors drawn from it in order — same series color across every chart in the report |
| Sequential / diverging scales | Declared per chart type in the theme registry; ✗ library default rainbow scales |
| Diverging data | Zero-centered scale with a neutral midpoint — ✗ sequential scale on signed data |
| Device theme | Figures re-themed by the device switcher on OS preference change ([THEMING.md](THEMING.md) §4) |

---

## 3. Chart Height

**CSS owns height.** The figure declares autosize; the container class declares the height ([THEMING.md](THEMING.md) §7).

Exception — a figure whose intrinsic row count drives its height (stacked subplots, long horizontal bar charts, tall matrices) needs a computed pixel height. That height comes from **one** calculator, never a literal.

| Mode | Per-item allowance | Use for |
|---|---|---|
| `subplot` | 220 px per row | Stacked subplot rows |
| `bar` | 28 px per row | Horizontal bar categories |
| `heatmap` | 28 px per row | Matrix rows |
| `fixed` | — | Caller passes the height directly |

| Constant | Value |
|---|---|
| Base overhead (title, legend, margins) | 80 px |
| Clamp floor | 280 px |
| Clamp ceiling | 1800 px |

Rules:

- ✗ magic-number heights in engine or report code — call the calculator.
- ✗ height in the base layout dict or in the figure-theming helper.
- A chart with both a CSS container height and a figure height clips or double-scrolls. Pick one: CSS by default, calculator only for the row-driven exception.
- Container cap remains `80vh` ([THEMING.md](THEMING.md) §7) even when the calculator returns more — the container scrolls.

---

## 4. Chart Configuration

One shared config object, defined once ([STANDARDS.md](STANDARDS.md) §5), applied to every figure.

| Setting | Value | Reason |
|---|---|---|
| Responsive | on | Chart resizes with its container and on device rotation |
| Mode bar | shown | Zoom, pan, and image export are the report's only export path |
| Scroll zoom | on | Dense scatter and time series are unreadable without it |
| GL pixel ratio | `0` | ! Prevents WebGL memory bloat on high-DPI displays — a report with many GL charts crashes the tab without it |
| Image export | Local only | Export filename derives from the chart title |
| Logo / branding link | off | External link is an offline-first violation |

Rules:

- ✗ per-call-site literal config objects — one constant, imported.
- Resize: charts inside a modal, a collapsed section, or an off-canvas panel must be relayed out when revealed — a chart sized while hidden renders at zero width.

---

## 5. Chart Selection

Chart type follows the question, not preference.

| Question | Chart | Constraint |
|---|---|---|
| Distribution of one numeric | Histogram · box · violin | Bin count declared, ✗ library default when n is small |
| Relationship, two numerics | Scatter | > 5,000 points → density heatmap or sampled scatter (§10) |
| Comparison across categories | Horizontal bar | Sorted by value, ✗ alphabetical ; category has a natural order |
| Composition of a whole | Stacked bar | ✗ pie beyond 5 slices ; ✗ donut chart in a data report |
| Change over time | Line | Time on the x axis, ordered ascending |
| Correlation matrix | Heatmap | Diverging scale, zero-centered, symmetric ordering |
| Ranking | Ordered bar | Top-N with an explicit "N of M shown" label |
| Missingness | Matrix / bar of null rate | Rate, not count, when column lengths differ |

Rules:

| Rule | Detail |
|---|---|
| Axes labeled | Every axis carries a name and, where applicable, a unit |
| Y axis on counts starts at zero | Truncated count axes misrepresent magnitude |
| Truncation disclosed | Any chart showing a subset states the subset in its title or caption |
| Legend suppressed for one series | A one-item legend is noise |
| Number formatting | Thousands separated; floats to a declared precision; percentages carry `%` |
| Text alternative | Every chart is accompanied by its underlying table or a caption stating its finding ([THEMING.md](THEMING.md) §12) |

---

## 6. Embedded JavaScript

### Language

| Rule | Detail |
|---|---|
| Vanilla only | ! No framework or library runtime is embedded — ✗ React · Vue · Angular · Alpine · jQuery · Lodash |
| No module system | ✗ `import` · ✗ `require()` in emitted script — nothing can be fetched |
| Baseline | ES2017+ authored directly, or TypeScript **compiled** to it. TypeScript is an authoring tool; only its output is embedded. Typing, build config, and lint rules → [typescript](../typescript/STANDARDS.md) |
| No build step, no TS | Projects without a build step author vanilla JS directly |
| Strict mode | Every script block runs in strict mode |

| Feature | Rule |
|---|---|
| Declarations | `const` / `let` only. ✗ `var` |
| Callbacks | Arrow functions |
| String building | Template literals |
| Safe access | Optional chaining · nullish coalescing for defaults |
| Async | Rare in a static report; permitted for clipboard and blob APIs |

### Structure

| Rule | Detail |
|---|---|
| IIFE per block | Every emitted script block is wrapped in an immediately-invoked function. Zero globals |
| No cross-block globals | Blocks are written independently and concatenated — a global from one collides with another. Communicate via events (§7) |
| Guard on missing elements | Every block resolves its elements and returns early when absent — a report that omits a section must not throw |
| Idempotent init | Re-running an init block must not double-bind listeners |
| Data in | Host data arrives as JSON parsed into a `const` ([STANDARDS.md](STANDARDS.md) §8) |
| ✗ `eval` · ✗ `new Function` · ✗ `innerHTML` with data | See [STANDARDS.md](STANDARDS.md) §8 |

### Errors

A failing control must never break the page. Wrap each feature's init; on failure, log to the console and leave the static content intact. The report is readable with every script removed.

---

## 7. Cross-Chart Events

When one control affects several charts, the control ✗ calls chart functions directly.

| Rule | Detail |
|---|---|
| Event bus | Controls dispatch a custom event on the document; charts subscribe. Control and chart never reference each other |
| Event payload | Carries the source id and the change — enough for a subscriber to act without asking back |
| Source ignores itself | A chart ignores events it emitted |
| ✗ chained events | An event handler ✗ dispatch another bus event — cycles are unbounded |
| State store | Filter state lives in one module-scoped object per report; the event carries the delta, the store holds the truth |
| Reset | Every cross-chart interaction has a visible "Clear filter" control restoring all charts |

Persisted UI state (collapsed sections, active tab, column selection) → tab-scoped session store, keyed by section or control id ([THEMING.md](THEMING.md) §11). ✗ persistent local storage.

---

## 8. Interactive Controls

Progressive enhancement is binding: the page is fully readable with JavaScript disabled. Controls enhance, ✗ gate.

| Control | Required when | Contract |
|---|---|---|
| Column / variable picker | Report covers > 10 columns | Dropdown with search box · checkbox list · Select-all · Clear. Search filters live, debounced ≥ `150ms`. Selection persisted in the session store. Menu closes on outside click and on `Escape` |
| Numeric range filter | Table filterable by a numeric column | Min input · max input · Apply · Clear. Validate `min ≤ max` → ! inline error on violation; ✗ silently clamp or swap |
| Live table search | Table has > 20 rows | Debounced ≥ `150ms` live row filter over all visible row text. Shows a "N of M rows" count |
| Sortable table | Any static data table | Click header to sort; ▲ / ▼ indicator on the active column only. Numeric columns sort numerically, others lexicographically. Sortable headers are keyboard activatable |
| Chart expand | Chart in a grid of charts | Expand button opens the chart in a modal at full size. `Escape` or backdrop click closes and returns the chart to its card. Modal open and close both trigger a chart relayout |
| Cross-filter | Dashboard with related charts | Uses the library's **selection** event, ✗ its click event — click fires on hover-adjacent points and is not clearable. Non-selected points dim via opacity; a "Clear filter" button restores all |
| Collapsible section | Report over ~5 sections | Heading toggles the section; state persisted per section id in the session store; collapsed sections expand for print |
| Row limit + "show more" | Table exceeding the row cap (§10) | Explicit "N more rows" footer. ✗ silently truncate |

Rules for every control:

| Rule | Detail |
|---|---|
| Keyboard | Tab to reach · Enter/Space to activate · `Escape` to dismiss |
| Reset | Every filter has a visible Clear/Reset. A user must never be stuck in a filtered state with no way out |
| Focus | Modal traps focus while open and returns focus to the invoking button on close |
| Labels | Icon-only controls carry accessible labels |
| No hidden data | Filters are user-initiated; the default state shows everything within the row cap |
| Listeners | Attached with `addEventListener`, ✗ inline handlers ([STANDARDS.md](STANDARDS.md) §8) |

---

## 9. Dashboard Composition

| Rule | Detail |
|---|---|
| One question per section | A section answers one question; its charts are the evidence |
| KPI row first | Headline metrics at the top as cards — value · label · optional delta |
| Deltas signed | A delta shows direction by sign and color, ✗ color alone ([THEMING.md](THEMING.md) §12) |
| Chart grid second | Auto-fill grid ([THEMING.md](THEMING.md) §7), ordered most-to-least important |
| Table last | The backing table follows the charts it summarizes |
| Consistent series color | The same series is the same color in every chart of the report (§2) |
| Consistent axes | Charts compared side by side share axis scale and units, or state that they do not |
| Section count | > 5 sections → sidebar navigation + scroll spy is required ([THEMING.md](THEMING.md) §11) |
| Chart count | > 12 charts on one page → split into sections with collapsible bodies, or into separate reports (§10) |

---

## 10. Performance Budgets

A generated report opens on a laptop and a phone. Budgets are hard.

| Budget | Limit | Action on breach |
|---|---|---|
| Output file size | ≤ 5 MB | Sample data · truncate table rows · split the report |
| Charts per page | ≤ 12 rendered on load | Render below-fold charts on section reveal |
| Points per scatter | ≤ 5,000 | Sample or switch to a density heatmap; state the sampling in the title |
| Table rows in DOM | ≤ 1,000 | Truncate with an explicit "N more rows" footer |
| WebGL charts per page | ≤ 4 | Fall back to SVG rendering for the rest |
| Time to interactive | ≤ 2 s on a mid-range laptop | Reduce charts, points, or rows — in that order |

Rules:

- GL pixel ratio is pinned (§4) — without it, high-DPI displays multiply WebGL memory per chart.
- Sampling is always disclosed in the chart title or caption. ✗ silently sample.
- Row and point caps are configuration with documented defaults, ✗ hardcoded at call sites.
- Measurement method and profiling → [performance](../performance/STANDARDS.md).

---

## 11. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| Chart library from a CDN | Blank report offline | Inline the library (§1) |
| Library embedded per chart | 20 MB report | Embed once per document (§1) |
| Embedding suppressed on a first figure | Blank div | Embed on the first figure (§1) |
| Figure embedded without theming | White chart on a dark page | Theme before embed (§2) |
| Figure background `--bg` inside a card | Visible seam | Use `--surface` (§2) |
| Hardcoded `height=600` | Clipping, double scrollbars | CSS height or the calculator (§3) |
| Config object copy-pasted per chart | Drift; missing GL pixel ratio | One shared config (§4) |
| Chart sized while hidden | Zero-width chart on reveal | Relayout on reveal (§4) |
| Framework runtime embedded | Megabytes and an import that cannot resolve | Vanilla JS (§6) |
| Globals shared across script blocks | Name collision between independent features | IIFE per block; events between them (§7) |
| Click event used for cross-filter | Fires on the wrong point; cannot be cleared | Selection event + Clear button (§8) |
| Filter with no reset | User trapped in a filtered view | Clear/Reset on every filter (§8) |
| Silent row truncation | Reader believes they see all data | Explicit "N more rows" (§8, §10) |
| Undisclosed scatter sampling | Reader misreads density | State sampling in the title (§10) |
| Pie chart with 12 slices | Unreadable | Sorted horizontal bar (§5) |

---

## 12. Checklist

- [ ] Chart library inlined; zero CDN or `src` references
- [ ] Library embedded exactly once per document
- [ ] Figure theming applied immediately before every embed
- [ ] Figure paper and plot backgrounds use `--surface`, font uses `--text`
- [ ] No height set in the layout dict or the figure-theming helper
- [ ] Row-driven heights come from the height calculator, clamped to [280, 1800]
- [ ] No magic-number chart heights anywhere in engine or report code
- [ ] One shared chart config; GL pixel ratio pinned to `0`
- [ ] Charts revealed from modals, collapsed sections, or panels are relaid out on reveal
- [ ] Series colors come from the shared categorical palette and are stable across charts
- [ ] Every axis is labeled; count axes start at zero
- [ ] Any sampled or truncated chart discloses it in its title or caption
- [ ] Embedded JS is vanilla — no framework runtime, no `import`, no `require`
- [ ] Every script block is an IIFE in strict mode with no globals
- [ ] Every script block guards on missing elements and fails without breaking the page
- [ ] Host data reaches JS as JSON, never as native repr
- [ ] Cross-chart communication goes through custom events, not direct calls
- [ ] Cross-filter uses the selection event, not the click event
- [ ] Every filter and cross-filter has a visible Clear/Reset control
- [ ] Table search and picker search are debounced ≥ 150 ms
- [ ] Range filters validate min ≤ max and show an inline error
- [ ] Sort indicator appears on the active column only
- [ ] Expand modal closes on Escape and backdrop click, and restores the chart
- [ ] Collapsible section state persists in the session store and expands for print
- [ ] All controls are keyboard operable and carry accessible labels
- [ ] Page stays within budget: ≤ 5 MB, ≤ 12 charts, ≤ 5,000 scatter points, ≤ 1,000 table rows
