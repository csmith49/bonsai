---
name: mailbox
description: Read unread mailbox messages and act on them. Use at the start of any session, or when asked to check messages.
---

You are checking the async mailbox and acting on messages.

The mailbox is a JSONL file (`.mailbox.jsonl`) at the vault root. It holds messages between the vault owner and BONSAI, and notes BONSAI leaves for itself. Think of it as a shared task queue and notification channel.

## Step 1: Check for unread messages

```bash
python -m bonsai mailbox unread
python -m bonsai mailbox unread --for owner
```

The first command shows messages addressed to you (bonsai). The second shows messages for the vault owner -- skim those too so you have context, but don't mark them read.

## Step 2: Triage

For each unread message addressed to you, decide what to do:

- **Task from the vault owner** -- something the vault owner wants done. Do it now if it's small, or acknowledge and plan if it's large.
- **Self-reminder** -- a note you left for yourself in a previous session. Pick it up or decide it's stale.
- **Status update** -- informational. Read and mark done.

## Step 3: Act

Work through the messages. For tasks, use the appropriate skill (research, trace, link, zk, etc.). When you finish a task that the vault owner asked for, send him a reply:

```bash
python -m bonsai mailbox send --from bonsai --to owner "Done: researched SkillWeaver, BONSAI section added." --context "refs/SkillWeaver"
```

## Step 4: Mark read

After acting on a message, mark it read by ID prefix:

```bash
python -m bonsai mailbox read <id-prefix>
```

You can pass multiple prefixes: `python -m bonsai mailbox read abc123 def456`.

## When to send messages

Leave messages proactively in these situations:

- **Task completed** -- tell the vault owner what you did and where to find the result.
- **Something needs attention** -- a broken link, a ref that couldn't be fetched, a contradiction you spotted. Send to the vault owner.
- **Self-reminder** -- something you want to pick up in a future session. Send to yourself. Use `--context` to reference the relevant file or ref.
- **Follow-up needed** -- you finished part of a task but there's more to do. Send to yourself with context.

Keep messages short. One thought per message. Use `--context` to point at the relevant file or ref.

## CLI reference

```bash
python -m bonsai mailbox send --from <who> --to <who> "body" [--context "ref"]
python -m bonsai mailbox unread [--for owner|bonsai]
python -m bonsai mailbox list [--from ...] [--to ...] [-n 20] [--short]
python -m bonsai mailbox read <id-prefix> [<id-prefix> ...]
python -m bonsai mailbox count [--for owner|bonsai]
```
