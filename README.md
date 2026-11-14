# Alxarafe Resource Platform — Contracts

**arp-contract** is the language-neutral, authoritative source for the Alxarafe Resource Platform (ARP) specifications, schemas, examples, and conformance fixtures. ARP has independent Java, .NET, and PHP implementations; this repository defines their **observable contractual behavior**, not their internal architecture.

## Project status

**Initial governance setup — no ARP contract release has been published from this repository yet.** This branch documents the release and compatibility policy as task **ARP-CONTRACT-001**. It does not implement or publish **ARP-DICT-001**.

The planned first contractual release, `v0.1.0`, is contingent on approval of the ARP-DICT-001 MVP specification and its normative schemas and conformance fixtures. Until that release exists, examples of `v0.1.0` or `dictionary/v1` are illustrative, not supported-version claims.

## Sources of truth

| Concern | Authoritative location |
| --- | --- |
| Contract set and published releases | Annotated Git tags in this repository |
| Version-number rules, immutability, compatibility | [`docs/versioning.md`](docs/versioning.md) |
| Implementation adoption and evidence | [`docs/compatibility.md`](docs/compatibility.md) |
| Steps to publish a release | [`docs/release-process.md`](docs/release-process.md) |
| Human-readable changes | [`CHANGELOG.md`](CHANGELOG.md) |
| Per-release inventory | [`releases/`](releases/) |

Once a feature is approved, its specification, schema(s), and conformance fixtures will be added together. The initial feature is **ARP-DICT-001: reusable scalar dictionary elements**. Every feature must distinguish the **target design** from the **MVP committed in the current release**; unreleased targets are not normative.

## Key principles

- ARP contracts specify what implementations must accept, return, validate, and reject; they do not prescribe a database, ORM, directory layout, or application framework.
- A contract release (`arp-contract vX.Y.Z`), a document format version (for example, `dictionary/v1`), an implementation release (`arp-php vA.B.C`), and an application/module release are different version dimensions.
- Java, .NET, and PHP adopt a **specific released tag/commit** independently. No consumer claims support merely because a contract has been published.
- The released Git tag is immutable. Changes require a new release and a changelog entry; never rewrite a historical tag.
- Actual conformance requires running the released fixtures in the relevant implementation and recording evidence. Proposed, partial, or untested support is not conformance.
- Pre-1.0 development favors deliberate evolution. Breaking changes remain explicit and versioned, rather than hidden behind silent schema or behavior edits.

## Repository layout

```text
arp-contract/
├── README.md
├── LICENSE
├── .gitignore
├── CHANGELOG.md
├── docs/
│   ├── versioning.md
│   ├── compatibility.md
│   └── release-process.md
└── releases/
    └── README.md
```

The `schemas/`, `fixtures/`, and `docs/features/` directories are intentionally **not created** until a real feature needs them. They will be introduced with ARP-DICT-001, together with clearly versioned format rules.

## Previously published Erbas contracts

Existing `erbas-contract` releases are historical inputs, not implicitly republished by ARP. No existing tag is changed. Where a prior definition is reused, the new ARP specification must state exactly what is reused, modified, or replaced. During pre-production development, incompatible changes may be accepted using the policy in [`docs/versioning.md`](docs/versioning.md); there is no assumed obligation to maintain obsolete adapters.

## Contributing

Make changes on a feature branch, review specification and fixture changes together, and follow [`docs/release-process.md`](docs/release-process.md). Do not assign a release tag solely for this documentation bootstrap.

License: see [`LICENSE`](LICENSE).
