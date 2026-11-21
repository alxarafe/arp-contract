"""Shared contract draft vectors only; no native runtime conformance claim."""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_cds_compatibility_draft as c


class CdsCompatibilityDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compatibility = c.load(ROOT/'fixtures/cds/v1/compatibility.json')
        cls.history = c.load(ROOT/'fixtures/cds/v1/historical-updates.json')

    def by_id(self, bucket, identity):
        return next(x for x in bucket if x['id'] == identity)

    def test_shared_fixture_integrity(self):
        self.assertEqual(c.check(ROOT), {'structural':21,'server':10,'client':7,'createClient':3,'audit':4})

    def test_logical_type_can_differ_from_physical_type(self):
        case=self.by_id(self.compatibility['assertions'],'int16-narrowed-fits-mariadb')
        self.assertEqual(case['dictionaryType'],'INTEGER')
        self.assertEqual(case['physical']['scalarType'],'INTEGER')
        self.assertEqual(case['dictionaryConstraints']['bits'],16)
        self.assertEqual(case['physical']['integerRange'],{'minimum':'-128','maximum':'127'})
        self.assertEqual(c.structural_status(case),'compatible')

    def test_unconstrained_logical_int16_not_storable_in_int8(self):
        case=self.by_id(self.compatibility['assertions'],'int16-unrestricted-exceeds-mariadb')
        self.assertEqual(c.structural_status(case),'incompatible')

    def test_opaque_physical_capability_cannot_be_assumed(self):
        case=self.by_id(self.compatibility['assertions'],'int16-opaque-physical')
        self.assertEqual(c.structural_status(case),'not-verified')

    def test_context_cannot_expand_intrinsic_type(self):
        case=self.by_id(self.compatibility['assertions'],'int8-context-expands-intrinsic')
        self.assertEqual(c.structural_status(case),'definition-invalid')

    def test_existing_invalid_rating_does_not_block_other_field(self):
        case=self.by_id(self.history['serverCases'],'historic-patch-other-field')
        self.assertEqual(c.server_outcome(case),case['expected'])
        self.assertEqual(case['expected']['persisted']['rating'],'11')

    def test_explicit_original_invalid_value_is_rejected_even_if_unchanged(self):
        case=self.by_id(self.history['serverCases'],'historic-submit-original-invalid')
        self.assertEqual(c.server_outcome(case)['status'],'invalid-data')

    def test_new_invalid_value_is_rejected(self):
        case=self.by_id(self.history['serverCases'],'new-invalid')
        self.assertEqual(c.server_outcome(case)['status'],'invalid-data')

    def test_client_cannot_reselect_historical_value_after_editing(self):
        case=self.by_id(self.history['clientCases'],'historic-correct-then-forbidden-return')
        result=c.client_outcome(case)
        self.assertEqual(result['acceptedAttempts'],[True,False])
        self.assertEqual(result['patch'],{'rating':'8'})
        self.assertEqual(result['finalForm']['rating'],'8')

    def test_client_can_preserve_legacy_value_while_changing_code(self):
        case=self.by_id(self.history['clientCases'],'historic-display-and-edit-other-field')
        result=c.client_outcome(case)
        self.assertTrue(result['originalWarning'])
        self.assertEqual(result['patch'],{'code':'B'})

    def test_create_ui_cannot_select_eleven(self):
        case=self.by_id(self.history['createClientCases'],'create-ui-forbids-eleven')
        result=c.create_client_outcome(case)
        self.assertEqual(result['acceptedAttempts'],[False])
        self.assertFalse(result['canSubmit'])

    def test_create_ui_accepts_eight(self):
        case=self.by_id(self.history['createClientCases'],'create-ui-selects-eight')
        result=c.create_client_outcome(case)
        self.assertEqual(result['acceptedAttempts'],[True])
        self.assertTrue(result['canSubmit'])

    def test_audit_requires_complete_evidence_for_conformant(self):
        rows=[{'rating':'8'}]
        self.assertEqual(c.audit(rows, False)['status'],'not-verified')
        self.assertEqual(c.audit(rows, True)['status'],'conformant')
        self.assertEqual(c.audit([{'rating':'11'}],False)['status'],'nonconforming')


if __name__=='__main__':
    unittest.main()