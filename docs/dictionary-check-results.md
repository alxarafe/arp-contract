# Phase A local validation results

Date: 2026-11-14. Branch: `feature/arp-dict-001-contract`.
Environment: Linux, Python 3.14.4, jsonschema 4.19.2, PyYAML 6.0.3.
No pre-existing test suite was present in the initial checkout.

| Command | Result |
| --- | --- |
| `python3 tools/check_contract.py` | PASS: Draft 2020-12 metaschema, structural verdicts and fixture integrity |
| `python3 -m unittest discover -s tests -v` | PASS: 6 checker regression tests |
| `git diff --check` | PASS |
| `git check-ignore .openidea/test` | PASS: `.openidea/test` ignored |

Inventory checked: 131 value vectors (17 successful scalar types), 34 negative
definition vectors, 16 source vectors, 8 catalog scenarios. Eleven range vectors
are explicitly incomplete pending the constraint-name decision. Other contract
questions and coverage limitations are recorded in [the handoff](dictionary-checks.md).

These are structural/integrity results, not execution of the expected semantic
outcomes. No production runtime, ERP integration, Java, .NET or PHP conformance
suite was executed. All three stacks remain NOT_EVALUATED. No tag or publication.
The local commit is identified by Git history; this report does not embed its own SHA.
