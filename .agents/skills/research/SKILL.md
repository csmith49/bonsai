---
name: research
description: Research a reference and update BONSAI-managed reference notes.
---

You are researching a reference.

## Fetching the source

Use the fetch script to get the source text:

```bash
python -m bonsai fetch "<ref-name-or-url>"
```

This handles arxiv (rewrites to HTML), GitHub repos (fetches README), generic HTML (extracts article body), and PDFs (basic text extraction). You can pass either a URL or a ref filename (e.g. `python -m bonsai fetch "YourMemory"` reads the URL from front-matter).

### When fetch fails

The fetch script rewrites all arxiv URLs to `/html/` format, but many older papers (pre-2023) don't have HTML renderings. If you get a 404, try the PDF URL directly:

```bash
python -m bonsai fetch "https://arxiv.org/pdf/<id>"
```

PDF extraction is basic (stdlib zlib, approximate word spacing), but it's better than nothing. If both HTML and PDF fail, try version suffixes (`v1`, `v2`, etc.).

For blog posts, the HTML extractor relies on CSS selectors and sometimes captures only navigation/metadata instead of article content. If the result looks like boilerplate, the source may require a different extraction approach or may not be fetchable.

If the source truly can't be found (dead link, paywall, takedown), look for other hosts and web archives (Wayback Machine, Google Cache, mirrors). If it still can't be found, note the failed attempt with the date in the BONSAI section and stop. Leave a mailbox message for the vault owner noting the failed fetch:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Fetch failed for <ref>: <reason>" --context "refs/<ref>"
```

### Navigating long sources

A single fetch piped to `head -500` often misses results, discussion, and conclusion sections. For papers longer than a few pages, fetch in multiple passes:

```bash
python -m bonsai fetch "<ref>" 2>&1 | head -500          # intro/method
python -m bonsai fetch "<ref>" 2>&1 | tail -600 | head -400  # later sections
python -m bonsai fetch "<ref>" 2>&1 | grep -A200 "^5 "   # target a specific section
```

## Before writing

Read the existing ref file first. If the vault owner has already written notes in the body (above where `## BONSAI` will go), read them before writing. Your BONSAI section should complement the vault owner's notes, not repeat them. Focus on what the vault owner didn't cover: the source's searchable gist, useful connections, trust-relevant caveats, and open questions.

## Writing the notes

The BONSAI section is a retrieval blurb, not a paper review or source of truth. Its job is to make the reference findable later from vague searches and useful for building connections across the vault. Future the vault owner should be able to search for half-remembered phrases like "LLMs can't track optimization state", "context as fast weights", or "benchmark closure isn't science" and land on the right ref. If future work needs exact details, it should fetch/read the original source, not rely on the blurb.

Ground every factual claim in what the source actually states. Authors, dates, benchmarks, numerical results, and methodology descriptions must come directly from the source text -- never infer or fill in from memory. If you can't confirm a fact from the source, leave it out. Do not assume authorship or institutional affiliation based on related work or thematic similarity. When describing how a method works, use the process the source actually describes -- don't substitute a plausible-sounding mechanism.

Write for search and connection:

* Start with the plain-English gist: what problem this source is about, what it claims, and why it matters.
* Include the conceptual hooks someone might search for later: domain, method family, failure mode, contrast, metaphor, benchmark/task, and adjacent ideas.
* Prefer memorable phrasing over exhaustive detail. A good paragraph names the shape of the idea, not every table.
* Explain the source's place in the graph: what it supports, challenges, extends, or reframes.
* Note weaknesses only when they change how the source should be used or trusted.
* Add open questions when they mark a useful future thread.

Numbers are optional. Include a number only when it is part of the story someone would remember or search for: a headline result, surprising scale, decisive comparison, or constraint that changes the interpretation. Do not copy benchmark tables, dense score lists, affiliation lists, or metric details just because they are available.

**Quote directly** only when the source's wording is itself a useful hook, unusually revealing, or worth scrutinising. A quote is not mandatory. If a paraphrase would be more searchable, paraphrase.

Aim for 150-350 words by default. Longer is fine only when the source has multiple distinct ideas that future searches need to distinguish. The source is always there for the real details -- these notes exist to tell future us when and why we'd want to go back to it.

### Useful shape

```markdown
## BONSAI

[One paragraph with the searchable gist: problem, claim, why it matters, and the phrases future the vault owner might search for.]

[One paragraph on connections: what this ref supports/challenges/reframes, with wikilinks where the connection is real. Include caveats or open questions only if they affect how to use the source.]
```

### Search calibration

After drafting the BONSAI section, test whether it is findable. Generate 3-5 vague phrases future the vault owner might search for if he remembered the idea but not the title. Use phrases about the problem shape, failure mode, metaphor, or connection -- not exact title words.

Run searches like:

```bash
python -m bonsai search -n 10 "<vague phrase>"
```

The ref should land in the top 10 for at least one good vague query, and ideally top 5 for the strongest query. If it doesn't, revise the blurb to include more natural retrieval hooks. Don't append a keyword dump; rewrite the gist so the missing phrase belongs in the prose.

If you added or changed wikilinks, run one calibration search with `--rebuild` so PageRank reflects the new graph:

```bash
python -m bonsai search --rebuild "<vague phrase>"
```

## Mailbox

When you finish researching a ref, leave the vault owner a message:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Researched <ref>. BONSAI section added." --context "refs/<ref>"
```

If you notice something worth following up on -- a promising citation, a contradictory claim, a related ref that needs research -- leave yourself a reminder:

```bash
python -m bonsai mailbox send --from bonsai --to bonsai "<what to follow up>" --context "refs/<ref>"
```

## Linking

Use links to make the blurb connective, not decorative. Link to refs, maps, people, or zk entries when the connection helps future traversal: direct citation, shared method, same failure mode, explicit contrast, or a concept the vault owner is actively developing. Don't force thematic links. Before linking to another ref, prefer refs that already have a `## BONSAI` section; unread refs can be mentioned plain-text unless the link is necessary. To see which refs lack BONSAI sections:

```bash
python -m bonsai lint missing-bonsai
```

Use `python -m bonsai search "<terms>"` to find candidate refs to link to.

Write your notes in a `## BONSAI` section at the end of the reference file, after any existing content. This keeps BONSAI's notes separate from the vault owner's. **Never write outside the `## BONSAI` section.** The body area between the frontmatter and `## BONSAI` belongs to the vault owner. If it's empty, leave it empty. All AI-generated content -- summaries, analysis, connections, commentary -- goes inside `## BONSAI` and nowhere else.
