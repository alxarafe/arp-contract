# ARP contract versioning policy

**Status:** Policy proposal for approval under **ARP-CONTRACT-001**. This document becomes authoritative in the repository when merged. It does not itself publish a contract release.

## 1. Purpose and scope

This policy governs the published contract set in `arp-contract`, including specifications, normative schemas, accepted/rejected inputs, expected normalized outputs, and observable error/validation rules. It also describes how independent implementations identify the contract release they consume.

Compatibility must be evaluated from the perspective of a conforming producer **and** consumer, including observable results, errors, constraints, ordering where specified, and behavior under invalid input. A JSON or YAML shape appearing unchanged does not establish behavioral compatibility.

The word **MUST** indicates a requirement of this policy; **SHOULD** is a strong recommendation; **MAY** is optional. Normative feature-specific MUST/SHOULD requirements start only when that feature is published.

## 2. Distinct version dimensions

| Dimension | Identifier/example | Meaning | Owner |
| --- | --- | --- | --- |
| Contract set release | `arp-contract v0.1.0` | Immutable snapshot of normative features, schemas, and fixtures | `arp-contract` |
| Document/wire format | `arp.dictionary/v1` (illustrative) | Incompatible grammar/representation generation of a particular format | Feature contract |
| Feature identifier | `ARP-DICT-001` | Stable work/specification identity, **not** a version number | Feature contract |
| Framework implementation | `arp-java v0.3.0` (illustrative) | Version of a Java/.NET/PHP implementation, not of the contract | Implementation repo |
| Consuming module/application | `catalog v0.1.0` (illustrative) | Product's own lifecycle and migrations | Application/module |

The format identifier shown above is a **proposal**. ARP-DICT-001 must approve the actual identifier, schema placement, and parser rules before their use is normative. Format versions are not bumped for every contract repository release.

A contract release MAY contain several features and format generations. Implementations MAY adopt them at different times; an implementation's release number MUST NOT be interpreted as proof of contract conformance.

## 3. Contract repository versioning

`arp-contract` uses Semantic Versioning (`MAJOR.MINOR.PATCH`) with annotated tags named `vMAJOR.MINOR.PATCH`. A tag points to one exact commit; release contents are identified by that Git object, not by the current `main` branch.

### Before `1.0.0`

| Change | Bump | Example |
| --- | --- | --- |
| Editorial or test correction with **no changed normative behavior** | PATCH | `v0.1.0` → `v0.1.1` |
| New compatible functionality | MINOR | `v0.1.0` → `v0.2.0` |
| Deliberate incompatible normative change | MINOR | `v0.2.0` → `v0.3.0`, with breaking-change/migration notes |

This is an explicit project policy for development releases: although SemVer allows breaking changes in `0.x`, ARP requires them to be identified and documented. A breaking change MUST NOT be disguised as PATCH. A historical tag MUST NOT be retargeted.

### From `1.0.0` onward

| Change | Bump | Example |
| --- | --- | --- |
| Compatible clarification/correction that preserves normative behavior | PATCH | `v1.0.0` → `v1.0.1` |
| Backward-compatible extension | MINOR | `v1.0.1` → `v1.1.0` |
| Incompatible normative change | MAJOR | `v1.1.0` → `v2.0.0` |

The classification uses the **strongest** change in a release. For example, an additive feature does not make an unrelated breaking change compatible. An implementation bug fix may alter its implementation version independently; that does not justify quietly changing the authoritative contract.

### Common classification examples

- Adding an optional field to a **closed** object is potentially breaking if old validators reject unknown properties. Review schemas and strict consumers before calling it compatible.
- Making an optional field mandatory, narrowing a valid value range, or changing error precedence is normally breaking.
- Broadening accepted input can affect validation and downstream assumptions; assess compatibility, do not assume it.
- Adding a completely separate optional feature/endpoint is usually compatible if existing operations and schemas remain unchanged.
- Fixing a misleading example is PATCH **only** when it does not alter the normative requirements.
- Adding a normative negative fixture that rejects formerly valid input is a behavior change; classify accordingly.

## 4. Document and wire format versions

A format version is independent of the contract repository's SemVer. ARP uses a named generation, such as `dictionary/v1`, to distinguish **incompatible serialized representations**. A parser MUST identify the declared format before interpreting a document once that feature's format rule is published.

If a published format's grammar/encoding changes incompatibly (for example, replacing an object with a list or changing a field's type), define a **new format generation**, such as `dictionary/v2`, together with its own normative schema and fixtures. Do not modify the published v1 schema in place inside its historical release.

A compatible extension may remain within `v1` if the already published contract explicitly permits it **and** existing strict validators and consumers remain compatible. This is not assumed when schemas are closed.

A semantic breaking change that preserves the serialized shape still requires a breaking contract release, migration guidance, and review of whether a new format generation is needed to prevent ambiguity. Do not silently change what a declared format means. If accepting the old interpretation would give conflicting results, use an unambiguous new identifier or a documented negotiation/migration mechanism.

Multiple format generations MAY coexist in a later contract release; support must be stated and tested separately. Removal of a generation is a breaking change.

## 5. Feature specifications: target versus MVP

Each feature specification MUST distinguish:

1. **Target design:** the desired longer-term behavior, explicitly non-normative until delivered.
2. **MVP in this release:** the exact behavior, schemas, error cases, and fixtures implemented/required by this release.
3. **Dependencies and exclusions:** what belongs to the application, storage provider, another feature, or a later release.
4. **Acceptance/conformance criteria:** language-neutral inputs and expected outputs, including invalid cases.

A feature ID (for example, `ARP-DICT-001`) is stable. Its meaning is established by the versioned contract snapshot; avoid giving each Markdown file its own independent SemVer unless a concrete interoperability need is established.

## 6. Publication immutability and pinning

- Every published release MUST have a unique annotated Git tag, release notes, a changelog entry, and a recorded complete commit SHA.
- Published tags MUST NOT be changed, moved, deleted, or reused. A correction requires a new release.
- Implementations and automated conformance runs MUST pin an exact released tag **and** record its resolved commit SHA. Following `main`, an unqualified `latest`, or a moving branch does not qualify as a reproducible contract pin.
- An implementation MAY pin an older release and MUST not claim adoption of later releases until its relevant conformance results exist.
- A prerelease (`v0.1.0-rc.1`) is a test candidate, not a stable contract release. If it changes after review, issue another candidate rather than repointing the old candidate tag.

Teams SHOULD protect release tags with repository rules where permissions allow. Git policy is enforceable only to the extent the repository configuration actually implements it; documentation alone is not an access-control guarantee.

## 7. Release inventory and compatibility evidence

A release MUST enumerate:

- The feature identifiers and normative scopes included.
- Supported format generations and schema paths.
- Conformance fixture sets and expected outputs.
- Changes classified as compatible/incompatible, with rationale.
- Migration guidance for breaking changes; state explicitly if no automated migration exists.
- Explicit predecessor release (if any), annotated tag, and commit SHA.

Implementation support is recorded separately in [`compatibility.md`](compatibility.md). A contract being published **does not imply** that `arp-java`, `arp-dotnet`, or `arp-php` implements it. A `PASS` result requires the precise contract tag/SHA, implementation ref/SHA, executed fixtures, environment, and a reproducible test report.

## 8. Migration strategy

For each incompatible change, record what old documents or clients do, what the new contract requires, and concrete manual or automated migration steps. During `0.x`, projects MAY adopt the new contract without maintaining adapters where there are no deployed external consumers. Still record the change, and never rewrite historical release evidence.

Preserve historical migrations and other persisted artifacts according to the owning application's rules: do not alter previously applied database migrations just because a dictionary definition changed. Runtime contracts do not prescribe how an ERP migrates storage.

Existing `previous consumer contract` tags remain unchanged. This repository MAY supersede or reinterpret pre-production conventions in a new ARP release, with explicit release notes identifying what was retained or superseded. No silent transfer of normative ownership is implied.

## 9. First publication

**ARP-CONTRACT-001 publishes policy documentation only, without a Git release tag.** The prospective first stable contractual snapshot from this repository is `v0.1.0`, conditional on approval of ARP-DICT-001, including its MVP, schemas, positive/negative fixtures, expected normalized results, and release inventory.

See [`release-process.md`](release-process.md) for the publication checklist.