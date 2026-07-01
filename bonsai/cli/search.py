"""Search the vault for files matching a query.

Ranks results by text relevance * PageRank importance derived from the
wikilink graph.
"""

import json
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

import click

from bonsai import (
    VAULT_ROOT,
    extract_link_targets,
    get_aliases,
    iter_notes,
    load_frontmatter,
    split_sections,
)

CACHE_PATH = VAULT_ROOT / ".pagerank.json"
DAMPING = 0.85
MAX_ITERATIONS = 100
CONVERGENCE_THRESHOLD = 1e-6

# Section weight table. Unlisted headings default to 1.0.
SECTION_WEIGHTS: dict[str, float] = {
    "bonsai": 0.7,
}

FUZZY_FILENAME_THRESHOLD = 0.6


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def _build_name_table(notes: list[Path]) -> dict[str, Path]:
    """Map every possible target string (stem + aliases) to a file path."""
    table: dict[str, Path] = {}
    for path in notes:
        table[path.stem.lower()] = path
        for alias in get_aliases(path):
            table[alias.lower()] = path
    return table


def build_graph(notes: list[Path]) -> tuple[dict[str, list[str]], dict[str, Path]]:
    """Build the directed link graph."""
    name_table = _build_name_table(notes)
    path_to_rel = {p: str(p.relative_to(VAULT_ROOT)) for p in notes}
    edges: dict[str, list[str]] = {rel: [] for rel in path_to_rel.values()}

    for path in notes:
        text = path.read_text()
        source = path_to_rel[path]
        seen = set()
        for target_name in extract_link_targets(text):
            resolved = name_table.get(target_name.lower())
            if resolved is None or resolved not in path_to_rel:
                continue
            dest = path_to_rel[resolved]
            if dest != source and dest not in seen:
                edges[source].append(dest)
                seen.add(dest)

    return edges, name_table


# ---------------------------------------------------------------------------
# PageRank
# ---------------------------------------------------------------------------

def compute_pagerank(edges: dict[str, list[str]]) -> dict[str, float]:
    """Iterative PageRank over the wikilink graph."""
    nodes = list(edges.keys())
    n = len(nodes)
    if n == 0:
        return {}

    rank = {node: 1.0 / n for node in nodes}
    out_degree = {node: len(targets) for node, targets in edges.items()}
    dangling = [node for node, deg in out_degree.items() if deg == 0]

    for _ in range(MAX_ITERATIONS):
        dangling_sum = sum(rank[node] for node in dangling)
        new_rank: dict[str, float] = {}

        for node in nodes:
            incoming = 0.0
            for source, targets in edges.items():
                if node in targets:
                    incoming += rank[source] / out_degree[source]

            new_rank[node] = (
                (1 - DAMPING) / n
                + DAMPING * (incoming + dangling_sum / n)
            )

        diff = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        if diff < CONVERGENCE_THRESHOLD:
            break

    return rank


def _load_cache() -> dict[str, float] | None:
    if not CACHE_PATH.exists():
        return None
    try:
        data = json.loads(CACHE_PATH.read_text())
        return data.get("scores")
    except (json.JSONDecodeError, KeyError):
        return None


def _write_cache(scores: dict[str, float]) -> None:
    data = {"timestamp": time.time(), "scores": scores}
    CACHE_PATH.write_text(json.dumps(data, indent=2) + "\n")


def get_pagerank(rebuild: bool = False) -> dict[str, float]:
    """Return PageRank scores, using cache when available."""
    if not rebuild:
        cached = _load_cache()
        if cached is not None:
            return cached

    notes = iter_notes()
    edges, _ = build_graph(notes)
    scores = compute_pagerank(edges)
    _write_cache(scores)
    return scores


# ---------------------------------------------------------------------------
# Text search
# ---------------------------------------------------------------------------

def _section_weight(heading: str) -> float:
    return SECTION_WEIGHTS.get(heading.lower(), 1.0)


def _make_word_patterns(query: str) -> list[re.Pattern]:
    """Build a word-boundary prefix pattern for each query word.

    FUTURE: swap in a real stemmer (e.g. Porter) here.
    """
    return [
        re.compile(r"\b" + re.escape(w), re.IGNORECASE)
        for w in query.lower().split()
        if w
    ]


def _fuzzy_score(query: str, candidate: str) -> float:
    """SequenceMatcher ratio, or 0.0 if below threshold."""
    ratio = SequenceMatcher(None, query.lower(), candidate.lower()).ratio()
    return ratio if ratio >= FUZZY_FILENAME_THRESHOLD else 0.0


def _score_text_match(query: str, path: Path, text: str) -> float:
    """Score a single file against the query string."""
    q = query.lower()
    score = 0.0

    # Filename: exact substring, then fuzzy fallback.
    stem_lower = path.stem.lower()
    if q in stem_lower:
        score += 3.0
    else:
        f = _fuzzy_score(q, stem_lower)
        if f > 0.0:
            score += 3.0 * f

    # Aliases: exact substring, then fuzzy fallback.
    best_alias = 0.0
    for alias in get_aliases(path):
        if q in alias.lower():
            best_alias = 2.0
            break
        f = _fuzzy_score(q, alias)
        if f > 0.0:
            best_alias = max(best_alias, 2.0 * f)
    score += best_alias

    # Body: word-prefix matching, section-weighted.
    patterns = _make_word_patterns(query)
    if not patterns:
        return score

    sections = split_sections(text)
    body_score = 0.0
    for heading, section_text in sections:
        weight = _section_weight(heading)
        for pat in patterns:
            count = len(pat.findall(section_text))
            if count > 0:
                body_score += (1.0 + (min(count, 20) - 1) * 0.05) * weight

    score += body_score
    return score


def run_search(query: str, scores: dict[str, float]) -> list[tuple[str, float]]:
    """Search the vault, ranked by combined text + PageRank score."""
    notes = iter_notes()
    results: list[tuple[str, float]] = []
    max_pr = max(scores.values()) if scores else 1.0

    for path in notes:
        text = path.read_text()
        rel = str(path.relative_to(VAULT_ROOT))
        text_score = _score_text_match(query, path, text)
        if text_score == 0.0:
            continue

        pr = scores.get(rel, 0.0)
        pr_norm = pr / max_pr if max_pr > 0 else 0.0
        combined = text_score * (1.0 + pr_norm)
        results.append((rel, combined))

    results.sort(key=lambda r: r[1], reverse=True)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.argument("query")
@click.option("--top", "-n", default=0, help="Limit number of results (0 = all).")
@click.option("--rebuild", is_flag=True, help="Force PageRank recomputation.")
def search(query: str, top: int, rebuild: bool):
    """Search the vault for QUERY, ranked by relevance and link importance."""
    scores = get_pagerank(rebuild=rebuild)
    results = run_search(query, scores)

    if not results:
        click.echo("No results.")
        return

    if top > 0:
        results = results[:top]

    for rel, score in results:
        click.echo(f"{score:8.4f}  {rel}")
