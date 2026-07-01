---
name: qa
description: Verify a reference summary by cross-checking factual claims against the source.
---

You are verifying a BONSAI summary against its source.

The goal is to surface hallucinations -- facts the summary states that the source doesn't support. Every discrepancy is two problems: a summary to fix and a pattern to feed back into the research skill.

## Step 1: Extract questions from the summary

Read the `## BONSAI` section of the reference. Do NOT read the source yet.

Generate one question per distinct factual claim. Target the categories most prone to hallucination:

* **Attribution** -- who wrote it, who contributed
* **Affiliation** -- institutions, labs, companies
* **Quantities** -- percentages, counts, magnitudes, benchmarks
* **Methodology** -- what they actually did, pipeline stages, model names
* **Relationships** -- claimed connections to other work (same group, builds on, extends, replaces)
* **Temporal** -- dates, ordering of events, version history

Phrase each question so it has a short, concrete answer. Avoid vague questions like "what is the paper about?" -- prefer "what institution are the authors affiliated with?" or "what success rate improvement is reported on unseen websites?"

Aim for 8-15 questions depending on how claim-dense the summary is. Fewer for a light summary, more for one packed with specifics.

## Step 2: Answer from the summary

Answer every question using only the BONSAI section. Quote or paraphrase directly. If the summary doesn't address a question you generated, mark it **no answer (summary)**.

## Step 3: Answer from the source

Now fetch the source. References have URLs in their front-matter. For arxiv, use the HTML version.

Answer every question using only the source. If the source doesn't address a question, mark it **no answer (source)**.

## Step 4: Compare and classify

For each question, assign a verdict:

* **Match** -- summary and source agree
* **Mismatch** -- summary and source disagree (hallucination)
* **Unsupported** -- summary makes a claim the source never addresses (likely hallucination)
* **Unverifiable** -- source is ambiguous or the claim requires outside context to check

## Step 5: Report

Present results as a table:

| # | Question | Summary answer | Source answer | Verdict |
|---|----------|---------------|--------------|---------|

Below the table, for each **Mismatch** or **Unsupported** finding, write one line explaining what went wrong -- what the summary said, what the source actually says (or doesn't), and what category of error it is (wrong attribution, invented relationship, inflated number, etc.).

## Step 6: Fix the summary

If there are any Mismatch or Unsupported verdicts, edit the `## BONSAI` section to correct them. Keep the same tone and structure -- just fix the facts.

## Step 7: Flag the pattern

If corrections were needed, append a brief note to the end of this conversation describing the error pattern. This is raw material for tightening the research skill. Format:

```
Error pattern: <category>
Example: <what the summary said> vs <what the source says>
Possible cause: <why the research skill might have produced this>
```
