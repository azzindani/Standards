# HTML_STANDARDS.md — Data Visualization & Report Layout

Version 1.1 — applies to all MCP projects that produce HTML output.

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Fundamental Rules](#2-fundamental-rules)
3. [Theme System](#3-theme-system)
4. [CSS Architecture](#4-css-architecture)
5. [Plotly Integration](#5-plotly-integration)
6. [Output Path](#6-output-path)
7. [Module Structure](#7-module-structure)
8. [Standard Functions](#8-standard-functions)
9. [HTML Document Structure](#9-html-document-structure)
10. [Security](#10-security)
11. [Cross-Platform](#11-cross-platform)
12. [Checklist](#12-checklist)
13. [JavaScript & TypeScript Standards](#13-javascript--typescript-standards)
14. [Interactive Controls](#14-interactive-controls)
15. [UX Patterns](#15-ux-patterns)

---

## 1. Purpose

This document defines how all MCP projects that produce HTML files — charts,
dashboards, EDA reports, profiling reports — must structure, theme, and deliver
those outputs.

These rules exist because:
- All MCP servers run locally, offline, without internet access.
- LLMs call tools with limited context; output must open and render immediately.
- Reports must work on mobile without installing anything.
- Every project must produce visually consistent output.

---

## 2. Fundamental Rules

### No CDN. Ever.

All assets — Plotly, fonts, icons — must be **inline or system-supplied**.
No `<script src="https://...">`, no `@import url(...)`, no remote anything.

```python
# Wrong
PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"   # must not exist

# Correct
fig.to_html(include_plotlyjs=True, ...)   # embeds Plotly inline
```

If a file contains a `PLOTLY_CDN` constant, it is a violation even if not used.

### System fonts only

```css
/* Correct */
font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;

/* Wrong — downloads a font */
@import url('https://fonts.googleapis.com/...');
```

### Default theme is dark

All projects default to `theme="dark"` (`plotly_dark` template, `#0d1117`
background). Use `theme="light"` or `theme="device"` when the caller requests.

### All HTML outputs accept `theme` and `open_after`

Every tool that produces an HTML file must expose:
```python
theme: str = "dark"        # "dark" | "light" | "device"
open_after: bool = True    # open in browser after saving
```

---

## 3. Theme System

### Three themes

| Value | Plotly template | Background | When |
|---|---|---|---|
| `"dark"` | `plotly_dark` | `#0d1117` | Default |
| `"light"` | `plotly_white` | `#ffffff` | Caller opt-in |
| `"device"` | starts `plotly_white` | JS-switched | Follows system pref |

### Color tokens — dark

```
--bg:         #0d1117    page background
--surface:    #161b22    cards, sidebar, chart background
--border:     #21262d    borders, dividers
--text:       #c9d1d9    body text
--text-muted: #8b949e    labels, metadata
--accent:     #58a6ff    headings, links, active states
--green:      #3fb950    success, good values
--orange:     #f0883e    warnings
--red:        #f85149    errors, bad values
```

### Color tokens — light

```
--bg:         #ffffff
--surface:    #f6f8fa
--border:     #d0d7de
--text:       #1f2328
--text-muted: #636c76
--accent:     #0969da
--green:      #1a7f37
--orange:     #9a6700
--red:        #cf222e
```

### CSS token function

```python
def css_vars(theme: str) -> str:
    """Return :root{} block for the theme. Includes device media query if needed."""
```

For `"device"`: emit `:root{light vars}` + `@media(prefers-color-scheme:dark){:root{dark vars}}`.

### Spatial tokens (layout vars — same for all themes)

Spatial dimensions belong in a second token block that is merged with color vars.
All values in `rem`, no `px`.

```
--sidebar-w:     16.25rem     (260 px equivalent)
--sidebar-w-md:  13.75rem     (220 px at tablet breakpoint)
--main-pad:      2rem
--main-pad-sm:   1rem
--section-gap:   3rem
--card-gap:      0.75rem
--card-min:      8rem
--card-pad:      1rem
--radius-sm:     0.375rem
--radius-md:     0.625rem
--radius-lg:     0.75rem
--font-xs:       0.6875rem    (~11 px)
--font-sm:       0.8125rem    (~13 px)
--font-base:     1rem
--font-lg:       1.125rem
--font-xl:       1.25rem
--font-2xl:      clamp(1.125rem, 2vw, 1.5rem)
--chart-radius:  0.75rem
```

### Device-mode JS

Every `"device"` themed page must inject a JS snippet that:
1. Reads `window.matchMedia('(prefers-color-scheme:dark)')` on load
2. Sets `document.documentElement.setAttribute('data-theme', 'dark'|'light')`
3. Calls `Plotly.relayout()` on all `.plotly-graph-div` elements with matching
   `template`, `paper_bgcolor`, `plot_bgcolor`
4. Adds a `change` listener to update on system pref change

This snippet lives in `device_mode_js()` in `html_theme.py`.

---

## 4. CSS Architecture

### Units — never px for layout or typography

| Use case | Rule |
|---|---|
| Spacing, padding, margins | `rem` |
| Fluid headings, card numbers | `clamp()` |
| Chart container heights | `clamp()` via CSS class |
| Border radius | `rem` or CSS custom property |
| Borders | `1px` is the only allowed `px` (browser minimum) |

```css
/* Wrong */
.card { padding: 16px; font-size: 13px; }

/* Correct */
.card { padding: var(--card-pad); font-size: var(--font-sm); }
```

### Reset and base

Always first:
```css
*{box-sizing:border-box;margin:0;padding:0}
*{overflow-wrap:break-word;word-break:break-word}
code,pre,kbd,samp{word-break:normal;overflow-wrap:normal;overflow-x:auto}
html{scroll-behavior:smooth;font-size:16px}
```

### Text blowout prevention

Apply to all user-supplied content (column names, values, file names):
```css
overflow-wrap: break-word;
word-break: break-word;
```

For card numbers that must not wrap: use ellipsis instead:
```css
.card .num { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
```

### CSS structure order

Always layer CSS in this order:
1. CSS custom properties (`:root{}`)
2. Reset / base (`*`, `html`, `body`)
3. Scrollbar
4. Typography (`h1`–`h3`, helpers)
5. Component classes (cards, tables, charts, alerts, insights)
6. Layout (sidebar, main, header)
7. Responsive breakpoints (tablet → mobile → small mobile)
8. Print

### Z-index layers

| Layer | Value | Element |
|---|---|---|
| Overlay / backdrop | 90 | `#sb-overlay` |
| Sidebar | 100 | `.sidebar` |
| Mobile toggle button | 200 | `#sb-toggle` |
| Dropdowns / tooltips | 200 | `.ddmenu` |
| Modals | 1000 | `.modal` |

### Responsive breakpoints (rem, not px)

| Breakpoint | Max-width | Behaviour |
|---|---|---|
| Tablet | `68.75rem` | Sidebar narrows to `--sidebar-w-md` |
| Mobile | `48rem` | Sidebar hides; hamburger appears; single-column layout |
| Small mobile | `30rem` | Card grid collapses to 1 column |

Never use `px` in `@media` queries — use `em` or `rem` so they scale with
user font settings.

### Mobile sidebar — hamburger toggle required

The sidebar must never just `display:none` on mobile. It must be accessible via
a hamburger button with an overlay backdrop:

```html
<button id="sb-toggle" aria-label="Open navigation">&#9776;</button>
<div id="sb-overlay"></div>
```

```css
@media(max-width:48em) {
  #sb-toggle { display:flex; ... }
  .sidebar { transform:translateX(-100%); }
  .sidebar.open { transform:translateX(0); }
  #sb-overlay.show { display:block; }
}
```

JS to wire it up lives in `_SIDEBAR_JS` in `html_theme.py`.

### Grid layout for chart grids

Use CSS Grid with `auto-fill` + `minmax()` for chart grids. Never use fixed
column counts.

```css
.cgrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, clamp(18rem,42vw,34rem)), 1fr));
  gap: clamp(.5rem,1.5vw,.875rem);
}
```

Always set `min-width:0` on direct grid/flex children to prevent overflow.

### Chart container heights

CSS controls chart height. Plotly receives `autosize=True` and no `height` in
the layout dict. The container div has a defined height via a CSS class.

```css
.chart-div          { height: clamp(18rem, 40vh, 30rem); }
.chart-div.heatmap  { height: clamp(22rem, 50vh, 38rem); }
.chart-div.compact  { height: clamp(14rem, 30vh, 22rem); }
.chart-div.network  { height: clamp(20rem, 45vh, 34rem); }
```

Cap all chart heights at `80vh` maximum to prevent infinite scroll on tall
charts.

### Tables

Always wrap tables in a scroll container. Never let a table bleed off-screen.

```html
<div class="table-wrap"><table>...</table></div>
```

```css
.table-wrap { overflow-x:auto; -webkit-overflow-scrolling:touch; }
table { min-width: 30rem; }
th { white-space: nowrap; }
td { max-width: 20rem; overflow-wrap: break-word; }
```

### Transitions

Maximum `0.2s` for any UI transition (background, color, transform). Longer
transitions are distracting and make tools feel slow.

### Print media query

Every multi-section report must include:
```css
@media print {
  .sidebar, #sb-toggle, #sb-overlay { display:none !important; }
  .main { margin-left:0 !important; padding:0 !important; }
  .chart-container { break-inside:avoid; border:1px solid #ccc; }
  .section { break-inside:avoid; }
}
```

### Custom scrollbar

```css
::-webkit-scrollbar       { width: 0.375rem; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: var(--radius-sm); }
```

---

## 5. Plotly Integration

### Always inline — never CDN

```python
# Standalone page (save_chart, full HTML)
fig.to_html(include_plotlyjs=True, full_html=True, ...)

# Embedded div inside a report page that already loaded Plotly
pio.to_html(fig, include_plotlyjs=False, full_html=False, ...)
```

Use `include_plotlyjs=False` only when Plotly has already been embedded once
earlier in the same HTML document.

### Standard Plotly config

Always pass this config dict:
```python
{
    "responsive": True,
    "displayModeBar": True,
    "scrollZoom": True,
    "plotGlPixelRatio": 0,   # prevents WebGL memory bloat
}
```

### `apply_fig_theme()` — always call before embedding

Before embedding any figure in a report, set its background to match the card
surface token to prevent background mismatch:

```python
def apply_fig_theme(fig, theme: str) -> None:
    t = get_theme(theme)
    fig.update_layout(
        paper_bgcolor=t["paper_color"],
        plot_bgcolor=t["paper_color"],
        font=dict(color=t["text_color"]),
        template=plotly_template(theme),
        autosize=True,
    )
```

### `plotly_layout_base()` — no height in layout

```python
def plotly_layout_base(plot_bg: str, font_color: str, margin=None) -> dict:
    """Base layout dict. Never includes height — CSS controls that."""
    return {
        "paper_bgcolor": plot_bg,
        "plot_bgcolor":  plot_bg,
        "font":          {"color": font_color},
        "margin":        margin or {"l": 50, "r": 20, "t": 20, "b": 40},
        "autosize":      True,
    }
```

### `calc_chart_height()` — no magic numbers

Use this for standalone charts or embedded charts that need a Plotly `height`
(e.g., stacked subplots where CSS height alone is insufficient):

```python
def calc_chart_height(n: int = 1, mode: str = "subplot", extra_base: int = 0) -> int:
    """
    mode:  "subplot"  — stacked subplot rows
           "bar"      — horizontal bar rows
           "heatmap"  — matrix rows
           "fixed"    — return n directly
    Returns int px, clamped to [280, 1800].
    """
```

Per-item constants: subplot=220px/row, bar=28px/row, heatmap=28px/row,
base=80px overhead. Never hardcode these numbers in calling code.

### Template consistency

| Theme | Plotly template |
|---|---|
| `"dark"` | `"plotly_dark"` |
| `"light"` | `"plotly_white"` |
| `"device"` | starts `"plotly_white"`, JS switches to `"plotly_dark"` |

---

## 6. Output Path

### Downloads-first priority

```
1. Explicit output_path argument (if provided and non-empty)
2. ~/Downloads/<stem>_<suffix>.html  (if ~/Downloads exists)
3. Same directory as the input file
```

```python
def get_output_path(
    output_path: str,
    input_path: Path,
    stem_suffix: str,
    ext: str = "html",
) -> Path:
    if output_path:
        return Path(output_path).resolve()
    downloads = Path.home() / "Downloads"
    base_dir = downloads if downloads.is_dir() else input_path.parent
    return base_dir / f"{input_path.stem}_{stem_suffix}.{ext}"
```

Always call `.resolve()` on the explicit path — never return a relative Path.

### File naming convention

`{input_stem}_{descriptor}.html`

Examples:
- `sales_dashboard.html`
- `sales_eda.html`
- `sales_profile.html`
- `sales_distribution.html`
- `sales_correlation.html`

### Atomic writes

Always write HTML via atomic write (temp file → move), never direct open/write:

```python
from shared.file_utils import atomic_write_text
atomic_write_text(out_path, html, encoding="utf-8")
```

Or use `Path.write_text(html, encoding="utf-8")` if atomicity is guaranteed by
the file system context (single-threaded tool call).

### Tool response must include output path

Every tool that saves an HTML file must include in its return dict:
```python
{
    "output_path": str(out.resolve()),
    "filename":    out.name,
}
```

---

## 7. Module Structure

Every project that produces HTML output must have exactly these two files in
`shared/`:

```
shared/
├── html_layout.py   ← CSS strings, layout helpers, get_output_path()
└── html_theme.py    ← theme helpers, Plotly wrappers, report builders
```

### `html_layout.py` owns

- `get_output_path()` — Downloads-first path resolution
- `VIEWPORT_META` — the single source of truth (never redefine elsewhere)
- `PLOTLY_CFG_JS` — standard Plotly config as a JS string (for inline scripts)
- `plotly_config()` — standard Plotly config as a Python dict
- `_BASE_CSS`, `_REPORT_CSS`, `_DASHBOARD_CSS` — raw CSS string blocks
- `css_report()`, `css_dashboard()` — full CSS assemblers
- `plotly_layout_base()` — base Plotly layout dict (no height)

### `html_theme.py` owns

- `PLOTLY_TEMPLATE` dict + `plotly_template()` — theme → template name
- `_DARK_VARS`, `_LIGHT_VARS`, `_LAYOUT_VARS` — CSS token strings
- `css_vars()` — theme → `:root{}` CSS block
- `_DEVICE_JS` + `device_mode_js()` — device-mode theme switcher
- `_SIDEBAR_JS` — hamburger toggle JS
- `THEMES` dict + `get_theme()` — full theme config dicts
- `theme_plot_colors()` — returns (plot_bg, font_color, accent) tuple
- `apply_fig_theme()` — sets Plotly figure colors to match CSS tokens
- `calc_chart_height()` — formula-based chart height calculator
- `save_chart()` — save standalone Plotly figure as HTML
- `build_html_report()` — assemble multi-section HTML report
- `plotly_div()` — embed figure as inline div within a report
- `metrics_cards_html()` — render a dict as card HTML
- `data_table_html()` — render a list of dicts as scrollable table HTML
- `_open_file()` — cross-platform browser/viewer launch

### What must NOT exist anywhere

- `PLOTLY_CDN` constant — prohibited in all shared files
- Duplicate `VIEWPORT_META` — defined only in `html_layout.py`, imported everywhere else
- Hardcoded `height` in `plotly_layout_base()` or `apply_fig_theme()`
- Magic-number chart heights in engine code — use `calc_chart_height()`

---

## 8. Standard Functions

These functions must exist with exactly these signatures in every project that
produces HTML output. Deviate in implementation only — not in signature or
contract.

### `save_chart(fig, output_path, theme, open_browser, title) -> (str, str)`

Saves a standalone Plotly figure as a full responsive HTML page.
Returns `(absolute_path_str, filename)`.

### `build_html_report(title, subtitle, sections, theme, open_browser, output_path, ...) -> str`

Assembles a multi-section HTML report with sidebar navigation, hamburger toggle,
device-mode support, and print stylesheet.
`sections` is a list of `{"id": str, "heading": str, "html": str}`.
Returns rendered HTML string. Writes to `output_path` if provided.

### `plotly_div(fig, height, theme) -> str`

Embeds a Plotly figure as an inline `<div>` without a full HTML page wrapper.
Sets `include_plotlyjs=False`. Uses `apply_fig_theme()` before embedding.

### `calc_chart_height(n, mode, extra_base) -> int`

Returns a chart height in px, clamped to [280, 1800].

### `apply_fig_theme(fig, theme) -> None`

Applies `paper_bgcolor`, `plot_bgcolor`, `font color`, `template`, `autosize=True`
to a figure, using token values matching the CSS `--surface` and `--text` vars.

### `get_output_path(output_path, input_path, stem_suffix, ext) -> Path`

Downloads-first path resolution. Always resolves explicit paths.

### `metrics_cards_html(metrics, styles) -> str`

Renders a `dict[str, Any]` as a `.cards` grid of `.card` divs.

### `data_table_html(rows, max_rows) -> str`

Renders a `list[dict]` as a `.table-wrap > table`. Appends a "N more rows"
footer when truncated.

### `_open_file(path) -> None`

Cross-platform file open. Best-effort, never raises. Logs failures to stderr.

---

## 9. HTML Document Structure

Every full HTML page must follow this skeleton:

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page Title</title>
<style>
/* css_vars(theme) + all CSS */
</style>
</head><body>

<!-- Page content -->

<!-- device_mode_js() injected here if theme=="device" -->
<!-- _SIDEBAR_JS injected here if page has a sidebar -->
</body></html>
```

### Required elements on every page

- `<!DOCTYPE html>` — always first line
- `<html lang="en">` — lang attribute required
- `<meta charset="utf-8">` — always first in head
- `<meta name="viewport" ...>` — use the `VIEWPORT_META` constant
- All CSS inlined in `<style>` — no external stylesheets
- All JS inlined in `<script>` — no external scripts
- `encoding="utf-8"` on every `write_text()` call

### Section structure for reports

Every major section in a multi-section report must have a matching `id`
for sidebar anchor navigation:

```html
<div id="overview" class="section">
  <h2>Overview</h2>
  ...
</div>
```

The sidebar `<a href="#overview">` must match exactly.

---

## 10. Security

### No CDN assets

No `<script src="...">` or `<link href="...">` pointing to external URLs.
The only scripts and styles in the page are those written by the server itself.

### No `eval()` or `new Function()`

No JavaScript `eval()`. No `new Function(string)`. All JS is static, authored
at server build time.

### No inline event handlers

No `onclick="..."`, `onload="..."`, or other inline event attributes in HTML.
All event listeners must be attached via `addEventListener()` in `<script>`.

### No user content injected as raw HTML

Column names, file names, and data values passed into HTML must be
HTML-escaped. Use `html.escape()`:

```python
import html
safe_name = html.escape(column_name)
```

Never: `f"<td>{column_name}</td>"`
Always: `f"<td>{html.escape(str(column_name))}</td>"`

---

## 11. Cross-Platform

### Font stack

```css
font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
```

`Segoe UI` renders on Windows. `system-ui` / `-apple-system` cover macOS/Linux.
The stack degrades gracefully everywhere.

### Monospace font stack

```css
font-family: 'Cascadia Code', 'Fira Mono', monospace;
```

### Browser auto-open (`_open_file`)

```python
if sys.platform == "win32":
    os.startfile(str(p))
elif sys.platform == "darwin":
    subprocess.Popen(["open", str(p)])
else:
    subprocess.Popen(["xdg-open", str(p)])
```

Always `best-effort, never raises`. Wrap in try/except and log to stderr.

### Output path separators

Always use `pathlib.Path` for path construction. Never string concatenation.
`Path.resolve()` returns the OS-native separator automatically.

---

## 12. Checklist

Use this checklist when adding or reviewing any tool that produces HTML output.

### HTML output checklist

- [ ] No CDN URLs anywhere in the file (no `https://cdn.`, no `PLOTLY_CDN`)
- [ ] `include_plotlyjs=True` for standalone pages; `False` for embedded divs
- [ ] `apply_fig_theme(fig, theme)` called before every `plotly_div()` or embed
- [ ] `autosize=True` in figure layout; no hardcoded `height` in layout dict
- [ ] `calc_chart_height()` used for any standalone chart needing a px height
- [ ] `get_output_path()` used for output path resolution (Downloads-first)
- [ ] Explicit `output_path` passed through `.resolve()`
- [ ] `"output_path"` and `"filename"` keys in tool return dict
- [ ] `theme` parameter accepts `"dark"` | `"light"` | `"device"`
- [ ] `open_after: bool = True` parameter present
- [ ] Device-mode JS injected when `theme == "device"`
- [ ] `VIEWPORT_META` injected into `<head>` (imported from `html_layout.py`)
- [ ] `<!DOCTYPE html>`, `<html lang="en">`, `<meta charset="utf-8">` present
- [ ] All CSS inlined; no external stylesheets
- [ ] All JS inlined; no external scripts
- [ ] User content HTML-escaped before injection
- [ ] No `onclick=...` inline handlers; `addEventListener()` only
- [ ] No `eval()` or `new Function()` anywhere in JS

### CSS checklist

- [ ] No `px` except `1px` borders
- [ ] Spacing and typography use `rem` or CSS custom properties
- [ ] Fluid values use `clamp()`
- [ ] `overflow-wrap:break-word` on all user-content elements
- [ ] Tables wrapped in `.table-wrap` div
- [ ] `min-width:0` on flex/grid children
- [ ] Hamburger sidebar toggle for mobile (not just `display:none`)
- [ ] Print media query present on multi-section reports
- [ ] Custom scrollbar styles present
- [ ] Z-index follows defined layer table
- [ ] Transitions ≤ 0.2s

### Module structure checklist

- [ ] `VIEWPORT_META` defined only in `html_layout.py` (not redefined in `html_theme.py`)
- [ ] `get_output_path()` lives in `html_layout.py`
- [ ] `calc_chart_height()`, `apply_fig_theme()`, `build_html_report()` live in `html_theme.py`
- [ ] `_open_file()` lives in `html_theme.py`
- [ ] No `PLOTLY_CDN` constant anywhere in shared/

### JavaScript checklist

- [ ] Vanilla JS only — no framework imports (React, Vue, Alpine, jQuery)
- [ ] All Python data → JS via `json.dumps()`, never raw Python repr
- [ ] All variables declared inside IIFEs — no global pollution
- [ ] `const`/`let` only, never `var`
- [ ] `addEventListener()` only — no inline event attributes
- [ ] No `eval()`, no `new Function()`
- [ ] Cross-chart events use `CustomEvent` + `dispatchEvent`
- [ ] `sessionStorage` used for UI state that should survive page reload

### Interactive controls checklist

- [ ] Column/variable pickers: search box + checkbox list + Select-all/Clear-all
- [ ] Numeric range filters: two inputs with min/max validation
- [ ] Table search: debounced (≥ 150 ms) live row filter
- [ ] Sortable tables: `▲`/`▼` indicator on sorted column
- [ ] Chart expand: `⛶` button → modal; ESC or backdrop closes
- [ ] Collapsible sections: state persisted in `sessionStorage`
- [ ] Cross-filter: Plotly `plotly_selected` used, not `plotly_click`
- [ ] All controls fully keyboard-accessible (Tab, Enter, Escape)
- [ ] "Clear" / "Reset" available for every filter

### UX patterns checklist

- [ ] Scroll spy: `IntersectionObserver` drives sidebar `.active` class
- [ ] Section headings: `position:sticky;top:0` to stay visible while scrolling
- [ ] Animated counters: `requestAnimationFrame`, ≤ 600 ms, ease-out
- [ ] Copy-to-clipboard: `navigator.clipboard.writeText()` with "Copied!" feedback
- [ ] CSV download: Blob URL, includes only currently-visible rows
- [ ] Back-to-top button: appears after 300 px scroll, `scroll-behavior:smooth`
- [ ] Tooltips on truncated cells: `title` attribute at minimum

---

## 13. JavaScript & TypeScript Standards

### Language — what to embed

All JavaScript embedded inside HTML reports must be **vanilla JS** — no
framework or library imports of any kind (React, Vue, Angular, Alpine.js,
jQuery, Lodash, etc.). Every script must be self-contained and run without
any network access.

**TypeScript** is allowed as a development/authoring tool, but only its
compiled JavaScript output may be embedded in HTML. MCP projects that have
no build step must use vanilla JS directly.

```
Allowed in <script>:  ES2017+ vanilla JS (compiled from TS is fine)
Not allowed:          import statements, require(), framework runtime bundles
```

### Language features

Use modern JS idioms — all target browsers support ES2017+:

```javascript
// Good
const result = items.filter(x => x.active).map(x => x.value);
const label = `${col} (${dtype})`;
const val = obj?.nested?.key ?? "default";

// Bad — ES5 patterns are verbose and error-prone
var result = [];
for (var i = 0; i < items.length; i++) { ... }
```

| Feature | Use |
|---|---|
| `const` / `let` | Always — never `var` |
| Arrow functions | Prefer for callbacks |
| Template literals | String interpolation |
| Destructuring | For function params and return values |
| Optional chaining `?.` | Safe property access |
| Nullish coalescing `??` | Default values |
| `async`/`await` | Async operations (rare in reports) |

### IIFE module pattern

Every script block must be wrapped in an IIFE. No globals, no accidental
name collisions between independently-written script blocks.

```javascript
// Every script block
(function() {
  "use strict";
  const el = document.getElementById("my-chart");
  // ...
})();
```

### Python data → JavaScript

All data from Python must be serialized with `json.dumps()` before injection.
Never use Python's string representation of lists or dicts.

```python
import json

# Wrong — Python repr; breaks if column name has a quote
var x = {corr_x};

# Correct — valid JSON, handles all characters
var x = {json.dumps(corr_x)};
```

This applies to: column name arrays, matrix values, category lists,
node/edge data, any Python object placed in a JS variable.

### Cross-chart communication

When one control should affect multiple charts (cross-filter, theme switch,
column toggle), use `CustomEvent` on `document` rather than calling chart
functions directly. This decouples the control from the charts it affects.

```javascript
// Control fires an event
document.dispatchEvent(new CustomEvent("filter-change", {
  detail: { column: "revenue", min: 0, max: 10000 }
}));

// Chart listens
document.addEventListener("filter-change", function(e) {
  applyFilter(e.detail);
});
```

### State persistence

UI state that should survive page reload (collapsed sections, active tab,
selected theme override) must be stored in `sessionStorage`, not `localStorage`.
Reports are ephemeral; `sessionStorage` is scoped to the tab session.

```javascript
// Save
sessionStorage.setItem("section-overview-collapsed", "true");

// Restore
const collapsed = sessionStorage.getItem("section-overview-collapsed") === "true";
```

---

## 14. Interactive Controls

All controls follow progressive enhancement: the page is fully readable
with JavaScript disabled. Controls enhance the experience; they do not
gate it.

### Multi-select column / variable picker

Use when a report covers many columns (> 10) and the user may want to
focus on a subset. Standard pattern:

```html
<div class="ddw">
  <button class="ddbtn" id="col-picker-btn">Columns ▾</button>
  <div class="ddmenu hid" id="col-picker-menu">
    <input class="ddsrch" type="text" placeholder="Search…" />
    <div class="ddacts">
      <button class="btn" id="col-all">Select all</button>
      <button class="btn" id="col-none">Clear</button>
    </div>
    <!-- one .optlbl per column -->
    <label class="optlbl">
      <input type="checkbox" value="revenue" checked> revenue
    </label>
  </div>
</div>
```

Requirements:
- Search box filters the list in real time (debounce 150 ms)
- Select-all / Clear-all buttons
- Checked state persists in `sessionStorage`
- Menu closes when clicking outside (`document` click listener with `closest()`)
- Keyboard accessible: Tab to button, Enter/Space to open, Escape to close

### Numeric range filter

For filtering rows by a numeric column:

```html
<div class="nrng">
  <input class="ninp" type="number" id="min-val" placeholder="Min">
  <span class="nsep">–</span>
  <input class="ninp" type="number" id="max-val" placeholder="Max">
  <button class="btn" id="apply-range">Apply</button>
  <button class="btn" id="clear-range">Clear</button>
</div>
```

Validate: `min ≤ max`; show inline error if violated. Never silently clamp.

### Live table search

Every data table with more than 20 rows must have a search input that
filters rows in real time.

```javascript
(function() {
  "use strict";
  const input = document.getElementById("tbl-search");
  const rows = document.querySelectorAll("#data-table tbody tr");
  let timer;
  input.addEventListener("input", function() {
    clearTimeout(timer);
    timer = setTimeout(function() {
      const q = input.value.toLowerCase();
      rows.forEach(function(r) {
        r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none";
      });
    }, 150);
  });
})();
```

Debounce ≥ 150 ms. Filter applies to all visible text in the row.

### Sortable tables

Every static data table must support click-to-sort on column headers.

```javascript
(function() {
  "use strict";
  document.querySelectorAll("th[data-sort]").forEach(function(th) {
    th.style.cursor = "pointer";
    let dir = 1;
    th.addEventListener("click", function() {
      const idx = th.cellIndex;
      const tbody = th.closest("table").querySelector("tbody");
      const rows = Array.from(tbody.rows);
      rows.sort(function(a, b) {
        const av = a.cells[idx].textContent.trim();
        const bv = b.cells[idx].textContent.trim();
        return dir * (isNaN(av - bv) ? av.localeCompare(bv) : av - bv);
      });
      rows.forEach(function(r) { tbody.appendChild(r); });
      th.closest("table").querySelectorAll("th").forEach(function(t) {
        t.textContent = t.textContent.replace(/ [▲▼]$/, "");
      });
      th.textContent += dir > 0 ? " ▲" : " ▼";
      dir *= -1;
    });
  });
})();
```

Mark sortable headers with `data-sort` attribute. Numeric columns sort
numerically; others sort lexicographically.

### Chart expand modal

Every chart card in a grid report must have an expand button that opens
the chart full-size in a modal overlay.

Standard elements:
```html
<div class="modal" id="chart-modal">
  <div class="mbox">
    <div class="mhdr">
      <h3 id="modal-title"></h3>
      <button class="mclose" id="modal-close">&#x2715;</button>
    </div>
    <div id="mdiv"></div>
  </div>
</div>
```

Expand button HTML on each chart card:
```html
<button class="exp" data-chart-id="revenue-chart" data-chart-title="Revenue">⛶</button>
```

Behavior:
- Click expand → move chart div into `#mdiv` → set `#modal-title` → show modal
- ESC key or backdrop click → close modal → return chart div to original card
- Modal resize triggers `Plotly.relayout(div, {autosize: true})`

### Cross-filter

When a dashboard has multiple related charts, selecting a point or bar in
one chart should filter the data shown in others.

Use Plotly events:
```javascript
chartDiv.on("plotly_selected", function(eventData) {
  const selected = eventData ? eventData.points.map(p => p.customdata) : null;
  document.dispatchEvent(new CustomEvent("cross-filter", {
    detail: { source: "revenue-chart", keys: selected }
  }));
});
```

Always provide a visible **"Clear filter"** button that resets all charts.
Highlight filtered state in the source chart (change opacity of non-selected
points: `marker.opacity` update via `Plotly.restyle`).

### Collapsible sections

Long reports benefit from collapsible sections. Each section heading gets a
toggle, and state is persisted.

```javascript
(function() {
  "use strict";
  document.querySelectorAll(".section > h2").forEach(function(h) {
    const id = h.closest(".section").id;
    const body = h.nextElementSibling;
    if (!body) return;
    h.style.cursor = "pointer";
    const key = "collapsed-" + id;
    if (sessionStorage.getItem(key) === "1") {
      body.style.display = "none";
      h.textContent = "▶ " + h.textContent;
    } else {
      h.textContent = "▼ " + h.textContent;
    }
    h.addEventListener("click", function() {
      const hidden = body.style.display === "none";
      body.style.display = hidden ? "" : "none";
      sessionStorage.setItem(key, hidden ? "0" : "1");
      h.textContent = (hidden ? "▼ " : "▶ ") + h.textContent.slice(2);
    });
  });
})();
```

---

## 15. UX Patterns

### Scroll spy

The sidebar active link must track the currently visible section as the
user scrolls. Use `IntersectionObserver` — not `scroll` event listeners.

```javascript
(function() {
  "use strict";
  const links = document.querySelectorAll(".nav a[href^='#']");
  const sections = Array.from(document.querySelectorAll(".section[id]"));
  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        links.forEach(function(l) { l.classList.remove("active"); });
        const match = document.querySelector('.nav a[href="#' + entry.target.id + '"]');
        if (match) match.classList.add("active");
      }
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  sections.forEach(function(s) { observer.observe(s); });
})();
```

### Sticky section headings

Section headings in long reports should stick at the top of the viewport
while their section is visible. Add to CSS:

```css
.section > h2 {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg);
  padding-top: 0.5rem;
}
```

Only apply to reports without a fixed sidebar that already anchors
navigation (use with EDA/profile layouts; not needed in dashboard layout).

### Animated KPI counters

Numeric KPI cards animate from 0 to their final value on page load.
Duration 600 ms, ease-out. Skip animation if `prefers-reduced-motion`.

```javascript
(function() {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion:reduce)").matches) return;
  document.querySelectorAll(".card .num[data-val]").forEach(function(el) {
    const target = parseFloat(el.dataset.val);
    if (isNaN(target)) return;
    const fmt = el.dataset.fmt || "int";  // "int" | "float2" | "pct"
    const start = performance.now();
    const dur = 600;
    function step(now) {
      const t = Math.min((now - start) / dur, 1);
      const ease = 1 - Math.pow(1 - t, 3);  // ease-out cubic
      const v = target * ease;
      el.textContent = fmt === "float2" ? v.toFixed(2)
                      : fmt === "pct"    ? v.toFixed(1) + "%"
                                        : Math.round(v).toLocaleString();
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
})();
```

Mark cards with `data-val="{number}"` and `data-fmt="int|float2|pct"`.

### Copy to clipboard

File paths, column names, and code block values should be copyable with
a single click. Visual feedback: "Copied!" replaces the button label for
1.5 s then reverts.

```javascript
(function() {
  "use strict";
  document.querySelectorAll("[data-copy]").forEach(function(btn) {
    btn.addEventListener("click", function() {
      const text = btn.dataset.copy;
      navigator.clipboard.writeText(text).then(function() {
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(function() { btn.textContent = orig; }, 1500);
      });
    });
  });
})();
```

Add a small copy icon button `<button class="btn" data-copy="{path}">⧉</button>`
next to file paths in report headers and code blocks.

### Download filtered table as CSV

Every filterable data table must offer a "Download CSV" button that exports
only the currently visible rows.

```javascript
(function() {
  "use strict";
  const btn = document.getElementById("dl-csv");
  if (!btn) return;
  btn.addEventListener("click", function() {
    const tbl = document.getElementById("data-table");
    const headers = Array.from(tbl.querySelectorAll("th"))
      .map(th => JSON.stringify(th.textContent.trim()));
    const visibleRows = Array.from(tbl.querySelectorAll("tbody tr"))
      .filter(r => r.style.display !== "none");
    const rows = visibleRows.map(function(r) {
      return Array.from(r.cells).map(td => JSON.stringify(td.textContent.trim())).join(",");
    });
    const csv = [headers.join(","), ...rows].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = "export.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  });
})();
```

### Back-to-top button

Appears after the user scrolls 300 px. Smoothly returns to top.

```html
<button id="back-top" aria-label="Back to top"
  style="display:none;position:fixed;bottom:1.5rem;right:1.5rem;z-index:300;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-md);padding:.5rem .75rem;cursor:pointer;
  color:var(--accent);font-size:1rem;box-shadow:0 2px 8px rgba(0,0,0,.2)">▲</button>
```

```javascript
(function() {
  "use strict";
  const btn = document.getElementById("back-top");
  if (!btn) return;
  window.addEventListener("scroll", function() {
    btn.style.display = window.scrollY > 300 ? "" : "none";
  }, { passive: true });
  btn.addEventListener("click", function() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();
```

### Tooltip on truncated cells

Add `title` attribute to any cell where `text-overflow:ellipsis` may clip
content. For cells generated from data:

```python
f'<td title="{html.escape(full_value)}">{html.escape(display_value[:40])}</td>'
```

For dynamic truncation, use a `ResizeObserver` to detect when text overflows
and add/remove `title` accordingly.

### Print button

Every multi-section report should have a print button in the header area.
Works with the existing `@media print` stylesheet.

```html
<button class="btn" onclick="window.print()">🖨 Print</button>
```

Exception to the no-inline-handler rule: `window.print()` is the only
acceptable inline `onclick` because it has no side-effects and no injection
risk.
