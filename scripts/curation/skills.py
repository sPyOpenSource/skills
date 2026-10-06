"""Discovery and measurement of SKILL.md files in the catalog.

This module knows how to find skills and how large they are.
Tier constants (TIER_ACTIVE, TIER_ARCHIVED, VALID_TIERS) are exported here
for shared use, but tier *resolution* lives elsewhere, along with manifests
and config files.
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
    """Return the frontmatter including both delimiters, or None if absent.

    The opening delimiter must be exactly "---" on its own first line, and
    the closing "---" must be followed by a newline or the end of the text.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    while end != -1:
        after = end + 4
        if after == len(text) or text[after] == "\n":
            return text[:after]
        end = text.find("\n---", end + 1)
    return None


def _parse_frontmatter(span: str) -> dict:
    try:
        data = yaml.safe_load(span[3: span.rfind("---")])
    except (yaml.YAMLError, RecursionError):
        return {}
    return data if isinstance(data, dict) else {}


def est_tokens(fm_chars: int) -> int:
    """Rough token count for a frontmatter of fm_chars characters."""
    return fm_chars // 4


def discover_skills(root: str) -> list[Skill]:
    """Return every skill under root, sorted by install path.

    Raises FileNotFoundError or NotADirectoryError when root is unusable.
    Files whose YAML cannot be parsed yield a Skill with empty name and
    description; files that cannot be read as text are skipped entirely.
    """
    root = os.path.abspath(root)
    if not os.path.exists(root):
        raise FileNotFoundError(f"skill root does not exist: {root}")
    if not os.path.isdir(root):
        raise NotADirectoryError(f"skill root is not a directory: {root}")
    found: list[Skill] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        if "SKILL.md" not in filenames:
            continue
        # utf-8-sig strips a leading BOM when present; the text read may
        # still fail to decode, in which case the file is skipped.
        try:
            with open(
                os.path.join(dirpath, "SKILL.md"), encoding="utf-8-sig"
            ) as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        span = frontmatter_span(text)
        data = _parse_frontmatter(span) if span else {}
        name = data.get("name")
        desc = data.get("description")
        # A SKILL.md at the root itself yields rel == ".".
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
