import copy
import json
import tempfile
import unittest
from pathlib import Path

from daily_report_factory.catalog import load_catalog
from daily_report_factory.contracts import IssueDocument, load_issue, validate_issue
from daily_report_factory.errors import CatalogError

ROOT = Path(__file__).resolve().parents[1]


class CatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / "config/publications.json")
        cls.policy = load_issue(ROOT / "examples/policy-intelligence-daily/issue.json")

    def test_public_catalog_has_nine_unique_specs(self):
        self.assertEqual(len(self.catalog), 9)
        self.assertEqual(self.catalog["policy-intelligence-daily"].page_count, 7)
        self.assertEqual(self.catalog["ai-alpha-daily"].mode, "long-scroll")

    def test_paged_contract_rejects_mismatched_section_count(self):
        raw = json.loads((ROOT / "config/publications.json").read_text(encoding="utf-8"))
        raw["publications"][1]["max_sections"] = 9
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_catalog(path)

    def test_policy_fixture_passes(self):
        self.assertEqual(validate_issue(self.policy, self.catalog[self.policy.publication_id]), [])

    def test_unknown_source_reference_fails(self):
        raw = copy.deepcopy(self.policy.data)
        raw["sections"][0]["evidence"][0]["source_ids"] = ["MISSING"]
        errors = validate_issue(IssueDocument(raw), self.catalog[self.policy.publication_id])
        self.assertTrue(any("unknown source" in error for error in errors))

    def test_stale_and_future_sources_fail(self):
        stale = copy.deepcopy(self.policy.data)
        stale["sources"][0]["checked_at"] = "2029-01-01"
        self.assertTrue(any("stale" in error for error in validate_issue(IssueDocument(stale), self.catalog[self.policy.publication_id])))
        future = copy.deepcopy(self.policy.data)
        future["sources"][0]["published_at"] = "2030-01-16"
        self.assertTrue(any("after issue_date" in error for error in validate_issue(IssueDocument(future), self.catalog[self.policy.publication_id])))

    def test_active_markup_fails(self):
        raw = copy.deepcopy(self.policy.data)
        raw["subtitle"] = "unsafe <scr" + "ipt>alert(1)</scr" + "ipt>"
        self.assertTrue(any("forbidden active HTML" in error for error in validate_issue(IssueDocument(raw), self.catalog[self.policy.publication_id])))


if __name__ == "__main__":
    unittest.main()
