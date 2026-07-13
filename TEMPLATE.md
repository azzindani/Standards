# Standard Template

> Canonical structure every `STANDARDS.md` in this repository follows. Copy this file to start a new standard.

**ID** `template` · **Tier** Meta · **Version** 1.0
**Owns** standard file structure · header schema · section order · CI conformance contract
**Defers to** catalog + routing → [ROUTER.md](ROUTER.md) · writing density rules → [CLAUDE.md](CLAUDE.md)
**Load with** [CLAUDE.md](CLAUDE.md)

---

## Table of Contents

1. [Hard Constraints](#1-hard-constraints)
2. [File Layout](#2-file-layout)
3. [Header Schema](#3-header-schema)
4. [Section Rules](#4-section-rules)
5. [Scale Matrix](#5-scale-matrix)
6. [Checklist Section](#6-checklist-section)
7. [Cross-Reference Rules](#7-cross-reference-rules)
8. [Splitting a Standard](#8-splitting-a-standard)
9. [Skeleton](#9-skeleton)
10. [Checklist](#10-checklist)

---

## 1. Hard Constraints

CI enforces every row. Violation → build fails.

| Constraint | Rule |
|---|---|
| Length | ≤ 499 lines. Target 400–480. Over → split (§8) |
| Title | `# <Domain> Standards` — H1, first line, exactly one per file |
| Purpose | Blockquote, one sentence, directly under H1 |
| Header | Metadata block (§3) directly under purpose |
| TOC | `## Table of Contents` — entries match sections 1:1 |
| Sections | Numbered `## N. Title`, sequential from 1, no gaps |
| Checklist | Final section, always present |
| Links | Every relative link resolves to an existing file |
| Registration | File appears in [ROUTER.md](ROUTER.md) catalog |
| Code | Zero code blocks ; language standards (`python/`, `rust/`, `go/`, `typescript/`, `shell/`, `sql/`) |

---

## 2. File Layout

```text
<domain>/
├── STANDARDS.md      ← required · core rules · entry point
├── <ASPECT>.md       ← optional · split overflow (§8)
└── <ASPECT>.md
```

- One directory = one domain. `STANDARDS.md` is always the entry point.
- Split files use SCREAMING_CASE names describing the aspect: `PRESSURE.md` · `REALITY.md` · `TOOLS.md`.
- Split files carry the identical header schema and section rules. They are standards, not appendices.
- ✗ `README.md` inside a standard directory — `STANDARDS.md` is the readme.

---

## 3. Header Schema

Five lines, in order, immediately after the purpose blockquote.

| Field | Required | Content |
|---|---|---|
| `**ID**` | yes | Backtick slug = directory name. Split files: `<dir>/<aspect>` |
| `**Tier**` | yes | One of: Foundation · Core · Delivery · Interface · Domain · Language · Meta |
| `**Version**` | yes | Semver minor of the standard. Bump on rule change, not typo fix |
| `**Owns**` | yes | Topics this file is single source of truth for · `·`-separated |
| `**Defers to**` | yes | `<topic> → [link]` for every topic deliberately NOT covered here. `—` if none |
| `**Load with**` | yes | Standards that must be loaded alongside this one to be coherent |

**Owns** and **Defers to** are the anti-duplication contract. A rule lives in exactly one standard. Every other standard that touches the topic points at the owner via **Defers to**.

Tier meanings:

| Tier | Meaning | Loaded |
|---|---|---|
| Foundation | Structure + correctness of any code | Always |
| Core | Practice discipline — test, secure, observe, document | Always |
| Delivery | Getting code into production | Always |
| Interface | Contract with the outside — API, DB, CLI, web | By surface |
| Domain | Problem-space specific — ML, pipeline, MCP, agent | By domain |
| Language | Syntax + idiom + toolchain | By language |
| Meta | Governs the standards repo itself | Authoring only |

---

## 4. Section Rules

- Numbered `## N. Title`, sequential, no gaps, no re-use.
- Every sentence is a rule or a clarification of a rule. ✗ motivation · ✗ tutorial · ✗ "why this matters"
- Tables over prose. One-liner rules over paragraphs.
- Apply [CLAUDE.md](CLAUDE.md) density rules: strip articles · weak modals · scaffolding · hedging.
- ✗ compress load-bearing text: negations · hard thresholds · exception clauses · technical names · ordered sequences.
- Anti-patterns get their own section near the end when the domain has common failure modes.

Section ordering convention:

```text
1.  Principles / mental model     ← what the domain optimizes for
2..N-3.  Rules by topic           ← the substance
N-2. Anti-Patterns                ← optional
N-1. Scale Matrix                 ← optional (§5)
N.   Checklist                    ← required (§6)
```

---

## 5. Scale Matrix

Include when rules change with project size. Columns are fixed — ✗ invent new ones.

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| *what varies* | *1 dev, throwaway* | *users depend on it* | *multi-team, high traffic* |

Rules:

- Row = a dimension whose threshold moves with scale (coverage %, review depth, SLO tightness).
- Cell = a concrete threshold or a hard rule. ✗ vague ("more testing") → `≥80% line, ≥70% branch`.
- A rule that never relaxes is NOT a matrix row — it is a plain rule in a numbered section.

---

## 6. Checklist Section

Final section. Title exactly `## N. Checklist`.

- GitHub task-list format: `- [ ] <checkable assertion>`.
- Each item is verifiable by a reviewer in under a minute — binary pass/fail.
- ✗ aspirational items ("code is clean") → checkable items ("no function exceeds 50 lines").
- Order mirrors section order.
- 12–30 items. Fewer → standard is thin. More → standard is doing two jobs, split it.

---

## 7. Cross-Reference Rules

| Rule | Detail |
|---|---|
| Format | Relative markdown link: `[testing](../testing/STANDARDS.md)` |
| Section cite | Append section: `[testing §4](../testing/STANDARDS.md#4-size-classes)` |
| Direction | Point to the **owner** of the topic, declared in its `**Owns**` header |
| Duplication | Cross-reference ✓ ; restate the other standard's rules ✗ |
| Cycles | Allowed — standards are a graph, not a tree |
| Dead links | CI failure |

When two standards both need a rule: the one whose **Owns** covers it states it; the other adds a **Defers to** entry and a one-line pointer at point of use.

---

## 8. Splitting a Standard

Trigger: file exceeds 499 lines after density compression.

Procedure:

1. Find the natural seam — a contiguous run of sections serving a distinct question.
2. Move those sections into `<ASPECT>.md`. Renumber both files from 1.
3. Both files get the full header schema. Parent lists the child under **Load with**; child lists parent under **Load with**.
4. Parent adds the child's topics to its **Defers to**.
5. Register the child in [ROUTER.md](ROUTER.md).
6. Both files keep their own TOC, Scale Matrix (if applicable), and Checklist.

✗ split by line count alone — a split file must answer a distinct question standalone.
✗ split into an "appendix" or "part 2" — every file is a first-class standard.

---

## 9. Skeleton

Copy from H1 to end of checklist. Replace bracketed content.

```markdown
# <Domain> Standards

> <One sentence: what this standard governs.>

**ID** `<slug>` · **Tier** <tier> · **Version** 1.0
**Owns** <topic> · <topic>
**Defers to** <topic> → [<std>](../<std>/STANDARDS.md)
**Load with** [<std>](../<std>/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
…
N. [Checklist](#n-checklist)

---

## 1. Principles
…
## N. Checklist
```

---

## 10. Checklist

- [ ] File ≤ 499 lines
- [ ] H1 is `# <Domain> Standards`, first line, unique
- [ ] Purpose blockquote present, one sentence
- [ ] Header schema complete: ID · Tier · Version · Owns · Defers to · Load with
- [ ] `**ID**` slug matches directory name
- [ ] Tier is one of the seven defined values
- [ ] TOC present and entries match section titles 1:1
- [ ] Sections numbered sequentially from 1, no gaps
- [ ] Every sentence is a rule or clarifies a rule
- [ ] Tables used for comparisons ; prose
- [ ] Density rules applied — no articles, hedging, or scaffolding
- [ ] Load-bearing text uncompressed — negations, thresholds, exceptions intact
- [ ] Zero code blocks (non-language standards)
- [ ] Scale Matrix present if rules vary with project size
- [ ] Checklist is the final section, items are binary pass/fail
- [ ] Every relative link resolves
- [ ] No rule duplicated from another standard — cross-referenced instead
- [ ] File registered in [ROUTER.md](ROUTER.md)
- [ ] `tools/validate.py` passes
