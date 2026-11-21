import copy
import importlib.util
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))

spec = importlib.util.spec_from_file_location('checker', 'tools/check_contract.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ContractChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = checker.load(checker.ROOT / 'schemas/dictionary/v1/dictionary.schema.json')
        cls.validator = checker.contract_validator(cls.schema)
        cls.doc = checker.load(checker.ROOT / 'fixtures/dictionary/v1/catalog.json')

    def test_suite(self):
        counts = checker.check()
        self.assertGreater(counts['value vectors'], 100)
        self.assertGreater(counts['pattern grammar vectors'], 40)

    def test_closed_objects_and_types(self):
        for change in [lambda d: d.update(extra=1),
                       lambda d: d['elements'][0].update(extra=1),
                       lambda d: d['elements'][0].update(constraints={'minimum':'0'}),
                       lambda d: d['elements'][0].update(enumValues=['a']),
                       lambda d: d['elements'][1].update(id='test.x\n')]:
            d = copy.deepcopy(self.doc)
            change(d)
            self.assertFalse(self.validator.is_valid(d))

    def test_failure_cannot_normalize(self):
        with self.assertRaises(AssertionError):
            checker.outcome({'valid':False,'normalizedValue':'0','issues':[{'code':'DICTIONARY_VALUE_TYPE','elementId':'x.y'}]})

    def test_constraint_order(self):
        with self.assertRaises(AssertionError):
            checker.outcome({'valid':False,'issues':[{'code':'DICTIONARY_VALUE_CONSTRAINT','constraint':c} for c in ['scale','minimum']]})

    def test_unknown_error_and_missing_constraint(self):
        for issue in [{'code':'HTTP_400'}, {'code':'DICTIONARY_VALUE_CONSTRAINT'}]:
            with self.assertRaises((AssertionError,KeyError)):
                checker.outcome({'valid':False,'issues':[issue]})

    def test_duplicate_mapping(self):
        with self.assertRaises(ValueError):
            checker.unique([('x',1),('x',2)])

    def test_type_range_precedes_declared_constraints(self):
        checker.outcome({'valid':False,'issues':[
            {'code':'DICTIONARY_VALUE_CONSTRAINT','constraint':c}
            for c in ['typeRange','minimum','maximum']]})
        with self.assertRaises(AssertionError):
            checker.outcome({'valid':False,'issues':[
                {'code':'DICTIONARY_VALUE_CONSTRAINT','constraint':c}
                for c in ['minimum','typeRange']]})
        d = copy.deepcopy(self.doc)
        d['elements'][3]['constraints'] = {'typeRange':True}
        self.assertFalse(self.validator.is_valid(d))

    def test_all_range_vectors_complete(self):
        values = checker.load(checker.ROOT / 'fixtures/dictionary/v1/values.json')
        ranges = [v for v in values if v['id'].endswith(('-above','-below')) and any(i.get('constraint') == 'typeRange'
                  for i in v['expected']['issues'])]
        self.assertEqual(len(ranges), 14)
        self.assertTrue(all('unresolvedContract' not in v for v in values))
        for v in values:
            if v['id'].startswith('UINT') and v['id'].endswith('-below'):
                self.assertEqual(v['expected']['issues'][0]['code'], 'DICTIONARY_VALUE_CONSTRAINT')
                self.assertEqual(v['expected']['issues'][0]['constraint'], 'typeRange')
        self.assertEqual(next(v for v in values if v['id']=='numeric-limit')
                         ['expected']['issues'][0]['code'], 'DICTIONARY_LIMIT_EXCEEDED')

    def test_descriptor_projection(self):
        self.assertEqual(checker.descriptor_projection({'id':'test.x','type':'STRING'}),
                         {'id':'test.x','type':'STRING','constraints':{}})
        declaration = {'id':'test.x','type':'ENUM','enumValues':['z','a'],
                       'label':'Label','description':'Description'}
        projection = checker.descriptor_projection(declaration)
        self.assertEqual(projection, declaration | {'constraints':{}})
        self.assertEqual(projection['enumValues'], ['z','a'])
        self.assertNotIn('label', checker.descriptor_projection({'id':'test.x','type':'STRING'}))

    def test_pattern_grammar_and_full_match(self):
        for p in ['', '^$', '[]', '[z-a]', 'a\n', '\x7f', 'a++', 'a{01}', 'a{1025}', r'\d']:
            self.assertEqual(checker.pattern_verdict(p), 'DICTIONARY_ELEMENT_INVALID')
        self.assertIsNone(checker.pattern_verdict('a'*512))
        self.assertEqual(checker.pattern_verdict('a'*513), 'DICTIONARY_LIMIT_EXCEEDED')
        self.assertTrue(checker.matches('a{0}', ''))
        self.assertFalse(checker.matches('^a$', 'a\n'))
        self.assertTrue(checker.matches(r'\$', '$'))
        self.assertTrue(checker.matches(r'\\$', '\\'))
        self.assertTrue(checker.matches('[ -~]', '~'))
        self.assertFalse(checker.matches('[ -~]', 'é'))
        with self.assertRaises(checker.PatternLimit): checker.matches('a*', 'a'*4097)

    def test_all_ascii_controls_rejected(self):
        for n in [*range(32), 127]:
            for pattern in ['a'+chr(n), '['+chr(n)+']', '\\'+chr(n)]:
                self.assertEqual(checker.pattern_verdict(pattern), 'DICTIONARY_ELEMENT_INVALID')

    def test_source_error_classification(self):
        verdict = lambda d: checker.isolated_source_verdict(d, self.validator)
        self.assertEqual(verdict([]), 'DICTIONARY_DOCUMENT_INVALID')
        self.assertEqual(verdict({'elements':[{'id':'test.x','type':'STRING'}]}),
                         'DICTIONARY_FORMAT_UNSUPPORTED')
        self.assertEqual(verdict({'apiVersion':'arp.dictionary/v1','elements':[]}),
                         'DICTIONARY_DOCUMENT_INVALID')
        self.assertEqual(verdict({'apiVersion':'arp.dictionary/v1','elements':[{'id':'single','type':'STRING'}]}),
                         'DICTIONARY_ELEMENT_INVALID')

if __name__ == '__main__': unittest.main()
