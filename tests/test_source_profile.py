"""Development regression coverage for the consolidated intake/fixture profile."""
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path('tools').resolve()))
import source_profile as profile
import check_contract as checker


class PortableIntakeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = checker.contract_validator(checker.load(checker.ROOT / 'schemas/dictionary/v1/dictionary.schema.json'))

    def test_numeric_boundaries_are_exact_without_context_rounding(self):
        self.assertEqual(profile.number('9' * 128), 10**128 - 1)
        self.assertEqual(profile.number('1e127'), Decimal('1e127'))
        self.assertEqual(profile.number('1e-128'), Decimal('1e-128'))
        for value in ['1e128', '-1e128', '1e129', '1e-129', '0e9999999999999999999']:
            with self.subTest(value=value), self.assertRaises(profile.IntakeLimit):
                profile.number(value)

    def test_number_token_boundaries_include_redundant_zeros(self):
        self.assertEqual(profile.number('1.' + '0' * 254), 1)
        with self.assertRaises(profile.IntakeLimit):
            profile.number('1.' + '0' * 255)
        # Leading exponent zeros are legal within token budget; value still exact.
        self.assertEqual(profile.number('1e+0000127'), Decimal('1e127'))
        with self.assertRaises(profile.IntakeLimit):
            profile.number('0e' + '0' * 255)

    def test_schema_integer_is_mathematical_but_boolean_is_not_number(self):
        for value in [1, Decimal('1.00'), Decimal('0.1e1'), 10**128 - 1]:
            document = {'apiVersion':'arp.dictionary/v1', 'elements':[
                {'id':'test.length', 'type':'TEXT', 'constraints':{'maximumLength':value}}]}
            self.assertTrue(self.validator.is_valid(document), value)
        for value in [True, Decimal('1.01'), -1, 10**128]:
            document = {'apiVersion':'arp.dictionary/v1', 'elements':[
                {'id':'test.length', 'type':'TEXT', 'constraints':{'maximumLength':value}}]}
            self.assertFalse(self.validator.is_valid(document), value)

    def test_numeric_rejection_families_distinguish_budget_and_integrality(self):
        sources = checker.load(checker.ROOT / 'fixtures/dictionary/v1/sources.json')
        small_fraction = next(c for c in sources if c['id']=='numeric-negative-exponent-boundary.json')
        model = profile.parse_source(checker.ROOT / small_fraction['path'], 'json')
        self.assertEqual(checker.isolated_source_verdict(model, self.validator), 'DICTIONARY_ELEMENT_INVALID')
        # A fractional value below 10^128 is a type/configuration error, not a limit.
        fractional = {'apiVersion':'arp.dictionary/v1', 'elements':[
            {'id':'test.length', 'type':'TEXT', 'constraints':{'maximumLength':Decimal('9'*128+'.5')}}]}
        self.assertEqual(checker.isolated_source_verdict(fractional, self.validator), 'DICTIONARY_ELEMENT_INVALID')
        definitions = checker.load(checker.ROOT / 'fixtures/dictionary/v1/definitions.json')
        too_large = next(c for c in definitions if c['id']=='metadata-length-above-limit')
        self.assertEqual(checker.isolated_source_verdict(too_large['document'], self.validator), 'DICTIONARY_LIMIT_EXCEEDED')

    def test_numeric_looking_strings_do_not_consume_number_budgets(self):
        text = '1e9999999999999999999'
        self.assertEqual(profile.parse_bytes(json.dumps({'label':text}).encode(), 'json'), {'label':text})
        for source in [f"label: '{text}'\n", f'label: "{text}"\n', f'label: |\n  {text}\n']:
            self.assertIn(text, profile.parse_bytes(source.encode(), 'yaml')['label'])

    def test_yaml_plain_scalar_resolution_is_not_yaml_eleven(self):
        source = "values: [yes, no, on, off, True, ~, 012, +1, 2026-11-14, 'null', null, true, false, 1.00, 0.1e1]\n"
        values = profile.parse_bytes(source.encode(), 'yaml')['values']
        self.assertEqual(values[:10], ['yes','no','on','off','True','~','012','+1','2026-11-14','null'])
        self.assertIsNone(values[10])
        self.assertIs(values[11], True)
        self.assertIs(values[12], False)
        self.assertEqual(values[13:], [Decimal('1.00'), Decimal('0.1e1')])

    def test_json_compatible_yaml_quotes_and_surrogate_pairs(self):
        model = profile.parse_bytes(b'label: "\\uD83D\\uDE00\\n"\nother: \'It\'\'s literal\'\n', 'yaml')
        self.assertEqual(model, {'label':'😀\n', 'other':"It's literal"})
        for source in [b'label: "\\uD800"', b'label: "\\U0001F600"', b'label: "\\x41"', b'label: "raw\ttab"']:
            with self.subTest(source=source), self.assertRaises((ValueError, UnicodeError)):
                profile.parse_bytes(source, 'yaml')

    def test_all_supported_block_chomping_modes(self):
        for marker, expected in [('|','a\nb\n'), ('|-','a\nb'), ('|+','a\nb\n\n'),
                                 ('>','a b\n'), ('>-','a b'), ('>+','a b\n\n')]:
            with self.subTest(marker=marker):
                self.assertEqual(profile.parse_bytes(f'label: {marker}\n  a\n  b\n\n'.encode(), 'yaml'), {'label':expected})
        self.assertEqual(profile.parse_bytes(b'label: >-\n  a\n    b\n  c\n', 'yaml')['label'], 'a\n  b\nc')
        self.assertEqual(profile.parse_bytes(b'label: >-\n  a\n\n  b\n', 'yaml')['label'], 'a\nb')
        self.assertEqual(profile.parse_bytes(b'label: |\n\n', 'yaml')['label'], '')
        self.assertEqual(profile.parse_bytes(b'label: |+\n\n', 'yaml')['label'], '\n')

    def test_multiline_nonblock_scalars_are_not_accepted_extensions(self):
        for source in [b'label: "a\n  b"', b'label: \'a\n  b\'', b'label: a\n  b', b'label: |2\n  a\n']:
            with self.subTest(source=source), self.assertRaises(profile.IntakeInvalid):
                profile.parse_bytes(source, 'yaml')

    def test_duplicate_null_keys_are_checked_after_decoding(self):
        for source, encoding in [(b'{"x":null,"\\u0078":1}', 'json'), (b'x: null\nx: 1', 'yaml'),
                                 (b'{x: null, "\\u0078": 1}', 'yaml')]:
            with self.subTest(source=source), self.assertRaises(profile.IntakeInvalid):
                profile.parse_bytes(source, encoding)

    def test_depth_boundary_and_quoted_brackets(self):
        for encoding in ['json','yaml']:
            self.assertIsInstance(profile.parse_bytes(('['*128+'0'+']'*128).encode(), encoding), list)
            with self.assertRaises(profile.IntakeLimit):
                profile.parse_bytes(('['*129+'0'+']'*129).encode(), encoding)
        self.assertEqual(profile.parse_bytes(json.dumps({'x':'['*300}).encode(), 'json')['x'], '['*300)

    def test_default_byte_and_element_boundaries_without_large_checked_in_files(self):
        data = b'{"label":"' + b'x'*(profile.MAX_BYTES-len(b'{"label":""}')) + b'"}'
        self.assertEqual(len(data), profile.MAX_BYTES)
        profile.parse_bytes(data, 'json')
        with self.assertRaises(profile.IntakeLimit):
            profile.parse_bytes(data+b' ', 'json')
        profile.parse_bytes(json.dumps({'elements':[{}]*2048}).encode(), 'json')
        with self.assertRaises(profile.IntakeLimit):
            profile.parse_bytes(json.dumps({'elements':[{}]*2049}).encode(), 'json')

    def test_directives_tags_and_literal_symbols_are_distinct(self):
        for source in [b'%UNKNOWN example\n---\n{}', b'label: !!str value', b'label: &a value', b'label: *a', b'<<: {}']:
            with self.subTest(source=source), self.assertRaises((ValueError, checker.yaml.YAMLError)):
                profile.parse_bytes(source, 'yaml')
        literal = '! & * <<: %YAML ---'
        self.assertEqual(profile.parse_bytes(('label: '+json.dumps(literal)).encode(), 'yaml'), {'label':literal})

    def test_indentation_and_line_endings(self):
        self.assertEqual(profile.parse_bytes(b'label: |\r\n    a\r\n    b\r\n', 'yaml')['label'], 'a\nb\n')
        self.assertEqual(profile.parse_bytes(b'label: |\n  a\tcontent\n', 'yaml')['label'], 'a\tcontent\n')
        for source in [b'label:\n\tchild: x', b'label: x\r', 'label: x\u2028'.encode()]:
            with self.subTest(source=source), self.assertRaises((ValueError, checker.yaml.YAMLError)):
                profile.parse_bytes(source, 'yaml')

    def test_inventory_keeps_scope_and_source_projections(self):
        counts = checker.check()
        self.assertEqual(counts['shared runtime assertions inventoried'], 428)
        self.assertEqual(counts['source descriptor projections'], 4)


if __name__ == '__main__':
    unittest.main()