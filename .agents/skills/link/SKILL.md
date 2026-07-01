---
name: link
description: Add wikilinks to a reference by connecting it to existing notes.
---

You are adding `[[wikilinks]]` to a reference.

## Finding link targets

Use search to find candidate notes to link to:

```bash
python -m bonsai search "<terms from the reference>"
```

Also scan filenames in `refs/`, `people/`, `maps/`, and `zk/` for direct matches.

Only link to refs that have a `## BONSAI` section (i.e. they've been read). To check which refs are missing one:

```bash
python -m bonsai lint missing-bonsai
```

## Linking rules

Read through the reference and identify terms that match existing notes. Wrap them in `[[wikilinks]]`. Don't link to the note's own filename.

**One link per target per block.** Blocks are separated by `---`. Within a single block, link only the first occurrence of any given target. If the file has no `---` separators (outside front-matter), treat the entire body as one block.

Don't force links. If a term appears but the connection is incidental, leave it plain.
