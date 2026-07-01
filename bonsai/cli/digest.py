"""Digest recent vault activity.

Summarises recent journals, wikilink frequency, unread refs, and
recently-modified refs -- structured data that the assist and reading
skills consume.
"""

import re
from datetime import date, timedelta
from pathlib import Path

import click

from bonsai import (
    VAULT_ROOT,
    REFS_DIR,
    extract_link_targets,
    iter_refs,
    load_frontmatter,
)

JOURNAL_DIR = VAULT_ROOT / "journal"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _journal_date(path: Path) -> date | None:
    stem = path.stem
    if not DATE_RE.match(stem):
        return None
    try:
        return date.fromisoformat(stem)
    except ValueError:
        return None


def _recent_journals(days: int) -> list[Path]:
    """Return journal files from the last *days* days, newest first."""
    cutoff = date.today() - timedelta(days=days)
    results = []
    for path in sorted(JOURNAL_DIR.glob("*.md"), reverse=True):
        d = _journal_date(path)
        if d is not None and d >= cutoff:
            results.append(path)
    return results


def _has_bonsai(path: Path) -> bool:
    text = path.read_text()
    return "\n## BONSAI" in text or text.startswith("## BONSAI")


def _ref_name_table() -> dict[str, Path]:
    """Map lowercase stem and aliases to ref paths."""
    table: dict[str, Path] = {}
    for path in iter_refs():
        table[path.stem.lower()] = path
        try:
            post = load_frontmatter(path)
            for alias in post.metadata.get("aliases", []) or []:
                table[alias.lower()] = path
        except Exception:
            pass
    return table


def _recently_modified_refs(days: int) -> list[tuple[Path, date]]:
    """Return refs modified within *days* days, newest first."""
    cutoff = date.today() - timedelta(days=days)
    results = []
    for path in iter_refs():
        mtime = date.fromtimestamp(path.stat().st_mtime)
        if mtime >= cutoff:
            results.append((path, mtime))
    results.sort(key=lambda r: r[1], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Core digest
# ---------------------------------------------------------------------------

def build_digest(days: int) -> dict:
    """Gather all digest data and return as a structured dict."""
    journals = _recent_journals(days)
    ref_table = _ref_name_table()

    # Extract wikilinks from recent journals
    link_counts: dict[str, int] = {}
    linked_ref_paths: set[Path] = set()

    for jpath in journals:
        text = jpath.read_text()
        for target in extract_link_targets(text):
            link_counts[target] = link_counts.get(target, 0) + 1
            resolved = ref_table.get(target.lower())
            if resolved is not None:
                linked_ref_paths.add(resolved)

    # Sort links by frequency
    sorted_links = sorted(link_counts.items(), key=lambda r: r[1], reverse=True)

    # Unread refs: linked from recent journals but lacking BONSAI section
    unread = sorted(
        [p for p in linked_ref_paths if not _has_bonsai(p)],
        key=lambda p: p.stem,
    )

    # Recently modified refs
    modified = _recently_modified_refs(days)

    return {
        "journals": journals,
        "link_counts": sorted_links,
        "unread_refs": unread,
        "modified_refs": modified,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--days", "-d", default=7, help="Look-back window in days (default 7).")
def digest(days: int):
    """Digest recent vault activity."""
    data = build_digest(days)

    rel = lambda p: str(p.relative_to(VAULT_ROOT))

    # Recent journals
    click.echo("## Recent journals")
    for path in data["journals"]:
        click.echo(f"  {rel(path)}")
    click.echo()

    # Wikilink frequency
    click.echo("## Wikilink frequency (from recent journals)")
    for target, count in data["link_counts"]:
        click.echo(f"  {count:3d}  {target}")
    click.echo()

    # Unread refs
    click.echo("## Unread refs (linked recently, no BONSAI section)")
    if data["unread_refs"]:
        for path in data["unread_refs"]:
            click.echo(f"  {rel(path)}")
    else:
        click.echo("  (none)")
    click.echo()

    # Recently modified refs
    click.echo("## Recently modified refs")
    if data["modified_refs"]:
        for path, mtime in data["modified_refs"]:
            click.echo(f"  {mtime}  {rel(path)}")
    else:
        click.echo("  (none)")
