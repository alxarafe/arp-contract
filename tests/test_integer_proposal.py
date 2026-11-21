"""Structural review of an unapproved INTEGER sketch; no runtime conformance claim."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / 'docs/proposals/integer'
LEGACY_TYPES = ('INT8', 'UINT8', 'INT16', 'UINT16', 'INT32', 'UINT32', 'INT64')
SEMANTIC_CASES = {
    'unsigned_negative', 'forced_too_narrow', 'signed_too_narrow', 'reversed',
    'empty_exclusive', 'overflow_unsigned64', 'overflow_signed64',
}


def document(type_name, constraints=None):
    return {
        'apiVersion': 'arp.dictionary/v1',
        'elements': [{'id': 'demo.test', 'type': type_name, 'constraints': constraints or {}}],
    }


class IntegerProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((PROPOSAL / 'dictionary.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.proposed = Draft202012Validator(cls.schema)
        cls.current = Draft202012Validator(json.loads(
            (ROOT / 'schemas/dictionary/v1/dictionary.schema.json').read_text(encoding='utf-8')))
        cls.vectors = json.loads((PROPOSAL / 'cases.json').read_text(encoding='utf-8'))

    def test_proposal_is_incompatible_in_both_directions(self):
        for name in LEGACY_TYPES:
            with self.subTest(type=name):
                self.assertTrue(self.current.is_valid(document(name)))
                self.assertFalse(self.proposed.is_valid(document(name)))
        self.assertTrue(self.proposed.is_valid(document('INTEGER')))
        self.assertFalse(self.current.is_valid(document('INTEGER')))

    def test_existing_catalog_remains_valid_only_under_current_schema(self):
        catalog = json.loads((ROOT / 'fixtures/dictionary/v1/catalog.json').read_text(encoding='utf-8'))
        self.current.validate(catalog)
        self.assertFalse(self.proposed.is_valid(catalog))

    def test_structurally_valid_proposal_vectors(self):
        for case in self.vectors['validDefinitions']:
            with self.subTest(case=case['id']):
                self.proposed.validate(document('INTEGER', case['constraints']))

    def test_structure_rejects_only_structural_errors(self):
        semantic = set()
        for case in self.vectors['invalidDefinitions']:
            with self.subTest(case=case['id']):
                valid = self.proposed.is_valid(document('INTEGER', case['constraints']))
                self.assertEqual(valid, case['id'] in SEMANTIC_CASES)
                if valid:
                    semantic.add(case['id'])
        self.assertEqual(semantic, SEMANTIC_CASES)

    def test_unrelated_metadata_limit_is_unchanged(self):
        for validator in (self.current, self.proposed):
            validator.validate(document('STRING', {'maximumLength': 10 ** 128 - 1}))
            self.assertFalse(validator.is_valid(document('STRING', {'maximumLength': 10 ** 128})))


if __name__ == '__main__':
    unittest.main()