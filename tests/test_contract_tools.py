import copy
import importlib.util
import unittest

spec = importlib.util.spec_from_file_location('checker', 'tools/check_contract.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ContractChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = checker.load(checker.ROOT / 'schemas/dictionary/v1/dictionary.schema.json')
        cls.validator = checker.Draft202012Validator(cls.schema)
        cls.doc = checker.load(checker.ROOT / 'fixtures/dictionary/v1/catalog.json')

    def test_suite(self):
        counts, unresolved = checker.check()
        self.assertGreater(counts['value vectors'], 100)
        self.assertEqual(unresolved, 11)

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

if __name__ == '__main__': unittest.main()
