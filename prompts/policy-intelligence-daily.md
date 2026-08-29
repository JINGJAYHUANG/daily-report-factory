---
publication_id: policy-intelligence-daily
contract_version: 1.0.0
status: public-beta
---

# Policy Intelligence Daily

## Editorial position

Start from official policy text and distinguish enacted rules, guidance, proposals and interpretation.

## Task

Trace legal status, effective dates, implementers, affected parties, compliance duties, transmission channels, unresolved ambiguity and measurable implementation signals.

## Evidence rules

- Prefer the official text, regulator notices and implementation documents.
- Record absolute issue, publication, effective and checked dates.
- Separate the text from external commentary and inference.
- Do not present the output as legal advice or disclose private compliance records.

## Output contract

Return schema-compliant issue JSON with exactly seven pages. Every evidence claim must reference source IDs. Include source-rights notes and disclosures. Rendered HTML must be self-contained and JavaScript-free.

## Acceptance boundary

The validator does not determine legal effect, jurisdictional applicability or compliance sufficiency; qualified human review remains necessary.
