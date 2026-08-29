import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from daily_report_factory.prompts import check_prompt_manifest
from daily_report_factory.safety import scan_public_tree

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


class PromptSafetyCLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/reportctl.py"), *args], cwd=ROOT, env=ENV, text=True, capture_output=True, check=False)

    def test_manifest_matches_all_nine_prompts(self):
        self.assertEqual(check_prompt_manifest(ROOT, ROOT / "config/prompt-manifest.json"), [])
        manifest = json.loads((ROOT / "config/prompt-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["prompts"]), 9)

    def test_repository_tree_is_public_safe(self):
        self.assertEqual(scan_public_tree(ROOT), [])

    def test_scanner_detects_constructed_markers(self):
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        personal_path = "/" + "Users" + "/example/private.txt"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.txt"
            path.write_text(marker + "\n" + personal_path, encoding="utf-8")
            rules = {finding.rule for finding in scan_public_tree(temporary)}
            self.assertEqual(rules, {"private-key", "personal-macos-path"})

    def test_end_to_end_cli_render_validate_archive(self):
        self.assertEqual(self.run_cli("catalog-check").returncode, 0)
        with tempfile.TemporaryDirectory() as temporary:
            html = Path(temporary) / "issue.html"
            issue = "examples/policy-intelligence-daily/issue.json"
            rendered = self.run_cli("render", "--issue", issue, "--output", str(html))
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            validated = self.run_cli("validate", "--issue", issue, "--html", str(html))
            self.assertEqual(validated.returncode, 0, validated.stderr)
            archived = self.run_cli("archive", "--issue", issue, "--html", str(html), "--root", str(Path(temporary) / "archive"))
            self.assertEqual(archived.returncode, 0, archived.stderr)


if __name__ == "__main__":
    unittest.main()
