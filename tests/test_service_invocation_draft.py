"""Semantic properties of the invocation draft, independent of JSON shape checks."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_service_invocation_draft as c


class InvocationDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["id"]: case for case in c.updates.load(c.FILE)["cases"]}

    def result(self, identity):
        return c.invoke(copy.deepcopy(self.cases[identity]))

    def test_all_vectors(self):
        self.assertEqual(c.check(), len(self.cases))

    def test_all_result_kinds_and_five_families(self):
        results = [self.result(identity)["response"] for identity in self.cases]
        self.assertEqual({r["status"] for r in results}, {"success", "conflict", "rejected", "failed"})
        self.assertEqual({d["family"] for r in results for d in r["diagnostics"]}, c.FAMILIES)

    def test_rejections_conflicts_and_known_managed_rollback_do_not_write(self):
        for case in self.cases.values():
            result = c.invoke(case)
            status = result["response"]["status"]
            if (status in {"rejected", "conflict"}
                    or (status == "failed" and case["host"].get("commitFailure", False))):
                with self.subTest(case=case["id"]):
                    host = case["host"]
                    self.assertEqual(result["observed"]["persisted"],
                                     host.get("currentAtCommit", host["current"]))
                    self.assertEqual(result["observed"]["writtenFields"], [])
                    self.assertEqual(result["observed"]["effects"], 0)

    def test_hidden_conflict_has_no_public_observation(self):
        case = copy.deepcopy(self.cases["conflict-current-not-readable"])
        response = c.invoke(case)["response"]
        case["host"]["current"]["price"] = "999999"
        self.assertEqual(c.invoke(case)["response"], response)
        self.assertNotIn("conflicts", response)
        self.assertNotIn("persisted", response)
        self.assertNotIn("output", response)

    def test_client_authority_cannot_enable_dispatch(self):
        for field in ("context", "authorized", "identity", "scope"):
            case = copy.deepcopy(self.cases["operation-not-authorized"])
            case["request"][field] = True
            result = c.invoke(case)
            self.assertEqual(result["response"]["status"], "rejected")
            self.assertEqual(result["observed"]["dispatches"], 0)
            self.assertEqual(result["observed"]["effects"], 0)

    def test_absence_null_and_historical_validation(self):
        self.assertEqual(self.result("historical-rating-intact")["observed"]["persisted"]["rating"], "11")
        for identity in ("null-is-explicit-write", "historical-rating-resubmitted", "baseline-required"):
            self.assertEqual(self.result(identity)["response"]["status"], "rejected")
        case = copy.deepcopy(self.cases["single-field-update"])
        case["request"]["inputs"]["baseline"]["price"] = None
        self.assertEqual(c.invoke(case)["response"]["status"], "conflict")

    def test_noop_has_no_business_effect_but_still_authorizes(self):
        for identity in ("empty-update", "numeric-equality-no-write"):
            case = copy.deepcopy(self.cases[identity])
            self.assertEqual(c.invoke(case)["observed"]["effects"], 0)
            case["host"]["authorized"] = False
            self.assertEqual(c.invoke(case)["response"]["status"], "rejected")

    def test_atomic_boundary_sees_intervening_change(self):
        for identity in ("race-at-commit", "confirmation-race-at-commit", "mixed-conflict-is-atomic"):
            self.assertEqual(self.result(identity)["response"]["status"], "conflict")
        self.assertEqual(self.result("different-field-no-conflict")["observed"]["persisted"]["price"], "55")

    def test_confirmation_is_bound_and_reauthorized(self):
        self.assertEqual(self.result("confirmed-overwrite")["response"]["status"], "success")
        for identity in ("confirmation-changed-proposal", "confirmation-changed-context", "confirmation-expired",
                         "confirmation-lost-authorization", "confirmation-lost-read"):
            self.assertEqual(self.result(identity)["response"]["status"], "rejected")

    def test_value_comparison_does_not_claim_aba_detection(self):
        self.assertEqual(self.result("aba-not-detectable-by-value")["response"]["status"], "success")

    def test_failed_does_not_prove_absence_of_effects(self):
        without_effect = self.result("delegated-failure-unknown-effects-0")
        with_effect = self.result("delegated-failure-unknown-effects-1")
        self.assertEqual(without_effect["response"], with_effect["response"])
        self.assertEqual(with_effect["response"]["status"], "failed")
        self.assertEqual(without_effect["observed"]["effects"], 0)
        self.assertEqual(with_effect["observed"]["effects"], 1)
        self.assertNotIn("effects", with_effect["response"])
        rollback = self.result("commit-rollback")
        self.assertEqual(rollback["response"]["status"], "failed")
        self.assertEqual(rollback["observed"]["effects"], 0)

    def test_confirmation_is_not_required_by_every_service(self):
        case = copy.deepcopy(self.cases["local-delegated-success"])
        self.assertEqual(c.invoke(case)["response"]["status"], "success")
        case["request"]["inputs"]["confirmation"] = "arbitrary"
        self.assertEqual(c.invoke(case)["response"]["status"], "rejected")
        case["request"]["inputs"] = {}
        case["host"]["authorized"] = False
        result = c.invoke(case)
        self.assertEqual(result["response"]["status"], "rejected")
        self.assertEqual(result["observed"]["dispatches"], 0)

    def test_local_delegation_and_failure_sanitization(self):
        self.assertEqual(self.result("local-delegated-success")["observed"]["dispatches"], 1)
        response = self.result("handler-failure")["response"]
        self.assertEqual(response, {"status": "failed", "diagnostics": [
            {"family": "execution-failure", "code": "HANDLER_FAILED"}]})


if __name__ == "__main__":
    unittest.main()