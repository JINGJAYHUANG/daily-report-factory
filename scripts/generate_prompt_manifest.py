#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build_manifest(root: Path) -> dict:
    catalog = json.loads((root / "config/publications.json").read_text(encoding="utf-8"))
    prompts = []
    for spec in sorted(catalog["publications"], key=lambda item: item["publication_id"]):
        relative = spec["prompt_path"]
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        prompts.append({
            "publication_id": spec["publication_id"],
            "path": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "contract_version": spec["contract_version"],
        })
    return {
        "schema_version": "1.0",
        "manifest_version": catalog["catalog_version"],
        "algorithm": "sha256",
        "prompts": prompts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    target = root / "config/prompt-manifest.json"
    expected = json.dumps(build_manifest(root), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            print("prompt manifest is missing or stale")
            return 1
        print("prompt manifest is current")
        return 0
    target.write_text(expected, encoding="utf-8", newline="\n")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
