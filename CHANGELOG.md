# Changelog

All notable changes to this standards library are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html), applied to the standards themselves:

| Bump | Trigger |
|---|---|
| **Major** | A rule changes in a way that makes previously-conforming code non-conforming |
| **Minor** | A new standard, a new section, or a relaxed rule |
| **Patch** | Clarification, typo, dead-link fix — no semantic change to any rule |

---

## [0.1.0] — 2026-07-13

Initial release. The library is composable, conformance-checked, and usable across projects. Pre-1.0: rules may still change as the standards are exercised on real work; the first stable line is tagged `v1.0.0`.

### Added

- **`TEMPLATE.md`** — canonical structure every standard follows: header schema (ID · Tier · Version · Owns · Defers to · Load with), TOC, sequential sections, scale matrix, checklist. Defines the split procedure for oversized standards.
- **`ROUTER.md`** — full catalog, the six-tier model (Foundation → Core → Delivery → Interface → Domain → Language), the Always-On Set, routes by project type and by surface, and tier-based conflict resolution. A project loads a routed subset, never the whole library.
- **`tools/validate.py`** — dependency-free conformance validator. Enforces the line cap, header schema, ID↔directory match, tier validity, TOC↔section parity, sequential numbering, checklist presence, code-block policy, dead cross-references, and router registration.
- **CI pipeline** (`.github/workflows/standards.yml`) — conformance, markdown lint, offline link check, repo hygiene, and tag-triggered release publishing.
- **`README.md`** — was empty; now the front door (start-here table, design rules, tier model, adoption instructions).
- **`CHANGELOG.md`**, **`LICENSE`** (MIT).
- **`testing/REALITY.md`** — reality dimensions (faults, adversarial input, concurrency, resources, time, state accumulation, drift) split out of the testing standard.
- **`local_mcp/TOOLS.md`**, **`local_mcp/RUNTIME.md`**, **`local_mcp/DELIVERY.md`** — split out of a single 2,999-line standard.
- **`html_generation/THEMING.md`**, **`html_generation/CHARTS.md`** — split out of a 1,258-line standard.
- **`typescript/TOOLING.md`**, **`shell/HARDENING.md`** — split out of oversized language standards.

### Changed

- **Every standard now fits under 500 lines.** The library was 24,940 lines across 35 files, with 28 files over the cap and one at 2,999 lines. Content was compressed with the density rules in `CLAUDE.md` and split at natural seams — rules were preserved, prose was not.
- **One owner per topic.** Every standard declares what it `**Owns**` and what it `**Defers to**`. Duplicated rules were collapsed into their owning standard and replaced with cross-references. Notably: error boundaries consolidated into `error_handling/`, config cascade into `configuration/`, and the `sql/` ↔ `database/` boundary made explicit (how you *write* queries vs how you *design* the store).
- **Code blocks removed from non-language standards**, per the repo's own rule. Every rule a code block was demonstrating survives as a rule, table, or `X → Y` line.
- **`CLAUDE.md`** — catalog corrected (it marked ten existing standards as "Planned"), hard cap lowered from 800 to 499 lines, conformance and one-owner rules added, dead release branch reference removed.
- **`MCP_IDEAS.md`** → **`local_mcp/IDEAS.md`** — it is a server-idea catalog, not a standard; moved out of the repo root and excluded from validation.
- Tooling recommendations brought current across language standards.

[0.1.0]: https://github.com/azzindani/Standards/releases/tag/v0.1.0
