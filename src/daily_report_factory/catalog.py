from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import CatalogError
from .util import is_semver, is_slug, read_json, require_relative_path

_ALLOWED_MODES = {"paged", "long-scroll"}
_ALLOWED_STATUS = {"public-beta", "stable", "deprecated"}


@dataclass(frozen=True, slots=True)
class PublicationSpec:
    publication_id: str
    title: str
    title_zh: str
    mode: str
    page_count: int | None
    min_sections: int
    max_sections: int
    max_source_age_days: int
    prompt_path: str
    contract_version: str
    status: str
    description: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublicationSpec":
        return cls(
            publication_id=data["publication_id"], title=data["title"], title_zh=data["title_zh"],
            mode=data["mode"], page_count=data.get("page_count"), min_sections=data["min_sections"],
            max_sections=data["max_sections"], max_source_age_days=data["max_source_age_days"],
            prompt_path=data["prompt_path"], contract_version=data["contract_version"],
            status=data["status"], description=data["description"],
        )


def _validate_publication(raw: object, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"publications[{index}]"
    if not isinstance(raw, dict):
        return [f"{prefix} must be an object"]
    required = {"publication_id", "title", "title_zh", "mode", "min_sections", "max_sections",
                "max_source_age_days", "prompt_path", "contract_version", "status", "description"}
    missing = sorted(required - raw.keys())
    if missing:
        return [f"{prefix} missing fields: {', '.join(missing)}"]
    if not is_slug(raw["publication_id"]):
        errors.append(f"{prefix}.publication_id must be a lowercase kebab-case slug")
    for field in ("title", "title_zh", "description"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")
    if raw["mode"] not in _ALLOWED_MODES:
        errors.append(f"{prefix}.mode must be one of {sorted(_ALLOWED_MODES)}")
    if raw["status"] not in _ALLOWED_STATUS:
        errors.append(f"{prefix}.status must be one of {sorted(_ALLOWED_STATUS)}")
    if not is_semver(raw["contract_version"]):
        errors.append(f"{prefix}.contract_version must be semantic version text")
    if not require_relative_path(raw["prompt_path"]) or not str(raw["prompt_path"]).startswith("prompts/"):
        errors.append(f"{prefix}.prompt_path must be a relative path under prompts/")
    for field in ("min_sections", "max_sections", "max_source_age_days"):
        if not isinstance(raw[field], int) or isinstance(raw[field], bool) or raw[field] < 1:
            errors.append(f"{prefix}.{field} must be a positive integer")
    if isinstance(raw.get("min_sections"), int) and isinstance(raw.get("max_sections"), int) and raw["min_sections"] > raw["max_sections"]:
        errors.append(f"{prefix}.min_sections cannot exceed max_sections")
    page_count = raw.get("page_count")
    if raw["mode"] == "paged":
        if not isinstance(page_count, int) or isinstance(page_count, bool) or not 2 <= page_count <= 20:
            errors.append(f"{prefix}.page_count must be an integer from 2 to 20 for paged publications")
        elif raw.get("min_sections") != page_count or raw.get("max_sections") != page_count:
            errors.append(f"{prefix} paged publications must set min_sections=max_sections=page_count")
    elif page_count is not None:
        errors.append(f"{prefix}.page_count must be null for long-scroll publications")
    return errors


def load_catalog(path: str | Path) -> dict[str, PublicationSpec]:
    raw = read_json(path)
    errors: list[str] = []
    if not isinstance(raw, dict):
        raise CatalogError("catalog root must be an object")
    if raw.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not is_semver(raw.get("catalog_version")):
        errors.append("catalog_version must be semantic version text")
    publications = raw.get("publications")
    if not isinstance(publications, list) or not publications:
        errors.append("publications must be a non-empty array")
        publications = []
    for index, publication in enumerate(publications):
        errors.extend(_validate_publication(publication, index))
    ids = [p.get("publication_id") for p in publications if isinstance(p, dict)]
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    if duplicate_ids:
        errors.append(f"duplicate publication_id values: {', '.join(duplicate_ids)}")
    prompt_paths = [p.get("prompt_path") for p in publications if isinstance(p, dict)]
    duplicate_prompts = sorted({item for item in prompt_paths if prompt_paths.count(item) > 1})
    if duplicate_prompts:
        errors.append(f"duplicate prompt_path values: {', '.join(duplicate_prompts)}")
    if errors:
        raise CatalogError("\n".join(errors))
    return {p["publication_id"]: PublicationSpec.from_dict(p) for p in publications}
