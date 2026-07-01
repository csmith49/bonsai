---
name: trace
description: Find related sources for a reference by following citations, discussions, and links.
---

You are tracing outward from a reference to find related sources.

## Setup

Before tracing, build a dedup list. Use search to check whether a candidate already exists:

```bash
python -m bonsai search "<candidate title>"
```

A match in the results means the ref exists -- skip it. Do this for every candidate before proposing it.

Read the source URL and kind from the reference's front-matter. Use fetch to get the source text:

```bash
python -m bonsai fetch "<ref-name-or-url>"
```

## Where to look

Search these four channels and label each finding by how it was found:

* **Bibliography** -- papers and works cited by the source. For papers, the references section is the primary vein. For blog posts, follow inline links.
* **Forward citations** -- work that cites this source. Use Semantic Scholar or Google Scholar. These tend to surface the most interesting recent work; prioritize them.
* **Discussion threads** -- search Hacker News (use `hn.algolia.com`), Reddit, OpenReview, and forum posts. Discussion threads surface practical and opinion pieces that don't appear in citation graphs.
* **Inline links** -- tools, datasets, repos, related projects linked from the body of the source.

## Arxiv papers

Use the HTML rendering (`https://arxiv.org/html/<id>`) instead of the PDF. Links are extractable and the bibliography is structured.

## Batch tracing

When tracing multiple refs at once, spawn one sub-agent per ref and run them in parallel. Pass each sub-agent the full dedup list (existing refs + refs already proposed by earlier traces). After all agents return, consolidate and deduplicate. Sources that appear in multiple traces are strong signals -- flag them.

## Output format

Group findings by channel (Bibliography, Forward citations, Discussion, Inline links). For each proposed ref, include:

* **Title** -- what the ref file should be named (use the source's title, with ` -- ` replacing `:` in filenames)
* **URL** -- the source URL
* **Kind** -- one of: `paper`, `blog`, `tool`, `reporting`, `benchmark`
* **Why** -- one sentence on why it's relevant to the original reference

## Adding accepted refs

Create a new file in `refs/` with this format:

```
---
kind: <kind>
url: <url>
---
```

## Mailbox

After tracing, leave the vault owner a summary of what you found:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Traced <ref>: found N new sources. Created refs for: X, Y, Z." --context "refs/<ref>"
```

If you find sources that look important but couldn't be added (paywalled, ambiguous, needs the vault owner's judgment), leave a note:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Found <title> while tracing <ref> but couldn't access it: <reason>"
```
