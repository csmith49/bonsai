---
name: reading
description: Curate a reading list from unread refs related to recent vault activity.
---

You are curating a reading list for offline use.

## Gathering data

Run the digest command to get recent activity:

```bash
python -m bonsai digest -d 14
```

Also get the full list of unread refs:

```bash
python -m bonsai lint missing-bonsai
```

The digest gives you refs linked from recent journals that lack BONSAI sections. The lint output gives the complete unread set. Focus on the digest results first -- those are the most relevant.

## Reading the journals

Skim the recent journal entries listed in the digest. Identify the vault owner's current interests -- the topics, projects, and questions he's actively working on. The wikilink frequency list is a shortcut: high-frequency targets indicate active areas.

## Building the reading list

Select 5-10 refs to recommend. Rank by relevance to current activity. For each ref, include:

* **Title** -- the ref filename (as a wikilink)
* **Kind** -- from frontmatter (paper, blog, tool, etc.)
* **Why now** -- one sentence connecting it to a current thread, project, or question from the journals. Be specific: "related to the pr-review accuracy analysis" is better than "relevant to your work."

### Selection criteria

Prioritise in this order:

1. **Directly referenced** -- refs the vault owner explicitly linked in recent journals but hasn't read. These are the strongest signal.
2. **Topically adjacent** -- refs whose titles or topics connect to active threads. Use `python -m bonsai search "<topic>"` to find candidates beyond the digest output.
3. **High PageRank, unread** -- well-connected refs that the vault owner hasn't gotten to. These tend to be foundational. Check with search results -- high scores indicate importance.

Deprioritise refs that are purely tangential to current work, even if they're interesting.

## Downloading sources

If the vault owner asks for downloads, prefer PDFs for offline reading. Use `--pdf` to grab the raw PDF (arxiv papers and direct PDF URLs):

```bash
python -m bonsai fetch --pdf "<ref-name>"
```

For non-PDF sources (blogs, GitHub repos), fall back to `--save` which writes extracted text:

```bash
python -m bonsai fetch --save "<ref-name>"
```

Both flags save to `~/Downloads/`. Only download if explicitly asked. The default output is the ranked reading list.
