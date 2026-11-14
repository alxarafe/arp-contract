# ARP-DICT-001 — Reusable scalar data dictionary

**Status:** Design approved for implementation, including Phase A contractual clarifications; **not yet a published contract**.
**Target:** `arp-contract` first functional contract release, prospectively `v0.1.0`.
**Approved format:** `arp.dictionary/v1`.
**Ownership:** ARP defines the reusable logical language and its observable mechanics; the consuming application owns all element names, business meanings and usages.
**Sources reviewed:** [`arp-contract/docs/architecture.md`](../architecture.md), [`docs/versioning.md`](../versioning.md), and the published [`erbas-contract v0.13.0` resources specification](https://github.com/alxarafe/erbas-contract/blob/v0.13.0/docs/core/resources-001.md) and [OpenAPI resource schema](https://github.com/alxarafe/erbas-contract/blob/v0.13.0/openapi/core/resources/contract.yaml).

> **Review convention.** MUST, SHOULD and MAY describe the behavior intended for the first *approved* release; this approved implementation design does not itself publish a contract. Codex must not silently modify these decisions. Any discrepancy exposed by implementation goes back to contract review before publication.

## 1. Purpose and product boundary

Provide a reusable, self-contained dictionary of **named scalar elements**, with deterministic source registration, lookup, type validation, intrinsic constraints and normalized results, across independent PHP, Java and .NET implementations.

ARP is agnostic to the business vocabulary of identifiers such as `catalog.productCode`. A consuming ERP/module owns the definition and meaning of its elements, their eventual table/view usages, functions, validations, rules and persistence decisions.

The dictionary MUST be usable by itself without HTTP, authentication, a relational database, ORM, specific framework, Angular client, fixed application directory structure, or module installation subsystem.

### 1.1 Target design versus this MVP

**Long-term direction (not delivered by this feature):** named composite structures; contextual field/table/view metadata; reusable literals, localization and hints; registered ERP domain functions; resource definitions; adapters that map logical to physical storage or UI; dictionary-use tracing and storage verification.

**ARP-DICT-001 MVP:** standalone named scalar definitions, safe YAML/JSON document intake, explicit provider registration, complete catalog validation, deterministic resolution, exact scalar validation/normalization, and language-independent positive/negative conformance fixtures.

**Not included:** persisted storage; SQL generation/migrations; data access; FK checks; form generation; resource-specific `required`, `nullable`, `default`, `readOnly`, `immutable`; field-to-column mappings; business-rule evaluation; expression evaluation; HTTP routes; handler invocation; inheritance, aliases, overlays or automatic cross-source overriding.

## 2. Evidence and compatibility with Erbas

The published `erbas-contract v0.13.0` defines **17**, not 16, scalar type identifiers:

`BOOLEAN`, `STRING`, `TEXT`, `INT8`, `UINT8`, `INT16`, `UINT16`, `INT32`, `UINT32`, `INT64`, `DECIMAL`, `UUID`, `DATE`, `TIME`, `DATETIME`, `ENUM`, `BINARY`.

Its generic resource metadata also uses `minimum`, `maximum`, `multipleOf`, `exclusiveMinimum`, `exclusiveMaximum`, `precision`, `scale`, `minimumLength`, `maximumLength`, `pattern` and `enumValues`; `required` and `nullable` are explicitly distinct there. The published resource protocol has its own HTTP, field, CRUD, temporal and numeric wire semantics.

**Preserved direction:** recognizable type and constraint vocabulary, exact numeric handling, canonical UUID/temporal forms, and separation of presence from nullability.

**Intentional new ARP design (not automatic compatibility):** dictionary elements have no `required`/`nullable`/`default`/access or presentation properties; exact numeric constraints and canonical conformance values use **decimal strings**; the dictionary has its own document format, validation outcome and restricted portable pattern syntax. `arp-contract` does not modify historical `erbas-contract` tags or claim that existing resource clients can consume this new format unchanged. Resource adapters will perform an explicitly tested mapping later.

## 3. Portable document format

### 3.1 Illustrative conforming document

```yaml
apiVersion: arp.dictionary/v1
elements:
  - id: catalog.productCode
    type: STRING
    label: Product code
    description: Code assigned by the ERP
    constraints:
      minimumLength: 1
      maximumLength: 10
      pattern: '^[A-Z0-9-]+$'

  - id: finance.amount
    type: DECIMAL
    constraints:
      precision: 18
      scale: 2
      minimum: '0'

  - id: sales.quotationStatus
    type: ENUM
    enumValues: [draft, pending, approved, rejected]
```

The business words in this document are **application-owned examples**, not built-in ARP types, rules or modules.

### 3.2 Document shape

The top-level value MUST be an object with **exactly** these recognized keys:

| Property | Required | Type | Semantics |
| --- | --- | --- | --- |
| `apiVersion` | Yes | String, exactly `arp.dictionary/v1` | Format generation, not repository release |
| `elements` | Yes | Array of objects, at least one | Named scalar definitions |

Each element MUST be an object with only the following keys:

| Property | Required | Type | Semantics |
| --- | --- | --- | --- |
| `id` | Yes | String | Stable, case-sensitive qualified identity |
| `type` | Yes | String | Exactly one of the 17 uppercase scalar identifiers |
| `constraints` | No | Object | Intrinsic, type-specific constraints; absent means `{}` |
| `enumValues` | Only for `ENUM` | Array of unique nonempty Unicode strings | Allowed ENUM values, case-sensitive and ordered as authored |
| `label` | No | Nonempty Unicode string | Optional default descriptive text, not an i18n catalog or field-specific label |
| `description` | No | Nonempty Unicode string | Optional descriptive text; no executable semantics |

Unknown keys, unknown types, `null` in place of any required/optional typed property, and extraneous `enumValues` on non-`ENUM` definitions are errors. An empty `constraints: {}` is valid. `enumValues` MUST contain at least one value on `ENUM`. Duplicate ENUM values are invalid even if apparently identical in repeated entries. Labels and descriptions MUST NOT influence value validation, identity or business behavior.

### 3.3 Identity

The MVP identifier grammar is ASCII and case-sensitive:

```regex
^[A-Za-z][A-Za-z0-9_-]*(\.[A-Za-z][A-Za-z0-9_-]*)+$
```

At least two dot-separated segments are required; no empty segments, whitespace, Unicode confusables or implicit case folding. The whole identifier has a maximum of **128 ASCII characters**. `catalog.ProductCode` and `catalog.productCode` are distinct identifiers. No automatic namespace is supplied by ARP; providers must register the full ERP-owned identifier. Renaming an ID is a migration of references, not an alias.

### 3.4 YAML/JSON intake rules

- The normative **data model** is JSON-compatible objects, arrays, strings, booleans, integers and null where explicitly allowed. Both JSON and a **safe, restricted YAML 1.2 subset** MAY be accepted as source encodings; both MUST yield identical model semantics.
- Exactly one document/root object per source; duplicate mapping keys at any depth are rejected. No arbitrary tags, constructors, anchors/aliases, merge keys, directives, implicit timestamp objects, embedded executable content or additional YAML documents.
- Numbers for `minimum`, `maximum` and `multipleOf` are **quoted strings**, never YAML/JSON numeric literals. `precision`, `scale`, `minimumLength`, `maximumLength` and repetition counts are integer values where specified. Booleans are native `true`/`false`.
- A parser MUST reject malformed or unsupported input rather than interpreting it with language-specific YAML 1.1 implicit boolean/date rules. The normative JSON Schema validates node shapes; parser-level duplicate keys and forbidden YAML constructs additionally require dedicated checks.
- UTF-8 input is required. Invalid encoding and unpaired Unicode surrogates are rejected. No implicit Unicode normalization, trimming or case conversion of IDs, labels or enum values.
- The format is **closed**. Future attributes require an explicitly reviewed compatible format extension or new format generation under `docs/versioning.md`, not an unvalidated free-form extension bag in this MVP.

## 4. Scalar values and canonical conformance representation

The dictionary validates a value already selected for a particular element. **Presence and nullability belong to its consumer**: this feature's scalar validation accepts neither missing values nor `null` as a valid scalar value. A future field binder MAY permit omission or `null` before deciding whether to call the dictionary value validator. `""` is a real string, not a missing value.

For cross-language conformance, the portable **test value representation** is deliberately defined separately from any later HTTP resource/ERP field format:

| Family | Fixture input representation | Canonical successful fixture output |
| --- | --- | --- |
| `BOOLEAN` | JSON boolean | Same boolean |
| Signed/unsigned integers | String of ASCII base-10 integer digits, optional leading `-` for signed | Canonical base-10 string |
| `DECIMAL` | String containing a plain base-10 exact decimal | Canonical plain decimal string |
| `STRING`, `TEXT`, `ENUM` | JSON string | Exactly the same Unicode scalar sequence |
| `UUID`, `DATE`, `TIME`, `DATETIME` | JSON string | Normalized textual value specified below |
| `BINARY` | Strict padded standard Base64 JSON string | Same canonical Base64 text |

This table is the observable **fixture/neutral value codec** contract, **not** an assertion that a Java/PHP/.NET API must represent all native integers as strings internally, or that every ERP HTTP request must serialize them this way. Each implementation may expose additional native value overloads if they preserve the same semantics and never silently lose precision. Tests will use the portable representation.

### 4.1 Integer types

| Type | Inclusive minimum | Inclusive maximum |
| --- | ---: | ---: |
| `INT8` | -128 | 127 |
| `UINT8` | 0 | 255 |
| `INT16` | -32768 | 32767 |
| `UINT16` | 0 | 65535 |
| `INT32` | -2147483648 | 2147483647 |
| `UINT32` | 0 | 4294967295 |
| `INT64` | -9223372036854775808 | 9223372036854775807 |

Inputs MUST be exact base-10 integer strings matching `0|[1-9][0-9]*` for unsigned or `-?(0|[1-9][0-9]*)` for signed. No `+`, exponent, decimal point, whitespace, leading zeros or signs on unsigned values. Signed `-0` is accepted and normalizes to `0`. Integer arithmetic/comparisons MUST be exact (no IEEE-754 rounding). Out-of-range values are rejected, never clamped or wrapped.

### 4.2 `DECIMAL`

`DECIMAL` uses **arbitrary-precision base-10 arithmetic**. The portable lexical grammar is:

```regex
^-?(0|[1-9][0-9]*)(\.[0-9]+)?$
```

No exponent, leading `+`, whitespace, `NaN`, infinity or locale-dependent separators. The normalized value has no redundant leading zeros, no redundant trailing fractional zeros, no fractional dot if its fractional part is zero, and no negative zero: `"1.2300"` becomes `"1.23"`; `"-0.00"` becomes `"0"`. **Normalization never rounds a nonzero digit away.**

`precision` and `scale`, if used, MUST be supplied together: `1 <= precision <= 4096`, `0 <= scale <= precision`. Their meaning is **exact representability** as `DECIMAL(precision, scale)`: the value must be an exact multiple of `10^(-scale)` and `abs(value) < 10^(precision-scale)`. Thus `1.2300` satisfies scale 2 (exactly representable), while `1.231` does not; `1000` does not fit `DECIMAL(5,2)`; `999.99` does. The distinction between numeric value and the number of characters typed is intentional; formatting/trailing-zero display belongs to presentation metadata.

Absent `precision`/`scale` means no additional decimal-geometry restriction beyond the general **4096 total input numeric digits** safety ceiling (not counting sign or point). All comparisons, `multipleOf` and limits use exact decimal arithmetic, not binary floating point. Numeric constraint strings use the same non-exponent plain-decimal lexical grammar. Those strings are interpreted mathematically, not by their textual byte representation.

### 4.3 Text types and Unicode

`STRING` and `TEXT` accept the same class of **valid Unicode scalar sequences**. Their tags remain different for future semantic/presentation use, but neither imposes an implicit maximum length, trimming, whitespace prohibition, NFC normalization, case conversion or storage mapping. Both may use `minimumLength`, `maximumLength` and `pattern`. There is no SQL `VARCHAR`/`TEXT` implication.

Text length is measured in **Unicode code points (scalar values)**, not UTF-8 bytes, UTF-16 code units or grapheme clusters. A supplementary-plane emoji counts as one point; a decomposed letter plus combining mark counts as two. Invalid Unicode or an unpaired surrogate is not a text value. Different normalization forms remain different values.

### 4.4 `ENUM`

`ENUM` is a string equal to exactly one of the declaration's `enumValues` under **code-point-exact, case-sensitive** equality. Values are nonempty, unique and preserve authored order in resolved definitions. The optional text constraints (`minimumLength`, `maximumLength`, `pattern`) MAY further restrict the allowed set; **all declared values must themselves satisfy them**, otherwise the *definition* is invalid. No automatic localization or display label is inferred from an ENUM literal; that is a future metadata concern.

### 4.5 `UUID`

Accept exactly 36-character hyphenated UUID text of the shape `8-4-4-4-12` hexadecimal digits. Uppercase or lowercase hexadecimal input is permitted; canonical output is lowercase. No braces, `urn:uuid:` prefix or hyphenless forms. No particular UUID version is required, and the all-zero UUID is structurally valid at this layer. Business restrictions on identity belong to the ERP.

### 4.6 `DATE`, `TIME`, `DATETIME`

- `DATE`: precisely `YYYY-MM-DD`, four-digit Gregorian year `0001`–`9999`, and an actual calendar day. No offset or timezone; unchanged canonical form.
- `TIME`: `HH:mm:ss` with optional `.` followed by **1–7** decimal fractional digits. `HH=00..23`, `mm/ss=00..59`; no leap seconds or `24:00:00`. Canonical form always `HH:mm:ss.fffffff` (seven digits, right-padded with zeroes). A time has no date or timezone.
- `DATETIME`: an instant expressed as `YYYY-MM-DDTHH:mm:ss`, optional 1–7 fractional digits, and a **mandatory** `Z` or numeric offset `+HH:mm` / `-HH:mm`. Input offsets are limited to **±14:00**, with `14:00` as the only permitted `14`-hour offset; lower hours may have minutes `00..59`. Offset arithmetic is exact. Output is `YYYY-MM-DDTHH:mm:ss.fffffffZ`, normalized to UTC. A UTC result outside year `0001`–`9999` is rejected.

A `DATETIME` without an offset, locale-specific timestamps, lower-case `t`/`z`, reduced precision date, invalid day, leap second, or more than seven fractional digits is rejected. Daylight-saving ambiguity is not relevant to an instant carrying an explicit offset. **No system default timezone is consulted.**

### 4.7 `BINARY`

Input is strict RFC 4648 **standard Base64** (`A–Z`, `a–z`, `0–9`, `+`, `/`, trailing `=` padding), with no whitespace, line breaks, URL-safe alphabet, omitted required padding, or noncanonical unused padding bits. Decode then re-encode MUST equal the input. The empty string represents zero bytes. `minimumLength` and `maximumLength`, if present, count **decoded bytes**, not encoded text length. The dictionary never infers a MIME type, filename or storage encoding from `BINARY`.

### 4.8 `BOOLEAN`

Only true boolean values are valid. Strings `"true"`, `"false"`, numbers `0/1` and truthy/falsy conversions are rejected by the neutral value codec.

## 5. Constraints — legal types and semantics

Only the following keys are permitted within `constraints`. All constraints are **intrinsic** to the dictionary element.

| Key | Allowed element types | Definition / semantics |
| --- | --- | --- |
| `minimum` | All integers, `DECIMAL` | Exact numeric lower bound, represented as a quoted numeric string |
| `maximum` | All integers, `DECIMAL` | Exact numeric upper bound, represented as a quoted numeric string |
| `exclusiveMinimum` | All integers, `DECIMAL` | Boolean: when true, value must be strictly greater than `minimum` |
| `exclusiveMaximum` | All integers, `DECIMAL` | Boolean: when true, value must be strictly less than `maximum` |
| `multipleOf` | All integers, `DECIMAL` | Exact strictly positive divisor; value/divisor must be an integer |
| `precision` and `scale` | `DECIMAL` only | Paired geometry as §4.2; JSON/YAML integers |
| `minimumLength` | `STRING`, `TEXT`, `ENUM`, `BINARY` | Inclusive minimum Unicode points or decoded bytes |
| `maximumLength` | `STRING`, `TEXT`, `ENUM`, `BINARY` | Inclusive maximum Unicode points or decoded bytes |
| `pattern` | `STRING`, `TEXT`, `ENUM` | Portable full-string regular-expression subset defined in §5.2 |

Unrecognized or inapplicable constraint keys are definition errors, **not** ignored annotations. Numeric bounds MUST use the matching integer or decimal lexical grammar, and MUST be valid within the element's declared numeric domain; `multipleOf` MUST be positive and exact. For integers `multipleOf` MUST be an integer. If an exclusivity flag is present and true, its corresponding bound MUST exist; a false flag without a bound is allowed but has no effect. Default exclusivity is false.

`minimumLength`, `maximumLength` are nonnegative integral values; an explicit maximum below the minimum is a definition error. Numeric bounds with `minimum > maximum`, or equal bounds with an exclusive endpoint, are definition errors. These checks identify straightforward contradictions; the MVP is **not** a general satisfiability solver for arbitrary combinations of `pattern`, `multipleOf`, and other restrictions.

A value violating a constraint is invalid; ARP MUST NOT truncate, clamp, coerce or round to make it pass. Format validation happens before constraints so invalid lexemes do not create spurious range errors.

### 5.1 Length and equality

Equality for text and ENUM is code-point-exact. `pattern` and lengths evaluate original input without implicit normalization. For BINARY, length is decoded byte count. For UUID/DATE/TIME/DATETIME, the MVP permits **no additional generic constraints**; their strict grammar/normalization is already part of the type. Business validation belongs to ERP callables.

### 5.2 Portable MVP `pattern` language

An unrestricted PCRE/Java/.NET regular-expression string would yield different semantics across stacks. The MVP instead defines **full-string matching** over a deliberately limited ASCII expression subset:

- Permitted: printable ASCII literal characters; escaped ASCII punctuation; positive ASCII character classes with literal characters and ranges such as `[A-Z0-9_-]`; concatenation; per-atom quantifiers `?`, `*`, `+`, `{n}`, `{n,m}`; optional leading `^` and trailing `$` (redundant under full-string matching).
- Quantifier counts are decimal integers `0..1024`, with `m >= n` and no leading zeros except `0`. A pattern contains at most **512 ASCII characters**. A validated value with `pattern` contains at most **4096 Unicode code points**; larger inputs receive `DICTIONARY_LIMIT_EXCEEDED`, not a misleading pattern mismatch.
- Disallowed in this generation: capturing/noncapturing groups, alternation, lookaround, backreferences, shorthand classes (`\d`, `\w`, `\s`), Unicode property classes, flags, inline modifiers, named captures, nested quantifiers, backtracking controls, dot wildcard, negative character classes, engine-specific escapes and any non-ASCII pattern character.
- `^` may occur only at the beginning, `$` only at the end; they are redundant because matching already covers the full input. A hyphen within a character class is literal only at the beginning/end or when escaped. A literal metacharacter must be escaped according to the grammar; otherwise it is invalid.
- Pattern grammar is checked on **definition ingestion**. Implementations MAY translate it into their host regex library, but MUST retain exactly the accepted language and outcomes in the shared fixtures; they must not expose extra host-engine constructs as conformant.

#### 5.2.1 Formal grammar and lexical rules

The following EBNF operates on decoded pattern characters, not JSON/YAML escape
bytes. Square brackets denote optional EBNF terms, braces denote repetition, and
quoted terminals are literal pattern characters.

```ebnf
pattern     = [ "^" ], atom, { atom }, [ "$" ];
atom        = primary, [ quantifier ];
primary     = literal | escape | class;
quantifier  = "?" | "*" | "+" | "{", count, [ ",", count ], "}";
count       = "0" | nonzero, { digit };
class       = "[", classBody, "]";
classBody   = [ "-" ], { classItem }, [ "-" ];
classItem   = classChar, [ "-", classChar ];
classChar   = classLiteral | escape;
escape      = "\", punctuation;
digit       = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
nonzero     = "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
```

- Every decoded character MUST be printable ASCII U+0020..U+007E, including
  escaped characters. U+0000..U+001F, U+007F and all non-ASCII characters are
  invalid. A backslash followed by a letter/digit/space is not an escape.
- `punctuation` is ASCII punctuation U+0021..002F, U+003A..0040,
  U+005B..0060 or U+007B..007E. Escapes denote the escaped character literally;
  `\n`, `\x41`, `\u0041`, shorthand classes and backreferences are forbidden.
- `literal` is printable ASCII except `. ^ $ * + ? { } [ ] \ ( ) |`.
  `classLiteral` is printable ASCII except `\ [ ] ^ -`. Other punctuation has
  literal meaning inside a class. A raw caret is never a class literal;
  an escaped caret is literal, not negation.
- `classBody` MUST contain at least one decoded member. To disambiguate raw
  hyphens, first consume a raw hyphen at the start and/or end as literal members;
  then parse the remaining items left to right. An interior raw hyphen joins the
  immediately preceding and following `classChar` as one inclusive range.
  Endpoints cannot be reused by another range; a remaining raw hyphen is invalid.
  Escaped hyphens are ordinary `classChar` values. Thus `[-a-z]`, `[a-z-]`,
  `[-]`, `[a-a]` and `[\-]` are valid; `[]`, `[^a]`, `[z-a]` and `[a-b-c]` are not.
- Range endpoints are compared by ASCII code point and MUST be ascending or
  equal. Counts MUST be 0..1024, without leading zeros except `0`; in `{n,m}`,
  `m >= n`. `{n,}` is not permitted. Only one quantifier may follow a primary.
- The pattern MUST contain an atom: `""`, `^`, `$`, `^$` are invalid. A valid
  pattern may still match an empty value (for example `a*` or `a{0}`). Length
  includes anchors, escapes and quantifiers and MUST NOT exceed 512 characters;
  excess length is `DICTIONARY_LIMIT_EXCEEDED`. Other grammar violations are
  `DICTIONARY_ELEMENT_INVALID` on definition ingestion.
- Unescaped anchors occur only at the outer boundaries. Escaped `\^`/`\$`
  are literals. Full-string matching applies with or without anchors, including
  a final newline in the input: there is no host-engine end-anchor exception.

This is adequate for identifiers such as `^[A-Z0-9-]+$`. Sophisticated or Unicode-aware patterns can be proposed in a later format generation, or validated by ERP domain functions using a future domain bridge. **Do not quietly weaken these restrictions per language.**

## 6. Sources, catalog construction and lookup

A consuming application registers zero or more **active source providers** with ARP. Each provider supplies one or more immutable input snapshots plus a trusted, opaque `providerId` and `sourceId` for diagnostics. These identifiers are diagnostic identities only; ARP does not infer source paths, framework modules or filesystem structure. The application decides which modules/providers are enabled and which catalog context they belong to.

A catalog build MUST:

1. Obtain the application's explicitly selected active source snapshots.
2. Parse each document using the declared format.
3. Validate its shape and every scalar definition semantically.
4. Reject any duplicate fully qualified element ID across **all active sources**, even if the repeated definitions are byte-identical.
5. Publish the complete resolved catalog **atomically** only when every active source is valid.
6. Make `resolve(id)` return a deterministic immutable element descriptor, or a typed `DICTIONARY_ELEMENT_NOT_FOUND` result. Resolution is case-sensitive and never makes fallback guesses.

If a build fails, its partial result MUST NOT become the active catalog. A previously published snapshot MAY remain in service under a separately identified catalog generation; it MUST NOT be presented as if the failed new catalog was accepted. A consumer must not observe half of a replacement catalog.

Catalog ordering is **not semantically relevant**: providers and element order must not change duplicates, resolution or validity. Catalog enumeration, if exposed, uses ascending ASCII/Unicode-code-point order of element IDs. Source provenance and trusted diagnostic data must be available for error reporting, but must not become ERP business rules.

Any caching is scoped to the **specific application/catalog context**. Implementations MUST NOT leak definitions between tenants or applications and must not assume all installations share one global catalog. This MVP has no aliasing, overlay precedence, automatic hot reload, cross-catalog resolution, schema migrations or remote provider protocol. Future providers may supply sources from packages, memory or remote stores through adapters.

### 6.1 Minimum contractual resolved descriptor projection

A resolved scalar descriptor MUST expose this language-neutral projection:

| Property | Presence and meaning |
| --- | --- |
| `id`, `type` | Required; exactly the declared identity and scalar type |
| `constraints` | Required object; declared intrinsic constraints, or `{}` when absent |
| `enumValues` | Required exclusively for ENUM; preserve declared values and order; absent for other types |
| `label`, `description` | Present only when declared, with their exact Unicode text |

The projection does not add implicit constraint keys, contextual field/resource
metadata, presentation or persistence metadata. Numeric constraint strings retain
the declaration's representation; their mathematical interpretation remains §5.
This specifies observable data, not PHP/Java/.NET classes, interfaces or object
layout. Implementations may keep diagnostic provenance separately; it is not
part of the projection. Fixtures compare the whole contractual projection,
including absence of undeclared properties, without prescribing a native envelope.

## 7. Abstract operations and observable results

This specification defines observable behavior, **not** Java/PHP/.NET class or method names. Implementations MAY choose native APIs that implement these conceptual operations:

- `buildCatalog(activeSources)` → immutable resolved catalog or structured definition issues.
- `resolve(catalog, elementId)` → resolved scalar descriptor or not-found issue.
- `validate(catalog, elementId, portableValue)` → success with typed/canonical portable value, or structured validation issues.

Fixtures represent operations in JSON, for example:

```json
{
  "operation": "validate",
  "elementId": "finance.amount",
  "value": "1.2300"
}
```

A success is represented for test purposes as:

```json
{
  "valid": true,
  "normalizedValue": "1.23",
  "issues": []
}
```

A failure never invents a normalized value:

```json
{
  "valid": false,
  "issues": [
    {
      "code": "DICTIONARY_VALUE_CONSTRAINT",
      "elementId": "catalog.productCode",
      "constraint": "maximumLength"
    }
  ]
}
```

`normalizedValue` MUST be absent on failure; it MAY be absent for catalog/resolve operations that do not have scalar values. Business text, localized messages, stack traces, HTTP status or framework exception names are **not** part of the portable outcome.

### 7.1 Stable error families

| Code | When |
| --- | --- |
| `DICTIONARY_DOCUMENT_INVALID` | Invalid source syntax, forbidden YAML construct, duplicate mapping key or unexpected document shape |
| `DICTIONARY_FORMAT_UNSUPPORTED` | Unknown or missing `apiVersion` after a syntactically valid root object |
| `DICTIONARY_ELEMENT_INVALID` | Invalid element identity/type/constraint configuration, including illegal pattern grammar |
| `DICTIONARY_DUPLICATE_ELEMENT` | Repeated qualified ID across active source definitions |
| `DICTIONARY_ELEMENT_NOT_FOUND` | Unregistered ID on lookup/validation |
| `DICTIONARY_VALUE_TYPE` | Scalar input of wrong portable JSON kind or invalid lexical/Unicode/temporal/Base64 representation |
| `DICTIONARY_VALUE_CONSTRAINT` | A well-formed value fails a declared numeric/text/ENUM constraint or built-in numeric type bound |
| `DICTIONARY_LIMIT_EXCEEDED` | Explicit security limit applicable to document/value/pattern input exceeded |

For definition and duplicate errors, each issue SHOULD carry diagnostic `providerId`, `sourceId`, `elementId` (where known) and JSON Pointer path (when known). Value issues MUST carry `elementId`; constraint failures MUST carry the violated constraint name. An implementation MAY add non-contract diagnostic messages, but semantic tests cannot depend on them. Internal errors and resource failures must not be mislabeled as business-invalid values.

A type/lexical failure suppresses constraint checks for that value. For a well-typed value, applicable constraint failures are returned in fixed order: **`typeRange` (built-in integer type range); `minimum`; `maximum`; `multipleOf`; `precision`; `scale`; `minimumLength`; `maximumLength`; `pattern`; `enumValues`**. The same ordered conditions must yield the same `issues` across stacks. Exact parser line/column diagnostics may differ and are excluded from conformance comparisons.

`typeRange` is the normative constraint name for an integer outside its intrinsic
inclusive bounds (§4.1). It is not a legal declaration key. A negative unsigned
lexeme is `DICTIONARY_VALUE_TYPE`, not a range violation. A numeric input exceeding
the 4096-digit safety ceiling is `DICTIONARY_LIMIT_EXCEEDED`, not `typeRange`.

### 7.2 Intake classification and multiple definition defects

The following layers distinguish failures; JSON Schema alone does not choose a
portable error family:

- **Syntax/intake:** malformed encoding or syntax, duplicate mapping keys,
  forbidden YAML constructs, multiple roots or invalid Unicode:
  `DICTIONARY_DOCUMENT_INVALID`. Format dispatch requires a parsed object.
- **Format:** a missing or unsupported `apiVersion` in a parsed root object:
  `DICTIONARY_FORMAT_UNSUPPORTED`. This includes a non-string format value.
- **Document structure:** a non-object root, invalid top-level keys, missing/invalid `elements`
  container, empty array, or a non-object element entry:
  `DICTIONARY_DOCUMENT_INVALID` for the supported format.
- **Element structure/semantics:** missing, unknown or incorrectly typed element
  properties, invalid identity/type, inappropriate constraints, invalid ENUM
  declarations, pattern grammar or contradictory constraint configuration:
  `DICTIONARY_ELEMENT_INVALID`, except explicit security-limit violations which
  use `DICTIONARY_LIMIT_EXCEEDED`. Repeated IDs use `DICTIONARY_DUPLICATE_ELEMENT`.

These categories classify individual defects and prerequisites of intake; they
MUST NOT be read as a global ordering or accumulation policy for simultaneous
definition defects. This MVP does not require all such issues, a first issue,
or any global order among them. Fixtures that assert one definition error isolate
that defect. The fixed ordering in §7.1 applies to constraint failures of one
well-typed scalar value, not to multiple definition errors.

## 8. Portability, safety and resource limits

- **No implicit coercion:** no string-to-boolean, `"123"`-to-STRING when expecting an integer by guessed context, loss of integer precision, binary floating-point rounding, string trimming, local time zone assumptions or unknown-key ignoring.
- **Resource ceilings:** documents MAY have implementation-configurable limits, but the default conformance profile MUST accept at least **1 MiB UTF-8** and **2048 elements per source**. Numeric lexical inputs above 4096 digits, patterns above 512 ASCII chars, or pattern-matched values above 4096 code points MUST be rejected with the declared limit code. Implementations MAY reject larger documents with `DICTIONARY_LIMIT_EXCEEDED` if the configured limit is disclosed, but conformance tests use values below the baseline.
- **Safe parsing:** no arbitrary-object construction or code execution from YAML, no untrusted handler names interpreted as executable code, no external document `$ref` fetch, no filesystem/network access during bare value validation.
- **Snapshot consistency:** validation always uses one fully built catalog snapshot; changing an ERP module's effective source selection requires a new build, not in-place mutation visible to concurrent validations.
- **Optionality:** dictionary-only consumption requires no module manager, database, UI, messaging, HTTP or domain dispatcher.

## 9. Shared conformance suite — minimum inventory

Codex must create portable fixtures with explicit **input, expected validity, normalized output on success, or code/constraint on failure**. Each fixture must identify the approved format and test only this feature's boundary. At minimum:

| Area | Required cases |
| --- | --- |
| Source document | Valid YAML and equivalent JSON; missing/unknown format; duplicate mapping keys; unknown keys; malformed root; forbidden YAML aliases/tags/multiple documents; invalid UTF-8 |
| Catalog | Several providers; resolution across providers; order independence; duplicate ID across documents/providers; same ID repeated within document; atomic build rejection; missing element; two isolated catalog contexts |
| Identity | Valid qualified IDs; missing dot; leading digit; empty segment; excess length; case-sensitive pair |
| Type catalogue | One positive example for **each of the 17** types; unknown type; inapplicable constraint; ENUM without values |
| Integers | Exact inclusive bounds and one outside each end for all seven signed/unsigned variants; `INT64` values beyond JS safe integer; negative unsigned; `-0`; leading zero/exponent/plus sign/wrong JSON kind |
| Decimal | `1.2300`→`1.23`; `-0.00`→`0`; `DECIMAL(5,2)` accepting `999.99` and rejecting `1000`/`0.001`; exact max/min; exact `multipleOf` (`0.3` vs `0.1`); no float rounding; malformed exponent |
| Unicode/text | ASCII and supplementary character length; decomposed accent length; empty text; combining mark; no trim/NFC; invalid surrogate; minimum and maximum length |
| Pattern | `^[A-Z0-9-]+$` positive/negative; full-match instead of substring; unsupported `\d`, lookaround, groups, non-ASCII or overlong regex; long input limit |
| ENUM | Declared literal; unknown/case variant; duplicate declared value; empty list; incompatible declared-value constraints; stable declaration order |
| UUID | Lowercase and uppercase accepted; lowercase normalization; malformed shape; invalid hex; nil UUID structural acceptance |
| DATE | Leap years 2000/1900; month/day errors; year `0000`; invalid timezone/suffix |
| TIME | Missing fraction→seven zeros; 1 and 7 digits; invalid hour/second; 8 fractions; leap second |
| DATETIME | `Z` normalization; positive/negative offset crossing a day; 7-digit retention; missing offset; too-large offset; UTC out-of-range |
| BINARY | Empty bytes; padded canonical payload; decoded byte lengths; invalid alphabet/padding/whitespace/nonzero pad bits |
| Constraints | Missing/false/true exclusivity; equal exclusive endpoints; inverted numeric bounds; multipleOf zero; precision without scale; scale above precision; negative length; wrong constraint type; value failing multiple conditions in specified order |
| Isolation and errors | Exact portable error categories; no normalized value on failure; no business code/HTTP leakage; stable ordering independent of providers |

**Fixture format recommendation (not yet a claim of existing tests):** `fixtures/dictionary/v1/valid/`, `invalid-definitions/`, `values/` with a manifest mapping source snapshots to expected outcomes. A minimal offline fixture runner should verify the schema separately from semantic conformance. No language-specific expected result is permitted.

## 10. Acceptance criteria and handoff to Codex

`ARP-DICT-001` can be considered **contract-ready for release review** when:

1. This specification has been reviewed and adjusted for contradictions; target and MVP remain clearly distinct.
2. A versioned JSON Schema for `arp.dictionary/v1` enforces the closed document shape, per-type allowed constraints, ID syntax and portable lexical attributes to the degree JSON Schema can express. YAML duplicate keys and semantic predicates have additional independent checks.
3. The fixture suite includes all areas in §9 and is deterministic across languages.
4. The specification and fixtures define the same accepted/rejected inputs; every disputed boundary has a concrete expected example.
5. The repo's `CHANGELOG.md`, `releases/v0.1.0.md` and release inventory are prepared, but **no tag is created until review and required contract checks pass**.
6. `docs/compatibility.md` does not claim Java/.NET/PHP adoption unless their own pinned conformance runs and evidence exist.

**Implementation sequence proposed after design approval:**

- **Phase A — `arp-contract`:** schema(s), fixture manifest, offline checks and normative reconciliation. Codex must report any unimplementable/ambiguous rule without silently redefining it.
- **Phase B — independent stacks:** implement source registration, catalog build/resolve and scalar validation in `arp-php`, `arp-java`, `arp-dotnet` against the exact same contract fixtures; report per-stack support/evidence separately. A staged implementation may be partial but cannot claim full conformance until all required fixtures pass.
- **Phase C — consuming integration:** use a real ERP module to reuse one dictionary element in multiple contexts, without presuming database schemas, migrations or UI metadata. Later metadata/domain features extend this integration.

## 11. Architectural risks and explicit deferrals

- **High-risk, fixed for this candidate:** stable qualified IDs; exact decimal/integer semantics; separate presence/nullability; portable temporal meaning; closed versioned format; non-overwriting catalog registry; dictionary independent of infrastructure. Changing any after publication needs deliberate compatibility review.
- **Deliberate trade-off:** the restricted portable pattern subset is intentionally smaller than the regex features offered by host languages. A later format may widen it, but current conformance must be identical.
- **Deliberate trade-off:** neutral fixture numbers use strings; this does not establish the wire serialization of a future HTTP resource/field. That mapping is a separate versioned feature.
- **Deferred and reversible:** class names, library package structure, registration API ergonomics, cache algorithm, host-native overloads, directory packaging, consumer-specific defaults and presentation.
- **No migration guarantee:** existing `erbas-contract` schemas are historical and unchanged; applications under development may switch with explicit adapters or deliberate contract upgrades.

## 12. Relationship to governance

This document is an **approved implementation design, still unpublished**, not a published release or proof that any implementation conforms. It must be reviewed with [`docs/architecture.md`](../architecture.md), [`docs/versioning.md`](../versioning.md) and [`docs/compatibility.md`](../compatibility.md). The first actual normative snapshot requires an approved schema, fixtures, checks, release inventory and immutable tag under the published process. The next developer step is **implementation of an approved design**, not delegation of its architectural decisions.
