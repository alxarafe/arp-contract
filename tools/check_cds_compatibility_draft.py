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
import integer_semantics as integer

ROOT = Path(__file__).resolve().parents[1]
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


def _physical_domain(physical):
    if physical.get('scalarType') != 'INTEGER':
        return None
    extent = physical.get('integerRange', {})
    try:
        lower = integer.parse_lexeme(extent['minimum']) if 'minimum' in extent else None
        upper = integer.parse_lexeme(extent['maximum']) if 'maximum' in extent else None
    except integer.IntegerInvalid as error:
        raise ValueError(f'invalid physical integerRange: {error}')
    if lower is not None and upper is not None and lower > upper:
        raise ValueError('physical integerRange is inverted')
    return lower, upper


def structural_status(case):
    """Determine containment for exact integer types only; else not-verified.

    Assumes normalized scalarType appears only with verified adapter evidence.
    """
    if case.get('dictionaryType', 'INTEGER') != 'INTEGER':
        return 'not-verified'
    try:
        base = integer.derive(case.get('dictionaryConstraints', {}))
    except integer.IntegerInvalid:
        return 'definition-invalid'
    if not integer.interval_only(case.get('dictionaryConstraints', {})):
        return 'not-verified'
    contextual = case.get('contextualConstraints', {})
    lo, hi = base.effective_min, base.effective_max
    if contextual:
        if not integer.interval_only(case.get('dictionaryConstraints', {})):
            return 'not-verified'
        if set(contextual) - {'minimum', 'maximum'}:
            return 'not-verified'
        try:
            if 'minimum' in contextual:
                bound = integer.parse_lexeme(contextual['minimum'])
                if bound < lo:
                    return 'definition-invalid'
                lo = bound
            if 'maximum' in contextual:
                bound = integer.parse_lexeme(contextual['maximum'])
                if bound > hi:
                    return 'definition-invalid'
                hi = bound
        except integer.IntegerInvalid:
            return 'definition-invalid'
        if lo > hi:
            return 'definition-invalid'
    physical = _physical_domain(case['physical'])
    if physical is None:
        return 'not-verified'
    physical_lower, physical_upper = physical
    if physical_lower is not None and lo < physical_lower:
        return 'incompatible'
    if physical_upper is not None and hi > physical_upper:
        return 'incompatible'
    return ('compatible' if physical_lower is not None and physical_upper is not None
            else 'not-verified')


def valid_rating(value, minimum='0', maximum='10'):
    """Sample INTEGER rating: exact lexical integer, no implicit coercions."""
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
    print('PASS: CDS compatibility/historical draft fixtures:',
          ', '.join(f'{k}={v}' for k, v in c.items()), '(STATIC ONLY)')