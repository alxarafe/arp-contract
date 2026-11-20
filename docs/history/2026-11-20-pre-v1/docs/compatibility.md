# ARP compatibility and conformance record

**Release note:** this file distinguishes pre-release execution evidence from formal adoption of an immutable published contract. At the preparation of `v0.1.0`, the release tag had not been created; consult the current tag and release record before asserting publication. This document defines how adoption will be recorded after a release is available. Do not infer compatibility from a framework version, code compilation, documentation, or successful tests unrelated to released fixtures.

## What is compared

Conformance is established **per implementation, contract release, feature, and format generation**. The relevant unit is the observable contract, not identical source code or the same database/ORM.

Different implementations may use different parsers, persistence providers, or internal types, provided that their exposed behavior matches the normative specification and expected fixtures. Java, .NET, and PHP are evaluated independently.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `NOT_EVALUATED` | No execution evidence for this combination |
| `IN_PROGRESS` | Work or tests underway, not yet conformant |
| `PASS` | Required fixtures and acceptance criteria passed for the pinned refs |
| `FAIL` | Required fixture or acceptance criterion failed |
| `BLOCKED` | Cannot run because of a documented dependency/environment problem |
| `PARTIAL` | Only some capabilities/fixtures passed; **not conformant** |

A missing row is **not** a pass. `PASS` is invalid without reproducible evidence; passing a subset cannot be reported as complete. Deprecated or unsupported formats must be called out explicitly.

## Initial tracking table

These rows are placeholders only. They are **not claims of support**.

| Implementation | Implementation ref | Contract tag + SHA | Feature / format | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| `arp-java` | — | — | ARP-DICT-001 / arp.dictionary/v1 | `NOT_EVALUATED` | — |
| `arp-dotnet` | — | — | ARP-DICT-001 / arp.dictionary/v1 | `NOT_EVALUATED` | — |
| `arp-php` | — | — | ARP-DICT-001 / arp.dictionary/v1 | `NOT_EVALUATED` | — |

Populate the table only after the first contract release exists. Add one row for each contract/feature/format combination actually validated, including older supported generations where relevant. If the matrix becomes large, move detailed results to a versioned manifest while keeping a human-readable summary here.

## Minimum evidence for a `PASS`

A reproducible validation record MUST contain:

1. Contract tag, resolved Git commit SHA, feature ID, and format generation.
2. Implementation name, version/ref, and resolved Git commit SHA.
3. Exact fixture suite/version and confirmation that both valid and invalid cases were run (where defined).
4. Execution command and relevant environment (runtime/database when applicable).
5. Results and failure details, or a durable CI artifact link and run identifier.
6. Date of the run; known exclusions or unsupported optional capabilities.

Conformance runs SHOULD be reproducible from a clean checkout. Local integration tests in a consuming ERP or sample application are valuable but do not substitute for a shared ARP conformance suite unless they execute the normative fixtures against the proper boundary.

## Contract test design

- Normative fixtures distinguish valid input, invalid input, and expected normalized output or error (including codes/precedence if specified).
- Cross-language results must be compared semantically according to the contract; raw serialization differences matter only when the contract defines them.
- A negative fixture must never be interpreted as a passing case merely because an exception occurred; the expected rejection category and behavior must match.
- Fixture and schema paths are taken from the **pinned contract release**. Implementations MUST NOT substitute newer fixtures from `main` when reporting support for an older release.
- A release's test coverage must be described accurately. A `PASS` does not prove properties not tested or specified.

## Implementation release versus contract support

An implementation may publish its own version (for example, `arp-php v0.4.0`) while pinning `arp-contract v0.2.0`. These numbers do not need to match. The implementation's documentation SHOULD link to the relevant entries in this matrix or its maintained evidence, rather than silently upgrading its declared contract version.

For implementation-specific releases, verify the implementation actually contains the claimed support. A later ARP contract publication by itself never upgrades an existing implementation.

## Existing Erbas contracts

Earlier `erbas-contract` releases and adoption claims remain separate historical evidence. Nothing in this blank ARP matrix asserts that those releases have been migrated or that Java, .NET, and PHP currently conform to ARP-DICT-001.

## Pre-release evidence and portability consolidation

The earlier candidate `0172ab64742218b9f64a6ae96c43ebdfe690f4c6` was tested
against 298 shared assertions in PHP, Java and .NET. This is historical evidence,
not proof of adoption of the eventual release.

The consolidated **unpublished** contract candidate `2dde1a09780e29c7385606c5e018fa75a0808b68`
was then tested by all three independent runtimes. The following evidence is
specific to that exact candidate SHA, not to a future documentation commit or tag:

| Implementation | Merged runtime SHA | Shared | Independent | Evidence |
| --- | --- | ---: | ---: | --- |
| PHP 8.4 / 8.5 | [`ca097104c1ce188f19410af74b2d65d9b9e939fe`](https://github.com/alxarafe/arp-php/commit/ca097104c1ce188f19410af74b2d65d9b9e939fe) | 327/327 | 25/25 per version | [Conformance](https://github.com/alxarafe/arp-php/blob/ca097104c1ce188f19410af74b2d65d9b9e939fe/docs/conformance.md) |
| Java 25 | [`3a14a5ea1460ab6caaf634dc538292cefcb74c81`](https://github.com/alxarafe/arp-java/commit/3a14a5ea1460ab6caaf634dc538292cefcb74c81) | 327/327 | 28/28 | [Conformance](https://github.com/alxarafe/arp-java/blob/3a14a5ea1460ab6caaf634dc538292cefcb74c81/docs/conformance.md) / [Machine report](https://github.com/alxarafe/arp-java/blob/3a14a5ea1460ab6caaf634dc538292cefcb74c81/docs/conformance-summary.json) |
| .NET 10 | [`786632f3b04cd615a21db89d66942727152c7c8f`](https://github.com/alxarafe/arp-dotnet/commit/786632f3b04cd615a21db89d66942727152c7c8f) | 327/327 | 35/35 | [Conformance](https://github.com/alxarafe/arp-dotnet/blob/786632f3b04cd615a21db89d66942727152c7c8f/docs/conformance.md) / [Machine report](https://github.com/alxarafe/arp-dotnet/blob/786632f3b04cd615a21db89d66942727152c7c8f/docs/acceptance-summary.json) |

All execution results in this table were produced and recorded by the native
repositories on 2026-11-15, with zero reported failures/skips; they were not
independently rerun by this release-documentation change. The consolidated
contract's separate structural validation and 27 regression tests passed. No
GitHub Actions run was found for the runtime PR heads when reviewed.

The formal released-version adoption table above deliberately remains
`NOT_EVALUATED` until (1) the final immutable `v0.1.0` tag and resolved SHA
exist, (2) each runtime pins that final tag/SHA, and (3) the required tests
are rerun and the exact evidence is recorded. Updating these documentation-only
files changes the contract repository commit SHA even though the normative schema
and fixtures remain the same; previous exact-SHA results cannot be relabeled.

The published release does not automatically imply Erbas contract compatibility
or consumer application adoption. [Release process](release-process.md).
