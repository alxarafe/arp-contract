# ARP contract release process

This process implements [`versioning.md`](versioning.md). It covers contract set releases, not releases of `arp-java`, `arp-dotnet`, `arp-php`, or consuming applications.

## A. Before opening a release candidate

1. Work on a feature branch and review the current contract baseline and previously published tags.
2. Identify the features in scope and separately document their **target** and **MVP**.
3. Complete normative specifications, schemas, valid and invalid fixtures, expected outputs/errors, and acceptance criteria for **every newly normative feature**.
4. Run available schema/fixture validations; archive exact commands/results. If test tooling does not exist yet, do not claim a suite passed.
5. Classify every change as PATCH/MINOR/MAJOR following the policy, including semantic or strict-schema incompatibilities.
6. For breaking changes, provide concrete migration guidance, explicitly naming versions and format generations affected.
7. Update `CHANGELOG.md`, [`compatibility.md`](compatibility.md) as warranted by **real** evidence, and prepare a new `releases/vX.Y.Z.md` entry using [`releases/README.md`](../../../../releases/README.md).
8. Confirm no secrets, environment files, generated artifacts, or `.openidea/` files are staged.

For ARP-CONTRACT-001, stop after documenting the policy: **do not create a prerelease or release tag**. The first release awaits approved ARP-DICT-001 content.

## B. Release candidate

1. Merge the reviewed feature set according to repository rules, or use a dedicated reviewed release branch.
2. Freeze the candidate commit; create an annotated prerelease tag, e.g. `v0.1.0-rc.1`, only when the candidate is ready.
3. Record the candidate SHA and run the version-pinned normative validations against that exact commit.
4. If anything normative changes, prepare a new candidate tag (`rc.2`, etc.). Do not move an old tag.
5. Check documentation links, schema paths, fixture expectations, and the release inventory.

## C. Final publication

1. Review the completed changelog entry, release inventory, compatibility classification, and migration notes.
2. Confirm the release commit exactly contains the approved specification/schema/fixture versions.
3. Create the final **annotated** immutable `vX.Y.Z` tag on that commit and push it.
4. Record the resolved commit SHA in the GitHub release record or a durable post-tag verification report. The tracked `releases/vX.Y.Z.md` identifies its tag; it must **not** attempt to embed its own commit SHA, which would be self-referential. Do not amend or move an already published tag.
5. Publish a GitHub release with a summary, supported feature/format inventory, and breaking changes. Ensure links refer to version-pinned contents, not the moving `main` branch.
6. Verify the tag and release are publicly visible and point to the intended commit.

**No automatic claim of Java/.NET/PHP support is made by these actions.** Implementation adoption and evidence are separate follow-up work.

## D. Consumer adoption

1. Each implementation chooses a released contract tag and records its resolved SHA.
2. Execute the corresponding normative fixture suite against that implementation.
3. Record evidence and statuses according to [`compatibility.md`](compatibility.md).
4. Publish the implementation's own version when appropriate, independent of the ARP contract version.
5. For incompatible upgrades, update affected documents/migrations by a reviewed migration plan, not by rewriting historical applied migrations.

## E. Corrections after publication

Never force-push or retarget published release tags. Use a new version even for small documentation corrections that should be part of a reproducible published snapshot. Changes on `main` do not retroactively alter historical releases. If a previously published assertion was wrong, record the discrepancy and corrective release rather than rewriting history.

## F. Initial release checklist

The first version (`v0.1.0`, prospective) must at minimum have:

- [ ] Approved ARP-DICT-001 MVP specification, distinct from target design.
- [ ] Approved dictionary format identifier and parser/validation rules.
- [ ] Normative schema(s) and positive/negative conformance fixtures.
- [ ] Expected normalized results and errors; validation run results.
- [ ] `CHANGELOG.md` entry and `releases/v0.1.0.md` inventory.
- [ ] Breaking-change and migration notes, or an explicit `None`.
- [ ] Tag/SHA and GitHub release verified after publication.
- [ ] Implementation statuses recorded accurately as evaluated or `NOT_EVALUATED`.