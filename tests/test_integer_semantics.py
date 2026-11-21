"""Independent INTEGER arithmetic, proposal semantics and cross-operation regressions."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import integer_semantics as integer
import check_contract as dictionary
import check_cds_read_draft as cds
import check_cds_listget_draft as reads


class IntegerSemanticsTests(unittest.TestCase):
    def test_every_8_bit_value_matches_independent_arithmetic(self):
        for signed, low, high in ((True, -128, 127), (False, 0, 255)):
            constraints = {'bits': 8, 'signed': signed}
            for value in range(-260, 520):
                with self.subTest(signed=signed, value=value):
                    self.assertEqual(not integer.issues(str(value), constraints), low <= value <= high)

    def test_size_inference_at_every_capacity_transition(self):
        for signed in (True, False):
            for bits, next_bits in ((8, 16), (16, 32), (32, 64)):
                maximum = 2 ** (bits - int(signed)) - 1
                constraints = {'minimum': '0', 'maximum': str(maximum), 'signed': signed}
                self.assertEqual(integer.derive(constraints).bits, bits)
                constraints['maximum'] = str(maximum + 1)
                self.assertEqual(integer.derive(constraints).bits, next_bits)

    def test_multiple_of_existence_matches_enumeration_including_negative_intervals(self):
        for low in range(-8, 9):
            for high in range(low, 9):
                for step in (1, 2, 3, 5, 17):
                    constraints = {'minimum': str(low), 'maximum': str(high), 'multipleOf': str(step)}
                    possible = any(value % step == 0 for value in range(low, high + 1))
                    try:
                        integer.derive(constraints)
                    except integer.IntegerInvalid:
                        self.assertFalse(possible, constraints)
                    else:
                        self.assertTrue(possible, constraints)

    def test_historical_proposal_has_executable_semantic_expectations(self):
        cases = dictionary.load(ROOT / 'docs/proposals/integer/cases.json')
        definitions = {case['id']: case for case in cases['validDefinitions']}
        for case in definitions.values():
            actual = integer.derive(case['constraints'])
            self.assertEqual((actual.bits, actual.signed), (case['bits'], case['signed']))
        for case in cases['invalidDefinitions']:
            with self.subTest(case=case['id']), self.assertRaises(integer.IntegerInvalid):
                integer.derive(case['constraints'])
        for case in cases['values']:
            self.assertEqual(not integer.issues(case['input'], definitions[case['definition']]['constraints']),
                             case['valid'])

    def test_exact_integer_metadata_and_invalid_definitions_at_source_boundary(self):
        self.assertEqual(integer.derive({'bits': Decimal('8.0')}).bits, 8)
        validator = dictionary.contract_validator(dictionary.load(
            ROOT / 'schemas/dictionary/v1/dictionary.schema.json'))
        for constraints in ({'bits': None}, {'signed': None}, {'signed': False, 'maximum': '-1'},
                            {'minimum': '1', 'maximum': '2', 'multipleOf': '3'}):
            doc = {'apiVersion': 'arp.dictionary/v1',
                   'elements': [{'id': 'test.invalid', 'type': 'INTEGER', 'constraints': constraints}]}
            self.assertEqual(dictionary.isolated_source_verdict(doc, validator), 'DICTIONARY_ELEMENT_INVALID')

    def test_lexical_exactness_and_resource_limit(self):
        constraints = {'bits': 64, 'signed': False}
        for value in (True, 1, 9007199254740993, 18446744073709551615, None,
                      '01', '+1', '1.0', '1e0', ' 1', '1\n', '١'):
            self.assertEqual(integer.issues(value, constraints)[0]['code'], 'DICTIONARY_VALUE_TYPE')
        self.assertEqual(integer.normalized('-0'), '0')
        self.assertFalse(integer.issues('-0', constraints))
        self.assertEqual(integer.issues('9' * 4097, constraints)[0]['code'], 'DICTIONARY_LIMIT_EXCEEDED')
        self.assertNotEqual(reads.integer('9007199254740993', constraints),
                            reads.integer('9007199254740994', constraints))

    def test_context_does_not_reinfer_capacity_and_identity_ignores_business_limit(self):
        column = {'name': 'id', 'scalarType': 'INTEGER', 'nativeType': 'verified fixture',
                  'integerRange': {'minimum': '0', 'maximum': '18446744073709551615'}}
        elements = {'test.id': {'type': 'INTEGER', 'constraints': {'bits': 64, 'signed': False}}}
        field = cds.field(column, {'dictionary': 'test.id',
                                  'constraints': {'minimum': '0', 'maximum': '10'}}, elements, '/id')
        self.assertEqual(field['constraints']['bits'], 64)
        self.assertFalse(field['constraints']['signed'])
        self.assertEqual(reads.integer('18446744073709551615', field['constraints']), 18446744073709551615)
        self.assertTrue(integer.issues('11', field['constraints']))

    def test_unsigned64_list_get_and_ordering_without_rounding(self):
        assets = deepcopy(reads.load(reads.FOLDER / 'products.json'))
        vectors = reads.load(reads.FOLDER / 'cases.json')
        element = next(e for e in assets['dictionary']['elements'] if e['id'] == 'products.product_id')
        element['constraints'] = {'bits': 64, 'signed': False}
        layout = assets['layouts']['simple']
        col = layout['definitions']['physical']['observed']['columns'][1]
        col['integerRange'] = {'minimum': '0', 'maximum': '18446744073709551615'}
        layout['rows'] = layout['rows'][:2]
        for row, value in zip(layout['rows'], ('18446744073709551615', '18446744073709551614')):
            row['values']['product_id'] = value
        base = deepcopy(next(c for c in vectors['cases'] if c['id'] == 'get-simple-typed-key'))
        base['request']['inputs']['key']['components'][0]['value'] = '18446744073709551615'
        result = reads.invoke(base, assets, vectors['defaults'])
        self.assertEqual(result['response']['output']['record']['key']['components'][0],
                         {'field': 'product_id', 'type': 'INTEGER', 'value': '18446744073709551615'})
        base['request'].update(operation='LIST', inputs={'limit': 100})
        result = reads.invoke(base, assets, vectors['defaults'])
        self.assertEqual([r['key']['components'][0]['value'] for r in result['response']['output']['records']],
                         ['18446744073709551614', '18446744073709551615'])
        base['request'].update(operation='GET', inputs={'key': {'components': [
            {'field': 'product_id', 'type': 'INTEGER', 'value': '18446744073709551616'}]}})
        result = reads.invoke(base, assets, vectors['defaults'])
        self.assertEqual(result['response']['status'], 'rejected')
        self.assertEqual(result['observed']['reads'], 0)


if __name__ == '__main__':
    unittest.main()