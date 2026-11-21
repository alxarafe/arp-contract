# ARP-ARCH-001 — Architecture and product boundaries

**Status:** Proposed architecture baseline for review; not a published runtime or wire contract.
**Scope:** Cross-language architectural direction for `arp-contract`, `arp-java`, `arp-dotnet`, `arp-php`, their adapters, and consuming applications.
**Release impact:** Documentation only. No format identifier, schema, endpoint, function signature, or Git release is created by this document.

## 1. Product mission

**Alxarafe Resource Platform (ARP)** provides optional, reusable, language-neutral declarative capabilities and integration mechanisms for applications. It is intended to simplify building and evolving modular business software of a size and scope comparable to other modular business applications. It may draw architectural lessons from larger model-driven environments such as SAP and CAP, without reproducing their technology stacks, product scope, or business knowledge.

**ARP is not an ERP and does not contain business-domain definitions.** The consuming application owns every business entity, field meaning, calculation, policy, operation, process, decision, and domain implementation. ARP provides the language, generic mechanisms, and adapters that make those definitions usable and reusable.

The desired outcome is a **declarative business-model layer plus an infrastructure-independent domain**, not merely metadata-driven CRUD and not a new mandatory application framework.

## 2. Architectural invariants

These are design constraints to review against every feature. They are not claims that the corresponding runtime capability is already implemented.

1. **Domain agnosticism.** ARP MUST NOT embed the meaning of invoices, customers, credit, taxes, inventory, or any other application-specific concept. Names used in examples are consumer-owned.
2. **Consumer ownership.** The application owns its declarative business definitions, domain code, business decisions, persisted data, and deployment policies.
3. **Technology neutrality of contracts.** Shared contracts MUST NOT require Java, C#, PHP, Laravel, Symfony, Spring, ASP.NET, a specific ORM, SQL dialect, or storage engine.
4. **Independent domain code.** A domain function SHOULD be callable as ordinary language code without importing ARP, web-framework, ORM, transport, or database types. The application can use a mapper/composition layer to bridge representations.
5. **Optional adoption.** An application MAY use only the dictionary, or add resources, presentation, domain invocation, or other capabilities as required. Each capability SHOULD depend only on its indispensable prerequisites.
6. **One definition, multiple uses.** Reusable data elements, structures, metadata conventions, and registered operations SHOULD be referenced rather than copied, while preserving explicit context-specific rules.
7. **No prescribed application layout.** ARP MUST NOT infer its modules, resources, dictionary entries, or domain handlers from a fixed directory hierarchy. Applications or module source providers register them; their packaging can differ by language and framework.
8. **Observable interoperability.** Java, .NET, and PHP MAY have different internals, but claimed conformance MUST be measured against the same released contract and fixtures.
9. **Backend authority.** Client presentation and preflight validation are advisory. The consuming application's trusted server path MUST remain the authority on business authorization, invariants, concurrency, and persistence.
10. **Evolution without silent drift.** Changes to published meanings, formats, or behavior follow `docs/versioning.md`; implementation shortcuts must not redefine the target architecture accidentally.

## 3. Responsibility boundaries

| Owner | Responsibilities | Must not silently assume |
| --- | --- | --- |
| `arp-contract` | Portable specification of types, formats, resolution, observable behavior, extension boundaries, and conformance cases | Ownership of ERP business definitions or implementation internals |
| ARP runtime (`arp-java`, `arp-dotnet`, `arp-php`) | Generic parsing, type resolution, reusable validation, metadata processing, capability registration and dispatch where supported | A particular ORM, tenant scheme, module folder, business vocabulary, or persistence schema |
| Optional ARP adapter | Translation between ARP's published logical contracts and a host framework, UI, persistence technology, or application operation | Business decisions or that every feature must be enabled |
| Consuming application / ERP | Business-specific YAML/JSON, domain functions, policies, modules, business errors, data, and final save/authorize decisions | That ARP preflight validation substitutes for domain enforcement |
| Application composition/integration layer | Register sources and handlers, map logical input/output to domain objects, supply trusted execution context, wire infrastructure ports | That domain objects must inherit or import ARP runtime classes |
| Client (for example Angular) | Render UI from applicable metadata, submit edits, display validation and action availability | That UI controls provide security or that metadata alone authorizes persistence |

The conceptual **runtime execution path** is: application definitions → ARP resolution/metadata → UI or application call → registered adapter/handler → domain decision → application-controlled persistence/outcome. This is **not** a dependency direction diagram. Domain code must not import infrastructure just because the call path reaches it.

## 4. Declarative model and reusable elements

### 4.1 Logical dictionary

The dictionary provides reusable, consumer-named logical elements (type, immutable intrinsic constraints, optional generic label/description). An element's business meaning belongs to the consumer; ARP only understands its generic type and constraint semantics.

- `ARP-DICT-001` will define scalar registration, source intake, resolution and validation.
- `ARP-DICT-002` will define reusable named composite structures and recursive references.
- `ARP-DICT-003` may add traceable declarations of use.
- `ARP-DICT-004` may add optional storage verification through application-provided metadata.

Logical types and constraints should preserve relevant pre-existing published vocabulary when reused, but **ARP-DICT-001 must explicitly approve the new source syntax and format identifier**. No syntax is made normative by this architecture document.

### 4.2 Field, resource and view metadata

Dictionary elements are **not** the same as field usages. Consumer-supplied metadata may describe fields in logical resources, tables, and views, including labels/literals, hints, localization references, display ordering, editability, contextual requiredness, defaults, list/form grouping, and other presentation or operational hints.

- **Intrinsic constraints** follow the dictionary element and must not be weakened silently by a field usage.
- **Contextual constraints** and `required` are distinct from intrinsic types and `nullable`; their future composition and contradiction rules need a separate specification.
- A **logical view** must not necessarily be a database `VIEW`; a SQL view is one possible adapter implementation.
- Metadata for a UI must not be Angular-specific. A client can ignore unsupported optional presentation hints, but it must not infer permission from their presence.
- Literal/value catalogs, localization, dynamic value selection, and conditional editability are distinct future design topics; their mechanisms and precedence remain open.

### 4.3 Storage is an adapter concern

An application may use PDO and MariaDB, Eloquent, Doctrine, Hibernate, EF Core, raw SQL, or something else. ARP should provide enough resolved logical information for optional mappers or schema-audit providers, without requiring any of them for dictionary-only use.

Physical column compatibility is not identical to logical validation: collation, decimal precision, signedness, date/time semantics, `NULL`, application-side validation, SQL checks, and foreign-key behavior may differ. Future verifiers must distinguish demonstrable conformance, mismatch and lack of evidence, and identify the layer being checked.

ARP MUST NOT silently alter production schemas on document load. Persistence changes and migrations remain explicit, reviewed, application-owned operations; historical applied migrations must not be reinterpreted using newer dictionary definitions.

## 5. Application/module-provided sources

A consuming application (or one of its modules) registers **source providers**, not presumed filesystem paths. Implementations may receive filesystem trees, packaged resources, embedded assets, or other explicitly supported sources.

- A source has declared provenance/owner and deterministic precedence or conflict handling; duplicates must not be silently overwritten.
- Discovery, installation and enablement of modules belong to the application or its chosen module system, not to a mandatory ARP folder convention.
- Only enabled modules contribute to the **effective active catalog**. Disabling a module does not imply deleting its source files or persisted business records.
- Caches of derived catalogs are disposable and must not leak definitions or metadata across distinct application/tenant/context scopes.
- Safe parsing, validation of references, unrecognized fields and conflicts must be specified by each published source format.

The existing `arp-php-test/modules/<id>/module.yaml` convention is an **application test fixture**, not a portable ARP requirement.

## 6. Reusable integration with ERP domain functions

### 6.1 Intended capability

The application can **declare and reuse** a logical hook to its own function, such as an invoice calculation, a quotation preflight check, or action-availability decision. ARP's generic job is to resolve the declaration, locate a registered callable via an adapter, pass validated/typed inputs and trusted context, receive a normalized outcome, and make that outcome usable by other generic capabilities.

ARP does **not** prescribe the function's business logic or itself decide whether a quotation has sufficient credit. Nor does it require a declarative rule engine or force all domain function calls to pass through ARP.

A generic binding needs, as a **target-design consideration**, a stable logical operation identifier, declared input/output contracts, controlled handler registration, execution semantics and a structured outcome including business reasons where appropriate. The exact invocation and error contracts are deferred to `ARP-DOMAIN-001`.

The business-domain class may use an ERP-defined `Invoice` object and return an ERP-defined result object. The integration layer maps to and from ARP's logical structures. **Domain types need not inherit ARP classes**.

### 6.2 Illustrative scenario — not a published format

A consuming ERP defines a quotation resource and connects it to `sales.quotation.validate`. Angular can render the declared form using metadata, request an optional **preflight** check, and display a business rejection reason such as `INSUFFICIENT_CREDIT`. The ERP can reuse the same validator for other operations if its input/context contract permits it.

At actual save time, the server-side ERP operation **independently** decides whether to persist. It may re-evaluate relevant constraints and business state, reject the operation, and return reasons. Changes in available credit, concurrent writes, tenant context, or authorization between preflight and save must not be assumed away.

The preflight result is **informative, not a permission token**. UI action availability, button disabling and hidden fields are usability features, never server-side security boundaries.

### 6.3 Invocation boundaries and security

- A function is callable through ARP only when registered by the trusted application and explicitly exposed for the relevant capability. Arbitrary method names or user-supplied executable expressions must not become invocation paths.
- The server resolves identity, tenant, authorization, and other trusted execution context. The client must not supply authoritative values for these fields.
- The generic protocol must distinguish input-shape rejection, unregistered handler, unavailable capability, infrastructure failure, business rejection, and successful business output without inventing domain semantics.
- Only application-approved business details may be returned to clients; internal exception traces and secrets must not be exposed by default.
- Side effects, transactional boundaries, retry/reentrancy/idempotency, concurrency checks and execution-time authorization require deliberate future contracts. Read-only preflight and authoritative mutations must not share unsafe assumptions.
- Local dispatch should be possible without HTTP. HTTP, background jobs and messaging can be adapters where needed, not mandatory infrastructure.

## 7. Optional capabilities and composition

The following are **target capabilities**, not automatically included in the first runtime or required together:

| Capability | Generic service | Optional in a consumer? |
| --- | --- | --- |
| Dictionary | Logical scalars, constraints, resolution | Yes |
| Structures | Reusable composed input/output types | Yes, except when a chosen feature needs them |
| Resource runtime | Generic CRUD/resource contracts and metadata | Yes |
| Presentation | Forms, lists, actions, hints and navigation metadata | Yes |
| Domain bridge | Binding and invocation of consumer-owned functions | Yes |
| Rules / state / workflow | Generic future building blocks only if justified by real consumer use | Yes |
| Storage metadata / verification | Comparison of declared logical and observed physical definitions | Yes |
| Framework adapters | Laravel/Symfony, Spring, ASP.NET, PDO, ORM, client integration as applicable | Yes |

**Optionality is functional:** dictionary-only consumption must not require HTTP, a database, a particular module loader, a UI or a domain-dispatch runtime. Features may declare precise necessary prerequisites. ARP must avoid copying business rules into a framework adapter.

## 8. Portability and conformance

Each approved feature must state **target design**, **MVP scope**, dependencies, acceptance criteria and language-neutral fixtures. Common cases should test semantics rather than implementation class shapes.

- Exact decimals, ranges, nullability versus requiredness, string length, character classes and date/time handling need cross-language rules.
- Regular-expression formats must use an agreed interoperable subset or explicitly documented engine differences and fixtures; parser differences must not silently change results.
- Local domain value objects (e.g., money) are allowed when adapters preserve contractual meaning and precision.
- A change of language/framework requires translating ERP-owned domain code, but must be able to reuse portable logical definitions and language-neutral business test cases where applicable.
- An adapter may implement only a subset of ARP capabilities, but must state and test what it supports. Unsupported guarantees must not be silently presented as enforced.

Conformance to ARP is distinct from conformance of the ERP's **business rules**. The latter are owned and tested by the ERP, potentially using language-neutral test vectors.

## 9. Architecture-first, incremental implementation

**Design for the intended product; implement incrementally.** A deliberately small MVP must not close off a high-value target capability without an explicit architectural decision.

For each new feature, review:

1. Which long-term product capability does it enable?
2. Which identity, schema, semantics or coupling decisions would be expensive to reverse?
3. What extension boundary or data contract must exist now, even if its implementation comes later?
4. What can safely be postponed without constraining the target?
5. Which representative consumer scenario could falsify the design?

Do not implement speculative abstractions solely because they might be useful. But do not settle core semantics based only on the smallest demo. Prefer contracts that can later be extended through independently registered providers.

### Planned sequence (subject to review)

| Stage | Goal | What is deliberately deferred |
| --- | --- | --- |
| `ARP-ARCH-001` | Agree domain/infrastructure boundaries, optional adoption and product direction | Published protocols or runtime implementations |
| `ARP-DICT-001` | Scalar dictionary, registered sources, resolution and validation | Composite objects, persistence mapping, domain invocation |
| `ARP-DICT-002` | Reusable named composite structures | Business-domain execution rules |
| `ARP-DOMAIN-001` | Bind consumer-defined operations to registered domain callables with typed contracts | Domain-specific rule engine or mandatory HTTP |
| Separate metadata features (IDs TBD) | Resource/table/view field metadata, literals, hints, form/list presentation | Forcing UI or storage on dictionary-only users |
| `ARP-DICT-003/004` and later adapters | Usage traceability, optional storage conformance | Automatic production schema migration |

The table describes an **ordering hypothesis**, not a promise of delivery or an approved feature dependency graph. An earlier or smaller domain-bridge spike MAY be used to validate the dictionary boundary without publishing `ARP-DOMAIN-001` prematurely.

## 10. Anti-goals and review tests

ARP is **not**:

- An ERP containing sales, accounting, stock, taxation or other business vocabulary.
- A mandatory replacement for Laravel, Symfony, Spring, ASP.NET or an existing ERP platform.
- A fixed module-folder, database, migration or ORM convention.
- A full declarative programming language that hides arbitrary executable business logic inside YAML.
- A frontend authorization system or a guarantee that preflight decisions remain valid when committing.
- A requirement that all code, services or domain function calls be mediated by ARP.

A proposed feature should be challenged if it requires domain code to import ARP, binds shared contracts to a storage engine or web transport, duplicates consumer business logic, forces an optional capability, or cannot say which runtime/application component is authoritative.

## 11. Open decisions — explicitly not settled here

1. Exact YAML/JSON document format identifiers, schemas and parse restrictions for ARP-DICT-001.
2. Whether context-specific constraints can narrow intrinsic constraints and their formal composition/error rules.
3. The separation and format of reusable structures, logical views, field metadata and presentation hints.
4. How applications declare, localize and resolve literals, hints, enumerated values and lookups.
5. Registry identity, handler lifetime, synchronous/asynchronous execution and outcome envelopes for `ARP-DOMAIN-001`.
6. Authorization/tenant-context boundaries and cache identities for each runtime/adapter.
7. Capability discovery/negotiation across framework adapters and clients.
8. Future interface names and package boundaries; this document deliberately mandates **behavioral boundaries**, not class/interface names.

These decisions must be resolved in their own feature specifications and tested before publication. Revisions to this architecture document are allowed through normal review and versioning; they do not retroactively alter published releases.

## 12. Relationship to contract governance

Read alongside [`versioning.md`](versioning.md), [`compatibility.md`](compatibility.md), and [`release-process.md`](release-process.md). Those documents govern publication and conformance. This document establishes architectural direction and review criteria; it does **not** make illustrative formats or deferred runtime behavior normative. No version tag is created solely for `ARP-ARCH-001`.