#!/usr/bin/env python3
"""Offline schema and fixture integrity checks, never a production semantic runtime."""
import argparse
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
CODES = {'DICTIONARY_' + x for x in ['DOCUMENT_INVALID', 'FORMAT_UNSUPPORTED', 'ELEMENT_INVALID', 'DUPLICATE_ELEMENT', 'ELEMENT_NOT_FOUND', 'VALUE_TYPE', 'VALUE_CONSTRAINT', 'LIMIT_EXCEEDED']}
ORDER = ['minimum', 'maximum', 'multipleOf', 'precision', 'scale', 'minimumLength', 'maximumLength', 'pattern', 'enumValues']


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate mapping key')
        result[key] = value
    return result


def unicode_scalars(value):
    if isinstance(value, str):
        value.encode('utf-8', errors='strict')
    elif isinstance(value, dict):
        for k, v in value.items():
            unicode_scalars(k)
            unicode_scalars(v)
    elif isinstance(value, list):
        for item in value:
            unicode_scalars(item)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def parse_source(path, encoding):
    """Check parser restrictions only. No source registration or scalar validation."""
    text = path.read_bytes().decode('utf-8', errors='strict')
    if encoding == 'json':
        model = json.loads(text, object_pairs_hook=unique,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    else:
        # BaseLoader avoids YAML 1.1 timestamps and booleans. This tooling profile
        # only parses the simple string-valued YAML fixtures; not a YAML runtime.
        for token in yaml.scan(text):
            if isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken,
                                  yaml.tokens.TagToken, yaml.tokens.DirectiveToken)):
                raise ValueError('forbidden YAML token')
        docs = list(yaml.compose_all(text, Loader=yaml.BaseLoader))
        if len(docs) != 1:
            raise ValueError('multiple documents')
        def convert(node):
            if isinstance(node, yaml.ScalarNode):
                return node.value
            if isinstance(node, yaml.SequenceNode):
                return [convert(n) for n in node.value]
            pairs = [(convert(k), convert(v)) for k, v in node.value]
            if any(k == '<<' for k, _ in pairs):
                raise ValueError('merge key')
            return unique(pairs)
        model = convert(docs[0])
    unicode_scalars(model)
    return model


def outcome(expected, element_id=None, unresolved=False):
    assert set(expected) <= {'valid', 'issues', 'normalizedValue'}
    assert type(expected['valid']) is bool
    issues = expected['issues']
    assert isinstance(issues, list)
    assert expected['valid'] == (not issues)
    if not expected['valid']:
        assert 'normalizedValue' not in expected
    seen = []
    for issue in issues:
        assert set(issue) <= {'code', 'elementId', 'constraint'}
        assert issue['code'] in CODES
        if element_id is not None:
            assert issue['elementId'] == element_id
        if issue['code'] == 'DICTIONARY_VALUE_CONSTRAINT':
            if not unresolved:
                assert issue['constraint'] in ORDER
                seen.append(ORDER.index(issue['constraint']))
    assert seen == sorted(seen)


def check(root=ROOT):
    schema = load(root / 'schemas/dictionary/v1/dictionary.schema.json')
    Draft202012Validator.check_schema(schema)
    # No remote references, including accidental additions to nested schemas.
    def refs(x):
        if isinstance(x, dict):
            assert '$ref' not in x or x['$ref'].startswith('#')
            for v in x.values(): refs(v)
        if isinstance(x, list):
            for v in x: refs(v)
    refs(schema)
    validator = Draft202012Validator(schema)
    folder = root / 'fixtures/dictionary/v1'
    manifest = load(folder / 'manifest.json')
    assert manifest['apiVersion'] == 'arp.dictionary/v1'
    assert manifest['feature'] == 'ARP-DICT-001'
    assert set(manifest['sets']) == {'catalog','sources','definitions','values','catalogs'}
    for name, path in manifest['sets'].items():
        assert path == name + '.json' and (folder / path).is_file()
    catalog = load(folder / 'catalog.json')
    validator.validate(catalog)
    declared = {e['type'] for e in catalog['elements']}
    ids = set()
    counts = {}
    def identity(case):
        assert case['id'] not in ids, case['id']
        ids.add(case['id'])
    values = load(folder / 'values.json')
    successful_types = set()
    unresolved = 0
    for case in values:
        identity(case)
        validator.validate({'apiVersion':'arp.dictionary/v1', 'elements':[case['element']]})
        ambiguous = case.get('unresolvedContract') == 'intrinsic-range-constraint-name'
        outcome(case['expected'], case['element']['id'], ambiguous)
        if case['expected']['valid']:
            assert 'normalizedValue' in case['expected']
            unicode_scalars(case['expected']['normalizedValue'])
            successful_types.add(case['element']['type'])
        unresolved += ambiguous
    assert successful_types == declared and len(declared) == 17
    counts['value vectors'] = len(values)
    definitions = load(folder / 'definitions.json')
    for case in definitions:
        identity(case)
        assert validator.is_valid(case['document']) == case['schemaValid'], case['id']
        outcome(case['expected'])
    counts['definition vectors'] = len(definitions)
    sources = load(folder / 'sources.json')
    models = []
    for case in sources:
        identity(case)
        path = (root / case['path']).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file()
        try:
            model = parse_source(path, case['encoding'])
        except (ValueError, UnicodeError, yaml.YAMLError):
            assert case['expected']['issues'][0]['code'] == 'DICTIONARY_DOCUMENT_INVALID'
            assert case['schemaValid'] is None
        else:
            assert validator.is_valid(model) == case['schemaValid'], case['id']
            if case['expected']['valid']: models.append(model)
        outcome(case['expected'])
    assert len(models) == 2 and models[0] == models[1]
    counts['source vectors'] = len(sources)
    catalogs = load(folder / 'catalogs.json')
    for case in catalogs:
        identity(case)
        contexts = set()
        for step in case['steps']:
            assert step['operation'] in {'buildCatalog','resolve','assertRejectedGeneration'}
            if step['operation'] == 'buildCatalog':
                contexts.add(step['context'])
                for source in step['sources']:
                    assert isinstance(source['providerId'],str) and isinstance(source['sourceId'],str)
                    validator.validate(source['document'])
            else:
                assert step['context'] in contexts
            if step['operation'] != 'assertRejectedGeneration': outcome(step['expected'])
    counts['catalog scenarios'] = len(catalogs)
    return counts, unresolved


def main():
    if not __debug__:
        raise RuntimeError("Run checks without Python -O; integrity assertions are required")
    counts, unresolved = check()
    print('PASS: Draft 2020-12 schema and fixture integrity')
    for name, count in counts.items(): print(f'  {name}: {count}')
    print(f'  unresolved intrinsic-range vectors: {unresolved}')
    print('NOT EXECUTED: semantic conformance; Java/.NET/PHP remain NOT_EVALUATED')

if __name__ == '__main__': main()
