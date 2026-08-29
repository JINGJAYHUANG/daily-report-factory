from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from .archive import archive_issue
from .catalog import load_catalog
from .contracts import load_issue
from .errors import DailyReportFactoryError
from .prompts import check_prompt_manifest
from .renderer import render_issue
from .safety import scan_public_tree
from .validator import errors_only, validate_bundle, validate_rendered_html


def _catalog(args: argparse.Namespace) -> int:
    specs = load_catalog(args.catalog)
    print(json.dumps({"ok": True, "publication_count": len(specs), "publications": sorted(specs)}, indent=2))
    return 0


def _prompts(args: argparse.Namespace) -> int:
    errors = check_prompt_manifest(args.root, args.manifest)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def _render(args: argparse.Namespace) -> int:
    specs = load_catalog(args.catalog)
    issue = load_issue(args.issue)
    spec = specs.get(issue.publication_id)
    if spec is None:
        raise DailyReportFactoryError(f"unknown publication_id: {issue.publication_id}")
    html = render_issue(issue, spec)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    findings = validate_rendered_html(html, issue, spec)
    errors = errors_only(findings)
    print(json.dumps({"ok": not errors, "output": str(output), "findings": [asdict(f) for f in findings]}, indent=2))
    return 1 if errors else 0


def _validate(args: argparse.Namespace) -> int:
    specs = load_catalog(args.catalog)
    issue = load_issue(args.issue)
    spec = specs.get(issue.publication_id)
    if spec is None:
        raise DailyReportFactoryError(f"unknown publication_id: {issue.publication_id}")
    html = Path(args.html).read_text(encoding="utf-8") if args.html else None
    findings = validate_bundle(issue, spec, html)
    errors = errors_only(findings)
    print(json.dumps({"ok": not errors, "findings": [asdict(f) for f in findings]}, indent=2))
    return 1 if errors else 0


def _archive(args: argparse.Namespace) -> int:
    target = archive_issue(args.issue, args.html, args.root)
    print(json.dumps({"ok": True, "archive_path": str(target)}, indent=2))
    return 0


def _safety(args: argparse.Namespace) -> int:
    findings = scan_public_tree(args.root)
    print(json.dumps({"ok": not findings, "findings": [asdict(f) for f in findings]}, indent=2))
    return 1 if findings else 0


def _fixture(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    output = Path(args.output_dir).resolve()
    specs = load_catalog(root / "config/publications.json")
    fixtures = [root / "examples/ai-alpha-daily/issue.json", root / "examples/policy-intelligence-daily/issue.json"]
    results: list[dict[str, object]] = []
    output.mkdir(parents=True, exist_ok=True)
    for fixture in fixtures:
        issue = load_issue(fixture)
        spec = specs[issue.publication_id]
        html = render_issue(issue, spec)
        destination = output / f"{issue.issue_id}.html"
        destination.write_text(html, encoding="utf-8", newline="\n")
        findings = validate_bundle(issue, spec, html)
        results.append({"issue_id": issue.issue_id, "output": str(destination), "errors": [asdict(f) for f in errors_only(findings)]})
    ok = all(not result["errors"] for result in results)
    print(json.dumps({"ok": ok, "fixtures": results}, indent=2))
    return 0 if ok else 1


def _self_test(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    specs = load_catalog(root / "config/publications.json")
    prompt_errors = check_prompt_manifest(root, root / "config/prompt-manifest.json")
    safety_findings = scan_public_tree(root)
    fixture_results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="drf-self-test-") as temporary:
        temp = Path(temporary)
        for relative in (Path("examples/ai-alpha-daily/issue.json"), Path("examples/policy-intelligence-daily/issue.json")):
            issue_path = root / relative
            issue = load_issue(issue_path)
            spec = specs[issue.publication_id]
            html = render_issue(issue, spec)
            html_path = temp / f"{issue.issue_id}.html"
            html_path.write_text(html, encoding="utf-8", newline="\n")
            findings = validate_bundle(issue, spec, html)
            archived = archive_issue(issue_path, html_path, temp / "archive")
            fixture_results.append({"issue_id": issue.issue_id, "error_count": len(errors_only(findings)), "archive_manifest": (archived / "manifest.json").is_file()})
    ok = len(specs) == 9 and not prompt_errors and not safety_findings and all(item["error_count"] == 0 and item["archive_manifest"] for item in fixture_results)
    report = {"ok": ok, "publication_count": len(specs), "prompt_errors": prompt_errors, "safety_findings": [asdict(f) for f in safety_findings], "fixtures": fixture_results}
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reportctl", description="Validate, render and archive evidence-aware daily reports")
    subparsers = parser.add_subparsers(dest="command", required=True)
    catalog = subparsers.add_parser("catalog-check", help="validate the publication catalog")
    catalog.add_argument("--catalog", default="config/publications.json")
    catalog.set_defaults(func=_catalog)
    prompts = subparsers.add_parser("prompt-check", help="verify prompt manifest SHA-256 digests")
    prompts.add_argument("--root", default=".")
    prompts.add_argument("--manifest", default="config/prompt-manifest.json")
    prompts.set_defaults(func=_prompts)
    render = subparsers.add_parser("render", help="render one issue JSON file to deterministic HTML")
    render.add_argument("--catalog", default="config/publications.json")
    render.add_argument("--issue", required=True)
    render.add_argument("--output", required=True)
    render.set_defaults(func=_render)
    validate = subparsers.add_parser("validate", help="validate an issue contract and optional rendered HTML")
    validate.add_argument("--catalog", default="config/publications.json")
    validate.add_argument("--issue", required=True)
    validate.add_argument("--html")
    validate.set_defaults(func=_validate)
    archive = subparsers.add_parser("archive", help="archive an issue and rendered HTML atomically")
    archive.add_argument("--issue", required=True)
    archive.add_argument("--html", required=True)
    archive.add_argument("--root", default="archive")
    archive.set_defaults(func=_archive)
    safety = subparsers.add_parser("safety-scan", help="scan the public source tree for common secrets and PII")
    safety.add_argument("--root", default=".")
    safety.set_defaults(func=_safety)
    fixture = subparsers.add_parser("fixture", help="render and validate the two bundled synthetic fixtures")
    fixture.add_argument("--root", default=".")
    fixture.add_argument("--output-dir", default="build/fixtures")
    fixture.set_defaults(func=_fixture)
    self_test = subparsers.add_parser("self-test", help="run the full zero-network acceptance path")
    self_test.add_argument("--root", default=".")
    self_test.set_defaults(func=_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (DailyReportFactoryError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
