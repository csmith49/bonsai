---
name: assist
description: Build a daily report surfacing research trends, ongoing projects, pending tasks, and suggested reading.
---

You are producing a daily report from recent vault activity.

## Gathering data

Start by checking the mailbox for any unread messages -- both for you and for the vault owner:

```bash
python -m bonsai mailbox unread
python -m bonsai mailbox unread --for owner
```

Then run the digest command to get structured activity data:

```bash
python -m bonsai digest -d 14
```

Use the 14-day window by default. If the vault owner asks for a different period, adjust with `-d`.

## Reading the journals

Read each journal file listed in the digest output. Journals are organised into blocks separated by `---`. Pay attention to:

* **Projects and experiments** -- recurring topics across multiple entries (e.g. a named SDK, a dataset build, a proof attempt). Track what the vault owner said he was doing and what status he left it in.
* **Action items** -- anything phrased as "need to", "should", "todo", "next step", or similar. Note whether a later entry resolves it.
* **Questions and ideas** -- things the vault owner is wondering about or considering. These are research leads.

## Building the report

Produce a report with these sections. Be direct -- bullet points, not prose.

### Active threads

List ongoing projects or investigations that appear in multiple recent entries. For each, give:
* What it is (one line)
* Current status based on the most recent mention
* Open questions or blockers, if any

### Pending tasks

List action items from the journals that don't appear to be resolved by a later entry. Include the date they were mentioned. Drop anything that was clearly completed.

### Research leads

Topics, questions, or ideas the vault owner mentioned but hasn't acted on yet. Include the date and a brief quote or paraphrase.

### Suggested reading

Pull from the digest's "Unread refs" list -- refs linked from recent journals that lack a `## BONSAI` section. Also check the wikilink frequency list: high-frequency links to refs without BONSAI sections are strong candidates.

For each suggestion, explain in one line why it's relevant to current activity (connect it to an active thread or research lead).

### Mailbox

Include a section summarising any unread messages. Group by recipient:
* Messages for the vault owner that he hasn't read yet (task completions, alerts from BONSAI).
* Messages for BONSAI that haven't been acted on (tasks from the vault owner, self-reminders).

If the mailbox is empty, omit this section.

### Quiet threads

Topics that were active earlier in the window but have gone silent. These are reminders, not judgments. Only include if they were clearly active (appeared in 2+ entries) and then dropped off.

## Tone

Write like a briefing. No filler, no encouragement, no editorialising. the vault owner knows what he's working on -- this report catches what might have slipped through the cracks.
