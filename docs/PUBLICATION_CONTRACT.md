# Publication contract

Each issue JSON must identify a publication in `config/publications.json` and satisfy both the generic issue contract and publication-specific section rules.

## Required evidence structure

Every evidence item contains a claim and one or more `source_ids`. Each ID must resolve to a source record carrying:

- title and publisher;
- absolute publication date;
- absolute checked date;
- HTTP(S) locator;
- rights note;
- synthetic/non-synthetic flag.

The system checks referential integrity and freshness. It does not decide whether a cited source actually proves a claim; that remains an editorial responsibility.

## Paged versus long-scroll

Paged publications require an exact section count equal to the catalog page count. Long-scroll publications enforce minimum and maximum section counts. The renderer emits different semantic containers for the two modes, and the HTML validator rejects mixed-mode output.

## Cross-issue state

No deduplication, trend continuity or persistent memory is inferred from previous outputs. A future state adapter must supply explicit, auditable state before such claims are allowed.
