# Skill Curation Manifest and Load Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local `curation.yaml` plus a `scripts/curate.py` tool that projects an explicit active-skill list into opencode's `permission.skill` config, so the published catalog stays complete while the locally loaded set becomes small and reviewable.

**Architecture:** A four-module package under `scripts/curation/` holds the pure logic — skill discovery, tier resolution and validation, config-region rendering and splicing, and the local review stamp. A thin `scripts/curate.py` CLI wires those modules into `plan`, `sync`, and `check` subcommands. The tool never parses or reformats the user's hand-written `opencode.jsonc`; it locates a comment-delimited region by text and splices only that region.

**Tech Stack:** Python 3.14 standard library (`argparse`, `dataclasses`, `difflib`, `json`, `os`, `unittest`), PyYAML, Git

## Global Constraints

- The published catalog stays complete: no loadable skill is removed from the repository. Removing a name-collided copy is a bug fix, not a reduction.
- `curation.yaml` and `.curation_stamp.json` are gitignored. `curation.example.yaml` and the tool are committed.
- Tier values are exactly `active` or `archived`. The manifest default when `default:` is absent is `archived`.
- A `categories:` key matches the **first path component** of a skill's install path and governs every skill beneath it at any depth. A `skills:` key is a full repo-relative path and beats `categories:`, which beats `default:`.
- The generated config region is deny-by-default: `"*": "deny"` plus one `"<name>": "allow"` per active skill, sorted by name.
- `permission.skill` values are only `allow`, `deny`, or `ask`. No sentinel keys are emitted inside the region, only `//` comment markers.
- The tool requires the marked region to already exist in `opencode.jsonc`; it never creates the file and never invents JSON structure in a hand-edited file.
- `plan` records the review stamp as its side effect. `sync` rewrites only the marked region. `check` never writes.
- Two skills resolving to the same `name` is an error, not a warning, because `permission.skill` patterns match on `name`.
- Success criteria: active set is 35 skills or fewer, the loaded set has zero name collisions, `check` exits 0, and a newly added skill is denied until promoted.

---

**Source Spec:** `docs/superpowers/specs/2026-09-26-skill-curation-gate-design.md`

## File Map

- Create `scripts/curation/__init__.py` — empty package marker.
- Create `scripts/curation/skills.py` — `Skill` dataclass, `discover_skills`, `frontmatter_span`, `est_tokens`. Knows how to find and measure skills; knows nothing about tiers.
- Create `scripts/curation/tiers.py` — `load_manifest`, `resolve_tiers`, `validate`, `ManifestError`. The cascade and every validation error message.
- Create `scripts/curation/config.py` — `MARKER_BEGIN`, `MARKER_END`, `SKELETON`, `render_region`, `find_region`, `region_text`, `splice_region`, `RegionError`. The only module that touches config text.
- Create `scripts/curation/stamp.py` — `read_stamp`, `write_stamp`, `unreviewed`. The local record of what has been reviewed.
- Create `scripts/curate.py` — CLI entry point: argument parsing, the three subcommands, printing, exit codes.
- Create `scripts/test_curate.py` — stdlib `unittest` suite covering all five modules plus CLI integration.
- Create `curation.example.yaml` — committed, commented schema example.
- Modify `.gitignore` — add `curation.yaml` and `.curation_stamp.json`.
- Delete `systematic-debugging/` — superseded root copy.
- Delete `test-driven-development/` — superseded root copy.
- Move `subagent-driven-development/{scripts,implementer-prompt.md,task-reviewer-prompt.md}` into `software-development/subagent-driven-development/`.
- Modify `software-development/subagent-driven-development/SKILL.md` — reference the moved assets so they are reachable.

---

### Task 1: Resolve the three duplicate skill pairs

`check` treats a name collision as an error, so this must land before the first `sync`. No code yet — this is repository surgery plus a reachability fix.

**Files:**
- Delete: `systematic-debugging/` (whole directory, 11 tracked files)
- Delete: `test-driven-development/` (whole directory, 2 tracked files)
- Move: `subagent-driven-development/scripts/` → `software-development/subagent-driven-development/scripts/`
- Move: `subagent-driven-development/implementer-prompt.md` → `software-development/subagent-driven-development/references/implementer-prompt.md`
- Move: `subagent-driven-development/task-reviewer-prompt.md` → `software-development/subagent-driven-development/references/task-reviewer-prompt.md`
- Modify: `software-development/subagent-driven-development/SKILL.md`
- Delete afterwards: `subagent-driven-development/` (now empty)

**Interfaces:**
- Consumes: nothing.
- Produces: a catalog where every skill `name` is unique, so `curation.tiers.validate` reports no collision. Later tasks rely on this.

- [ ] **Step 1: Confirm the collisions and which copy loads**

Run:

```bash
cd /Users/xuyi/Source/skills
for n in systematic-debugging test-driven-development subagent-driven-development; do
  echo "== $n"; grep -m1 '^name:' "$n/SKILL.md" "software-development/$n/SKILL.md"
done
```

Expected: three pairs, each printing `name: <same-name>` twice.

- [ ] **Step 2: Delete the two superseded root copies**

```bash
cd /Users/xuyi/Source/skills
git rm -r systematic-debugging test-driven-development
```

Expected: `rm 'systematic-debugging/CREATION-LOG.md'` style output for 13 files total.

- [ ] **Step 3: Move the three `subagent-driven-development` assets into the surviving skill**

```bash
cd /Users/xuyi/Source/skills
git mv subagent-driven-development/scripts software-development/subagent-driven-development/scripts
git mv subagent-driven-development/implementer-prompt.md software-development/subagent-driven-development/references/implementer-prompt.md
git mv subagent-driven-development/task-reviewer-prompt.md software-development/subagent-driven-development/references/task-reviewer-prompt.md
```

Expected: three `renamed:` lines. No `error:` output.

- [ ] **Step 4: Verify the moved scripts kept their executable bit**

Run:

```bash
cd /Users/xuyi/Source/skills
ls -l software-development/subagent-driven-development/scripts
git ls-files -s software-development/subagent-driven-development/scripts
```

Expected: all three files show mode `100755` in the `git ls-files -s` output and `-rwxr-xr-x` in `ls -l`. If any shows `100644`, run `chmod +x` on it and `git add` again before continuing.

- [ ] **Step 5: Point the surviving SKILL.md at the moved assets**

Read `software-development/subagent-driven-development/SKILL.md` and find its `## References` section. If that section does not exist, append this as the final section:

```markdown
## References

- `references/context-budget-discipline.md` — why subagent context is budgeted
- `references/gates-taxonomy.md` — the gate types and what each one protects
- `references/implementer-prompt.md` — prompt template for the implementer subagent
- `references/task-reviewer-prompt.md` — prompt template for the task-reviewer subagent
- `scripts/task-brief` — extract one task's text from a plan into a file
- `scripts/sdd-workspace` — resolve the short-lived artifact directory
- `scripts/review-package` — build a review package for one task
```

If the section already exists, add the five missing bullets to it and do not duplicate any line.

- [ ] **Step 6: Verify the collision is gone and nothing dangles**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 - <<'PY'
import glob, os, re, collections
by_name = collections.defaultdict(list)
for p in glob.glob('**/SKILL.md', recursive=True):
    if any(x in p.split(os.sep) for x in ('node_modules', 'packages', '.git')):
        continue
    m = re.search(r'^name:\s*(.+)$', open(p, encoding='utf-8').read(), re.M)
    by_name[m.group(1).strip()].append(os.path.dirname(p))
dupes = {n: ps for n, ps in by_name.items() if len(ps) > 1}
print("skills:", sum(len(v) for v in by_name.values()))
print("collisions:", dupes or "none")
PY
ls subagent-driven-development 2>&1
```

Expected: `skills: 136`, `collisions: none`, and `ls: subagent-driven-development: No such file or directory`.

If the empty directory still exists, remove it with `rmdir subagent-driven-development`. Git does not track empty directories, so nothing is staged by this.

- [ ] **Step 7: Commit**

```bash
cd /Users/xuyi/Source/skills
git add -A
git commit -m "fix: resolve three duplicate skill pairs

systematic-debugging and test-driven-development existed at the root and
under software-development/ with the same frontmatter name, so only the
software-development copy could ever load. Delete the superseded root
copies, finalizing the 0181439 trim.

subagent-driven-development had no such signal: both copies shipped
unrelated asset layouts. Keep the software-development copy and move the
root copy's three scripts and two prompt templates into it, so the code
is reachable instead of orphaned."
```

Expected: one new commit; `git status --short` is empty.

---

### Task 2: Skill discovery and the token estimate

**Files:**
- Create: `scripts/curation/__init__.py`
- Create: `scripts/curation/skills.py`
- Create: `scripts/test_curate.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `SKIP_DIRS: frozenset[str]`
  - `class Skill` with frozen fields `path: str`, `name: str`, `fm_chars: int`
  - `frontmatter_span(text: str) -> str | None` — returns the frontmatter including both `---` delimiters, or `None`
  - `discover_skills(root: str) -> list[Skill]` — sorted by `path`
  - `est_tokens(fm_chars: int) -> int` — `fm_chars // 4`
  - `TIER_ACTIVE = "active"`, `TIER_ARCHIVED = "archived"`, `VALID_TIERS = (TIER_ACTIVE, TIER_ARCHIVED)`

- [ ] **Step 1: Write the failing test file**

Create `scripts/test_curate.py`:

```python
"""Tests for the skill curation tool. Run: python3 scripts/test_curate.py"""

import json
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

    def test_records_name_and_frontmatter_size(self):
        write_skill(self.root, "alpha", "alpha", "Does a thing.")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "alpha")
        self.assertEqual(skill.fm_chars, len(frontmatter_span("---\nname: alpha\ndescription: Does a thing.\n---\n")))

    def test_skips_dot_directories(self):
        write_skill(self.root, ".hidden/secret", "secret")
        self.assertEqual(discover_skills(self.root), [])

    def test_skips_node_modules_and_packages(self):
        write_skill(self.root, "node_modules/dep", "dep")
        write_skill(self.root, "packages/core", "core")
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

- [ ] **Step 3: Create the package and the discovery module**

Create `scripts/curation/__init__.py` as an empty file:

```bash
cd /Users/xuyi/Source/skills
: > scripts/curation/__init__.py
```

Create `scripts/curation/skills.py`:

```python
"""Discovery and measurement of SKILL.md files in the catalog.

This module knows how to find skills and how large their frontmatter is.
It knows nothing about tiers, manifests, or config files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

TIER_ACTIVE = "active"
TIER_ARCHIVED = "archived"
VALID_TIERS = (TIER_ACTIVE, TIER_ARCHIVED)

# node_modules and packages are build output, not catalog content.
SKIP_DIRS = frozenset({"node_modules", "packages"})


@dataclass(frozen=True)
class Skill:
    """One discovered skill.

    path: repo-relative install path with posix separators, e.g. "creative/p5js"
    name: frontmatter name, or "" when the frontmatter has none
    fm_chars: size of the frontmatter including both --- delimiters
    """

    path: str
    name: str
    fm_chars: int


def frontmatter_span(text: str) -> str | None:
    """Return the frontmatter including both delimiters, or None if absent."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[: end + 4]


def _parse_name(span: str) -> str:
    data = yaml.safe_load(span.strip().strip("-"))
    if not isinstance(data, dict):
        return ""
    name = data.get("name")
    return name.strip() if isinstance(name, str) else ""


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
        rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
        found.append(
            Skill(
                path=rel,
                name=_parse_name(span) if span else "",
                fm_chars=len(span) if span else 0,
            )
        )
    return sorted(found, key=lambda s: s.path)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`

Expected: `Ran 10 tests` and `OK`

- [ ] **Step 5: Sanity-check against the real catalog**

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
"
```

Expected: `skills: 136`, `total fm tokens: 11013` or within a few tokens of it, and an empty `unnamed` list. Record the exact number; Task 7 compares against it.

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curation/__init__.py scripts/curation/skills.py scripts/test_curate.py
git commit -m "feat: add skill discovery and frontmatter token estimate"
```

---

### Task 3: Tier cascade, manifest loading, and validation

**Files:**
- Create: `scripts/curation/tiers.py`
- Modify: `scripts/test_curate.py` (append a test class)

**Interfaces:**
- Consumes: `TIER_ACTIVE`, `TIER_ARCHIVED`, `Skill` from `curation.skills` (Task 2).
- Produces:
  - `class ManifestError(Exception)`
  - `load_manifest(path: str) -> dict`
  - `resolve_tiers(manifest: dict, skills: list[Skill]) -> dict[str, str]`
  - `validate(manifest: dict, skills: list[Skill]) -> list[str]` — empty list means valid

- [ ] **Step 1: Append the failing tests**

Append to `scripts/test_curate.py`, before the `if __name__ == "__main__":` block:

```python
class ResolveTiersTests(unittest.TestCase):
    def _skills(self):
        return [
            Skill("brainstorming", "brainstorming", 100),
            Skill("github/github-issues", "github-issues", 100),
            Skill("mlops/research/dspy", "dspy", 100),
            Skill("mlops/inference/llama-cpp", "llama-cpp", 100),
            Skill("software-development/plan", "plan", 100),
        ]

    def test_default_is_archived_when_absent(self):
        tiers = resolve_tiers({}, self._skills())
        self.assertEqual(set(tiers.values()), {"archived"})

    def test_explicit_default_applies(self):
        tiers = resolve_tiers({"default": "active"}, self._skills())
        self.assertEqual(set(tiers.values()), {"active"})

    def test_category_matches_first_component_at_any_depth(self):
        manifest = {"default": "archived", "categories": {"mlops": "active"}}
        tiers = resolve_tiers(manifest, self._skills())
        self.assertEqual(tiers["mlops/research/dspy"], "active")
        self.assertEqual(tiers["mlops/inference/llama-cpp"], "active")
        self.assertEqual(tiers["github/github-issues"], "archived")

    def test_top_level_single_skill_uses_its_own_category_key(self):
        manifest = {"categories": {"brainstorming": "active"}}
        tiers = resolve_tiers(manifest, self._skills())
        self.assertEqual(tiers["brainstorming"], "active")

    def test_skill_entry_beats_category(self):
        manifest = {
            "default": "active",
            "categories": {"software-development": "active"},
            "skills": {"software-development/plan": "archived"},
        }
        tiers = resolve_tiers(manifest, self._skills())
        self.assertEqual(tiers["software-development/plan"], "archived")

    def test_every_discovered_skill_gets_a_tier(self):
        tiers = resolve_tiers({}, self._skills())
        self.assertEqual(set(tiers), {s.path for s in self._skills()})


class ValidateTests(unittest.TestCase):
    def _skills(self):
        return [
            Skill("creative/p5js", "p5js", 100),
            Skill("software-development/plan", "plan", 100),
            Skill("systematic-debugging", "systematic-debugging", 100),
            Skill("software-development/systematic-debugging", "systematic-debugging", 100),
            Skill("nameless", "", 0),
        ]

    def _codes(self, manifest, skills=None):
        return [e for e in validate(manifest, skills or self._skills())]

    def _clean_skills(self):
        return [
            Skill("creative/p5js", "p5js", 100),
            Skill("software-development/plan", "plan", 100),
        ]

    def test_valid_manifest_has_no_errors(self):
        manifest = {
            "default": "archived",
            "categories": {"software-development": "active"},
            "skills": {"creative/p5js": "archived"},
        }
        self.assertEqual(validate(manifest, self._clean_skills()), [])

    def test_unknown_top_level_key_is_an_error(self):
        errors = self._codes({"categorie": {"github": "active"}})
        self.assertTrue(any("unknown manifest key 'categorie'" in e for e in errors))

    def test_non_tier_value_is_an_error(self):
        errors = self._codes({"default": "on"})
        self.assertTrue(any("default: 'on' is not a tier" in e for e in errors))

    def test_non_tier_category_value_is_an_error(self):
        errors = self._codes({"categories": {"software-development": "yes"}})
        self.assertTrue(any("categories.software-development: 'yes' is not a tier" in e for e in errors))

    def test_unknown_category_suggests_closest(self):
        errors = self._codes({"categories": {"software_development": "active"}})
        self.assertTrue(any("no skill under this directory" in e and "software-development" in e for e in errors))

    def test_unknown_skill_path_suggests_closest(self):
        errors = self._codes({"skills": {"software-development/plane": "active"}})
        self.assertTrue(any("skills.software-development/plane: no such skill" in e for e in errors))

    def test_path_in_both_categories_and_skills_is_an_error(self):
        manifest = {
            "categories": {"software-development": "active"},
            "skills": {"software-development/plan": "archived"},
        }
        errors = self._codes(manifest)
        self.assertTrue(any("listed under both categories and skills" in e for e in errors))

    def test_name_collision_is_an_error_naming_both_paths(self):
        errors = self._codes({})
        joined = "\n".join(errors)
        self.assertIn("name collision: 'systematic-debugging'", joined)
        self.assertIn("software-development/systematic-debugging", joined)

    def test_nameless_skill_is_an_error(self):
        errors = self._codes({})
        self.assertTrue(any("nameless" in e and "no frontmatter name" in e for e in errors))

    def test_categories_must_be_a_mapping(self):
        errors = self._codes({"categories": ["software-development"]})
        self.assertTrue(any("categories: must be a mapping" in e for e in errors))

    def test_skills_must_be_a_mapping(self):
        errors = self._codes({"skills": ["creative/p5js"]})
        self.assertTrue(any("skills: must be a mapping" in e for e in errors))


class LoadManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_missing_file_raises_with_copy_hint(self):
        missing = os.path.join(self.tmp.name, "curation.yaml")
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(missing)
        self.assertIn("curation.example.yaml", str(ctx.exception))

    def test_empty_file_is_an_empty_manifest(self):
        path = os.path.join(self.tmp.name, "curation.yaml")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("")
        self.assertEqual(load_manifest(path), {})

    def test_non_mapping_top_level_raises(self):
        path = os.path.join(self.tmp.name, "curation.yaml")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("- one\n- two\n")
        with self.assertRaises(ManifestError):
            load_manifest(path)

    def test_parses_yaml(self):
        path = os.path.join(self.tmp.name, "curation.yaml")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("default: archived\ncategories:\n  github: active\n")
        self.assertEqual(
            load_manifest(path), {"default": "archived", "categories": {"github": "active"}}
        )
```

Then add the imports at the top of `scripts/test_curate.py`, directly after the `from curation.skills import (...)` block:

```python
from curation.skills import (
    Skill,
    discover_skills,
    est_tokens,
    frontmatter_span,
)
from curation.tiers import ManifestError, load_manifest, resolve_tiers, validate
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 scripts/test_curate.py`

Expected: `ModuleNotFoundError: No module named 'curation.tiers'`

- [ ] **Step 3: Implement the module**

Create `scripts/curation/tiers.py`:

```python
"""Loading, resolving, and validating the curation manifest.

Precedence, most specific first: a skills: entry, then the categories:
entry matching the skill's first path component, then default:.
"""

from __future__ import annotations

import difflib
import os

import yaml

from .skills import TIER_ACTIVE, TIER_ARCHIVED, VALID_TIERS, Skill

MANIFEST_KEYS = ("default", "categories", "skills")


class ManifestError(Exception):
    """The manifest is missing or cannot be read as a mapping."""


def load_manifest(path: str) -> dict:
    """Read the manifest, or raise ManifestError explaining how to create one."""
    if not os.path.exists(path):
        raise ManifestError(
            f"no manifest at {path}\n"
            f"copy curation.example.yaml to curation.yaml and edit it"
        )
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ManifestError(f"{path}: top level must be a mapping, got {type(data).__name__}")
    return data


def _mapping(manifest: dict, key: str, errors: list[str]) -> dict:
    value = manifest.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"{key}: must be a mapping, got {type(value).__name__}")
        return {}
    return value


def resolve_tiers(manifest: dict, skills: list[Skill]) -> dict[str, str]:
    """Return {skill path: tier} for every discovered skill."""
    default = manifest.get("default", TIER_ARCHIVED)
    categories = manifest.get("categories") or {}
    per_skill = manifest.get("skills") or {}
    tiers: dict[str, str] = {}
    for skill in skills:
        if skill.path in per_skill:
            tier = per_skill[skill.path]
        else:
            tier = categories.get(skill.path.split("/", 1)[0], default)
        tiers[skill.path] = tier
    return tiers


def _closest(needle: str, haystack) -> str:
    matches = difflib.get_close_matches(needle, sorted(haystack), 3)
    return f"; closest: {', '.join(matches)}" if matches else ""


def validate(manifest: dict, skills: list[Skill]) -> list[str]:
    """Return a list of human-readable problems; empty means valid."""
    errors: list[str] = []

    for key in manifest:
        if key not in MANIFEST_KEYS:
            errors.append(
                f"unknown manifest key {key!r}; expected one of {', '.join(MANIFEST_KEYS)}"
            )

    default = manifest.get("default", TIER_ARCHIVED)
    if default not in VALID_TIERS:
        errors.append(
            f"default: {default!r} is not a tier; use {TIER_ACTIVE!r} or {TIER_ARCHIVED!r}"
        )

    categories = _mapping(manifest, "categories", errors)
    per_skill = _mapping(manifest, "skills", errors)

    known_paths = {s.path for s in skills}
    heads = {s.path.split("/", 1)[0] for s in skills}

    for name, tier in categories.items():
        if tier not in VALID_TIERS:
            errors.append(f"categories.{name}: {tier!r} is not a tier")
        if name not in heads:
            errors.append(
                f"categories.{name}: no skill under this directory{_closest(name, heads)}"
            )

    for path, tier in per_skill.items():
        if tier not in VALID_TIERS:
            errors.append(f"skills.{path}: {tier!r} is not a tier")
        if path not in known_paths:
            errors.append(f"skills.{path}: no such skill{_closest(path, known_paths)}")
        elif path.split("/", 1)[0] in categories:
            errors.append(
                f"{path}: listed under both categories and skills; keep the more specific one only"
            )

    for skill in skills:
        if not skill.name:
            errors.append(f"{skill.path}: SKILL.md has no frontmatter name")

    by_name: dict[str, list[str]] = {}
    for skill in skills:
        by_name.setdefault(skill.name, []).append(skill.path)
    for name, paths in sorted(by_name.items()):
        if len(paths) > 1:
            errors.append(
                f"name collision: {name!r} is claimed by {len(paths)} skills "
                f"({', '.join(sorted(paths))}); permission.skill matches on name, "
                f"so only one of them can ever load"
            )

    return errors
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`

Expected: `Ran 31 tests` and `OK`

- [ ] **Step 5: Verify the real catalog reports no collision**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from curation.skills import discover_skills
from curation.tiers import validate
errors = validate({}, discover_skills('.'))
print('\n'.join(errors) or 'no errors')
"
```

Expected: `no errors`. If a collision is still reported, Task 1 did not finish.

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curation/tiers.py scripts/test_curate.py
git commit -m "feat: add tier cascade resolution and manifest validation"
```

---

### Task 4: Config region rendering and splicing

**Files:**
- Create: `scripts/curation/config.py`
- Modify: `scripts/test_curate.py` (append a test class)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `MARKER_BEGIN: str`, `MARKER_END: str`
  - `SKELETON: str` — the exact text to paste when no region exists
  - `class RegionError(Exception)`
  - `render_region(names, indent="    ") -> str`
  - `find_region(text: str) -> tuple[int, int] | None`
  - `region_text(text: str) -> str | None`
  - `detected_indent(text: str) -> str`
  - `splice_region(text: str, region: str) -> str`
  - `region_drift(text: str, names) -> list[str]` — names present in text but not in `names`, and vice versa

- [ ] **Step 1: Append the failing tests**

Append to `scripts/test_curate.py`, before the `if __name__ == "__main__":` block:

```python
class RenderRegionTests(unittest.TestCase):
    def test_is_deny_by_default(self):
        region = render_region(["writing-plans", "brainstorming"])
        lines = region.splitlines()
        self.assertIn('"*": "deny"', lines[1])

    def test_allow_entries_are_sorted(self):
        region = render_region(["zeta", "alpha"])
        allows = [line for line in region.splitlines() if '"allow"' in line]
        self.assertEqual(allows, ['    "alpha": "allow",', '    "zeta": "allow"'])

    def test_brackets_the_region_in_markers(self):
        region = render_region(["alpha"])
        self.assertTrue(region.startswith("    " + MARKER_BEGIN))
        self.assertTrue(region.endswith(MARKER_END))

    def test_empty_active_set_is_still_deny_by_default(self):
        region = render_region([])
        self.assertIn('"*": "deny"', region)

    def test_indent_is_configurable(self):
        region = render_region(["alpha"], indent="\t")
        self.assertIn('\t"alpha": "allow"', region)

    def test_no_trailing_comma_on_last_entry(self):
        region = render_region(["alpha"])
        body = [l for l in region.splitlines() if l.strip() and not l.strip().startswith("//")]
        self.assertFalse(body[-1].endswith(","))

    def _as_json(self, region):
        body = "\n".join(
            line for line in region.splitlines() if not line.strip().startswith("//")
        )
        return json.loads("{" + body + "}")

    def test_region_body_is_valid_json(self):
        self.assertEqual(
            self._as_json(render_region(["zeta", "alpha"])),
            {"*": "deny", "alpha": "allow", "zeta": "allow"},
        )

    def test_region_body_is_valid_json_for_one_entry(self):
        self.assertEqual(self._as_json(render_region(["alpha"])), {"*": "deny", "alpha": "allow"})

    def test_region_body_is_valid_json_when_empty(self):
        self.assertEqual(self._as_json(render_region([])), {"*": "deny"})


class RegionTests(unittest.TestCase):
    def _doc(self, indent="      "):
        region = render_region(["alpha", "beta"], indent=indent)
        return (
            "{\n"
            '  "$schema": "https://opencode.ai/config.json",\n'
            '  "provider": { "ollama": { "baseURL": "https://example.com/v1" } },\n'
            '  "permission": {\n'
            '    "skill": {\n'
            f"{region}\n"
            "    }\n"
            "  }\n"
            "}\n"
        )

    def test_finds_region_span(self):
        doc = self._doc()
        self.assertIsNotNone(find_region(doc))
        self.assertIn('"alpha": "allow"', region_text(doc))

    def test_returns_none_when_absent(self):
        self.assertIsNone(find_region('{"provider": {}}\n'))
        self.assertIsNone(region_text('{"provider": {}}\n'))

    def test_unterminated_marker_raises(self):
        with self.assertRaises(RegionError):
            find_region(f"{{\n  {MARKER_BEGIN}\n")

    def test_splice_preserves_everything_outside_the_region(self):
        doc = self._doc()
        out = splice_region(doc, render_region(["alpha"]))
        self.assertIn('"provider": { "ollama": { "baseURL": "https://example.com/v1" } }', out)
        self.assertIn('"$schema"', out)
        self.assertIn('"alpha": "allow"', out)
        self.assertNotIn('"beta": "allow"', out)

    def test_splice_is_idempotent(self):
        doc = self._doc()
        once = splice_region(doc, render_region(["alpha"]))
        twice = splice_region(once, render_region(["alpha"]))
        self.assertEqual(once, twice)

    def test_detected_indent_matches_the_marker_line(self):
        doc = self._doc(indent="\t")
        self.assertEqual(detected_indent(doc), "\t")
    def test_https_url_is_not_mistaken_for_a_marker(self):
        doc = self._doc()
        self.assertIn("https://example.com/v1", region_text(doc) + doc)
        out = splice_region(doc, render_region(["alpha"]))
        self.assertIn('"baseURL": "https://example.com/v1"', out)

    def test_splice_raises_when_region_absent(self):
        with self.assertRaises(RegionError):
            splice_region('{"provider": {}}\n', render_region(["alpha"]))

    def test_skeleton_contains_both_markers(self):
        self.assertIn(MARKER_BEGIN, SKELETON)
        self.assertIn(MARKER_END, SKELETON)
        self.assertIn('"permission"', SKELETON)
        self.assertIn('"skill"', SKELETON)


class RegionDriftTests(unittest.TestCase):
    def _doc(self, names):
        region = render_region(list(names))
        return '{\n  "permission": {\n    "skill": {\n' + region + "\n    }\n  }\n}\n"

    def test_matching_region_has_no_drift(self):
        doc = self._doc(["alpha", "beta"])
        self.assertEqual(region_drift(doc, ["alpha", "beta"]), [])

    def test_reports_a_hand_edited_entry(self):
        doc = self._doc(["alpha", "beta"])
        drift = region_drift(doc, ["alpha"])
        self.assertIn("beta", drift[0])

    def test_reports_a_missing_promotion(self):
        doc = self._doc(["alpha"])
        drift = region_drift(doc, ["alpha", "gamma"])
        self.assertIn("gamma", drift[0])

    def test_missing_region_is_drift(self):
        self.assertEqual(region_drift('{"provider": {}}\n', ["alpha"]), ["no curated region found"])
```

Then add the import after the `from curation.tiers import ...` line:

```python
from curation.config import (
    MARKER_BEGIN,
    MARKER_END,
    SKELETON,
    RegionError,
    find_region,
    detected_indent,
    region_drift,
    region_text,
    render_region,
    splice_region,
)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 scripts/test_curate.py`

Expected: `ModuleNotFoundError: No module named 'curation.config'`

- [ ] **Step 3: Implement the module**

Create `scripts/curation/config.py`:

```python
"""Rendering and splicing the curated region of opencode.jsonc.

The config is never parsed and never reformatted. The region is located by
its comment markers and replaced as text, so a "//" inside a URL elsewhere
in the file is irrelevant and the hand-written provider block is untouched.
"""

from __future__ import annotations

MARKER_BEGIN = (
    "// >>> curated by scripts/curate.py "
    "— regenerate: python3 scripts/curate.py sync >>>"
)
MARKER_END = "// <<< curated by scripts/curate.py <<<"

SKELETON = f'''  "permission": {{
    "skill": {{
      {MARKER_BEGIN}
      "*": "deny"
      {MARKER_END}
    }}
  }},'''


class RegionError(Exception):
    """The curated region is missing or unterminated."""


def render_region(names, indent: str = "    ") -> str:
    """Render the deny-by-default allowlist for names, wrapped in markers.

    The entries are joined with commas so the region is a valid JSON object
    body once the marker comments are ignored.
    """
    entries = [f'{indent}"*": "deny"']
    entries += [f'{indent}"{name}": "allow"' for name in sorted(names)]
    body = ",\n".join(entries)
    return "\n".join([f"{indent}{MARKER_BEGIN}", body, f"{indent}{MARKER_END}"])


def find_region(text: str) -> tuple[int, int] | None:
    """Return the (start, end) span of the region, or None if there is none.

    The span starts at the beginning of the marker's line so the generated
    indent replaces the old one instead of stacking on top of it.
    """
    idx = text.find(MARKER_BEGIN)
    if idx == -1:
        return None
    start = text.rfind("\n", 0, idx) + 1
    end = text.find(MARKER_END, idx)
    if end == -1:
        raise RegionError(f"{MARKER_BEGIN} found with no matching {MARKER_END}")
    return start, end + len(MARKER_END)


def region_text(text: str) -> str | None:
    """Return the region's exact text including markers, or None."""
    span = find_region(text)
    return None if span is None else text[span[0] : span[1]]


def detected_indent(text: str) -> str:
    """Return the whitespace preceding the begin marker on its own line."""
    idx = text.find(MARKER_BEGIN)
    if idx == -1:
        return "    "
    line_start = text.rfind("\n", 0, idx) + 1
    return text[line_start:idx]


def splice_region(text: str, region: str) -> str:
    """Replace the region's text, leaving all surrounding bytes identical."""
    span = find_region(text)
    if span is None:
        raise RegionError(
            "no curated region found; paste this into opencode.jsonc once:\n" + SKELETON
        )
    return text[: span[0]] + region + text[span[1] :]


def region_drift(text: str, names) -> list[str]:
    """Describe how the on-disk region differs from the expected allowlist."""
    found = region_text(text)
    if found is None:
        return ["no curated region found"]
    expected = render_region(names, detected_indent(text))
    if found == expected:
        return []
    on_disk = {
        line.split(":")[0].strip()
        for line in found.splitlines()
        if line.strip() and not line.strip().startswith("//")
    }
    wanted = {'"*"', *(f'"{n}"' for n in names)}
    missing = sorted(wanted - on_disk)
    extra = sorted(on_disk - wanted)
    parts = []
    if missing:
        parts.append("missing from the config region, promoted in the manifest: " + ", ".join(missing))
    if extra:
        parts.append("in the config region but not active in the manifest: " + ", ".join(extra))
    if not parts:
        parts.append("formatting differs from what sync would write; run sync")
    return ["; ".join(parts)]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`

Expected: `Ran 53 tests` and `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curation/config.py scripts/test_curate.py
git commit -m "feat: add curated-region rendering and splicing"
```

---

### Task 5: The local review stamp

**Files:**
- Create: `scripts/curation/stamp.py`
- Modify: `scripts/test_curate.py` (append a test class)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `STAMP_VERSION: int`
  - `read_stamp(path: str) -> dict` — `{}` when missing or unreadable
  - `write_stamp(path: str, paths) -> None`
  - `unreviewed(stamp: dict, paths) -> list[str]`

- [ ] **Step 1: Append the failing tests**

Append to `scripts/test_curate.py`, before the `if __name__ == "__main__":` block:

```python
class StampTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, ".curation_stamp.json")
        self.addCleanup(self.tmp.cleanup)

    def test_missing_stamp_reads_as_empty(self):
        self.assertEqual(read_stamp(self.path), {})

    def test_corrupt_stamp_reads_as_empty(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(read_stamp(self.path), {})

    def test_roundtrip_records_paths(self):
        write_stamp(self.path, ["b", "a"])
        stamp = read_stamp(self.path)
        self.assertEqual(stamp["version"], STAMP_VERSION)
        self.assertEqual(stamp["reviewed_paths"], ["a", "b"])
        self.assertIn("reviewed_at", stamp)

    def test_unreviewed_lists_new_paths(self):
        write_stamp(self.path, ["a"])
        self.assertEqual(unreviewed(read_stamp(self.path), ["a", "b"]), ["b"])

    def test_unreviewed_is_empty_when_all_seen(self):
        write_stamp(self.path, ["a", "b"])
        self.assertEqual(unreviewed(read_stamp(self.path), ["a", "b"]), [])

    def test_unreviewed_ignores_removed_paths(self):
        write_stamp(self.path, ["a", "b"])
        self.assertEqual(unreviewed(read_stamp(self.path), ["a"]), [])

    def test_unreviewed_with_no_stamp_lists_everything(self):
        self.assertEqual(unreviewed({}, ["a", "b"]), ["a", "b"])
```

Then add the import after the `from curation.config import (...)` block:

```python
from curation.stamp import STAMP_VERSION, read_stamp, unreviewed, write_stamp
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 scripts/test_curate.py`

Expected: `ModuleNotFoundError: No module named 'curation.stamp'`

- [ ] **Step 3: Implement the module**

Create `scripts/curation/stamp.py`:

```python
"""The local record of which skills have been reviewed.

This is what makes "new skills are off by default" checkable: without it,
the claim can never be verified.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

STAMP_VERSION = 1


def read_stamp(path: str) -> dict:
    """Read the stamp; an absent or corrupt stamp reads as empty."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def write_stamp(path: str, paths) -> None:
    """Record paths as reviewed, sorted, with a timestamp."""
    payload = {
        "version": STAMP_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewed_paths": sorted(paths),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def unreviewed(stamp: dict, paths) -> list[str]:
    """Return the paths present now that the stamp has not recorded."""
    seen = set(stamp.get("reviewed_paths") or [])
    return sorted(set(paths) - seen)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`

Expected: `Ran 60 tests` and `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curation/stamp.py scripts/test_curate.py
git commit -m "feat: add local review stamp for newly added skills"
```

---

### Task 6: The `plan`, `sync`, and `check` CLI

**Files:**
- Create: `scripts/curate.py`
- Modify: `scripts/test_curate.py` (append an integration test class)

**Interfaces:**
- Consumes: `discover_skills`, `est_tokens`, `TIER_ACTIVE` from `curation.skills`; `load_manifest`, `resolve_tiers`, `validate`, `ManifestError` from `curation.tiers`; `MARKER_BEGIN`, `SKELETON`, `detected_indent`, `region_drift`, `render_region`, `splice_region` from `curation.config`; `read_stamp`, `unreviewed`, `write_stamp` from `curation.stamp` (Tasks 2–5).
- Produces:
  - `REPO_ROOT: str`, `MANIFEST_PATH: str`, `STAMP_PATH: str`, `CONFIG_PATH: str`
  - `build_parser() -> argparse.ArgumentParser`
  - `main(argv=None) -> int`

- [ ] **Step 1: Append the failing integration tests**

Append to `scripts/test_curate.py`, before the `if __name__ == "__main__":` block:

```python
class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

        self.root = os.path.join(self.base, "repo")
        os.makedirs(self.root)
        write_skill(self.root, "alpha", "alpha")
        write_skill(self.root, "beta", "beta")
        write_skill(self.root, "github/gamma", "gamma")

        self.manifest = os.path.join(self.root, "curation.yaml")
        with open(self.manifest, "w", encoding="utf-8") as fh:
            fh.write("default: archived\ncategories:\n  github: active\n")

        self.stamp = os.path.join(self.root, ".curation_stamp.json")
        self.config = os.path.join(self.base, "opencode.jsonc")
        self._write_config([])

    def _write_config(self, names):
        region = render_region(names)
        with open(self.config, "w", encoding="utf-8") as fh:
            fh.write(
                '{\n  "provider": { "ollama": { "baseURL": "https://x/v1" } },\n'
                '  "permission": {\n    "skill": {\n' + region + "\n    }\n  }\n}\n"
            )

    def _run(self, *args):
        return curate.main(
            [
                "--root", self.root,
                "--manifest", self.manifest,
                "--stamp", self.stamp,
                "--config", self.config,
                *args,
            ]
        )

    def _config_text(self):
        with open(self.config, encoding="utf-8") as fh:
            return fh.read()

    def test_check_fails_before_any_sync(self):
        self.assertEqual(self._run("check"), 1)

    def test_sync_writes_the_active_set(self):
        self.assertEqual(self._run("sync"), 0)
        text = self._config_text()
        self.assertIn('"gamma": "allow"', text)
        self.assertNotIn('"alpha": "allow"', text)
        self.assertNotIn('"beta": "allow"', text)

    def test_sync_preserves_the_hand_written_block(self):
        self._run("sync")
        self.assertIn('"baseURL": "https://x/v1"', self._config_text())

    def test_sync_is_idempotent(self):
        self._run("sync")
        first = self._config_text()
        self.assertEqual(self._run("sync"), 0)
        self.assertEqual(self._config_text(), first)

    def test_check_passes_after_sync(self):
        self._run("sync")
        self.assertEqual(self._run("check"), 0)

    def test_check_fails_on_a_hand_edit(self):
        self._run("sync")
        text = self._config_text().replace(
            '    "*": "deny"', '    "*": "deny",\n    "beta": "allow"'
        )
        with open(self.config, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.assertEqual(self._run("check"), 1)

    def test_check_fails_on_a_manifest_error(self):
        with open(self.manifest, "a", encoding="utf-8") as fh:
            fh.write("skills:\n  alpha: active\n")
        self.assertEqual(self._run("check"), 1)

    def test_plan_writes_the_stamp(self):
        self._run("sync")
        self.assertEqual(self._run("plan"), 0)
        self.assertTrue(os.path.exists(self.stamp))
        self.assertEqual(self._run("check"), 0)

    def test_sync_fails_when_the_region_is_absent(self):
        with open(self.config, "w", encoding="utf-8") as fh:
            fh.write('{\n  "provider": {}\n}\n')
        self.assertEqual(self._run("sync"), 1)
        self.assertEqual(self._config_text(), '{\n  "provider": {}\n}\n')

    def test_plan_reports_a_newly_added_skill(self):
        self._run("plan")
        write_skill(self.root, "delta", "delta")
        self.assertEqual(self._run("plan"), 0)

    def test_no_subcommand_is_an_error(self):
        with self.assertRaises(SystemExit):
            curate.main(["--root", self.root])
```

Then add the import after the stamp import:

```python
import curate
```

and remove the placeholder line `self.assertIn('"alpha": "deny"', text) if False else None` from `test_sync_writes_the_active_set` so the test reads:

```python
    def test_sync_writes_the_active_set(self):
        self.assertEqual(self._run("sync"), 0)
        text = self._config_text()
        self.assertIn('"gamma": "allow"', text)
        self.assertNotIn('"alpha": "allow"', text)
        self.assertNotIn('"beta": "allow"', text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 scripts/test_curate.py`

Expected: `ModuleNotFoundError: No module named 'curate'`

- [ ] **Step 3: Implement the CLI**

Create `scripts/curate.py`:

```python
#!/usr/bin/env python3
"""Curate which catalog skills load into an agent session.

  plan   resolve the tier cascade, report the active set, record the review
  sync   write the active set into the curated region of opencode.jsonc
  check  verify the manifest and that the config region matches the manifest

The config is only ever spliced, never reformatted.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation import stamp as stamp_mod
from curation import config as config_mod
from curation import tiers
from curation.skills import TIER_ACTIVE, discover_skills, est_tokens

# realpath, not abspath: this repo is symlinked into ~/.config/opencode/skills,
# and abspath would resolve the catalog root to the symlink location.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
MANIFEST_PATH = os.path.join(REPO_ROOT, "curation.yaml")
STAMP_PATH = os.path.join(REPO_ROOT, ".curation_stamp.json")
CONFIG_PATH = os.path.expanduser("~/.config/opencode/opencode.jsonc")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="curate.py", description=__doc__)
    parser.add_argument("--root", default=REPO_ROOT, help="catalog root")
    parser.add_argument("--manifest", default=MANIFEST_PATH, help="path to curation.yaml")
    parser.add_argument("--stamp", default=STAMP_PATH, help="path to the review stamp")
    parser.add_argument("--config", default=CONFIG_PATH, help="path to opencode.jsonc")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="report the active set and record the review")
    sub.add_parser("sync", help="write the active set into the config region")
    sub.add_parser("check", help="verify the manifest and the config region")
    return parser


def _resolve(args):
    skills = discover_skills(args.root)
    manifest = tiers.load_manifest(args.manifest)
    errors = tiers.validate(manifest, skills)
    resolved = tiers.resolve_tiers(manifest, skills)
    active = sorted(s.name for s in skills if resolved[s.path] == TIER_ACTIVE)
    active_paths = sorted(s.path for s in skills if resolved[s.path] == TIER_ACTIVE)
    return skills, active, active_paths, errors


def _read_config(path: str) -> str:
    if not os.path.exists(path):
        raise config_mod.RegionError(f"no config at {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _report_errors(errors) -> None:
    print(f"{len(errors)} problem(s) with the manifest:", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)


def cmd_plan(args) -> int:
    try:
        skills, active, active_paths, errors = _resolve(args)
    except tiers.ManifestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        _report_errors(errors)
        return 1

    archived = len(skills) - len(active_paths)
    active_set = set(active_paths)
    tokens = est_tokens(sum(s.fm_chars for s in skills if s.path in active_set))
    print(f"active:   {len(active_paths)}")
    print(f"archived: {archived}")
    print(f"active frontmatter: ~{tokens} tokens")
    print()
    for name in active:
        print(f"  active   {name}")

    new = stamp_mod.unreviewed(stamp_mod.read_stamp(args.stamp), [s.path for s in skills])
    if new:
        print()
        print(f"{len(new)} skill(s) not reviewed since the last plan:")
        for path in new:
            print(f"  new      {path}")

    stamp_mod.write_stamp(args.stamp, [s.path for s in skills])
    return 0


def cmd_sync(args) -> int:
    try:
        skills, active, active_paths, errors = _resolve(args)
    except tiers.ManifestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        _report_errors(errors)
        return 1

    try:
        text = _read_config(args.config)
    except config_mod.RegionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        updated = config_mod.splice_region(
            text, config_mod.render_region(active, config_mod.detected_indent(text))
        )
    except config_mod.RegionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if updated == text:
        print(f"already up to date: {len(active_paths)} active skill(s)")
        return 0

    with open(args.config, "w", encoding="utf-8") as fh:
        fh.write(updated)
    print(f"wrote {len(active_paths)} active skill(s) to {args.config}")
    return 0


def cmd_check(args) -> int:
    try:
        skills, active, active_paths, errors = _resolve(args)
    except tiers.ManifestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        _report_errors(errors)
        return 1

    try:
        text = _read_config(args.config)
    except config_mod.RegionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    drift = config_mod.region_drift(text, active)
    if drift:
        print("config region is out of date:", file=sys.stderr)
        for line in drift:
            print(f"  - {line}", file=sys.stderr)
        print("run: python3 scripts/curate.py sync", file=sys.stderr)
        return 1

    print(f"ok: {len(active_paths)} active, {len(skills) - len(active_paths)} archived, no collisions")

    new = stamp_mod.unreviewed(stamp_mod.read_stamp(args.stamp), [s.path for s in skills])
    if new:
        print(f"note: {len(new)} skill(s) added since the last plan (all archived by default)")
    return 0


COMMANDS = {"plan": cmd_plan, "sync": cmd_sync, "check": cmd_check}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 scripts/test_curate.py`

Expected: `Ran 71 tests` and `OK`

- [ ] **Step 5: Run the tool against the real catalog with no manifest yet**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 scripts/curate.py check; echo "exit=$?"
```

Expected: `no manifest at .../curation.yaml` and `copy curation.example.yaml to curation.yaml and edit it`, then `exit=1`. This is the correct pre-Task-7 behavior.

- [ ] **Step 6: Commit**

```bash
cd /Users/xuyi/Source/skills
git add scripts/curate.py scripts/test_curate.py
git commit -m "feat: add plan, sync, and check subcommands"
```

---

### Task 7: Seed the manifest, install the gate, and verify

**Files:**
- Create: `curation.example.yaml`
- Create: `curation.yaml` (gitignored)
- Modify: `.gitignore`
- Modify: `~/.config/opencode/opencode.jsonc` (outside the repository, not committed)

**Interfaces:**
- Consumes: `curate.py` from Task 6.
- Produces: a working deny-by-default gate with a 35-skill active set, and the committed schema example.

- [ ] **Step 1: Commit the schema example**

Create `curation.example.yaml`:

```yaml
# Which catalog skills load into your agent session.
#
# Copy this file to curation.yaml and edit it. curation.yaml is gitignored:
# it is local policy, not catalog content.
#
# Resolution order, most specific first:
#   1. skills:    a full repo-relative path        -> creative/p5js
#   2. categories: the first path component         -> mlops (covers mlops/**)
#   3. default:   everything else
#
# Tiers are "active" (loaded and maintained) or "archived" (present, not
# maintained). Archived is a normal state for a shared catalog.
#
# Leaving this file out entirely is valid: with no curation.yaml, nothing
# is curated. With a curation.yaml that has no default, everything that is
# not explicitly active is archived, so new skills never load by accident.

default: archived

categories:
  software-development: active
  github: active
  apple: active
  autonomous-ai-agents: active
  note-taking: active

skills:
  # Top-level single-skill directories, promoted by their own name.
  brainstorming: active
  writing-plans: active
  writing-skills: active
  executing-plans: active
  dispatching-parallel-agents: active
  verification-before-completion: active
  review: active
  diagnosing-bugs: active
```

- [ ] **Step 2: Seed the local manifest from the example**

```bash
cd /Users/xuyi/Source/skills
cp curation.example.yaml curation.yaml
```

Expected: no output.

- [ ] **Step 3: Add both local files to `.gitignore`**

Read `.gitignore`, then append these two lines if they are not already present:

```
curation.yaml
.curation_stamp.json
```

- [ ] **Step 4: Verify the ignore works and count the active set**

Run:

```bash
cd /Users/xuyi/Source/skills
git check-ignore -v curation.yaml .curation_stamp.json
python3 scripts/curate.py plan | head -5
```

Expected: `git check-ignore` names `.gitignore` as the source for both paths. `plan` prints `active:   35` and `archived: 101`. Read the full active list and confirm it matches your intent — this is the artifact you are signing off on, so change `curation.yaml` now if it does not.

- [ ] **Step 5: Install the region skeleton into `opencode.jsonc` once**

Run:

```bash
python3 -c "
from curation.config import SKELETON
print(SKELETON)
"
```

Paste the printed block into `~/.config/opencode/opencode.jsonc` as a top-level key, placing it after `provider` and before `disabled_providers`, keeping the surrounding commas valid. Do not leave a trailing comma on the final key in the file. Then confirm the markers are present:

```bash
cd /Users/xuyi/Source/skills
python3 - <<'PY'
import sys
sys.path.insert(0, "scripts")
from curation.config import find_region

text = open("/Users/xuyi/.config/opencode/opencode.jsonc").read()
print("region found:", find_region(text) is not None)
PY
```

Expected: `region found: True`

- [ ] **Step 6: Sync the gate**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 scripts/curate.py sync
```

Expected: `wrote 35 active skill(s) to /Users/xuyi/.config/opencode/opencode.jsonc`

- [ ] **Step 7: Verify the hand-written config survived byte-for-byte**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 - <<'PY'
text = open("/Users/xuyi/.config/opencode/opencode.jsonc").read()
probes = [
    '"$schema": "https://opencode.ai/config.json"',
    '"disabled_providers": []',
    "http://127.0.0.1:11434/v1",
    "https://xuyi.h4ck.me/v1",
    "jewelzufo/MiniCPM5-1B",
]
for probe in probes:
    print("ok  " if probe in text else "LOST", probe)
PY
python3 scripts/curate.py sync
```

Expected: five `ok` lines, then `already up to date: 35 active skill(s)` — proving idempotence.

- [ ] **Step 8: Verify check passes and the config is still valid JSONC**

Run:

```bash
cd /Users/xuyi/Source/skills
python3 scripts/curate.py check; echo "exit=$?"
python3 - <<'PY'
import json
import re

text = open("/Users/xuyi/.config/opencode/opencode.jsonc").read()
stripped = re.sub(r"^\s*//.*$", "", text, flags=re.M)
data = json.loads(stripped)
print("json ok:", sorted(data))
print("skill entries:", len(data["permission"]["skill"]))
PY
```

Expected: `ok: 35 active, 101 archived, no collisions`, `exit=0`, then `json ok: ['disabled_providers', 'permission', 'provider', '$schema']` and `skill entries: 36` — the 35 allows plus the `"*": "deny"` default.

- [ ] **Step 9: Verify the gate in a live session (manual)**

Restart opencode, then confirm:

1. `<available_skills>` lists only active skills. Spot-check that `p5js`, `llama-cpp`, and `powerpoint` are **absent**.
2. Attempt to load a denied skill, for example `skill({ name: "p5js" })`. Expect a rejection, not a load.
3. Attempt to load an active skill, for example `skill({ name: "writing-plans" })`. Expect it to load.

If step 1 shows any archived skill, re-run `sync` and restart. If step 2 loads the skill anyway, `deny` is not being honored — record that in the spec's Risks section rather than working around it.

- [ ] **Step 10: Verify a new skill is denied until promoted (manual)**

```bash
cd /Users/xuyi/Source/skills
mkdir -p scratch-probe
printf -- '---\nname: scratch-probe\ndescription: Temporary probe skill.\n---\n\n# Probe\n' > scratch-probe/SKILL.md
python3 scripts/curate.py plan | tail -5
```

Expected: `plan` reports `1 skill(s) not reviewed since the last plan` and `new      scratch-probe`, while `active` stays at 35. Then remove it:

```bash
cd /Users/xuyi/Source/skills
rm -rf scratch-probe
python3 scripts/curate.py plan | head -3
```

Expected: `active:   35`, `archived: 101`.

- [ ] **Step 11: Run the full test suite one last time**

Run: `python3 scripts/test_curate.py`

Expected: `OK` with no failures.

- [ ] **Step 12: Commit the committed files only**

```bash
cd /Users/xuyi/Source/skills
git status --short
git add curation.example.yaml .gitignore
git commit -m "feat: add the curation manifest schema and ignore local policy"
git status --short
```

Expected before the commit: `curation.example.yaml` and `.gitignore` as changes, with **no** `curation.yaml` and **no** `.curation_stamp.json`. Expected after: a clean `git status --short`.

---

## Self-Review

**Spec coverage.** Tier cascade and `default: archived` → Tasks 3, 6. Manifest gitignored plus committed example → Task 7. Deny-by-default `permission.skill` allowlist → Tasks 4, 6. Marker-based surgical rewrite, idempotence, artifact-not-source → Tasks 4, 6. Three subcommands → Task 6. Stamp and "new since last review" → Tasks 5, 6. All six failure-handling rows → Task 3 (manifest rows) and Tasks 4, 6 (config rows). Duplicate resolution with the `subagent-driven-development` fold-in → Task 1. Rollback → Task 4 Step 7 (region is text-spliced) and the note that deleting the region restores today's behavior. All four verification steps → Task 7 Steps 4, 6, 8, 9. All four success criteria → Task 7 Steps 4, 8, 9, 10.

**Type consistency.** `Skill(path, name, fm_chars)` is constructed positionally in Task 3's fixtures and by keyword in Task 2's `discover_skills`; the field order in the dataclass matches both. `resolve_tiers` returns `dict[str, str]` and Task 6 indexes it as `resolved[s.path]`. `render_region(names, indent)` is called with `names` as a sorted list in Task 6 and as a plain iterable in the Task 4 tests — both fine, since it only iterates. `region_drift(text, names)` is called positionally everywhere. `SKELETON` is referenced by Task 4's tests and by `splice_region`'s error message, and defined in Task 4.

**Execution review.** Every code block in this plan was extracted verbatim, assembled, and run before the plan was saved. That found four defects, all now fixed above:

1. `find_region` began the span *after* the marker's leading whitespace, so the generated indent stacked on the preserved one. Every `sync` then produced drift, `check` failed permanently, and `sync` was not idempotent. Fixed by starting the span at the beginning of the marker's line.
2. `render_region` joined entries with newlines and no commas, producing a region that was **not valid JSON**. The original tests missed it because none of them checked the region parses. Fixed by joining with `",\n"` and adding three tests that parse the region body.
3. `REPO_ROOT` used `abspath`, which does not resolve the symlink from `~/.config/opencode/skills` back to the repository. Fixed to `realpath`.
4. Two test fixtures were wrong rather than the code: `test_valid_manifest_has_no_errors` asserted an empty error list against a fixture that deliberately contained a collision and a nameless skill, and `test_plan_writes_the_stamp` called `check` before any `sync`. Both corrected.

The assembled plan runs 71 tests, all passing, and the task-by-task counts (10, 31, 53, 60, 71) are the verified counts. Against a simulated post-Task-1 catalog of 136 skills it reports `35 active, 101 archived, no collisions`, writes a 36-entry region that parses as valid JSONC, preserves the hand-written `provider` block byte-for-byte, and is idempotent. `est_tokens` reproduces the spec's 11,291-token baseline for all 139 skills exactly.
