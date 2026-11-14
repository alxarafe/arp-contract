# Published release inventories

Each published `arp-contract` release has a corresponding document `vX.Y.Z.md` here, matched to an **annotated, immutable Git tag**. These documents are release inventories, not implementation conformance certificates. No release has yet been published from this repository.

## Required contents of each release inventory

Use the following outline when preparing a release:

```markdown
# arp-contract vX.Y.Z

Status: Draft / Published
Annotated tag: vX.Y.Z
Commit SHA: resolved from annotated tag; record the full SHA in GitHub release metadata after tagging
Predecessor: <previous release or None>
Release date: <YYYY-MM-DD>

## Normative features and MVP scope
- FEATURE-ID — exact normative scope and document path

## Format generations and schemas
- Format ID — schema path, validity policy

## Conformance fixtures
- Suite paths, valid/invalid/expected cases, verification evidence

## Compatibility classification
- PATCH/MINOR/MAJOR; changes and rationale

## Breaking changes and migration
- Exact old/new behavior and migration steps, or None

## Consumer adoption
- No automatic support claim; link to compatibility record
```

Do not commit placeholder files named for prospective releases. In particular, **`v0.1.0` does not exist yet**; it will only be published after approval of the ARP-DICT-001 MVP and its schemas/fixtures.

See [`../docs/release-process.md`](../docs/release-process.md) and [`../docs/versioning.md`](../docs/versioning.md).
