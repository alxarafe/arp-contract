# ARP-DICT-001 — Contract checks and implementation handoff

The specification includes [portability consolidation 002](dictionary-portability-002.md).
It remains an unpublished candidate; no release or updated stack adoption is inferred.

## Execute offline

Python 3.10+ and the development-only pinned requirements are used:

```sh
python3 -m venv /tmp/arp-contract-venv
/tmp/arp-contract-venv/bin/pip install -r tools/requirements.txt
PYTHONDONTWRITEBYTECODE=1 /tmp/arp-contract-venv/bin/python tools/check_contract.py
PYTHONDONTWRITEBYTECODE=1 /tmp/arp-contract-venv/bin/python -m unittest discover -s tests -v
```

Existing environments with these packages can run the same commands with
`python3`. After dependency installation, checks use no network. No framework,
database, ERP, native runtime library or production validator is imported.

## Distinct verification layers

1. **Structural:** Draft 2020-12 metaschema, closed shapes, 17 types, applicability,
   lexical strings, paired geometry and mathematical metadata maxima. Integer
   validation includes exact integral Decimal nodes (`1.00`), never floats or
   booleans. Numeric token spellings and parser/resource errors are outside schema.
2. **Integrity/focused intake:** fixture identities/refs/outcomes/error order,
   successful type coverage, complete descriptor projections, independent portable
   pattern grammar/matching, explicit YAML styles/resolution, strict Unicode,
   duplicate/forbidden constructs, exact numeric source budgets and depth. The
   manifest profile and schema mathematical bounds are checked against tool constants.
3. **Stack semantics:** each implementation still has to run build/resolve/validate
   against this exact candidate. General value validation, definition semantics,
   catalog registration, concurrency and snapshot guarantees are not implemented by
   the development checker. It is not a production reference implementation.

`tools/source_profile.py` replaces the old simple-string-only YAML helper with
bounded event intake for the specified subset. PyYAML BaseLoader is only a syntax/
event provider; no native resolver or tag constructor chooses the data model.
JSON uses int/Decimal, YAML numeric scalars use the same exact callbacks. Invalid
surrogates are intentionally retained only in the negative **value fixture** data;
actual source parsing and successful projected data require valid Unicode scalars.

## Portable fixture protocol

`fixtures/dictionary/v1/manifest.json` indexes the same six sets and the common
`intakeProfile` budgets. Values embed definitions and portable inputs; original
expectations are preserved. `catalog.json` has all 17 types. Catalog scenarios
execute their steps in order in independent contexts. Catalog ordering is not
semantic; descriptor projections are complete and optional undeclared fields stay absent.

Definition/source `schemaValid` is separate from semantic `expected.valid`.
A null structural verdict means no model reaches schema validation, whether due
to malformed/unsupported intake **or an intake security budget**. Explicit
LIMIT_EXCEEDED expectations distinguish limits from syntax. Source paths are
repository-relative and provider identities remain opaque.

A valid source case may additionally contain `descriptorProjection`. A runtime
runner MUST build that source, resolve `descriptorProjection.id` and compare the
whole projection, as for catalog scenarios. This catches parsers that accept
multiline text or metadata with the wrong decoded content/kind. There are four
such assertions in the new cases; they add no new production operation.

Comparison uses JSON model equality: object key ordering is irrelevant, arrays
retain order, numeric nodes compare as exact mathematical numbers regardless of
spelling (`1` == `1.00` == `0.1e1`), and booleans/strings are distinct from numbers.
Numeric constraint **strings** retain representation under specification §6.1.
Diagnostics remain excluded; scalar constraint issue ordering is unchanged.

`patterns.json` still describes grammar verdicts and matching samples, independently
of schema structural verdicts. `assertRejectedGeneration` requires that the failed
new generation was not published, without forcing disposal of a prior snapshot.

The checker reports **327 shared runtime assertions inventoried**, not 327 native
runtime passes: 136 values, 36 definitions, 40 sources, four source projections,
45 patterns, 21 samples, 32 catalog steps, 12 catalog projections and one base catalog.
The 27 regression test methods are separate development-tool checks, including
all ASCII controls, byte/element boundaries generated in memory, depth, numeric
budget edges, YAML scalar styles/chomping, exact type resolution and error families.

## Coverage and limits

Original Phase A clarifications (`typeRange`, descriptor projection, formal
pattern grammar, intake layering and unpublished status) remain intact. Original
298 shared assertions are preserved and extended by 25 vectors / 29 assertions.
The additions are mapped to distinct divergences/boundaries in the
[consolidation record](dictionary-portability-002.md).

These checks are representative, not an exhaustive proof of every YAML string or
runtime behavior. Bare validation's no-I/O guarantee, immutable snapshots,
isolation and concurrency need native implementation tests. No native stack is
run or modified by this contract-only task. Historical `0172ab6` reports do not
establish conformance with the updated candidate.