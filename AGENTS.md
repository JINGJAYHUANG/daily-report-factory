# Agent contribution rules

- Treat `config/publications.json` and `schemas/` as public contracts.
- Do not add network calls, model calls, credentials or private editorial inputs to the trusted core without an explicit design change.
- Keep rendered HTML deterministic and JavaScript-free.
- Preserve the distinction between structural acceptance and factual/editorial acceptance.
- Run the full unit suite and `python scripts/reportctl.py self-test` before proposing completion.
- Never weaken safe archive extraction or public-tree scans merely to make a test pass.
