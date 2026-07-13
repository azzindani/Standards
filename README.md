# Standards

Composable engineering standards library. One directory per domain, one `STANDARDS.md` per directory, every file under 500 lines.

Projects don't adopt this whole repo — they **route** to the subset they need. A Python CLI loads a different set than an MCP server or a TypeScript web app.

---

## Start Here

| You want to | Read |
|---|---|
| Know which standards *your* project loads | [ROUTER.md](ROUTER.md) §5 |
| Write or change a standard | [TEMPLATE.md](TEMPLATE.md) |
| Understand the rules this repo is written under | [CLAUDE.md](CLAUDE.md) |
| See what changed | [CHANGELOG.md](CHANGELOG.md) |

---

## Design Rules

| Rule | Detail |
|---|---|
| **Under 500 lines** | Hard cap, CI-enforced. A standard that outgrows it splits at a natural seam |
| **One owner per topic** | Each standard declares what it `**Owns**`. Rules live in exactly one file; everything else cross-references |
| **Composable, not monolithic** | Load the Always-On Set + the routes matching your surfaces, languages, and domain |
| **Rules, not essays** | Every sentence is a rule or clarifies one. No motivation, no tutorials |
| **Tables over prose** | Comparisons are tables. Conditions are `X → Y`. Density over word count |
| **Code only in language standards** | `python/` `rust/` `go/` `typescript/` `shell/` `sql/` carry code. Everything else is language-agnostic |

---

## Tiers

Standards load in tier order. Later tiers assume earlier ones are in effect.

```text
Foundation → Core → Delivery → Interface → Domain → Language
```

| Tier | Question | Loaded |
|---|---|---|
| **Foundation** | How is the system structured? | Always |
| **Core** | How do we prove it works and keep it safe? | Always |
| **Delivery** | How does it reach production? | Always |
| **Interface** | How does the outside world talk to it? | Per surface |
| **Domain** | What does this problem space demand? | Per domain |
| **Language** | What is idiomatic here? | Per language |

Full catalog: [ROUTER.md](ROUTER.md) §4.

---

## Using This in a Project

Reference the standards your project routes to from its own `CLAUDE.md` / `AGENTS.md`:

```markdown
## Standards

Load from the Standards library:
- Always-On Set — see Standards/ROUTER.md §3
- Language: python/STANDARDS.md
- Surface: cli/STANDARDS.md · api/STANDARDS.md
- Domain: data_pipeline/STANDARDS.md
```

Vendor the repo as a submodule, a sibling checkout, or copy the routed subset. The routing rule is the contract — not the delivery mechanism.

---

## Conformance

Every standard is validated in CI against the [TEMPLATE.md](TEMPLATE.md) contract:

```bash
python3 tools/validate.py
```

Checks: line cap · header schema · TOC ↔ section parity · sequential numbering · checklist present · dead cross-references · code-block policy · router registration.

---

## Contributing

1. Read [TEMPLATE.md](TEMPLATE.md) — the structure is non-negotiable.
2. Check no existing standard already `**Owns**` your topic ([ROUTER.md](ROUTER.md) §4).
3. Write incrementally. Register in the catalog and at least one route.
4. `python3 tools/validate.py` must pass before you push.

---

## License

MIT — see [LICENSE](LICENSE).
