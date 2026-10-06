#!/usr/bin/env python3
"""Emit the skill inventory: one row per skill, plus inert directories.

Rows carry the data the heuristic rules in propose.py consume.
Nothing here mutates the catalog.
"""

import argparse
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import SKIP_DIRS, discover_skills, est_tokens

# label -> (members that may be considered for keeping; keep-count lives in propose.py)
FAMILIES = {
    "grill": ["grill-me", "grill-with-docs", "grilling"],
    "design": [
        "creative/claude-design",
        "creative/sketch",
        "creative/popular-web-designs",
        "prototype",
    ],
    "review": [
        "review",
        "requesting-code-review",
        "github/github-code-review",
        "software-development/code-review-pre-commit",
    ],
    "understand": [
        "understand-anything/understand",
        "understand-anything/understand-chat",
        "understand-anything/understand-dashboard",
        "understand-anything/understand-diff",
        "understand-anything/understand-domain",
        "understand-anything/understand-explain",
        "understand-anything/understand-knowledge",
        "understand-anything/understand-onboard",
    ],
}

REF_RE = re.compile(
    r"`([^`\s]+\.(?:md|py|sh|ts|js|json|ya?ml|txt))`|\]\(([^)\s]+\.(?:md|py|sh|ts|js|json|ya?ml|txt))\)"
)


def inert_dirs(root: str) -> list[str]:
    """Dirs containing DESCRIPTION.md whose subtree contains no SKILL.md."""
    rootp = pathlib.Path(root)
    out = []
    for desc in rootp.rglob("DESCRIPTION.md"):
        rel_parts = desc.relative_to(rootp).parts
        if any(p.startswith(".") or p in SKIP_DIRS for p in rel_parts):
            continue
        if not any(desc.parent.rglob("SKILL.md")):
            out.append(desc.parent.relative_to(rootp).as_posix())
    return sorted(set(out))


def _body_text(skill_md: pathlib.Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    return text[end + 4:] if text.startswith("---") and end != -1 else text


def broken_refs(root: str, rel_path: str) -> list[str]:
    """Relative path references in the skill body that resolve nowhere."""
    base = pathlib.Path(root) / rel_path
    body = _body_text(base / "SKILL.md")
    broken = []
    for m in REF_RE.finditer(body):
        ref = m.group(1) or m.group(2)
        if ref.startswith(("http://", "https://", "~", "/")):
            continue
        if not (base / ref).exists() and not (pathlib.Path(root) / ref).exists():
            broken.append(ref)
    return sorted(set(broken))


def inventory(root: str) -> dict:
    skills = discover_skills(root)
    families_by_path = {
        p: [label for label, members in FAMILIES.items() if p in members]
        for p in (s.path for s in skills)
    }
    rows = []
    for s in skills:
        rows.append(
            {
                "path": s.path,
                "name": s.name,
                "desc_chars": s.desc_chars,
                "fm_tokens": est_tokens(s.fm_chars),
                "families": families_by_path[s.path],
                "broken_refs": broken_refs(root, s.path),
            }
        )
    return {
        "skills": rows,
        "inert_dirs": inert_dirs(root),
        "totals": {
            "skills": len(rows),
            "fm_tokens": sum(r["fm_tokens"] for r in rows),
            "offenders": sum(1 for r in rows if r["desc_chars"] > 400),
        },
    }


def to_markdown(inv: dict) -> str:
    lines = [
        "| path | name | desc chars | fm tokens | families | broken refs |",
        "|---|---|---|---|---|---|",
    ]
    for r in inv["skills"]:
        lines.append(
            f"| {r['path']} | {r['name']} | {r['desc_chars']} | {r['fm_tokens']} "
            f"| {','.join(r['families'])} | {','.join(r['broken_refs'])} |"
        )
    lines.append("")
    lines.append(f"Inert directories: {', '.join(inv['inert_dirs']) or '(none)'}")
    t = inv["totals"]
    lines.append(
        f"Totals: {t['skills']} skills, {t['fm_tokens']} fm tokens, "
        f"{t['offenders']} description offenders (>400 chars)"
    )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", help="write inventory JSON here")
    ap.add_argument("--md", help="write inventory markdown here")
    args = ap.parse_args(argv)
    inv = inventory(args.root)
    md = to_markdown(inv)
    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(inv, fh, indent=1)
    if args.md:
        os.makedirs(os.path.dirname(args.md) or ".", exist_ok=True)
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(md)
    if not args.json and not args.md:
        sys.stdout.write(md)
    else:
        t = inv["totals"]
        print(f"inventory: {t['skills']} skills, {t['fm_tokens']} fm tokens, {t['offenders']} offenders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
