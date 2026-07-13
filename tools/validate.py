#!/usr/bin/env python3
"""Conformance validator for the Standards library.

Enforces the contract defined in TEMPLATE.md. Exit 0 = all standards conform.
No third-party dependencies — stdlib only, runs on any Python >= 3.9.
"""

from __future__ import annotations

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


def main() -> int:
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
