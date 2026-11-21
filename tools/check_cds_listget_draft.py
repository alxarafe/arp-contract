#!/usr/bin/env python3
"""Bounded LIST/GET fixture oracle, not a SQL executor, scalar validator or permission system."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import check_cds_read_draft as cds
import integer_semantics as integers
import module_menu_profile as modules
from check_contract import contract_validator, descriptor_projection, load

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'fixtures/cds/listget/v1'
FAMILIES = {'definition-invalid', 'physical-incompatible', 'invalid-data',
            'operation-not-allowed', 'execution-failure'}


class InvalidKey(ValueError):
    pass


def integer(value, constraints):
    """Exact identity codec: capacity only; business constraints do not invalidate identity."""
    if not isinstance(value, str) or len(value) > 4096:
        raise InvalidKey()
    try:
        definition = integers.derive(constraints)
        number = integers.parse_lexeme(value)
    except integers.IntegerInvalid:
        raise InvalidKey() from None
    if not definition.domain_min <= number <= definition.domain_max:
        raise InvalidKey()
    return number


def binding(host, generation):
    return {key: deepcopy(host[key]) for key in ('target', 'projection', 'context')} | {'generation': generation}


def modular_catalog(assets, layout, state):
    """Reuse MODULES/MENUS registrations; substitute product payloads, never duplicate its resolver."""
    scenario = deepcopy(load(ROOT / 'fixtures/modules/v1/scenario.json'))
    definitions = layout['definitions']
    scenario['payloads'].update({
        'app-physical': deepcopy(next(iter(definitions['physical'].values()))),
        'catalog-dictionary': deepcopy(assets['dictionary']),
        'catalog-logical': deepcopy(next(iter(definitions['logical'].values()))),
        'catalog-projection': deepcopy(definitions['projections']['catalog']),
        'reports-projection': deepcopy(definitions['projections']['summary']),
    })
    targets = {'catalog.articles.public': 'products.catalog', 'reports.articles.summary': 'products.summary'}
    for name in ('app-menus', 'catalog-menus', 'reports-menus'):
        payload = scenario['payloads'][name]
        for group in payload.get('menus', []) + payload.get('contributions', []):
            for entry in group['entries']:
                destination = entry.get('destination', {})
                if destination.get('kind') == 'projection':
                    destination['target'] = targets.get(destination['target'], destination['target'])
    host = modules.case_host(scenario, state)
    host['projectionAccess'] = {targets.get(key, key): value for key, value in host['projectionAccess'].items()}
    snapshot = modules.activate(scenario, host)
    menus = modules.compose(snapshot, host.get('composition', scenario['composition']), host)
    snapshot['queryAccess'] = deepcopy(host['projectionAccess'])
    return snapshot, menus


def invoke(case, assets, defaults):
    """host/observed are private test evidence. Row grants and token evidence are host decisions."""
    host = deepcopy(defaults)
    host.update(deepcopy(case.get('host', {})))
    layout = deepcopy(assets['layouts'][case.get('layout', 'composite')])
    bundle = host.get('definitions', layout['definitions'])
    layout['definitions'] = bundle
    rows = host.get('rows', layout['rows'])
    request = case['request']
    observed = {'reads': 0, 'selectedRows': [], 'writes': 0}
    snapshot = None

    def finish(status, family=None, code=None, output=None):
        # The publication gate also covers empty GET results and unissued references.
        if status == 'success':
            if host.get('generationAtPublish', host['generation']) != host['generation']:
                status, family, code, output = 'failed', 'execution-failure', 'GENERATION_CHANGED', None
            elif snapshot is not None and 'moduleStateAtPublish' in host:
                current, menus = modular_catalog(assets, layout, host['moduleStateAtPublish'])
                if (not current['valid'] or not menus['valid']
                        or current['inputs'] != snapshot['inputs']):
                    status, family, code, output = 'failed', 'execution-failure', 'GENERATION_CHANGED', None
                elif any(request['operation'] not in current['queryAccess'].get(host['projection'], {}).get(key, [])
                         for key in ('available', 'authorized')):
                    status, family, code, output = 'rejected', 'operation-not-allowed', 'UNAVAILABLE', None
            if status == 'success' and (not host.get('authorizedAtPublish', True)
                  or host.get('contextAtPublish', host['context']) != host['context']):
                status, family, code, output = 'rejected', 'operation-not-allowed', 'UNAVAILABLE', None
        if status != 'success':
            observed['selectedRows'] = []
        response = {'status': status, 'diagnostics': []}
        if family:
            response['diagnostics'] = [{'family': family, 'code': 'CDS_LISTGET_' + code}]
        if output is not None:
            response['output'] = output
        return {'response': response, 'observed': observed}

    def reject(code, family='operation-not-allowed'):
        return finish('rejected', family, code)

    def failed(code):
        return finish('failed', 'execution-failure', code)

    if not isinstance(request, dict):
        return reject('INPUT_SHAPE', 'invalid-data')
    if (not host['authorized'] or not host['registered'] or request.get('target') != host['target']
            or request.get('operation') not in {'LIST', 'GET'}
            or request.get('operation') not in host['enabledOperations']
            or request.get('operation') not in host.get('authorizedOperations', host['enabledOperations'])):
        return reject('UNAVAILABLE')
    if set(request) != {'target', 'operation', 'inputs'} or not isinstance(request['inputs'], dict):
        return reject('INPUT_SHAPE', 'invalid-data')
    dictionary = {element['id']: descriptor_projection(element) for element in assets['dictionary']['elements']}
    if 'moduleState' in host:
        snapshot, menus = modular_catalog(assets, layout, host['moduleState'])
        if not snapshot['valid'] or not menus['valid']:
            return reject('INVALID_DEFINITION', 'definition-invalid')
        resolved = snapshot['cds']
        if host['projection'] not in {p['id'] for p in resolved['projections']}:
            return reject('UNAVAILABLE')
        access = snapshot['queryAccess'].get(host['projection'], {})
        if any(request['operation'] not in access.get(key, []) for key in ('available', 'authorized')):
            return reject('UNAVAILABLE')
    else:
        resolved = cds.resolve(bundle, dictionary)
    if not resolved['valid']:
        family = resolved['issues'][0]['family']
        code = {'physical-incompatible': 'INCOMPATIBLE_STORAGE', 'definition-invalid': 'INVALID_DEFINITION',
                'operation-not-allowed': 'CAPABILITY_UNAVAILABLE'}[family]
        return reject(code, family)
    projections = {projection['id']: projection for projection in resolved['projections']}
    projection = projections.get(host['projection'])
    if projection is None:
        return reject('INVALID_DEFINITION', 'definition-invalid')
    if (type(host['defaultLimit']) is not int or type(host['maxLimit']) is not int
            or not 1 <= host['defaultLimit'] <= host['maxLimit'] <= 100):
        return reject('INVALID_DEFINITION', 'definition-invalid')
    if request['operation'] not in projection['operations']:
        return reject('UNAVAILABLE')
    fields = [field['name'] for field in projection['fields']]
    if not set(fields) <= set(host['readableFields']):
        return reject('UNAVAILABLE')
    if not host['readCapability']:
        return reject('CAPABILITY_UNAVAILABLE')
    model = next(model for model in resolved['models'] if model['id'] == projection['entity'])
    effective = {field['name']: field for field in model['fields']}
    primary = model['physical'].get('primaryKey', [])
    if (not primary or any(effective[name].get('type') != 'INTEGER'
                           or effective[name]['physical'].get('nullable') is not False for name in primary)):
        return reject('CAPABILITY_UNAVAILABLE')
    generation = host['generation']
    if generation != host['currentGeneration']:
        return reject('GENERATION_EXPIRED')
    direct = set(primary) <= set(fields)
    inputs = request['inputs']
    after = None
    wanted = None
    limit = None

    def row_key(row):
        return tuple(integer(row['values'][name], effective[name]['constraints']) for name in primary)

    def evidence(token, collection):
        item = host[collection].get(token)
        if item is None or any(item.get(key) != value for key, value in binding(host, generation).items()
                               if key != 'generation'):
            return None, False
        return item, item.get('generation') != generation

    if request['operation'] == 'GET':
        key = inputs.get('key')
        if set(inputs) != {'key'} or not isinstance(key, dict):
            return reject('INVALID_KEY', 'invalid-data')
        if direct:
            if set(key) != {'components'} or not isinstance(key['components'], list):
                return reject('INVALID_KEY', 'invalid-data')
            components = key['components']
            if len(components) != len(primary):
                return reject('INVALID_KEY', 'invalid-data')
            try:
                wanted = []
                for name, component in zip(primary, components):
                    if (not isinstance(component, dict) or set(component) != {'field', 'type', 'value'}
                            or component['field'] != name or component['type'] != effective[name]['type']):
                        raise InvalidKey()
                    wanted.append(integer(component['value'], effective[name]['constraints']))
                wanted = tuple(wanted)
            except InvalidKey:
                return reject('INVALID_KEY', 'invalid-data')
        else:
            if (set(key) != {'reference'} or not isinstance(key['reference'], str)
                    or not 1 <= len(key['reference']) <= 128):
                return reject('INVALID_KEY', 'invalid-data')
            item, stale = evidence(key['reference'], 'references')
            if stale:
                return reject('GENERATION_EXPIRED')
            if item is None:
                return finish('success', output={'found': False})
            wanted = tuple(int(value) for value in item['key'])
    else:
        if set(inputs) - {'limit', 'continuation'}:
            return reject('INPUT_SHAPE', 'invalid-data')
        requested = inputs.get('limit', host['defaultLimit'])
        if (isinstance(requested, bool) or not isinstance(requested, (int, Decimal))
                or (isinstance(requested, Decimal) and not requested.is_finite())
                or not 1 <= requested <= 100 or requested != int(requested)):
            return reject('INPUT_SHAPE', 'invalid-data')
        limit = min(int(requested), host['maxLimit'])
        if 'continuation' in inputs:
            token = inputs['continuation']
            if not isinstance(token, str) or not 1 <= len(token) <= 128:
                return reject('INVALID_CURSOR', 'invalid-data')
            item, stale = evidence(token, 'continuations')
            if stale:
                return reject('GENERATION_EXPIRED')
            if item is None or item.get('limit') != limit:
                return reject('INVALID_CURSOR', 'invalid-data')
            after = tuple(int(value) for value in item['after'])
    observed['reads'] = 1
    if host.get('readFailure', False):
        return failed('READ_FAILED')
    # Precomputed host row decisions stand for a real restricted provider, not an ARP ACL expression language.
    accessible = [row for row in rows if row['id'] in host['allowedRows']]
    try:
        keys = [row_key(row) for row in accessible]
    except (InvalidKey, KeyError):
        return failed('ROW_DECODE_FAILED')
    if len(set(keys)) != len(keys):
        return failed('ROW_IDENTITY_INVALID')
    ordered = sorted(zip(keys, accessible), key=lambda pair: pair[0])
    if request['operation'] == 'GET':
        selected = [row for key, row in ordered if key == wanted]
        more = False
    else:
        remaining = [row for key, row in ordered if after is None or key > after]
        selected, more = remaining[:limit], len(remaining) > limit
    records = []
    for row in selected:
        values = row['values']
        if (row['id'] in host.get('decodeFailures', []) or any(name not in values for name in fields)
                or any(values[name] is None and effective[name]['physical'].get('nullable') is not True
                       for name in fields)):
            return failed('ROW_DECODE_FAILED')
        if direct:
            key = {'components': [{'field': name, 'type': effective[name]['type'],
                                   'value': str(value)} for name, value in zip(primary, row_key(row))]}
        else:
            token = host['referenceFor'].get(row['id'])
            item = host['references'].get(token)
            if (item is None or any(item.get(k) != v for k, v in binding(host, generation).items())
                    or tuple(map(int, item['key'])) != row_key(row)):
                return failed('READ_FAILED')
            key = {'reference': token}
        decoded = {name: deepcopy(values[name]) for name in fields}
        try:
            for name in fields:
                if effective[name].get('type') == 'INTEGER' and decoded[name] is not None:
                    number = integer(decoded[name], effective[name]['constraints'])
                    extent = effective[name]['physical'].get('integerRange', {})
                    if not int(extent.get('minimum', number)) <= number <= int(extent.get('maximum', number)):
                        raise InvalidKey()
                    decoded[name] = str(number)
        except InvalidKey:
            return failed('ROW_DECODE_FAILED')
        records.append({'key': key, 'values': decoded})
    next_token = None
    if more:
        last = selected[-1]
        next_token = host['cursorFor'].get(last['id'])
        item = host['continuations'].get(next_token)
        if (item is None or any(item.get(k) != v for k, v in binding(host, generation).items())
                or item.get('limit') != limit or tuple(map(int, item['after'])) != row_key(last)):
            return failed('READ_FAILED')
    observed['selectedRows'] = [row['id'] for row in selected]
    if request['operation'] == 'GET':
        output = {'found': bool(records)}
        if records:
            output['record'] = records[0]
    else:
        output = {'records': records, 'page': {'limit': limit, 'hasMore': more, 'next': next_token}}
    return finish('success', output=output)


def check():
    assets, vectors = load(FOLDER / 'products.json'), load(FOLDER / 'cases.json')
    schema = load(ROOT / 'schemas/cds/v1/listget-result.schema.json')
    validator = contract_validator(schema)
    validator.check_schema(schema)
    assert assets['feature'] == vectors['feature'] == 'ARP-CDS-LISTGET-001'
    assert assets['status'] == vectors['status'] == 'unreleased-draft'
    contract_validator(load(ROOT / 'schemas/dictionary/v1/dictionary.schema.json')).validate(assets['dictionary'])
    dictionary = {element['id']: descriptor_projection(element) for element in assets['dictionary']['elements']}
    assert len(dictionary) == len(assets['dictionary']['elements'])
    for layout in assets['layouts'].values():
        resolved = cds.resolve(layout['definitions'], dictionary)
        assert resolved['valid']
        model = resolved['models'][0]
        primary = model['physical']['primaryKey']
        types = {field['name']: field['constraints'] for field in model['fields']}
        keys = [tuple(integer(row['values'][name], types[name]) for name in primary) for row in layout['rows']]
        assert len(set(keys)) == len(keys)
        assert len({row['id'] for row in layout['rows']}) == len(layout['rows'])
    obligations = load(FOLDER / 'provider-obligations.json')
    assert obligations['feature'] == assets['feature'] and obligations['executed'] is False
    assert obligations['engines'] == {'dotnet': 'postgresql', 'java': 'postgresql', 'php': 'mariadb'}
    assert obligations['data'] == 'products.json'
    identities = [case['id'] for case in vectors['cases']]
    assert len(set(identities)) == len(identities)
    for case in vectors['cases']:
        before = deepcopy((case, assets, vectors['defaults']))
        actual = invoke(case, assets, vectors['defaults'])
        validator.validate(case['expected']['response'])
        validator.validate(actual['response'])
        assert cds.canonical(actual) == cds.canonical(case['expected']), case['id']
        assert before == (case, assets, vectors['defaults']), case['id']
        assert actual['observed']['writes'] == 0
    return len(identities)


if __name__ == '__main__':
    print(f'PASS: {check()} candidate LIST/GET vectors; no SQL or native conformance executed')