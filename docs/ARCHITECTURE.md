# Architecture

## Design objective

Daily Report Factory turns editorial content already expressed as structured issue JSON into a reproducible publication artifact. Content collection and model inference are deliberately outside the trusted core.

## Trust boundaries

1. **Untrusted input** — issue JSON and source metadata.
2. **Contract layer** — validates dates, source references, section counts and active-markup exclusions.
3. **Renderer** — escapes user text and emits self-contained, JavaScript-free HTML.
4. **Acceptance layer** — parses output and verifies mode, page count, IDs, viewport, link security and static layout guards.
5. **Archive layer** — writes to staging, hashes files, acquires an exclusive lock and atomically publishes an immutable issue directory.

## Determinism

The renderer never reads the clock, network, environment variables or random state. The `generated_at` value comes from the issue document. Identical catalog and issue inputs therefore produce identical HTML bytes.

## Failure behavior

Validation errors produce a nonzero exit code and machine-readable JSON. Archive conflicts fail closed unless the existing manifest is equivalent. No failed issue is silently marked accepted.
