#!/usr/bin/env python3
"""Exact derivation and validation of the portable INTEGER scalar."""
import re
from dataclasses import dataclass
from decimal import Decimal

BITS = (8, 16, 32, 64)
LEXEME = re.compile(r'-?(?:0|[1-9][0-9]*)\Z', re.ASCII)
INTERVAL_KEYS = {'bits', 'signed', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum'}


class IntegerInvalid(ValueError):
    pass


class IntegerLimit(IntegerInvalid):
    pass


@dataclass(frozen=True)
class Definition:
    signed: bool
    bits: int
    domain_min: int
    domain_max: int
    declared_min: int | None
    declared_max: int | None
    exclusive_min: bool
    exclusive_max: bool
    multiple_of: int | None
    effective_min: int
    effective_max: int


def parse_lexeme(value):
    if isinstance(value, str) and len(value) > 4096:
        raise IntegerLimit('integer lexeme exceeds resource limit')
    if not isinstance(value, str) or not LEXEME.fullmatch(value):
        raise IntegerInvalid('not an exact decimal integer lexeme')
    return int(value)


def domain(signed, bits):
    if type(signed) is not bool:
        raise IntegerInvalid('signed must be boolean')
    if type(bits) is not int or bits not in BITS:
        raise IntegerInvalid('bits must be one of 8, 16, 32, 64')
    if signed:
        return -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    return 0, (1 << bits) - 1


def _flag(constraints, name):
    value = constraints.get(name, False)
    if type(value) is not bool:
        raise IntegerInvalid(f'{name} must be boolean')
    return value


def _bound(constraints, name):
    if name not in constraints:
        return None
    return parse_lexeme(constraints[name])


def _multiple_of(constraints):
    if 'multipleOf' not in constraints:
        return None
    value = parse_lexeme(constraints['multipleOf'])
    if value <= 0:
        raise IntegerInvalid('multipleOf must be a positive integer')
    return value


def derive(constraints):
    if not isinstance(constraints, dict):
        raise IntegerInvalid('constraints must be an object')
    if set(constraints) - (INTERVAL_KEYS | {'multipleOf'}):
        raise IntegerInvalid('unknown INTEGER constraint')
    bits = constraints.get('bits')
    if 'bits' in constraints and (type(bits) not in (int, Decimal) or bits not in BITS):
        raise IntegerInvalid('bits must be one of 8, 16, 32, 64')
    if bits is not None:
        bits = int(bits)
    signed = constraints.get('signed')
    if 'signed' in constraints and type(signed) is not bool:
        raise IntegerInvalid('signed must be boolean')
    declared_min = _bound(constraints, 'minimum')
    declared_max = _bound(constraints, 'maximum')
    exclusive_min = _flag(constraints, 'exclusiveMinimum')
    exclusive_max = _flag(constraints, 'exclusiveMaximum')
    if exclusive_min and declared_min is None:
        raise IntegerInvalid('exclusiveMinimum requires minimum')
    if exclusive_max and declared_max is None:
        raise IntegerInvalid('exclusiveMaximum requires maximum')
    multiple_of = _multiple_of(constraints)
    if signed is None:
        signed = not (declared_min is not None and declared_min >= 0)
    bounds = [v for v in (declared_min, declared_max) if v is not None]
    if declared_min is not None and declared_max is not None and declared_min > declared_max:
        raise IntegerInvalid('minimum exceeds maximum')
    if bits is None:
        candidates = BITS if len(bounds) == 2 else (32, 64)
        for candidate in candidates:
            low, high = domain(signed, candidate)
            if all(low <= value <= high for value in bounds):
                bits = candidate
                break
        else:
            raise IntegerInvalid('declared bounds do not fit any capacity')
    domain_min, domain_max = domain(signed, bits)
    if not all(domain_min <= value <= domain_max for value in bounds):
        raise IntegerInvalid('declared bound is outside the representable domain')
    effective_min = domain_min
    if declared_min is not None:
        effective_min = max(domain_min, declared_min + (1 if exclusive_min else 0))
    effective_max = domain_max
    if declared_max is not None:
        effective_max = min(domain_max, declared_max - (1 if exclusive_max else 0))
    if effective_min > effective_max:
        raise IntegerInvalid('effective interval is empty')
    if multiple_of is not None and -(-effective_min // multiple_of) * multiple_of > effective_max:
        raise IntegerInvalid('effective interval contains no multipleOf value')
    return Definition(signed, bits, domain_min, domain_max, declared_min, declared_max,
                      exclusive_min, exclusive_max, multiple_of, effective_min, effective_max)


def interval_only(constraints):
    return isinstance(constraints, dict) and set(constraints) <= INTERVAL_KEYS


def issues(value, constraints, element_id=None):
    try:
        definition = derive(constraints)
    except IntegerLimit:
        return [{'code': 'DICTIONARY_LIMIT_EXCEEDED', 'elementId': element_id}]
    except IntegerInvalid:
        return [{'code': 'DICTIONARY_ELEMENT_INVALID', 'elementId': element_id}]
    if isinstance(value, str) and len(value) > 4096:
        return [{'code': 'DICTIONARY_LIMIT_EXCEEDED', 'elementId': element_id}]
    if not isinstance(value, str) or not LEXEME.fullmatch(value):
        return [{'code': 'DICTIONARY_VALUE_TYPE', 'elementId': element_id}]
    number = int(value)
    found = []
    if number < definition.domain_min or number > definition.domain_max:
        found.append('typeRange')
    if definition.declared_min is not None and (
            number < definition.declared_min
            or definition.exclusive_min and number == definition.declared_min):
        found.append('minimum')
    if definition.declared_max is not None and (
            number > definition.declared_max
            or definition.exclusive_max and number == definition.declared_max):
        found.append('maximum')
    if definition.multiple_of is not None and number % definition.multiple_of != 0:
        found.append('multipleOf')
    return [{'code': 'DICTIONARY_VALUE_CONSTRAINT', 'elementId': element_id, 'constraint': name}
            for name in found]


def normalized(value):
    return str(parse_lexeme(value))