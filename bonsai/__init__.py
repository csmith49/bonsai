"""Shared infrastructure for the Bonsai CLI.

Bonsai commands operate on an Obsidian-style markdown vault. By default the
vault root is the current working directory; set ``BONSAI_VAULT_ROOT`` to run
commands against a different vault.
"""

import os
import re
from pathlib import Path

import frontmatter as _fm


def _vault_root() -> Path:
    configured = os.environ.get("BONSAI_VAULT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.cwd().resolve()


VAULT_ROOT = _vault_root()
REFS_DIR = VAULT_ROOT / "refs"

EXCLUDED_DIRS = {".git", ".agents", ".obsidian", ".venv", "node_modules", "personal"}

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)


def iter_notes() -> list[Path]:
    """Return all markdown files in the vault, excluding tool/private dirs."""
    results = []
    for path in VAULT_ROOT.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(VAULT_ROOT).parts):
            continue
        results.append(path)
    return sorted(results)


def iter_refs() -> list[Path]:
    """Return all markdown files in refs/, sorted."""
    if not REFS_DIR.exists():
        return []
    return sorted(REFS_DIR.glob("*.md"))


def load_frontmatter(path: Path) -> _fm.Post:
    """Load a markdown file's frontmatter. Raises on parse failure."""
    return _fm.load(path)


def get_aliases(path: Path) -> list[str]:
    """Return the aliases list from frontmatter, or an empty list."""
    try:
        post = load_frontmatter(path)
        aliases = post.metadata.get("aliases", []) or []
        if isinstance(aliases, str):
            return [aliases]
        return list(aliases)
    except Exception:
        return []


def get_url(path: Path) -> str | None:
    """Return the url from frontmatter, or None."""
    try:
        post = load_frontmatter(path)
        return post.metadata.get("url")
    except Exception:
        return None


def resolve_ref(name: str) -> Path | None:
    """Find a ref file by name, with or without the .md extension."""
    for candidate in [REFS_DIR / name, REFS_DIR / f"{name}.md"]:
        if candidate.is_file():
            return candidate
    return None


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs.

    Text before the first heading is returned with an empty heading.
    """
    splits = list(HEADING_RE.finditer(text))
    if not splits:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    if splits[0].start() > 0:
        sections.append(("", text[: splits[0].start()]))

    for i, match in enumerate(splits):
        heading = match.group(2).strip()
        start = match.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        sections.append((heading, text[start:end]))

    return sections


def extract_link_targets(text: str) -> list[str]:
    """Pull wikilink targets from markdown text.

    Handles both [[Target]] and [[Target|Display]] forms.
    """
    targets = []
    for match in WIKILINK_RE.finditer(text):
        raw = match.group(1)
        target = raw.split("|", 1)[0].strip()
        targets.append(target)
    return targets
