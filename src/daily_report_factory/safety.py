from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".html", ".css", ".csv"}
_EXCLUDED_PARTS = {".git", ".venv", "venv", "build", "dist", "archive", "__pycache__", ".pytest_cache"}
_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "feishu-webhook": re.compile(r"https://open\.feishu\.cn/open-apis/bot/v2/hook/[A-Za-z0-9_-]{8,}"),
    "personal-windows-path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    "personal-macos-path": re.compile(r"/Users/[^/\s]+/"),
    "mainland-phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "personal-email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?:gmail\.com|163\.com|qq\.com|outlook\.com)\b", re.IGNORECASE),
    "secret-assignment": re.compile(r"(?:TOKEN|SECRET|PASSWORD|WEBHOOK_URL)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", re.IGNORECASE),
}


@dataclass(frozen=True, slots=True)
class SafetyFinding:
    path: str
    line: int
    rule: str


def scan_public_tree(root: str | Path) -> list[SafetyFinding]:
    root_path = Path(root).resolve()
    findings: list[SafetyFinding] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        if any(part in _EXCLUDED_PARTS for part in path.relative_to(root_path).parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, 1):
            for rule, pattern in _PATTERNS.items():
                if pattern.search(line):
                    findings.append(SafetyFinding(str(path.relative_to(root_path)), line_number, rule))
    return findings
