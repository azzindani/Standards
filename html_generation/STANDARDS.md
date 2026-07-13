# HTML Generation Standards

> Rules for programs that emit standalone HTML files — charts, dashboards, EDA and profiling reports — so every output opens offline, renders instantly, and is safe to hand to a browser.

**ID** `html_generation` · **Tier** Domain · **Version** 1.0
**Owns** offline-first HTML output · asset inlining · output path resolution · generator module structure · standard function contracts · document skeleton · output-specific security
**Defers to** theme system · CSS architecture · UX patterns → [THEMING.md](THEMING.md) · chart integration · dashboards · interactive controls → [CHARTS.md](CHARTS.md) · generic input validation · secrets · injection classes → [security](../security/STANDARDS.md) · error taxonomy · boundaries → [error_handling](../error_handling/STANDARDS.md) · logging · metrics → [observability](../observability/STANDARDS.md) · file/module naming → [directory](../directory/STANDARDS.md) · language idiom → [python](../python/STANDARDS.md) | [typescript](../typescript/STANDARDS.md)
**Load with** [THEMING.md](THEMING.md) · [CHARTS.md](CHARTS.md) · [security](../security/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Offline-First Rules](#2-offline-first-rules)
3. [Tool Surface Contract](#3-tool-surface-contract)
4. [Output Path](#4-output-path)
5. [Module Structure](#5-module-structure)
6. [Standard Functions](#6-standard-functions)
7. [Document Structure](#7-document-structure)
8. [Output Security](#8-output-security)
9. [Cross-Platform](#9-cross-platform)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Principles

Generated HTML is an **artifact**, not a service. It is written once, copied anywhere, opened at any time — on a laptop with no network, on a phone, from an email attachment, five years later.

| Principle | Rule |
|---|---|
| Self-contained | One `.html` file. Zero sidecar assets. Zero network requests at render time |
| Deterministic | Same data + same theme → byte-comparable output ; embedded timestamps |
| Render-on-open | No build step, no server, no `file://` CORS dependency |
| Consistent | Every generator in a project emits the same theme, layout, and control vocabulary |
| Escaped by default | All data reaching the DOM is untrusted until escaped (§8) |
| Progressive | Page is fully readable with JavaScript disabled — JS enhances, ✗ gates |

Consumer is often an LLM tool call with limited context: output must be one path, one file, immediately viewable.

---

## 2. Offline-First Rules

**! The central constraint: no CDN, ever.** Generators run locally, offline, air-gapped. A remote reference is a broken report.

| Asset | Rule |
|---|---|
| Chart library (Plotly et al.) | Inlined into the document — see [CHARTS.md](CHARTS.md) §1 |
| Scripts | Inline `<script>` only. ✗ `<script src="http…">` · ✗ `import` · ✗ `require()` |
| Stylesheets | Inline `<style>` only. ✗ `<link rel="stylesheet" href="http…">` · ✗ `@import url(…)` |
| Fonts | System font stack only (§9). ✗ webfont download · ✗ Google Fonts |
| Icons | Unicode glyphs or inline SVG. ✗ icon-font CDN · ✗ remote sprite sheet |
| Images | Inline `data:` URI. ✗ remote `src` |
| Source maps | ✗ emitted — they reference files that will not travel with the HTML |

Hard bans, enforced by grep in CI:

- ✗ any `https://` or `http://` in a `src`, `href`, or `@import` of generated HTML ; anchor links intended for human clicking.
- ✗ a `PLOTLY_CDN`-style constant anywhere in the codebase — its **existence** is the violation, use is not required.
- ✗ `fetch()` · `XMLHttpRequest` · `WebSocket` · `navigator.sendBeacon` in emitted JS.
- ✗ external form `action` targets.

### Verification

| Check | Rule |
|---|---|
| Grep gate | CI greps generated fixtures for `http://` · `https://` · `cdn.` · `@import` → any hit fails the build |
| Offline render test | Open a generated fixture with the network disabled; page must render fully — see [testing](../testing/STANDARDS.md) |
| Single-file assertion | Generator writes exactly one file per output; ✗ companion `.css` · `.js` · `.json` |

---

## 3. Tool Surface Contract

Every function or tool that produces an HTML file exposes the same surface.

| Parameter | Type | Default | Rule |
|---|---|---|---|
| `theme` | `"dark"` \| `"light"` \| `"device"` | `"dark"` | Dark is the default for every project. Reject unknown values — ✗ silently fall back |
| `open_after` | bool | `true` | Open in the system viewer after write. Best-effort (§9) |
| `output_path` | path \| empty | empty | Empty → resolve per §4 |
| `title` | string | required | Rendered into `<title>` and page header, escaped |

Return payload must include, at minimum:

| Key | Value |
|---|---|
| `output_path` | Absolute, resolved path string |
| `filename` | Basename only |

✗ return a relative path. ✗ return only a success flag — the caller cannot find the file.

---

## 4. Output Path

### Resolution order

1. Explicit `output_path` argument, if provided and non-empty → resolve to absolute, use it.
2. `~/Downloads/<stem>_<descriptor>.html`, if `~/Downloads` exists and is a directory.
3. Directory of the input file.

Resolution is total — it always yields a path. ✗ raise on step 2 miss ; fall through to step 3.

### Rules

| Rule | Detail |
|---|---|
| Always absolute | Explicit paths pass through path-resolution before use and before return |
| Path objects | Construct with a path library. ✗ string concatenation · ✗ hardcoded `/` or `\` |
| Naming | `{input_stem}_{descriptor}.html` — e.g. `sales_dashboard.html` · `sales_eda.html` · `sales_correlation.html` |
| Descriptor is fixed vocabulary | One descriptor per report type across the project; ✗ freeform names |
| Atomic write | Write to temp file in the destination directory → `fsync` → atomic rename onto the final path |
| Encoding | `utf-8` explicit on every write. ✗ platform default |
| Overwrite | Same inputs overwrite the same path silently — outputs are regenerable, not precious |

Partial output is never visible: a reader either sees the previous complete file or the new complete file.

---

## 5. Module Structure

Every project emitting HTML has exactly two shared generator modules. Names are conventions; the **split** is the rule.

| Module | Owns |
|---|---|
| `html_layout` | Output-path resolution · viewport meta constant · CSS string blocks · CSS assemblers · chart-library config constant · base layout dict |
| `html_theme` | Theme registry · color/spatial token strings · `:root{}` assembler · device-mode JS · sidebar JS · figure theming · chart height calculator · report builders · table/card renderers · viewer launch |

Split rule: **`html_layout` produces strings that do not know the theme; `html_theme` chooses the theme and calls into `html_layout`.** Dependency is one-directional: `html_theme` → `html_layout`. ✗ reverse import.

### Single-definition rules

| Symbol | Rule |
|---|---|
| Viewport meta | Defined once in `html_layout`; imported everywhere. ✗ redefine |
| Chart config dict | Defined once; ✗ inline literal config at call sites |
| Color + spatial tokens | Defined once in `html_theme`; ✗ literal hex or `rem` values in engine code |
| Chart height constants | Defined once in the height calculator; ✗ magic numbers in engine code |

### Must not exist

- ✗ CDN URL constant of any kind, used or unused.
- ✗ Hardcoded pixel `height` inside the base layout or figure-theming helpers — CSS owns height ([CHARTS.md](CHARTS.md) §3).
- ✗ Per-report bespoke CSS copies — a new report composes existing CSS blocks or adds one to `html_layout`.
- ✗ HTML string assembly inside engine/analysis code — engines return data, renderers return HTML. See [architecture](../architecture/STANDARDS.md).

---

## 6. Standard Functions

These contracts are identical across projects. Implementation may vary; signature, inputs, and return shape may not.

| Function | Input | Returns | Contract |
|---|---|---|---|
| `get_output_path` | explicit path · input path · descriptor · extension | absolute path | §4 resolution order. Always resolved |
| `css_vars` | theme | `:root{}` CSS block | Includes the `prefers-color-scheme` media query when theme is `device` |
| `get_theme` | theme | theme config | Rejects unknown theme names |
| `apply_fig_theme` | figure · theme | none (mutates) | Sets paper/plot background, font color, template, autosize. ✗ set height |
| `calc_chart_height` | count · mode · extra base | integer px | Clamped `[280, 1800]`. Modes: subplot · bar · heatmap · fixed |
| `plotly_div` | figure · theme | HTML `<div>` string | Chart library **not** re-embedded; theming applied first |
| `save_chart` | figure · path · theme · open flag · title | (absolute path, filename) | Full standalone page; chart library inlined |
| `build_html_report` | title · subtitle · sections · theme · open flag · path | HTML string | Sidebar nav · hamburger · device JS · print CSS. Writes file when path given |
| `metrics_cards_html` | metrics mapping | HTML string | Card grid. Keys and values escaped |
| `data_table_html` | rows · max rows | HTML string | Scroll-wrapped table. Appends "N more rows" footer when truncated |
| `open_file` | path | none | Best-effort viewer launch. ✗ raise — log to stderr and continue |

Section input to `build_html_report` is an ordered list of records with `id` · `heading` · `html`. The `id` is the sidebar anchor target (§7).

---

## 7. Document Structure

Fixed head order for every generated page:

| Order | Element | Rule |
|---|---|---|
| 1 | Doctype | `<!DOCTYPE html>` — first line, always |
| 2 | Root element | `<html lang="en">` — `lang` required |
| 3 | Charset meta | `utf-8` — first element inside `<head>` |
| 4 | Viewport meta | From the shared constant — `width=device-width,initial-scale=1` |
| 5 | Title | Escaped page title |
| 6 | Style | One inline `<style>`: token block → CSS blocks, in the order fixed by [THEMING.md](THEMING.md) §6 |
| 7 | Body | Page content |
| 8 | Scripts | Inline `<script>` blocks at end of body — device-mode JS if theme is `device`, sidebar JS if a sidebar exists, feature JS last |

### Report body structure

| Rule | Detail |
|---|---|
| Section wrapper | Every major section is a container carrying a stable `id` |
| Sidebar linkage | Sidebar anchor href matches the section `id` exactly — mismatch = dead in-page link |
| Heading level | One `h1` per page (report title); sections use `h2`; subsections `h3` |
| Section ids are slugs | Lowercase, hyphenated, derived from heading; stable across runs |
| Empty section | Rendered with an explicit "no data" placeholder. ✗ omit silently — the sidebar link would break |

Scripts run after the DOM they reference exists. ✗ rely on `defer` for inline scripts placed in `<head>`.

---

## 8. Output Security

Generated HTML is an untrusted-data rendering surface: column names, cell values, file paths, and error strings all originate outside the generator. Generic injection theory, secret handling, and threat classes → [security](../security/STANDARDS.md). What follows is output-specific and binding.

### Escaping

| Rule | Detail |
|---|---|
| Escape at injection point | Every interpolated value is HTML-escaped immediately before it enters the string — ✗ "escaped upstream" assumptions |
| Escape everything from data | Column names · cell values · file names · paths · error messages · titles · units |
| Attribute context | Values inside attributes are escaped **and** quoted. ✗ unquoted attribute values |
| Never raw | ✗ interpolate a data value into markup without escaping, even when "known" numeric — types lie |
| Escape once | Double-escaping corrupts display; escape at the boundary, ✗ again downstream |

### Script rules

| Rule | Detail |
|---|---|
| ✗ `eval()` · ✗ `new Function(string)` | All JS is authored at generation time and static |
| ✗ inline event attributes | `onclick` · `onload` · `onerror` etc. → `addEventListener` in an inline `<script>` ; single exception below |
| ✗ `innerHTML` with data | Data → `textContent`. `innerHTML` only with generator-authored, data-free markup |
| Data → JS | Serialize as JSON. ✗ language-native repr of lists/dicts — it breaks on quotes, NaN, and non-ASCII |
| JSON in script | Values embedding `</script>` must be escaped so the tag cannot terminate the block early |

**Inline-handler exception (only one):** `window.print()` on a print button — no arguments, no data, no injection surface. Every other inline handler is a defect.

### Content-Security-Policy

Emit a restrictive CSP meta tag on every page. Because everything is inlined, the policy is inline-only and network-free.

| Directive | Required value | Reason |
|---|---|---|
| `default-src` | `'none'` | Nothing loads by default |
| `script-src` | `'unsafe-inline'` | Inline scripts only — no host source is ever allowed |
| `style-src` | `'unsafe-inline'` | Inline styles only |
| `img-src` | `'self' data:` | Inline data URIs only |
| `connect-src` | `'none'` | ! Kills every runtime fetch — enforces §2 at the browser |
| `font-src` | `'none'` | System fonts need no source |
| `frame-src` · `object-src` | `'none'` | No embedded documents or plugins |

`connect-src 'none'` is the mechanical guarantee behind the offline-first rule: even a smuggled `fetch()` cannot leave the page.

---

## 9. Cross-Platform

### Font stacks

| Use | Stack |
|---|---|
| Body / UI | `'Segoe UI', system-ui, -apple-system, sans-serif` |
| Monospace | `'Cascadia Code', 'Fira Mono', monospace` |

Every entry is either OS-supplied or a generic family. Degradation is graceful on any OS. ✗ add a family that requires download.

### Viewer launch

| Platform | Mechanism |
|---|---|
| Windows | OS shell open |
| macOS | `open` |
| Linux / BSD | `xdg-open` |
| Headless / no viewer | Skip silently; path is already in the return payload |

Launch is best-effort: wrap it, never let it raise, log the failure to stderr. A failed browser launch ✗ fail the tool — the file is written and its path returned.

### Paths and text

| Rule | Detail |
|---|---|
| Separators | Path library only. `resolve()` yields OS-native separators |
| Encoding | `utf-8` on read and write, explicit, everywhere |
| Newlines | Written as `\n`; ✗ platform-dependent newline translation in HTML output |
| Long values | Non-ASCII column names and paths must survive round-trip — test with them |

---

## 10. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| CDN "just for the chart library" | Report is blank offline | Inline the library ([CHARTS.md](CHARTS.md) §1) |
| Unused CDN constant "for later" | Copy-paste reintroduces it | Delete the constant; CI greps for it |
| Webfont `@import` | Silent network call, FOUT, offline failure | System font stack (§9) |
| Sidecar `report.css` | File emailed alone renders unstyled | Single-file output (§2) |
| Relative `output_path` returned | Caller cannot locate the file | Resolve before returning (§4) |
| Direct write to the final path | Reader sees a half-written page | Temp file → atomic rename (§4) |
| f-string interpolation of a column name | XSS from a CSV header | Escape at the injection point (§8) |
| `innerHTML = userValue` | Same, via JS | `textContent` (§8) |
| Language-native repr into JS | Breaks on `'`, `None`, `NaN` | JSON serialization (§8) |
| Height set in both layout dict and CSS | Charts clip or double-scroll | CSS owns height ([CHARTS.md](CHARTS.md) §3) |
| Hex colors in engine code | Theme switch misses them | Token references only ([THEMING.md](THEMING.md) §2) |
| Browser launch raises | Tool fails after writing a valid file | Best-effort launch (§9) |

---

## 11. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Report types | 1–2, one module | 3–10, shared `html_layout` + `html_theme` | >10, versioned generator package |
| Offline enforcement | Manual review | CI grep gate for `http` · `cdn.` · `@import` | Grep gate + network-disabled render test on fixtures |
| Escaping | Escape helper used by convention | Escape helper mandatory; review rejects raw interpolation | Escaping enforced by renderer API — raw string injection impossible |
| CSP | Optional | Meta tag with `connect-src 'none'` on every page | CSP + automated fixture assertion on every directive |
| Output size | Unbounded | ≤5 MB per report; row-truncate tables beyond the cap | ≤5 MB + explicit row/chart budgets per section |
| Theme support | `dark` only | `dark` · `light` · `device` | All three + per-project brand token override |
| Regression testing | Open and eyeball | Golden-file diff on generated HTML | Golden-file diff + DOM assertions + offline render test |

---

## 12. Checklist

- [ ] Zero `http://` or `https://` in `src`, `href`, or `@import` of generated HTML
- [ ] No CDN URL constant exists anywhere in the codebase, used or unused
- [ ] No `fetch`, `XMLHttpRequest`, `WebSocket`, or `sendBeacon` in emitted JS
- [ ] Chart library, CSS, and JS are inlined; output is exactly one file
- [ ] Generated fixture renders fully with the network disabled
- [ ] `theme` accepts `dark` | `light` | `device`, defaults to `dark`, rejects unknown values
- [ ] `open_after` parameter present and defaults to true
- [ ] Return payload contains absolute `output_path` and `filename`
- [ ] Output path follows explicit → `~/Downloads` → input directory order
- [ ] Writes are atomic (temp file → rename) with explicit `utf-8` encoding
- [ ] Viewport meta, chart config, tokens, and height constants each defined exactly once
- [ ] `html_theme` imports `html_layout`; no reverse import
- [ ] No hardcoded chart height in layout dict or figure-theming helper
- [ ] Doctype, `<html lang="en">`, charset meta, viewport meta present in fixed order
- [ ] Every report section has a stable `id` matching its sidebar anchor
- [ ] Every data-derived value is HTML-escaped at its injection point
- [ ] Attribute-context values are escaped and quoted
- [ ] No `eval()`, no `new Function()`, no `innerHTML` with data
- [ ] No inline event handlers ; the single `window.print()` exception
- [ ] Python/host data reaches JS as JSON, never as native repr
- [ ] CSP meta tag present with `default-src 'none'` and `connect-src 'none'`
- [ ] Font stacks are system-only; no downloadable font referenced
- [ ] Viewer launch is best-effort and never raises
- [ ] Paths built with a path library, never string concatenation
