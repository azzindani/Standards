#!/usr/bin/env python3
"""Conformance validator + index emitter for the Standards library.

Enforces the contract defined in TEMPLATE.md. Exit 0 = all standards conform.
No third-party dependencies — stdlib only, runs on any Python >= 3.9.

    validate.py                 validate only
    validate.py --emit-index    validate, then write index.json
    validate.py --check-index   validate, then fail if index.json is stale

index.json is the machine-readable contract consumed by downstream tools
(Pipeline et al). It carries what a consumer needs to route and inject
standards without re-parsing markdown: catalog · headers · checklists ·
always-on set · routes. Regenerate it whenever a standard or ROUTER changes;
CI runs --check-index to guarantee it never drifts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAX_LINES = 499
MIN_CHECKLIST_ITEMS = 8
MAX_CHECKLIST_ITEMS = 40

TIERS = {
    "Foundation",
    "Core",
    "Delivery",
    "Interface",
    "Domain",
    "Language",
    "Meta",
}

# Standards that legitimately contain code blocks: language-specific ones.
CODE_ALLOWED = {"python", "rust", "go", "typescript", "shell", "sql"}

# Repo-root files that are not standards and are exempt from the schema.
NON_STANDARD_FILES = {"README.md", "CLAUDE.md", "CHANGELOG.md", "ROUTER.md", "TEMPLATE.md"}

HEADER_FIELDS = ["ID", "Tier", "Version", "Owns", "Defers to", "Load with"]

RE_H1 = re.compile(r"^# (.+) Standards$")
RE_SECTION = re.compile(r"^## (\d+)\. (.+)$")
RE_TOC_ENTRY = re.compile(r"^\d+\. \[(.+?)\]\(#(.+?)\)$")
RE_ID = re.compile(r"^\*\*ID\*\* `([a-z0-9_/]+)`", re.MULTILINE)
RE_TIER = re.compile(r"\*\*Tier\*\* ([A-Za-z]+)")
RE_VERSION = re.compile(r"\*\*Version\*\* (\d+\.\d+)")
RE_LINK = re.compile(r"\[[^\]]*\]\((?!https?://|#)([^)#]+)(?:#[^)]*)?\)")
RE_FENCE = re.compile(r"^```")


@dataclass
class Result:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(ROOT))


def slugify(title: str) -> str:
    """GitHub anchor slug for a '## N. Title' heading."""
    s = title.lower()
    # Match GitHub's anchor algorithm exactly: drop punctuation, then map each
    # space to one hyphen with NO collapsing. "Foo & Bar" -> "foo--bar", so the
    # in-page TOC link resolves on GitHub. Collapsing here would demand a single
    # hyphen and silently break navigation for any title containing " & ".
    s = re.sub(r"[^\w\s-]", "", s)
    return s.strip().replace(" ", "-")


def discover_standards() -> list[Path]:
    out: list[Path] = []
    for p in sorted(ROOT.glob("*/*.md")):
        if p.parts[len(ROOT.parts)] in {"tools", ".github", ".git"}:
            continue
        if p.name == "IDEAS.md":  # reference catalogs, not standards
            continue
        out.append(p)
    return out


def check_length(r: Result, lines: list[str]) -> None:
    n = len(lines)
    if n > MAX_LINES:
        r.errors.append(f"{n} lines — exceeds hard cap of {MAX_LINES} (split it: TEMPLATE.md §8)")
    elif n < 100:
        r.warnings.append(f"{n} lines — thin for a standard")


def check_title_and_purpose(r: Result, lines: list[str]) -> None:
    if not lines:
        r.errors.append("empty file")
        return
    if not RE_H1.match(lines[0]):
        r.errors.append(f"line 1 must match '# <Domain> Standards', got: {lines[0]!r}")
    if len([l for l in lines if l.startswith("# ")]) != 1:
        r.errors.append("must contain exactly one H1")
    purpose = [l for l in lines[1:6] if l.startswith("> ")]
    if not purpose:
        r.errors.append("missing purpose blockquote under H1")


def check_header(r: Result, lines: list[str], expect_id: str) -> None:
    head = "\n".join(lines[:14])
    for f in HEADER_FIELDS:
        if f"**{f}**" not in head:
            r.errors.append(f"header missing **{f}** field (TEMPLATE.md §3)")

    m = RE_ID.search(head)
    if not m:
        r.errors.append("header **ID** must be a backticked lowercase slug")
    elif m.group(1) != expect_id:
        r.errors.append(f"header ID `{m.group(1)}` does not match path-derived id `{expect_id}`")

    m = RE_TIER.search(head)
    if not m:
        r.errors.append("header **Tier** missing or malformed")
    elif m.group(1) not in TIERS:
        r.errors.append(f"Tier {m.group(1)!r} not one of {sorted(TIERS)}")

    if not RE_VERSION.search(head):
        r.errors.append("header **Version** missing or not semver-minor (e.g. 1.0)")


def check_sections(r: Result, lines: list[str]) -> list[tuple[int, str]]:
    sections = [
        (int(m.group(1)), m.group(2))
        for line in lines
        if (m := RE_SECTION.match(line))
    ]
    if not sections:
        r.errors.append("no numbered '## N. Title' sections found")
        return []

    nums = [n for n, _ in sections]
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        r.errors.append(f"section numbers not sequential from 1: got {nums}")

    if sections[-1][1] != "Checklist":
        r.errors.append(f"final section must be 'Checklist', got {sections[-1][1]!r}")

    return sections


def check_toc(r: Result, lines: list[str], sections: list[tuple[int, str]]) -> None:
    if "## Table of Contents" not in lines:
        r.errors.append("missing '## Table of Contents'")
        return
    start = lines.index("## Table of Contents")
    entries = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if m := RE_TOC_ENTRY.match(line.strip()):
            entries.append((m.group(1), m.group(2)))

    if len(entries) != len(sections):
        r.errors.append(
            f"TOC has {len(entries)} entries but file has {len(sections)} sections — must match 1:1"
        )
        return

    for (title, anchor), (num, sec_title) in zip(entries, sections):
        if title != sec_title:
            r.errors.append(f"TOC entry {title!r} != section title {sec_title!r}")
        want = f"{num}-{slugify(sec_title)}"
        if anchor != want:
            r.errors.append(f"TOC anchor '#{anchor}' should be '#{want}'")


def check_checklist(r: Result, lines: list[str]) -> None:
    items = [l for l in lines if l.strip().startswith("- [ ]")]
    if not items:
        r.errors.append("checklist has no '- [ ]' items")
    elif len(items) < MIN_CHECKLIST_ITEMS:
        r.warnings.append(f"only {len(items)} checklist items (min {MIN_CHECKLIST_ITEMS})")
    elif len(items) > MAX_CHECKLIST_ITEMS:
        r.warnings.append(
            f"{len(items)} checklist items (max {MAX_CHECKLIST_ITEMS}) — standard may be doing two jobs"
        )
    if any(l.strip().startswith("- [x]") for l in lines):
        r.errors.append("checklist contains pre-ticked '- [x]' items — ship them unticked")


def check_code_blocks(r: Result, lines: list[str], domain: str) -> None:
    if domain in CODE_ALLOWED:
        return
    fences = sum(1 for l in lines if RE_FENCE.match(l))
    if fences:
        r.errors.append(
            f"{fences // 2} code block(s) — only language standards {sorted(CODE_ALLOWED)} may carry code"
        )


def check_links(r: Result, lines: list[str], path: Path) -> None:
    for i, line in enumerate(lines, 1):
        for target in RE_LINK.findall(line):
            if not (path.parent / target).resolve().exists():
                r.errors.append(f"line {i}: dead link → {target}")


def check_router_coverage(standards: list[Path]) -> Result:
    r = Result(ROOT / "ROUTER.md")
    router = ROOT / "ROUTER.md"
    if not router.exists():
        r.errors.append("ROUTER.md missing — it is the catalog + routing entry point")
        return r
    text = router.read_text(encoding="utf-8")
    for p in standards:
        rel = str(p.relative_to(ROOT))
        if rel not in text:
            r.errors.append(f"standard not registered in catalog: {rel}")
    return r


def validate(path: Path) -> Result:
    r = Result(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    domain = path.parent.name
    stem = path.stem
    expect_id = domain if stem == "STANDARDS" else f"{domain}/{stem.lower()}"

    check_length(r, lines)
    check_title_and_purpose(r, lines)
    check_header(r, lines, expect_id)
    sections = check_sections(r, lines)
    check_toc(r, lines, sections)
    check_checklist(r, lines)
    check_code_blocks(r, lines, domain)
    check_links(r, lines, path)
    return r


# ──────────────────────────────────────────────────────────────────────
# Index emission — the machine-readable contract for downstream consumers.
# ──────────────────────────────────────────────────────────────────────

INDEX_PATH = ROOT / "index.json"
INDEX_SCHEMA = 1

# Load order — later tiers assume earlier tiers are in effect (ROUTER.md §2).
TIER_ORDER = ["Foundation", "Core", "Delivery", "Interface", "Domain", "Language"]

RE_OWNS = re.compile(r"^\*\*Owns\*\* (.+)$", re.MULTILINE)
RE_DEFERS = re.compile(r"^\*\*Defers to\*\* (.+)$", re.MULTILINE)
RE_LOAD_WITH = re.compile(r"^\*\*Load with\*\* (.+)$", re.MULTILINE)
RE_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
RE_TOKEN = re.compile(r"`([A-Za-z0-9_/*.]+)`")
RE_PAREN = re.compile(r"\(([^)]*)\)")
# Markdown row cells split on pipes that are NOT backslash-escaped: ROUTER
# writes alternation as `go` \| `rust` inside a cell, and a naive split on "|"
# would tear that row in half.
RE_CELL_SPLIT = re.compile(r"(?<!\\)\|")


def path_to_id(rel: str) -> str:
    """Path relative to ROOT → standard id. Mirrors validate()'s expect_id."""
    p = Path(rel)
    return p.parent.name if p.stem == "STANDARDS" else f"{p.parent.name}/{p.stem.lower()}"


def link_to_id(href: str, base: Path) -> str | None:
    """Resolve a relative markdown link to a standard id, or None if off-corpus."""
    target = (base.parent / href.split("#")[0]).resolve()
    try:
        return path_to_id(str(target.relative_to(ROOT)))
    except ValueError:
        return None


def split_dots(cell: str) -> list[str]:
    return [s.strip() for s in cell.split("·") if s.strip()]


def parse_header_meta(path: Path, text: str) -> dict:
    head = "\n".join(text.splitlines()[:14])

    owns: list[str] = []
    if m := RE_OWNS.search(head):
        owns = [s.replace("`", "") for s in split_dots(m.group(1))]

    defers: list[dict] = []
    if m := RE_DEFERS.search(head):
        for seg in split_dots(m.group(1)):
            topic = seg.split("→")[0].strip() if "→" in seg else seg
            for _, href in RE_MD_LINK.findall(seg):
                if sid := link_to_id(href, path):
                    defers.append({"topic": topic, "to": sid})

    load_with: list[str] = []
    if m := RE_LOAD_WITH.search(head):
        for _, href in RE_MD_LINK.findall(m.group(1)):
            if (sid := link_to_id(href, path)) and sid not in load_with:
                load_with.append(sid)

    return {"owns": owns, "defers_to": defers, "load_with": load_with}


def parse_checklist(lines: list[str]) -> list[str]:
    """Items of the final Checklist section — TEMPLATE.md guarantees it exists."""
    return [l.strip()[6:].strip() for l in lines if l.strip().startswith("- [ ]")]


def build_standard(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = str(path.relative_to(ROOT))

    head = "\n".join(lines[:14])
    m_tier = RE_TIER.search(head)
    m_ver = RE_VERSION.search(head)
    purpose = next((l[2:].strip() for l in lines[1:6] if l.startswith("> ")), "")
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else rel

    entry = {
        "id": path_to_id(rel),
        "domain": path.parent.name,
        "path": rel,
        "title": title,
        "purpose": purpose,
        "tier": m_tier.group(1) if m_tier else None,
        "version": m_ver.group(1) if m_ver else None,
        "lines": len(lines),
        "checklist": parse_checklist(lines),
    }
    entry.update(parse_header_meta(path, text))
    return entry


def expand_token(token: str, known: list[str]) -> list[str]:
    """`local_mcp/*` → every id in that domain · `testing/PRESSURE.md` → id · else itself."""
    if token.endswith("/*"):
        prefix = token[:-2]
        hits = [i for i in known if i == prefix or i.startswith(prefix + "/")]
        return sorted(hits, key=lambda i: (i != prefix, i))  # domain root first
    if token.endswith(".md"):
        return [path_to_id(token)]
    return [token] if token in known else []


def parse_route_cell(cell: str, known: list[str]) -> dict:
    """A ROUTER route cell → structured adds.

    Handles the three shapes ROUTER uses, and keeps `raw` so no nuance is lost:
      `api` · `security`            → add (unconditional)
      `go` \\| `rust`                → alternatives (choose one)
      `python` (or `typescript`)    → alternatives (choose one)
      `local_mcp/*` (if tool-serving) → conditional
    """
    add: list[str] = []
    alternatives: list[list[str]] = []
    conditional: list[dict] = []

    for seg in split_dots(cell):
        ids = [i for t in RE_TOKEN.findall(seg) for i in expand_token(t, known)]
        if not ids:
            continue  # prose-only segment, e.g. "language route" — preserved in raw
        paren = RE_PAREN.search(seg)
        note = paren.group(1).strip() if paren else ""

        if "\\|" in seg or note.startswith("or "):
            alternatives.append(ids)
        elif note.startswith("if "):
            conditional.append({"add": ids, "when": note[3:].strip()})
        else:
            add.extend(i for i in ids if i not in add)

    return {
        "add": add,
        "alternatives": alternatives,
        "conditional": conditional,
        "raw": cell.strip(),
    }


def router_section(text: str, heading: str) -> list[str]:
    """Lines of one '## N. Heading' section of ROUTER.md."""
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line.split(". ", 1)[-1].strip() == heading
            continue
        if inside:
            out.append(line)
    return out


def table_rows(lines: list[str]) -> list[list[str]]:
    """Data rows of the first markdown table in `lines` — header + rule dropped."""
    rows: list[list[str]] = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if rows:
                break  # table ended
            continue
        cells = [c.strip() for c in RE_CELL_SPLIT.split(s)[1:-1]]
        if not cells or set("".join(cells)) <= set("-: "):
            continue  # separator row
        rows.append(cells)
    return rows[1:] if rows else []  # drop header row


def build_routes(known: list[str]) -> dict:
    text = (ROOT / "ROUTER.md").read_text(encoding="utf-8")

    always_on: list[str] = []
    for cells in table_rows(router_section(text, "Always-On Set")):
        for _, href in RE_MD_LINK.findall(cells[0]):
            if (sid := link_to_id(href, ROOT / "ROUTER.md")) and sid not in always_on:
                always_on.append(sid)

    by_type = {
        cells[0]: parse_route_cell(cells[1], known)
        for cells in table_rows(router_section(text, "Routes by Project Type"))
        if len(cells) >= 2
    }
    by_surface = {
        cells[0]: {**parse_route_cell(cells[1], known), "trigger": cells[2] if len(cells) > 2 else ""}
        for cells in table_rows(router_section(text, "Routes by Surface"))
        if len(cells) >= 2
    }

    return {"always_on": always_on, "by_type": by_type, "by_surface": by_surface}


def build_index(standards: list[Path]) -> dict:
    entries = [build_standard(p) for p in standards]
    known = [e["id"] for e in entries]
    routes = build_routes(known)
    return {
        "schema": INDEX_SCHEMA,
        "generator": "tools/validate.py --emit-index",
        "tier_order": TIER_ORDER,
        "always_on": routes["always_on"],
        "routes": {"by_type": routes["by_type"], "by_surface": routes["by_surface"]},
        "standards": sorted(entries, key=lambda e: e["id"]),
    }


def render_index(index: dict) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def emit_index(standards: list[Path]) -> None:
    INDEX_PATH.write_text(render_index(build_index(standards)), encoding="utf-8")
    print(f"wrote {INDEX_PATH.relative_to(ROOT)} — {len(standards)} standards")


def check_index(standards: list[Path]) -> int:
    """CI gate: index.json must match what the current corpus would generate."""
    if not INDEX_PATH.exists():
        print("FAIL — index.json missing. Run: tools/validate.py --emit-index", file=sys.stderr)
        return 1
    want = render_index(build_index(standards))
    if INDEX_PATH.read_text(encoding="utf-8") != want:
        print(
            "FAIL — index.json is stale. Run: tools/validate.py --emit-index",
            file=sys.stderr,
        )
        return 1
    print("PASS — index.json is current")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--emit-index", action="store_true", help="write index.json")
    g.add_argument("--check-index", action="store_true", help="fail if index.json is stale")
    args = ap.parse_args()

    standards = discover_standards()
    if not standards:
        print("FAIL: no standards discovered", file=sys.stderr)
        return 1

    results = [validate(p) for p in standards]
    results.append(check_router_coverage(standards))

    n_err = sum(len(r.errors) for r in results)
    n_warn = sum(len(r.warnings) for r in results)

    for r in results:
        if not r.errors and not r.warnings:
            continue
        print(f"\n{r.rel}")
        for e in r.errors:
            print(f"  ERROR   {e}")
        for w in r.warnings:
            print(f"  warn    {w}")

    print(f"\n{'─' * 60}")
    print(f"{len(standards)} standards · {n_err} errors · {n_warn} warnings")

    if n_err:
        print(f"FAIL — {n_err} error(s). See TEMPLATE.md for the contract.")
        return 1
    print("PASS — all standards conform to TEMPLATE.md")

    # Index is only emitted/checked off a conforming corpus — a malformed
    # header would otherwise be baked into the contract downstream reads.
    if args.emit_index:
        emit_index(standards)
    if args.check_index:
        return check_index(standards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
