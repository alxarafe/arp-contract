"""Development-only portable intake checks, not an ARP catalog implementation.

JSON numbers stay int/Decimal. YAML is scanned/parsed as events, never constructed
as Python objects by tags. Profile limits are checked before shape validation.
"""
import json
import re
from decimal import Decimal
from pathlib import Path

import yaml

MAX_BYTES = 1048576
MAX_ELEMENTS = 2048
MAX_DEPTH = 128
MAX_NUMBER_CHARS = 256
MAX_EXPONENT = 128
NUMBER_MAGNITUDE = 10 ** 128
MAX_LENGTH = NUMBER_MAGNITUDE - 1
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z', re.ASCII)


class IntakeInvalid(ValueError):
    code = 'DICTIONARY_DOCUMENT_INVALID'


class IntakeLimit(ValueError):
    code = 'DICTIONARY_LIMIT_EXCEEDED'


def unique(pairs):
    result = {}
    for key, value in pairs:
        if not isinstance(key, str) or key in result:
            raise IntakeInvalid('mapping keys must be unique strings')
        result[key] = value
    return result


def unicode_scalars(value):
    if isinstance(value, str):
        value.encode('utf-8', errors='strict')
    elif isinstance(value, dict):
        for key, item in value.items():
            unicode_scalars(key)
            unicode_scalars(item)
    elif isinstance(value, list):
        for item in value:
            unicode_scalars(item)


def number(text):
    # JSON grammar is established before this budget; never parse a giant exponent.
    if len(text) > MAX_NUMBER_CHARS:
        raise IntakeLimit('numeric token length')
    parts = re.split('[eE]', text)
    if len(parts) == 2:
        exponent = parts[1].lstrip('+-').lstrip('0') or '0'
        if len(exponent) > 3 or int(exponent) > MAX_EXPONENT:
            raise IntakeLimit('numeric exponent')
    value = Decimal(text)
    if value.copy_abs() >= NUMBER_MAGNITUDE:
        raise IntakeLimit('numeric magnitude')
    return int(text) if '.' not in text and len(parts) == 1 else value


def _depth_json(text):
    # Iterative lexical scan before the recursive JSON decoder. Quotes/escapes
    # make brackets inside text harmless; malformed syntax remains decoder-owned.
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > MAX_DEPTH:
                raise IntakeLimit('collection depth')
        elif char in ']}':
            depth -= 1


def _yaml(text):
    if re.search(r'\r(?!\n)|[\x85\u2028\u2029]', text):
        raise IntakeInvalid('unsupported physical line separator')
    # Scan token styles before composition: YAML 1.1 implicit resolvers and
    # object constructors must not choose the portable data model.
    scalar_values = {}
    for token in yaml.scan(text):
        if isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken,
                              yaml.tokens.TagToken, yaml.tokens.DirectiveToken)):
            raise IntakeInvalid('forbidden YAML construct')
        if not isinstance(token, yaml.tokens.ScalarToken):
            continue
        raw = text[token.start_mark.index:token.end_mark.index]
        if token.style in ('|', '>'):
            header = re.split(r'\r\n|\r|\n', raw, maxsplit=1)[0]
            if not re.fullmatch(r'[|>][+-]?(?:[ \t]+(?:#.*)?)?', header):
                raise IntakeInvalid('unsupported block scalar header')
            value = token.value
        else:
            if '\n' in raw or '\r' in raw:
                raise IntakeInvalid('multiline flow/plain scalar')
            if token.style == '"':
                # Only JSON-compatible escapes. json.loads combines valid escaped
                # surrogate pairs; unicode_scalars rejects unpaired surrogates.
                value = json.loads(raw)
            elif token.style == "'":
                value = token.value
            else:
                value = token.value
                if value == 'null':
                    value = None
                elif value in ('true', 'false'):
                    value = value == 'true'
                elif NUMBER.fullmatch(value):
                    value = number(value)
        unicode_scalars(value)
        scalar_values[token.start_mark.index] = value
    # Events validate grammar without constructing a recursive object graph.
    events = []
    documents = depth = 0
    for event in yaml.parse(text, Loader=yaml.BaseLoader):
        if isinstance(event, yaml.events.DocumentStartEvent):
            documents += 1
        if isinstance(event, (yaml.events.MappingStartEvent, yaml.events.SequenceStartEvent)):
            depth += 1
            if depth > MAX_DEPTH:
                raise IntakeLimit('collection depth')
        if isinstance(event, (yaml.events.MappingEndEvent, yaml.events.SequenceEndEvent)):
            depth -= 1
        events.append(event)
    if documents != 1:
        raise IntakeInvalid('one YAML document required')
    # A tab in an indentation prefix is forbidden, but scalar content may contain
    # tabs after its space indentation. Token spans distinguish those positions.
    scalars = [e for e in events if isinstance(e, yaml.events.ScalarEvent)]
    span_index = offset = 0
    for line in text.splitlines(keepends=True):
        prefix = re.match(r'[ \t]*', line)[0]
        tab = prefix.find('\t')
        if tab >= 0:
            position = offset + tab
            while span_index < len(scalars) and scalars[span_index].end_mark.index <= position:
                span_index += 1
            if not (span_index < len(scalars) and scalars[span_index].start_mark.index <= position < scalars[span_index].end_mark.index):
                raise IntakeInvalid('tab indentation')
        offset += len(line)
    index = 0
    if not isinstance(events[index], yaml.events.StreamStartEvent):
        raise IntakeInvalid('stream')
    index += 1
    if not isinstance(events[index], yaml.events.DocumentStartEvent):
        raise IntakeInvalid('document')
    index += 1

    def node():
        nonlocal index
        event = events[index]
        index += 1
        if isinstance(event, yaml.events.ScalarEvent):
            return scalar_values.get(event.start_mark.index)  # omitted scalar => null
        if isinstance(event, yaml.events.SequenceStartEvent):
            items = []
            while not isinstance(events[index], yaml.events.SequenceEndEvent):
                items.append(node())
            index += 1
            return items
        if isinstance(event, yaml.events.MappingStartEvent):
            pairs = []
            while not isinstance(events[index], yaml.events.MappingEndEvent):
                key = node()
                if key == '<<':
                    raise IntakeInvalid('merge key')
                pairs.append((key, node()))
            index += 1
            return unique(pairs)
        raise IntakeInvalid('unsupported YAML node')

    model = node()
    if not isinstance(events[index], yaml.events.DocumentEndEvent) or not isinstance(events[index + 1], yaml.events.StreamEndEvent) or index + 2 != len(events):
        raise IntakeInvalid('trailing YAML input')
    return model


def parse_bytes(data, encoding):
    if len(data) > MAX_BYTES:
        raise IntakeLimit('document bytes')
    text = data.decode('utf-8', errors='strict')
    if encoding == 'json':
        _depth_json(text)
        model = json.loads(text, object_pairs_hook=unique, parse_int=number, parse_float=number,
                           parse_constant=lambda _: (_ for _ in ()).throw(IntakeInvalid('non-JSON number')))
    elif encoding == 'yaml':
        model = _yaml(text)
    else:
        raise IntakeInvalid('unknown encoding')
    unicode_scalars(model)
    if isinstance(model, dict) and isinstance(model.get('elements'), list) and len(model['elements']) > MAX_ELEMENTS:
        raise IntakeLimit('elements per source')
    return model


def parse_source(path: Path, encoding):
    return parse_bytes(path.read_bytes(), encoding)
