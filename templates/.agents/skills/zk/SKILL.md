---
name: zk
description: Manage the zettelkasten -- add, browse, link, refine, and structure atomic notes for idea development.
---

You are managing the vault owner's zettelkasten, located at `zk/`.

The zettelkasten is a thinking tool. Notes exist to develop ideas through connection, not to store information. That's what `refs/` is for. A zk entry captures a claim, observation, or question in the vault owner's own words and wires it into the graph.

## When to use

- the vault owner wants to capture an idea, observation, or question
- the vault owner wants to browse, search, or traverse existing entries
- the vault owner wants to refine, split, merge, or challenge existing entries
- the vault owner wants to review threads or build an outline from connected cards
- A brainstorming session produces something worth crystallising

## Files

- **Location:** `zk/`
- **Naming:** 8-character hex UUID. Prefer `python -m bonsai zk new "Title"` to create new cards.
- **One atomic idea per file.** If an entry makes two distinct claims, split it. The test: could someone disagree with half of this note? If yes, it's two notes.

## Entry structure

```markdown
# [short title -- a phrase, not a sentence]

[The idea. A few sentences max. One claim, observation, question, or connection.
Written in the vault owner's voice, first person.]

---
Links: [[id1|description]], [[id2|description]]
Tags: #tag1 #tag2
```

### Title

A noun phrase that names the idea, not a sentence that states it. "Sharpness of search spaces" not "Search spaces are sharp." The body states the claim; the title indexes it.

### Body

Terse. Two sentences is ideal, five is the upper bound. The note should be self-contained: a reader seeing it without context should grasp the core claim and why it matters. Write in the vault owner's voice, first person.

Don't summarise sources -- that's what `refs/` BONSAI sections are for. A zk entry takes a position. "I think X because Y" or "X implies Z, which nobody seems to have noticed."

### Links

Use Obsidian-style wikilinks: `[[target|display text]]`.

Aim for 1-3 genuine links, but don't force a quota. Links can point to:
- Other zk entries: `[[a1b2c3d4|short description]]`
- Refs: `[[refs/SomeRef|description]]`
- Maps: `[[maps/SomeTopic|description]]`
- People: `[[people/SomePerson|description]]`

Prefer linking to other zk entries -- that's how the graph grows. Link to refs when a card is grounded in a specific source. Use `python -m bonsai zk related "query"` or `python -m bonsai zk related path/to/note.md` to find candidate links via the existing vault search, filtered to zk notes. Don't force links; a genuine connection is worth more than a full quota.

### Tags

Agent-managed, lowercase, no fixed vocabulary. Use whatever aids retrieval. the vault owner doesn't maintain these.

## Browsing the zk

Use zk-specific commands before falling back to raw shell exploration:

```bash
python -m bonsai zk related "topic"              # existing search, filtered to zk notes
python -m bonsai zk related path/to/note.md       # derive query from a note, then search
python -m bonsai zk related --scope maps "topic"  # include maps as well as zk
python -m bonsai zk outline bfbdd5b3 --depth 2    # traverse outgoing links
python -m bonsai zk outline bfbdd5b3 --include-refs
python -m bonsai zk lint                         # loose graph hygiene warnings
```

`zk related` deliberately reuses the normal bonsai search implementation and filters afterward. If you need the whole vault, use `python -m bonsai search "topic"`.

## Meta-files

Two special file types support the zk. These are not atomic notes -- they're working documents.

### threads/

A directory of thread files (`threads/<name>.md`), one per thread. A staging area for ideas that aren't yet crystallised into atomic cards. Each file contains open questions, speculative connections, and references. Threads can span the whole vault -- research directions, vault infrastructure, tooling decisions. Promote a thread to a card when it firms up into a positive claim. Delete the thread file when it's been fully absorbed into cards or abandoned.

### OUTLINE files

When the vault owner wants to build a narrative from cards (for a talk, a post, a conversation), create `zk/OUTLINE-<name>.md`. An outline weaves card references into a structured argument. It's how the zk gets *used* -- the payoff of having atomic, linked notes.

## Workflow

1. **Dialogue first.** When the vault owner says "let's brainstorm" or "I'm thinking about X," that means conversation -- not immediate card creation. Engage with the idea. Push back. Ask questions. Only crystallise when something concrete emerges.

2. **Check before creating.** Before making a new entry, search existing entries with `python -m bonsai zk related "idea phrase"`. The idea might already exist, or it might be a refinement of something that does. If it refines an existing card, edit in place.

3. **Create.** Use `python -m bonsai zk new "Card title" --link target --tag tag` when starting a new card, then edit the generated file in place. Read back the title and links for confirmation.

4. **Thread speculative ideas.** If an idea is interesting but not yet a claim, add it to `threads/` instead of forcing a card.

5. **Refine over time.** Cards aren't permanent. Split cards that have grown too complex. Merge cards that turned out to be the same idea. Update claims when thinking evolves.

## Voice

Write in the vault owner's first person. Don't editorialize, pad, or hedge. Terse is right. "I think X because Y" is better than "It could be argued that X, given that Y, though further investigation is needed."

Don't create entries proactively. Only create when the vault owner expresses something worth capturing.

## Mailbox

If you create or substantially revise zk entries during a session, leave the vault owner a note summarising what changed:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Created zk entry <id>: <title>. Linked to <targets>." --context "zk/<id>.md"
```

If brainstorming surfaces a thread that needs more work later, leave yourself a reminder:

```bash
python -m bonsai mailbox send --from bonsai --to bonsai "Thread '<topic>' needs crystallising into a card." --context "threads/<topic>.md"
```
