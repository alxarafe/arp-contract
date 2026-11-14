#!/usr/bin/env python3
"""Offline schema and fixture integrity checks, never a production semantic runtime."""
import json
from decimal import Decimal
from jsonschema import validators
from pathlib import Path
from jsonschema import Draft202012Validator
import yaml
from source_profile import (parse_source, unique, unicode_scalars, IntakeInvalid, IntakeLimit,
                            MAX_BYTES, MAX_ELEMENTS, MAX_DEPTH, MAX_NUMBER_CHARS, MAX_EXPONENT, MAX_LENGTH)
from portable_pattern import parse as parse_pattern, matches, PatternInvalid, PatternLimit

ROOT = Path(__file__).resolve().parents[1]
CODES = {'DICTIONARY_' + x for x in ['DOCUMENT_INVALID', 'FORMAT_UNSUPPORTED', 'ELEMENT_INVALID', 'DUPLICATE_ELEMENT', 'ELEMENT_NOT_FOUND', 'VALUE_TYPE', 'VALUE_CONSTRAINT', 'LIMIT_EXCEEDED']}
ORDER = ['typeRange', 'minimum', 'maximum', 'multipleOf', 'precision', 'scale', 'minimumLength', 'maximumLength', 'pattern', 'enumValues']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_float=Decimal,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def contract_validator(schema):
    # JSON mathematical integer model, without converting Decimal through float.
    integer = Draft202012Validator.TYPE_CHECKER.redefine('integer',
        lambda checker, value: type(value) is int or
        isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value())
    return validators.extend(Draft202012Validator, type_checker=integer)(schema)


def outcome(expected, element_id=None):
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
            assert issue['constraint'] in ORDER
            seen.append(ORDER.index(issue['constraint']))
    assert seen == sorted(seen)


def pattern_verdict(pattern):
    try:
        parse_pattern(pattern)
    except PatternLimit:
        return 'DICTIONARY_LIMIT_EXCEEDED'
    except PatternInvalid:
        return 'DICTIONARY_ELEMENT_INVALID'
    return None


def isolated_source_verdict(model, validator):
    """Classify only the isolated defects in source fixtures; no accumulation policy."""
    if not isinstance(model, dict):
        return 'DICTIONARY_DOCUMENT_INVALID'
    if model.get('apiVersion') != 'arp.dictionary/v1':
        return 'DICTIONARY_FORMAT_UNSUPPORTED'
    if (set(model) != {'apiVersion', 'elements'}
            or not isinstance(model['elements'], list) or not model['elements']
            or any(not isinstance(e, dict) for e in model['elements'])):
        return 'DICTIONARY_DOCUMENT_INVALID'
    for element in model['elements']:
        constraints = element.get('constraints', {}) if isinstance(element, dict) else {}
        if isinstance(constraints, dict):
            for name in ('minimumLength', 'maximumLength'):
                number = constraints.get(name)
                if type(number) is int or isinstance(number, Decimal):
                    if (number.copy_abs() if isinstance(number, Decimal) else abs(number)) >= MAX_LENGTH + 1:
                        return 'DICTIONARY_LIMIT_EXCEEDED'
    if not validator.is_valid(model):
        return 'DICTIONARY_ELEMENT_INVALID'
    return None


def descriptor_projection(declaration):
    # Fixture coherence only: compare authored data, do not resolve a runtime.
    projection = {k:v for k,v in declaration.items()
                  if k in {'id','type','constraints','enumValues','label','description'}}
    projection.setdefault('constraints', {})
    return projection


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
    validator = contract_validator(schema)
    folder = root / 'fixtures/dictionary/v1'
    manifest = load(folder / 'manifest.json')
    assert manifest['apiVersion'] == 'arp.dictionary/v1'
    assert manifest['feature'] == 'ARP-DICT-001'
    assert set(manifest['sets']) == {'catalog','sources','definitions','values','catalogs','patterns'}
    for name, path in manifest['sets'].items():
        assert path == name + '.json' and (folder / path).is_file()
    catalog = load(folder / 'catalog.json')
    validator.validate(catalog)
    declared = {e['type'] for e in catalog['elements']}
    ids = set()
    counts = {}
    assert manifest['intakeProfile'] == {
        'maxDocumentBytes':MAX_BYTES, 'maxElementsPerSource':MAX_ELEMENTS,
        'maxCollectionDepth':MAX_DEPTH, 'maxNumberTokenCharacters':MAX_NUMBER_CHARS,
        'maxAbsoluteExponent':MAX_EXPONENT, 'numberMagnitudeExclusive':'1e128'}
    def length_bounds(node):
        if isinstance(node, dict):
            for key in ('minimumLength', 'maximumLength'):
                if key in node:
                    assert node[key]['maximum'] == MAX_LENGTH
            for child in node.values(): length_bounds(child)
        elif isinstance(node, list):
            for child in node: length_bounds(child)
    length_bounds(schema)
    def identity(case):
        assert case['id'] not in ids, case['id']
        ids.add(case['id'])
    values = load(folder / 'values.json')
    successful_types = set()
    for case in values:
        identity(case)
        validator.validate({'apiVersion':'arp.dictionary/v1', 'elements':[case['element']]})
        assert 'unresolvedContract' not in case
        outcome(case['expected'], case['element']['id'])
        if 'pattern' in case['element'].get('constraints', {}):
            pattern = case['element']['constraints']['pattern']
            parse_pattern(pattern)
            try:
                matched = matches(pattern, case['value'])
            except PatternLimit:
                assert case['expected']['issues'][0]['code'] == 'DICTIONARY_LIMIT_EXCEEDED'
            else:
                pattern_issue = any(i.get('constraint') == 'pattern' for i in case['expected']['issues'])
                assert matched == (not pattern_issue), case['id']
        if case['expected']['valid']:
            assert 'normalizedValue' in case['expected']
            unicode_scalars(case['expected']['normalizedValue'])
            successful_types.add(case['element']['type'])
    assert successful_types == declared and len(declared) == 17
    counts['value vectors'] = len(values)
    definitions = load(folder / 'definitions.json')
    for case in definitions:
        identity(case)
        assert validator.is_valid(case['document']) == case['schemaValid'], case['id']
        outcome(case['expected'])
        for element in case['document']['elements']:
            pattern = element.get('constraints', {}).get('pattern')
            if pattern is not None:
                code = pattern_verdict(pattern)
                if code:
                    assert case['expected']['issues'] == [{'code':code}], case['id']
    counts['definition vectors'] = len(definitions)
    sources = load(folder / 'sources.json')
    models = {}
    source_projections = 0
    for case in sources:
        identity(case)
        path = (root / case['path']).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file()
        try:
            model = parse_source(path, case['encoding'])
        except IntakeLimit:
            assert case['expected']['issues'][0]['code'] == 'DICTIONARY_LIMIT_EXCEEDED', case['id']
            assert case['schemaValid'] is None
        except (ValueError, UnicodeError, yaml.YAMLError):
            assert case['expected']['issues'][0]['code'] == 'DICTIONARY_DOCUMENT_INVALID', case['id']
            assert case['schemaValid'] is None
        else:
            assert validator.is_valid(model) == case['schemaValid'], case['id']
            code = isolated_source_verdict(model, validator)
            assert case['expected']['valid'] == (code is None), case['id']
            if code: assert case['expected']['issues'] == [{'code':code}], case['id']
            if case['expected']['valid']:
                models[case['id']] = model
                if 'descriptorProjection' in case:
                    projection = case['descriptorProjection']
                    declaration = next(e for e in model['elements'] if e['id'] == projection['id'])
                    assert projection == descriptor_projection(declaration), case['id']
                    source_projections += 1
        outcome(case['expected'])
    assert models['valid.yaml'] == models['valid.json']
    counts['source vectors'] = len(sources)
    counts['source descriptor projections'] = source_projections
    catalogs = load(folder / 'catalogs.json')
    for case in catalogs:
        identity(case)
        contexts = set()
        declarations = {}
        for step in case['steps']:
            assert step['operation'] in {'buildCatalog','resolve','assertRejectedGeneration'}
            if step['operation'] == 'buildCatalog':
                contexts.add(step['context'])
                for source in step['sources']:
                    assert isinstance(source['providerId'],str) and isinstance(source['sourceId'],str)
                    validator.validate(source['document'])
                if step['expected']['valid']:
                    declarations[step['context']] = {e['id']: e for src in step['sources'] for e in src['document']['elements']}
            else:
                assert step['context'] in contexts
            if step['operation'] != 'assertRejectedGeneration': outcome(step['expected'])
            if step['operation'] == 'resolve' and step['expected']['valid']:
                declaration = declarations[step['context']][step['elementId']]
                assert step['descriptorProjection'] == descriptor_projection(declaration), case['id']
    counts['catalog scenarios'] = len(catalogs)
    patterns = load(folder / 'patterns.json')
    for case in patterns:
        identity(case)
        document = {'apiVersion':'arp.dictionary/v1', 'elements':[{'id':'test.pattern', 'type':'STRING', 'constraints':{'pattern':case['pattern']}}]}
        assert validator.is_valid(document) == case['schemaValid'], case['id']
        code = pattern_verdict(case['pattern'])
        assert case['expected']['valid'] == (code is None), case['id']
        if code:
            assert case['expected']['code'] == code
            assert not case['samples']
        for sample in case['samples']:
            assert matches(case['pattern'], sample['value']) == sample['matches'], case['id']
    counts['pattern grammar vectors'] = len(patterns)
    counts['shared runtime assertions inventoried'] = (1 + len(values) + len(definitions) + len(sources)
        + source_projections + len(patterns) + sum(len(p['samples']) for p in patterns)
        + sum(len(c['steps']) for c in catalogs)
        + sum('descriptorProjection' in step for c in catalogs for step in c['steps']))
    return counts


def main():
    if not __debug__:
        raise RuntimeError("Run checks without Python -O; integrity assertions are required")
    counts = check()
    print('PASS: Draft 2020-12 schema and fixture integrity')
    for name, count in counts.items(): print(f'  {name}: {count}')
    print('NOT EXECUTED: stack semantic conformance for this candidate; prior 0172ab6 evidence does not establish updated support')

if __name__ == '__main__': main()
