from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from typing import Iterable

from .catalog import PublicationSpec
from .contracts import IssueDocument, validate_issue


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    code: str
    message: str


class _AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.page_count = 0
        self.section_count = 0
        self.forbidden_tags: list[str] = []
        self.event_attributes: list[str] = []
        self.external_assets: list[str] = []
        self.bad_blank_links: list[str] = []
        self.meta_viewport = False
        self.html_lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "iframe", "object", "embed", "form"}:
            self.forbidden_tags.append(tag)
        for name, value in attrs:
            if name.lower().startswith("on"):
                self.event_attributes.append(name)
            if name in {"src", "href"} and value and tag in {"img", "script", "link", "iframe", "object", "embed"} and value.startswith(("http://", "https://", "//")):
                self.external_assets.append(value)
        if tag == "a" and attributes.get("target") == "_blank":
            rel = set((attributes.get("rel") or "").split())
            if not {"noopener", "noreferrer"}.issubset(rel):
                self.bad_blank_links.append(attributes.get("href") or "")
        if tag == "meta" and attributes.get("name") == "viewport":
            self.meta_viewport = "width=device-width" in (attributes.get("content") or "")
        if tag == "html":
            self.html_lang = attributes.get("lang") or ""
        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)
        classes = set((attributes.get("class") or "").split())
        if "report-page" in classes:
            self.page_count += 1
        if "report-section" in classes:
            self.section_count += 1


def validate_rendered_html(html: str, issue: IssueDocument, spec: PublicationSpec) -> list[Finding]:
    findings: list[Finding] = []
    if not html.lstrip().lower().startswith("<!doctype html>"):
        findings.append(Finding("error", "HTML_DOCTYPE", "HTML must start with an HTML5 doctype"))
    parser = _AuditParser()
    try:
        parser.feed(html)
    except Exception as exc:
        return [Finding("error", "HTML_PARSE", f"HTML parser failed: {exc}")]
    if not parser.meta_viewport:
        findings.append(Finding("error", "HTML_VIEWPORT", "responsive viewport metadata is missing"))
    if not parser.html_lang:
        findings.append(Finding("error", "HTML_LANG", "html lang attribute is missing"))
    for tag in parser.forbidden_tags:
        findings.append(Finding("error", "HTML_ACTIVE_CONTENT", f"forbidden active-content tag: {tag}"))
    for name in parser.event_attributes:
        findings.append(Finding("error", "HTML_EVENT_HANDLER", f"inline event handler is forbidden: {name}"))
    for url in parser.external_assets:
        findings.append(Finding("error", "HTML_EXTERNAL_ASSET", f"external runtime asset is forbidden: {url}"))
    for url in parser.bad_blank_links:
        findings.append(Finding("error", "HTML_LINK_REL", f"target=_blank link lacks noopener+noreferrer: {url}"))
    duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicate_ids:
        findings.append(Finding("error", "HTML_DUPLICATE_ID", f"duplicate element ids: {', '.join(duplicate_ids)}"))
    if spec.mode == "paged":
        if parser.page_count != spec.page_count:
            findings.append(Finding("error", "HTML_PAGE_COUNT", f"expected {spec.page_count} report pages, found {parser.page_count}"))
        if parser.section_count:
            findings.append(Finding("error", "HTML_MODE", "paged output must not include report-section containers"))
    else:
        if parser.section_count != len(issue.sections):
            findings.append(Finding("error", "HTML_SECTION_COUNT", f"expected {len(issue.sections)} report sections, found {parser.section_count}"))
        if parser.page_count:
            findings.append(Finding("error", "HTML_MODE", "long-scroll output must not include report-page containers"))
    required_layout_guards = ("max-width:100%", "overflow-x:hidden", "overflow-wrap:anywhere", ".table-wrap{max-width:100%;overflow-x:auto", "@media(max-width:720px)", "@media print")
    for guard in required_layout_guards:
        if guard not in html:
            findings.append(Finding("error", "HTML_LAYOUT_GUARD", f"missing static layout guard: {guard}"))
    if "<script" in html.lower():
        findings.append(Finding("error", "HTML_SCRIPT", "rendered reports must be JavaScript-free"))
    if escape(issue.data["title"]) not in html:
        findings.append(Finding("error", "HTML_TITLE", "issue title is missing from rendered HTML"))
    if "Disclosures and limits" not in html or "Source register" not in html:
        findings.append(Finding("error", "HTML_EVIDENCE_SECTIONS", "source register or disclosures section is missing"))
    return findings


def validate_bundle(issue: IssueDocument, spec: PublicationSpec, html: str | None = None) -> list[Finding]:
    findings = [Finding("error", "ISSUE_CONTRACT", error) for error in validate_issue(issue, spec)]
    if not findings and html is not None:
        findings.extend(validate_rendered_html(html, issue, spec))
    return findings


def errors_only(findings: Iterable[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity == "error"]
