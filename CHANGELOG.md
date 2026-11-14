# Changelog

This file records **published** `arp-contract` releases. Every release must have an annotated, immutable Git tag, release notes in `releases/`, and an explicit inventory of normative specifications, schemas, and fixtures.

Changes follow the policy in [`docs/versioning.md`](docs/versioning.md). A release entry is prepared during release review and finalized only when the tag is created.

## Unreleased

### ARP-DICT-001 Phase A

- Added versioned Draft 2020-12 dictionary schema, portable positive/negative
  source, definition, value and catalog fixtures covering all 17 scalar types.
- Added independent offline structural/integrity checks and checker regression tests.
- Prepared prospective initial MINOR inventory; documented unresolved contractual
  boundaries and semantic checks deferred to independently tested runtimes.
- No published ARP behavior is changed; no automatic Erbas migration or stack
  conformance is claimed.


### Architecture

- Documented the product mission, optional capabilities, business-domain ownership, infrastructure-independent domain boundary, and adapter responsibilities (**ARP-ARCH-001**).
- Distinguished reusable logical dictionary elements from contextual field/resource/view metadata and from application-owned function invocation.
- Defined the target split between informative preflight validation and authoritative ERP server-side persistence decisions, without publishing a runtime interface or schema.
- Recorded deliberate open questions to resolve in ARP-DICT-001/002 and future domain/metadata features.

### Governance

- Initial repository documentation and versioning policy (**ARP-CONTRACT-001**).
- Defined independent contract-release, document-format, implementation, and module version dimensions.
- Defined pre-1.0 and post-1.0 change classifications, release immutability, and conformance evidence requirements.

**No `arp-contract` version has been published by these documentation changes.** In particular, `v0.1.0` is reserved as a prospective first feature release, not an existing tag.
