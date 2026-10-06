"""Tests for skill discovery and the curation tool. Run: python3 scripts/test_curate.py"""

import dataclasses
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

    def test_closing_delimiter_needs_newline_or_end_of_text(self):
        self.assertIsNone(frontmatter_span("---\nname: a\n--- body that never closes"))
        self.assertIsNone(frontmatter_span("---\nname: a\n---junk\nmore\n"))

    def test_opening_delimiter_must_be_exactly_three_dashes(self):
        self.assertIsNone(frontmatter_span("----\nname: a\n---\n"))
        self.assertIsNone(frontmatter_span("---"))

    def test_empty_frontmatter_closed_by_end_of_text(self):
        self.assertEqual(frontmatter_span("---\n---"), "---\n---")


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
        self.assertIsInstance(skill, Skill)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            skill.name = "other"
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

    def test_malformed_yaml_frontmatter_yields_empty_fields(self):
        path = os.path.join(self.root, "badyaml")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: badyaml\ndescription: [docs](url)\n---\n\n# hi\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "")
        self.assertEqual(skill.description, "")
        self.assertGreater(skill.fm_chars, 0)

    def test_non_utf8_file_is_skipped(self):
        path = os.path.join(self.root, "binary")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "wb") as fh:
            fh.write(b"---\nname: \xff\xfe\n---\n")
        self.assertEqual(discover_skills(self.root), [])

    def test_bom_prefixed_frontmatter_is_discovered(self):
        path = os.path.join(self.root, "bom")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "wb") as fh:
            fh.write(b"\xef\xbb\xbf---\nname: bomskill\ndescription: Has a BOM.\n---\n\n# hi\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "bomskill")
        self.assertEqual(skill.description, "Has a BOM.")

    def test_missing_root_raises_file_not_found(self):
        missing = os.path.join(self.root, "does-not-exist")
        with self.assertRaises(FileNotFoundError) as ctx:
            discover_skills(missing)
        self.assertIn(missing, str(ctx.exception))

    def test_root_that_is_a_file_raises_not_a_directory(self):
        afile = os.path.join(self.root, "plain.txt")
        with open(afile, "w", encoding="utf-8") as fh:
            fh.write("not a dir")
        with self.assertRaises(NotADirectoryError) as ctx:
            discover_skills(afile)
        self.assertIn(afile, str(ctx.exception))

    def test_non_string_description_scalar_is_stringified(self):
        path = os.path.join(self.root, "numeric")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: numeric\ndescription: 42\n---\n\n# hi\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.description, "42")

    def test_crlf_frontmatter_is_discovered(self):
        path = os.path.join(self.root, "crlf")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8", newline="") as fh:
            fh.write("---\r\nname: crlfskill\r\ndescription: Windows ends.\r\n---\r\n\r\n# hi\r\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "crlfskill")
        self.assertEqual(skill.description, "Windows ends.")

    def test_unicode_name_and_description_preserved(self):
        write_skill(self.root, "i18n", "日本語スキル 🚀", "絵文字と中文描述 ✨")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "日本語スキル 🚀")
        self.assertEqual(skill.description, "絵文字と中文描述 ✨")

    def test_deeply_nested_yaml_recursion_error_yields_empty_fields(self):
        path = os.path.join(self.root, "deep")
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(
                "---\nname: deep\ndescription: " + "[" * 600 + "]" * 600 + "\n---\n\n# hi\n"
            )
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.name, "")
        self.assertEqual(skill.description, "")
        self.assertGreater(skill.fm_chars, 0)

    def test_root_skill_md_yields_dot_path(self):
        with open(os.path.join(self.root, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: toproot\ndescription: At the root.\n---\n\n# hi\n")
        (skill,) = discover_skills(self.root)
        self.assertEqual(skill.path, ".")
        self.assertEqual(skill.name, "toproot")


if __name__ == "__main__":
    unittest.main(verbosity=2)
