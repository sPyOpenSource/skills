# Skill Index Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the always-on skill index from 135 skills / ~11,000 frontmatter tokens to an enforced active set of ≤35 skills by running a heuristic cleanup (inventory → approve → archive → rewrite) and then implementing the curation gate over the reduced catalog.

**Architecture:** Four one-off CLI tools under `scripts/` (`inventory`, `propose`, `archive_skills`, `rewrite_desc`) share the `scripts/curation/skills.py` discovery module and a gitignored `.curation_review/` working area where proposal lists are written, hand-edited, and approved. Cleanup runs first with no gate; afterwards the curation gate from `docs/superpowers/plans/2026-09-26-skill-curation-gate.md` is executed with the deltas specified in Task 9, so `curate.py check` permanently enforces the cleanup's invariants.

**Tech Stack:** Python 3.14 standard library (`argparse`, `dataclasses`, `json`, `os`, `pathlib`, `re`, `subprocess`, `unittest`), PyYAML, Git

## Global Constraints

- Active set ≤ **35 skills**; `curate.py`'s token budget is `TOKEN_BUDGET = 3000` frontmatter tokens (baseline for all skills: 11,291 as stated in the spec; the exact number for the current tree is recorded in Task 2 and used as the "before" figure).
- No active skill's `description` exceeds **400 characters**; every rewrite targets **≤160 characters**, one sentence.
- Rewrites are applied only from a single batch file approved by the user — no description is ever edited outside that batch.
- Archiving = move to `archive/<original/path>/` **plus** rename `SKILL.md` → `SKILL.md.archived`. Nothing is deleted except the two superseded duplicate pairs already resolved (Task 1 verifies this).
- Nothing mutates until its approval checkpoint passes: proposal lists are approved before Task 6 runs `--apply`; the rewrite batch is approved before Task 7 runs `apply`.
- `curation.yaml`, `.curation_stamp.json`, and `.curation_review/` are gitignored. `curation.example.yaml`, all scripts, and all test files are committed.
- Proposal lists are hand-editable — the user may move any skill between `active.txt` and `archive.txt` before approving; overlap between the two files is a hard error.

---

**Source Spec:** `docs/superpowers/specs/2026-10-06-skill-index-optimization-design.md`
**Depends on (executed with deltas, not rewritten):** `docs/superpowers/plans/2026-09-26-skill-curation-gate.md`

## File Map

- Create: `scripts/curation/__init__.py` — package marker (also serves the gate plan's package).
- Create: `scripts/curation/skills.py` — `Skill` dataclass (with `description`), `discover_skills`, `frontmatter_span`, `est_tokens`. Single source of truth for discovery/measurement, shared by cleanup tools and the gate.
- Create: `scripts/test_curate.py` — unittest suite for `skills.py` now; Task 9 appends the gate's tests to it.
- Create: `scripts/inventory.py` — inventory report: per-skill rows, family/category flags, inert directories, broken relative references.
- Create: `scripts/propose.py` — heuristic rules → `.curation_review/` proposal files (archive list, active list, rewrite-needed list, proposed `curation.yaml`).
- Create: `scripts/archive_skills.py` — applies the approved archive list (dry-run by default, `--apply` to execute).
- Create: `scripts/rewrite_desc.py` — `extract` lists description offenders; `apply` applies the approved batch.
- Create: `scripts/test_index_tools.py` — unittest suite for the four cleanup tools.
- Modify: `gate_tests.py` — add a `CURATE` group that runs both suites as subprocesses.
- Modify: `.gitignore` — add `.curation_review/` (Task 4); `curation.yaml` and `.curation_stamp.json` (Task 9, per the gate plan).
- Task 9 only, per the gate plan: `scripts/curation/tiers.py`, `scripts/curation/config.py`, `scripts/curation/stamp.py`, `scripts/curate.py`, `curation.example.yaml`.
- Modify (Task 9): `docs/superpowers/specs/2026-09-26-skill-curation-gate-design.md` — status header pointing at the new spec.

---

### Task 1: Verify duplicate resolution is complete

The repo surgery from the gate plan's Task 1 was already committed in `c3cef3e`. This task verifies it and fixes the one remaining gap (if any): reachability of the folded-in `subagent-driven-development` assets.

**Files:**
- Verify: `systematic-debugging/` and `test-driven-development/` deleted, `subagent-driven-development/` root dir gone, assets under `software-development/subagent-driven-development/`
- Modify (only if missing): `software-development/subagent-driven-development/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a catalog where every skill `name` is unique — Task 9's `check` treats a collision as an error, so this must hold from here on.

- [ ] **Step 1: Confirm no name collisions remain**

Run:

```bash
cd /Users/xuyi/Source/skills
find . -name SKILL.md -not -path "./node_modules/*" -not -path "./.git/*" \
  -exec grep -m1 '^name:' {} + | awk '{print $2}' | sort | uniq -d
```

Expected: empty output (no duplicated `name:` values).

- [ ] **Step 2: Confirm the folded assets exist and are executable**

Run:

```bash
cd /Users/xuyi/Source/skills
ls software-development/subagent-driven-development/scripts
git ls-files -s software-development/subagent-driven-development/scripts
```

Expected: `review-package`, `sdd-workspace`, `task-brief` listed; each with mode `100755` in `git ls-files -s`. If any shows `100644`: `chmod +x <file> && git add <file>`.

- [ ] **Step 3: Confirm SKILL.md references every folded asset**

Run:

```bash
cd /Users/xuyi/Source/skills
grep -c -e 'references/implementer-prompt.md' -e 'references/task-reviewer-prompt.md' \
       -e 'scripts/task-brief' -e 'scripts/sdd-workspace' -e 'scripts/review-package' \
       software-development/subagent-driven-development/SKILL.md
```

Expected: `5`. If less, the `## References` section needs the missing bullets — read the section first and add only what's absent, using this form for each:

```markdown
- `scripts/task-brief` — extract one task's text from a plan into a file
```

- [ ] **Step 4: Commit any fixes**

```bash
cd /Users/xuyi/Source/skills
git status --short
```

If changes were made: `git add -A && git commit -m "fix: complete duplicate-skill resolution (asset reachability)"`. If nothing changed: no commit — note "Task 1: nothing to commit" in the run log.

---

### Task 2: Skill discovery with description measurement

The shared discovery module. The gate plan's Task 2 defines the same file; this version wins (it adds `description`), and Task 9 instructs the implementer to skip the gate plan's Task 2.

**Files:**
- Create: `scripts/curation/__init__.py`
- Create: `scripts/curation/skills.py`
- Create: `scripts/test_curate.py`

**Interfaces:**
- Consumes: nothing.
- Produces (Task 9 and every later task depend on these exact names):
  - `SKIP_DIRS: frozenset[str]` = `{"node_modules", "packages", "archive"}`
  - `TIER_ACTIVE = "active"`, `TIER_ARCHIVED = "archived"`, `VALID_TIERS = (TIER_ACTIVE, TIER_ARCHIVED)`
  - `class Skill` — frozen dataclass, fields `path: str`, `name: str`, `fm_chars: int`, `description: str = ""`, property `desc_chars: int`
  - `frontmatter_span(text: str) -> str | None`
  - `discover_skills(root: str) -> list[Skill]` — sorted by `path`, posix separators, dot-dirs and `SKIP_DIRS` excluded
  - `est_tokens(fm_chars: int) -> int` — `fm_chars // 4`

- [ ] **Step 1: Write the failing test file**

Create `scripts/test_curate.py`:

```python
"""Tests for skill discovery and the curation tool. Run: python3 scripts/test_curate.py"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import (
    Skill,
    discover_skills,
    est_tokens,
    frontmatter_span,
)


def write_skill(root, relpath, name, description="A skill."):
    path = os.path.join(root, relpath, "SKILL.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n")
    return path


class FrontmatterSpanTests(unittest.TestCase):
    def test_returns_none_without_frontmatter(self):
        self.assertIsNone(frontmatter_span("# just a heading\n"))

    def test_includes_both_delimiters(self):
        text = "---\nname: alpha\ndescription: Does a thing.\n---\n\n# Alpha\n"
        span = frontmatter_span(text)
        self.assertTrue(span.startswith("---\n"))
        self.assertTrue(span.endswith("---"))
        self.assertIn("name: alpha", span)

    def test_truncated_frontmatter_returns_none(self):
        self.assertIsNone(frontmatter_span("---\nname: alpha\nno closing delimiter"))


class EstimateTokensTests(unittest.TestCase):
    def test_is_chars_over_four(self):
        self.assertEqual(est_tokens(400), 100)
        self.assertEqual(est_tokens(401), 100)
        self.assertEqual(est_tokens(0), 0)


class DiscoverSkillsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_finds_top_level_and_nested_skills_sorted(self):
        write_skill(self.root, "zeta", "zeta")
        write_skill(self.root, "creative/alpha", "alpha")
        found = discover_skills(self.root)
        self.assertEqual([s.path for s in found], ["creative/alpha", "zeta"])

    def test_records_name_description_and_frontmatter_size(self):
        write_skill(self.root, "alpha", "alpha", "Does a thing.")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "alpha")
        self.assertEqual(skill.description, "Does a thing.")
        self.assertEqual(skill.desc_chars, len("Does a thing."))
        self.assertEqual(
            skill.fm_chars,
            len(frontmatter_span("---\nname: alpha\ndescription: Does a thing.\n---\n")),
        )

    def test_missing_description_defaults_to_empty(self):
        path = os.path.join(self.root, "nodesc")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: nodesc\n---\n\n# hi\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.description, "")
        self.assertEqual(skill.desc_chars, 0)

    def test_skips_dot_directories(self):
        write_skill(self.root, ".hidden/secret", "secret")
        self.assertEqual(discover_skills(self.root), [])

    def test_skips_node_modules_packages_and_archive(self):
        write_skill(self.root, "node_modules/dep", "dep")
        write_skill(self.root, "packages/core", "core")
        write_skill(self.root, "archive/old/skill", "oldskill")
        self.assertEqual(discover_skills(self.root), [])

    def test_nameless_skill_is_reported_with_empty_name(self):
        path = os.path.join(self.root, "broken")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("no frontmatter here\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.path, "broken")
        self.assertEqual(skill.name, "")

    def test_paths_use_posix_separators(self):
        write_skill(self.root, os.path.join("a", "b", "c"), "c")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.path, "a/b/c")


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 scripts/test_curate.py`
Expected: `ModuleNotFoundError: No module named 'curation'`

- [ ] **Step 3: Create the package and discovery module**

```bash
cd /Users/xuyi/Source/skills
mkdir -p scripts/curation
: > scripts/curation/__init__.py
```

Create `scripts/curation/skills.py`:

```python
"""Discovery and measurement of SKILL.md files in the catalog.

This module knows how to find skills and how large they are.
It knows nothing about tiers, manifests, or config files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

TIER_ACTIVE = "active"
TIER_ARCHIVED = "archived"
VALID_TIERS = (TIER_ACTIVE, TIER_ARCHIVED)

# node_modules and packages are build output; archive/ holds undiscoverable
# archived skills (SKILL.md renamed) and must never re-enter the index.
SKIP_DIRS = frozenset({"node_modules", "packages", "archive"})


@dataclass(frozen=True)
class Skill:
    """One discovered skill.

    path: repo-relative install path with posix separators, e.g. "creative/p5js"
    name: frontmatter name, or "" when the frontmatter has none
    fm_chars: size of the frontmatter including both --- delimiters
    description: frontmatter description value, or "" when absent
    """

    path: str
    name: str
    fm_chars: int
    description: str = ""

    @property
    def desc_chars(self) -> int:
        return len(self.description)


def frontmatter_span(text: str) -> str | None:
    """Return the frontmatter including both delimiters, or None if absent."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[: end + 4]


def _parse_frontmatter(span: str) -> dict:
    data = yaml.safe_load(span[3: span.rfind("---")])
    return data if isinstance(data, dict) else {}


def est_tokens(fm_chars: int) -> int:
    """Rough token count for a frontmatter of fm_chars characters."""
    return fm_chars // 4


def discover_skills(root: str) -> list[Skill]:
    """Return every skill under root, sorted by install path."""
    root = os.path.abspath(root)
    found: list[Skill] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        if "SKILL.md" not in filenames:
            continue
        with open(os.path.join(dirpath, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        span = frontmatter_span(text)
        data = _parse_frontmatter(span) if span else {}
        name = data.get("name")
        desc = data.get("description")
        rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
        found.append(
            Skill(
                path=rel,
                name=name.strip() if isinstance(name, str) else "",
                fm_chars=len(span) if span else 0,
                description=desc if isinstance(desc, str) else ("" if desc is None else str(desc)),
            )
        )
    return sorted(found, key=lambda s: s.path)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`
Expected: `Ran 11 tests` and `OK`

- [ ] **Step 5: Sanity-check against the real catalog and record the baseline**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills, est_tokens
s = discover_skills('.')
print('skills:', len(s))
print('total fm tokens:', est_tokens(sum(x.fm_chars for x in s)))
print('unnamed:', [x.path for x in s if not x.name])
print('desc>400:', [(x.path, x.desc_chars) for x in s if x.desc_chars > 400])
"
```

Expected: `skills: 135`, `total fm tokens` within a few tokens of **11013** (record the exact number — it is the "before" figure reported in Task 8), `unnamed: []`, and a `desc>400` list (record its length — that is the rewrite workload). If a name is missing or the skill count differs by more than 2, stop and investigate before continuing.

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curation/__init__.py scripts/curation/skills.py scripts/test_curate.py
git commit -m "feat: add skill discovery with description measurement"
```

---

### Task 3: Inventory report

**Files:**
- Create: `scripts/inventory.py`
- Test: `scripts/test_index_tools.py`

**Interfaces:**
- Consumes: `discover_skills`, `est_tokens` from `scripts/curation/skills.py` (Task 2).
- Produces (Task 4 reads these):
  - `inventory(root: str) -> dict` with keys `skills` (list of row dicts), `inert_dirs` (list of posix paths), `totals` (dict with `skills`, `fm_tokens`, `offenders`)
  - row dict keys: `path`, `name`, `desc_chars`, `fm_tokens`, `families` (list of family labels), `broken_refs` (list of relative refs that resolve nowhere)
  - CLI: `python3 scripts/inventory.py --root . --json .curation_review/inventory.json --md .curation_review/inventory.md`

- [ ] **Step 1: Write the failing tests**

Create `scripts/test_index_tools.py`:

```python
"""Tests for the index cleanup tools. Run: python3 scripts/test_index_tools.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inventory import FAMILIES, inert_dirs, inventory


def write_skill(root, relpath, name, description="A skill.", body=""):
    path = os.path.join(root, relpath, "SKILL.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n{body}\n")
    return path


class InertDirsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_dir_with_description_and_no_skill_is_inert(self):
        os.makedirs(os.path.join(self.root, "diagramming"))
        with open(os.path.join(self.root, "diagramming", "DESCRIPTION.md"), "w") as fh:
            fh.write("# diagramming\n")
        self.assertEqual(inert_dirs(self.root), ["diagramming"])

    def test_category_with_nested_skills_is_not_inert(self):
        with open(os.path.join(self.root, "DESCRIPTION.md"), "w") as fh:
            fh.write("# cat\n")
        write_skill(self.root, "cat/one", "one")
        self.assertEqual(inert_dirs(self.root), [])

    def test_archive_and_dot_dirs_are_ignored(self):
        os.makedirs(os.path.join(self.root, ".hidden"))
        with open(os.path.join(self.root, ".hidden", "DESCRIPTION.md"), "w") as fh:
            fh.write("x\n")
        os.makedirs(os.path.join(self.root, "archive", "old"))
        with open(os.path.join(self.root, "archive", "old", "DESCRIPTION.md"), "w") as fh:
            fh.write("x\n")
        self.assertEqual(inert_dirs(self.root), [])


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_rows_carry_description_and_token_counts(self):
        write_skill(self.root, "alpha", "alpha", "x" * 500)
        inv = inventory(self.root)
        (row,) = inv["skills"]
        from curation.skills import discover_skills, est_tokens
        (s,) = discover_skills(self.root)
        self.assertEqual(row["desc_chars"], 500)
        self.assertEqual(row["fm_tokens"], est_tokens(s.fm_chars))
        self.assertEqual(inv["totals"]["offenders"], 1)

    def test_family_membership_is_flagged(self):
        write_skill(self.root, "grill-me", "grill-me")
        inv = inventory(self.root)
        (row,) = inv["skills"]
        self.assertIn("grill", row["families"])

    def test_broken_relative_reference_is_flagged(self):
        write_skill(self.root, "alpha", "alpha", body="See `references/missing.md` for detail.")
        write_skill(self.root, "beta", "beta", body="See `references/exists.md` for detail.")
        os.makedirs(os.path.join(self.root, "beta", "references"))
        with open(os.path.join(self.root, "beta", "references", "exists.md"), "w") as fh:
            fh.write("ok\n")
        inv = inventory(self.root)
        rows = {r["path"]: r for r in inv["skills"]}
        self.assertEqual(rows["alpha"]["broken_refs"], ["references/missing.md"])
        self.assertEqual(rows["beta"]["broken_refs"], [])

    def test_external_and_absolute_refs_are_not_flagged(self):
        write_skill(self.root, "alpha", "alpha",
                    body="See [docs](https://example.com/a.md) and `~/x.md` and `/abs/y.md`.")
        inv = inventory(self.root)
        (row,) = inv["skills"]
        self.assertEqual(row["broken_refs"], [])

    def test_json_output_round_trips(self):
        write_skill(self.root, "alpha", "alpha")
        out = os.path.join(self.root, "out.json")
        subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.py"),
             "--root", self.root, "--json", out],
            check=True,
        )
        data = json.load(open(out))
        self.assertEqual(data["skills"][0]["path"], "alpha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 scripts/test_index_tools.py`
Expected: `ModuleNotFoundError: No module named 'inventory'`

- [ ] **Step 3: Write the inventory tool**

Create `scripts/inventory.py`:

```python
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
        print(f"inventory: {t['skills']} skills, {t['fm_tokens']} tokens, {t['offenders']} offenders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 scripts/test_index_tools.py`
Expected: `Ran 8 tests` and `OK`

- [ ] **Step 5: Run the inventory against the real catalog**

```bash
cd /Users/xuyi/Source/skills
mkdir -p .curation_review
python3 scripts/inventory.py --root . --json .curation_review/inventory.json --md .curation_review/inventory.md
```

Expected: prints `inventory: 135 skills, ~11013 tokens, N offenders` (N matches Task 2 Step 5). Then open `.curation_review/inventory.md` and spot-check: inert directories should include `diagramming`, `domain`, `email`, `gifs`, `inference-sh`, `smart-home` (plus any skill-less category stubs such as `mlops/training` — they follow the same rule and land in the same approval list).

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/inventory.py scripts/test_index_tools.py
git commit -m "feat: add skill inventory report"
```

---

### Task 4: Proposal generator

Turns inventory data into the three reviewable lists plus a proposed `curation.yaml`. This is where the heuristic rules live; every output is a proposal, not a decision.

**Files:**
- Create: `scripts/propose.py`
- Modify: `scripts/test_index_tools.py` — append `ProposeTests`
- Modify: `.gitignore` — add `.curation_review/`

**Interfaces:**
- Consumes: `inventory()`, `FAMILIES` from `scripts/inventory.py`; `discover_skills` from `scripts/curation/skills.py`.
- Produces (Tasks 5–7 read these files):
  - `.curation_review/archive.txt` — one path per line (skills and inert dirs), `#` comments allowed
  - `.curation_review/archive-reasons.tsv` — `path<TAB>reason`
  - `.curation_review/active.txt` — one skill path per line
  - `.curation_review/rewrite-needed.tsv` — `path<TAB>desc_chars` for active skills >400
  - `.curation_review/curation.proposed.yaml` — cascade manifest from the active list
  - CLI: `python3 scripts/propose.py --root . --archive-categories creative,media,gaming,red-teaming`

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_index_tools.py` (before `if __name__`):

```python
from curation.skills import discover_skills
from propose import FAMILY_KEEP, propose, to_manifest


def body_bytes(root, rel):
    total = 0
    for dirpath, _, filenames in os.walk(os.path.join(root, rel)):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total


class ProposeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.root, ".curation_review")
        os.makedirs(self.out)

    def test_category_members_and_inert_dirs_go_to_archive(self):
        write_skill(self.root, "creative/one", "one")
        write_skill(self.root, "grill-me", "grill-me")
        os.makedirs(os.path.join(self.root, "gifs"))
        with open(os.path.join(self.root, "gifs", "DESCRIPTION.md"), "w") as fh:
            fh.write("x\n")
        files = propose(self.root, archive_categories={"creative"}, out_dir=self.out)
        archive = set(l for l in files["archive"].splitlines() if l and not l.startswith("#"))
        active = set(l for l in files["active"].splitlines() if l and not l.startswith("#"))
        self.assertIn("creative/one", archive)
        self.assertIn("gifs", archive)
        self.assertIn("grill-me", active)
        self.assertNotIn("creative/one", active)

    def test_family_keeps_largest_by_body_bytes(self):
        write_skill(self.root, "grill-me", "grill-me", body="x" * 10)
        write_skill(self.root, "grilling", "grilling", body="y" * 500)
        write_skill(self.root, "grill-with-docs", "grill-with-docs", body="z" * 10)
        files = propose(self.root, archive_categories=set(), out_dir=self.out)
        active = files["active"].split()
        archive = files["archive"].split()
        self.assertEqual(FAMILY_KEEP["grill"], 1)
        self.assertIn("grilling", active)
        self.assertIn("grill-me", archive)
        self.assertIn("grill-with-docs", archive)

    def test_category_verdict_beats_family_membership(self):
        write_skill(self.root, "creative/claude-design", "claude-design", body="y" * 500)
        write_skill(self.root, "prototype", "prototype", body="x" * 10)
        files = propose(self.root, archive_categories={"creative"}, out_dir=self.out)
        self.assertIn("creative/claude-design", files["archive"])
        self.assertIn("prototype", files["active"])

    def test_rewrite_list_is_active_offenders_only(self):
        write_skill(self.root, "alpha", "alpha", description="x" * 500)
        write_skill(self.root, "creative/one", "one", description="y" * 500)
        files = propose(self.root, archive_categories={"creative"}, out_dir=self.out)
        paths = [l.split("\t")[0] for l in files["rewrite"].splitlines() if l]
        self.assertEqual(paths, ["alpha"])

    def test_manifest_groups_whole_categories(self):
        write_skill(self.root, "github/one", "one")
        write_skill(self.root, "github/two", "two")
        write_skill(self.root, "solo", "solo")
        write_skill(self.root, "creative/cut", "cut")
        files = propose(self.root, archive_categories={"creative"}, out_dir=self.out)
        active = files["active"].split()
        manifest = to_manifest(active, [s.path for s in discover_skills(self.root)])
        self.assertEqual(manifest["default"], "archived")
        self.assertEqual(manifest["categories"], {"github": "active"})
        self.assertIn("solo", manifest["skills"])
        self.assertNotIn("creative/cut", manifest["skills"])

    def test_missing_family_member_is_an_error(self):
        # FAMILIES lists prototype; it does not exist in this fixture tree
        write_skill(self.root, "grill-me", "grill-me")
        with self.assertRaises(SystemExit):
            propose(self.root, archive_categories=set(), out_dir=self.out)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 scripts/test_index_tools.py`
Expected: `ModuleNotFoundError: No module named 'propose'`

- [ ] **Step 3: Write the proposal tool**

Create `scripts/propose.py`:

```python
#!/usr/bin/env python3
"""Apply the heuristic rules and write proposal lists for user approval.

Outputs land in .curation_review/. Every file is hand-editable; overlap
between archive.txt and active.txt is a hard error, enforced here and
again by archive_skills.py.
"""

import argparse
import os
import pathlib
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import discover_skills
from inventory import FAMILIES, inventory

# family label -> how many members to keep (decided in the design; the
# *which* is decided by body size here and may be hand-edited afterwards)
FAMILY_KEEP = {"grill": 1, "design": 2, "review": 2, "understand": 2}

DESC_OFFENDER = 400


def body_bytes(root: str, rel: str) -> int:
    total = 0
    for dirpath, _, filenames in os.walk(os.path.join(root, rel)):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total


def to_manifest(active_paths: list[str], all_paths: list[str]) -> dict:
    """Cascade manifest: categories entry when every skill under the first
    path component is active, otherwise per-skill entries."""
    active = set(active_paths)
    by_cat: dict[str, list[str]] = {}
    all_by_cat: dict[str, list[str]] = {}
    for p in all_paths:
        all_by_cat.setdefault(p.split("/")[0], []).append(p)
    for p in active_paths:
        by_cat.setdefault(p.split("/")[0], []).append(p)
    categories: dict[str, str] = {}
    skills: dict[str, str] = {}
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

    # Rule 2: redundancy families, keep-ranked by body size (largest first)
    for label, members in FAMILIES.items():
        missing = [m for m in members if m not in known]
        if missing:
            sys.exit(f"error: family '{label}' member(s) not found: {', '.join(missing)}")
        keep = FAMILY_KEEP[label]
        eligible = [m for m in members if m not in reasons]
        ranked = sorted(eligible, key=lambda p: (-body_bytes(root, p), p))
        for p in ranked[keep:]:
            reasons[p] = f"rule 2: family '{label}' keep top {keep} by body size"

    archive_paths = sorted(reasons)
    # Complements by construction, so overlap is impossible here; hand-edited
    # lists are validated by archive_skills.py and the comm check in Task 5.
    active_paths = [p for p in all_paths if p not in reasons]

    # Rule 4: broken references among survivors (report only; fixing or
    # archiving is a decision made at approval time)
    broken_rows = [r for r in rows if r["path"] in set(active_paths) and r["broken_refs"]]
    broken_md = "# Broken references in surviving skills\n\n"
    broken_md += "\n".join(
        f"- `{r['path']}`: {', '.join('`' + b + '`' for b in r['broken_refs'])}"
        for r in broken_rows
    ) or "(none)\n"

    offenders = [
        (r["path"], r["desc_chars"]) for r in rows
        if r["path"] in set(active_paths) and r["desc_chars"] > DESC_OFFENDER
    ]

    os.makedirs(out_dir, exist_ok=True)
    files = {
        "archive": "\n".join(archive_paths) + "\n",
        "active": "\n".join(active_paths) + "\n",
        "rewrite": "\n".join(f"{p}\t{n}" for p, n in offenders) + ("\n" if offenders else ""),
        "reasons": "\n".join(f"{p}\t{reasons[p]}" for p in archive_paths) + "\n",
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
    files = propose(args.root, cats, args.out)
    n_arch = len(_lines(files["archive"]))
    n_act = len(_lines(files["active"]))
    n_rw = len([l for l in files["rewrite"].splitlines() if l])
    print(f"proposal: {n_act} active, {n_arch} archived, {n_rw} descriptions to rewrite")
    print(f"review and edit files in {args.out}/, then approve before applying")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 scripts/test_index_tools.py`
Expected: `Ran 14 tests` and `OK` (8 existing + 6 new).

- [ ] **Step 5: Add `.curation_review/` to `.gitignore`**

Append this line to `.gitignore`:

```
.curation_review/
```

Run: `git check-ignore .curation_review/inventory.json`
Expected: prints `.curation_review/inventory.json`

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/propose.py scripts/test_index_tools.py .gitignore
git commit -m "feat: add heuristic proposal generator for skill curation"
```

---

### Task 5: Generate and approve the proposal

No code. This is the checkpoint where the heuristic output becomes a human decision. The deliverable is approved list files.

**Files:**
- Read: `.curation_review/inventory.md`, `.curation_review/broken-refs.md`, `.curation_review/archive-reasons.tsv`
- Create (by editing): `.curation_review/archive.txt`, `.curation_review/active.txt`

**Interfaces:**
- Consumes: `scripts/propose.py` output (Task 4).
- Produces: approved `archive.txt` / `active.txt`, validated by the dry-run in Step 3 — Tasks 6 and 7 consume them unchanged.

- [ ] **Step 1: Run the proposal**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/propose.py --root . --archive-categories creative,media,gaming,red-teaming
```

Expected: `proposal: N active, M archived, K descriptions to rewrite` with **N ≤ 35**. If N > 35, add another category to `--archive-categories` (candidates not yet cut: `social-media`, `research`, `note-taking`, `data-science`) and re-run. Record the final command in the run log.

- [ ] **Step 2: Present the lists for approval (human gate)**

Show the user, in this order:

1. Active count vs. target: `wc -l .curation_review/active.txt` ≤ 35.
2. The full active list, with per-skill desc chars and family flags (`.curation_review/inventory.md`, filtered to active paths).
3. The archive list with reasons (`.curation_review/archive-reasons.tsv`).
4. Broken-reference report (`.curation_review/broken-refs.md`) — each entry is a fix-now (edit the reference) or archive decision; apply any fix by editing the skill, any archive by editing the two list files.
5. The family keep-rankings — the user may swap which member is kept by moving paths between `active.txt` and `archive.txt` (hand-edits are legitimate; re-running `propose.py` overwrites them, so do not re-run after approval starts).

Wait for explicit approval. The user may edit `active.txt` / `archive.txt` directly during this step. No file outside `.curation_review/` changes yet.

- [ ] **Step 3: Validate the approved lists**

Run:

```bash
cd /Users/xuyi/Source/skills
comm -12 <(sort .curation_review/active.txt | grep -v '^#') <(sort .curation_review/archive.txt | grep -v '^#')
```

Expected: empty output (no path on both lists). Any output = overlap; fix the lists and re-run until empty.

Then verify the active list is a subset of the real catalog:

```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills
known = {s.path for s in discover_skills('.')}
active = {l.strip() for l in open('.curation_review/active.txt') if l.strip() and not l.startswith('#')}
archive = {l.strip() for l in open('.curation_review/archive.txt') if l.strip() and not l.startswith('#')}
print('active not in catalog:', sorted(active - known - {d for d in archive if '/' not in d}))
print('counts:', len(active), 'active /', len(archive), 'archived')
"
```

Expected: `active not in catalog: []`, counts with active ≤ 35.

---

### Task 6: Archive executor

**Files:**
- Create: `scripts/archive_skills.py`
- Modify: `scripts/test_index_tools.py` — append `ArchiveTests`

**Interfaces:**
- Consumes: approved `.curation_review/archive.txt` and `.curation_review/active.txt` (Task 5).
- Produces: `archive/<path>/` trees whose skills have `SKILL.md.archived` instead of `SKILL.md`; `discover_skills()` no longer returns them. CLI: `python3 scripts/archive_skills.py --root . [--apply]` (dry-run without `--apply`).

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_index_tools.py` (before `if __name__`):

```python
from archive_skills import archive_paths


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.root, ".curation_review")
        os.makedirs(self.out)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def _git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True,
                       capture_output=True)

    def _commit_all(self):
        self._git("add", "-A")
        self._git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")

    def test_dry_run_changes_nothing(self):
        write_skill(self.root, "alpha", "alpha")
        self._commit_all()
        with open(os.path.join(self.out, "archive.txt"), "w") as fh:
            fh.write("alpha\n")
        errors = archive_paths(self.root, apply=False)
        self.assertEqual(errors, [])
        self.assertTrue(os.path.exists(os.path.join(self.root, "alpha", "SKILL.md")))

    def test_apply_moves_and_renames(self):
        write_skill(self.root, "alpha", "alpha")
        self._commit_all()
        with open(os.path.join(self.out, "archive.txt"), "w") as fh:
            fh.write("alpha\n")
        errors = archive_paths(self.root, apply=True)
        self.assertEqual(errors, [])
        self.assertTrue(os.path.exists(os.path.join(self.root, "archive", "alpha", "SKILL.md.archived")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "archive", "alpha", "SKILL.md")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "alpha")))
        from curation.skills import discover_skills
        self.assertEqual(discover_skills(self.root), [])

    def test_path_on_active_list_is_rejected(self):
        write_skill(self.root, "alpha", "alpha")
        self._commit_all()
        with open(os.path.join(self.out, "archive.txt"), "w") as fh:
            fh.write("alpha\n")
        with open(os.path.join(self.out, "active.txt"), "w") as fh:
            fh.write("alpha\n")
        errors = archive_paths(self.root, apply=True)
        self.assertTrue(any("active list" in e for e in errors))
        self.assertTrue(os.path.exists(os.path.join(self.root, "alpha", "SKILL.md")))

    def test_nested_archive_paths_are_rejected(self):
        write_skill(self.root, "cat/one", "one")
        self._commit_all()
        with open(os.path.join(self.out, "archive.txt"), "w") as fh:
            fh.write("cat\ncat/one\n")
        errors = archive_paths(self.root, apply=True)
        self.assertTrue(any("ancestor" in e for e in errors))
        self.assertTrue(os.path.exists(os.path.join(self.root, "cat", "one", "SKILL.md")))

    def test_missing_path_is_rejected(self):
        self._commit_all()
        with open(os.path.join(self.out, "archive.txt"), "w") as fh:
            fh.write("ghost\n")
        errors = archive_paths(self.root, apply=True)
        self.assertTrue(any("does not exist" in e for e in errors))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 scripts/test_index_tools.py`
Expected: `ModuleNotFoundError: No module named 'archive_skills'`

- [ ] **Step 3: Write the executor**

Create `scripts/archive_skills.py`:

```python
#!/usr/bin/env python3
"""Apply the approved archive list: move to archive/<path>/ and rename
SKILL.md -> SKILL.md.archived so discovery never sees it again.

Dry-run by default; --apply executes git mv operations. Any validation
error aborts the whole run — nothing is moved partially.
"""

import argparse
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REVIEW = ".curation_review"


def _read_list(path: pathlib.Path) -> list[str]:
    if not path.exists():
        sys.exit(f"error: {path} not found — run propose.py and approve first")
    return [
        l.strip() for l in path.read_text().splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]


def archive_paths(root: str, apply: bool) -> list[str]:
    """Validate and (optionally) execute the archive list.
    Returns a list of error strings; empty means success."""
    rootp = pathlib.Path(root)
    review = rootp / REVIEW
    archive_list = _read_list(review / "archive.txt")
    active = set(_read_list(review / "active.txt")) if (review / "active.txt").exists() else set()

    errors: list[str] = []
    for p in archive_list:
        if p in active:
            errors.append(f"{p}: listed on both archive.txt and active.txt")
        if p.startswith("archive/") or p == "archive":
            errors.append(f"{p}: already under archive/")
        src = rootp / p
        if not src.exists():
            errors.append(f"{p}: does not exist")
        for other in archive_list:
            if other != p and (other.startswith(p + "/")):
                errors.append(f"{p}: ancestor of '{other}' in the same list")
                break
    if errors:
        return sorted(set(errors))

    moved: list[tuple[list[str], list[str]]] = []
    for p in archive_list:
        src = rootp / p
        dest = rootp / "archive" / p
        cmds: list[list[str]] = []
        if (src / "SKILL.md").exists():
            cmds.append(["git", "mv", str(src / "SKILL.md"), str(src / "SKILL.md.archived")])
        cmds.append(["git", "mv", str(src), str(dest)])
        moved.append((cmds, [p]))

    if not apply:
        for cmds, (p,) in moved:
            for c in cmds:
                print("would run:", " ".join(c[1:3]), "... ->", c[-1])
        print(f"dry-run: {len(moved)} path(s); re-run with --apply to execute")
        return []

    for cmds, (p,) in moved:
        for c in cmds:
            r = subprocess.run(c, cwd=root, capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"error: {' '.join(c)}\n{r.stderr.strip()}")
        print(f"archived: {p} -> archive/{p}")
    print(f"{len(moved)} path(s) archived; review with: git status --short")
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true", help="execute (default is dry-run)")
    args = ap.parse_args(argv)
    errors = archive_paths(args.root, apply=args.apply)
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 scripts/test_index_tools.py`
Expected: `Ran 19 tests` and `OK`

- [ ] **Step 5: Dry-run against the approved lists**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/archive_skills.py --root .
```

Expected: prints `would run:` lines for every approved path, ending with `dry-run: N path(s)`. Cross-check N against `wc -l < .curation_review/archive.txt`. Zero validation errors. If any ERROR appears, fix the lists (Task 5 Step 3) — do not proceed.

- [ ] **Step 6: Show the dry-run summary to the user and get the go-ahead**

Present the dry-run line count and a sample of the moves. On approval:

```bash
cd /Users/xuyi/Source/skills
python3 scripts/archive_skills.py --root . --apply
git status --short | head -30
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills, est_tokens
s = discover_skills('.')
print('skills after archive:', len(s), 'tokens:', est_tokens(sum(x.fm_chars for x in s)))
"
```

Expected: each path prints `archived: ...`; `git status` shows renames (R) into `archive/`; discovery count drops by the number of archived skills that had a `SKILL.md`.

- [ ] **Step 7: Commit**

```bash
cd /Users/xuyi/Source/skills
git add -A
git commit -m "chore: archive skills cut by heuristic review"
```

---

### Task 7: Description rewrite batch

**Files:**
- Create: `scripts/rewrite_desc.py`
- Modify: `scripts/test_index_tools.py` — append `RewriteTests`
- Create (by approval): `.curation_review/rewrites.json`

**Interfaces:**
- Consumes: `.curation_review/active.txt` and current catalog state (post-Task-6).
- Produces: frontmatter descriptions rewritten in place for exactly the skills in the approved batch; `git diff` shows only `description:` lines changed.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_index_tools.py` (before `if __name__`):

```python
from rewrite_desc import apply_batch, extract_offenders, replace_description


class RewriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_extract_lists_only_offenders(self):
        write_skill(self.root, "long", "long", description="x" * 500)
        write_skill(self.root, "short", "short", description="ok")
        rows = extract_offenders(self.root)
        self.assertEqual([r[0] for r in rows], ["long"])

    def test_replace_single_line_description(self):
        text = "---\nname: a\ndescription: old text\nmetadata:\n  k: v\n---\n\nbody\n"
        new = replace_description(text, "New one-sentence description.")
        self.assertIn('description: "New one-sentence description."', new)
        self.assertIn("k: v", new)
        self.assertIn("body", new)

    def test_replace_block_scalar_description_falls_back(self):
        text = "---\nname: a\ndescription: >\n  old text spans\n  two lines\n---\n\nbody\n"
        new = replace_description(text, "New description.")
        self.assertIn("New description.", new)
        self.assertIn("body", new)

    def test_apply_rewrites_only_batch_members(self):
        write_skill(self.root, "alpha", "alpha", description="x" * 500)
        write_skill(self.root, "beta", "beta", description="y" * 500)
        batch = {"alpha": "Alpha does alpha things."}
        errors = apply_batch(self.root, batch, active={"alpha", "beta"})
        self.assertEqual(errors, [])
        text = open(os.path.join(self.root, "alpha", "SKILL.md")).read()
        self.assertIn("Alpha does alpha things.", text)
        beta = open(os.path.join(self.root, "beta", "SKILL.md")).read()
        self.assertIn("y" * 20, beta)

    def test_apply_rejects_non_offender_and_overlong(self):
        write_skill(self.root, "short", "short", description="ok")
        write_skill(self.root, "long", "long", description="x" * 500)
        errors = apply_batch(self.root, {"short": "Nope."}, active={"short", "long"})
        self.assertTrue(any("not an offender" in e for e in errors))
        errors = apply_batch(self.root, {"long": "z" * 401}, active={"short", "long"})
        self.assertTrue(any("exceeds 400" in e for e in errors))

    def test_apply_rejects_path_outside_active_list(self):
        write_skill(self.root, "cut", "cut", description="x" * 500)
        errors = apply_batch(self.root, {"cut": "New."}, active=set())
        self.assertTrue(any("not on the active list" in e for e in errors))

    def test_warns_when_over_target(self):
        write_skill(self.root, "long", "long", description="x" * 500)
        errors, warnings = apply_batch(self.root, {"long": "y" * 161}, active={"long"}, return_warnings=True)
        self.assertEqual(errors, [])
        self.assertTrue(any("over the 160" in w for w in warnings))
```

Note: `apply_batch` must accept `return_warnings=False`; when true it returns `(errors, warnings)`. The test in Step 1 calls it both ways — implement that signature in Step 3.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 scripts/test_index_tools.py`
Expected: `ModuleNotFoundError: No module named 'rewrite_desc'`

- [ ] **Step 3: Write the rewrite tool**

Create `scripts/rewrite_desc.py`:

```python
#!/usr/bin/env python3
"""Extract description offenders and apply an approved rewrite batch.

extract: list active skills whose frontmatter description exceeds 400 chars.
apply: rewrite exactly the skills named in the batch JSON (path -> new
description), validating offender status, the active list, and length.
No file is touched unless every entry in the batch validates.
"""

import argparse
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import discover_skills, frontmatter_span

OFFENDER = 400
TARGET = 160
REVIEW = ".curation_review"


def extract_offenders(root: str) -> list[tuple[str, int]]:
    return sorted(
        (s.path, s.desc_chars) for s in discover_skills(root) if s.desc_chars > OFFENDER
    )


def replace_description(text: str, new_desc: str) -> str:
    span = frontmatter_span(text)
    if span is None:
        raise ValueError("no frontmatter")
    lines = span.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith("description:")), None)
    if idx is None:
        raise ValueError("no description line in frontmatter")
    value = lines[idx][len("description:"):].strip()
    if value and not value.startswith((">", "|")):
        lines[idx] = "description: " + json.dumps(new_desc)
        new_span = "\n".join(lines)
    else:
        # block scalar or empty: round-trip the mapping (may normalize quoting)
        data = yaml.safe_load(span[3: span.rfind("---")])
        data["description"] = new_desc
        new_span = "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip("\n") + "\n---"
    return text[: text.index(span)] + new_span + text[text.index(span) + len(span):]


def apply_batch(root: str, batch: dict[str, str], active: set[str],
                return_warnings: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    offenders = {p for p, _ in extract_offenders(root)}
    for path, new in batch.items():
        if path not in active:
            errors.append(f"{path}: not on the active list")
            continue
        if path not in offenders:
            errors.append(f"{path}: not an offender (description already <= {OFFENDER} chars)")
            continue
        if len(new) > OFFENDER:
            errors.append(f"{path}: new description is {len(new)} chars, exceeds {OFFENDER}")
            continue
        if len(new) > TARGET:
            warnings.append(f"{path}: {len(new)} chars is over the {TARGET} target")
    if errors:
        return (errors, warnings) if return_warnings else errors

    for path, new in batch.items():
        p = os.path.join(root, path, "SKILL.md")
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(replace_description(text, new))
    return (errors, warnings) if return_warnings else errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract", help="list offenders")
    ex.add_argument("--root", default=".")
    ex.add_argument("--out", default=f"{REVIEW}/rewrite-needed.tsv")
    ap_run = sub.add_parser("apply", help="apply approved batch")
    ap_run.add_argument("--root", default=".")
    ap_run.add_argument("--batch", default=f"{REVIEW}/rewrites.json")
    ap_run.add_argument("--active", default=f"{REVIEW}/active.txt")
    args = ap.parse_args(argv)

    if args.cmd == "extract":
        rows = extract_offenders(args.root)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("".join(f"{p}\t{n}\n" for p, n in rows))
        print(f"{len(rows)} offenders written to {args.out}")
        return 0

    with open(args.batch, encoding="utf-8") as fh:
        batch = json.load(fh)
    active = {
        l.strip() for l in open(args.active, encoding="utf-8")
        if l.strip() and not l.startswith("#")
    } if os.path.exists(args.active) else {s.path for s in discover_skills(args.root)}
    errors, warnings = apply_batch(args.root, batch, active, return_warnings=True)
    for w in warnings:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        return 1
    print(f"{len(batch)} description(s) rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 scripts/test_index_tools.py`
Expected: `Ran 26 tests` and `OK`

- [ ] **Step 5: Extract the current offender list (post-archive)**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/rewrite_desc.py extract --root .
cat .curation_review/rewrite-needed.tsv
```

Expected: prints `N offenders written to ...`; N equals the count of active skills with description >400 after Task 6. If N is 0, skip to Step 8.

- [ ] **Step 6: Author the batch and get it approved (human gate)**

Draft one new description per offender into `.curation_review/rewrites.json` — a JSON object mapping install path to the new description string. Drafting rules (from the spec): one sentence, ≤160 characters, concrete trigger ("Use when…") plus core capability; the skill body is the source of truth — read each skill's opening section before writing its description.

Example entry (illustrative only — every real entry is written from the actual skill body):

```json
{
  "creative/p5js": "Use when building p5.js sketches: generative art, shaders, interactive and 3D sketches."
}
```

Present the batch as a before/after table to the user (path, old length from `rewrite-needed.tsv`, new text, new length) and wait for explicit approval of the whole batch. Edit only `.curation_review/rewrites.json` during this step.

- [ ] **Step 7: Apply the approved batch and verify it touched nothing else**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/rewrite_desc.py apply --root .
git diff -U0 | grep -E '^[-+][^-+]' | grep -v 'description:' | grep -v '^[-+]---'
```

Expected: apply prints `N description(s) rewritten` with no WARN/ERROR lines; the verification grep prints **nothing** — every changed line is a `description:` line or a frontmatter delimiter. Investigate any other output before committing (a block-scalar fallback normalizes frontmatter formatting; if that shows up, inspect the diff manually and confirm it only affects the description key's block).

- [ ] **Step 8: Commit**

```bash
cd /Users/xuyi/Source/skills
git add -A
git commit -m "feat: rewrite oversized skill descriptions from approved batch"
```

---

### Task 8: Post-cleanup measurement and gate test wiring

**Files:**
- Modify: `gate_tests.py` — add `CURATE` group

**Interfaces:**
- Consumes: `scripts/test_curate.py` (Task 2), `scripts/test_index_tools.py` (Tasks 3–7).
- Produces: the "after" measurement recorded for the spec's success criteria; a single command that runs both suites through the repo's existing test entry point.

- [ ] **Step 1: Add the CURATE group to `gate_tests.py`**

In `gate_tests.py`, change the group line:

```python
GROUPS = ("T1", "T2", "PASSSTR", "FM")
```

to:

```python
GROUPS = ("T1", "T2", "PASSSTR", "FM", "CURATE")
```

Immediately before the `# ---------- report ----------` line, append:

```python
# ---------- curation / cleanup tool suites ----------
if "CURATE" in SELECT:
    import subprocess

    here = os.path.dirname(os.path.abspath(__file__))
    for suite in ("test_curate.py", "test_index_tools.py"):
        r = subprocess.run(
            [sys.executable, os.path.join("scripts", suite)],
            capture_output=True, text=True, cwd=here,
        )
        check(
            f"CURATE {suite} passes",
            r.returncode == 0,
            (r.stdout + r.stderr)[-600:],
        )
```

Also ensure `import os` is present in the imports at the top of `gate_tests.py` (it currently imports `pathlib`, `re`, `sys` — add `os` if missing).

- [ ] **Step 2: Run the full gate test entry point**

Run: `python3 gate_tests.py`
Expected: last line like `T1 T2 PASSSTR FM CURATE: N/N passed, 0 failed`, exit code 0. If the CURATE checks fail, the detail bracket shows the tail of the failing suite's output — run that suite directly for the full traceback.

- [ ] **Step 3: Measure the after-state and report**

```bash
cd /Users/xuyi/Source/skills
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills, est_tokens
s = discover_skills('.')
print('active:', len(s))
print('fm tokens:', est_tokens(sum(x.fm_chars for x in s)))
print('over 400 chars:', [(x.path, x.desc_chars) for x in s if x.desc_chars > 400])
print('under archive/:', __import__('glob').glob('archive/*/SKILL.md') + __import__('glob').glob('archive/*/*/SKILL.md'))
"
```

Expected: `active` ≤ 35, `fm tokens` ≤ 3000, `over 400 chars: []`, `under archive/: []`. If `fm tokens` > 3000, the remaining excess is description length — draft another approved batch (Task 7 Steps 5–7) until the count fits. Record before (Task 2) and after numbers in the run log; these are the spec's success-criterion figures.

- [ ] **Step 4: Commit**

```bash
cd /Users/xuyi/Source/skills
git add gate_tests.py
git commit -m "test: wire index tool suites into gate_tests CURATE group"
```

---

### Task 9: Implement the curation gate over the reduced catalog

The gate's design and full implementation plan already exist. Execute **Tasks 3, 4, 5, 6, 7** of `docs/superpowers/plans/2026-09-26-skill-curation-gate.md`, applying the deltas below. **Do not execute its Tasks 1 and 2** — Task 1 of this plan verified that work is done, and Task 2 here already built `scripts/curation/skills.py` (with `description` added).

**Files:**
- Create (per the gate plan): `scripts/curation/tiers.py`, `scripts/curation/config.py`, `scripts/curation/stamp.py`, `scripts/curate.py`, `curation.example.yaml`
- Modify: `scripts/test_curate.py` — **append** the gate plan's test classes to this existing file; never recreate it (its discovery tests must keep passing)
- Modify: `.gitignore` — add `curation.yaml` and `.curation_stamp.json`
- Modify: `docs/superpowers/specs/2026-09-26-skill-curation-gate-design.md` — status header (Step 6)

**Interfaces:**
- Consumes: `scripts/curation/skills.py` (Task 2) with the exact names listed there; the approved active list `.curation_review/active.txt`.
- Produces: `scripts/curate.py` with `plan` / `sync` / `check`, a marked `permission.skill` region in `~/.config/opencode/opencode.jsonc`, and `curation.yaml` seeded from the approved list.

- [ ] **Step 1: Execute gate plan Tasks 3–7 with these deltas**

Delta list (each overrides the gate plan's text):

1. **`skills.py` and discovery tests already exist.** Skip the gate plan's Task 2 entirely. Its test file (`scripts/test_curate.py`) exists with 11 discovery tests — append new test classes to it (`python3 scripts/test_curate.py` must end green after every gate task).
2. **`Skill` has a fourth field.** `Skill(path, name, fm_chars, description="")` — any test in the gate plan that constructs a `Skill` positionally still works (3 args); do not remove the `description` field.
3. **`SKIP_DIRS` includes `archive`**, so archived skills never enter token counts. Do not remove `archive` from it.
4. **Seeding `curation.yaml` (gate plan Task 7, manifest seeding step):** instead of hand-writing the manifest, run:

   ```bash
   cp .curation_review/curation.proposed.yaml curation.yaml
   ```

   That file was generated from the approved active list in Task 4 and matches the cascade schema. If the user hand-edited `active.txt` after Step 4 of Task 4, regenerate first:

   ```bash
   python3 scripts/propose.py --root . --archive-categories creative,media,gaming,red-teaming
   cp .curation_review/curation.proposed.yaml curation.yaml
   ```

   (Re-running propose overwrites hand-edits — only do this when the active list itself changed, and show the diff of `active.txt` before re-running.)

5. **`check` gains four assertions.** Add them to the `check` implementation (gate plan Task 6), after its existing checks, with these exact behaviors — write the corresponding tests by appending to `scripts/test_curate.py`:

   ```python
   # --- index budget assertions (skill-index-optimization spec) ---
   ACTIVE_CAP = 35
   TOKEN_BUDGET = 3000
   DESC_CAP = 400

   # 1. No SKILL.md may exist under archive/ (archived = undiscoverable)
   import glob as _glob
   leaked = sorted(
       os.path.relpath(p, root).replace(os.sep, "/")
       for p in _glob.glob(os.path.join(root, "archive", "**", "SKILL.md"), recursive=True)
   )
   if leaked:
       errors.append("archived skill is discoverable (SKILL.md present): " + ", ".join(leaked))

   # 2. Active set stays within the cap
   active_skills = [s for s in skills if tier_of(s) == TIER_ACTIVE]  # use the resolved cascade
   if len(active_skills) > ACTIVE_CAP:
       errors.append(f"active set has {len(active_skills)} skills, cap is {ACTIVE_CAP}")

   # 3. No active description exceeds the cap
   over = [f"{s.path} ({s.desc_chars})" for s in active_skills if s.desc_chars > DESC_CAP]
   if over:
       errors.append("active description over 400 chars: " + ", ".join(over))

   # 4. Active frontmatter stays within the token budget
   total = est_tokens(sum(s.fm_chars for s in active_skills))
   if total > TOKEN_BUDGET:
       errors.append(f"active frontmatter is {total} tokens, budget is {TOKEN_BUDGET}")
   ```

   Fit these into the gate plan's error-reporting style: every condition is a named message, never a stack trace, and `check` exits non-zero when any fires. (`skills` = the discovery result from `curation.skills.discover_skills`; wire the resolved tier per skill through whatever the gate plan's `resolve_tiers` returns — the names come from its Task 3.)

6. **Test additions for the four assertions** (append to `scripts/test_curate.py`): a fixture tree with 36 active skills → error; 34 active + `archive/x/SKILL.md` → error; an active skill with a 401-char description → error; active tokens over 3000 → error. Each as its own `test_` method asserting the message substring appears in `check`'s failure output.

- [ ] **Step 2: Green after every gate task**

After each gate-plan task (3, 4, 5, 6, 7) completes:

```bash
cd /Users/xuyi/Source/skills
python3 scripts/test_curate.py && python3 scripts/test_index_tools.py
```

Expected: both suites `OK`. `test_index_tools.py` must stay green — the gate work does not change cleanup tooling.

- [ ] **Step 3: First sync and drift check**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/curate.py plan
python3 scripts/curate.py sync
python3 scripts/curate.py check
```

Expected: `plan` prints active/archive counts matching the approved lists and a token figure ≤3000; `sync` writes the marked region into `~/.config/opencode/opencode.jsonc`; `check` exits 0. Re-run `check` — still 0 (idempotence).

Inspect the config region:

```bash
grep -A3 'curated by scripts/curate.py' ~/.config/opencode/opencode.jsonc | head -8
grep -c '"allow"' ~/.config/opencode/opencode.jsonc
```

Expected: markers present; allow-count equals the active count.

- [ ] **Step 4: Confirm hand-written config survived**

```bash
cd /Users/xuyi/Source/skills
git diff --stat  # config is outside the repo; instead:
python3 -c "
import pathlib
t = pathlib.Path.home().joinpath('.config/opencode/opencode.jsonc').read_text()
assert '\"ollama\"' in t and '\"omniroute\"' in t and '\"disabled_providers\"' in t
print('provider blocks intact')
"
```

Expected: `provider blocks intact`.

- [ ] **Step 5: Run the repo's full test entry point**

Run: `python3 gate_tests.py`
Expected: `... CURATE: N/N passed, 0 failed`, exit 0.

- [ ] **Step 6: Annotate the superseded spec**

Edit `docs/superpowers/specs/2026-09-26-skill-curation-gate-design.md`: change the `**Status:**` line to:

```
**Status:** Superseded in part by `2026-10-06-skill-index-optimization-design.md` (physical archiving and token targets added; non-goals on catalog completeness and token cost amended). Mechanism unchanged; implementation plan remains authoritative for build steps.
```

- [ ] **Step 7: Commit**

```bash
cd /Users/xuyi/Source/skills
git add .gitignore scripts/ curation.example.yaml docs/
git commit -m "feat: add curation gate enforcing cleaned skill index"
```

(`curation.yaml` and `.curation_stamp.json` must NOT appear — they are gitignored; verify with `git status --short` before committing.)

---

### Task 10: Final verification

No new code. Runs the spec's Verification section end to end.

**Files:**
- Read: `docs/superpowers/specs/2026-10-06-skill-index-optimization-design.md` (Verification and Success Criteria sections)

- [ ] **Step 1: Run every check**

```bash
cd /Users/xuyi/Source/skills
python3 scripts/curate.py check && echo CHECK_OK
python3 gate_tests.py && echo SUITES_OK
python3 -c "
import sys, glob; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills, est_tokens
s = discover_skills('.')
assert len(s) <= 35, len(s)
assert est_tokens(sum(x.fm_chars for x in s)) <= 3000
assert not [x for x in s if x.desc_chars > 400]
assert not glob.glob('archive/**/SKILL.md', recursive=True)
names = [x.name for x in s]
assert len(names) == len(set(names)), 'collision'
print('SUCCESS CRITERIA OK:', len(s), 'skills,', est_tokens(sum(x.fm_chars for x in s)), 'tokens')
"
```

Expected: `CHECK_OK`, `SUITES_OK`, `SUCCESS CRITERIA OK: N skills, M tokens` with N ≤ 35, M ≤ 3000.

- [ ] **Step 2: Restart opencode and confirm the visible index**

Restart the opencode session, then confirm `<available_skills>` contains only the active skills and none of the archived ones (spot-check three archived paths, e.g. a `creative/` skill and one grill-family cut).

- [ ] **Step 3: Denial hand-check (once)**

Attempt to load an archived/denied skill by name. Expected: access rejected (opencode documents `deny` as hidden and access-rejected). Then promote a throwaway skill in `curation.yaml`, run `python3 scripts/curate.py sync`, restart, confirm it appears; remove it, re-sync, confirm it disappears — the promotion drill from the spec's Verification §8.

- [ ] **Step 4: Recovery spot-check**

Pick three archived skills and confirm recoverability:

```bash
cd /Users/xuyi/Source/skills
git log --oneline --follow -- archive/<one-of-the-three>/SKILL.md.archived | head -3
```

Expected: history reaches back through the move; restoring is `git mv` back plus renaming the file to `SKILL.md`.

- [ ] **Step 5: Report results**

Summarize for the user: before/after skill counts and tokens (Task 2 vs. Task 8 figures), active list size, `check` status, and the archived count — against the spec's Success Criteria checklist.
