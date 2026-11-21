# ARP-DICT-001-CONTRACT-002 — Portability consolidation

Base contract: `0172ab64742218b9f64a6ae96c43ebdfe690f4c6` (merged PR #4).
Branch: `feature/arp-dict-001-portability-002`. Status: unpublished review candidate.
This resolves intake/metadata ambiguities within the existing scalar dictionary.
The 17 types, operations, scalar numeric domains, business boundaries and original
fixture outcomes remain unchanged. No CRUD, persistence or new component is added.

## Reviewed merged references

The following local `main` files were verified against GitHub `main` blob IDs;
none of their repositories was modified:

- [PHP conformance](https://github.com/alxarafe/arp-php/blob/16338d76f82bb9127edf37d3a3bdb87dde582e66/docs/conformance.md),
  blob `576e9ad473eccde6638c7a6f41599194a2843f16`.
- [Java contract feedback](https://github.com/alxarafe/arp-java/blob/85a880afa0d02a93950557b6347012e62d570a18/docs/contract-feedback.md),
  blob `35b9766e92e16f29295700e220c44d934caeb946`.
- [.NET review](https://github.com/alxarafe/arp-dotnet/blob/ecb9a8630bf5cd9a4fae979cc0e79d9bc8954883/docs/contract-review.md),
  blob `0585ec065d03214888fde0aca1097f4f388bbb9a`.
- [.NET probe inputs](https://github.com/alxarafe/arp-dotnet/blob/ecb9a8630bf5cd9a4fae979cc0e79d9bc8954883/docs/review-probes/inputs.json),
  blob `7604e847eff0c305d1541eaafb2ac8ff81379fa1`.
- [.NET observed results](https://github.com/alxarafe/arp-dotnet/blob/ecb9a8630bf5cd9a4fae979cc0e79d9bc8954883/docs/review-probes/observed.json),
  blob `036746af18f99528143c55aad878841a6d8d6725`.

These reports establish the disagreements, not their normative resolution. ARP's
specification, schema and authored expectations establish the decisions below.

## Adopted decisions and rationale

| Area | Common decision | Reason |
| --- | --- | --- |
| YAML scalars | One-line plain/single/double quoted; JSON-compatible escapes in double quotes | Avoid full flow folding and host escape extensions while preserving normal configuration data |
| Implicit types | Exact lowercase null/booleans and JSON-number lexemes; everything else plain is text | Dates, yes/no/on/off, leading-zero codes and `+1` must not acquire YAML 1.1/native meanings |
| Multiline text | Literal/folded block text with clip/strip/keep; infer space indentation; no explicit numeric indicator | Real descriptions need multiline text; mature parsers already support these small, explicit styles |
| Continuations | Reject all multiline plain/quoted scalars, indented or not | Close the actual Java/PHP/.NET divergence consistently; block text provides the same functional need |
| Source numbers | At most 256 token characters, exponent absolute value <=128 and absolute magnitude <10^128 | More than enough for length/geometry metadata, bounded exact processing before native overflow; no practical need for 1e10000 or larger |
| Metadata integer kind | Mathematical integer, not lexical spelling; export exact JSON Number | `1`, `1.00`, `0.1e1` are equivalent; booleans and quoted strings remain distinct kinds |
| Resource profile | 1 MiB, 2048 elements, depth 128, with explicit pre-semantic limit rejection | Reuse existing common defaults and remove arbitrary parser recursion/numeric limits |
| Numeric domain wording | DECIMAL bounds need not fit optional geometry | Already established by original `ordered-constraints`; no satisfiability solver is introduced |

The 128-digit metadata magnitude exceeds any practical in-memory text length and
ordinary machine integer range; choosing it is not adopting a PHP/Java/.NET native
maximum. Token and exponent bounds prevent attacks disguised as small/zero values.
Scalar DECIMAL/INTEGER inputs remain non-exponent strings with the original
4096-digit ceiling. No accepted scalar precision is reduced.

YAML syntax is now a required, closed portable subset instead of an unspecified
optional subset. Raw tags/directives/aliases remain forbidden; literal-looking
symbols inside text are data. Unsupported syntax is DOCUMENT_INVALID. Reaching a
resource budget is LIMIT_EXCEEDED before shape validation; an in-budget fractional
integer-typed metadata value remains ELEMENT_INVALID. No machine timeout is added.

This is a deliberate pre-publication tightening/clarification, **not a PATCH of a
released contract**. `arp.dictionary/v1` is retained because no ARP contract has
been published. Historical `0172ab6` and its implementation evidence are not altered.

## New shared vectors: 25 cases, 29 additional assertions

| Set | Added cases | What each group closes |
| --- | ---: | --- |
| Sources: portable scalars/literal/folded/equivalent JSON | 4 | Quoting, decoded Unicode, dates/words, integer-number spellings, true block text and exact 128-digit metadata; four complete descriptor projections verify data, not just acceptance |
| Sources: multiline quoted/plain, tab indentation, YAML-only escape, explicit block indent | 5 | Each independent unsupported syntax boundary |
| Sources: unknown directive and null/escaped duplicate | 2 | Constructs lost or silently overwritten by some host parsers |
| Sources: depth 128/129 | 2 | In-budget semantic defect versus pre-semantic limit; root is depth one |
| Sources: numeric exponent/zero/negative exponent/magnitude/token overflow, negative exponent boundary | 6 | Distinct bypasses/budgets and exact fractional rejection instead of underflow-to-zero |
| Definitions: maximum integer length metadata / first excess | 2 | Inclusive 10^128-1 mathematical boundary and its limit category |
| Values: lower/upper UTC tick, upper overflow, literal U+FFFD | 4 | Seven-digit calendar limits and real replacement text versus invalid Unicode |

Original values (132), definitions (34), sources (21), patterns/samples,
13 catalog scenarios, projections and base catalog remain intact. A comparison
against the base Git object verified every original vector's JSON model and every
original raw source's bytes. No duplicate giant-exponent cases are added: the
single `1e10000` vector covers the old 1e2147483648/1e2147483649/huge-exponent
probe family; the zero and negative cases test different bypasses.

The new inventory is 136 values, 36 definitions, 40 sources, 45 pattern cases,
21 pattern samples, 32 catalog steps, 12 catalog projections, four source
projections and one base catalog: **327 shared runtime assertions**. Large
byte/element boundary tests are generated in the checker tests instead of adding
megabytes of redundant checked-in fixture data.

## Required implementation follow-up (no stack changed here)

| Stack | Concrete adaptation |
| --- | --- |
| PHP | Replace its restricted YAML guard that rejects block styles/plain dates; implement the common scalar resolver, JSON-compatible escapes and all single-line restrictions. Add depth 128 counting and source-number token/exponent/magnitude preflight. Replace its 4096 exponent expansion policy with the common bounded metadata policy; keep exact numeric kinds/export. |
| Java | Reject multiline plain/quoted extensions currently accepted by SnakeYAML and YAML-only escape/block-header extensions. Align all plain scalars with the ARP resolver rather than assuming native JsonSchema matches every case. Check source numeric text before BigDecimal conversion so exponent overflow becomes LIMIT_EXCEEDED. Enforce magnitude/token bounds and the length schema bound. |
| .NET | Restrict even indented multiline quoted/plain scalars and YAML-only escape/explicit-indent extensions; retain correct treatment of implicit default tag handles. Add numeric token/exponent/magnitude checks to its existing raw-token path before arbitrary BigInteger exponent handling. Existing depth default already matches. |
| All three | Honor the manifest's portable profile, complete optional source descriptor projections, compare JSON numeric nodes mathematically/exactly with booleans distinct, retain string constraint spelling, update schema/pins and rerun all 327 assertions plus stack-specific instrumentation. Review out-of-budget tests that previously expected acceptance. |

No runtime API shape, framework, parser package or arithmetic implementation is
mandated. Different numeric representations are fine if these bounded observable
results match. Pure source-model tests cannot replace runtime immutability,
concurrency, side-effect and resource instrumentation.

## Validation and handoff

See [checker commands and layers](dictionary-checks.md) and
[recorded contract-only results](dictionary-check-results.md). Structural and
focused intake checks pass independently of native runtime execution. Existing
298-case stack reports concern `0172ab6`; all three stacks are **NOT_EVALUATED for
this updated candidate** until adapted and rerun against its exact commit.

The contract is prepared for first-publication review under the existing release
process. Remaining actions are implementation follow-ups, review and explicitly
authorized publication. No tag, release, push, merge or implementation edit is
part of this task. The next ARP component is not implemented here.