from __future__ import annotations

import json
import lzma
import os
import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from .errors import ArchiveSafetyError
from .util import sha256_file, write_json_atomic

_MAX_MEMBERS = 2_000
_MAX_UNPACKED_BYTES = 128 * 1024 * 1024


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def safe_extract_tar(archive_path: str | Path, destination: str | Path, *, max_members: int = _MAX_MEMBERS, max_unpacked_bytes: int = _MAX_UNPACKED_BYTES) -> list[Path]:
    destination_path = Path(destination).resolve()
    destination_path.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    try:
        archive = tarfile.open(archive_path, mode="r:*")
    except (tarfile.TarError, OSError, EOFError, lzma.LZMAError) as exc:
        raise ArchiveSafetyError(f"cannot open archive: {exc}") from exc
    with archive:
        members = archive.getmembers()
        if len(members) > max_members:
            raise ArchiveSafetyError(f"archive contains {len(members)} members; limit is {max_members}")
        total = 0
        for member in members:
            if not _safe_member_name(member.name):
                raise ArchiveSafetyError(f"unsafe archive path: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise ArchiveSafetyError(f"links and device members are forbidden: {member.name}")
            if not (member.isdir() or member.isfile()):
                raise ArchiveSafetyError(f"unsupported archive member type: {member.name}")
            total += max(member.size, 0)
            if total > max_unpacked_bytes:
                raise ArchiveSafetyError(f"archive exceeds unpacked byte limit {max_unpacked_bytes}")
            target = (destination_path / member.name).resolve()
            try:
                target.relative_to(destination_path)
            except ValueError as exc:
                raise ArchiveSafetyError(f"archive member escapes destination: {member.name}") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ArchiveSafetyError(f"cannot read archive member: {member.name}")
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                os.chmod(target, 0o644)
            extracted.append(target)
    return extracted


@contextmanager
def _exclusive_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ArchiveSafetyError(f"archive lock already exists: {lock_path}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def archive_issue(issue_path: str | Path, html_path: str | Path, archive_root: str | Path) -> Path:
    issue_source = Path(issue_path).resolve()
    html_source = Path(html_path).resolve()
    if not issue_source.is_file() or not html_source.is_file():
        raise ArchiveSafetyError("issue JSON and rendered HTML must both exist")
    try:
        issue = json.loads(issue_source.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ArchiveSafetyError(f"cannot read issue JSON: {exc}") from exc
    publication_id, issue_id, issue_date = issue.get("publication_id"), issue.get("issue_id"), issue.get("issue_date")
    if not all(isinstance(value, str) and value for value in (publication_id, issue_id, issue_date)):
        raise ArchiveSafetyError("issue JSON lacks publication_id, issue_id or issue_date")
    if any("/" in value or "\\" in value or value in {".", ".."} for value in (publication_id, issue_id)):
        raise ArchiveSafetyError("publication_id and issue_id must be safe path components")
    try:
        year, month, _ = issue_date.split("-")
    except ValueError as exc:
        raise ArchiveSafetyError("issue_date must use YYYY-MM-DD") from exc
    root = Path(archive_root).resolve()
    target = root / publication_id / year / month / issue_id
    lock = root / ".locks" / f"{issue_id}.lock"
    with _exclusive_lock(lock):
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{issue_id}.", dir=target.parent))
        try:
            issue_target, html_target = staging / "issue.json", staging / "index.html"
            shutil.copy2(issue_source, issue_target)
            shutil.copy2(html_source, html_target)
            manifest = {"schema_version": "1.0", "publication_id": publication_id, "issue_id": issue_id, "issue_date": issue_date,
                        "files": {"issue.json": sha256_file(issue_target), "index.html": sha256_file(html_target)}}
            write_json_atomic(staging / "manifest.json", manifest)
            if target.exists():
                current = target / "manifest.json"
                if current.is_file() and json.loads(current.read_text(encoding="utf-8")) == manifest:
                    shutil.rmtree(staging)
                    return target
                raise ArchiveSafetyError(f"archive target already exists with different content: {target}")
            os.replace(staging, target)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise
    return target
