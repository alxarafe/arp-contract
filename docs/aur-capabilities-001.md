# AUR-CAPABILITIES-001 — Implementation inventory and migration proposal

**Status:** Analysis and documentation only; implementation tasks below require separate authorization.
**Inspection date:** 2026-11-25. **Scope:** Existing Angular capabilities, ownership and controlled extraction.
This is not a normative contract, protocol approval, release, runtime conformance report or authorization to move code.

The approved direction is [ARP-UI-BOUNDARIES-001](decisions/ARP-UI-BOUNDARIES-001.md).
The [architecture entry](architecture.md) links the preserved historical baseline; this inventory changes neither.
AUR owns reusable visuals and editing interaction; ARP Angular owns ARP interpretation and CRUD adaptation;
ERBAS owns its application. Demonstration applications remain separate consumers.

## 1. Repository safety, revisions and evidence

All three tracked working trees were clean at the initial inspection. No interrupted tracked changes were found.
The canceled ERBAS integration left local `feature/erbas-aur-crud-001` branches in AUR and ERBAS and ignored AUR
pack/build artifacts. Those are separate from this inventory and were neither removed nor incorporated.
No package adoption from that canceled task has occurred.

| Repository | Exact main revision inspected | Initial local state |
| --- | --- | --- |
| arp-contract | `fcf9b42b0fa8fefb4c900125682faabcfc768ac3` | Clean main, initially one commit behind |
| angular-ui-runtime | `26d4fa3458c8d4fc66b65a1eac9d9c5e5f036e9e` | Clean feature branch, same HEAD as main |
| erbas-client | `1ec83f63f2cf77dc2820e47af18c645fcf156b11` | Clean feature branch, same HEAD as main |

ARP initially had local main `6066ba8b6163d27df660be5fbcee43114056cd19`. Remote main was inspected, fetched,
and used as the base of `docs/aur-capabilities-001`, without resetting local main. The intervening commit adds
only the architectural decision. Main references for all three repositories were checked against GitHub.
The two consumer feature branches and their HEADs remain unchanged.

Source keys below refer to these immutable trees:

- **C:** [arp-contract source](https://github.com/alxarafe/arp-contract/tree/fcf9b42b0fa8fefb4c900125682faabcfc768ac3).
- **U:** [AUR source](https://github.com/alxarafe/angular-ui-runtime/tree/26d4fa3458c8d4fc66b65a1eac9d9c5e5f036e9e).
- **E:** [ERBAS source](https://github.com/alxarafe/erbas-client/tree/1ec83f63f2cf77dc2820e47af18c645fcf156b11).

Paths are repository-relative. In C the requested `src/remote/` files actually reside under
`demo/client/angular/src/remote/`; there is no root Angular library at `src/remote/`.
For compact records, **D** means C:`demo/client/angular/`, **R** means E:`app/src/app/resource-runtime/`,
and **U-src** means U:`projects/ui-runtime/src/`. **E-app** means E:`app/src/app/`.
Directory references include adjacent templates/styles/tests.

Evidence levels must remain separate:

- **Inspected:** Source, exports, installed archive declarations, assertions, documentation and provenance.
  “Active” below means used by current source, not a new successful execution report.
- **Historical execution:** D:`VALIDATION.md` records 14 unit and 32 Chromium tests for PHP CRUD, and separately
  74 Chromium tests for three-runtime dictionary integration. E documentation records prior mocked and live proofs.
  Their dates, pins and limitations remain authoritative for those runs; this task did not rerun them.
- **Current execution:** Only documentation validation described in section 12. No new browser, database,
  backend conformance, accessibility certification or end-to-end consumer proof was executed.

### Package identity is not source identity

Both D and E consume APF from AUR `ee60123d03f095a14c4004632c214dbd822332c2`, not the U revision above.
Runtime is nominally `0.3.0-alpha.3`; five themes are `0.1.0-alpha.3`, with exact runtime peers.
E:`app/vendor/README.md`, `app/vendor/aur-integration-002-provenance.json` and
`app/package-lock.json` preserve archive
SHA-256, source commit and npm integrity. D:`scripts/install-packages.mjs` and `artifacts/packages.json`
record its pinned build/adoption mechanism. Generated artifacts are not new tracked evidence here.

Inspection of E's vendored runtime declaration confirms shell/field ports, but no `FormComposition`,
`DocumentSession`, `MenuDefinition` or editor binding exports. Its field artifacts still include `field.INT8`,
`field.UINT8`, etc. Current U has fourteen mandatory artifacts: three structural and eleven semantic fields,
including `field.INTEGER`. E's `NormalizedFieldTypeRegistry` still uses the old artifact constants.
Thus identical package version strings do not imply interchangeable archives or compilable consumers.
Future adoption must record source SHA, all six hashes, lock integrity and compatibility tests together;
it must preserve historical provenance and must not mix old themes with new runtime bytes.

## 2. Ownership matrix and extraction rules

| Owner | Capabilities | Excluded responsibilities |
| --- | --- | --- |
| AUR | Visuals, layouts, themes, focus, feedback, document state | Metadata, routing, HTTP, policy |
| ARP Angular | ARP negotiation, metadata, codecs, CRUD, responses | Visual renderer or state engine |
| ERBAS | Composition, auth, routes, backend choice, domain policy | Permanent generic visual copies |
| Demo/QA | Fixtures, explorer, disposable hosts and proof workflows | Reusable capability ownership |
| Backend | Effective permissions, final validation, atomic execution and persistence | Angular components or themes |

Location is not ownership: reusable orchestration currently embedded in D is an extraction candidate, not demo-only
by definition. Conversely, an ERBAS transport adapter remains protocol-specific even when its operation is called CRUD.
“ARP Angular” ownership below means the ARP equivalent belongs there; it does not authorize copying ERBAS wire types
into an ARP contract. Section 6 defines the compatibility boundary.

### Capability ownership index

Split owners below refer to distinct responsibilities, detailed in the matching record. E's v0.14 compatibility
mapping remains protocol-specific at the application seam until a separate packaging decision is approved.

| Record/capability | Correct owner | Active source/use |
| --- | --- | --- |
| F01 Theme resolution | AUR; app chooses theme | U, D, E |
| F02 Theme field renderers | AUR; adapter maps types | U, E; D shell only |
| F03 Shell/panel/regions | AUR | U, D, E |
| F04 Menus/navigation | AUR visuals; app routes | Legacy D/E; typed U QA |
| F05 Contributions/slots | AUR projection; app registration | E registry, U regions |
| F06 Form composition | AUR | U QA; E/D local forms |
| F07 Layout/context | AUR visuals; adapter interpretation | U QA, E contextual layouts |
| F08 Lossless widgets | AUR | U QA; E themed scalar ports |
| F09 Optional controls | AUR | U QA |
| F10 Relationship choice | AUR visuals; adapter relation/query | E MANY_TO_ONE |
| F11 Field capabilities | AUR flags; adapter derives policy | U, D, E, different semantics |
| F12 Slots/objects/dialogs | AUR primitives; app content/policy | Partial U/E/D mechanisms |
| F13 Validation | AUR engine; adapter truthful plan | U QA, E local subset |
| F14 Feedback/reveal | AUR visuals; adapter error mapping | U QA, E field feedback |
| F15 List/query | AUR visuals; adapter query | U table, E filters/actions, D pager |
| F16 Keyed details | AUR; adapter aggregate semantics | U QA only |
| F17 Paths/models | AUR neutral; adapter metadata | Separate U/D/E definitions |
| F18 Editing/dirty state | AUR | U core; E/D duplicate drafts |
| F19 Save/reconciliation | AUR lifecycle; adapter operation | U synthetic; E/D local saves |
| F20 Discard/leave | AUR boundary; app integration | U synthetic; E/D simple close |
| F21 Wire exact codec | ARP Angular or E compatibility | Different D/E codecs |
| F22 Metadata conversion | ARP Angular or E compatibility | D/E local parsers |
| F23 CREATE/update mapping | ARP Angular or E compatibility | Different D/E requests |
| F24 Transport/outcomes | ARP Angular; app transport context | D fetch, E RuntimeClient |
| F25 Contextual actions | AUR visuals; adapter operations | E effective actions |
| F26 Context/stale responses | App context; adapter lifetimes | D/E abort/generation guards |
| F27 Router/domain screens | ERBAS/application | E routing/overrides |
| F28 Auth/backend policy | ERBAS/application | E; separate D token policy |
| F29 Explorer/fixtures/locale | Demo host; reusable requests extracted | D |
| F30 Test harnesses/evidence | Demo/QA in respective repositories | U testbed, D/E tests |

Complexity estimates are relative: **L** isolated mapping/port work, **M** multiple public interactions,
**H** protocol or lifecycle parity requiring independent evidence. Each record identifies source, current use,
equivalence/reuse, public surface, gap and regression gate. These gates apply before deletion or extraction.

## 3. Functional and visual capability inventory

### 3.1 Theme, shell and navigation

**F01 — Theme registry, resolution and registration.** Source U-src:`theme/theme-runtime.ts`,
`theme/theme-definition.ts`, `theme/optional-controls.ts`; E-app:`core-fe/themes/`;
D:`src/main.ts`, `src/app.ts`. Active in all consumers at their respective pins. Owner: AUR mechanism,
application selection/registration. Public: `provideThemeRuntime`, `ThemeRegistry`, `ThemeService`, `ThemeResolver`.
Reuse U directly; E registers imported themes, not an independent replacement registry. Gap: old/new APF compatibility.
Regression: unknown themes, fallback, duplicate registrations, one registry instance and exact installed peers.
Complexity L for selection, M for atomic six-package adoption; depends on provenance and F03.

**F02 — Five themes and semantic renderers.** Source U:`packages/themes/{default,alternative,cyberpunk,vintage,
high-contrast}/`, U-src:`field-types/renderer-context.ts`; E-app:`core-fe/field-types/normalized-field-types.ts`,
`field-renderer-outlet.ts`. Active in E forms and U QA; D CRUD uses its own native controls inside themed shell.
Owner: AUR visual contracts/themes; protocol type mapping belongs to the adapter. Public: `ThemeDefinition`,
`ThemeArtifact`, `THEME_ARTIFACTS`, `FieldRendererContext`, `FieldRenderer`, `FieldValue`.
Reuse renderers, not E's obsolete artifact references. Gap: semantic lossless bridge (F08), type revision mapping.
Regression: all five installed packages, fourteen current mandatory artifacts, CSS-only/structural fallback,
read-only/disabled behavior, exact input and High Contrast large controls. Complexity M; depends F01/F08.
Do not expand or replace the mandatory artifact catalogue as part of adapter extraction.

**F03 — Shell, panels, regions and retained ownership.** Source U-src:`structure/theme-outlets.ts`,
`theme-ports.ts`, `retained-focus.ts`; D:`src/app.html`; E-app:`app.html`, `core-fe/shell/shell-extension-regions.ts`.
Active: shells in D/E, structural and form/grid frames in U QA. Owner AUR. Public: `ThemeShellOutlet`,
`ThemePanelOutlet`, `ThemeNavigationOutlet`, `ThemeRegions`, structural ports and optional `ThemeComponents`.
Reuse retained projected views; no new shell renderer in ARP Angular. Gap: comprehensive independent visual proof.
Regression: same owned DOM/component instance, input selection, subscriptions, focus and dirty state across themes,
missing named-region fallback and no duplicate projections. Complexity M; depends F01/F02.

**F04 — Legacy and typed navigation/menu rendering.** Source U-src:`menu/menu-definition.ts`, `menu-view.ts`,
`structure/link-activation.ts`; E-app:`app.ts`, R:`runtime-client.ts`; D:`src/app.ts`, `catalog.ts`.
Active: legacy tree in D/E, typed mode in U QA only. Owner AUR visuals; effective entries come from backend/adapter;
actual routes/actions belong to application. Public: legacy `ThemeNavigationItem`, `MenuDefinition`, `MenuPlacement`,
`snapshotMenus`, `composeMenus`, neutral selection and native-link activation ports.
Reuse typed menus where needed, preserving legacy single-tree mode without simultaneous injection.
Gap: real consumer typed-menu integration. Regression: same-kind menus, stable IDs, input ordering, cycles/duplicates,
exactly-once items, unsupported-region overflow, mobile keyboard/Escape/focus, native modified/target/download links.
Complexity M; depends F03 and application route policy. A resource catalogue must not imply a menu entry.

**F05 — Shell contribution discovery and slots.** Source E-app:`core-fe/shell/shell-extensions.ts`,
`shell-slot-outlet.ts`, `shell-extension-regions.ts`, `shell-slots.spec.ts`.
Active registry validates standalone components, unique IDs/slots and priority then ID ordering.
Owner: AUR neutral projection mechanism (already F03); ERBAS contribution registration, slot vocabulary and composition.
Public E-local: `ShellExtensionRegistry`, `provideShellExtensions`; no shared equivalent registry is required.
Reuse existing contributions through public regions. Gap: assess only specific missing neutral projection needs;
do not extract the whole app registry or merge it with menus. Regression: ordering, duplicates, lifetime and catch-all.
Complexity L/M; depends F03. This does not authorize a second theme or extension registry in ARP Angular.

### 3.2 Forms, controls, layout and feedback

**F06 — Neutral form composition.** Source U-src:`form/form-definition.ts`, `compose-form.ts`,
`form-composition.ts`, `form-contexts.ts`, `form-outlets.ts`.
Active U form/editor QA; absent from currently installed D/E APF. Owner AUR. Public: `FormDefinition`,
`FormComposition`, `composeForm`, field/collection contexts and `ValuePath`.
Equivalent E ResourceForm combines this responsibility with metadata, input state, relations and serialization;
D `remote/crud.html` is a simpler independent native renderer, not the same feature set.
Reuse U for layout/visual lifecycle; split adapters from E/D, do not rename their whole components into a library.
Gap: F08/F10/F12 and contextual parity F07. Regression: no-layout fallback, exclusions, duplicate/unknown refs,
ordered fields/actions, hidden containers, read-only and theme-preserved edits. Complexity H; depends F07–F12/F18.

**F07 — Tabs, sections, groups and contextual placement.** Source R:`resource-layout.ts`, `.html`, `.css`,
`contextual-presentation.ts`; U-src:`form/compose-form.ts`, `form-composition.ts`.
Active E visual tabs with roving keyboard and native disclosure sections; U has neutral composition/reveal.
Owner AUR visual primitives; ARP Angular ARP layout interpretation; E retains v0.14 context selection/exclusions.
Public U: `FormLayout`, `LayoutTab`, `LayoutSection`, `LayoutGroup`, context actions and presentation frames.
Reuse U after mapping, not raw metadata passthrough. Not equivalent automatically: explicit contextual field subsets,
action scopes/fallback, absent versus empty layout and E pruning rules need comparison tests.
Gap: exact parity matrix and supported custom insertion F12. Regression: LIST/CREATE/EDIT/VIEW independently,
explicit empty forms, first placement, eligible fallback, exclusions never resurrected, keyboard/reveal/state.
Complexity M/H; depends F06/F15/F25.

**F08 — Lossless scalar editing and semantic widgets.** Source U-src:`editor/document-input.ts`,
`form/form-field-renderer.ts`, `field-types/renderer-context.ts`; R:`fields.ts`, `resource-form.html`.
Active U editor uses neutral text/checkbox bridge; E uses themed scalar widgets; D uses native text/checkbox/null.
Owner AUR interaction, adapter type/constraint interpretation. Public: `EditingInput`, `documentInput`,
`FormFieldEdit`, `DetailGridEdit`; legacy scalar `valueChange` remains supported.
Reuse lossless channel and existing theme widgets where representable. They are not currently one complete path:
bridge bypasses semantic widgets, offers explicit Unset/Set null/Empty text, and rejects optional-control opt-in.
ENUM is currently text in that bridge; BINARY file UX and semantic temporal controls are not proved by it.
Gap: opt-in semantic widgets must retain absence/null/empty/raw, unknown enum/raw values, booleans and exact strings.
Regression: one intent/channel, no coercion, invalid intermediate input, readonly suppression, labels/errors/focus
and five themes. Complexity M per widget; depends F02/F18. Do not replace with Number-based HTML numeric editing.

**F09 — Optional semantic control selection.** Source U-src:`theme/optional-controls.ts`,
`form/form-field-renderer.ts`; U:`apps/testbed/src/rating*.ts`.
Active opt-in finite-choice/rating QA, not E's MANY_TO_ONE. Owner AUR. Public: `ControlRequest`, `ControlDomain`,
`ControlPresentation`, optional control definitions/resolution via existing theme registry.
Reuse capability negotiation/fallback; do not treat the rating example as a universal relation selector.
Gap: lossless input support and evidence for expanded domains. Regression: unsupported request, fallback,
non-disclosure diagnostics, domain fit, disabled and exact values. Complexity M; depends F08, no new registry.

**F10 — MANY_TO_ONE selector.** Source R:`resource-form.ts`, `.html`, `models.ts`, `runtime-client.ts`.
Active E: target metadata/list lookup, bounded pages, previous/more, exact identifier comparison,
and preservation/display of a selected key outside the current page. No equivalent public AUR relation widget;
a string ENUM or optional rating is not equivalent.
Owner AUR generic accessible selector and focus/paging intents; ARP Angular interprets ARP relations and fetches
options only when contracted; E v0.14 adapter retains current transport/mapping until replacement is proved.
Public now E-local only. Gap: neutral choice identity/value/label/unknown-current/busy/error ports, not HTTP in AUR.
Regression: exact keys, missing selected page, null/absence, stale lookup, immutability, keyboard/mobile/theme state.
Complexity H split into visual M and protocol M; depends F08/F24/F26. No invented ARP relation wire format.

**F11 — Read-only, immutable, disabled and generated fields.** Source R:`fields.ts`, `resource-form.ts`;
D:`remote/crud.ts`, `.html`; U-src:`state/document-state.ts`, `editor/document-bindings.ts`.
Active all, with different semantics: D locks keys on edit, E distinguishes readOnly from immutable,
U applies neutral inherited capabilities. Owner AUR rendering/enforcement of supplied flags;
adapter derives flags and excludes non-writable request fields; backend remains authority.
Public U flags already available. Reuse core locks; do not infer generated fields from a name like `id`.
Gap: protocol-specific generated/default semantics and projection tests, not extra theme policy.
Regression: CREATE immutable input permitted where contracted; UPDATE immutable omitted even unchanged;
readonly submitted events rejected; disabled inherited collections; generated omission and authoritative value.
Complexity M; depends F18/F22/F23.

**F12 — Custom components, objects, dialogs and workspace interaction.** Source U-src:`form/form-definition.ts`,
`structure/theme-ports.ts`; U:`apps/testbed/src/editor.ts`, `document-protection.ts`;
E-app:`core-fe/shell/`, specialized screens; D delete confirmation markup.
Active shell TemplateRef regions and compiled custom screens; U document tree supports nested objects/collections.
These are not a public arbitrary complex-object editor, form custom-component slot catalogue or reusable dialog API.
Owner AUR neutral visual primitives; application owns component implementation, dialog decision and workspace policy.
Public: shell regions, form/grid frames, reveal APIs and async discard boundary; no generic dialog export.
Gap: scoped form insertion with retained ownership and accessible dialog/focus contract when required;
objects must not be advertised as fully editable widgets merely because state supports an object node.
Regression: manual screen and declarative form share visuals, three tabs, insertion lifetime, dialog focus trap/return,
multiple errors and readonly mixed controls, five themes. Complexity M per primitive; depends F03/F06/F20.

**F13 — Local scalar and document validation.** Source U-src:`validation/validate-field.ts`,
`validate-document.ts`, `scalar-values.ts`, `temporal-values.ts`, `portable-pattern.ts`;
R:`fields.ts`, `resource-form.ts`; D relies on native required checks and server validation.
Active U validator/editor QA; E own lexical/range checks; D no equivalent complete local validator.
Owner AUR neutral validation engine; ARP Angular supplies truthful plans and deferred server checks.
Public: `validateField`, `validateDocument`, validation plan/result/issue types.
Reuse U for supported constraints, not duplicate E scalar parsing inside ARP Angular indefinitely.
Gap: protocol dialect/limit parity; unsupported regex/constraints must defer or explicitly prevent unsupported use,
never produce invented success. Regression: all eleven types, integer width/sign, exact decimal bounds/scale,
Unicode length, temporal profiles, binary/enum/UUID, unsafe pattern handling, nested paths and definition errors.
Complexity H for semantic mapping, L for calling public validator; depends F21/F22.

**F14 — Error presentation, summary, reveal and focus.** Source U-src:`editor/document-bindings.ts`,
`form/form-composition.ts`, `grid/grid.ts`; U:`apps/testbed/src/editor.ts`;
R:`resource-form.html`, `resource-screen.ts`; D:`remote/crud.html`.
Active U associated feedback/summary example and typed-path reveal; E maps server field codes to messages;
D exposes raw JSON result, not multiple associated field errors. Owner AUR visual feedback/reveal;
adapter maps server diagnostics, application localizes and chooses summary policy.
Public: context `feedback`, `invalid`, `describedBy`, `EditorFeedback`, `revealField`, `revealPath`.
Reuse these ports. Summary markup and accessible discard dialog in U are currently fixture-owned, not public components.
Gap: reusable summary/dialog only where needed; server multi-error mapping must retain unknown/root issues;
help/touched policies, hidden columns and comprehensive assistive review remain incomplete.
Regression: multiple field errors, root/row/collection messages, inactive tab/collapse opening, first invalid focus,
retained raw input, server versus local/deferred distinctions. Complexity M; depends F13/F18/F24.

### 3.3 Lists, collection editing and state

**F15 — Lists, filters, sorting and pagination.** Source R:`resource-screen.ts`, `.html`, `runtime-client.ts`;
D:`remote/crud.ts`, `.html`; U-src:`grid/grid.ts`, `grid-definition.ts`.
Active E has typed filters, AND composition, sorting priorities, pagination/selection; D bounded page/limit/next table.
Owner AUR table/selection/filter-control visuals; ARP Angular contracted query and list orchestration;
ERBAS retains existing query dialect and application policy. Public: `ListGrid`, `ListGridContext`, `GridColumn`.
Reuse table where feature parity allows; `ListGrid` is a read-only projected table, not a server list/filter engine.
Gap: no proven replacement for all E filter/selection/action/pager UX. Keep that UI until generic ports exist.
Regression: query serialization, offsets/limits, all filters/sorts, empty pages, selection limits, exact cells,
context switching and mobile scroll. Complexity H; depends F24/F25/F26, avoid premature list rewrite.

**F16 — Editable keyed collections.** Source U-src:`grid/grid.ts`, `grid-definition.ts`,
`editor/document-bindings.ts`; U:`apps/testbed/src/editor.ts`, `grid.ts`.
Active U QA with two independent detail collections and a nested collection; no current E flat CRUD equivalent.
Owner AUR visual grid and state operations, adapter aggregate save semantics only when backend supports them.
Public: `DetailGrid`, row/column/collection contexts, add/remove/move/cell intents and lossless grid edit.
Reuse directly. Gap: columns address immediate row fields; deeper collections require independent full-path definitions;
no spreadsheet engine, hidden-column reveal or aggregate HTTP contract. Do not flatten rows into unapproved CRUD writes.
Regression: stable UI keys distinct from server identity, order, duplicate values, add/remove/reorder, nested raw edits,
capabilities and row/collection feedback. Complexity M UI, H for any future aggregate backend adapter; depends F18/F19.

**F17 — Paths and neutral definitions.** Source U-src:`form/value-path.ts`, `form/form-definition.ts`,
`state/document-state.ts`; R:`models.ts`; D:`remote/crud-protocol.ts`.
Active distinct definition models, not interchangeable schemas. Owner AUR `ValuePath`/visual/state models;
ARP Angular metadata-to-model conversion; ERBAS retains published wire types.
Public U: typed property/row segments and path keys. Reuse typed paths, never labels or display indexes as identity.
Gap: protocol error-path decoding and stable field/collection IDs. Regression: repeated labels, nested row paths,
invalid references, key mapping after accepted responses and strict unsupported metadata diagnostics.
Complexity M; depends F06/F16/F24. No application metadata contract is added to AUR.

**F18 — Immutable document state and exact dirty tracking.** Source U-src:`state/document-state.ts`,
`exact-numeric.ts`, `numeric-syntax.ts`; R:`resource-form.ts`; D:`remote/crud.ts`, `crud-protocol.ts`.
Active U sole-tree core; E mutable values plus changed Set; D draft plus selected baseline and lexical diff.
Owner AUR. Public: `DocumentObject`, `DocumentField`, `DocumentCollection`, `EditingInput`, `DocumentChange`,
`createDocumentState`, `applyDocumentChange`, `resetDocumentState`, `exactNumericEqual`.
Reuse U, remove old mutable trees only when integration proves parity. Numeric effective equality differs from
E/D lexical comparison; do not silently change sparse-patch behavior without protocol/consumer tests.
Gap: legacy presence projection E `fieldValue(undefined)` becomes null, D initializes every CREATE field;
neither is lossless absence semantics suitable for blind extraction. Regression: absent/null/empty/raw,
exact integer/decimal equality, invalid drafts, revision, nested operations and readonly. Complexity H integration.

**F19 — Save lifecycle and editor binding.** Source U-src:`state/document-session.ts`,
`editor/document-bindings.ts`; R:`resource-screen.ts`; D:`remote/crud.ts`.
Active U synthetic save/reconcile/recovery QA; E and D close editor/reload list after success rather than reconcile
an AUR session. Owner AUR neutral lifecycle; ARP Angular transport/result adapter; application screen composition.
Public: `DocumentSession`, `bindDocumentEditor`, `applyDocumentFieldIntent`, `applyDocumentCollectionIntent`,
`submit`, `resolve`, `recover`, `subscribe` and immutable attempt/result types.
Reuse core; derived contexts are projections, not another editing store. App/adapter owns subscriptions,
row preparation/defaults/keys, plans and conversion of a complete accepted snapshot.
Gap: no real ARP/ERBAS integration with this API; successful HTTP alone cannot clean a session.
Regression: invalid submit, duplicate/save locks, authoritative returned values, missing partial response -> recovery,
rejection/conflict retention, stale attempts, uncertain outcome without automatic replay. Complexity H; depends F18/F24.

**F20 — Discard, leave and unload protection.** Source U-src:`state/document-session.ts`,
`state/navigation-protection.ts`; U:`apps/testbed/src/document-protection.ts`; E/D cancel handlers and context resets.
Active U tested synthetic adapters; E/D currently close drafts without a universal unsaved-change guard.
Owner AUR decision boundary; application Router/history/dialog/backend-switch/logout policy.
Public: `requestDiscard`, `NavigationProtection.requestLeave`, explicit SSR-safe `protectBeforeUnload`.
Reuse async revision/lifecycle rechecks and lock/duplicate protection. Gap: actual Router/app interception still
consumer-owned and unproved; forced authentication invalidation cannot retain cross-context protected data.
Regression: cancel preserves all state/focus, confirm accepted baseline, stale confirmations, concurrent leave,
saving/recovery blocks, route/Back/programmatic transitions, explicit listener disposal.
Native browser prompts/mobile lifecycle events cannot be guaranteed. Complexity M per consumer; depends F19/F26.

### 3.4 Protocol, orchestration and application composition

**F21 — Exact JSON codecs.** Source R:`exact-json.ts`; D:`remote/crud-protocol.ts`, `dictionary.ts`.
Active E `ExactNumber` parser/writer and D source-aware number wrapper/raw descriptor text. Owner ARP Angular for
ARP codec; E compatibility adapter for ERBAS JSON-number codec; generic document exact equality remains AUR.
Public now local helpers only. Reuse algorithms/tests only after comparing required grammars and limits.
They are not equivalent: E emits contractual JSON numeric tokens; D scalar numerics are strings,
`ExactJsonNumber.toJSON()` emits a string for metadata display, and D requires reviver source support.
Gap: no shared approved protocol codec; parser limits/duplicate-key policy must not be weakened.
Regression: UINT64-sized text where supported, INT64, long DECIMAL, fractional metadata rounding to integers,
exponents, duplicate keys, bounds and malformed input. Complexity M per codec, H to unify; depends section 6.

**F22 — Effective metadata and constraint interpretation.** Source R:`models.ts`, `fields.ts`,
`contextual-presentation.ts`; D:`remote/crud-protocol.ts`, `protocol.ts`.
Active E closed v0.14 parsing; D strict recognized adapter shapes and capability intersection.
Owner ARP Angular for ARP, protocol-specific ERBAS compatibility at the app seam initially.
Public shared API absent. Reuse strict parsing approach and fixtures, not wire interfaces wholesale.
Gap: stable common ARP resource/form transport not approved, current INTEGER revision adoption differs from old hosts.
Regression: missing/unknown constraints, duplicates, malformed definitions, readOnly/immutable/default/presence,
all effective types and layout exclusions, unsupported capabilities reported before editing. Complexity H; gates
F13/F23.

**F23 — CREATE/defaults and sparse UPDATE/PATCH.** Source R:`resource-form.ts`, `fields.ts`, `runtime-client.ts`;
D:`remote/crud.ts`, `crud-protocol.ts`; C:`docs/features/arp-crud-001a.md` and write fixtures.
Active E flat POST/PATCH and D invoke CREATE/UPDATE with baseline. Owner ARP Angular ARP operation builder;
ERBAS codec/semantics remain a distinct adapter. AUR submission is an editing snapshot, not either request body.
Reuse session/validation, add protocol-specific diff/omission mapping; no second dirty tree.
Gap: D's all-fields initial CREATE cannot preserve omitted defaults generically; E's changed Set needs replacement
with tested presence-aware projection. Regression: omitted/default/null/empty, readonly and immutable filtering,
unchanged fields absent, exact tokens/strings, no upsert or invented identifier/token. Complexity H; depends
F18/F21/F22.

**F24 — Transport, response and error/conflict adaptation.** Source D:`remote/crud.ts`, `dictionary.ts`,
`protocol.ts`; R:`runtime-client.ts`, `models.ts`, `resource-screen.ts`.
Active fetch demo versus RxJS HttpClient ERBAS. Owner ARP Angular contract-specific ports and orchestration;
application supplies backend/auth context; backend owns final enforcement.
No public ARP Angular API yet. Reuse cancellation/generation discipline, validation and definite/uncertain distinction;
Retain actual payload semantics. E metadata ETag is not record concurrency; D baseline comparison is not a
version token.
Gap: multi-issue typed paths, complete authoritative snapshots/recovery and negotiated supported profiles.
Regression: 400/401/403/404/409, malformed envelopes, transport loss, stale responses, no uncertain write retry,
missing fields, unchanged drafts and no cross-session cache reuse. Complexity H; depends section 6/F19/F26.

**F25 — Contextual actions and operation availability.** Source R:`contextual-presentation.ts`,
`resource-screen.ts`, `resource-layout.ts`, `runtime-client.ts`; U-src:`form/form-definition.ts`.
Active E entity/collection/selection actions, parameter forms, effective availability and refresh;
D only five advertised CRUD operations. Owner AUR neutral buttons/placement, ARP Angular ARP operation mapping,
ERBAS context selection/policies and existing v0.14 adapter. Public U `ContextAction` and action intent ports.
Reuse visual action ports; no assumption ARP drafts equal ERBAS actions.
Gap: list selection/pager visual parity and ARP formal action contracts. Regression: unavailable/unauthorized omission,
module enablement, scopes, parameter required/readonly behavior, no lost action-only containers or duplicate activation.
Complexity H; depends F07/F15/F22/F24; not a reason to remove working E contextual controls early.

**F26 — Backend/session context and stale response prevention.** Source E-app:`auth-session.ts`,
`backend-selection.ts`, R:`runtime-client.ts`, `resource-screen.ts`,
`resource-form.ts`; D:`src/app.ts`, `remote/dictionary.ts`, `remote/crud.ts`.
Active E backend/context epochs, cancellation and cache invalidation; D AbortController plus sequence guard and
in-memory credential clearing on runtime/URL/disconnect. Owner application auth/backend choice;
ARP Angular context-scoped request/cache lifetime. Public shared API absent.
Reuse generation check pattern, not app login state inside library. Gap: coordinate optional leave guard with
mandatory invalidation; abort alone cannot establish server rollback. Regression: delayed metadata/list/lookup/save,
same backend new session, logout, wrong identity, zero stale data/credentials, forced 401 versus voluntary leave.
Complexity H; depends F20/F24; no persistence of credentials in shared layer.

**F27 — Routing and specialized screens.** Source R:`resource-routing.ts`, E-app:`app.ts`, route registration and
compiled authentication/users/assistant screens. Active generic `ResourceScreen` fallback with `RESOURCE_SCREENS`
NgComponentOutlet overrides and explicit manual routes; native link interception is application-owned.
Owner ERBAS (and each independent application). Public E extension tokens remain local.
Reuse routes and compiled screen override seam; do not move Router or domain screens into AUR or auto-register
routes from metadata. Gap: consume adapter facade without changing route policy.
Regression: generic fallback, specialized override, unknown paths, link gestures, existing auth/users/assistant
and unsaved guards. Complexity M; depends F20/F24; excludes complete client architecture rewrite.

**F28 — Authentication, backend configuration and application policies.** Source E:`app/src/app/` auth,
login/backend selection, HTTP service/proxy configuration and protected feature tests.
Active production application composition. Owner ERBAS; demo bearer token input remains a demo host policy.
No equivalent needed in AUR or a mandatory ARP login system. Reuse application injection of credentials/context
without exposing it in visual models. Gap: agree smallest injected transport/context port, not new endpoints/headers.
Regression: login/logout, 401 clears versus 403 preserves ERBAS auth, backend selection and feature availability.
Complexity L extraction exclusion, M integration; depends F26/F27.

**F29 — Demonstration host, localization and fixture explorer.** Source D:`src/app.*`, `catalog.ts`,
`src/i18n/`, `scripts/assets.mjs`, `config/instances.json`, `bin/`, `tests/`.
Active static contract explorer, per-runtime URL input validation, ES/EN fallback/persistence and fixture downloads;
separate live dictionary and PHP CRUD panels. Owner demo for catalogue/fixtures/workflow; application owns its
language policy. Reusable ARP dictionary/CRUD request logic belongs in ARP Angular despite originating here.
No shared localization framework is required. Gap: demo must consume shared visuals/adapter without losing source
bytes, translated states or disconnect behavior. Regression: exact assets, URL credentials/scheme rejection,
blocked storage, language changes retaining draft/theme/session, actual advertised capabilities only.
Complexity M; depends F03/F24. Do not distribute demo as the library or enable fixture execution implicitly.

**F30 — QA, packaging and contract evidence.** Source U:`apps/testbed/`, `tests/`, `bin/{test,check,pack}`,
`docs/contracts/ui-runtime-v1-acceptance.md`; D:`tests/`, `bin/integration-*`, `VALIDATION.md`;
E tests beside R/core-fe and `tests/test_theme_packages.py`, live proof sources and QA docs.
Active isolated APF consumers and protocol-specific tests. Owner demo/QA; each library owns its own verification.
Reuse evidence and fixtures without modifying their original meaning. Gap: independent current-APF consumer,
formal ARP host interoperability and comprehensive human visual/assistive review.
Regression: installed public exports only, reproducible peers/archives/locks, all five themes, desktop/mobile,
owned-DOM/focus invariants and clean disposable data/container lifecycle. Complexity M baseline, H real-host matrix.

## 4. Duplication: what to reuse and what to retain

The records above distinguish equivalents by behavior, not name. The concrete consolidation decisions are:

| Existing pair | Reusable part | Part that cannot be substituted directly |
| --- | --- | --- |
| ResourceForm / FormComposition | U layout, bindings, controls | E metadata, relations, payload/defaults |
| ResourceLayout / U composition | Containers, fallback/reveal | Context pruning and effective actions |
| E field outlet / U renderers | Public themed components | Old artifact IDs and scalar-only edit projection |
| D CRUD markup / U editor | Controls, grid, state, feedback | PHP discovery, invoke, baseline/delete |
| ResourceScreen / CRUD facade | Query/save/action patterns | Router, overrides, ERBAS context/wire |
| E / D exact JSON | Exact-source parsing techniques and tests | JSON-number codec versus portable string codec |
| E / U local validation | U neutral supported scalar validation | ERBAS server dialect/limits and issue mapping |
| E/D drafts / DocumentSession | U editing tree/save lifecycle | Protocol projection, accepted response |
| E/D navigation / U menus | Neutral renderers and link intents | Effective entries, routes and manual catalogue |
| E extension registry / U regions | Public retained projection | App contribution registration and slot policy |

Keep all working E relation, action, query and specialized-screen paths until feature-level replacement tests pass.
Unsupported metadata must enter an explicit, documented compatibility path or a clear unsupported-state view.
That path must preserve controls and constraints, not replace a relation with unrestricted text or omit actions.
Temporary legacy use must have a tracked removal gate; no new generic renderer should be built there.

## 5. Required AUR API work and current acceptance limits

The initial adapter tranche must use public `FormComposition`, `DocumentSession`, `bindDocumentEditor`,
`validateDocument`, grids and theme outlets. No new document/validation/theme engine is justified.
Needed gaps should be separate changes with neutral contracts, not an umbrella “finish AUR 1.0” project:

1. Complete lossless semantic editing incrementally, starting with ENUM choices through existing themed controls.
   Preserve unsupported/current raw values, absence/null/empty, exact text and legacy ports. Optional-control
   lossless support is a later explicit capability, not implicit acceptance by the scalar bridge.
2. Provide a data-only relationship/choice selector with paging/current-selection/busy/error/focus intents.
   ARP/ERBAS relation metadata, query and authorization stay outside AUR.
3. Add the smallest retained custom-component insertion contract inside form composition. Shell regions and
   compiled standalone screens do not prove insertion within tabs/groups. Nested object editing requires a separate
   supported scope; do not claim it from tree storage alone.
4. Promote generic summary/dialog interaction only where consumer needs require it. Existing feedback/reveal and
   async confirmation ports should remain the foundation; dialog decision and localization remain application-owned.
5. Close demonstrated visual gaps for list selection/filter/pager/action controls before replacing those E controls.
   Existing read-only ListGrid must not be presented as their complete replacement.
6. Extend the existing private U testbed: all implemented public controls observable, three-tab mixed form,
   multiple simultaneous errors, readonly states, custom insertion, keyboard/focus and dirty theme switching.
   Its current editor already proves three tabs, two details/nested rows and synthetic save/discard; extend that
   scenario rather than creating a permanent demo app. Only demonstrate objects when their public API exists.

Current acceptance at U's inspected revision: MENU-001/002 and STATE-003/004/006 are implemented;
MENU-003/004, STATE-001/002/005, FORM-001..003, GRID-001..003, FIELD-003, VALID-010 and THEME-004 remain partial.
ADAPTER-002 and ADAPTER-003 remain missing. Other FIELD/VISUAL requirements are not closed by this inventory.
Functional Chromium coverage is not human accessibility/visual certification or a real Router/backend proof.
No acceptance matrix or historical evidence is modified here.

## 6. Protocol boundaries and ERBAS compatibility

### 6.1 Current ARP demo HTTP adapters

D:`remote/protocol.ts` recognizes only `arp-demo-dotnet/1`, `arp-demo-java/1`, `arp-demo-php/1` and advertised
`dictionary.list`, `dictionary.describe`, `dictionary.validate`. Dictionary requests use `/demo/info`,
`/demo/dictionary/elements`, its element descriptor and `/validate` paths. These are demo host interfaces.
D preserves descriptors/results as text rather than round numeric metadata through browser numbers.

CRUD is specifically `arp-demo-php-crud/1`, enabled only for recognized PHP info advertising both `crud.metadata`
and `crud.invoke`. It uses authenticated `/demo/crud/metadata` and POST `/demo/crud/invoke` with
`{target, operation, inputs}`; operations are LIST, GET, CREATE, UPDATE, DELETE.
Records contain `{key, values}`; numeric scalar values are strings, booleans remain boolean, null remains null.
UPDATE supplies sparse changes plus baseline; DELETE supplies the complete displayed `confirmedValues`.
Responses distinguish success/conflict/rejected/failed. Conflicts require reload/reconfirmation, not overwrite.
A failed/uncertain write blocks repetition; page traversal is not a snapshot, and A→B→A is not detectable by
value comparison. D's parser must not be mistaken for a general exact JSON-number request writer.

These facts describe executable demo code, not a proposal to standardize its endpoints, token, envelopes or limits.
The approved decision explicitly leaves formal frontend/backend discovery, versions and wire contracts open.

### 6.2 Contract candidate versus backend implementation

[Dictionary/INTEGER](dictionary.md) is the active prepublication candidate; it deliberately replaces old integer
identifiers within `arp.dictionary/v1`, with no aliases or release. It includes unsigned 64-bit capacity as
`INTEGER` constraints. The [1.0 draft](contract-v1-draft.md) is not activated as a whole.
[CRUD writing](features/arp-crud-001a.md) remains a review candidate, not an approved wire format.
CDS physical/logical/projection, verified LIST/GET, services/invocation, modules and menus have preserved draft
specifications/fixtures; static verifiers do not demonstrate backend implementation or published transport.
The [review](review-contract-v1.md) and historical links preserve earlier guarantees rather than replacing them.

Historical host evidence in D:`INVENTORY.md`, `MULTIRUNTIME-HOSTS.md`, `DOTNET-HOST.md`, `CRUD-PHP.md`,
`VALIDATION.md` identifies these distinct implementation scopes:

| Host evidence | Revision | Demonstrated scope at that pin |
| --- | --- | --- |
| arp-dotnet | `442cd19556a3381d47e7e26b0351aa9ee567a791` | Dictionary HTTP demo, not CRUD |
| arp-java | `a76f2d59feb66eb2beca6e94c00814b3512f384d` | Dictionary HTTP demo, not CRUD |
| arp-php | `419cb8faa9f7775968e52e08688642fb416365f1` | Earlier dictionary HTTP demo |
| arp-php | `51c57cfbbe3953d460896d1a2e30b196329b5f58` | PHP/MariaDB CRUD demo plus dictionary |

The earlier dictionary libraries pin `4c0f4bd0337c01c15a036910b6462e6f0e674927`;
PHP's later write contract pin is `e3c2c08c93add63faebbe011a7e8e1ec3eccff2c`.
These are documentary implementation pins, not current backend main inspection or blanket conformance with C main.
The current client expects INTEGER; older recorded seventeen-type host evidence predates that change.
A future run must establish actual pinned host adoption before claiming compatibility. This task neither inspected
backend working trees nor started hosts; it does not infer Java/.NET CRUD from dictionary support.

### 6.3 Published ERBAS v0.14.0 is a different contract

E:`contract.revision`, `docs/client-runtime-001.md`, `client-runtime-002.md`,
`resource-presentation-001.md` and R:`models.ts`, `runtime-client.ts` identify immutable erbas-contract v0.14.0:
annotated tag `22191afb8ab477fef319093b8c212264f4019816`, target
`9919ad3725e50d63e7a19befbe0d81b4d91df0cc`.
The [published resource contract](https://github.com/alxarafe/erbas-contract/tree/v0.14.0/openapi/core/resources)
and its specification govern ERBAS, not D or future ARP drafts.

- ERBAS has `/api/meta/navigation`, resource metadata/contextual presentation, `/api/resources` CRUD and separate
  resource-action availability/execution. Application RuntimeClient owns HttpClient, caching and effective context.
- CREATE sends a flat field object; omissions preserve server defaults; null does not mean omission/default.
  PATCH is a sparse flat object, not ARP UPDATE's `{key,changes,baseline}` invocation.
- Exact integer/decimal values use contractual JSON numeric tokens through E's exact codec. v0.14.0 includes the
  seven historical integer types through INT64, not a UINT64 type. Test UINT64 in AUR/ARP only where supported;
  never claim ERBAS accepts it. Supported-type mapping can retain those exact domains without changing the wire.
- Static readOnly/immutable and presentation exclusions differ from effective action/navigation authorization.
  Field-level user authorization is not a v0.14.0 capability. Presentation never grants permission.
- LIST/CREATE/EDIT/VIEW contexts have identity/hash, strict shapes, exclusions/order and permitted legacy fallback
  only when specified. Only the presentation endpoint's contracted 404 permits its existing legacy fallback.
- Structured error codes/paths, HTTP statuses, action scopes and MANY_TO_ONE semantics require ERBAS decoding.
  Metadata ETags/definitionHash do not establish record concurrency; no If-Match or synthetic version is proposed.
- Successful POST/PATCH return validated rows to RuntimeClient. ResourceScreen currently closes/reloads, ignoring
  that row as an accepted editing baseline. New integration must map complete authoritative data to session.resolve;
  incomplete/uncertain results require explicit readback/recovery without automatically replaying a write.

E documents .NET adoption at `6c8cf72b5ceefd15411f24befa140bcf28b9e201` and prior live proof sources;
this is ERBAS .NET, not `arp-dotnet`. New Java compatibility is explicitly unclaimed.
No new real ERBAS proof was executed here, and none establishes a normative ARP transport.

### 6.4 Integration path without protocol equivalence

First ERBAS can adopt current AUR public editing interfaces through an application-owned v0.14 compatibility mapper
and its unchanged RuntimeClient. This is not yet ARP Angular adoption and must be named accordingly.
Once a supported ARP profile is approved and implemented, ERBAS may register that explicit backend adapter for
ARP-capable endpoints. Alternatively, an explicitly approved ERBAS compatibility entry point can adapt v0.14 into
shared orchestration while retaining its separate codec, error model, capabilities and tests.

That optional compatibility entry point is an unresolved packaging decision, not permission to label ERBAS as ARP.
Do not implement a speculative universal resource protocol or pass wire objects directly into AUR.
Select a profile explicitly from supported identity/capability evidence; unsupported/mismatched profiles fail visibly.
Do not invent negotiation, endpoint probing, permissions, version tokens or concurrency guarantees to bridge gaps.

## 7. Proposed minimum ARP Angular library boundary

**Location proposal, pending explicit approval:** a separate `alxarafe/arp-angular` repository producing
`@alxarafe/arp-angular`, leaving C:`demo/client/angular` as a separate private demonstration application.
A separately buildable package in another approved repository is possible; the choice is not settled by this inventory.
No library directory, manifest or public signature is created in this task.

Use one APF package initially, with internal modules rather than speculative public subpackages:

| Internal responsibility | Proposed public responsibility; names/signatures not yet approved |
| --- | --- |
| Profile/transport | Explicit supported profile, injected transport/context/cancellation, capability outcome |
| Intake/metadata | Validated effective definition and unsupported/invalid diagnostics |
| AUR mapping | Produce neutral FormDefinition, contexts/options, document and validation plan |
| Operations | Resource/query/action operations with protocol-specific request builders |
| Session orchestration | Own DocumentSession lifetime, derived bindings, submit/resolve/recover bridge |
| Codec/feedback | Exact wire conversion, typed ValuePath issues, conflict/uncertain outcome mapping |

The smallest first public slice should be a headless resource-editor facade plus explicit adapter/transport ports:
load a supported resource, expose AUR definition/session/derived snapshot, submit/cancel/recover and report status.
This is a responsibility sketch, not a new schema. Reuse exported AUR types and infer only documented capabilities.
Lists/actions/relations may be added in later independently tested slices; unsupported ones remain explicit.

AUR is a peer dependency (with an explicitly tested compatible range/revision policy); Angular peers likewise
follow APF conventions. The application registers themes once and chooses its own routes/auth/backend.
Do not bundle private AUR source, duplicate Angular/AUR instances, make themes mandatory adapter dependencies,
or rely on same-version rebuilt archive content without provenance. Any exact current pre-release pins must be
verified together through installed packages.

No adapter-owned form, field renderer, tab set, dialog renderer, visual validation, navigation shell, theme registry
or mutable draft tree is allowed. The facade can own session/subscriptions and request/cache lifetimes, but its
editing values come only from DocumentSession. Parsed metadata and derived read-only projections are not drafts.
Optional relation/list transport controllers contain request state, not competing document values.

## 8. Ordered, independently reviewable migration tasks

These are proposals, not authorization. Each item should fit a focused commit/PR; conditional tasks are activated
only by demonstrated consumer need. Preservation checks gate every replacement.

There are two ordering requirements: the task sequence places independent consumption at the end, while the approved
architectural decision requires independent consumption before ERBAS. Honor both with an initial independent
proof before ERBAS, then rerun/extend it as the final acceptance gate. Do not defer the decision's gate silently.

### Stage 1 — Preserve behavior and evidence

**CAP-BASE-001 — Freeze feature parity fixtures.** Target C/D and E in separate commits. Scope: capture existing
protocol/metadata/layout/lookup/action/lifecycle expectations using existing tests, with exact revision/package pins.
Precondition: this inventory reviewed. Public API: none. Acceptance: existing tests unchanged and passing, explicit
absence/default/context/conflict baselines, list of unsupported cases. Dependencies: none. Excludes production
refactoring, backend changes and rewriting historical evidence. Real-host evidence remains separate from mocks.

### Stage 2 — Close necessary AUR visual gaps

**AUR-EDITOR-ENUM-001 — Lossless themed ENUM editing (first proposed implementation task).** Target U.
Scope: connect the lossless editor channel to semantic ENUM selection through the existing visual/theme contracts;
retain invalid/unknown raw values and explicit absent/null/empty states without dual emission or coercion.
Preconditions: CAP-BASE-001 relevant baseline and approved minimal port design. Expected public API: smallest
backward-compatible renderer/edit capability extension if needed, reusing EditingInput and current theme registry.
Tests/acceptance: unit/type compatibility, installed-APF FormComposition and DetailGrid, legacy scalar mode,
readonly/disabled, correction/error association/focus, five themes and desktop/mobile Chromium.
Dependencies: F02/F08; no adapter required. Excludes HTTP, ARP metadata, optional-control rewrite, new artifacts,
relations, unrelated widget overhaul or package version changes. Run U `./bin/test`, `./bin/check`, diff checks.

**AUR-SELECTOR-001 — Neutral paged choice control.** Target U. Scope: generic current selection/options, exact value,
labels, paging/busy/error and user intents. Preconditions: E MANY_TO_ONE parity fixtures and approved neutral port.
API: public data-only selector integrated with existing themes/lossless edit channel. Tests: keyboard/current value
outside page, null/absence, stale displayed options, readonly, mobile/five themes and stable DOM ownership.
Dependencies: CAP-BASE-001, ENUM tranche. Excludes metadata/network/authorization and relation wire definitions.

**AUR-FORM-SLOTS-001 — Retained custom form insertion.** Target U. Scope: minimal typed slot/template insertion
inside existing layout, not replacement composition. Preconditions: missing insertion demonstrated against F12.
API: neutral insertion port. Tests: manual component retained through tabs/sections/theme changes, focus/order,
readonly mixed content and no duplicate projection. Dependencies: CAP-BASE-001. Excludes domain components,
arbitrary object engine and runtime-compiled templates.

**AUR-FEEDBACK-001 — Shared feedback interaction tranche.** Target U, conditional. Scope: smallest reusable
summary/first-invalid or dialog primitive absent from current public ports, retaining multiple/root errors.
Preconditions: API gap confirmed; use revealPath and existing async confirmation. API: neutral feedback/focus port,
not server error decoder. Tests: simultaneous errors, inactive tab/collapse, focus return, keyboard and five themes.
Dependencies: CAP-BASE-001. Excludes touched policy framework, Router and business messages.

**AUR-LIST-PORTS-001 — List interaction parity tranche.** Target U, conditional per missing primitive.
Scope: one selection/filter/pager visual port per reviewed change. Preconditions: compare F15 to E fixtures.
API: neutral contexts/intents. Tests: selection, narrow scrolling, large labels, disabled controls and theme lifetime.
Dependencies: CAP-BASE-001. Excludes query dialect/network and complete ResourceScreen replacement.

**AUR-QA-COMPOSITION-001 — Complete autonomous visual evidence.** Target U. Scope: extend existing private APF
QA to show each implemented API and required three-tab mixed/custom form, without invented object support.
Preconditions: relevant visual tranches pass. API: none beyond those tranches. Acceptance: simultaneous errors,
readonly, custom insertion, typed/legacy menus, grids, focus/keyboard/dirty state in five themes and mobile/desktop;
update only proven acceptance rows. Dependencies: required U tasks. Excludes ARP/ERBAS/HTTP/permanent demo application.

### Stage 3 — Extract ARP client logic without copying visuals

**ARP-PROFILE-001 — Approve adapter profile scope.** Target C, separate contract proposal/review task.
Scope: identify approved existing contracts and remaining discovery/resource/form/value/error/concurrency gaps
for the first adapter slice. Preconditions: backend implementation inventory at exact pins. Public API: only
explicitly approved contract/profile references; no endpoint invented by extraction. Acceptance: fixtures and
interoperability criteria distinguish demo/experimental versus approved profiles. Dependencies: CAP-BASE-001.
Excludes implicitly promoting demo HTTP, backend implementation and formalizing all future ARP features at once.

**ARP-ANGULAR-PACK-001 — Independent package scaffold.** Target proposed repository, only after location approval.
Scope: APF/public entry/peer dependencies and disposable consumer build. Preconditions: approved location and
first profile. API: bootstrap/ports for that slice only. Tests: one AUR/Angular instance, installed APF exports,
no source aliases, themes registered by consumer. Dependencies: required U tranches, ARP-PROFILE-001.
Excludes production demo code move, publication, release/version policy changes and visual components.

**ARP-ANGULAR-TRANSPORT-001 — Headless recognized adapter.** Target library. Scope: extract request lifetime,
capability checks and strict codec/intake for the explicitly selected profile from D, preserving protocol identity.
Preconditions: scaffold and profile scope. API: transport/context/profile ports and typed failures.
Tests: unsupported identity/capabilities, exact metadata/scalars, cancellation, stale generation and auth failure.
Dependencies: ARP-ANGULAR-PACK-001. Excludes UI and silent endpoint fallback; a demo-only profile stays named as such.

**ARP-ANGULAR-MAP-001 — Metadata to public AUR models.** Target library. Scope: supported scalar resource fields,
read-only/capabilities, presence/default rules, validation plan and form layout mapping. Preconditions: approved
profile descriptors and visual APIs. API: mapping result with explicit unsupported/deferred diagnostics.
Tests: every supported type/constraint, invalid definitions, exclusions, exact bounds, labels versus IDs and layout.
Dependencies: transport and required U tranche. Excludes relation/action capabilities not actually contracted.

**ARP-ANGULAR-EDITOR-001 — Session-backed CRUD editor slice.** Target library. Scope: create/read/update with
DocumentSession, bindDocumentEditor and protocol request projection; no second draft. API: headless editor facade,
status, submission/feedback and recovery boundary. Preconditions: metadata mapping and known write outcome model.
Tests: omissions/defaults, sparse changes, locks, duplicate prevention, rejection/conflict/raw retention,
complete acceptance versus readback, stale outcomes and no uncertain replay. Dependencies: mapping/transport.
Excludes Router/auth/theme selection, fabricated IDs/version tokens and DELETE semantics.

**ARP-ANGULAR-DELETE-001 — Preserved deletion preconditions.** Target library. Scope: selected profile's explicit
GET/confirmation/delete flow, distinct from discard. API: deletion request/decision/status ports, visual UI in AUR.
Preconditions: approved profile deletion semantics. Tests: displayed-state consent, concurrent change, cancel,
reload/reconfirmation and uncertain delete lock. Dependencies: editor/transport. Excludes generic overwrite policy.

### Stages 4 and 5 — Demo consumption and real implementing host

**ARP-DEMO-ADOPT-001 — Replace duplicate demo plumbing.** Target C/D. Scope: install library and current compatible
six AUR archives with provenance; use shared facade/visuals for the supported slice. Preserve separate dictionary,
explorer, ES/EN, token/session and fixtures. API: only library/public AUR imports. Preconditions: library tests pass.
Tests: existing browser assertions retained plus field-associated errors, guards and five-theme state continuity.
Dependencies: package/map/editor/delete and U QA. Excludes turning demo into library or modifying normative contracts.

**ARP-HOST-PROOF-001 — Real CRUD lifecycle.** Target C/D QA and implementing host evidence only.
Scope: disposable host/data at explicit backend/contract pins, metadata → editor → real transport → authoritative
result/readback → sparse update → conflict/rejection → delete. Preconditions: actual profile adoption established.
API: none. Acceptance: exact values/omissions, no lost fields, no uncertain retry, cleanup and artifact manifest;
report absent host capability as pending. Dependencies: demo adoption. Excludes blanket Java/.NET claims from PHP.
No backend code change is authorized by this proof task; a missing capability needs a separate backend task.

**ARP-CONSUMER-PROOF-001 — Independent pre-ERBAS gate.** Target disposable third-party Angular consumer, location
separately approved. Scope: installed APF metadata CRUD plus manual AUR screen with shared controls, five themes
and one new third-party theme. API: existing public library surfaces only. Preconditions: real-host proof and U QA.
Tests: lifecycle, keyboard/focus, theme switching/owned DOM, no source imports and one registry/state engine.
Dependencies: ARP-HOST-PROOF-001. Excludes modifying reference apps or treating U testbed/D as independent evidence.

### Stages 6 and 7 — ERBAS adoption and removal after parity

**ERBAS-AUR-ADOPT-001 — Atomic APF/type adoption.** Target E. Scope: six archives, provenance/integrity and
historical integer-to-current-artifact mapping without changing ERBAS wire types. Preconditions: current U checks
and CAP baseline. API: existing AUR exports. Tests: installed peers/declarations, five themes and full existing
client regressions. Dependencies: U tranches; perform as the first E migration commit after independent gate.
Excludes unrelated dependency updates, source aliases or assuming same version means same bytes.

**ERBAS-EDITOR-MAP-001 — v0.14 compatibility projection.** Target E initially. Scope: pure metadata/presence/plan/
context-layout and sparse exact request mapping around unchanged RuntimeClient. API: application-owned mapper,
not normative ARP metadata. Preconditions: explicit compatibility path from section 6 approved.
Tests: published scalar domains/defaults/immutability/nullable, closed errors/layouts and existing exclusions.
Dependencies: APF adoption and independent gate. Excludes new protocol, resource-specific exceptions and UI copies.

**ERBAS-EDITOR-SWAP-001 — Session-backed generic form.** Target E. Scope: replace ResourceForm's values/changed
store with shared session/visuals for supported metadata; preserve action parameter forms/relations via tested
compatibility routing. API: current ResourceScreen route/override seam plus shared facade where protocol-compatible.
Preconditions: mapping and controls pass. Tests: CREATE/VIEW/EDIT, multiple errors, exact sparse save/acceptance,
recovery, cancellation, themes, all old form tests plus new installed-APF tests. Dependencies: mapper and F10 parity.
Excludes rewriting lists/auth/specialized screens or removing unsupported working controls.

**ERBAS-LIFECYCLE-001 — Actual leave and context integration.** Target E. Scope: app Router/Back/discard boundary,
voluntary backend/resource/logout protection and mandatory context invalidation with stale response isolation.
API: existing AUR leave ports plus application guards/dialogs. Preconditions: session editor.
Tests: canceled route retains focus/data, confirmed discard, save/recovery locks, forced 401 clears protected data,
late lookup/save/metadata responses cannot cross contexts. Dependencies: editor swap. Excludes Router in libraries.

**ERBAS-LIST-ACTIONS-001 — Complete shared slice adoption.** Target E and library in separate changes.
Scope: one supported list/query/action/relation slice at a time, preserving effective scopes/contextual layouts.
Preconditions: explicit matching backend profile or approved v0.14 adapter, visual parity APIs and existing tests.
API: incremental headless operation ports and AUR controls only. Tests: filters/sorts/pagination/selections,
parameter forms, availability, MANY_TO_ONE current key, specialized overrides. Dependencies: relevant U ports,
editor/lifecycle. Excludes pretending distinct protocols have equivalent actions or deleting incomplete paths.

**ERBAS-DEDUP-001 — Remove only replaced duplicates.** Target E; D cleanup separately.
Scope: delete one proven redundant visual/state/mapping implementation per change; retain required app adapters.
Preconditions: old and replacement behavioral tests, installed-package and real/backend evidence for the slice.
API: no new public contract. Tests: full regression plus search proving no consumers remain and package separation.
Dependencies: relevant swap/lifecycle/list slices. Excludes removal by name similarity or blanket legacy rewrite.

### Stage 8 — Final independent acceptance

**ARP-CONSUMER-PROOF-002 — Independent regression after migration.** Target independent consumer/proof record.
Scope: repeat pre-ERBAS proof on final pinned packages and new theme, including any API additions from migration.
Preconditions: replacement/removal tests pass. API: public exports only. Tests: same lifecycle plus absence/default/
exact values, multiple errors, routing owned by consumer and no ERBAS dependency. Dependencies: consumer proof 001
and completed migration tranches. Excludes publication, all-backend conformance claims or forced completion of AUR 1.0.

## 9. Preservation and regression strategy

Every migration slice must carry the following behavioral gates; missing evidence blocks removal, not documentation:

- All five themes, CSS-only and structural variation, fallback, High Contrast large controls, desktop/mobile widths,
  long labels, keyboard/focus and stable owned component/DOM state while dirty or saving.
- Existing ERBAS login/backend selection, navigation, contextual layouts/actions, filters/sorts/pagination,
  MANY_TO_ONE, generic and specialized compiled screens and application authorization boundaries.
- Existing D dictionary/fixture explorer, ES/EN, URL selection, token clearing, live PHP CRUD, delete consent,
  conflict reload, uncertain write lock and byte-exact downloadable assets.
- Create/read/update/delete, exact integers/decimals with no arbitrary Number conversion, absence/null/empty/raw,
  defaults/omissions, sparse updates, readonly/immutable and key/order preservation.
- Local/deferred/server diagnostics remain distinct; multiple field and root errors accessible, hidden fields
  revealed without deleting drafts. No client valid flag substitutes for backend authorization or acceptance.
- Canceled leave/discard preserves values/revision/keys/focus; stale confirmations cannot reset later edits.
  Backend/session invalidation prevents stale protected data even when browser requests were aborted late.
- Save attempts cannot duplicate or clean on HTTP status alone. Complete authoritative reconciliation or explicit
  recovery must be proved; unknown outcome cannot be automatically retried. No new concurrency guarantees inferred.

Use small pure adapter tests for parsing/projection, public type tests for compatibility and installed APF component
integration for visual behavior. Unit fixtures should include arbitrary identifiers/repeated labels, not only demo
field names. Do not weaken old assertions; replace internal-detail assertions only with stronger behavioral evidence
in a separately reviewed change. Keep backend contract fixtures independent of rendering implementation.

U's `./bin/test` and `./bin/check` run through ephemeral Docker and cover reproducible install, types, unit/browser,
production APF/package checks and disposable Angular consumer. Future U changes must run both.
D uses `demo/client/angular/bin/run check`, `bin/integration-multiruntime` and `bin/integration-crud` with documented
paths/pins and Docker. E uses its AGENTS-prescribed workflows including `./bin/test`/`./bin/check`; if developer-run
long validation is required, obtain the actual result and exact command before marking a task complete.
No Node/npm/Angular installation on the host is needed for any implementation tranche.

### Existing regression entry points

Use these inspected assertions as the starting map, not as newly executed test results:

- F01–F05: U `tests/theme.test.mjs`, `structure.test.mjs`, `link-activation.test.mjs`, `menus.test.mjs`,
  `tests/browser/specs/{composition,navigation,menus}.spec.mjs`; E-app `core-fe/shell/shell-slots.spec.ts`,
  `core-fe/theme/theme-runtime.spec.ts`, field outlet tests and E `tests/test_theme_packages.py`.
- F06–F14: U `tests/form.test.mjs`, `optional-controls.test.mjs`, scalar/decimal/temporal/pattern validation tests,
  `document-validation.test.mjs`, `editor-bindings.test.mjs` and installed browser form/validation/editor scenarios;
  R `presentation.spec.ts`, `contextual-presentation.spec.ts`, `contextual-ui.spec.ts`, `resource-ui.spec.ts`.
- F15–F20: U `tests/grid.test.mjs`, `state.test.mjs`, `document-session.test.mjs`,
  `document-protection.test.mjs`, `editor-bindings.test.mjs`, public type probes under `tests/fixtures/` and browser
  grid/state/document-save/document-protection/editor specs; R `resource-ui.spec.ts` and `runtime-client.spec.ts`.
- F21–F29: D `tests/unit/{protocol,crud-protocol,i18n}.test.mjs`,
  `tests/browser/{demo,multiruntime,crud}.spec.mjs`; R `runtime-client.spec.ts`, `contextual-cache.spec.ts`,
  `runtime-live.proof.ts`, `presentation-live.proof.ts`, E-app auth/backend selection tests and specialized screens.
- F30: U `tests/{testbed-boundary,consumer-lock,package-versioning,optional-themes-boundary}.test.mjs`,
  E package provenance checks and the D integration scripts. Existing proof files are opt-in, not default mock runs.

New tests must explicitly cover missing semantic lossless widgets, lookup port parity, custom form insertion,
real application guards and adapter-authoritative reconciliation. Existing tests of separate layers do not prove
those integrations by composition alone.

### Real-host proof, separate from mocked tests

Before running, record actual host revision, contract ref, negotiated profile/capabilities, library/source/archives,
fixtures, commands, ports and container ownership. Use disposable data and known cleanup keys; never shared business
records. Fetch metadata and data, create with omissions/defaults, GET the complete row, update one exact value,
verify untouched values, provoke invalid values and genuine concurrent conflict where supported, then delete.
Record final baseline equivalence and cleanup. A transport timeout requires readback, not blind write repetition.

Start with the implementing PHP demo host at an explicitly verified compatible pin; its historical success is useful
baseline evidence but must be rerun against the extracted adapter. Dictionary-only Java/.NET evidence cannot pass
CRUD. ERBAS .NET validation is a separate v0.14 proof, not ARP proof. If live hosts/adoption are unavailable, record
pending evidence; do not close U ADAPTER-002 or any cross-backend gate. Browser assertions and raw HTTP results
should agree; isolated codec/unit success cannot certify persistence, transactionality or production security.

## 10. Risks and unresolved decisions

1. **Protocol approval/adoption:** Common ARP HTTP resource/form discovery, diagnostics, versions and capabilities
   are still open. Extraction must not freeze D wire shapes accidentally. Profile ownership/review is a prerequisite.
2. **Source/version drift:** Same nominal APF versions hide breaking artifact/API changes. Atomic provenance-backed
   adoption and installed-package compatibility are mandatory; no version change is authorized by this inventory.
3. **Semantic parity:** E v0.14 integers, exact JSON tokens, contextual exclusions, relations/actions and immutable
   semantics differ from ARP candidate/UI neutral models. Mapping needs explicit unsupported/deferred results.
4. **Library location:** Separate repo is recommended, not approved. Initial peer/version support and optional ERBAS
   compatibility entry point need decisions before package scaffolding. Avoid a speculative generic protocol framework.
5. **Visual completeness:** Lossless editing is not yet full themed semantic widget support. Objects/custom insertion,
   dialog/summary reuse and list interaction ports need scoped proof, not parallel app implementations.
6. **State lifetime:** A facade can accidentally retain old mutable form values or invalidate a session on theme switch.
   Enforce one session tree and retained host-owned views, with explicit destroy/context lifetime tests.
7. **Recovery and identity:** A successful partial response, page refresh or generated ID cannot establish a complete
   accepted document. UI row identity and server identity differ; missing evidence must keep recovery explicit.
8. **Security versus discard:** Voluntary leave can ask; forced session loss must clear protected state. Exact policy
   belongs to each app and needs tests. Browser unload prompts are inherently unreliable, especially on mobile.
9. **Evidence age:** Historical tests pin older libraries/backends; current contract main differs. Do not extrapolate
   old seventeen-type dictionary results or PHP CRUD into current multi-runtime compatibility.
10. **Review order:** Independent proof occurs before ERBAS per decision and again at final closure per task sequence.
    This two-gate interpretation should be confirmed when authorizing the implementation backlog.

## 11. First recommended implementation task

Authorize **AUR-EDITOR-ENUM-001** after its preservation fixtures/minimal public port review.
It closes a concrete consumer gap: the current DocumentSession bridge renders ENUM as text while existing themes
already provide semantic selection. The outcome must be one shared lossless themed control path available both to
manual Angular screens and metadata-generated forms, preserving invalid drafts and legacy behavior.
It does not require creating ARP Angular, deciding a new wire protocol or migrating ERBAS prematurely.
The next selector/layout tasks should follow demonstrated parity needs, not a wholesale form-engine rewrite.

## 12. Documentation validation and scope of this change

Only this implementation inventory/proposal is added. Production code, normative contracts, historical evidence,
backend repositories, packages, lockfiles and versions are unchanged.
Relevant checks from C's documentation tooling:

```sh
python3 -B tools/check_documentation.py
python3 -B -m unittest discover -s tests -p test_documentation.py
git diff --check
```

Also review the entire new file, verify UTF-8/LF, no trailing whitespace, maximum 120-character lines and the
repository's `.editorconfig` no-final-newline setting. Documentation validation checks local links/anchors and
historical manifest integrity; it is not Angular/backend execution. The implementation test commands above are
future task gates, not claims of executions in this analysis task.

Executed on this documentation branch: the reference/hash checker passed with 276 local references and 25 archived
documents; both documentation unit tests passed. The checker inventories 21 external URLs without fetching them.
Cross-repository source revisions were inspected separately; no external URL availability or backend conformance
is implied by the offline checker. Formatting and diff checks must also pass before the local commit.