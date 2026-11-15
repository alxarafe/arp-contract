#!/usr/bin/env python3
"""CDS draft shared-fixture checker: bounded integer semantics, not a runtime.

This is a development-only oracle for proposed JSON test vectors. It does not
query databases, implement the dictionary's native validator, or guarantee CRUD.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGER_RANGES = {
    'INT8': (-128, 127), 'UINT8': (0, 255),
    'INT16': (-32768, 32767), 'UINT16': (0, 65535),
    'INT32': (-2147483648, 2147483647),
    'UINT32': (0, 4294967295),
    'INT64': (-9223372036854775808, 9223372036854775807),
}
INTEGER_LEXEME = re.compile(r'-?(?:0|[1-9][0-9]*)\Z', re.ASCII)


def load(path: Path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError(f'duplicate JSON key {k}')
            d[k] = v
        return d
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def _exact_bound(value):
    if not isinstance(value, str) or not INTEGER_LEXEME.fullmatch(value):
        raise ValueError(f'invalid integer bound: {value!r}')
    return Decimal(value)


def structural_status(case):
    """Determine containment for exact integer types only; else not-verified.

    Assumes normalized scalarType appears only with verified adapter evidence.
    """
    dtype = case['dictionaryType']
    phys = case['physical']
    if dtype not in INTEGER_RANGES:
        return 'not-verified'
    min_type, max_type = map(Decimal, INTEGER_RANGES[dtype])
    lo, hi = min_type, max_type
    intrinsic = case.get('intrinsicConstraints', {})
    contextual = case.get('contextualConstraints', {})
    if 'minimum' in intrinsic:
        bound = _exact_bound(intrinsic['minimum'])
        if bound < min_type or bound > max_type:
            return 'definition-invalid'
        lo = max(lo, bound)
    if 'maximum' in intrinsic:
        bound = _exact_bound(intrinsic['maximum'])
        if bound < min_type or bound > max_type:
            return 'definition-invalid'
        hi = min(hi, bound)
    if lo > hi:
        return 'definition-invalid'
    for key, value in contextual.items():
        if key not in ('minimum', 'maximum'):
            return 'not-verified'  # Unspecified constraints require a richer solver.
        bound = _exact_bound(value)
        if key == 'minimum':
            # Contextual constraint must not loosen the element's intrinsic range.
            if bound < lo:
                return 'definition-invalid'
            lo = bound
        else:
            if bound > hi:
                return 'definition-invalid'
            hi = bound
    if lo > hi:
        return 'definition-invalid'
    ptype = phys.get('scalarType')
    if ptype not in INTEGER_RANGES:
        return 'not-verified'
    plo, phi = map(Decimal, INTEGER_RANGES[ptype])
    if 'minimum' in phys:
        plo = max(plo, _exact_bound(phys['minimum']))
    if 'maximum' in phys:
        phi = min(phi, _exact_bound(phys['maximum']))
    if plo > phi:
        return 'incompatible'
    return 'compatible' if plo <= lo and hi <= phi else 'incompatible'


def valid_rating(value, minimum='0', maximum='10'):
    """Sample INT16 rating: exact lexical integer, no implicit coercions."""
    return (isinstance(value, str) and INTEGER_LEXEME.fullmatch(value) is not None
            and Decimal(minimum) <= Decimal(value) <= Decimal(maximum))


def audit(rows, complete):
    invalid = sum(not valid_rating(row['rating']) for row in rows)
    if invalid:
        status = 'nonconforming'
    elif complete:
        status = 'conformant'
    else:
        status = 'not-verified'
    return {'status':status, 'invalidCount':invalid}


def server_outcome(case):
    op = case['operation']
    data = case['input']
    # The contract never treats an included invalid field as an unchanged-field bypass.
    if op not in ('CREATE', 'UPDATE'):
        raise ValueError(f'Unsupported fixture operation: {op}')
    if 'rating' in data and not valid_rating(data['rating']):
        return {'status':'invalid-data', 'field':'rating'}
    if op == 'CREATE' and 'rating' not in data:
        raise ValueError('This demo requires rating on CREATE; generic presence is deferred')
    if op == 'UPDATE':
        persisted = {**case['original'], **data}
    else:
        persisted = dict(data)
    return {'status':'accepted', 'persisted':persisted}


def client_outcome(case):
    """Model field *selection*, not typing/composition DOM events."""
    original = case['original']
    current = dict(original)
    verdicts = []
    for attempt in case['attempts']:
        field, value = attempt['field'], attempt['value']
        if field == 'rating':
            accepted = valid_rating(value)
        elif field == 'code':
            accepted = isinstance(value,str) and bool(value)
        else:
            raise ValueError('Unknown field in client fixture')
        verdicts.append(accepted)
        if accepted:
            current[field] = value
    if case.get('cancelWholeEdit'):
        current = dict(original)
    patch = {k:v for k,v in current.items() if original.get(k) != v}
    return {'originalWarning':not valid_rating(original['rating']),
            'finalForm':current, 'patch':patch, 'acceptedAttempts':verdicts}



def create_client_outcome(case):
    """A new form has no grandfathered historical value."""
    current = dict(case['initialForm'])
    verdicts = []
    for attempt in case['attempts']:
        field, value = attempt['field'], attempt['value']
        if field == 'rating':
            accepted = valid_rating(value)
        elif field == 'code':
            accepted = isinstance(value, str) and bool(value)
        else:
            raise ValueError('Unknown new-form field')
        verdicts.append(accepted)
        if accepted:
            current[field] = value
    return {'finalForm':current,
            'canSubmit':valid_rating(current.get('rating')) and bool(current.get('code')),
            'acceptedAttempts':verdicts}


def check(root=ROOT):
    manifest = load(root / 'fixtures/cds/v1/manifest.json')
    assert manifest['compatibilityFixtures'] == 'fixtures/cds/v1/compatibility.json'
    assert manifest['historicalUpdateFixtures'] == 'fixtures/cds/v1/historical-updates.json'
    comp = load(root / manifest['compatibilityFixtures'])
    history = load(root / manifest['historicalUpdateFixtures'])
    assert comp['feature'] == history['feature'] == 'ARP-CDS-001'
    assert comp['status'] == history['status'] == 'unreleased-draft'
    assert history['allowedInclusive'] == ['0','10'] and history['nullable'] is False
    ids = []
    for c in comp['assertions']:
        ids.append(c['id'])
        actual = structural_status(c)
        assert actual == c['expected'], f"{c['id']}: {actual} != {c['expected']}"
    for c in history['serverCases']:
        ids.append(c['id'])
        actual = server_outcome(c)
        assert actual == c['expected'], f"{c['id']}: {actual} != {c['expected']}"
    for c in history['clientCases']:
        ids.append(c['id'])
        actual = client_outcome(c)
        expected = c['expected']
        assert actual['originalWarning'] == expected['originalWarning'], c['id']
        assert actual['finalForm'] == expected['finalForm'], c['id']
        assert actual['patch'] == expected['patch'], c['id']
        assert actual['acceptedAttempts'] == [a['accepted'] for a in c['attempts']], c['id']
    for c in history['createClientCases']:
        ids.append(c['id'])
        actual = create_client_outcome(c)
        assert actual['finalForm'] == c['expected']['finalForm'], c['id']
        assert actual['canSubmit'] == c['expected']['canSubmit'], c['id']
        assert actual['acceptedAttempts'] == [a['accepted'] for a in c['attempts']], c['id']
    for c in history['auditCases']:
        ids.append(c['id'])
        actual = audit(c['rows'], c['complete'])
        assert actual == c['expected'], f"{c['id']}: {actual} != {c['expected']}"
    assert len(ids) == len(set(ids)), 'Duplicate scenario identity'
    return {'structural':len(comp['assertions']), 'server':len(history['serverCases']),
            'client':len(history['clientCases']), 'createClient':len(history['createClientCases']), 'audit':len(history['auditCases'])}


if __name__ == '__main__':
    c = check()
    print('PASS: CDS compatibility/historical draft fixtures:', ', '.join(f'{k}={v}' for k,v in c.items()), '(STATIC ONLY)')
