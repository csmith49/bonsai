---
name: search
description: Find notes in the knowledge base using text search ranked by wikilink importance.
---

You are searching the knowledge base to find relevant notes.

Run `python -m bonsai search "query"` with a short keyword or phrase. Results are ranked by a combination of text relevance and PageRank importance derived from the wikilink graph. Higher-scored files are both better textual matches and more connected within the vault.

```
python -m bonsai search "query"            # all results
python -m bonsai search -n 10 "query"      # top 10
python -m bonsai search --rebuild "query"   # recompute PageRank first
```

## Choosing good queries

Single keywords work best for broad exploration. Multi-word queries score each word independently -- a file matching both "skill" and "library" ranks above one matching only "skill".

Word-prefix matching is built in: "agent" finds "agents" and "agentic". Fuzzy matching catches typos in filenames and aliases. You don't need to be precise.

If a broad query returns too much, narrow with a second word. If a narrow query returns nothing, drop to a single keyword.

## When to use search

Use search as your first step when you need to:

- Find existing notes on a topic before writing or linking
- Discover which refs, maps, or people notes are related to a concept
- Check whether a reference already exists before creating one
- Gather context for a `link`, `research`, or `trace` task

## Interpreting results

Output is one line per hit: `score  path`. The score is not meaningful on its own -- use it only for relative ordering within a single query. Files from `refs/`, `maps/`, and `people/` tend to be more useful starting points than journal entries.

## When to rebuild

Pass `--rebuild` if you've recently added or edited notes with new wikilinks. The PageRank cache is otherwise reused across searches.
