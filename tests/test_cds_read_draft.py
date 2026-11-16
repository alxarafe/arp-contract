"""Semantic checks of the read candidate; never database or native conformance."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_cds_read_draft as read
import check_cds_draft as previous


class CdsReadCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = json.loads((ROOT / 'fixtures/cds/read/v1/cases.json').read_text())
        cls.cases = {case['id']: case for case in cls.suite['cases']}
        cls.base = cls.cases['mariadb-independent-identities']['input']
        cls.dictionary = read.load_dictionary('fixtures/dictionary/v1/catalog.json')

    def test_all_exact_fixture_results_and_sources(self):
        self.assertEqual(read.check(), len(self.cases))

    def test_same_authoring_schemas_no_alternative_physical_or_entity_grammar(self):
        self.assertEqual(read.SCHEMAS['physical']['$id'],
                         'https://alxarafe.org/arp/drafts/cds/v1/physical.schema.json')
        self.assertEqual(read.SCHEMAS['logical']['properties']['apiVersion']['const'], 'arp.logical/v1')
        self.assertEqual(read.SCHEMAS['projections']['properties']['apiVersion']['const'], 'arp.projection/v1')

    def test_independent_ids_also_work_in_previous_fixture_oracle(self):
        bundle = deepcopy(self.base)
        dictionary = {'elements': list(self.dictionary.values())}
        previous.resolve(bundle['physical']['storage'], bundle['logical']['model'], dictionary,
                         bundle['projections']['public'], bundle['projections']['summary'])

    def test_inputs_and_independent_results_never_mutate(self):
        original, dictionary = deepcopy(self.base), deepcopy(self.dictionary)
        result = read.resolve(self.base, self.dictionary)
        result['models'][0]['fields'][0]['constraints']['maximumLength'] = 999
        result['projections'][1]['fields'][0]['type'] = 'BOOLEAN'
        self.assertEqual(self.base, original)
        self.assertEqual(self.dictionary, dictionary)
        self.assertEqual(read.resolve(self.base, self.dictionary),
                         self.cases['mariadb-independent-identities']['expected'])

    def test_failed_replacement_has_no_partial_catalog_and_preserves_old_result(self):
        old = read.resolve(self.base, self.dictionary)
        saved = deepcopy(old)
        broken = deepcopy(self.base)
        broken['projections']['summary']['fields'].append('rating-not-exposed')
        failure = read.resolve(broken, self.dictionary)
        self.assertFalse(failure['valid'])
        self.assertEqual(set(failure), {'valid', 'issues'})
        self.assertEqual(old, saved)

    def test_adding_any_unselected_physical_column_never_expands_projection(self):
        baseline = read.resolve(self.base, self.dictionary)
        for name in ('internal', 'secret', '\ue000', '\U00010000'):
            bundle = deepcopy(self.base)
            bundle['physical']['storage']['columns'].append({'name': name, 'nativeType': 'opaque'})
            result = read.resolve(bundle, self.dictionary)
            self.assertEqual(result['projections'], baseline['projections'])
            self.assertIn(name, [field['name'] for field in result['models'][0]['fields']])

    def test_projected_metadata_omits_native_connection_and_hidden_fields(self):
        result = read.resolve(self.base, self.dictionary)
        for projection in result['projections']:
            self.assertNotIn('physical', projection)
            self.assertNotIn('provider', json.dumps(projection))
            for field in projection['fields']:
                self.assertNotIn('physical', field)
                self.assertNotIn('intrinsicConstraints', field)
                self.assertNotIn('contextualConstraints', field)
        self.assertEqual([field['name'] for field in result['projections'][1]['fields']], ['code', 'id'])

    def test_integer_proof_matches_complete_domain_containment(self):
        for lower, upper in [(-128, 127), (0, 10), (-129, 10), (0, 128), (0, 0), (-32768, 32767)]:
            bundle = deepcopy(self.base)
            bundle['logical']['model']['fields']['rating']['constraints'] = {
                'minimum': str(lower), 'maximum': str(upper)}
            result = read.resolve(bundle, self.dictionary)
            self.assertEqual(result['valid'], -128 <= lower <= upper <= 127, (lower, upper))
            if not result['valid']:
                self.assertEqual(result['issues'][0]['family'], 'physical-incompatible')

    def test_dictionary_types_are_not_redefined_by_physical_type(self):
        result = read.resolve(self.base, self.dictionary)
        rating = next(field for field in result['models'][0]['fields'] if field['name'] == 'rating')
        self.assertEqual(rating['type'], 'INT16')
        self.assertEqual(rating['physical']['scalarType'], 'INT8')
        self.assertEqual(rating['compatibility'], 'compatible')

    def test_unbound_base_is_physical_but_dictionary_domain_is_never_clipped(self):
        bundle = deepcopy(self.base)
        bundle['physical']['storage']['columns'][2]['integerRange'] = {'minimum': '0', 'maximum': '10'}
        bundle['logical']['model']['fields'].pop('rating')
        result = read.resolve(bundle, self.dictionary)
        rating = result['models'][0]['fields'][2]
        self.assertEqual(rating['constraints'], {'minimum': '0', 'maximum': '10'})
        self.assertEqual(rating['type'], 'INT8')
        bundle['logical']['model']['fields']['rating'] = {'dictionary': 'test.int16'}
        self.assertEqual(read.resolve(bundle, self.dictionary)['issues'][0]['family'], 'physical-incompatible')

    def test_absent_flags_are_not_default_false_or_null(self):
        for prop in ('nullable', 'identity', 'generated'):
            bundle = deepcopy(self.base)
            bundle['physical']['storage']['columns'][0].pop(prop, None)
            before = read.resolve(bundle, self.dictionary)
            self.assertNotIn(prop, next(field for field in before['models'][0]['fields']
                                       if field['name'] == 'id')['physical'])
            bundle['physical']['storage']['columns'][0][prop] = False
            after = read.resolve(bundle, self.dictionary)
            self.assertIs(next(field for field in after['models'][0]['fields']
                               if field['name'] == 'id')['physical'][prop], False)
            self.assertNotEqual(before, after)
            bundle['physical']['storage']['columns'][0][prop] = None
            self.assertFalse(read.resolve(bundle, self.dictionary)['valid'])

    def test_source_adversaries_and_budget_boundaries(self):
        for payload in (b'\xff', b'{"label":"\\ud800"}', b'{"x":1,"x":2}'):
            with self.assertRaises(read.Rejected) as failure:
                read.parse_document(payload, 'json', 's')
            self.assertEqual(failure.exception.issue['code'], 'CDS_READ_SOURCE_INVALID')
        for payload in (b' ' * 1048577, b'[' * 129 + b']' * 129, b'{"x":0e129}'):
            with self.assertRaises(read.Rejected) as failure:
                read.parse_document(payload, 'json', 's')
            self.assertEqual(failure.exception.issue['code'], 'CDS_READ_LIMIT')
        self.assertEqual(read.parse_document(b' ' * 1048574 + b'{}', 'json', 's'), {})

    def test_json_mathematical_integer_metadata_remains_exact(self):
        bundle = deepcopy(self.base)
        raw = b'{"value":1e127}'
        number = read.parse_document(raw, 'json', 's')['value']
        self.assertIsInstance(number, Decimal)
        self.assertEqual(number, 10 ** 127)
        bundle['physical']['storage']['columns'][1]['characterLength']['value'] = number
        result = read.resolve(bundle, self.dictionary)
        self.assertTrue(result['valid'])
        self.assertEqual(result['models'][0]['physical']['columns'][1]['characterLength']['value'], number)

    def test_catalog_document_limit(self):
        for size, expected in [(256, True), (257, False)]:
            bundle = {'physical': {}, 'logical': {}, 'projections': {}}
            for i in range(size):
                doc = deepcopy(self.base['physical']['storage'])
                doc['id'] = f'storage.object{i}'
                bundle['physical'][f's{i:03}'] = doc
            self.assertEqual(read.resolve(bundle, self.dictionary)['valid'], expected)

    def test_field_limit(self):
        bundle = deepcopy(self.base)
        bundle['logical']['model']['fields'] = {}
        bundle['projections'] = {}
        for size, valid in [(2048, True), (2049, False)]:
            bundle['physical']['storage']['columns'] = [
                {'name': f'c{i}', 'nativeType': 'opaque'} for i in range(size)]
            bundle['physical']['storage'].pop('primaryKey', None)
            self.assertEqual(read.resolve(bundle, self.dictionary)['valid'], valid)

    def test_chain_limit_independent_of_cached_parent_order(self):
        for size, valid in [(64, True), (65, False)]:
            bundle = deepcopy(self.base)
            bundle['projections'] = {}
            for i in range(size):
                bundle['projections'][f's{i}'] = {
                    'apiVersion': 'arp.projection/v1', 'id': f'projection.p{i:03}', 'fields': ['id'],
                    'source': {'entity': 'demo.items'} if i == 0 else {'projection': f'projection.p{i - 1:03}'},
                    'operations': ['GET']}
            result = read.resolve(bundle, self.dictionary)
            self.assertEqual(result['valid'], valid)
            if not valid:
                self.assertEqual(result['issues'][0]['code'], 'CDS_READ_LIMIT')

    def test_error_precedence_independent_of_registration_order(self):
        bundle = deepcopy(self.base)
        bundle['physical']['storage']['extra'] = True
        bundle['logical']['model']['extra'] = True
        reordered = {key: dict(reversed(list(value.items()))) for key, value in reversed(list(bundle.items()))}
        self.assertEqual(read.resolve(bundle, self.dictionary), read.resolve(reordered, self.dictionary))
        self.assertEqual(read.resolve(bundle, self.dictionary)['issues'][0]['at'], '/physical/storage')

    def test_physical_range_diagnostic_does_not_depend_on_json_member_order(self):
        expected = {'valid': False, 'issues': [{'family': 'definition-invalid', 'code': 'CDS_READ_LIMIT',
                    'at': '/physical/storage/columns/2/integerRange/minimum'}]}
        for order in [('minimum', 'maximum'), ('maximum', 'minimum')]:
            bundle = deepcopy(self.base)
            bundle['physical']['storage']['columns'][2]['integerRange'] = {key: '9' * 4097 for key in order}
            self.assertEqual(read.resolve(bundle, self.dictionary), expected)

    def test_all_fixture_results_are_independent_of_json_object_member_order(self):
        def reordered(value):
            if isinstance(value, dict):
                return {key: reordered(item) for key, item in reversed(list(value.items()))}
            if isinstance(value, list):
                return [reordered(item) for item in value]
            return value
        for case in self.suite['cases']:
            with self.subTest(case=case['id']):
                result = read.resolve(reordered(case['input']), read.load_dictionary(case['dictionary']))
                self.assertEqual(read.canonical(result), read.canonical(case['expected']))

    def test_provider_identity_is_not_inferred_from_language_or_native_name(self):
        bundle = deepcopy(self.base)
        bundle['physical']['storage']['source'] = {'provider': 'registered-two', 'dialect': 'opaque', 'name': 't'}
        bundle['physical']['storage']['columns'][2] = {'name': 'rating', 'nativeType': 'INT8 in a name'}
        result = read.resolve(bundle, self.dictionary)
        self.assertTrue(result['valid'])
        self.assertEqual(result['models'][0]['fields'][2]['compatibility'], 'not-verified')

    def test_reused_intake_does_not_apply_dictionary_specific_shape_budget_to_cds(self):
        from source_profile import parse_bytes, IntakeLimit
        raw = json.dumps({'elements': [None] * 2049}).encode()
        self.assertEqual(len(read.parse_document(raw, 'json', 's')['elements']), 2049)
        with self.assertRaises(IntakeLimit):
            parse_bytes(raw, 'json')  # DICT-001's default behavior remains unchanged.

    def test_fixture_comparison_preserves_json_kinds_and_exact_numeric_value(self):
        self.assertNotEqual(read.canonical({'x': False}), read.canonical({'x': 0}))
        self.assertEqual(read.canonical({'x': 10 ** 127}), read.canonical({'x': Decimal('1e127')}))
        self.assertNotEqual(read.canonical(['a', 'b']), read.canonical(['b', 'a']))
        self.assertEqual(read.canonical({'a': 1, 'b': 2}), read.canonical({'b': 2, 'a': 1}))

    def test_database_plan_is_separate_and_its_failures_match_result_schema(self):
        plan = json.loads((ROOT / 'fixtures/cds/read/v1/database-cases.json').read_text())
        self.assertEqual(plan['execution'], 'REQUIRES_REAL_DB_NOT_EXECUTED')
        self.assertEqual({engine['engine'] for engine in plan['engines']}, {'postgresql', 'mariadb'})
        schema = json.loads((ROOT / 'schemas/cds/v1/read-result.schema.json').read_text())
        validator = read.Validator(schema, registry=read.REGISTRY)
        for engine in plan['engines']:
            self.assertTrue((ROOT / engine['setupSql']).is_file())
            for case in engine['cases']:
                if 'expected' in case:
                    validator.validate(case['expected'])

    def test_result_schema_rejects_partial_failure_or_wrong_error_family(self):
        schema = json.loads((ROOT / 'schemas/cds/v1/read-result.schema.json').read_text())
        validator = read.Validator(schema, registry=read.REGISTRY)
        result = {'valid': False, 'issues': [{'family': 'physical-incompatible',
                  'code': 'CDS_READ_DOMAIN_NOT_REPRESENTABLE', 'at': '/logical/model/fields/rating'}]}
        self.assertTrue(validator.is_valid(result))
        result['models'] = []
        self.assertFalse(validator.is_valid(result))
        result.pop('models')
        result['issues'][0]['family'] = 'execution-failure'
        self.assertFalse(validator.is_valid(result))


if __name__ == '__main__':
    unittest.main()