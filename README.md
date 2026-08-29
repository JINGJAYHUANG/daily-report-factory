# Daily Report Factory

[![CI](https://github.com/JINGJAYHUANG/daily-report-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/JINGJAYHUANG/daily-report-factory/actions/workflows/ci.yml)

Daily Report Factory is an **API-agnostic, evidence-aware publication pipeline** for validating structured issue data, rendering deterministic standalone HTML, and archiving accepted outputs with integrity manifests.

It does **not** browse the web, call an LLM, certify factual accuracy, or claim that an earlier private prototype passed production acceptance. Version `0.1.0` is a clean public reconstruction focused on reproducibility and truthful boundaries.

## What it provides

- Nine versioned publication contracts.
- SHA-256-pinned public prompt contracts.
- Structured issue JSON with claim-to-source links.
- Deterministic, JavaScript-free, self-contained HTML rendering.
- Paged and long-scroll layouts.
- Static responsive-layout guards and print rules.
- Source freshness, date and reference validation.
- Atomic, lock-protected archival bundles with file hashes.
- Safe tar extraction that rejects traversal, links and oversized archives.
- Public-tree scans for common secrets, personal paths, phone numbers and personal email addresses.
- Two synthetic end-to-end fixtures and a zero-network CI path.

## Publication catalog

| Publication | Mode | Contract |
|---|---|---:|
| AI Alpha Daily | Long-scroll | 4–12 sections |
| EQIQ Micro Research Daily | Paged | 8 pages |
| Non-Economic Global Intelligence | Paged | 8 pages |
| Global Business Opportunity Daily | Paged | 10 pages |
| Global Economic Daily | Paged | 8 pages |
| History & Insights Daily | Paged | 8 pages |
| Daily Capability | Paged | 8 pages |
| Learning from History | Paged | 8 pages |
| Policy Intelligence Daily | Paged | 7 pages |

The public prompt files are compact editorial contracts written for this repository. They are not presented as verbatim copies of any private prompt archive.

## Quick start

Requires Python 3.11 or newer. The core has no runtime dependencies outside the standard library.

```bash
python scripts/reportctl.py catalog-check
python scripts/reportctl.py prompt-check
python scripts/reportctl.py self-test
```

Render and validate an issue:

```bash
python scripts/reportctl.py render \
  --issue examples/policy-intelligence-daily/issue.json \
  --output build/policy-fixture.html

python scripts/reportctl.py validate \
  --issue examples/policy-intelligence-daily/issue.json \
  --html build/policy-fixture.html
```

Archive an accepted issue:

```bash
python scripts/reportctl.py archive \
  --issue examples/policy-intelligence-daily/issue.json \
  --html build/policy-fixture.html \
  --root archive
```

## Architecture

```text
publication catalog + prompt manifest
                 │
                 ▼
        structured issue JSON
                 │
        contract/source checks
                 │
                 ▼
       deterministic HTML render
                 │
        static acceptance audit
                 │
                 ▼
      atomic archive + SHA-256 manifest
```

## Acceptance model

A green CI run means:

1. Python compiles on the supported versions.
2. Unit and integration tests pass.
3. All nine publication contracts and prompt hashes are internally consistent.
4. The two synthetic fixtures render, validate and archive without network access.
5. Static HTML checks find no scripts, external runtime assets, duplicate IDs, missing viewport metadata or contract page-count errors.
6. The repository safety scan finds no configured secret or PII patterns.

It does **not** mean that a real issue is factually correct, unbiased, complete, legally cleared, visually perfect in every browser, or safe to publish without human editorial review.

## Repository map

```text
config/       publication catalog and prompt digest manifest
prompts/      public-safe editorial contracts
schemas/      interoperable JSON Schema documents
src/          validation, rendering, safety and archive library
scripts/      reportctl command wrapper
examples/     synthetic long-scroll and paged fixtures
tests/        unit and end-to-end acceptance tests
docs/         architecture, contracts, security and status
```

## Public-safety boundary

Do not commit private prompts, correspondence, credentials, licensed articles, unlicensed images, customer information or proprietary research data. Real production inputs should live outside the repository and pass a separate rights and privacy review.

See [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md) and [`docs/STATUS.md`](docs/STATUS.md).

## AI-use disclosure

AI coding tools assisted requirements decomposition, implementation review and documentation. Repository scope, public/private boundaries, test criteria and release acceptance remain accountable human decisions.

## License

MIT. The license covers repository code and original documentation only; it does not grant rights to third-party material supplied by users.
