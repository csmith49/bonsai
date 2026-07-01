"""Zettelkasten helpers for the Obsidian vault."""

import re
import sys
import uuid
from collections import Counter, deque
from pathlib import Path

import click

from bonsai import (
    VAULT_ROOT,
    WIKILINK_RE,
    extract_link_targets,
    get_aliases,
    iter_notes,
)
from bonsai.cli.search import build_graph, get_pagerank, run_search

ZK_DIR = VAULT_ROOT / "zk"
MAPS_DIR = VAULT_ROOT / "maps"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rel(path: Path) -> str:
    return str(path.relative_to(VAULT_ROOT))


def _title(path: Path) -> str:
    try:
        for line in path.read_text(errors="ignore").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return path.stem


def _note_by_rel(rel: str) -> Path:
    return VAULT_ROOT / rel


def _name_keys(path: Path) -> set[str]:
    rel = _rel(path)
    keys = {path.stem.lower(), rel.lower()}
    if rel.endswith(".md"):
        keys.add(rel[:-3].lower())
    title = _title(path)
    if title:
        keys.add(title.lower())
    for alias in get_aliases(path):
        keys.add(alias.lower())
    return keys


def _build_name_table(notes: list[Path]) -> dict[str, Path]:
    table: dict[str, Path] = {}
    for path in notes:
        for key in _name_keys(path):
            table[key] = path
    return table


def _resolve_note(target: str, name_table: dict[str, Path] | None = None) -> Path | None:
    raw = target.strip()
    candidates = [
        Path(raw).expanduser(),
        VAULT_ROOT / raw,
        ZK_DIR / raw,
        ZK_DIR / f"{raw}.md",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    table = name_table if name_table is not None else _build_name_table(iter_notes())
    return table.get(raw.lower())


def _target_to_query(target: str) -> tuple[str, Path | None]:
    notes = iter_notes()
    name_table = _build_name_table(notes)
    path = _resolve_note(target, name_table)
    if path is None:
        return target, None

    text = path.read_text(errors="ignore")
    paragraphs = [
        " ".join(block.split())
        for block in re.split(r"\n\s*\n", text)
        if block.strip() and not block.lstrip().startswith("---")
    ]
    title = _title(path)
    body = " ".join(paragraphs[:2])
    return f"{title} {body}".strip(), path


def _is_thread_or_outline(rel: str) -> bool:
    path = Path(rel)
    return rel.startswith("threads/") or (rel.startswith("zk/OUTLINE-") and path.suffix == ".md")


def _in_scope(rel: str, scope: str, include_threads: bool) -> bool:
    if not include_threads and _is_thread_or_outline(rel):
        return False
    if scope == "zk":
        return rel.startswith("zk/")
    if scope == "maps":
        return rel.startswith("zk/") or rel.startswith("maps/")
    return True


def _print_result(rel: str, score: float) -> None:
    path = _note_by_rel(rel)
    title = _title(path)
    click.echo(f"{score:8.4f}  {rel}  {title}")


# ---------------------------------------------------------------------------
# related
# ---------------------------------------------------------------------------

@click.group()
def zk():
    """Zettelkasten helpers."""


@zk.command()
@click.argument("target")
@click.option("--top", "top", "-n", default=10, show_default=True, help="Number of results.")
@click.option(
    "--scope",
    type=click.Choice(["zk", "maps", "all"]),
    default="zk",
    show_default=True,
    help="Where to look after running the normal vault search.",
)
@click.option("--include-threads", is_flag=True, help="Include zk/THREADS.md and outline files.")
@click.option("--rebuild", is_flag=True, help="Force PageRank recomputation before searching.")
def related(target: str, top: int, scope: str, include_threads: bool, rebuild: bool):
    """Find zk notes related to TARGET using the existing search ranking.

    TARGET can be a free-text query or a vault path/note title. Results are produced
    by the normal bonsai search and then filtered to the requested scope.
    """
    query, source_path = _target_to_query(target)
    source_rel = _rel(source_path) if source_path and source_path.is_relative_to(VAULT_ROOT) else None
    scores = get_pagerank(rebuild=rebuild)
    results = []
    for rel, score in run_search(query, scores):
        if rel == source_rel:
            continue
        if _in_scope(rel, scope, include_threads):
            results.append((rel, score))
        if len(results) >= top:
            break

    if not results:
        click.echo("No related notes found.")
        return

    for rel, score in results:
        _print_result(rel, score)


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------

def _resolved_targets(notes: list[Path]) -> set[str]:
    names = set()
    for path in notes:
        names.update(_name_keys(path))
    return names


@zk.command(name="lint")
@click.option("--strict", is_flag=True, help="Exit non-zero if warnings are found.")
def zk_lint(strict: bool):
    """Loose lint for zk notes.

    These are warnings, not hard style rules. The goal is to surface likely graph
    hygiene issues without forcing every card into one format.
    """
    notes = iter_notes()
    known = _resolved_targets(notes)
    zk_files = sorted(ZK_DIR.glob("*.md"))
    warnings: list[str] = []
    titles: Counter[str] = Counter()

    for path in zk_files:
        text = path.read_text(errors="ignore")
        rel = _rel(path)
        title = _title(path)
        if title == path.stem:
            warnings.append(f"{rel}: no '# Title' heading")
        else:
            titles[title.lower()] += 1

        body = text.strip()
        if not body:
            warnings.append(f"{rel}: empty file")
            continue

        if not _is_thread_or_outline(rel) and not extract_link_targets(text):
            warnings.append(f"{rel}: no wikilinks")

        for raw in WIKILINK_RE.findall(text):
            target = raw.split("|", 1)[0].strip()
            target_name = target.split("#", 1)[0].strip()
            if not target_name or target_name.startswith(("http://", "https://")):
                continue
            if target_name.lower() not in known:
                warnings.append(f"{rel}: unresolved wikilink [[{target}]]")

    duplicate_titles = {title for title, count in titles.items() if count > 1}
    if duplicate_titles:
        for path in zk_files:
            title = _title(path).lower()
            if title in duplicate_titles:
                warnings.append(f"{_rel(path)}: duplicate title '{_title(path)}'")

    if not warnings:
        click.echo("No zk lint warnings.")
        return

    for warning in warnings:
        click.echo(warning)
    if strict:
        sys.exit(1)


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------

@zk.command()
@click.argument("title")
@click.option("--link", "links", multiple=True, help="Initial wikilink target. Repeatable.")
@click.option("--tag", "tags", multiple=True, help="Initial tag without or with '#'. Repeatable.")
def new(title: str, links: tuple[str, ...], tags: tuple[str, ...]):
    """Create a new zk note with a random short id."""
    ZK_DIR.mkdir(exist_ok=True)
    for _ in range(20):
        note_id = uuid.uuid4().hex[:8]
        path = ZK_DIR / f"{note_id}.md"
        if not path.exists():
            break
    else:
        raise click.ClickException("could not generate a unique zk id")

    normalized_tags = [tag if tag.startswith("#") else f"#{tag}" for tag in tags]
    link_line = ", ".join(f"[[{link}]]" for link in links)
    tag_line = " ".join(normalized_tags)
    path.write_text(
        f"# {title.strip()}\n\n"
        "---\n"
        f"Links: {link_line}\n"
        f"Tags: {tag_line}\n"
    )
    click.echo(_rel(path))


# ---------------------------------------------------------------------------
# outline
# ---------------------------------------------------------------------------

def _label(rel: str) -> str:
    return f"{rel} — {_title(_note_by_rel(rel))}"


def _outline_edges() -> tuple[dict[str, list[str]], dict[str, Path]]:
    notes = iter_notes()
    return build_graph(notes)


@zk.command()
@click.argument("target")
@click.option("--depth", default=1, show_default=True, help="Outgoing-link traversal depth.")
@click.option("--include-refs", is_flag=True, help="Include refs in the outline.")
@click.option("--include-maps", is_flag=True, help="Include maps in the outline.")
def outline(target: str, depth: int, include_refs: bool, include_maps: bool):
    """Print a small outgoing-link neighborhood for TARGET."""
    notes = iter_notes()
    name_table = _build_name_table(notes)
    path = _resolve_note(target, name_table)
    if path is None or not path.is_relative_to(VAULT_ROOT):
        raise click.ClickException("target note not found")

    edges, _ = _outline_edges()
    root = _rel(path)
    click.echo(_label(root))

    seen = {root}
    queue = deque([(root, 0, "")])
    while queue:
        rel, level, prefix = queue.popleft()
        if level >= depth:
            continue

        children = []
        for child in edges.get(rel, []):
            if child.startswith("zk/"):
                children.append(child)
            elif include_maps and child.startswith("maps/"):
                children.append(child)
            elif include_refs and child.startswith("refs/"):
                children.append(child)

        for i, child in enumerate(children):
            last = i == len(children) - 1
            branch = "└── " if last else "├── "
            click.echo(f"{prefix}{branch}{_label(child)}")
            if child not in seen:
                seen.add(child)
                extension = "    " if last else "│   "
                queue.append((child, level + 1, prefix + extension))
