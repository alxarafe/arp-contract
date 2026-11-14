"""Development-only ARP pattern grammar checker and fixture matcher.

No host regex engine, source intake, catalog runtime or production API.
"""
import string


class PatternInvalid(ValueError):
    pass


class PatternLimit(ValueError):
    pass


def parse(pattern):
    if len(pattern) > 512:
        raise PatternLimit('pattern exceeds 512 characters')
    if not pattern or any(not 0x20 <= ord(c) <= 0x7e for c in pattern):
        raise PatternInvalid('nonempty printable ASCII required')
    i = 0
    end = len(pattern)
    if pattern.startswith('^'):
        i += 1
    # Only an unescaped final dollar is an anchor.
    slashes = 0
    for c in reversed(pattern[:-1]):
        if c != '\\': break
        slashes += 1
    if pattern.endswith('$') and slashes % 2 == 0:
        end -= 1
    atoms = []

    def escaped():
        nonlocal i
        i += 1
        if i >= end or pattern[i] not in string.punctuation:
            raise PatternInvalid('escape must precede ASCII punctuation')
        c = pattern[i]
        i += 1
        return c

    while i < end:
        c = pattern[i]
        if c == '\\':
            chars = {escaped()}
        elif c == '[':
            i += 1
            tokens = []
            while i < end and pattern[i] != ']':
                if pattern[i] == '\\': tokens.append((escaped(), False))
                else:
                    c = pattern[i]
                    if c in '[^': raise PatternInvalid('invalid class literal')
                    tokens.append((c, c == '-'))
                    i += 1
            if i >= end or not tokens:
                raise PatternInvalid('empty or unterminated class')
            i += 1
            chars = set()
            # Raw edge hyphens are literals; escaped hyphens are ordinary chars.
            if tokens and tokens[0][1]: chars.add(tokens.pop(0)[0])
            if tokens and tokens[-1][1]: chars.add(tokens.pop()[0])
            j = 0
            while j < len(tokens):
                lo, raw = tokens[j]
                if raw: raise PatternInvalid('misplaced hyphen')
                if j + 1 < len(tokens) and tokens[j + 1][1]:
                    if j + 2 >= len(tokens) or tokens[j + 2][1]:
                        raise PatternInvalid('missing range endpoint')
                    hi = tokens[j + 2][0]
                    if ord(lo) > ord(hi): raise PatternInvalid('reversed range')
                    chars.update(chr(n) for n in range(ord(lo), ord(hi) + 1))
                    j += 3
                else:
                    chars.add(lo)
                    j += 1
        elif c in r'.^$*+?{}[]\()|':
            raise PatternInvalid('unescaped metacharacter')
        else:
            chars = {c}
            i += 1
        minimum = maximum = 1
        if i < end and pattern[i] in '?*+':
            q = pattern[i]
            i += 1
            minimum, maximum = {'?':(0,1), '*':(0,None), '+':(1,None)}[q]
        elif i < end and pattern[i] == '{':
            i += 1
            start = i
            while i < end and pattern[i] != '}': i += 1
            if i == end: raise PatternInvalid('unterminated quantifier')
            parts = pattern[start:i].split(',')
            i += 1
            if len(parts) not in (1,2) or any(not p or not p.isascii() or not p.isdecimal() or (len(p)>1 and p[0]=='0') for p in parts):
                raise PatternInvalid('invalid repetition count')
            minimum, maximum = int(parts[0]), int(parts[-1])
            if maximum < minimum or maximum > 1024:
                raise PatternInvalid('repetition count out of bounds')
        atoms.append((frozenset(chars), minimum, maximum))
    if not atoms: raise PatternInvalid('empty expression')
    return atoms


def matches(pattern, value):
    atoms = parse(pattern)
    if len(value) > 4096: raise PatternLimit('value exceeds 4096 code points')
    # Reachable positions after each atom: no backtracking or engine extensions.
    positions = {0}
    for chars, minimum, maximum in atoms:
        following = set()
        for start in positions:
            if minimum == 0: following.add(start)
            stop = len(value) if maximum is None else min(len(value), start + maximum)
            pos = start
            while pos < stop and value[pos] in chars:
                pos += 1
                if pos - start >= minimum: following.add(pos)
        positions = following
    return len(value) in positions
