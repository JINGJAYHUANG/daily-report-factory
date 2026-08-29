from __future__ import annotations

from pathlib import Path

from .util import read_json, require_relative_path, sha256_file


def check_prompt_manifest(root: str | Path, manifest_path: str | Path) -> list[str]:
    root_path = Path(root).resolve()
    manifest = read_json(manifest_path)
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "1.0":
        return ["prompt manifest schema_version must be '1.0'"]
    entries = manifest.get("prompts")
    if not isinstance(entries, list) or not entries:
        return ["prompt manifest prompts must be a non-empty array"]
    seen_publications: set[str] = set()
    seen_paths: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"prompts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        publication_id = entry.get("publication_id")
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(publication_id, str) or not publication_id:
            errors.append(f"{prefix}.publication_id must be non-empty")
        elif publication_id in seen_publications:
            errors.append(f"duplicate prompt publication_id: {publication_id}")
        seen_publications.add(str(publication_id))
        if not require_relative_path(relative) or not str(relative).startswith("prompts/"):
            errors.append(f"{prefix}.path must be a relative path under prompts/")
            continue
        if relative in seen_paths:
            errors.append(f"duplicate prompt path: {relative}")
        seen_paths.add(str(relative))
        path = (root_path / relative).resolve()
        try:
            path.relative_to(root_path)
        except ValueError:
            errors.append(f"{prefix}.path escapes repository root")
            continue
        if not path.is_file():
            errors.append(f"missing prompt file: {relative}")
            continue
        actual = sha256_file(path)
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"{prefix}.sha256 must be a 64-character digest")
        elif actual != expected:
            errors.append(f"prompt digest mismatch for {relative}: expected {expected}, got {actual}")
    return errors
