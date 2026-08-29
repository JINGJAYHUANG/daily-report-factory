from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .catalog import PublicationSpec
from .errors import ContractError
from .util import parse_iso_date, parse_iso_datetime, read_json

_ALLOWED_STATUS = {"draft", "reviewed", "published", "fixture"}
_ALLOWED_SECTION_KINDS = {"cover", "reading-map", "snapshot", "analysis", "comparison", "watchlist", "methodology", "conclusion", "sources"}
_FORBIDDEN_MARKUP = re.compile(r"<(?:script|iframe|object|embed|form)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class IssueDocument:
    data: dict[str, Any]

    @property
    def publication_id(self) -> str:
        return self.data["publication_id"]

    @property
    def issue_id(self) -> str:
        return self.data["issue_id"]

    @property
    def sections(self) -> list[dict[str, Any]]:
        return self.data["sections"]

    @property
    def sources(self) -> list[dict[str, Any]]:
        return self.data["sources"]


def load_issue(path: str | Path) -> IssueDocument:
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ContractError("issue root must be an object")
    return IssueDocument(raw)


def _valid_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _walk_strings(value: Any, path: str = "issue"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{path}[{index}]")


def validate_issue(issue: IssueDocument, spec: PublicationSpec) -> list[str]:
    data = issue.data
    errors: list[str] = []
    required = {"schema_version", "publication_id", "issue_id", "issue_date", "generated_at", "language", "timezone", "title", "subtitle", "status", "synthetic", "sections", "sources", "disclosures"}
    missing = sorted(required - data.keys())
    if missing:
        return [f"missing issue fields: {', '.join(missing)}"]
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if data.get("publication_id") != spec.publication_id:
        errors.append(f"publication_id {data.get('publication_id')!r} does not match catalog spec {spec.publication_id!r}")
    for field in ("issue_id", "language", "timezone", "title", "subtitle"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if data.get("status") not in _ALLOWED_STATUS:
        errors.append(f"status must be one of {sorted(_ALLOWED_STATUS)}")
    if not isinstance(data.get("synthetic"), bool):
        errors.append("synthetic must be a boolean")
    issue_date = parse_iso_date(data.get("issue_date"))
    if issue_date is None:
        errors.append("issue_date must be an ISO date (YYYY-MM-DD)")
    generated_at = parse_iso_datetime(data.get("generated_at"))
    if generated_at is None or generated_at.tzinfo is None:
        errors.append("generated_at must be an ISO datetime with timezone")

    sections = data.get("sections")
    if not isinstance(sections, list):
        errors.append("sections must be an array")
        sections = []
    if not spec.min_sections <= len(sections) <= spec.max_sections:
        errors.append(f"{spec.publication_id} requires exactly {spec.page_count} sections/pages" if spec.mode == "paged" else f"{spec.publication_id} requires between {spec.min_sections} and {spec.max_sections} sections")
    section_ids: list[str] = []
    referenced_sources: set[str] = set()
    for index, section in enumerate(sections):
        prefix = f"sections[{index}]"
        if not isinstance(section, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "kind", "heading", "summary"):
            if not isinstance(section.get(field), str) or not section[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if section.get("kind") not in _ALLOWED_SECTION_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(_ALLOWED_SECTION_KINDS)}")
        if isinstance(section.get("id"), str):
            section_ids.append(section["id"])
        for list_field in ("implications", "actions"):
            value = section.get(list_field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{prefix}.{list_field} must be an array of non-empty strings")
        evidence = section.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{prefix}.evidence must be an array")
            continue
        for evidence_index, item in enumerate(evidence):
            evidence_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(item, dict):
                errors.append(f"{evidence_prefix} must be an object")
                continue
            if not isinstance(item.get("claim"), str) or not item["claim"].strip():
                errors.append(f"{evidence_prefix}.claim must be a non-empty string")
            source_ids = item.get("source_ids")
            if not isinstance(source_ids, list) or not source_ids or any(not isinstance(x, str) for x in source_ids):
                errors.append(f"{evidence_prefix}.source_ids must be a non-empty string array")
            else:
                referenced_sources.update(source_ids)
    duplicates = sorted({item for item in section_ids if section_ids.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate section ids: {', '.join(duplicates)}")

    sources = data.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []
    source_ids: list[str] = []
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "title", "publisher", "url", "published_at", "checked_at", "rights"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if isinstance(source.get("id"), str):
            source_ids.append(source["id"])
        if not _valid_http_url(source.get("url")):
            errors.append(f"{prefix}.url must use http or https")
        published_at = parse_iso_date(source.get("published_at"))
        checked_at = parse_iso_date(source.get("checked_at"))
        if published_at is None:
            errors.append(f"{prefix}.published_at must be an ISO date")
        if checked_at is None:
            errors.append(f"{prefix}.checked_at must be an ISO date")
        if published_at and issue_date and published_at > issue_date:
            errors.append(f"{prefix}.published_at cannot be after issue_date")
        if checked_at and issue_date:
            if checked_at > issue_date:
                errors.append(f"{prefix}.checked_at cannot be after issue_date")
            elif (issue_date - checked_at).days > spec.max_source_age_days:
                errors.append(f"{prefix} is stale: checked {(issue_date - checked_at).days} days before issue; maximum is {spec.max_source_age_days}")
        if not isinstance(source.get("synthetic"), bool):
            errors.append(f"{prefix}.synthetic must be a boolean")
        if data.get("synthetic") is True and source.get("synthetic") is not True:
            errors.append(f"{prefix} must be synthetic when the issue is a synthetic fixture")
    duplicate_sources = sorted({item for item in source_ids if source_ids.count(item) > 1})
    if duplicate_sources:
        errors.append(f"duplicate source ids: {', '.join(duplicate_sources)}")
    unknown_sources = sorted(referenced_sources - set(source_ids))
    if unknown_sources:
        errors.append(f"evidence references unknown source ids: {', '.join(unknown_sources)}")

    disclosures = data.get("disclosures")
    if not isinstance(disclosures, list) or not disclosures or any(not isinstance(item, str) or not item.strip() for item in disclosures):
        errors.append("disclosures must be a non-empty array of strings")
    elif data.get("synthetic") is True and not any("synthetic" in item.lower() for item in disclosures):
        errors.append("synthetic fixtures must disclose that the content is synthetic")
    for location, value in _walk_strings(data):
        if _FORBIDDEN_MARKUP.search(value):
            errors.append(f"forbidden active HTML markup in {location}")
    return errors


def validate_issue_or_raise(issue: IssueDocument, spec: PublicationSpec) -> None:
    errors = validate_issue(issue, spec)
    if errors:
        raise ContractError("\n".join(errors))
