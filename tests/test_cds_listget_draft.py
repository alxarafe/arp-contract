"""LIST/GET contract properties; no SQL, live permissions or cryptographic token implementation."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_cds_listget_draft as c


class ListGetDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = c.load(c.FOLDER / 'products.json')
        cls.vectors = c.load(c.FOLDER / 'cases.json')
        cls.cases = {case['id']: case for case in cls.vectors['cases']}
        cls.schema = c.contract_validator(c.load(c.ROOT / 'schemas/cds/v1/listget-result.schema.json'))

    def run_case(self, identity, host=None, assets=None):
        case = deepcopy(self.cases[identity])
        if host:
            case.setdefault('host', {}).update(deepcopy(host))
        return c.invoke(case, self.assets if assets is None else assets, self.vectors['defaults'])

    def test_all_shared_expectations(self):
        self.assertEqual(c.check(), len(self.cases))

    def test_only_services_results_and_all_five_families(self):
        responses = [self.run_case(identity)['response'] for identity in self.cases]
        self.assertEqual({r['status'] for r in responses}, {'success', 'rejected', 'failed'})
        self.assertEqual({d['family'] for r in responses for d in r['diagnostics']}, c.FAMILIES)

    def test_every_case_is_read_only_and_errors_have_no_partial_output(self):
        for identity in self.cases:
            result = self.run_case(identity)
            with self.subTest(case=identity):
                self.assertEqual(result['observed']['writes'], 0)
                if result['response']['status'] != 'success':
                    self.assertNotIn('output', result['response'])
                    self.assertEqual(result['observed']['selectedRows'], [])

    def test_simple_and_composite_exact_identity(self):
        simple = self.run_case('get-simple-typed-key')['response']['output']['record']
        composite = self.run_case('get-composite-typed-key')['response']['output']['record']
        self.assertEqual(simple['key']['components'], [
            {'field': 'product_id', 'type': 'INTEGER', 'value': '9007199254740993'}])
        self.assertEqual([x['field'] for x in composite['key']['components']], ['tenant_id', 'product_id'])
        self.assertEqual([x['value'] for x in composite['key']['components']], ['7', '10'])

    def test_identity_integer_codec_does_not_coerce_round_or_wrap(self):
        self.assertEqual(c.integer('-0', {'bits': 64, 'signed': True}), 0)
        self.assertEqual(c.integer('9223372036854775807', {'bits': 64, 'signed': True}), 9223372036854775807)
        self.assertNotEqual(c.integer('9007199254740993', {'bits': 64, 'signed': True}),
                            c.integer('9007199254740994', {'bits': 64, 'signed': True}))
        for value in (True, 2, '02', '+2', '2.0', '2e0', ' 2', '9223372036854775808'):
            with self.subTest(value=value), self.assertRaises(c.InvalidKey):
                c.integer(value, {'bits': 64, 'signed': True})
        self.assertEqual(c.integer('-0', {'bits': 32, 'signed': False}), 0)
        with self.assertRaises(c.InvalidKey):
            c.integer('-1', {'bits': 32, 'signed': False})

    def test_hidden_key_is_not_a_public_field_or_partial_key(self):
        result = self.run_case('get-authorized-hidden-key')['response']['output']['record']
        self.assertEqual(set(result['key']), {'reference'})
        self.assertTrue({'tenant_id', 'product_id', 'cost', 'internal_note'}.isdisjoint(result['values']))
        self.assertEqual(self.run_case('get-raw-hidden-key-rejected')['observed']['reads'], 0)

    def test_missing_and_inaccessible_have_the_same_response(self):
        absent = self.run_case('get-unknown-reference')['response']
        denied = self.run_case('get-existing-but-row-denied')['response']
        self.assertEqual(absent, denied)
        self.assertEqual(absent['output'], {'found': False})

    def test_reference_and_cursor_bindings_are_not_permissions(self):
        for identity in ('get-scope-binding-denied', 'get-principal-binding-denied',
                         'get-policy-binding-denied', 'get-projection-binding-denied'):
            with self.subTest(case=identity):
                self.assertEqual(self.run_case(identity)['response']['output'], {'found': False})
        self.assertEqual(self.run_case('cursor-context-changed')['response']['status'], 'rejected')
        self.assertEqual(self.run_case('operation-not-authorized')['observed']['reads'], 0)

    def test_pages_cover_only_authorized_rows_once_in_numeric_pk_order(self):
        combined = []
        for identity in ('list-first-page', 'list-second-page', 'list-last-page'):
            result = self.run_case(identity)
            combined.extend(result['observed']['selectedRows'])
        self.assertEqual(combined, ['p1', 'p2', 'p3', 'p4', 'p5'])
        self.assertEqual(len(combined), len(set(combined)))
        self.assertFalse(self.run_case('list-last-page')['response']['output']['page']['hasMore'])
        self.assertIsNone(self.run_case('list-last-page')['response']['output']['page']['next'])

    def test_input_provider_order_and_json_member_order_do_not_change_pages(self):
        assets = deepcopy(self.assets)
        for layout in assets['layouts'].values():
            layout['rows'].reverse()
        for identity in ('list-first-page', 'list-second-page', 'list-last-page'):
            self.assertEqual(self.run_case(identity), self.run_case(identity, assets=assets))

        def reverse(value):
            if isinstance(value, dict):
                return {k: reverse(v) for k, v in reversed(list(value.items()))}
            if isinstance(value, list):
                return [reverse(v) for v in value]
            return value

        for case in self.cases.values():
            actual = c.invoke(reverse(case), reverse(self.assets), reverse(self.vectors['defaults']))
            self.assertEqual(c.cds.canonical(actual), c.cds.canonical(case['expected']), case['id'])

    def test_unreadable_rows_and_hidden_values_cannot_affect_public_page(self):
        assets = deepcopy(self.assets)
        for row in assets['layouts']['composite']['rows']:
            row['values']['cost'] = 'private-decoding-not-requested'
            row['values']['internal_note'] = 'private-secret'
            if row['id'] == 'other-scope':
                row['values']['product_id'] = 'not-an-integer'
                row['values']['name'] = 'private-secret'
        self.assertEqual(self.run_case('list-first-page'), self.run_case('list-first-page', assets=assets))

    def test_row_restriction_is_applied_before_limit_and_continuation(self):
        result = self.run_case('list-first-page', {'allowedRows': ['p1', 'p3', 'p4', 'p5']})
        self.assertEqual(result['observed']['selectedRows'], ['p1', 'p3'])
        self.assertTrue(result['response']['output']['page']['hasMore'])
        empty = self.run_case('list-empty-authorized-set')['response']['output']
        self.assertEqual(empty['records'], [])
        self.assertFalse(empty['page']['hasMore'])

    def test_limits_are_exact_and_server_bounded(self):
        output = self.run_case('list-server-clamps-limit')['response']['output']
        self.assertEqual(output['page']['limit'], 3)
        self.assertEqual(len(output['records']), 3)
        case = deepcopy(self.cases['list-first-page'])
        case['request']['inputs']['limit'] = Decimal('2.0')
        self.assertEqual(c.invoke(case, self.assets, self.vectors['defaults']), case['expected'])
        for value in (True, False, None, 0, -1, Decimal('1.5'), 101, '2'):
            case['request']['inputs']['limit'] = value
            self.assertEqual(c.invoke(case, self.assets, self.vectors['defaults'])['response']['status'], 'rejected')

    def test_no_query_or_context_injection(self):
        for key, value in [('filter', {'cost': 0}), ('sort', ['cost']), ('fields', ['internal_note']),
                           ('offset', 3), ('context', {'scope': 'other'})]:
            case = deepcopy(self.cases['list-first-page'])
            case['request']['inputs'][key] = value
            result = c.invoke(case, self.assets, self.vectors['defaults'])
            self.assertEqual(result['response']['status'], 'rejected')
            self.assertEqual(result['observed']['reads'], 0)

    def test_null_empty_unicode_and_exact_decimals_survive(self):
        self.assertIsNone(self.run_case('get-null-preserved')['response']['output']['record']['values']['description'])
        values = self.run_case('get-exact-decimal')['response']['output']['record']['values']
        self.assertEqual(values['price'], '999999999999999999999999.123456789')
        self.assertEqual(values['description'], '')
        values = self.run_case('get-unicode-and-empty-values')['response']['output']['record']['values']
        self.assertEqual(values['name'], 'Te\u0301 verde 🍵')
        self.assertIs(values['available'], True)

    def test_historical_value_is_not_clipped_or_revalidated_as_write(self):
        values = self.run_case('get-historical-rating')['response']['output']['record']['values']
        self.assertEqual(values['rating'], '11')
        constraints = self.assets['layouts']['composite']['definitions']['logical']['authored']['fields']['rating']
        self.assertEqual(constraints['constraints']['maximum'], '10')

    def test_unknown_fields_are_not_added_after_rebuild(self):
        row = self.run_case('new-column-not-published-after-rebuild')['response']['output']['record']
        self.assertNotIn('supplier_reference', row['values'])
        self.assertEqual(self.run_case('removed-published-column-rebuild-rejected')['observed']['reads'], 0)

    def test_generation_and_authorization_gate_also_apply_to_empty_results(self):
        for identity in ('stale-catalog-generation', 'stale-record-reference', 'stale-continuation',
                         'invalidation-during-read', 'authorization-lost-before-publication',
                         'empty-get-still-checks-publication-generation', 'context-changed-before-publication'):
            response = self.run_case(identity)['response']
            self.assertNotEqual(response['status'], 'success', identity)
            self.assertNotIn('output', response)

    def test_failing_last_row_never_returns_first_row(self):
        result = self.run_case('last-row-decode-failure-no-partial-page')
        self.assertEqual(result['response']['status'], 'failed')
        self.assertNotIn('output', result['response'])
        self.assertEqual(result['observed']['selectedRows'], [])

    def test_no_authentication_system_is_mandatory(self):
        response = self.run_case('public-application-without-principal')['response']
        self.assertEqual(response['status'], 'success')
        self.assertNotIn('principal', self.cases['public-application-without-principal']['host']['context'])

    def test_response_schema_rejects_new_status_partial_failure_and_bad_page(self):
        good = self.cases['list-first-page']['expected']['response']
        for mutate in ('status', 'page', 'failure', 'family'):
            invalid = deepcopy(good)
            if mutate == 'status':
                invalid['status'] = 'not-found'
            elif mutate == 'page':
                invalid['output']['page']['next'] = None
            elif mutate == 'failure':
                invalid['status'] = 'failed'
            else:
                invalid = deepcopy(self.cases['provider-failure']['expected']['response'])
                invalid['diagnostics'][0]['family'] = 'invalid-data'
            self.assertFalse(self.schema.is_valid(invalid), mutate)

    def test_modular_authorization_is_per_operation_and_server_authoritative(self):
        self.assertEqual(self.run_case('modules-catalog-list')['response']['status'], 'success')
        denied = self.run_case('modules-catalog-get-denied-independently')
        self.assertEqual(denied['response']['diagnostics'][0]['code'], 'CDS_LISTGET_UNAVAILABLE')
        self.assertEqual(denied['observed']['reads'], 0)
        self.assertEqual(self.run_case('modules-catalog-get-authorized')['response']['status'], 'success')

    def test_reports_reads_only_its_active_derived_projection(self):
        result = self.run_case('modules-reports-derived-list')
        self.assertEqual(set(result['response']['output']['records'][0]['values']), {'sku', 'name'})
        for identity in ('modules-reports-inactive', 'modules-all-inactive', 'modules-reports-get-unavailable'):
            with self.subTest(case=identity):
                self.assertEqual(self.run_case(identity)['observed']['reads'], 0)
                self.assertEqual(self.run_case(identity)['response']['status'], 'rejected')

    def test_modular_dependencies_reuse_existing_module_validation(self):
        for identity in ('modules-reports-without-catalog', 'modules-undeclared-projection-dependency'):
            with self.subTest(case=identity):
                result = self.run_case(identity)
                self.assertEqual(result['observed']['reads'], 0)
                self.assertEqual(result['response']['diagnostics'][0]['family'], 'definition-invalid')

    def test_module_membership_and_permissions_are_checked_before_publication(self):
        for identity in ('modules-deactivation-during-read', 'modules-permission-revoked-before-publication'):
            with self.subTest(case=identity):
                result = self.run_case(identity)
                self.assertNotEqual(result['response']['status'], 'success')
                self.assertNotIn('output', result['response'])
                self.assertEqual(result['observed']['selectedRows'], [])

    def test_module_activation_never_bypasses_field_and_row_restrictions(self):
        self.assertEqual(self.run_case('modules-row-restriction-still-authoritative')
                         ['response']['output']['records'], [])
        self.assertEqual(self.run_case('modules-field-access-still-authoritative')['observed']['reads'], 0)
        self.assertEqual(self.run_case('modules-client-cannot-activate')['observed']['reads'], 0)

    def test_one_application_cache_selectively_retires_query_metadata(self):
        layout = self.assets['layouts']['composite']
        before, _ = c.modular_catalog(self.assets, layout, {})
        after, _ = c.modular_catalog(self.assets, layout, {'active': ['catalog']})
        cache = {'applicationId': 'demo.shop', 'entries': [
            {'id': 'catalog-query', 'complete': True, 'dependsOn': [
                {'kind': 'selection', 'type': 'projection', 'id': 'products.catalog'}]},
            {'id': 'reports-query', 'complete': True, 'dependsOn': [
                {'kind': 'artifact', 'id': 'catalog-query'},
                {'kind': 'selection', 'type': 'projection', 'id': 'products.summary'}]},
            {'id': 'physical', 'complete': True, 'dependsOn': [
                {'kind': 'source', 'providerId': 'application', 'sourceId': 'physical'}]},
        ]}
        plan = c.modules.cache_plan(before, after, cache)
        self.assertTrue(plan['valid'])
        self.assertEqual(plan['invalidated'], ['reports-query'])
        self.assertEqual(plan['retained'], ['catalog-query', 'physical'])
        inactive, _ = c.modular_catalog(self.assets, layout, {'active': []})
        self.assertEqual(c.modules.cache_plan(before, inactive, cache)['invalidated'],
                         ['catalog-query', 'reports-query'])
        self.assertEqual(len(cache['entries']), 3)

    def test_module_catalog_preserves_definitions_rows_and_menu_authority(self):
        original = deepcopy(self.assets)
        snapshot, menus = c.modular_catalog(self.assets, self.assets['layouts']['composite'], {})
        self.assertTrue(snapshot['valid'])
        self.assertTrue(menus['valid'])
        self.assertEqual(snapshot['dependencies']['reports'], {'catalog'})
        self.assertEqual(snapshot['queryAccess']['products.catalog']['authorized'], ['LIST'])
        self.assertEqual(self.assets, original)

    def test_native_obligations_are_explicitly_not_executed(self):
        manifest = c.load(c.FOLDER / 'provider-obligations.json')
        self.assertIs(manifest['executed'], False)
        self.assertEqual(manifest['engines'], {'dotnet': 'postgresql', 'java': 'postgresql', 'php': 'mariadb'})
        self.assertTrue((c.FOLDER / manifest['data']).is_file())
        self.assertIn('hidden-key-reference-binding-and-unforgeability', manifest['requirements'])


if __name__ == '__main__':
    unittest.main()