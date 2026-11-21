# Alxarafe Resource Platform — Contracts

**arp-contract** is the language-neutral, authoritative source for the Alxarafe Resource Platform (ARP) specifications, schemas, examples, and conformance fixtures. ARP has independent Java, .NET, and PHP implementations; this repository defines their **observable contractual behavior**, not their internal architecture.

## Product and architectural direction

ARP is a set of **optional, reusable declarative capabilities and integration mechanisms** for consuming applications. It does **not** contain any business-domain knowledge or replace the consuming ERP's framework. The ERP owns its business definitions, operations, calculations, policies, and final persistence decisions.

The target is to let applications combine a portable dictionary, logical structures, resource and field metadata, presentation, and registered domain operations while keeping domain code isolated from framework and infrastructure concerns. A consumer may choose only the capabilities it needs. See **[ARP-ARCH-001 — Architecture and product boundaries](docs/architecture.md)** for the complete design principles, intended product boundaries, and explicitly open decisions. That document is architectural direction, not an implemented/runtime contract.

## Project status

**Initial architecture and governance — no ARP contract release has been published from this repository yet.** `ARP-CONTRACT-001` established the versioning and release policy; `ARP-ARCH-001` documents the architecture direction without publishing a runtime contract.

The planned first contractual release, `v0.1.0`, is subject to release review of the ARP-DICT-001 design approved for implementation, its schemas and conformance fixtures. Until that release exists, examples of `v0.1.0` or `dictionary/v1` are illustrative, not supported-version claims.

## Revisión del borrador 1.0

El [borrador funcional](docs/contract-v1-draft.md) y la [propuesta de diccionario](docs/dictionary.md)
están pendientes de aprobación. `INTEGER` es un cambio incompatible aislado del esquema vigente.
La [revisión de cambios](docs/review-contract-v1.md) separa documentación y contrato.
El [archivo documental](docs/history/README.md) conserva estados, decisiones y evidencias anteriores;
los enlaces históricos siguen disponibles. No se publica ninguna versión por esta revisión.

## Sources of truth

| Concern | Authoritative location |
| --- | --- |
| Architecture, ownership boundaries and optional capabilities | [`docs/architecture.md`](docs/architecture.md) |
| Contract set and published releases | Annotated Git tags in this repository |
| Version-number rules, immutability, compatibility | [`docs/versioning.md`](docs/versioning.md) |
| Implementation adoption and evidence | [`docs/compatibility.md`](docs/compatibility.md) |
| Steps to publish a release | [`docs/release-process.md`](docs/release-process.md) |
| Human-readable changes | [`CHANGELOG.md`](CHANGELOG.md) |
| Per-release inventory | [`releases/`](releases/) |

The first feature candidate is **ARP-DICT-001: reusable scalar dictionary elements**, with specification, schema and shared fixtures reviewed together. Every feature must distinguish the **target design** from the **MVP committed in the current release**; unreleased targets are not normative.

## Key principles

- ARP contracts specify what implementations must accept, return, validate, and reject; they do not prescribe a database, ORM, directory layout, or application framework.
- ARP supplies general mechanisms, never domain-specific ERP rules. The application defines and reuses its own business model and domain implementations.
- Shared contracts are infrastructure-neutral, and domain code can remain independent of both ARP and its framework adapters.
- Optional capabilities must remain optional, subject only to their declared indispensable dependencies. Client preflight and presentation never replace authoritative server-side decisions.
- A contract release (`arp-contract vX.Y.Z`), a document format version (for example, `dictionary/v1`), an implementation release (`arp-php vA.B.C`), and an application/module release are different version dimensions.
- Java, .NET, and PHP adopt a **specific released tag/commit** independently. No consumer claims support merely because a contract has been published.
- The released Git tag is immutable. Changes require a new release and a changelog entry; never rewrite a historical tag.
- Actual conformance requires running the released fixtures in the relevant implementation and recording evidence. Proposed, partial, or untested support is not conformance.
- Pre-1.0 development favors deliberate evolution. Breaking changes remain explicit and versioned, rather than hidden behind silent schema or behavior edits.

## Contract checks and candidate assets

ARP-DICT-001, including portability consolidation 002, provides `schemas/dictionary/v1/`, portable fixtures in
`fixtures/dictionary/v1/`, and development-only checks in `tools/` and `tests/`.
See [execution and coverage](docs/dictionary-checks.md)
and [recorded results](docs/dictionary-check-results.md). These assets remain
unreleased. Historical PHP/Java/.NET results cover the earlier `0172ab6` candidate;
updated stack conformance has not been evaluated. See
[portability decisions and implementation impact](docs/dictionary-portability-002.md).

## Candidate modules and menus

[ARP-MODULES-001](docs/features/arp-modules-001.md) and [ARP-MENUS-001](docs/features/arp-menus-001.md) propose
source activation, manual/modular menu composition and selective invalidation in one application cache.
Their shared fixtures and offline verifiers remain candidates for review; no installer, cache backend or UI is added.

## Candidate record reads

[ARP-CDS-LISTGET-001](docs/features/arp-cds-listget-001.md) proposes minimal LIST/GET semantics over an existing
table, with 88 shared product vectors, active catalog/reports projections, a SERVICES-002 result profile and
an adapter responsibility boundary. It remains subject to review; it does not implement SQL, HTTP, permissions
or native runtime conformance. The original 74 vectors are preserved; the verifier also covers modular activation.

## Previously published consumer contracts

Existing `previous consumer contract` releases are historical inputs, not implicitly republished by ARP. No existing tag is changed. Where a prior definition is reused, the new ARP specification must state exactly what is reused, modified, or replaced. During pre-production development, incompatible changes may be accepted using the policy in [`docs/versioning.md`](docs/versioning.md); there is no assumed obligation to maintain obsolete adapters.

## Contributing

Make changes on a feature branch, review specification and fixture changes together, and follow [`docs/release-process.md`](docs/release-process.md). Do not assign a release tag solely for architecture documentation.

License: see [`LICENSE`](LICENSE).

## Candidate record writes

[ARP-CRUD-001A](docs/features/arp-crud-001a.md) proposes CREATE and physical DELETE over the existing `demo.items`
definitions and registration, reusing SERVICES-001/002 partial UPDATE and LIST/GET identities.
Its fixtures and finite in-memory oracle distinguish missing/null/default values, read-bound deletion,
authorization, concurrency, integrity restrictions and uncertain commit outcomes. No runtime, transport,
new scalar type or general rules engine is introduced; the candidate requires review.