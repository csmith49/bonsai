# bonsai

Opinionated AI agent utilities for Obsidian-style knowledge bases.

Bonsai started as infrastructure inside a personal notes vault. This repository extracts the reusable parts: a Python CLI, OpenHands-style skills, and copyable vault templates.

## What Bonsai provides

- **Vault search**: text relevance combined with PageRank over `[[wikilinks]]`.
- **Source fetching**: fetch URLs or `refs/` entries, with special handling for arXiv, GitHub READMEs, HTML, and PDFs.
- **Reference linting**: find refs missing frontmatter, URLs, kinds, or `## BONSAI` sections.
- **Activity digests**: summarize recent journal activity, linked refs, unread refs, and modified refs.
- **Mailbox**: a JSONL queue for asynchronous owner/BONSAI messages.
- **Zettelkasten helpers**: create, search, lint, and outline atomic notes in `zk/`.
- **Agent skills**: reusable workflows for research, search, linking, QA, reading lists, mailbox triage, daily assistance, tracing, and zk work.

## Expected vault layout

Bonsai is loose about structure, but these directories unlock the full workflow:

```text
journal/   daily notes; used by digest and assist workflows
refs/      source references with frontmatter such as kind/url/aliases
maps/      curated topic maps
people/    people notes
zk/        atomic zettelkasten notes
threads/   speculative working threads
.agents/   optional agent skills
```

Reference files usually look like this:

```markdown
---
kind: paper
url: https://example.com/source
aliases:
  - Optional Alias
---

## BONSAI

Short agent-written retrieval blurb and connective notes.
```

`## BONSAI` sections are search handles, not a replacement for source text.

## Install

From this repository:

```bash
python -m pip install -e .
```

Then run Bonsai from a vault root:

```bash
bonsai search "agent skills"
```

If you do not install the console script, use:

```bash
python -m bonsai search "agent skills"
```

To target a vault from another directory:

```bash
BONSAI_VAULT_ROOT=/path/to/vault python -m bonsai search "agent skills"
```

## CLI reference

### Search

```bash
python -m bonsai search "query"
python -m bonsai search -n 10 "query"
python -m bonsai search --rebuild "query"
```

Search ranks markdown files by text relevance multiplied by PageRank importance from the wikilink graph. PageRank is cached in `.pagerank.json` at the vault root.

### Fetch

```bash
python -m bonsai fetch "https://example.com/article"
python -m bonsai fetch "Ref Name"
python -m bonsai fetch --save "Ref Name"
python -m bonsai fetch --pdf "Arxiv Ref"
```

A non-URL target resolves to `refs/<target>.md` and reads `url` from frontmatter. `--save` and `--pdf` write to `~/Downloads/`.

### Digest

```bash
python -m bonsai digest
python -m bonsai digest -d 14
```

Digest reads recent `journal/YYYY-MM-DD.md` files, counts wikilinks, lists linked refs missing `## BONSAI`, and shows recently modified refs.

### Lint

```bash
python -m bonsai lint
python -m bonsai lint missing-bonsai
python -m bonsai lint missing-kind
python -m bonsai lint missing-url
python -m bonsai lint bad-url
python -m bonsai lint frontmatter-only
```

### Mailbox

```bash
python -m bonsai mailbox send --from owner --to bonsai "Please research X"
python -m bonsai mailbox unread
python -m bonsai mailbox unread --for owner
python -m bonsai mailbox list --short
python -m bonsai mailbox read <id-prefix>
python -m bonsai mailbox count --for bonsai
```

Messages are stored in `.mailbox.jsonl`, which should stay gitignored.

### ZK

```bash
python -m bonsai zk related "topic"
python -m bonsai zk related path/to/note.md
python -m bonsai zk new "Card title" --link "refs/Source" --tag synthesis
python -m bonsai zk lint
python -m bonsai zk outline <note> --depth 2 --include-refs
```

## Agent infrastructure

The repository includes OpenHands-style skills under `.agents/skills/` and a copyable vault template under `templates/.agents/skills/`.

To add Bonsai to a vault:

```bash
cp templates/AGENTS.md /path/to/vault/AGENTS.md
cp templates/.gitignore /path/to/vault/.gitignore
cp -R templates/.agents /path/to/vault/.agents
```

Then install this package in the environment your agent uses, or ensure `python -m bonsai` can import the repository.

## Utility scripts

- `scripts/backup-vault.sh [vault] [branch]`: commit and push vault changes if there are any.

## Runtime files

Keep these out of version control in vaults:

- `.pagerank.json`
- `.mailbox.jsonl`
- `.DS_Store`
- `__pycache__/`
