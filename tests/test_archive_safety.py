import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from daily_report_factory.archive import archive_issue, safe_extract_tar
from daily_report_factory.catalog import load_catalog
from daily_report_factory.contracts import load_issue
from daily_report_factory.errors import ArchiveSafetyError
from daily_report_factory.renderer import render_issue

ROOT = Path(__file__).resolve().parents[1]


class ArchiveSafetyTests(unittest.TestCase):
    def test_atomic_archive_contains_manifest_and_is_idempotent(self):
        issue_path = ROOT / "examples/ai-alpha-daily/issue.json"
        issue = load_issue(issue_path)
        spec = load_catalog(ROOT / "config/publications.json")[issue.publication_id]
        with tempfile.TemporaryDirectory() as temporary:
            html_path = Path(temporary) / "issue.html"
            html_path.write_text(render_issue(issue, spec), encoding="utf-8")
            first = archive_issue(issue_path, html_path, Path(temporary) / "archive")
            second = archive_issue(issue_path, html_path, Path(temporary) / "archive")
            self.assertEqual(first, second)
            manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["files"]), {"issue.json", "index.html"})

    def test_safe_extract_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "bad.tar"
            with tarfile.open(archive_path, "w") as archive:
                payload = b"bad"
                info = tarfile.TarInfo("../escape.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with self.assertRaises(ArchiveSafetyError):
                safe_extract_tar(archive_path, Path(temporary) / "out")

    def test_safe_extract_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "bad-link.tar"
            with tarfile.open(archive_path, "w") as archive:
                info = tarfile.TarInfo("link")
                info.type = tarfile.SYMTYPE
                info.linkname = "target"
                archive.addfile(info)
            with self.assertRaises(ArchiveSafetyError):
                safe_extract_tar(archive_path, Path(temporary) / "out")


if __name__ == "__main__":
    unittest.main()
