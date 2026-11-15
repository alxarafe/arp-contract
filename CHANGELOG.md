# Changelog

This file records **published** `arp-contract` releases. Every release must have an annotated, immutable Git tag, release notes in `releases/`, and an explicit inventory of normative specifications, schemas, and fixtures.

Changes follow the policy in [`docs/versioning.md`](docs/versioning.md). A release entry is prepared during release review and finalized only when the tag is created.

## Unreleased

No changes after the first-release candidate have been recorded.

## v0.1.0 — first functional contract (release inventory prepared)

This entry describes the intended content of `v0.1.0`. Publication is
established by the annotated Git tag and GitHub Release, not this heading.

### ARP-DICT-001 portability consolidation 002

- Defined the mandatory bounded YAML subset: explicit scalar resolution, plain
  dates/boolean-looking words as text, single-line flow scalars and block multiline
  text; common indentation/escapes/security rules replace native-parser extensions.
- Added exact source-number token/exponent/magnitude budgets (256 characters,
  absolute exponent 128, magnitude below 10^128), mathematical integer metadata
  semantics, shared depth 128 and distinct syntax versus security-limit errors.
- Added 25 directed vectors and four source descriptor projections: 327 shared
  runtime assertions, preserving every original expectation. Updated schema,
  manifest, focused intake checks, regression tests and per-stack handoff.
- Classified these as pre-publication behavior tightening/clarification, not a
  released PATCH or automatic adoption by existing stacks. No functionality added.

### ARP-DICT-001 Phase A

- Closed approved contractual incidents: normative `typeRange`, minimum resolved
  descriptor projection, formal printable-ASCII pattern grammar, error-layer
  classification and approved-but-unpublished specification status.
- Completed the eleven range expectations; added descriptor, source classification
  and pattern fixtures plus independent grammar/match coherence checks. No global
  definition-error accumulation/order requirement or runtime support is introduced.

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

These entries specify the first functional contract release content. The annotated `v0.1.0` tag and matching GitHub Release must be verified before reporting publication.
