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
