# Contributing

1. Open an issue describing the contract or failure mode before a broad change.
2. Keep the runtime standard-library-only unless a dependency has a documented security and maintenance justification.
3. Add or update tests for every behavior change.
4. Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/reportctl.py self-test
```

5. Never commit private prompts, personal paths, credentials, correspondence, proprietary data or third-party full text.
6. Update `CHANGELOG.md` when behavior or contracts change.
7. Do not describe static layout checks as browser-perfect visual testing.
