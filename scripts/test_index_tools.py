"""Tests for the index cleanup tools. Run: python3 scripts/test_index_tools.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from curation.skills import discover_skills, est_tokens
from inventory import (
    DESC_OFFENDER,
    FAMILIES,
    broken_refs,
    inert_dirs,
    inventory,
    to_markdown,
)

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.py")


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
        with open(os.path.join(self.root, "diagramming", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("# diagramming\n")
        self.assertEqual(inert_dirs(self.root), ["diagramming"])

    def test_category_with_nested_skills_is_not_inert(self):
        with open(os.path.join(self.root, "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("# cat\n")
        write_skill(self.root, "cat/one", "one")
        self.assertEqual(inert_dirs(self.root), [])

    def test_archive_and_dot_dirs_are_ignored(self):
        os.makedirs(os.path.join(self.root, ".hidden"))
        with open(os.path.join(self.root, ".hidden", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        os.makedirs(os.path.join(self.root, "archive", "old"))
        with open(os.path.join(self.root, "archive", "old", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        self.assertEqual(inert_dirs(self.root), [])

    def test_archive_subtree_skill_does_not_count(self):
        os.makedirs(os.path.join(self.root, "category"))
        with open(os.path.join(self.root, "category", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("# category\n")
        write_skill(self.root, "category/archive/x", "x")
        self.assertEqual(inert_dirs(self.root), ["category"])

    def test_dot_dir_subtree_skill_does_not_count(self):
        os.makedirs(os.path.join(self.root, "category"))
        with open(os.path.join(self.root, "category", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
            fh.write("# category\n")
        write_skill(self.root, "category/.hidden/x", "x")
        self.assertEqual(inert_dirs(self.root), ["category"])


class BodyTextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def _write_raw(self, relpath, text, encoding="utf-8"):
        path = os.path.join(self.root, relpath, "SKILL.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding=encoding) as fh:
            fh.write(text)
        return path

    def test_bom_frontmatter_refs_are_not_scanned(self):
        self._write_raw(
            "bom",
            "---\nname: bom\ndescription: [see](docs/gone.md)\n---\n\n# bom\n",
            encoding="utf-8-sig",
        )
        self.assertEqual(broken_refs(self.root, "bom"), [])

    def test_hr_after_frontmatter_keeps_body_refs(self):
        write_skill(self.root, "hr", "hr", body="\n---\n\nSee `missing-after-hr.md`.\n")
        self.assertEqual(broken_refs(self.root, "hr"), ["missing-after-hr.md"])

    def test_invalid_frontmatter_opener_treats_whole_file_as_body(self):
        self._write_raw(
            "bad",
            '----\nname: bad\ndescription: [a](docs/gone.md)\n----\n\nbody\n',
        )
        self.assertEqual(broken_refs(self.root, "bad"), ["docs/gone.md"])


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_rows_carry_description_and_token_counts(self):
        write_skill(self.root, "alpha", "alpha", "x" * 500)
        inv = inventory(self.root)
        (row,) = inv["skills"]
        (s,) = discover_skills(self.root)
        self.assertEqual(row["desc_chars"], 500)
        self.assertEqual(row["fm_tokens"], est_tokens(s.fm_chars))
        self.assertEqual(inv["totals"]["offenders"], 1)

    def test_family_membership_is_flagged(self):
        self.assertEqual(set(FAMILIES), {"grill", "design", "review", "understand"})
        write_skill(self.root, "grill-me", "grill-me")
        inv = inventory(self.root)
        (row,) = inv["skills"]
        self.assertIn("grill", row["families"])

    def test_broken_relative_reference_is_flagged(self):
        write_skill(self.root, "alpha", "alpha", body="See `references/missing.md` for detail.")
        write_skill(self.root, "beta", "beta", body="See `references/exists.md` for detail.")
        os.makedirs(os.path.join(self.root, "beta", "references"))
        with open(os.path.join(self.root, "beta", "references", "exists.md"), "w", encoding="utf-8") as fh:
            fh.write("ok\n")
        write_skill(
            self.root,
            "refs",
            "refs",
            body='see [a](docs/a.md#frag), [b](docs/b.md "Title") and `//host/c.md`.',
        )
        inv = inventory(self.root)
        rows = {r["path"]: r for r in inv["skills"]}
        self.assertEqual(rows["alpha"]["broken_refs"], ["references/missing.md"])
        self.assertEqual(rows["beta"]["broken_refs"], [])
        self.assertIn("docs/a.md", rows["refs"]["broken_refs"])
        self.assertNotIn("docs/a.md#frag", rows["refs"]["broken_refs"])
        self.assertIn("docs/b.md", rows["refs"]["broken_refs"])
        self.assertNotIn("//host/c.md", rows["refs"]["broken_refs"])

    def test_external_and_absolute_refs_are_not_flagged(self):
        write_skill(self.root, "alpha", "alpha",
                    body="See [docs](https://example.com/a.md) and `~/x.md` and `/abs/y.md`.")
        inv = inventory(self.root)
        (row,) = inv["skills"]
        self.assertEqual(row["broken_refs"], [])

    def test_titled_markdown_link_is_flagged(self):
        write_skill(self.root, "titled", "titled",
                    body='see [x](docs/titled.md "Title")')
        inv = inventory(self.root)
        (row,) = inv["skills"]
        self.assertEqual(row["broken_refs"], ["docs/titled.md"])

    def test_json_output_round_trips(self):
        write_skill(self.root, "alpha", "alpha")
        out = os.path.join(self.root, "out.json")
        subprocess.run(
            [sys.executable, SCRIPT, "--root", self.root, "--json", out],
            check=True,
            capture_output=True,
        )
        with open(out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["skills"][0]["path"], "alpha")


class MarkdownTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_family_and_broken_ref_render(self):
        write_skill(self.root, "grill-me", "grill-me", body="See `docs/a.md` and `docs/b.md`.")
        md = to_markdown(inventory(self.root))
        self.assertIn("grill", md)
        self.assertIn("docs/a.md, docs/b.md", md)

    def test_multiple_families_join_with_comma_space(self):
        inv = {
            "skills": [
                {
                    "path": "p",
                    "name": "n",
                    "desc_chars": 1,
                    "fm_tokens": 1,
                    "families": ["grill", "design"],
                    "broken_refs": ["a.md", "b.md"],
                }
            ],
            "inert_dirs": [],
            "totals": {"skills": 1, "fm_tokens": 1, "offenders": 0},
        }
        md = to_markdown(inv)
        self.assertIn("| grill, design |", md)
        self.assertIn("| a.md, b.md |", md)

    def test_empty_inventory_renders_none_and_totals(self):
        md = to_markdown(inventory(self.root))
        self.assertIn("Inert directories: (none)", md)
        self.assertIn(
            f"Totals: 0 skills, 0 fm tokens, 0 description offenders (>{DESC_OFFENDER} chars)",
            md,
        )

    def test_pipe_in_name_is_escaped(self):
        write_skill(self.root, "pipe", '"a|b"')
        md = to_markdown(inventory(self.root))
        self.assertIn(r"a\|b", md)
        self.assertNotIn("a|b", md)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_bad_root_exits_2_with_error_on_stderr(self):
        res = subprocess.run(
            [sys.executable, SCRIPT, "--root", "/nonexistent/path-xyz"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        self.assertIn("error:", res.stderr)
        self.assertEqual(res.stdout, "")

    def test_write_path_oserror_exits_2_with_error_on_stderr(self):
        blocker = os.path.join(self.root, "blocker")
        with open(blocker, "w", encoding="utf-8") as fh:
            fh.write("not a directory\n")
        res = subprocess.run(
            [sys.executable, SCRIPT, "--root", self.root, "--json", os.path.join(blocker, "out.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        self.assertTrue(res.stderr.startswith("error:"), res.stderr)
        self.assertNotIn("Traceback", res.stderr)
        self.assertEqual(res.stdout, "")

    def test_directory_output_target_is_rejected(self):
        outdir = os.path.join(self.root, "outdir")
        os.makedirs(outdir)
        res = subprocess.run(
            [sys.executable, SCRIPT, "--root", self.root, "--md", outdir],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        self.assertIn(f"error: {outdir} is not a file", res.stderr)
        self.assertEqual(res.stdout, "")


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
        with open(os.path.join(self.root, "gifs", "DESCRIPTION.md"), "w", encoding="utf-8") as fh:
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
