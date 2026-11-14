# Phase A local validation results — approved incident closure

Date: 2026-11-14. Branch: `feature/arp-dict-001-contract`.
Starting commit: `baf79735990140e8172a994a40707aa4ab808ca0`.
Environment: Linux, Python 3.14.4, jsonschema 4.19.2, PyYAML 6.0.3.

| Command | Result |
| --- | --- |
| `python3 tools/check_contract.py` | PASS: Draft 2020-12 metaschema, structural verdicts, fixture integrity and focused grammar/projection coherence |
| `python3 -m unittest discover -s tests -v` | PASS: 12 checker regression tests |
| `git diff --check` | PASS |
| `git check-ignore .openidea/test` | PASS: `.openidea/test` ignored |

Inventory checked: 132 value vectors (17 successful scalar types), 34 negative
definition vectors, 21 source vectors, 13 catalog scenarios and 45 pattern grammar
vectors (14 valid, 31 invalid). All eleven former range expectations now contain
`constraint: typeRange`; no `unresolvedContract` markers remain in the fixture suite.

New checks cover scalar constraint ordering with `typeRange` first, rejection of
`typeRange` as a declaration key, distinction from unsigned lexical and security
limit errors, complete descriptor projections and optional-field absence,
printable ASCII grammar and full-match samples. All 33 ASCII control characters
are rejected directly, in classes and after a backslash. Pattern length boundaries
512/513, repetition bounds, empty patterns versus empty-capable expressions and
engine-specific constructs are exercised independently of host regex matching.
Source fixtures isolate syntax, format, document structure and element defects.
No multiple-definition-error accumulation or global ordering policy is asserted.

This supersedes the initial Phase A results (6 tests and eleven incomplete range
expectations). Approved incidents A–E are closed; deliberate deferrals and actual
coverage limits are recorded in [the handoff](dictionary-checks.md).

These are structural/integrity and focused development coherence checks, not
execution of a production runtime's semantic outcomes. No ERP integration,
Java, .NET or PHP conformance suite was executed. All three stacks remain
NOT_EVALUATED. No tag or publication. The new local commit is identified by Git
history; this report does not embed its own SHA.
