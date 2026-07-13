# HTML Theming Standards

> Theme tokens, CSS architecture, responsive layout, and UX patterns for generated HTML reports and dashboards.

**ID** `html_generation/theming` · **Tier** Domain · **Version** 1.0
**Owns** theme model · color + spatial tokens · device-mode switching · CSS layer order · units · responsive breakpoints · z-index scale · print + motion rules · report UX patterns
**Defers to** offline-first · asset inlining · document skeleton · escaping · CSP → [STANDARDS.md](STANDARDS.md) · figure theming · chart containers · interactive controls → [CHARTS.md](CHARTS.md) · browser routing · app state · auth → [web](../web/STANDARDS.md) · rendering budgets → [performance](../performance/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [CHARTS.md](CHARTS.md)

---

## Table of Contents

1. [Theme Model](#1-theme-model)
2. [Color Tokens](#2-color-tokens)
3. [Spatial Tokens](#3-spatial-tokens)
4. [Device Mode](#4-device-mode)
5. [Units](#5-units)
6. [CSS Layer Order](#6-css-layer-order)
7. [Layout](#7-layout)
8. [Responsive Rules](#8-responsive-rules)
9. [Z-Index Scale](#9-z-index-scale)
10. [Motion, Print, Scrollbar](#10-motion-print-scrollbar)
11. [UX Patterns](#11-ux-patterns)
12. [Accessibility](#12-accessibility)
13. [Anti-Patterns](#13-anti-patterns)
14. [Checklist](#14-checklist)

---

## 1. Theme Model

Three themes. No fourth. Dark is the default for every project.

| Theme | Chart template | Page background | Selection |
|---|---|---|---|
| `dark` | dark template | `--bg` = `#0d1117` | Default — used unless caller asks otherwise |
| `light` | light template | `--bg` = `#ffffff` | Caller opt-in |
| `device` | starts light, JS-switched | Follows OS preference | Caller opt-in; page tracks system preference live |

Rules:

| Rule | Detail |
|---|---|
| Single source | Theme values live in one theme registry module; ✗ literal hex anywhere else |
| Token indirection | Every color used by CSS or a chart resolves from a token, never from a literal |
| Unknown theme | Reject with an error. ✗ silently fall back to dark |
| Same tokens both themes | Dark and light define the **identical** token set — only values differ. A token missing from one theme is a defect |
| Charts follow page | Figure background matches the surface it sits on — see [CHARTS.md](CHARTS.md) §2 |

---

## 2. Color Tokens

Nine tokens. Every project defines exactly these, in both themes.

| Token | Meaning | Dark value | Light value |
|---|---|---|---|
| `--bg` | Page background | `#0d1117` | `#ffffff` |
| `--surface` | Cards · sidebar · chart background | `#161b22` | `#f6f8fa` |
| `--border` | Borders · dividers · scrollbar thumb | `#21262d` | `#d0d7de` |
| `--text` | Body text | `#c9d1d9` | `#1f2328` |
| `--text-muted` | Labels · metadata · axis ticks | `#8b949e` | `#636c76` |
| `--accent` | Headings · links · active states · focus ring | `#58a6ff` | `#0969da` |
| `--green` | Success · good values | `#3fb950` | `#1a7f37` |
| `--orange` | Warning values | `#f0883e` | `#9a6700` |
| `--red` | Errors · bad values | `#f85149` | `#cf222e` |

Rules:

| Rule | Detail |
|---|---|
| Semantic naming | Tokens name a **role**, ✗ a color. `--red`/`--green`/`--orange` are the only value-named tokens and are reserved for status semantics |
| Chart backgrounds | Figures embedded in a card use `--surface`, ✗ `--bg` — mismatch shows as a rectangle seam |
| Status colors | Red/green/orange never carry meaning alone — pair with text, icon, or sign (§12) |
| Extension | A project needing more colors extends the token set in the theme registry for **both** themes; ✗ one-off hex at a call site |
| Contrast | Every text token on its intended background meets WCAG AA (§12) |

---

## 3. Spatial Tokens

Layout dimensions are theme-independent — one block, merged with the color block into `:root{}`. All values in `rem`.

| Token | Value | Meaning |
|---|---|---|
| `--sidebar-w` | `16.25rem` | Sidebar width, desktop |
| `--sidebar-w-md` | `13.75rem` | Sidebar width, tablet |
| `--main-pad` | `2rem` | Main content padding, desktop |
| `--main-pad-sm` | `1rem` | Main content padding, mobile |
| `--section-gap` | `3rem` | Vertical gap between report sections |
| `--card-gap` | `0.75rem` | Gap inside card grids |
| `--card-min` | `8rem` | Minimum card width in the auto-fill grid |
| `--card-pad` | `1rem` | Card internal padding |
| `--radius-sm` | `0.375rem` | Small radius — inputs, scrollbar thumb |
| `--radius-md` | `0.625rem` | Medium radius — buttons, cards |
| `--radius-lg` | `0.75rem` | Large radius — panels, modals |
| `--chart-radius` | `0.75rem` | Chart container radius |
| `--font-xs` | `0.6875rem` | Micro labels |
| `--font-sm` | `0.8125rem` | Table text · captions |
| `--font-base` | `1rem` | Body |
| `--font-lg` | `1.125rem` | Subheadings |
| `--font-xl` | `1.25rem` | Section headings |
| `--font-2xl` | `clamp(1.125rem, 2vw, 1.5rem)` | Page title — fluid |

Rules:

- Root font size is `16px`. Every `rem` resolves against it — this is the one place a pixel value appears.
- ✗ literal spacing or font sizes in component CSS — token references only.
- A new dimension used in more than one place becomes a token; used once, it stays inline.

---

## 4. Device Mode

When `theme` is `device`, the page emits light tokens plus a dark override under the `prefers-color-scheme: dark` media query, **and** a switcher script — CSS alone cannot retheme charts.

Switcher contract, in order:

1. Read the OS dark-mode media query on load.
2. Set a `data-theme` attribute of `dark` | `light` on the root element.
3. Relayout every chart container with the matching template, paper background, and plot background.
4. Register a `change` listener on the media query; repeat steps 2–3 on every change.

| Rule | Detail |
|---|---|
| CSS + JS both required | Media query retints CSS; script retints charts. Either alone leaves a half-themed page |
| Attribute-driven | Components that must override the media query key off `data-theme` on the root element |
| No flash | Light tokens are the base; dark override is a media query in the same inline `<style>` — ✗ post-load class swap that repaints |
| Static themes | `dark` and `light` emit their token block only — ✗ ship the switcher script |
| Live update | System preference change retints the page without reload |

---

## 5. Units

| Use | Unit |
|---|---|
| Spacing · padding · margin · gap | `rem` (via token) |
| Typography | `rem` (via token) |
| Fluid headings · card numbers · chart heights | `clamp()` |
| Border radius | `rem` (via token) |
| Media query thresholds | `rem` or `em` |
| Borders | `1px` — the **only** permitted pixel value |
| Root font size | `16px` — the second and last permitted pixel value |

✗ `px` for layout or typography — it ignores the user's font-size setting and breaks accessibility zoom.
✗ `px` in media queries — breakpoints must scale with user font settings.
✗ viewport units alone for text — always inside `clamp()` with a `rem` floor and ceiling.

---

## 6. CSS Layer Order

Inline `<style>` blocks are concatenated in this fixed order. Order is the cascade contract — reordering changes rendering.

| Order | Layer | Content |
|---|---|---|
| 1 | Tokens | `:root{}` — color block + spatial block ; device media query |
| 2 | Reset + base | Box sizing, margin/padding zeroing, wrapping defaults, root font size, smooth scroll |
| 3 | Scrollbar | Custom scrollbar styling |
| 4 | Typography | `h1`–`h3`, muted text, code, helper classes |
| 5 | Components | Cards · tables · chart containers · alerts · badges · buttons · dropdowns · modals |
| 6 | Layout | Sidebar · main · header · section · grid |
| 7 | Responsive | Tablet → mobile → small mobile, in that order |
| 8 | Print | `@media print` overrides |

Required base rules:

| Rule | Applies to |
|---|---|
| Border-box sizing, zero default margin and padding | Universal selector |
| `overflow-wrap: break-word` · `word-break: break-word` | Universal selector — prevents blowout from long values |
| `word-break: normal` · `overflow-x: auto` | `code` · `pre` · `kbd` · `samp` — restores their normal wrapping |
| `scroll-behavior: smooth` · `font-size: 16px` | Root element |

Text blowout is the single most common visual defect: user data (column names, file paths, category labels) is arbitrarily long. Wrapping is on by default and opted **out** of, never in.

Card numbers that must not wrap use nowrap + hidden overflow + ellipsis, paired with a `title` attribute carrying the full value (§11).

---

## 7. Layout

### Grids

| Rule | Detail |
|---|---|
| Auto-fill grids | Chart and card grids use CSS Grid `auto-fill` + `minmax()`. ✗ fixed column counts |
| Minimum track | `minmax(min(100%, clamp(18rem, 42vw, 34rem)), 1fr)` for chart grids; `--card-min` floor for card grids |
| Fluid gap | `clamp()` between `0.5rem` and `0.875rem` |
| Overflow guard | ! `min-width: 0` on every direct grid and flex child — without it, content forces the track wider and the page scrolls sideways |

### Tables

| Rule | Detail |
|---|---|
| Scroll wrapper | Every table is wrapped in a container with `overflow-x: auto` and touch scrolling. ✗ let a table bleed off-screen |
| Table min width | `30rem` — narrower tables become unreadable when crushed |
| Header cells | `white-space: nowrap` |
| Body cells | `max-width: 20rem` + `overflow-wrap: break-word` |
| Truncated cells | Carry a `title` attribute with the full value (§11) |

### Sidebar

| Rule | Detail |
|---|---|
| Desktop | Fixed sidebar at `--sidebar-w`; main content offset by the same |
| Tablet | Narrows to `--sidebar-w-md` |
| Mobile | ! Slides off-canvas — ✗ `display: none`. A hidden-with-no-affordance sidebar is a lost navigation |
| Toggle | Hamburger button, always reachable, with an accessible label |
| Backdrop | Overlay behind the open sidebar; click on it closes the sidebar |
| Close paths | Hamburger · backdrop click · `Escape` · anchor click all close it |
| Transform | Off-canvas via `transform: translateX(-100%)` → `translateX(0)` on open |

### Chart containers

Height is a CSS concern only — the figure never carries a height ([CHARTS.md](CHARTS.md) §3).

| Container class | Height |
|---|---|
| Default | `clamp(18rem, 40vh, 30rem)` |
| Heatmap / matrix | `clamp(22rem, 50vh, 38rem)` |
| Compact | `clamp(14rem, 30vh, 22rem)` |
| Network / graph | `clamp(20rem, 45vh, 34rem)` |

Cap every chart at `80vh`. Taller charts turn a report into an infinite scroll.

---

## 8. Responsive Rules

| Breakpoint | Max width | Behavior |
|---|---|---|
| Tablet | `68.75rem` | Sidebar narrows to `--sidebar-w-md`; main padding unchanged |
| Mobile | `48rem` | Sidebar goes off-canvas; hamburger appears; layout collapses to one column; padding → `--main-pad-sm` |
| Small mobile | `30rem` | Card grid collapses to a single column; font scale drops one step |

Rules:

- Breakpoints are declared in `rem` — ✗ `px` (§5).
- Mobile-first is ✗ required, but the mobile path must be **tested**, not assumed.
- Every interactive target is ≥ `2.75rem` in its smallest dimension on touch layouts.
- Horizontal page scroll at any breakpoint is a defect — the page scrolls vertically; wide content scrolls inside its own container.

---

## 9. Z-Index Scale

Five layers. A z-index outside this table is a defect.

| Layer | Value | Element |
|---|---|---|
| Backdrop / overlay | `90` | Sidebar overlay |
| Sidebar | `100` | Off-canvas navigation |
| Dropdowns · tooltips | `200` | Menus, popovers |
| Sticky affordances | `200` | Mobile sidebar toggle |
| Floating actions | `300` | Back-to-top button |
| Modals | `1000` | Chart expand modal, dialogs |

Sticky section headings sit at `10` — below every layer above, above page content.

---

## 10. Motion, Print, Scrollbar

### Motion

| Rule | Detail |
|---|---|
| Transition duration | ≤ `0.2s` for any UI transition — background, color, transform. Longer feels slow |
| Animation duration | ≤ `600ms` for content animation (counters, reveals) |
| Easing | Ease-out for entrances; linear for progress |
| Reduced motion | ! Under `prefers-reduced-motion: reduce`, skip all animation and jump to the final state. Applies to counters, smooth scroll, and transitions |
| ✗ Infinite animation | No spinners, pulses, or marquees in a static report |

### Print

Every multi-section report carries a print stylesheet:

| Rule | Detail |
|---|---|
| Hide chrome | Sidebar · hamburger · overlay · floating buttons · interactive controls hidden |
| Reset offsets | Main content margin and padding zeroed |
| Avoid breaks | Chart containers and sections use `break-inside: avoid` |
| Chart borders | Charts get a visible border — background colors do not print by default |
| Expand collapsed | Collapsed sections expand for print — ✗ print an accordion shut |

### Scrollbar

| Rule | Detail |
|---|---|
| Width | `0.375rem` |
| Track | `--bg` |
| Thumb | `--border`, radius `--radius-sm` |
| Native fallback | Styling is progressive — unsupported browsers get the native scrollbar. ✗ hide the scrollbar entirely |

---

## 11. UX Patterns

Each pattern is required when its trigger condition is met.

| Pattern | Trigger | Contract |
|---|---|---|
| Scroll spy | Report has a sidebar | Sidebar active link tracks the visible section via an intersection observer, ✗ scroll-event listeners. Observer margins bias toward the section occupying the upper viewport |
| Sticky section heading | Long report **without** a fixed sidebar | Section heading sticks to the top while its section is in view; background = `--bg`; z-index `10` |
| Animated KPI counter | Numeric KPI card | Counts from 0 to the final value over ≤ `600ms`, ease-out. Format declared per card: integer · fixed-2 · percent. Skipped entirely under reduced-motion — final value rendered immediately |
| Copy to clipboard | File path · column name · code value | Button copies the value; label swaps to a "Copied!" confirmation for `1.5s`, then reverts. Failure path leaves the original label and does not raise |
| CSV download | Any filterable table | Exports **only currently visible rows**, in current sort order, with header row. Generated as an in-page blob — ✗ network round trip. Values quoted; embedded quotes escaped |
| Back-to-top | Page scrolls past `300px` | Fixed button appears; click scrolls to top smoothly (instantly under reduced-motion); z-index `300`; accessible label |
| Truncation tooltip | Any cell that can clip | `title` attribute carries the full untruncated value — minimum viable affordance. Escaped like any other data value |
| Print button | Multi-section report | Triggers the browser print dialog. The single permitted inline handler ([STANDARDS.md](STANDARDS.md) §8) |
| Empty state | Section with no data | Explicit placeholder text naming what is missing and why. ✗ blank section · ✗ omitted section (breaks the sidebar anchor) |

Rules across all patterns:

- Every pattern degrades: with JS disabled the content is still readable, the table still renders, the sidebar links still jump.
- State that survives a reload (collapsed sections, active tab, filter selections) is stored in the tab-scoped session store — ✗ persistent local storage. Reports are ephemeral.
- ✗ pattern that hides data by default. Collapsing, filtering, and truncating are user-initiated ; explicit "N more rows" affordances.

---

## 12. Accessibility

| Rule | Detail |
|---|---|
| Contrast | Body text ≥ 4.5:1 against its background; large text and UI borders ≥ 3:1 |
| Color is never alone | Status is carried by text, sign, or icon in addition to `--red`/`--green`/`--orange` |
| Focus visible | Every interactive element shows a focus ring in `--accent`. ✗ `outline: none` without a replacement |
| Keyboard | Every control reachable by Tab, activated by Enter/Space, dismissed by Escape |
| Landmarks | Sidebar is a navigation landmark; main content is a main landmark |
| Labels | Icon-only buttons (hamburger, back-to-top, expand, copy) carry accessible labels |
| Heading order | Sequential — ✗ skip levels for visual size; use tokens for size |
| Reduced motion | Honored for every animation and smooth scroll (§10) |
| Chart fallback | Every chart is accompanied by the table or summary it visualizes, or by a text caption stating its finding |

---

## 13. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| `padding: 16px` | Ignores user font scaling | Token in `rem` (§3) |
| Media query in `px` | Breakpoint misfires at non-default font sizes | `rem`/`em` breakpoints (§8) |
| Sidebar `display: none` on mobile | Navigation silently disappears | Off-canvas + hamburger (§7) |
| Missing `min-width: 0` on grid child | Whole page scrolls sideways | Set it on every flex/grid child (§7) |
| Chart height in both CSS and figure | Clipping and double scrollbars | CSS owns height ([CHARTS.md](CHARTS.md) §3) |
| Unwrapped wide table | Table bleeds off-screen on mobile | Scroll wrapper (§7) |
| Hex color in a component rule | Theme switch leaves it stranded | Token reference (§2) |
| Chart on `--bg` inside a `--surface` card | Visible rectangle seam | Figure background = `--surface` (§2) |
| Persistent local storage for UI state | State leaks across unrelated reports | Session store (§11) |
| 0.6s hover transition | UI feels laggy | ≤ `0.2s` (§10) |
| Animation ignoring reduced-motion | Accessibility failure, motion sickness | Skip to final state (§10) |
| Status shown by color alone | Invisible to colorblind readers | Add text or sign (§12) |
| Device theme without the switcher script | Charts stay light on a dark page | CSS + JS both (§4) |

---

## 14. Checklist

- [ ] Exactly three themes: `dark` (default) · `light` · `device`; unknown values rejected
- [ ] All nine color tokens defined in both dark and light, with identical names
- [ ] No literal hex color outside the theme registry
- [ ] Chart surfaces use `--surface`, not `--bg`
- [ ] Spatial tokens defined once and referenced everywhere; no inline spacing literals
- [ ] `device` theme emits the dark media query **and** the chart-retint switcher
- [ ] Device switcher re-runs on live OS preference change
- [ ] No `px` outside `1px` borders and the `16px` root font size
- [ ] Media query thresholds expressed in `rem` or `em`
- [ ] CSS emitted in the fixed layer order: tokens → reset → scrollbar → type → components → layout → responsive → print
- [ ] `overflow-wrap: break-word` applied globally; `code`/`pre` exempted
- [ ] Grids use `auto-fill` + `minmax()`; every grid/flex child has `min-width: 0`
- [ ] Tables wrapped in an `overflow-x: auto` container
- [ ] Mobile sidebar is off-canvas with a hamburger toggle, backdrop, and Escape close
- [ ] Chart container heights use `clamp()` and are capped at `80vh`
- [ ] Every z-index value appears in the z-index scale table
- [ ] All transitions ≤ `0.2s`; content animations ≤ `600ms`
- [ ] `prefers-reduced-motion: reduce` skips every animation and smooth scroll
- [ ] Print stylesheet present: chrome hidden, sections avoid breaks, collapsed sections expanded
- [ ] Scroll spy uses an intersection observer, not scroll events
- [ ] CSV export includes only currently visible rows, generated in-page
- [ ] UI state persisted in the tab-scoped session store, never persistent local storage
- [ ] Text contrast ≥ 4.5:1; status never conveyed by color alone
- [ ] Every interactive element is keyboard reachable with a visible focus ring
- [ ] Icon-only buttons carry accessible labels
- [ ] No horizontal page scroll at any breakpoint
