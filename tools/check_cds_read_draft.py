#!/usr/bin/env python3
"""Candidate CDS read fixture oracle. No SQL, row reads, services or native conformance.

The dictionary argument is an already validated DICT-001 descriptor snapshot.
This bounded oracle does not reimplement scalar value validation.
"""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re

from referencing import Registry, Resource

from check_cds_draft import INTEGER_RANGES
from check_contract import contract_validator, descriptor_projection, load as load_json
from source_profile import IntakeInvalid, IntakeLimit, parse_bytes

ROOT = Path(__file__).resolve().parents[1]
INTEGER = re.compile(r'-?(?:0|[1-9][0-9]*)\Z', re.ASCII)
ORDER = ('physical', 'logical', 'projections')
SCHEMAS = {kind: json.loads((ROOT / 'schemas/cds/v1' / (name + '.schema.json')).read_text())
           for kind, name in zip(ORDER, ('physical', 'logical', 'projection'))}
REGISTRY = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in SCHEMAS.values())
Validator = type(contract_validator({}))
VALIDATORS = {kind: Validator(schema, registry=REGISTRY) for kind, schema in SCHEMAS.items()}


def pointer(*parts):
    return '/' + '/'.join(str(part).replace('~', '~0').replace('/', '~1') for part in parts)


class Rejected(ValueError):
    def __init__(self, code, at, family='definition-invalid'):
        self.issue = {'family': family, 'code': code, 'at': at}


def require(condition, code, at, family='definition-invalid'):
    if not condition:
        raise Rejected(code, at, family)


def parse_document(data, encoding, source_id):
    """Only intake classification; no dictionary error codes escape this boundary."""
    try:
        return parse_bytes(data, encoding, dictionary_document=False)
    except IntakeLimit:
        raise Rejected('CDS_READ_LIMIT', pointer('sources', source_id)) from None
    except (IntakeInvalid, ValueError, UnicodeError, RecursionError):
        raise Rejected('CDS_READ_SOURCE_INVALID', pointer('sources', source_id)) from None


def bound(value, at):
    require(isinstance(value, str) and len(value) <= 4096, 'CDS_READ_LIMIT', at)
    require(INTEGER.fullmatch(value), 'CDS_READ_PROFILE_UNSUPPORTED', at)
    return int(value)


def interval_only(constraints):
    return (set(constraints) <= {'minimum', 'maximum'}
            and all(isinstance(value, str) and len(value) <= 4096 and INTEGER.fullmatch(value)
                    for value in constraints.values()))


def physical_check(doc, at):
    require(doc['kind'] == 'table', 'CDS_READ_PROFILE_UNSUPPORTED', at + '/kind')
    columns = doc['columns']
    require(len(columns) <= 2048, 'CDS_READ_LIMIT', at + '/columns')
    names = [col['name'] for col in columns]
    ordinals = [col['ordinal'] for col in columns if 'ordinal' in col]
    require(len(set(names)) == len(names) and len(set(ordinals)) == len(ordinals),
            'CDS_READ_PHYSICAL_INVALID', at + '/columns')
    for col in columns:
        point = at + '/columns/' + str(names.index(col['name']))
        extent = col.get('integerRange', {})
        values = {key: bound(extent[key], point + '/integerRange/' + key)
                  for key in ('minimum', 'maximum') if key in extent}
        if 'minimum' in values and 'maximum' in values:
            require(values['minimum'] <= values['maximum'], 'CDS_READ_PHYSICAL_INVALID', point)
        if col.get('scalarType') in INTEGER_RANGES:
            lo, hi = INTEGER_RANGES[col['scalarType']]
            require(all(lo <= value <= hi for value in values.values()), 'CDS_READ_PHYSICAL_INVALID', point)
        geometry = col.get('decimalGeometry')
        if geometry:
            require(geometry['scale'] <= geometry['precision'], 'CDS_READ_PHYSICAL_INVALID', point)
    require(all(name in names for name in doc.get('primaryKey', [])), 'CDS_READ_PHYSICAL_INVALID', at)
    for index in doc.get('indexes', []):
        require(all(name in names for name in index['columns']), 'CDS_READ_PHYSICAL_INVALID', at)
    for key in doc.get('foreignKeys', []):
        require(all(name in names for name in key['columns'])
                and len(key['columns']) == len(key['target']['columns']), 'CDS_READ_PHYSICAL_INVALID', at)
    for key in ('indexes', 'foreignKeys'):
        names = [item['name'] for item in doc.get(key, [])]
        require(len(names) == len(set(names)), 'CDS_READ_PHYSICAL_INVALID', at + '/' + key)


def field(column, overlay, dictionary, at):
    result = {'name': column['name'], 'physical': deepcopy(column), 'compatibility': 'not-verified'}
    dtype = column.get('scalarType')
    intrinsic = {}
    if 'dictionary' in overlay:
        identity = overlay['dictionary']
        require(identity in dictionary, 'CDS_READ_REFERENCE_NOT_FOUND', at + '/dictionary')
        element = dictionary[identity]
        dtype = element['type']
        intrinsic = deepcopy(element.get('constraints', {}))
        result['dictionary'] = identity
        if 'enumValues' in element:
            result['enumValues'] = deepcopy(element['enumValues'])
    elif dtype in INTEGER_RANGES:
        # Without a logical binding, the base model is the observed physical domain itself.
        # This is not clipping an independently authored dictionary domain to make it fit.
        lo, hi = INTEGER_RANGES[dtype]
        for key, value in column.get('integerRange', {}).items():
            number = int(value)
            if number != (lo if key == 'minimum' else hi):
                intrinsic[key] = str(number)
    if dtype is not None:
        result.update(type=dtype, intrinsicConstraints=intrinsic, constraints=deepcopy(intrinsic))
    contextual = overlay.get('constraints', {})
    if 'constraints' in overlay:
        result['contextualConstraints'] = deepcopy(contextual)
    if contextual:
        require(dtype in INTEGER_RANGES and interval_only(intrinsic),
                'CDS_READ_PROFILE_UNSUPPORTED', at + '/constraints')
        require(set(contextual) <= {'minimum', 'maximum'},
                'CDS_READ_PROFILE_UNSUPPORTED', at + '/constraints')
    if dtype in INTEGER_RANGES and interval_only(intrinsic):
        lo, hi = INTEGER_RANGES[dtype]
        lo = max(lo, int(intrinsic.get('minimum', lo)))
        hi = min(hi, int(intrinsic.get('maximum', hi)))
        for key in ('minimum', 'maximum'):
            if key not in contextual:
                continue
            value = bound(contextual[key], at + '/constraints/' + key)
            require(value >= lo if key == 'minimum' else value <= hi,
                    'CDS_READ_CONSTRAINT_WEAKENING', at + '/constraints/' + key)
            if key == 'minimum':
                lo = value
            else:
                hi = value
            result['constraints'][key] = str(value)
        require(lo <= hi, 'CDS_READ_CONSTRAINT_CONTRADICTION', at + '/constraints')
        ptype = column.get('scalarType')
        if ptype in INTEGER_RANGES:
            plo, phi = INTEGER_RANGES[ptype]
            extent = column.get('integerRange', {})
            plo = max(plo, int(extent.get('minimum', plo)))
            phi = min(phi, int(extent.get('maximum', phi)))
            require(plo <= lo and hi <= phi, 'CDS_READ_DOMAIN_NOT_REPRESENTABLE', at,
                    'physical-incompatible')
            result['compatibility'] = 'compatible'
    for key in ('label', 'description', 'hint'):
        if key in overlay:
            result[key] = overlay[key]
    return result


def resolve(bundle, dictionary):
    """Resolve a complete supplied snapshot, never a global registry. Failure has no partial result."""
    try:
        require(sum(len(bundle[kind]) for kind in ORDER) <= 256, 'CDS_READ_LIMIT', '/')
        return _resolve(deepcopy(bundle), dictionary)
    except Rejected as failure:
        return {'valid': False, 'issues': [failure.issue]}


def _resolve(bundle, dictionary):
    indexes = {}
    for kind in ORDER:
        entries = {}
        for handle, doc in sorted(bundle[kind].items()):
            at = pointer(kind, handle)
            require(VALIDATORS[kind].is_valid(doc), 'CDS_READ_SCHEMA_INVALID', at)
            require(doc['id'] not in entries, 'CDS_READ_DUPLICATE_ID', at)
            entries[doc['id']] = (doc, at)
        indexes[kind] = entries
    for doc, at in indexes['physical'].values():
        physical_check(doc, at)
    models = {}
    for identity, (logical, at) in sorted(indexes['logical'].items()):
        require(logical['physical'] in indexes['physical'], 'CDS_READ_REFERENCE_NOT_FOUND', at + '/physical')
        physical = indexes['physical'][logical['physical']][0]
        columns = {col['name']: col for col in physical['columns']}
        require(set(logical['fields']) <= set(columns), 'CDS_READ_UNKNOWN_FIELD', at + '/fields')
        fields = [field(col, logical['fields'].get(name, {}), dictionary, at + '/fields/'
                        + name.replace('~', '~0').replace('/', '~1')) for name, col in sorted(columns.items())]
        models[identity] = {'id': identity, 'physical': physical, 'fields': fields}
    projected = {}

    def projection(identity, stack):
        doc, at = indexes['projections'][identity]
        require(identity not in stack, 'CDS_READ_REFERENCE_CYCLE', at + '/source')
        require(len(stack) < 64, 'CDS_READ_LIMIT', at + '/source')
        require(set(doc['operations']) <= {'LIST', 'GET'}, 'CDS_READ_OPERATION_UNSUPPORTED',
                at + '/operations', 'operation-not-allowed')
        source = doc['source']
        if 'entity' in source:
            require(source['entity'] in models, 'CDS_READ_REFERENCE_NOT_FOUND', at + '/source')
            entity = source['entity']
            fields = models[entity]['fields']
        else:
            require(source['projection'] in indexes['projections'], 'CDS_READ_REFERENCE_NOT_FOUND', at + '/source')
            parent = projection(source['projection'], stack + [identity])
            entity, fields = parent['entity'], parent['fields']
            require(set(doc['operations']) <= set(parent['operations']), 'CDS_READ_OPERATION_EXPANSION',
                    at + '/operations')
        available = {item['name']: item for item in fields}
        require(set(doc['fields']) <= set(available), 'CDS_READ_FIELD_NOT_EXPOSED', at + '/fields')
        selected = []
        for name in doc['fields']:
            public = {key: deepcopy(value) for key, value in available[name].items()
                      if key not in ('physical', 'intrinsicConstraints', 'contextualConstraints')}
            physical_col = available[name].get('physical')
            if physical_col is not None and 'nullable' in physical_col:
                public['nullable'] = physical_col['nullable']
            elif 'nullable' in available[name]:
                public['nullable'] = available[name]['nullable']
            selected.append(public)
        projected[identity] = {'id': identity, 'source': source, 'entity': entity,
                               'fields': selected, 'operations': doc['operations']}
        return projected[identity]

    for identity in sorted(indexes['projections']):
        projection(identity, [])
    return {'valid': True, 'issues': [], 'models': [models[key] for key in sorted(models)],
            'projections': [projected[key] for key in sorted(projected)]}


def load_dictionary(path):
    doc = parse_bytes((ROOT / path).read_bytes(), 'yaml' if path.endswith('.yaml') else 'json')
    # Fixture inputs must already satisfy DICT-001, whose semantic authority is unchanged.
    contract_validator(json.loads((ROOT / 'schemas/dictionary/v1/dictionary.schema.json').read_text())).validate(doc)
    return {element['id']: descriptor_projection(element) for element in doc['elements']}


def canonical(value):
    """JSON equality with exact numbers and distinct booleans; object order is irrelevant."""
    if value is None:
        return ('null',)
    if isinstance(value, bool):
        return ('boolean', value)
    if isinstance(value, (int, Decimal)):
        return ('number', value)
    if isinstance(value, str):
        return ('string', value)
    if isinstance(value, list):
        return ('array', tuple(canonical(item) for item in value))
    if isinstance(value, dict):
        return ('object', tuple(sorted((key, canonical(item)) for key, item in value.items())))
    raise AssertionError(f'Nonportable fixture number/value: {type(value).__name__}')


def check(path=ROOT / 'fixtures/cds/read/v1/cases.json'):
    suite = load_json(path)
    schema = json.loads((ROOT / 'schemas/cds/v1/read-result.schema.json').read_text())
    registry = REGISTRY.with_resource(schema['$id'], Resource.from_contents(schema))
    validator = Validator(schema, registry=registry)
    ids = set()
    for case in suite['cases']:
        assert case['id'] not in ids, case['id']
        ids.add(case['id'])
        actual = resolve(case['input'], load_dictionary(case['dictionary']))
        validator.validate(case['expected'])
        assert canonical(actual) == canonical(case['expected']), (case['id'], actual, case['expected'])
        validator.validate(actual)
    source_suite = load_json(ROOT / 'fixtures/cds/read/v1/source-cases.json')
    for case in source_suite['cases']:
        try:
            data = bytes.fromhex(case['bytesHex']) if 'bytesHex' in case else case['text'].encode('utf-8')
            model = parse_document(data, case['encoding'], 's')
        except Rejected as failure:
            assert failure.issue == case.get('expectedError'), (case['id'], failure.issue)
        else:
            assert 'expected' in case and canonical(model) == canonical(case['expected']), case['id']
    return len(ids)


if __name__ == '__main__':
    count = len(json.loads((ROOT / 'fixtures/cds/read/v1/source-cases.json').read_text())['cases'])
    print(f'PASS: {check()} CDS read resolution + {count} intake cases (PURE ONLY; no DB/native execution)')