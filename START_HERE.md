# Turn organized research into a shareable report
## 把整理好的研究内容，变成可交付的 HTML 报告

[Full documentation](README.md) · [Public tool collection](https://github.com/JINGJAYHUANG/JINGJAYHUANG)

**For:** researchers, analysts, students and newsletter builders who already have structured material.  
**Input:** issue JSON matching a publication contract.  
**Output:** a standalone HTML report and, optionally, an archive with integrity metadata.

## Try a bundled example

Requires Python 3.11 or newer. The core uses the Python standard library; this example does not require an AI API key.

```bash
git clone https://github.com/JINGJAYHUANG/daily-report-factory.git
cd daily-report-factory
python scripts/reportctl.py catalog-check
python scripts/reportctl.py prompt-check
python scripts/reportctl.py self-test
```

Render and validate a synthetic issue:

```bash
python scripts/reportctl.py render --issue examples/policy-intelligence-daily/issue.json --output build/policy-fixture.html
python scripts/reportctl.py validate --issue examples/policy-intelligence-daily/issue.json --html build/policy-fixture.html
```

Open `build/policy-fixture.html` in a browser. The file is the result to inspect; a GitHub link to HTML source is not a hosted demonstration.

## What to look for

Check the section structure, claim-to-source references and presentation of the supplied material. Then inspect the issue JSON beside the output: this makes the input-to-report relationship visible.

先用仓库内的虚构示例，确认格式和输出符合需要，再换自己的内容。它适合处理“已经整理好的资料”，不会替你搜新闻、核实事实或自动写出可靠结论。

## Optional: archive the accepted result

```bash
python scripts/reportctl.py archive --issue examples/policy-intelligence-daily/issue.json --html build/policy-fixture.html --root archive
```

The archive records file integrity. A matching hash proves neither factual accuracy nor publication rights.

## Example adaptations

A team update, research digest or class reading brief can follow the same pattern: select a supported contract, map the input fields, render, inspect, and archive only after acceptance. A new publication shape requires its own contract rather than assuming arbitrary JSON will work.

## Boundaries

The project does not browse the web, call an LLM or certify factual accuracy. Keep private prompts, confidential documents and unlicensed articles or images out of public examples. Static validation is not a substitute for visual review, source checking or editorial judgment.

See the [README](README.md) for the nine publication contracts and full verification scope. This walkthrough follows default-branch documentation reviewed on 2026-09-05; it is not a claim that all tests were freshly executed during this documentation change.
