"""Candidate-only structure and fixture checks; not SQL introspection nor runtime conformance."""
import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'fixtures/physical/v1'
SCHEMA = ROOT / 'schemas/physical/v1/physical.schema.json'


def local_semantic_issues(doc):
    """Small declared local invariants; never proof that the DB matches this snapshot."""
    issues = []
    columns = doc['columns']
    names = [col['name'] for col in columns]
    ordinals = [col['ordinal'] for col in columns]
    if len(names) != len(set(names)):
        issues.append('DUPLICATE_COLUMN')
    if len(ordinals) != len(set(ordinals)):
        issues.append('DUPLICATE_ORDINAL')
    local = set(names)
    for name in doc.get('primaryKey', []):
        if name not in local:
            issues.append('UNKNOWN_PRIMARY_KEY_COLUMN')
    for index in doc.get('indexes', []):
        if any(name not in local for name in index['columns']):
            issues.append('UNKNOWN_INDEX_COLUMN')
    for fk in doc.get('foreignKeys', []):
        if any(name not in local for name in fk['columns']):
            issues.append('UNKNOWN_FOREIGN_KEY_COLUMN')
        if len(fk['columns']) != len(fk['target']['columns']):
            issues.append('MISMATCHED_FOREIGN_KEY_ARITY')
    for col in columns:
        extent = col.get('integerRange')
        if extent is not None and int(extent['minimum']) > int(extent['maximum']):
            issues.append('REVERSED_INTEGER_RANGE')
        geom = col.get('decimalGeometry')
        if geom is not None and geom['scale'] > geom['precision']:
            issues.append('INVALID_DECIMAL_GEOMETRY')
    return issues


class PhysicalContractCandidateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.cases = json.loads((FIXTURES / 'cases.json').read_text(encoding='utf-8'))['cases']

    def test_candidate_fixture_expectations(self):
        ids = [item['id'] for item in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 10)
        for item in self.cases:
            with self.subTest(case=item['id']):
                errors = list(self.validator.iter_errors(item['document']))
                if item['expected'] == 'SCHEMA_INVALID':
                    self.assertTrue(errors, item['id'])
                    continue
                self.assertFalse(errors, [str(e) for e in errors])
                semantic = local_semantic_issues(item['document'])
                if item['expected'] == 'SEMANTIC_INVALID':
                    self.assertTrue(semantic, item['id'])
                else:
                    self.assertEqual(item['expected'], 'VALID')
                    self.assertEqual(semantic, [])

    def test_yaml_example_matches_json_fixture(self):
        text = (FIXTURES / 'example.mariadb.yaml').read_text(encoding='utf-8')
        example = yaml.safe_load(text)
        self.assertFalse(list(self.validator.iter_errors(example)))
        self.assertEqual(local_semantic_issues(example), [])
        self.assertEqual(example, next(c['document'] for c in self.cases if c['id'] == 'valid-mariadb'))

    def test_unknown_does_not_mean_false(self):
        doc = next(c['document'] for c in self.cases if c['id'] == 'valid-unknown-nullability')
        self.assertNotIn('nullable', doc['columns'][0])
        self.assertFalse(list(self.validator.iter_errors(doc)))
        self.assertIsNot(doc['columns'][0].get('nullable', 'UNVERIFIED'), False)


if __name__ == '__main__':
    unittest.main()
