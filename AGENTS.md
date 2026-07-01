This repository contains Bonsai, reusable AI-agent infrastructure for Obsidian-style markdown knowledge bases.

## Repository conventions

- Source code lives in `bonsai/` and exposes both `python -m bonsai` and the `bonsai` console script.
- Bonsai commands operate on a vault root. By default this is the current working directory; set `BONSAI_VAULT_ROOT=/path/to/vault` to target another vault.
- Agent skills live in `.agents/skills/` for this repository and are mirrored under `templates/.agents/skills/` for copying into a vault.
- `templates/AGENTS.md`, `templates/.gitignore`, and `templates/ontology.md` are copyable starter files for vaults.
- `MANIFEST.in` keeps skills, scripts, and templates in source distributions even though they are not Python packages.
- Avoid adding personal vault content, journal entries, private refs, or generated runtime files (`.pagerank.json`, `.mailbox.jsonl`).

## Development commands

```bash
python -m pip install -e .
python -m bonsai --help
python -m bonsai search --help
```

For smoke tests against a temporary vault, run commands from that vault root or set `BONSAI_VAULT_ROOT`.
