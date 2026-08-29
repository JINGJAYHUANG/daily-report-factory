import unittest
from pathlib import Path

from daily_report_factory.catalog import load_catalog
from daily_report_factory.contracts import load_issue
from daily_report_factory.renderer import render_issue
from daily_report_factory.validator import errors_only, validate_rendered_html

ROOT = Path(__file__).resolve().parents[1]


class RendererValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / "config/publications.json")

    def test_long_scroll_is_deterministic_and_valid(self):
        issue = load_issue(ROOT / "examples/ai-alpha-daily/issue.json")
        spec = self.catalog[issue.publication_id]
        first = render_issue(issue, spec)
        second = render_issue(issue, spec)
        self.assertEqual(first, second)
        self.assertEqual(errors_only(validate_rendered_html(first, issue, spec)), [])
        self.assertEqual(first.count('class="report-section"'), 4)

    def test_paged_fixture_has_exact_page_count(self):
        issue = load_issue(ROOT / "examples/policy-intelligence-daily/issue.json")
        spec = self.catalog[issue.publication_id]
        html = render_issue(issue, spec)
        self.assertEqual(html.count('class="report-page"'), 7)
        self.assertEqual(errors_only(validate_rendered_html(html, issue, spec)), [])

    def test_renderer_escapes_text(self):
        issue = load_issue(ROOT / "examples/ai-alpha-daily/issue.json")
        issue.data["title"] = "A & B < C"
        html = render_issue(issue, self.catalog[issue.publication_id])
        self.assertIn("A &amp; B &lt; C", html)
        self.assertNotIn("A & B < C", html)

    def test_validator_rejects_script_external_asset_and_duplicate_id(self):
        issue = load_issue(ROOT / "examples/ai-alpha-daily/issue.json")
        spec = self.catalog[issue.publication_id]
        html = render_issue(issue, spec)
        scripted = html.replace("</body>", "<scr" + "ipt>alert(1)</scr" + "ipt></body>")
        self.assertIn("HTML_ACTIVE_CONTENT", {f.code for f in errors_only(validate_rendered_html(scripted, issue, spec))})
        external = html.replace("</head>", '<link rel="stylesheet" href="https://example.com/x.css"></head>')
        self.assertIn("HTML_EXTERNAL_ASSET", {f.code for f in errors_only(validate_rendered_html(external, issue, spec))})
        duplicate = html.replace('id="signal-map"', 'id="mechanism"', 1)
        self.assertIn("HTML_DUPLICATE_ID", {f.code for f in errors_only(validate_rendered_html(duplicate, issue, spec))})


if __name__ == "__main__":
    unittest.main()
