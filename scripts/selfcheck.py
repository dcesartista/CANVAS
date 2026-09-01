#!/usr/bin/env python3
"""selfcheck — CANVAS's own test suite.

The corpus is the authority the agents copy from, so its internal consistency
is a correctness property, not a style preference. Four checks:

  sections   every `## Term <!-- N -->` line count matches reality. Agents use
             N as the `Read` limit (CONVENTIONS §3), so a wrong N silently
             truncates the section the agent asked for.
  terms      every `<file>.md` -> `## Term` cross-reference resolves. A dangling
             reference makes the agent's Grep return nothing and fall back to
             guessing.
  links      every relative markdown link resolves.
  grants     no read-only agent is ever rendered with a mutating tool.

Usage:
    selfcheck.py              run all checks (exit 1 on any violation)
    selfcheck.py --fix        rewrite drifted <!-- N --> counts in place
    selfcheck.py --only NAME  run one check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = re.compile(r"^## (.+?)(?:\s*<!--\s*(\d+)\s*-->)?\s*$")
MUTATING_TOOLS = ("Write", "Edit", "Patch", "NotebookEdit")


def corpus_files() -> list[Path]:
    """Reference docs carrying the grep-addressable heading contract."""
    return sorted(
        [*(ROOT / "reference").glob("*.md")]
        + [*(ROOT / "lib" / "android" / "reference").glob("*.md")]
    )


def all_markdown() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)


def _sections(lines: list[str]) -> list[tuple[int, str, int | None, int]]:
    """(index, term, claimed_n, actual_n) for each `## ` heading.

    actual_n counts from the heading line up to (not including) the next `## `
    heading, or to end of file for the final heading.
    """
    heads = [(i, m) for i, l in enumerate(lines) if (m := HEADING.match(l))]
    out = []
    for k, (i, m) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        claimed = int(m.group(2)) if m.group(2) else None
        out.append((i, m.group(1).strip(), claimed, end - i))
    return out


def check_sections(fix: bool = False) -> list[str]:
    problems: list[str] = []
    for f in corpus_files():
        lines = f.read_text().splitlines()
        changed = False
        for i, term, claimed, actual in _sections(lines):
            rel = f.relative_to(ROOT)
            if claimed is None:
                if fix:
                    lines[i] = f"## {term} <!-- {actual} -->"
                    changed = True
                else:
                    problems.append(f"{rel}:{i+1}  '## {term}' has no <!-- N --> line count")
                continue
            if claimed != actual:
                if fix:
                    lines[i] = f"## {term} <!-- {actual} -->"
                    changed = True
                else:
                    problems.append(
                        f"{rel}:{i+1}  '## {term}' claims {claimed} lines, actual {actual}"
                        + ("  <-- TRUNCATES" if claimed < actual else "")
                    )
        if changed:
            f.write_text("\n".join(lines) + "\n")
    return problems


def check_terms() -> list[str]:
    """Resolve `<path>.md` -> `## Term` [/ `## Other`] cross-references."""
    headings: dict[str, set[str]] = {}
    for f in all_markdown():
        headings[str(f.relative_to(ROOT))] = {
            t for _, t, _, _ in _sections(f.read_text().splitlines())
        }
    pattern = re.compile(r"`([\w/.-]+\.md)`\s*(?:→|->)\s*((?:`##[^`]+`\s*(?:/|and|\+|,)?\s*)+)")
    problems: list[str] = []
    for f in all_markdown():
        rel = f.relative_to(ROOT)
        for m in pattern.finditer(f.read_text()):
            target = m.group(1)
            candidates = [k for k in headings if k.endswith(target)]
            for term in (t.strip() for t in re.findall(r"##\s*([^`]+)", m.group(2))):
                if not candidates:
                    problems.append(f"{rel}  -> `{target}` (file not found) `## {term}`")
                elif not any(term in headings[c] for c in candidates):
                    problems.append(f"{rel}  -> `{target}` has no `## {term}`")
    return problems


def check_canonical() -> list[str]:
    """One concept = one Term spelling (CONVENTIONS §3).

    Terms are the corpus's addressing scheme: an agent Greps `^## <Term>`, so
    two spellings of one concept means half the lookups miss.
    """
    import collections

    seen = collections.defaultdict(set)
    for f in corpus_files():
        for _, term, _, _ in _sections(f.read_text().splitlines()):
            seen[term.lower()].add((term, str(f.relative_to(ROOT))))
    problems: list[str] = []
    for variants in seen.values():
        if len({t for t, _ in variants}) > 1:
            rendered = "; ".join(f"'{t}' in {f}" for t, f in sorted(variants))
            problems.append(f"one concept spelled several ways -> {rendered}")
    return problems


def check_links() -> list[str]:
    problems: list[str] = []
    for f in all_markdown():
        for m in re.finditer(r"\]\((\.\.?/[^)#]*\.md)", f.read_text()):
            if not (f.parent / m.group(1)).resolve().exists():
                problems.append(f"{f.relative_to(ROOT)}  -> {m.group(1)}")
    return problems


def check_grants() -> list[str]:
    """A read-only agent must never be rendered with a mutating tool.

    Renders every host adapter to a temp dir and inspects the real output —
    the manifest declaring read_only is not enough on its own, the adapter has
    to honour it.
    """
    import tempfile

    sys.path.insert(0, str(ROOT / "scripts"))
    manifest = json.loads((ROOT / "core" / "manifest.json").read_text())
    read_only = {a["id"] for a in manifest["agents"] if a.get("read_only")}
    problems: list[str] = []

    for a in manifest["agents"]:
        if a.get("read_only") and any(t in a.get("tools", "") for t in MUTATING_TOOLS):
            problems.append(f"core/manifest.json  read-only agent '{a['id']}' is granted {a['tools']}")

    import importlib.util

    hosts = [d.name for d in (ROOT / "adapters").iterdir() if (d / "render.py").exists()]
    for host in sorted(hosts):
        spec = importlib.util.spec_from_file_location(
            f"sc_{host}", ROOT / "adapters" / host / "render.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        m = dict(manifest)
        m["_canvas_version"] = (ROOT / "VERSION").read_text().strip()
        with tempfile.TemporaryDirectory() as td:
            try:
                mod.render(root=ROOT, manifest=m, target=Path(td), global_install=False)
            except Exception as e:  # a renderer that refuses to guess is correct behaviour
                problems.append(f"adapters/{host}  render failed: {e}")
                continue
            for path in Path(td).rglob("*.md"):
                if path.stem not in read_only:
                    continue
                fm = path.read_text().split("---")[1] if path.read_text().startswith("---") else ""
                granted = [t for t in MUTATING_TOOLS if re.search(rf"\b{t}\b", fm, re.I)
                           and not re.search(rf"{t}\s*:\s*false", fm, re.I)]
                if granted:
                    problems.append(
                        f"adapters/{host}  '{path.stem}' is read-only but rendered with {', '.join(granted)}"
                    )
    return problems


CHECKS = {
    "sections": check_sections,
    "terms": check_terms,
    "canonical": check_canonical,
    "links": check_links,
    "grants": check_grants,
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="selfcheck")
    p.add_argument("--fix", action="store_true", help="rewrite drifted <!-- N --> counts")
    p.add_argument("--only", choices=sorted(CHECKS), default=None)
    args = p.parse_args(argv)

    names = [args.only] if args.only else list(CHECKS)
    total = 0
    for name in names:
        fn = CHECKS[name]
        problems = fn(fix=args.fix) if name == "sections" else fn()
        total += len(problems)
        status = "ok" if not problems else f"{len(problems)} violation(s)"
        print(f"[{'PASS' if not problems else 'FAIL'}] {name:9s} {status}")
        for pr in problems:
            print(f"         {pr}")
    if args.fix:
        print("\n--fix applied; re-run without --fix to confirm.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
