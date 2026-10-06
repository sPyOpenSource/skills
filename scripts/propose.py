#!/usr/bin/env python3
"""Apply the heuristic rules and write proposal lists for user approval.

Outputs land in .curation_review/. Every file is hand-editable; overlap
between archive.txt and active.txt is checked by archive_skills.py and
the comm check in the approval step — propose itself writes complements
by construction. curation.proposed.yaml is generated from the lists at
propose time — if the lists are hand-edited afterwards, regenerate the
manifest (or edit it directly) before relying on it.
"""

import argparse
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import discover_skills
from inventory import DESC_OFFENDER, FAMILIES, inventory

# family label -> how many members to keep (decided in the design; the
# *which* is decided by body size here and may be hand-edited afterwards)
FAMILY_KEEP = {"grill": 1, "design": 2, "review": 2, "understand": 2}


def body_bytes(root: str, rel: str) -> int:
    total = 0
    for dirpath, _, filenames in os.walk(os.path.join(root, rel)):
        for f in filenames:
            if f.startswith("."):
                continue
            total += os.path.getsize(os.path.join(dirpath, f))
    return total


def to_manifest(active_paths: list[str], all_paths: list[str]) -> dict:
    """Cascade manifest: categories entry when every skill under the first
    path component is active, otherwise per-skill entries. Root-level skill
    paths (no "/") are always individual skill entries, never categories."""
    active = set(active_paths)
    by_cat: dict[str, list[str]] = {}
    all_by_cat: dict[str, list[str]] = {}
    for p in all_paths:
        if "/" in p:
            all_by_cat.setdefault(p.split("/")[0], []).append(p)
    for p in active_paths:
        if "/" in p:
            by_cat.setdefault(p.split("/")[0], []).append(p)
    categories: dict[str, str] = {}
    skills: dict[str, str] = {}
    for p in sorted(active_paths):
        if "/" not in p:
            skills[p] = "active"
    for cat, members in sorted(by_cat.items()):
        if set(all_by_cat.get(cat, [])) == set(members):
            categories[cat] = "active"
        else:
            for p in sorted(members):
                skills[p] = "active"
    return {"default": "archived", "categories": categories, "skills": skills}


def _lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


def propose(root: str, archive_categories: set[str], out_dir: str) -> dict:
    inv = inventory(root)
    rows = inv["skills"]
    all_paths = [r["path"] for r in rows]
    known = set(all_paths)
    reasons: dict[str, str] = {}

    # Rule 1: inert directories
    for d in inv["inert_dirs"]:
        reasons[d] = "rule 1: DESCRIPTION.md with no loadable skill"

    # Rule 3: category verdicts
    for r in rows:
        if r["path"].split("/")[0] in archive_categories:
            reasons[r["path"]] = "rule 3: category verdict"

    # Rule 2: redundancy families, keep-ranked by body size (largest first).
    # Snapshot whether rules 1/3 yielded candidates: a family partially
    # present (some members known, some missing) is fatal only when rules 1
    # and 3 produced nothing — then the family ranking is the whole proposal,
    # so incomplete family data cannot be trusted. Rule 2 archives produced by
    # earlier families must not suppress that error. Trees that omit whole
    # families (fixtures, partial checkouts) are fine.
    rules13 = bool(reasons)
    for label, members in FAMILIES.items():
        present = [m for m in members if m in known]
        missing = [m for m in members if m not in known]
        if present and missing and not rules13:
            sys.exit(f"error: family '{label}' member(s) not found: {', '.join(missing)}")
        keep = FAMILY_KEEP[label]
        eligible = [m for m in members if m in known and m not in reasons]
        ranked = sorted(eligible, key=lambda p: (-body_bytes(root, p), p))
        for p in ranked[keep:]:
            reasons[p] = f"rule 2: family '{label}' keep top {keep} by body size"

    archive_paths = sorted(reasons)
    # Complements by construction, so overlap is impossible here; hand-edited
    # lists are validated by archive_skills.py and the comm check in Task 5.
    active_paths = [p for p in all_paths if p not in reasons]

    # Rule 4: broken references among survivors (report only; fixing or
    # archiving is a decision made at approval time)
    active_set = set(active_paths)
    broken_rows = [r for r in rows if r["path"] in active_set and r["broken_refs"]]
    broken_md = "# Broken references in surviving skills\n\n"
    if broken_rows:
        broken_md += "\n".join(
            f"- `{r['path']}`: {', '.join('`' + b + '`' for b in r['broken_refs'])}"
            for r in broken_rows
        )
        broken_md += "\n"
    else:
        broken_md += "(none)\n"

    offenders = [
        (r["path"], r["desc_chars"]) for r in rows
        if r["path"] in active_set and r["desc_chars"] > DESC_OFFENDER
    ]

    os.makedirs(out_dir, exist_ok=True)
    files = {
        "archive": ("\n".join(archive_paths) + "\n") if archive_paths else "",
        "active": ("\n".join(active_paths) + "\n") if active_paths else "",
        "rewrite": "\n".join(f"{p}\t{n}" for p, n in offenders) + ("\n" if offenders else ""),
        "reasons": ("\n".join(f"{p}\t{reasons[p]}" for p in archive_paths) + "\n") if archive_paths else "",
        "manifest": yaml.safe_dump(to_manifest(active_paths, all_paths), sort_keys=False),
        "broken": broken_md,
    }
    paths = {
        "archive": os.path.join(out_dir, "archive.txt"),
        "active": os.path.join(out_dir, "active.txt"),
        "rewrite": os.path.join(out_dir, "rewrite-needed.tsv"),
        "reasons": os.path.join(out_dir, "archive-reasons.tsv"),
        "manifest": os.path.join(out_dir, "curation.proposed.yaml"),
        "broken": os.path.join(out_dir, "broken-refs.md"),
    }
    for key, path in paths.items():
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(files[key])
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--archive-categories", default="",
                    help="comma-separated top-level categories to archive (rule 3)")
    ap.add_argument("--out", default=".curation_review")
    args = ap.parse_args(argv)
    cats = {c.strip() for c in args.archive_categories.split(",") if c.strip()}
    try:
        files = propose(args.root, cats, args.out)
    except SystemExit as e:
        if e.code:
            print(e.code, file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    n_arch = len(_lines(files["archive"]))
    n_act = len(_lines(files["active"]))
    n_rw = len([l for l in files["rewrite"].splitlines() if l])
    print(f"proposal: {n_act} active, {n_arch} archived, {n_rw} descriptions to rewrite")
    print(f"review and edit files in {args.out}/, then approve before applying")
    return 0


if __name__ == "__main__":
    sys.exit(main())
