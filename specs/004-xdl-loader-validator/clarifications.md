# Clarification record: XDL loader, validator, and normalizer

**Date**: 2026-09-20
**Method**: Spec Kit ambiguity scan against approved M2 schemas, examples, ADRs, and validation contract.

| ID | Area | Decision | Effect |
|---|---|---|---|
| C01 | Capability boundary | Complete the implementation half of M2 before M3. | Delivers document loading/validation/normalization but no runtime or legacy adapter. |
| C02 | Resource discovery | The input arguments form a closed resource set; no implicit filesystem, registry, or network resolution. | Makes validation deterministic, offline, and public-safe. |
| C03 | File packaging | Accept exactly one resource per UTF-8 YAML or JSON file. | Bundle/import and multi-document semantics remain deferred. |
| C04 | Element identity | Require IDs to be unique across the entire owning resource. | Removes ambiguity because ElementRef has no collection field; preserves current examples and reference syntax. |
| C05 | Profiles | Require Profile resources plus explicitly supplied local schemas whose `$id` equals `schemaRef`. | Extension validation fails closed without enabling schema networking. |
| C06 | Validation flow | Stop progression after a gate has errors but collect deterministic independent errors within that gate. | Prevents cascaded interpretations while returning useful feedback. |
| C07 | Readiness | Evaluate static completeness and return `Ready`, `NotReady`, or `NotEvaluated`; never probe live systems. | Honest readiness evidence without runtime scope expansion. |
| C08 | Normalization | Return no normalized resources unless every resource passes gates 1–4. | Avoids partial graphs and implicit best-effort behavior. |
| C09 | Output | Canonical JSON sorts keys and excludes presentation-only source locations from semantic equality. | Equivalent YAML and JSON can compare deterministically. |
| C10 | Safety limits | Default to 5 MiB per file, 100 nesting levels, 100,000 traversed nodes, and 1,000 resources; callers may lower bounds. | Bounds untrusted-input work without provider assumptions. |

No unresolved clarification remains. Registry governance, network retrieval, Bundle/import, conversion,
signatures, runtime-plan compilation, orchestration, adapters, and live readiness remain deferred.
