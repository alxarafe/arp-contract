"""Semantic guardrails on candidate service behavior; no native runtime claims."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_services_draft as c


class ServicesDraftChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {x["id"]: x for x in c.load()["cases"]}

    def test_all_cases(self):
        self.assertGreaterEqual(c.check(), 15)

    def test_different_field_concurrent_updates_do_not_overwrite(self):
        result = c.outcome(self.cases["different-field-no-conflict"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["persisted"]["price"], "55")
        self.assertEqual(result["writtenFields"], ["code"])

    def test_same_field_requires_confirmation(self):
        result = c.outcome(self.cases["same-field-conflict"])
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["writtenFields"], [])

    def test_confirmation_must_be_current_again(self):
        result = c.outcome(self.cases["stale-confirmation-new-conflict"])
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["persisted"]["price"], "56")

    def test_atomicity_across_all_fields(self):
        result = c.outcome(self.cases["mixed-conflict-is-atomic"])
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["persisted"]["code"], "A")

    def test_historical_invalid_untouched(self):
        result = c.outcome(self.cases["historical-rating-intact"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["persisted"]["rating"], "11")

    def test_historical_invalid_included_rejected(self):
        result = c.outcome(self.cases["historical-rating-resubmitted"])
        self.assertEqual(result["status"], "invalid-data")

    def test_hidden_current_value_not_disclosed(self):
        result = c.outcome(self.cases["conflict-current-not-readable"])
        self.assertEqual(result["status"], "operation-not-allowed")
        self.assertNotIn("conflicts", result)

    def test_request_unchanged(self):
        source = copy.deepcopy(self.cases["confirmed-overwrite"])
        c.outcome(source)
        self.assertEqual(source, self.cases["confirmed-overwrite"])

    def test_equal_numeric_values_do_not_force_write(self):
        result = c.outcome(self.cases["numeric-equality-no-write"])
        self.assertEqual(result["writtenFields"], [])


if __name__ == "__main__":
    unittest.main()
