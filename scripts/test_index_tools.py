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
