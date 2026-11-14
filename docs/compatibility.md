# ARP compatibility and conformance record

**Current state: no ARP contract release or conformance claim yet.** This document defines how adoption will be recorded after a release is available. Do not infer compatibility from a framework version, code compilation, documentation, or successful tests unrelated to released fixtures.

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

PHP, Java and .NET have documented 298 shared fixture assertions against the
unpublished `0172ab64742218b9f64a6ae96c43ebdfe690f4c6` candidate. These are historical
candidate results, not adoption of a released contract, and are not rewritten by
the [327-assertion portability consolidation](dictionary-portability-002.md).

All three implementations are **NOT_EVALUATED for the consolidated candidate**.
Each needs the concrete parser/budget/runner adaptations documented there, an
exact updated pin and its own new semantic/instrumentation evidence. No native
repository was modified or rerun by this contract-only task. The first release
matrix remains unpopulated until a published contract and precise evidence exist.
