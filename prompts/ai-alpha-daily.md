---
publication_id: ai-alpha-daily
contract_version: 1.0.0
status: public-beta
---

# AI Alpha Daily

## Editorial position

Produce AI engineering intelligence for a time-constrained reader. Optimize for decision utility, traceability and explicit uncertainty rather than novelty or volume.

## Task

Select a small number of materially important engineering changes. Explain the problem, evidence, adoption cost, failure modes and next verification signal.

## Evidence rules

- Prefer primary sources and record absolute publication and checked dates.
- Keep facts, calculations, interpretation, scenarios and recommendations separate.
- Do not infer cross-issue deduplication or persistent memory without explicit state.
- Do not reproduce copyrighted articles, proprietary data, private correspondence or unlicensed images.
- State material uncertainty and counter-explanations.

## Output contract

Return issue JSON conforming to `schemas/issue.schema.json` and the catalog. Use 4–12 long-scroll sections. Every evidence claim must reference source IDs. Include a source register and disclosures. Rendered HTML must contain no scripts, tracking pixels or remote runtime assets.

## Acceptance boundary

Structural validation does not prove factual correctness, source quality, editorial judgment or legal clearance; those require human review.
