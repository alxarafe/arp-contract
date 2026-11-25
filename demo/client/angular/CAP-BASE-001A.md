# CAP-BASE-001A — Angular demo regression baseline

Verified on 2026-11-25, before extraction. Only demo regression tests/fixtures and this QA documentation change.
The existing application, protocols, contract fixtures, package versions and workflows remain unchanged.
This is a behavior baseline, not ARP transport approval, AUR editor adoption or general backend conformance.

## Revisions and installed packages

- Demo production source and contract assets: `c8b41ec49c7d337deddeb0c6a0896a16143727af`.
  Tests are those committed with this report; production source is unchanged from that base.
- AUR provider: clean `ee60123d03f095a14c4004632c214dbd822332c2`, required by the existing demo runner.
  A separate detached clone was used; the current AUR checkout was not switched or modified.
- PHP backend: `51c57cfbbe3953d460896d1a2e30b196329b5f58`; actual disposable HTTP/MariaDB integration.
- PHP write contract: `e3c2c08c93add63faebbe011a7e8e1ec3eccff2c`, exported to a separate pinned checkout by the runner.
  This differs from the current contract assets displayed by the browser; no pin was silently upgraded.

The existing Docker build installs all six built public APF archives, checks exported declarations and preserves
the consumer lockfile/dependency graph. Runtime is `@alxarafe/ui-runtime@0.3.0-alpha.3`; themes are independently
`@alxarafe/ui-theme-<id>@0.1.0-alpha.3`. Package version alone is not source or archive identity.
The following SHA-256 values come from this run's `artifacts/packages.json`, not a previous consumer adoption.
Runtime archive is `alxarafe-ui-runtime-0.3.0-alpha.3.tgz`; theme archives follow
`alxarafe-ui-theme-<id>-0.1.0-alpha.3.tgz`.

| Archive | SHA-256 |
| --- | --- |
| `runtime-0.3.0-alpha.3` | `8b07a27d640bec08a619c893556d91d11ca6a458d699526e048c469fd585913b` |
| `theme-default-0.1.0-alpha.3` | `017068379d25b8fa87da54a578a031ab13a5475050ac5857875e0fbc0a567c2e` |
| `theme-alternative-0.1.0-alpha.3` | `40c71af36697b1b43ccecad87578ab8ef2aa8cc92a07ae9e57e312b0fecaa743` |
| `theme-cyberpunk-0.1.0-alpha.3` | `5d4894291d3ae898be00dd46030c837d8fb40a63dcfc108a55854b7e3fecd064` |
| `theme-vintage-0.1.0-alpha.3` | `e9d3cbb84465ffc12f06abe31babd8b02041b8dad77b25d9efa31263cde94f20` |
| `theme-high-contrast-0.1.0-alpha.3` | `23d86de77c313f785f76fa4012431b358e6884ca0a128699be3d01281e8c9be5` |

Node image: `node:24.22.2-bookworm-slim`, digest
`sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9`.
Chromium runner: `mcr.microsoft.com/playwright:v1.58.2-noble`, digest
`sha256:65cefd09a5e943921ecd3a6e5414c603db2eb161e9eb48f2e2ccc63486dc7dc0`.
PHP's existing Dockerfile pins its PHP/Composer bases; its runner uses `mariadb:12.3` and installs OS packages.
Observed MariaDB image digest:
`sha256:4ebbcf100a3ba320766dfa0e1af008df12261301db6ef72798c7650f70794aed`.
Those backend inputs are not represented as a fully reproducible dependency lock or a new release guarantee.

## Added protection

- Two unit cases in `tests/unit/crud-protocol.test.mjs`: missing record fields are rejected rather than converted
  to null/empty; sparse omission, explicit null, empty text, false and lexical numeric edits remain distinct.
- Seventeen browser/mock cases in `tests/browser/crud-baseline.spec.mjs`, each at both viewport widths:
  partial negotiation never sends credentials; invalid metadata renders no partial operations; exact request bodies;
  full-field CREATE initialization; sparse UPDATE with original baseline; rejection/invalid-draft retention;
  conflict/network-loss/malformed-response locks; duplicate-save suppression; displayed-state DELETE consent/cancel;
  cancellation and non-cooperative late info/metadata/LIST/GET/UPDATE responses. A late UPDATE cannot close a new
  session's draft or issue a stale follow-up request. Gates and retryable assertions replace elapsed-time sleeps.
- Six browser/mock dictionary cases in `tests/browser/dictionary-baseline.spec.mjs`, each at both widths:
  recognized .NET/Java/PHP identities, capability withholding, descriptor bytes, exact integer/decimal strings,
  empty text, false, null and response clearing. Scripted responses are not validators or proof of runtime adoption.
- The mock UPDATE scenario retains the same focused input DOM through Spanish/English and all five themes,
  then checks real Tab navigation. No reload or synthetic state replacement substitutes for that retained node.
- Existing real PHP lifecycle assertions now check the rejected draft after an UPDATE conflict. One additional
  real case per viewport executes CREATE via PHP/MariaDB, loses only the browser response, proves the draft/replay
  lock and reads the committed row back explicitly. Its disposable row is deleted in `finally`.

`tests/browser/fixtures/crud-baseline.mjs` is a fixed boundary-response fixture and request recorder.
It does not implement persistence, validation or a second resource protocol. Original lifecycle/browser assertions
remain in place. The original 24 autonomous browser cases still protect fixture downloads, pagination-independent
navigation, ES/EN/storage/error behavior and theme activation.

## Executed validation

Commands run from the repository root, using existing ephemeral Docker workflows and a clean detached provider clone:

```sh
ARP_UI_RUNTIME_PATH=/tmp/aur-cap-base-001a demo/client/angular/bin/run check
ARP_UI_RUNTIME_PATH=/tmp/aur-cap-base-001a python3 -B demo/client/angular/bin/integration-crud
python3 -B tools/check_documentation.py
python3 -B -m unittest discover -s tests -p test_documentation.py
git diff --check
```

| Layer/check | Verified result |
| --- | --- |
| APF install, strict Angular build, unit tests | PASS; 16 unit tests, including 2 added cases |
| Autonomous Chromium (`bin/run check`) | 70 passed; 0 failed/skipped/flaky |
| Final Chromium with PHP/MariaDB (`bin/integration-crud`) | 80 passed; 0 failed/skipped/flaky |
| Actual PHP/MariaDB browser cases within that 80 | 10 passed, including 2 new lost-response cases |
| Final database comparison | All 30 CSV records identical to the initial state |
| Package provenance | Same six archive hashes in both workflows |

The autonomous run preceded the final strengthening of late-response assertions; the final integrated run executed
all 70 autonomous/mock cases with those assertions plus the 10 real-backend cases. No earlier pass is substituted
for final-suite validation. Browser reports identify starts at 13:01:58 UTC (autonomous) and 13:04:12 UTC (integrated).

Chromium uses desktop 1440×1000 and mobile 390×844, one worker, zero retries. The integrated total includes the
same autonomous/mock suite; totals must not be added as independent coverage. Real CRUD cases disable credential
traces/video/automatic screenshots. The PHP workflow uses loopback HTTP, an unexposed disposable database and
owner-checked cleanup. It compares all original CSV records after the browser cases, not just their count.
No pre-existing running containers were present at the start; final ownership/cleanup was checked separately.

Generated `artifacts/packages.json`, `artifacts/browser/results.json` and `artifacts/crud-integration.json` remain
ignored QA artifacts; the integrated run overwrites the browser report. Source identities, archive hashes and
results necessary to interpret this baseline are retained here. An initial authoring run failed because a new
mock expected a shortened connection-status message; the assertion was corrected to the exact existing text,
then the workflows were rerun. No production behavior or existing assertion was relaxed.

## Limits and preserved behavior that is not a new capability

- Current CREATE initializes every metadata field (nullable -> null, BOOLEAN -> false, other fields -> empty text).
  It has no general “leave field absent for server default” UI. Absence protection here concerns rejected incomplete
  response records and omitted UPDATE changes; this is not evidence of optional/default CREATE editing support.
- The demo compares changed numeric strings lexically. `1.00` -> `1.0` is a change; no new numeric equality policy
  or arbitrary JavaScript Number conversion is introduced.
- Large integer/decimal request precision and nullable/empty distinctions have unit/mock browser evidence.
  The actual PHP demo table exercises its existing INTEGER/rating/text fields, not arbitrary DECIMAL/UINT64 SQL.
- Real PHP cases cover pagination, CREATE/GET/sparse UPDATE/DELETE, invalid value rejection, UPDATE/DELETE conflicts,
  renewed deletion consent, credentials/context invalidation and committed-CREATE response loss. They do not prove
  every native transaction/rollback vector, uncertain DELETE or all possible network failure points.
- Three-runtime live dictionary integration was not rerun. The 74-case multiruntime evidence and earlier counts in
  [VALIDATION.md](VALIDATION.md) remain historical at their original pins. Mock identity tests do not establish
  Java/.NET adoption of the current INTEGER contract or CRUD support.
- Browser viewport/focus checks are not physical mobile-device, assistive-technology or human visual certification.
  Existing cancel/disconnect behavior is preserved; there is still no general confirmed-discard/navigation guard,
  AUR DocumentSession integration or reusable field-linked server-error presentation in this demo.

Reproduction of live dictionary evidence remains a separate invocation of `bin/integration-multiruntime` with
explicit compatible runtime/contract checkouts. See [PHP operation and evidence boundaries](CRUD-PHP.md).
No historical report or normative contract is rewritten by this baseline.