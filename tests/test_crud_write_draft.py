"""Semantic regressions for the write profile. These tests do not connect to a database."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_crud_write_draft as crud


class CrudWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = crud.load(crud.FOLDER / 'cases.json')
        cls.defaults = fixture['defaults']
        cls.cases = {case['id']: case for case in fixture['cases']}

    def run_case(self, identity):
        return crud.invoke(self.cases[identity], self.defaults)

    def test_all_expected_outcomes_and_reused_vectors(self):
        self.assertEqual(crud.check(), len(self.cases))

    def test_shared_update_contract_is_referenced_intact(self):
        manifest = crud.load(crud.FOLDER / 'manifest.json')
        self.assertEqual([(item['feature'], len(item['cases'])) for item in manifest['reuse']],
                         [('ARP-SERVICES-001', 25), ('ARP-SERVICES-002', 51)])
        for item in manifest['reuse']:
            source = crud.load(ROOT / item['path'])
            self.assertEqual(set(item['cases']), {case['id'] for case in source['cases']})

    def test_no_input_or_host_mutation(self):
        before = deepcopy((self.defaults, self.cases))
        for case in self.cases.values():
            crud.invoke(case, self.defaults)
        self.assertEqual((self.defaults, self.cases), before)

    def test_create_presence_null_and_defaults_are_distinct(self):
        for name in ('create-required-rating', 'create-null-does-not-use-default', 'create-unverified-default'):
            self.assertEqual(self.run_case(name)['response']['status'], 'rejected')
        result = self.run_case('create-verified-default')
        self.assertEqual(result['observed']['persisted'][-1]['rating'], '3')
        for name in ('create-nullable-explicit', 'create-nullable-absent'):
            self.assertIsNone(self.run_case(name)['observed']['persisted'][-1]['code'])

    def test_delete_requires_read_evidence_and_exact_purpose(self):
        for name in ('delete-no-precondition', 'delete-blind-baseline', 'delete-get-purpose-not-delete',
                     'delete-get-key-not-reusable', 'delete-wrong-context-binding'):
            result = self.run_case(name)
            self.assertEqual(result['response']['status'], 'rejected')
            self.assertEqual(result['observed']['writes'], 0)

    def test_every_relevant_state_change_prevents_deletion(self):
        original = self.cases['delete-valid']
        for change in ({'code': 'B'}, {'rating': '6'}, {'code': 'B', 'rating': '6'}):
            case = deepcopy(original)
            row = self.defaults['rows'][0] | change
            case['host']['rowsAtBoundary'] = [row]
            result = crud.invoke(case, self.defaults)
            self.assertEqual(result['response']['status'], 'conflict')
            self.assertEqual(result['observed']['persisted'], [row])
            self.assertEqual(result['observed']['effects'], 0)

    def test_absent_and_inaccessible_delete_are_publicly_indistinguishable(self):
        self.assertEqual(self.run_case('delete-absent')['response'],
                         self.run_case('delete-inaccessible')['response'])

    def test_hidden_values_never_appear_in_conflict_output(self):
        result = self.run_case('delete-hidden-concurrent-change')
        self.assertEqual(result['response']['status'], 'conflict')
        public = json.dumps(result['response'])
        for private in ('private-old', 'private-new', 'internal_note', 'rowsAtBoundary', 'context'):
            self.assertNotIn(private, public)

    def test_new_columns_require_complete_preconditions_without_expanding_projection(self):
        result = self.run_case('delete-uncovered-new-column')
        self.assertEqual(result['response']['status'], 'rejected')
        result = self.run_case('create-new-hidden-column-not-published')
        self.assertNotIn('internal_note', json.dumps(result['response']))
        self.assertIn('internal_note', result['observed']['persisted'][-1])

    def test_explicit_delegation_does_not_borrow_managed_guarantees(self):
        self.assertEqual(self.run_case('delete-uncharacterized-effects')['observed']['dispatches'], 0)
        delegated = self.run_case('delegated-specialized-delete')
        self.assertEqual(delegated['observed']['dispatches'], 1)
        self.assertEqual(delegated['observed']['certainty'], 'unknown')
        for operation in ('create', 'delete', 'update'):
            self.assertEqual(self.run_case(operation + '-uncertain-0')['response'],
                             self.run_case(operation + '-uncertain-1')['response'])
        self.assertEqual(self.run_case('delegated-failure-effects-0')['response'],
                         self.run_case('delegated-failure-effects-1')['response'])

    def test_known_rollback_and_uncertainty_do_not_share_diagnostics(self):
        rolled_back = self.run_case('delete-commit-rollback')
        uncertain = self.run_case('delete-uncertain-1')
        self.assertNotEqual(rolled_back['response'], uncertain['response'])
        self.assertEqual(rolled_back['observed']['certainty'], 'rolled-back')
        self.assertEqual(uncertain['observed']['certainty'], 'unknown')
        self.assertEqual(uncertain['observed']['writes'], 1)

    def test_noop_still_checks_revoked_permission(self):
        self.assertEqual(self.run_case('update-demo-noop')['response']['status'], 'success')
        self.assertEqual(self.run_case('update-revoked-field-before-noop')['response']['status'], 'rejected')
        self.assertEqual(self.run_case('update-demo-noop')['observed']['writes'], 0)

    def test_update_preserves_independent_and_historical_values(self):
        row = self.run_case('update-demo-independent-change')['observed']['persisted'][0]
        self.assertEqual((row['code'], row['rating']), ('B', '6'))
        row = self.run_case('update-demo-historical-omitted')['observed']['persisted'][0]
        self.assertEqual(row['rating'], '11')
        self.assertEqual(self.run_case('update-demo-historical-resent')['response']['status'], 'rejected')
        self.assertEqual(self.run_case('update-conflict-after-interleave')['response']['status'], 'conflict')

    def test_confirmation_binding_survives_identity_adaptation(self):
        self.assertEqual(self.run_case('update-confirmation-valid')['response']['status'], 'success')
        self.assertEqual(self.run_case('update-confirmation-obsolete')['response']['status'], 'conflict')
        self.assertEqual(self.run_case('update-confirmation-wrong-key-binding')['response']['status'], 'rejected')

    def test_member_order_cannot_change_outcomes(self):
        for identity in ('create-valid', 'delete-valid', 'update-demo-partial'):
            case = deepcopy(self.cases[identity])
            case['request'] = dict(reversed(list(case['request'].items())))
            case['request']['inputs'] = dict(reversed(list(case['request']['inputs'].items())))
            self.assertEqual(crud.invoke(case, self.defaults), self.run_case(identity))

    def test_codec_preserves_exactness_and_rejects_ambiguous_sources(self):
        for case in crud.load(crud.FOLDER / 'codec-cases.json'):
            with self.subTest(case=case['id']):
                self.assertEqual(crud.codec(case), case['expected'])
        with self.assertRaises(ValueError):
            crud.decode('{"target":"demo.items","target":"other"}')

    def test_conflicts_recheck_field_read_permission(self):
        for phase in ('AtBoundary', 'AtPublish'):
            case = deepcopy(self.cases['update-conflict-after-interleave'])
            case['host']['readableFields' + phase] = ['id', 'code']
            result = crud.invoke(case, self.defaults)
            self.assertEqual(result['response']['status'], 'rejected')
            self.assertNotIn('conflicts', result['response'])

    def test_malformed_operation_is_a_safe_rejection(self):
        for operation in ([], {}, None, True, 7):
            case = deepcopy(self.cases['create-valid'])
            case['request']['operation'] = operation
            self.assertEqual(crud.invoke(case, self.defaults)['response']['status'], 'rejected')

    def test_postcommit_permission_loss_never_claims_no_effects(self):
        for name in ('create-postcommit-output-revoked', 'delete-postcommit-output-revoked'):
            result = self.run_case(name)
            self.assertEqual(result['response']['status'], 'failed')
            self.assertNotIn('output', result['response'])
            self.assertEqual(result['observed']['certainty'], 'committed')
            self.assertEqual(result['observed']['effects'], 1)


if __name__ == '__main__':
    unittest.main()