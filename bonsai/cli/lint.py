"""Lint tools for the Obsidian vault."""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

from bonsai import VAULT_ROOT, iter_refs, load_frontmatter


# ---------------------------------------------------------------------------
# Per-file snapshot -- loaded once, checked many times
# ---------------------------------------------------------------------------

@dataclass
class RefInfo:
    path: Path
    text: str
    metadata: dict = field(default_factory=dict)
    content: str = ""


def _load_refs() -> list[RefInfo]:
    """Load every ref file once and return structured snapshots."""
    refs = []
    for path in iter_refs():
        text = path.read_text()
        try:
            post = load_frontmatter(path)
            refs.append(RefInfo(path, text, post.metadata or {}, post.content))
        except Exception:
            refs.append(RefInfo(path, text))
    return refs


# ---------------------------------------------------------------------------
# Checks -- each takes a RefInfo and returns True if the issue is present
# ---------------------------------------------------------------------------

def _is_frontmatter_only(ref: RefInfo) -> bool:
    return bool(ref.metadata) and not ref.content.strip()


def _is_missing_bonsai(ref: RefInfo) -> bool:
    return "\n## BONSAI" not in ref.text and not ref.text.startswith("## BONSAI")


def _is_missing_kind(ref: RefInfo) -> bool:
    return "kind" not in ref.metadata


def _is_missing_url(ref: RefInfo) -> bool:
    return "url" not in ref.metadata


_BAD_URL_RE = re.compile(r"^(?!https?://)|^jhttps?://|arxiv\.org/\d")

def _is_bad_url(ref: RefInfo) -> bool:
    url = ref.metadata.get("url", "")
    if not url:
        return False
    return bool(_BAD_URL_RE.search(url))


CHECKS = {
    "frontmatter-only": (_is_frontmatter_only, "No frontmatter-only files found."),
    "missing-bonsai": (_is_missing_bonsai, "No refs missing ## BONSAI section."),
    "missing-kind": (_is_missing_kind, "No refs missing kind."),
    "missing-url": (_is_missing_url, "No refs missing url."),
    "bad-url": (_is_bad_url, "No malformed URLs found."),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _run_check(name: str, refs: list[RefInfo]) -> bool:
    """Run a single named check. Returns True if any issues found."""
    check_fn, empty_msg = CHECKS[name]
    hits = [r.path for r in refs if check_fn(r)]
    if not hits:
        click.echo(empty_msg)
        return False
    for path in hits:
        click.echo(path.relative_to(VAULT_ROOT))
    return True


@click.group(invoke_without_command=True)
@click.pass_context
def lint(ctx):
    """Lint tools for the Obsidian vault.

    Run without a subcommand to execute all checks.
    """
    if ctx.invoked_subcommand is not None:
        return
    refs = _load_refs()
    found = False
    for name in CHECKS:
        if _run_check(name, refs):
            found = True
    if found:
        sys.exit(1)


@lint.command()
def frontmatter_only():
    """Report ref files that contain only frontmatter and no body content."""
    if _run_check("frontmatter-only", _load_refs()):
        sys.exit(1)


@lint.command()
def missing_bonsai():
    """Report ref files that lack a ## BONSAI section."""
    if _run_check("missing-bonsai", _load_refs()):
        sys.exit(1)


@lint.command()
def missing_kind():
    """Report ref files missing kind in frontmatter."""
    if _run_check("missing-kind", _load_refs()):
        sys.exit(1)


@lint.command()
def missing_url():
    """Report ref files missing url in frontmatter."""
    if _run_check("missing-url", _load_refs()):
        sys.exit(1)


@lint.command()
def bad_url():
    """Report ref files with malformed URLs."""
    if _run_check("bad-url", _load_refs()):
        sys.exit(1)
