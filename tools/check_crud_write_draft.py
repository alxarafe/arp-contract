#!/usr/bin/env python3
"""Finite ARP-CRUD-001A oracle. Trusted evidence and atomic boundaries are simulated, never SQL."""
from copy import deepcopy
import hashlib
from pathlib import Path

import check_cds_draft as demo
import check_cds_read_draft as cds
import check_cds_listget_draft as reads
import check_services_draft as updates
import check_service_invocation_draft as services
from check_contract import contract_validator, load
from source_profile import IntakeInvalid, IntakeLimit, parse_bytes, unicode_scalars

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'fixtures/crud/write/v1'


def assets(engine='mariadb', host=None):
    """Reuse demo definitions and existing resolvers; no second authoring format."""
    host = host or {}
    manifest = load(ROOT / 'fixtures/cds/v1/manifest.json')
    docs = {name: demo.source(ROOT / path) for name, path in manifest['examples'].items()}
    physical = demo.source(ROOT / manifest['physicalObservations'][engine])
    for column in physical['columns']:
        column.update(deepcopy(host.get('columnOverrides', {}).get(column['name'], {})))
    physical['columns'].extend(deepcopy(host.get('additionalColumns', [])))
    if 'physicalKind' in host:
        physical['kind'] = host['physicalKind']
    for kind, doc in (('physical', physical), ('logical', docs['logical']),
                      ('projection', docs['public']), ('projection', docs['summary'])):
        demo.validate_document(load(ROOT / manifest['schemas'][kind]), doc)
    contract_validator(load(ROOT / 'schemas/dictionary/v1/dictionary.schema.json')).validate(docs['dictionary'])
    demo.resolve(physical, docs['logical'], docs['dictionary'], docs['public'], docs['summary'])
    if host.get('mode') != 'delegated' or physical['kind'] == 'table':
        cds.physical_check(physical, '/physical')
    dictionary = {element['id']: element for element in docs['dictionary']['elements']}
    fields = {column['name']: cds.field(column, docs['logical']['fields'].get(column['name'], {}),
                                      dictionary, '/fields/' + column['name'])
              for column in physical['columns']}
    for name, field in fields.items():
        if field.get('type') == 'STRING':
            physical_length = field['physical'].get('characterLength', {})
            logical_maximum = field.get('constraints', {}).get('maximumLength')
            if (physical_length.get('unit') == 'CHARACTERS' and logical_maximum is not None
                    and logical_maximum > physical_length['value']):
                raise cds.Rejected('CDS_READ_DOMAIN_NOT_REPRESENTABLE', '/fields/' + name,
                                   'physical-incompatible')
    projection = next((docs[name] for name in ('public', 'summary')
                       if docs[name]['id'] == host.get('projection', 'demo.items.public')), None)
    return physical, fields, projection


def value(field, candidate, *, historical=False):
    """Only the demo integer/text slice; integer grammar/ranges come from LIST/GET."""
    physical = field['physical']
    if candidate is None:
        if physical.get('nullable') is not True:
            raise ValueError('null')
        return None
    kind = field.get('type')
    if kind in cds.INTEGER_RANGES:
        number = reads.integer(candidate, kind)
        extent = physical.get('integerRange', {})
        if not int(extent.get('minimum', number)) <= number <= int(extent.get('maximum', number)):
            raise ValueError('physical range')
        if not historical:
            limits = field.get('constraints', {})
            if not int(limits.get('minimum', number)) <= number <= int(limits.get('maximum', number)):
                raise ValueError('logical range')
        return str(number)
    if kind not in {'STRING', 'TEXT'} or not isinstance(candidate, str):
        raise ValueError('unsupported scalar')
    unicode_scalars(candidate)
    if not historical:
        constraints = field.get('constraints', {})
        if not (constraints.get('minimumLength', 0) <= len(candidate)
                <= constraints.get('maximumLength', len(candidate))):
            raise ValueError('logical length')
    extent = physical.get('characterLength', {})
    if extent and (extent.get('unit') != 'CHARACTERS' or len(candidate) > extent['value']):
        raise ValueError('physical length')
    return candidate


def key_value(key, fields, primary):
    if not isinstance(key, dict) or set(key) != {'components'} or not isinstance(key['components'], list):
        raise ValueError('key shape')
    components = key['components']
    if len(components) != len(primary):
        raise ValueError('key arity')
    canonical = []
    for name, component in zip(primary, components):
        if (not isinstance(component, dict) or set(component) != {'field', 'type', 'value'}
                or component['field'] != name or component['type'] != fields[name]['type']):
            raise ValueError('key component')
        canonical.append({'field': name, 'type': fields[name]['type'],
                          'value': str(reads.integer(component['value'], fields[name]['type']))})
    return {'components': canonical}


def invoke(case, defaults=None):
    """request is untrusted; host and observed are private instrumentation, never response fields."""
    host = deepcopy(defaults or {})
    host.update(deepcopy(case.get('host', {})))
    rows = deepcopy(host.get('rowsAtBoundary', host.get('rows', [])))
    observed = {'persisted': rows, 'writtenFields': [], 'writes': 0, 'effects': 0,
                'dispatches': 0, 'certainty': 'not-started'}
    request = case.get('request')

    def publication_allowed():
        return (host.get('authorizedAtPublish', True)
                and host.get('contextAtPublish', host.get('context')) == host.get('context')
                and host.get('generationAtPublish', host.get('generation')) == host.get('generation')
                and host.get('accessRevisionAtPublish', host.get('accessRevision')) == host.get('accessRevision'))

    def finish(status, family=None, code=None, output=None, **extra):
        readable_output = (not output or 'key' not in output or
                           all(component['field'] in host.get('readableFieldsAtPublish', ['id'])
                               for component in output['key'].get('components', [])))
        if status == 'success' and (not publication_allowed() or not readable_output):
            if observed['writes'] or observed['dispatches']:
                status, family, code = 'failed', 'execution-failure', 'RESPONSE_UNAVAILABLE'
            else:
                status, family, code = 'rejected', 'operation-not-allowed', 'UNAVAILABLE'
            output, extra = None, {}
        response = {'status': status, 'diagnostics': []}
        if family:
            response['diagnostics'] = [{'family': family, 'code': code}]
        if output is not None:
            response['output'] = output
        response.update(extra)
        return {'response': response, 'observed': observed}

    def reject(code, family='operation-not-allowed'):
        return finish('rejected', family, code)

    if not isinstance(request, dict):
        return reject('INPUT_SHAPE', 'invalid-data')
    operation = request.get('operation')
    if (not host.get('authorized', True) or not host.get('registered', True)
            or not host.get('active', True) or request.get('target') != 'demo.items'
            or not isinstance(operation, str) or operation not in {'CREATE', 'UPDATE', 'DELETE'}
            or operation not in host.get('authorizedOperations', ['CREATE', 'UPDATE', 'DELETE'])):
        return reject('UNAVAILABLE')
    if set(request) != {'target', 'operation', 'inputs'} or not isinstance(request['inputs'], dict):
        return reject('INPUT_SHAPE', 'invalid-data')
    try:
        physical, fields, projection = assets(host.get('engine', 'mariadb'), host)
    except cds.Rejected as error:
        if error.issue['code'] == 'CDS_READ_PROFILE_UNSUPPORTED':
            return reject('CAPABILITY_UNAVAILABLE')
        family = error.issue['family']
        return reject('INCOMPATIBLE_STORAGE' if family == 'physical-incompatible' else 'INVALID_DEFINITION', family)
    except demo.DraftInvalid as error:
        if str(error).startswith('physical-incompatible'):
            return reject('INCOMPATIBLE_STORAGE', 'physical-incompatible')
        return reject('INVALID_DEFINITION', 'definition-invalid')
    except (AssertionError, ValueError):
        return reject('INVALID_DEFINITION', 'definition-invalid')
    if projection is None or operation not in projection['operations']:
        return reject('UNAVAILABLE')
    exposed = set(projection['fields'])
    readable = set(host.get('readableFields', projection['fields'])) & exposed
    readable &= set(host.get('readableFieldsAtBoundary', readable))
    writable = set(host.get('writableFields', projection['fields'])) & exposed
    writable &= set(host.get('writableFieldsAtBoundary', writable))
    if (not host.get('authorizedAtBoundary', True)
            or host.get('contextAtBoundary', host.get('context')) != host.get('context')
            or host.get('accessRevisionAtBoundary', host.get('accessRevision')) != host.get('accessRevision')):
        return reject('UNAVAILABLE')
    if host.get('generationAtBoundary', host.get('generation')) != host.get('generation'):
        return reject('GENERATION_EXPIRED')
    inputs = request['inputs']
    primary = physical.get('primaryKey', [])
    if not primary or any(fields[name].get('type') not in cds.INTEGER_RANGES
                          or fields[name]['physical'].get('nullable') is not False for name in primary):
        return reject('CAPABILITY_UNAVAILABLE')
    if operation != 'CREATE':
        key = inputs.get('key')
        if not set(primary) <= readable:
            if not isinstance(key, dict) or set(key) != {'reference'} or not isinstance(key['reference'], str):
                return reject('INVALID_KEY', 'invalid-data')
            evidence = host.get('keyReferences', {}).get(key['reference'])
            binding = {'purpose': operation, 'target': request['target'], 'projection': projection['id'],
                       'context': host.get('context'), 'generation': host.get('generation'),
                       'accessRevision': host.get('accessRevision')}
            if not evidence or evidence.get('binding') != binding or not evidence.get('active', True):
                return reject('UNAVAILABLE')
            key = evidence['key']
        try:
            key = key_value(key, fields, primary)
        except (ValueError, KeyError, TypeError):
            return reject('INVALID_KEY', 'invalid-data')
    if host.get('mode', 'managed') == 'delegated':
        # A separate registered demonstration handler, not an automatic fallback or managed guarantee.
        if (not host.get('handlerRegistered', False) or not host.get('recordAccessible', True)
                or operation != 'DELETE'
                or set(inputs) != {'key'}):
            return reject('UNAVAILABLE')
        if host.get('ruleReject', False):
            return reject('BUSINESS_REJECTED', 'invalid-data')
        observed['dispatches'] = 1
        observed['effects'] = host.get('handlerEffects', 0)
        observed['certainty'] = 'unknown'
        if host.get('handlerFailure', False):
            return finish('failed', 'execution-failure', 'HANDLER_FAILED')
        return finish('success', output={'accepted': True})
    if host.get('mode', 'managed') != 'managed':
        return reject('CAPABILITY_UNAVAILABLE')
    if host.get('capacity') == 'incompatible':
        return reject('INCOMPATIBLE_STORAGE', 'physical-incompatible')
    if (host.get('capacity') != 'verified' or physical['kind'] != 'table'
            or not host.get('atomicBoundary', False) or not host.get('effectsCharacterized', False)
            or not host.get('singleRowEffects', False)
            or not host.get('ruleDependenciesProtected', True)
            or not host.get('constraintsVerified', False)
            or (host.get('ruleRequired', False) and not host.get('ruleAvailable', False))):
        return reject('CAPABILITY_UNAVAILABLE')
    if any('nullable' not in field['physical'] or field.get('type') not in
           set(cds.INTEGER_RANGES) | {'STRING', 'TEXT'} for field in fields.values()):
        return reject('CAPABILITY_UNAVAILABLE')
    if any(field.get('type') == 'STRING' and field['physical'].get('characterLength', {}).get('unit')
           != 'CHARACTERS' for field in fields.values()):
        return reject('CAPABILITY_UNAVAILABLE')

    if operation in {'CREATE', 'UPDATE'} and not host.get('candidateAuthorized', True):
        return reject('UNAVAILABLE')

    if operation == 'CREATE':
        if set(inputs) != {'values'} or not isinstance(inputs['values'], dict):
            return reject('INPUT_SHAPE', 'invalid-data')
        supplied = inputs['values']
        if not set(supplied) <= writable:
            return reject('UNAVAILABLE')
        candidate = {}
        for name, field in fields.items():
            if name in supplied:
                raw = supplied[name]
            else:
                default = host.get('verifiedDefaults', {}).get(name)
                if default and default.get('verified') is True:
                    raw = default['value']
                elif field['physical'].get('nullable') is True:
                    raw = None
                else:
                    return reject('REQUIRED_VALUE', 'invalid-data')
            # Explicit demo identity is required, even if a host supplied a synthetic default.
            if name in primary and name not in supplied:
                return reject('REQUIRED_VALUE', 'invalid-data')
            try:
                candidate[name] = value(field, raw)
            except (ValueError, TypeError, UnicodeError):
                return reject('INVALID_VALUE', 'invalid-data')
        if not set(primary) <= readable:
            return reject('CAPABILITY_UNAVAILABLE')
        if any(all(row.get(name) == candidate[name] for name in primary) for row in rows):
            return reject('CONSTRAINT_REJECTED', 'invalid-data')
        if host.get('ruleReject', False):
            return reject('BUSINESS_REJECTED', 'invalid-data')
        proposed_rows = rows + [candidate]
        written = sorted(candidate)
        output = {'created': True, 'key': {'components': [
            {'field': name, 'type': fields[name]['type'], 'value': candidate[name]} for name in primary]}}
    else:
        matches = [index for index, row in enumerate(rows) if all(
            row.get(component['field']) == component['value'] for component in key['components'])]
        if len(matches) > 1:
            return finish('failed', 'execution-failure', 'ROW_IDENTITY_INVALID')
        if operation == 'DELETE':
            if set(inputs) != {'key', 'precondition'} or not isinstance(inputs['precondition'], dict):
                return reject('PRECONDITION_REQUIRED', 'invalid-data')
            reference = inputs['precondition']
            if set(reference) != {'reference'} or not isinstance(reference['reference'], str):
                return reject('PRECONDITION_REQUIRED', 'invalid-data')
            evidence = host.get('preconditions', {}).get(reference['reference'])
            binding = {'purpose': 'DELETE', 'target': request['target'], 'projection': projection['id'],
                       'key': key, 'context': host.get('context'), 'generation': host.get('generation'),
                       'accessRevision': host.get('accessRevision')}
            if not evidence or evidence.get('binding') != binding or not evidence.get('active', True):
                return reject('UNAVAILABLE')
            if not matches or not host.get('recordAccessible', True):
                return finish('success', output={'deleted': False})
            state = evidence.get('state', {})
            if set(state) != set(fields) - set(primary):
                return reject('PRECONDITION_REQUIRED', 'invalid-data')
            current = rows[matches[0]]
            try:
                current_state = {name: value(fields[name], current[name], historical=True) for name in state}
                expected_state = {name: value(fields[name], state[name], historical=True) for name in state}
            except (ValueError, KeyError, TypeError, UnicodeError):
                return finish('failed', 'execution-failure', 'ROW_DECODE_FAILED')
            if current_state != expected_state:
                return finish('conflict', conflictCode='CONCURRENT_CHANGE')
            if host.get('ruleReject', False):
                return reject('BUSINESS_REJECTED', 'invalid-data')
            proposed_rows = [row for index, row in enumerate(rows) if index != matches[0]]
            written = []
            output = {'deleted': True}
        else:
            if (set(inputs) - {'key', 'changes', 'baseline', 'confirmation'}
                    or not isinstance(inputs.get('changes'), dict) or not isinstance(inputs.get('baseline'), dict)):
                return reject('INPUT_SHAPE', 'invalid-data')
            if not matches or not host.get('recordAccessible', True):
                return reject('UNAVAILABLE')
            changes = inputs['changes']
            if not set(changes) <= writable or set(changes) & set(primary):
                return reject('UNAVAILABLE')
            try:
                for name, proposed in changes.items():
                    value(fields[name], proposed)
            except (ValueError, TypeError, UnicodeError):
                return reject('INVALID_VALUE', 'invalid-data')
            # Delegate concurrency/confirmation/no-op to SERVICES-002 and its SERVICES-001 oracle.
            legacy_inputs = deepcopy(inputs)
            legacy_inputs['key'] = 'item-1'
            legacy_inputs['changes'] = {name: value(fields[name], proposed) for name, proposed in changes.items()}
            try:
                legacy_inputs['baseline'] = {
                    name: value(fields[name], original, historical=True)
                    for name, original in inputs['baseline'].items() if name in changes}
            except (ValueError, TypeError, UnicodeError):
                return reject('INVALID_VALUE', 'invalid-data')
            legacy_host = {name: deepcopy(host[name]) for name in (
                'context', 'readableFields', 'confirmationEvidence') if name in host}
            legacy_host.update(readableFields=sorted(readable),
                               current={name: rows[matches[0]][name] for name in ('code', 'rating')},
                               exposedFields=sorted(exposed - set(primary)),
                               writableFields=sorted(writable - set(primary)),
                               dependentRuleReject=host.get('ruleReject', False))
            evidence = legacy_host.get('confirmationEvidence')
            if 'confirmation' in inputs and evidence:
                original_binding = {'target': request['target'], 'operation': 'UPDATE',
                                    'key': inputs['key'], 'changes': changes, 'baseline': inputs['baseline'],
                                    'context': host.get('context', {})}
                if evidence.get('binding') != original_binding:
                    return reject('INVALID_CONFIRMATION', 'invalid-data')
            if evidence and evidence['binding'].get('changes') == inputs['changes']:
                evidence['binding']['changes'] = deepcopy(legacy_inputs['changes'])
            if evidence and evidence['binding'].get('baseline') == inputs['baseline']:
                evidence['binding']['baseline'] = deepcopy(legacy_inputs['baseline'])
            if evidence and evidence['binding'].get('key') == inputs['key']:
                evidence['binding']['key'] = 'item-1'
            result = services.invoke({'request': {'target': request['target'], 'operation': 'UPDATE',
                                                  'inputs': legacy_inputs}, 'host': legacy_host})
            if result['response']['status'] != 'success':
                visible = set(host.get('readableFieldsAtPublish', readable))
                if (not publication_allowed() or any(item['field'] not in visible
                        for item in result['response'].get('conflicts', []))):
                    return reject('UNAVAILABLE')
                return {'response': result['response'], 'observed': observed}
            if not result['response']['output']['changed']:
                return finish('success', output={'changed': False})
            proposed_rows = deepcopy(rows)
            proposed_rows[matches[0]].update(result['observed']['persisted'])
            written = result['observed']['writtenFields']
            output = {'changed': True}
    if host.get('constraintReject', False):
        observed['certainty'] = 'rolled-back'
        return reject('CONSTRAINT_REJECTED', 'invalid-data')
    failure = host.get('persistenceFailure')
    if failure in {'before-commit', 'commit-rolled-back', 'rollback-unproven', 'commit-unknown'}:
        if failure in {'before-commit', 'commit-rolled-back'}:
            observed['certainty'] = 'rolled-back'
            code = 'PERSISTENCE_FAILED' if failure == 'before-commit' else 'COMMIT_FAILED'
        else:
            observed['certainty'] = 'unknown'
            code = 'OUTCOME_UNKNOWN'
            if host.get('unknownCommitted', False):
                observed.update(persisted=proposed_rows, writtenFields=written, writes=1, effects=1)
        return finish('failed', 'execution-failure', code)
    observed.update(persisted=proposed_rows, writtenFields=written, writes=1, effects=1, certainty='committed')
    return finish('success', output=output)


def decode(raw):
    return parse_bytes(raw.encode('utf-8'), 'json', dictionary_document=False)


def codec(case):
    try:
        decoded = decode(case['raw'])
        if not isinstance(decoded, dict) or set(decoded) != {'value'}:
            raise ValueError('codec shape')
        candidate = decoded['value']
        kind = case['type']
        if candidate is None and case.get('nullable', False):
            canonical = None
        elif kind in cds.INTEGER_RANGES:
            canonical = str(reads.integer(candidate, kind))
        elif kind in {'STRING', 'TEXT'} and isinstance(candidate, str):
            unicode_scalars(candidate)
            canonical = candidate
        else:
            raise ValueError('codec type')
        return {'valid': True, 'value': canonical}
    except (ValueError, UnicodeError, IntakeInvalid, IntakeLimit):
        return {'valid': False}


def check():
    manifest = load(FOLDER / 'manifest.json')
    fixtures = load(FOLDER / manifest['cases'])
    assert manifest['feature'] == 'ARP-CRUD-001A' and manifest['status'] == 'unreleased-draft'
    ids = set()
    for case in fixtures['cases']:
        assert case['id'] not in ids, case['id']
        ids.add(case['id'])
        before = deepcopy(case)
        result = invoke(case, fixtures['defaults'])
        assert result == case['expected'], f"{case['id']}: {result} != {case['expected']}"
        assert case == before, case['id']
        assert all(item['family'] in services.FAMILIES for item in result['response']['diagnostics'])
        if result['response']['status'] in {'rejected', 'conflict'}:
            assert result['observed']['writes'] == 0 and result['observed']['effects'] == 0
    obligations = load(FOLDER / manifest['providerObligations'])
    assert obligations['executed'] is False
    for requirement in obligations['requirements']:
        assert set(requirement['oracleCases']) <= ids, requirement['id']
    for case in load(FOLDER / manifest['codec']):
        assert codec(case) == case['expected'], case['id']
    for reuse in manifest['reuse']:
        assert hashlib.sha256((ROOT / reuse['path']).read_bytes()).hexdigest() == reuse['sha256']
        historical = updates.load(ROOT / reuse['path'])
        cases = {case['id']: case for case in historical['cases']}
        for identity in reuse['cases']:
            case = cases[identity]
            oracle = services.invoke if reuse['feature'] == 'ARP-SERVICES-002' else updates.outcome
            assert oracle(case) == case['expected'], identity
    return len(ids)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Run the oracle without -O; expectations require assertions')
    print(f'PASS: {check()} ARP-CRUD-001A vectors and referenced UPDATE vectors (MEMORY ONLY; no SQL/runtime)')