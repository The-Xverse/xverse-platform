# T018 Detailed Design — `src/xverse_xdl/xcom_plan.py` Deterministic Plan Compiler

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T018 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `56506d2c9cb71791cba06a1cc418fcadee72e0fa` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Input grammar authority | `xdl/profiles/xcom-v0.1.schema.json` (T017) and `specs/007-xcom-core/contracts/xdl-profile.md` |
| Output schema authority | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (T017) and `specs/007-xcom-core/contracts/communication-plan.md` |
| Reference implementation | `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `validate_plan_structure`, `check_digest`) |
| Governing ADRs | ADR-0016, ADR-0018, ADR-0020 |
| Language / tooling | Python 3.11+ standard library plus sibling `xverse_xdl` models at import time; `jsonschema`/`referencing` only in the T017 validator the tests load |

This design is written **before** implementation. The implementation must realise every named identifier and
rule. The identifiers below are fixed by this document; the plan member names are the T017 schema's interface.

## 2. Fixed identifiers and vocabularies

### 2.1 Artifact identifiers

| Identifier | Path |
| --- | --- |
| `COMPILER` | `src/xverse_xdl/xcom_plan.py` |
| `COMPILER_TESTS` | `tests/test_xcom_plan.py` |
| `PROFILE_SCHEMA` | `xdl/profiles/xcom-v0.1.schema.json` |
| `PLAN_SCHEMA` | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` |
| `PLAN_VALIDATOR` | `scripts/validate_xcom_plan.py` |
| `PLAN_DOCS` | `docs/engineering/xcom/t018/` |
| `XDL_EXAMPLES` | `xdl/examples/v1alpha1/` (anchor only; never changed) |

### 2.2 Closed vocabularies and constants

| Name | Value |
| --- | --- |
| `TASK_ID` | `"T018"` |
| `GENERATOR_VERSION` | `"0.1.0"` |
| `PLAN_VERSION` | `"1"` |
| `PROFILE_NAMESPACE` | `"io.xverse.xcom"` |
| `DEFAULT_GENERATED_AT` | `"1970-01-01T00:00:00Z"` |
| `PLAN_DOMAIN_SEPARATOR` | `b"xverse.xcom.activation-plan.v1\x00"` |
| `GRAPH_DOMAIN_SEPARATOR` | `b"xverse.xcom.normalized-graph.v1\x00"` |
| `SCOPE_KINDS` | `("System", "Component", "Deployment", "Scenario", "Profile")` |
| `PROVENANCE_KINDS` | `("Component", "Deployment", "Scenario")` (the plan `resourceRef.kind` enum excludes `System`) |
| `INTERFACE_KINDS` | `("interface-policy", "flow-policy", "network-provider", "observation-policy", "validation-policy")` |
| `ENDPOINT_ROLES` | `("initiator", "responder")` (first proof; `observer`/`tool` are reserved and not emitted) |
| `CLOCK_SOURCES` | `("monotonic", "local-validation-clock", "unmapped")` |
| `OVERFLOW_POLICIES` | `("drop-oldest", "drop-newest", "coalesce", "lossless-backpressure", "reject", "fail-closed")` |
| `BACKPRESSURE_POLICIES` | `("fail-closed", "reject", "lossless-backpressure")` |
| `RESOLUTION_STATES` | `("resolved", "unresolved")` |
| `PLAN_STATUS` | `("inspectable", "activatable")` |
| `PLACEHOLDER_POLICY` | `{"ordering":"unordered","reliability":"best-effort","deadlineMs":0,"retry":0,"queueDepth":1,"overflow":"fail-closed","backpressure":"fail-closed"}` |
| `ERROR_CODES` | `XCOM-PLAN-INPUT`, `XCOM-PLAN-BOUND`, `XCOM-PLAN-IDENTITY`, `XCOM-PLAN-DUPLICATE`, `XCOM-PLAN-PROFILE`, `XCOM-PLAN-CONTRACT`, `XCOM-PLAN-POLICY`, `XCOM-PLAN-CAPABILITY`, `XCOM-PLAN-UNKNOWN` |
| `DIAGNOSTIC_CODES` | `XCOM-PLAN-IDENTITY-UNRESOLVED`, `XCOM-PLAN-SCHEMA-UNRESOLVED`, `XCOM-PLAN-CAPABILITY-UNRESOLVED`, `XCOM-PLAN-TIME-UNRESOLVED`, `XCOM-PLAN-OWNERSHIP-UNRESOLVED`, `XCOM-PLAN-POLICY-UNRESOLVED`, `XCOM-PLAN-POLICY-CONFLICT` |
| `PLAN_TARGET` | `"xcom-plan"` (the fixed diagnostic target for plan-level findings) |

Every `ERROR_CODES`/`DIAGNOSTIC_CODES` token matches the schema diagnostic pattern
`^XCOM-[A-Z0-9-]{3,64}$`. Every identifier emitted into the plan satisfies the plan identifier pattern
`^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$` (≤ 127 chars) because it is copied from an XDL identifier or a
namespace, both of which satisfy the stricter XDL pattern; a value that fails the plan pattern is rejected
with `XCOM-PLAN-INPUT` rather than rewritten.

### 2.3 Closed Profile v0.1 grammar table (drift-guarded against `PROFILE_SCHEMA`)

| `kind` | required `policy` members | all permitted members | legal attachment collections |
| --- | --- | --- | --- |
| `interface-policy` | `interactionKind`, `schemaId`, `schemaVersion`, `encoding`, `semanticCompatibility` | same (closed) | `interfaces`, or resource level iff the resource declares exactly one interface |
| `flow-policy` | `ordering`, `reliability`, `deadlineMs`, `retry`, `queueDepth`, `overflow`, `observationPoints` | same (closed) | `flows`, or System resource level |
| `network-provider` | `requiredCapabilities`, `fidelity`, `limitations` | same (closed) | `targets`, `networkBindings`, or Deployment resource level |
| `observation-policy` | `filters`, `payloadAccess`, `bounds`, `validityEffect` | plus optional `allowList` | `observers`, or Scenario resource level |
| `validation-policy` | `allowedActions`, `injectionPoints`, `serviceEmulation`, `timePolicy`, `quotas`, `permitPolicyRef` | same (closed) | `steps`, or Scenario resource level |

The compiler holds this table as constants and a test asserts it equals the corresponding `$defs` of
`PROFILE_SCHEMA` member-for-member (`CHK-06`), so the compiler grammar cannot silently drift from the
normative schema.

## 3. `COMPILER` public API (`T018-U-07`)

```python
from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class CompileLimits:
    max_bytes: int = 5 * 1024 * 1024
    max_depth: int = 100
    max_nodes: int = 100_000
    max_resources: int = 1_000
    max_endpoints: int = 4_096
    max_routes: int = 4_096
    max_providers: int = 256
    max_observation_points: int = 1_024
    max_clock_domains: int = 256
    max_diagnostics: int = 4_096

class XcomPlanError(Exception):
    code: str
    message: str

@dataclass(frozen=True)
class GraphView:
    resources: tuple[Mapping[str, Any], ...]

def load_normalized_graph(document: Any, *, limits: CompileLimits = CompileLimits()) -> GraphView: ...
def compile_plan(graph: Any, *, generated_at: str | None = None,
                 generator_version: str = GENERATOR_VERSION,
                 limits: CompileLimits = CompileLimits()) -> dict[str, Any]: ...
def compile_plan_text(text: str, *, generated_at: str | None = None,
                      generator_version: str = GENERATOR_VERSION,
                      limits: CompileLimits = CompileLimits()) -> dict[str, Any]: ...
def canonical_plan_bytes(plan: Mapping[str, Any]) -> bytes: ...
def compute_digest(plan: Mapping[str, Any]) -> str: ...
def plan_matches_digest(plan: Mapping[str, Any]) -> bool: ...
def plan_status(plan: Mapping[str, Any]) -> str: ...
```

- `__all__` lists exactly these public names plus the closed vocabularies needed by tests.
- `compile_plan` accepts a `GraphView`, a `{"resources": [...]}` document, or a sequence of resource mappings;
  any other value is `load_normalized_graph`'s job to reject.
- The return value is a fresh plain `dict` tree (JSON-compatible, no immutable wrappers), so the caller owns
  it (`caller-owns-value`). No module-level mutable state is retained between calls.

## 4. `T018-U-01` — Graph input loading and bounds

`load_normalized_graph(document, *, limits)`:

1. If `document` is a `GraphView`, take a detached resource snapshot and reapply the supplied limits; a reused view may have been created under looser limits.
2. If `document` is a sequence (not a string/bytes), treat it as the resource list; if it is a mapping, require
   the key `resources` and use its value. Otherwise `XCOM-PLAN-INPUT`.
3. Require `resources` to be a list; otherwise `XCOM-PLAN-INPUT`.
4. `len(resources) > limits.max_resources` → `XCOM-PLAN-BOUND`.
5. For each entry (in input order):
   - must be a mapping → else `XCOM-PLAN-INPUT`;
   - `identity` must be a mapping with non-empty string `apiVersion`, `kind`, `namespace`, `name` → else
     `XCOM-PLAN-INPUT`;
   - `kind` must be in `SCOPE_KINDS` → else `XCOM-PLAN-INPUT`;
   - walk the whole entry: reject a non-finite `float` (`XCOM-PLAN-INPUT`), track depth against
     `limits.max_depth` and node count against `limits.max_nodes` (`XCOM-PLAN-BOUND`);
   - reject a `namespace`/`name` that does not satisfy the plan identifier pattern (`XCOM-PLAN-INPUT`).
6. Duplicate identity tuple `(apiVersion, kind, namespace, name)` → `XCOM-PLAN-DUPLICATE`.
7. Return `GraphView(resources=tuple(sorted(entries, key=_identity_key)))` where `_identity_key` is the
   4-tuple above. Sorting makes the rest of the compiler independent of input resource order.

`compile_plan_text(text, ...)` measures `len(text.encode("utf-8"))` against `limits.max_bytes` first
(`XCOM-PLAN-BOUND`), then parses with `json.loads(object_pairs_hook=_reject_duplicate_members)` so a repeated
object member is `XCOM-PLAN-INPUT` (never collapsed last-wins), then delegates to `compile_plan`. The compiler
never opens a file, socket, or subprocess.

## 5. `T018-U-02` — Profile payload index (`T018-SR-002`)

### 5.1 Index construction

For each resource `r` in `GraphView.resources`, read `r.get("extensions", {})`. The normalized model stores,
per namespace, `{"profile": <uri>, "payloads": [{"pointer": <json-pointer>, "value": <payload>}, ...]}`. For the
namespace `PROFILE_NAMESPACE`:

1. `element = _attachment(pointer, r)`: strip the trailing `/extensions/io.xverse.xcom` token; the remaining
   parent path is either `""` (resource level) or `/spec/<collection>/<index>` for one of the collections in
   §2.3. A pointer that does not fit either shape → `XCOM-PLAN-PROFILE`.
2. `(collection, index)`; the decorated element id is `r["content"]["spec"][collection][index]["id"]` when the
   collection is a list of id-bearing objects, else `None` (resource level).
3. Validate the payload `value` structurally against §2.3: closed top level
   `{schemaVersion, kind, target, policy}`; `schemaVersion == "0.1"`; `kind` in `INTERFACE_KINDS`; `target` a
   closed object `{apiVersion, kind, namespace, name, version?}`; `policy` a closed object with exactly the
   form's members for the declared `kind` (the union table of §2.3). Violation → `XCOM-PLAN-PROFILE`.
4. Verify the attachment is legal for the `kind` per §2.3; illegal collection, or a resource-level
   `interface-policy` on a resource that declares more than one interface → `XCOM-PLAN-PROFILE`.
5. Verify `target` names the attachment resource: `apiVersion`, `kind`, `namespace`, `name` must equal the
   attachment identity; otherwise the payload is **not applied** and the `identity` family is marked
   `unresolved` with `XCOM-PLAN-IDENTITY-UNRESOLVED` targeting the attachment resource name. A `target.version`
   that is present must equal `r["revision"]`, else the same unresolved outcome.
6. Duplicate: if `(attachment identity, kind)` was already indexed by a distinct payload → `XCOM-PLAN-PROFILE`
   (duplicate/conflicting policy for the same decorated identity).

The index is a sorted tuple of frozen records `(resource_key, kind, collection, element_id, payload)`, sorted
by `(kind, resource_key, collection, element_id or "")`, so iteration is deterministic.

### 5.2 Placement and safety

Because each form's member set is closed, any address, credential, permit, handle, or session member is an
unknown member and is rejected (`XCOM-PLAN-PROFILE`). The compiler never copies payload content into the plan;
it copies only the declared policy fields listed in §7.

## 6. `T018-U-03` — Contracts, endpoints, routes, providers

All lookups use the sorted resource index; all derived collections are sorted by their plan key.

### 6.1 Scope selection

- Collect `System` resources. Exactly one required; zero or more than one → `XCOM-PLAN-IDENTITY`.
- `deployments` = `Deployment` resources whose `spec.systemRef` equals the selected System identity;
  `scenarios` = `Scenario` resources whose `spec.systemRef` equals the System identity.
- More than one deployment or more than one scenario → `XCOM-PLAN-IDENTITY`. Zero is permitted (the
  corresponding families become unresolved); one is `deployment`/`scenario`.

### 6.2 Contracts

For each indexed `interface-policy` applied to an interface element in scope (the System, or a Component
reachable from the System's `componentInstances`), emit
`{"contractId": <interface id>, "schemaId": <policy.schemaId>, "schemaVersion": <policy.schemaVersion>}`.
`schemaId` must satisfy the plan identifier pattern and `schemaVersion` the plan version pattern; otherwise
`XCOM-PLAN-CONTRACT`. Contracts are sorted by `contractId`; a duplicate `contractId` from two interfaces →
`XCOM-PLAN-DUPLICATE`.

### 6.3 Endpoints

Collect the System `spec.endpoints` (each `{id, ownerId, interfaceId, direction}`). For each endpoint:

- `initiator` if its `id` equals a flow `sourceEndpointId`;
- `responder` if its `id` appears in a flow `destinationEndpointIds`;
- both → `XCOM-PLAN-IDENTITY` (conflicting roles);
- neither → map `direction`: `output` → `initiator`, `input` → `responder`, `bidirectional` → `XCOM-PLAN-IDENTITY`
  (ambiguous role; the compiler does not guess).

Emit `{"endpointId": id, "role": role}`, sorted by `endpointId`; duplicate endpoint ids → `XCOM-PLAN-DUPLICATE`.

### 6.4 Routes

For each System `spec.flows` entry `f`:

- require `f["interfaceId"]`, `f["sourceEndpointId"]`, `f["destinationEndpointIds"]` present; a flow with a
  number of destinations != 1 → `XCOM-PLAN-IDENTITY` (multi-destination naming is out of first-proof scope and
  is not invented);
- `routeId = f["id"]`, `from = sourceEndpointId`, `to = destinationEndpointIds[0]`, `contractId = f["interfaceId"]`;
- `source`/`destination` must be declared endpoint ids, else `XCOM-PLAN-IDENTITY`;
- emit `{"routeId", "from", "to", "contractId"}`, sorted by `routeId`; duplicate route ids → `XCOM-PLAN-DUPLICATE`.

`activationOrder` (U-04) is composed from the endpoint and route ids; if any route id equals an endpoint id →
`XCOM-PLAN-DUPLICATE` (the `activationOrder` must be duplicate-free). If no endpoint and no route exist →
`XCOM-PLAN-IDENTITY` (the schema requires at least one `activationOrder` entry).

### 6.5 Providers

For each `network-provider` payload attached to a Deployment in scope (target, network binding, or resource
level):

- `providerId` = the decorated element id, or the Deployment `metadata.name` at resource level; a
  `providerId` not satisfying the plan identifier pattern → `XCOM-PLAN-INPUT`;
- `capabilities` = the Deployment target's declared `spec.targets[<i>].capabilities` when the payload is
  attached to a target, else the union of all target capabilities for the referenced realization (sorted,
  unique), and `[]` when the Deployment declares none;
- `requiredCapabilities` = the payload's `requiredCapabilities` (sorted, unique);
- emit `{"providerId", "capabilities", "requiredCapabilities"}`, sorted by `providerId`; duplicate
  `providerId` → `XCOM-PLAN-DUPLICATE`.

The `capability` family is `unresolved` when a route exists but no provider is selected, or when any
provider's `requiredCapabilities` is not a subset of its `capabilities` (`XCOM-PLAN-CAPABILITY-UNRESOLVED`
targeting the `providerId`). `capabilities` is never invented: an absent declaration yields `[]` and an
unresolved capability state, not a fabricated capability.

## 7. `T018-U-04` — Policies, observation, stimulation, clocks, activation order

### 7.1 Policies

Sources: every indexed `flow-policy` applied in scope. For each of `ordering`, `reliability`, `deadlineMs`,
`retry`, `queueDepth`, `overflow`, collect the declared value from each source. The effective value is:

- the single distinct declared value when the sources agree;
- the deterministic least element (first in the schema enum order for enums, numeric minimum for integers)
  when they differ, with `policy` marked `unresolved` and a `XCOM-PLAN-POLICY-CONFLICT` diagnostic targeting
  the lexicographically-first route id or `PLAN_TARGET` when no route exists;
- `PLACEHOLDER_POLICY`'s value for a field with no source, with `policy` marked `unresolved` and a
  `XCOM-PLAN-POLICY-UNRESOLVED` diagnostic.

`backpressure` is mapped deterministically from `overflow`: `lossless-backpressure` →
`lossless-backpressure`; `fail-closed` → `fail-closed`; every other overflow → `reject`. When `policy` is
unresolved the full `PLACEHOLDER_POLICY` object is recorded, so the emitted plan is schema-valid and
inspectable but cannot activate.

### 7.2 Observation points

For each Scenario in scope, for each `spec.observers` entry `o`:

- `tapId = o["id"]`; `o["id"]` must satisfy the plan identifier pattern else `XCOM-PLAN-INPUT`;
- resolve `o["targetRef"]`: require `kind == "System"` and `targetRef.element` equal to a declared route id
  (a flow id) in scope; otherwise `XCOM-PLAN-IDENTITY`;
- find an `observation-policy` attached to that observer element; if present, `payloadAccess` and
  `validityEffect` come from it (`allow-listed` additionally requires `allowList`, already enforced by the
  closed grammar and the `allOf` of `PROFILE_SCHEMA`; the plan schema records only `payloadAccess` and
  `validityEffect`);
- if no `observation-policy` is attached, record the declared least-privilege default
  `payloadAccess = "metadata-only"`, `validityEffect = "none"` (explicitly permitted by `contracts/xdl-profile.md`
  and FR-012); this default is a resolved default, not an unresolved input;
- emit `{"tapId", "routeId", "payloadAccess", "validityEffect"}`, sorted by `tapId`; duplicate `tapId` →
  `XCOM-PLAN-DUPLICATE`.

### 7.3 Stimulation

Sources: every indexed `validation-policy` applied to the Scenario in scope. `actions` = the sorted unique
union of `allowedActions`; `permitPolicyRefs` = the sorted unique union of `permitPolicyRef`. A
`serviceEmulation: true` payload whose `permitPolicyRef` is absent is rejected (`XCOM-PLAN-POLICY`; the schema
also forbids it). With no `validation-policy`, emit `{"actions": [], "permitPolicyRefs": []}` (stimulation is
disabled by default per FR-016) and leave `policy` resolved. Every `actions`/`permitPolicyRefs` entry is
copied from a closed-grammar identifier; an entry failing the plan identifier pattern is `XCOM-PLAN-POLICY`.

### 7.4 Clock domains

For each System `spec.timeDomains` entry `t`, emit `{"clockDomainId": t["id"], "source": <source>}` where the
source is chosen deterministically in precedence order:

1. `local-validation-clock` when a `validation-policy.timePolicy` in scope equals `local-validation-clock` and
   the domain is the referenced validation clock (the first time domain in sorted id order when the payload
   does not name one);
2. `monotonic` when `t.get("monotonic") is True`;
3. `unmapped` otherwise.

`clockDomains` is sorted by `clockDomainId`; duplicate ids → `XCOM-PLAN-DUPLICATE`. The `time` family is
`unresolved` when `clockDomains` is empty, or when any emitted source is `unmapped`
(`XCOM-PLAN-TIME-UNRESOLVED` targeting the `clockDomainId`).

### 7.5 Activation order

`activationOrder` = the sorted endpoint ids followed by the sorted route ids (endpoints precede routes), each
listed once. It is never empty (§6.4). Every entry is a declared endpoint or route id, satisfying the T017
ordering check.

## 8. `T018-U-06` — Input resolution, diagnostics, status

### 8.1 Input-resolution families

| Family | `resolved` when | `unresolved` otherwise with diagnostic |
| --- | --- | --- |
| `identity` | every referenced logical identity resolves and every applied Profile `target` matches its attachment | `XCOM-PLAN-IDENTITY-UNRESOLVED` → attachment resource name |
| `schema` | every route's interface id has a contract in `contracts` | `XCOM-PLAN-SCHEMA-UNRESOLVED` → offending `routeId` |
| `capability` | a route exists ⇒ at least one provider and every provider's required ⊆ declared capabilities | `XCOM-PLAN-CAPABILITY-UNRESOLVED` → `providerId` or `PLAN_TARGET` |
| `time` | `clockDomains` non-empty and no source is `unmapped` | `XCOM-PLAN-TIME-UNRESOLVED` → `clockDomainId` or `PLAN_TARGET` |
| `ownership` | a Deployment is in scope, every endpoint `ownerId` resolves to a System node/component-instance/device, and every Deployment `bindings[].logicalRef.element` maps to at most one binding | `XCOM-PLAN-OWNERSHIP-UNRESOLVED` → offending endpoint/owner id |
| `policy` | no policy conflict or absence was recorded in §7.1 | `XCOM-PLAN-POLICY-UNRESOLVED`/`XCOM-PLAN-POLICY-CONFLICT` → route id or `PLAN_TARGET` |

`status = "activatable"` iff all six are `"resolved"`; otherwise `status = "inspectable"`.

### 8.2 Diagnostics

`diagnostics` is the list of the diagnostics emitted above, each
`{"code": <DIAGNOSTIC_CODES token>, "severity": <"error"|"warning"|"info">, "targetId": <identifier>}`.
Unresolved families emit `severity = "error"`; an information-only note is not synthesized, so a fully
resolved plan has `diagnostics = []`. The list is de-duplicated by `(code, targetId)` and sorted by
`(code, targetId)`, satisfying the T017 uniqueness/order rule. When the diagnostic count would exceed
`limits.max_diagnostics` → `XCOM-PLAN-BOUND`.

## 9. `T018-U-05` — Canonicalization, digest, and provenance

### 9.1 Canonical serialization (`T018-SR-005`)

`canonical_plan_bytes(plan)` is `json.dumps(_normalize_numbers(plan), sort_keys=True,
separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")` where `_normalize_numbers`
recursively replaces an integral `float` by `int` and rejects a non-finite number (`XCOM-PLAN-UNKNOWN`). This
is byte-for-byte the T017 rule, reproduced independently (a test asserts agreement, §CHK-03).

### 9.2 Digest and provenance (`T018-SR-006`)

- `compute_digest(plan)` = `sha256(PLAN_DOMAIN_SEPARATOR + canonical_plan_bytes(body)).hexdigest()` where
  `body = {k: v for k, v in plan.items() if k != "digest"}`. The `digest` member is verified equal to
  `{"algorithm": "sha256", "value": compute_digest(plan)}` before return; a mismatch is `XCOM-PLAN-UNKNOWN`
  (an internal defect, not a data error).
- `generator` = `{"task": TASK_ID, "version": generator_version}` with `generator_version` matching
  `^[0-9]+\.[0-9]+(?:\.[0-9]+)?$` (else `XCOM-PLAN-INPUT`).
- `provenance.generatedAt` = the explicit `generated_at` argument, or `DEFAULT_GENERATED_AT`; a supplied value
  must be an RFC 3339 `date-time` string (else `XCOM-PLAN-INPUT`).
- `provenance.graphDigest` = `{"algorithm": "sha256", "value": sha256(GRAPH_DOMAIN_SEPARATOR +
  canonical_plan_bytes(graph_document)).hexdigest()}` where `graph_document` is `{"resources": [...]}` in the
  sorted order of §4.
- `provenance.resources` = the sorted unique identity records of the contributing `PROVENANCE_KINDS`
  resources (the Component instances reachable from the System, the Deployment in scope, and the Scenario in
  scope). Each record is `{apiVersion, kind, namespace, name, version?, sourceDigest}` where `version` is
  present only when `revision` matches `^[0-9]+\.[0-9]+(?:\.[0-9]+)?$` (a prerelease/build semver omits the
  optional member rather than being rewritten), and `sourceDigest` =
  `{"algorithm": "sha256", "value": sha256(canonical_plan_bytes(resource)).hexdigest()}`. An empty
  contributing set → `XCOM-PLAN-INPUT` (the schema requires `minItems: 1`).

## 10. `T018-U-07` — Composition and status

`compile_plan` composes the plan in this member order (order is irrelevant to the digest because
canonicalization sorts members): `planVersion`, `digest`, `generator`, `provenance`, `contracts`, `endpoints`,
`routes`, `providers`, `policies`, `observationPoints`, `stimulation`, `clockDomains`, `activationOrder`,
`diagnostics`, `status`, `inputResolution`. It sets `digest` last, then re-verifies `plan_matches_digest`. The
completed plan is passed to the T017 schema/ordering/digest rules by the tests; the compiler itself does not
embed a JSON Schema validator at import time.

## 11. `T018-U-08` — Bounds and failure semantics

`CompileLimits` bounds are applied as: `max_bytes` (text input only), `max_depth`/`max_nodes` (graph walk),
`max_resources` (graph size), and the per-collection caps checked after derivation (endpoints, routes,
providers, observation points, clock domains, diagnostics). A cap breach → `XCOM-PLAN-BOUND` (`failed`) before
any plan value is returned.

| T018 condition | Outcome |
| --- | --- |
| malformed graph root/shape, non-finite number, non-identifier value | `rejected` (`XCOM-PLAN-INPUT`) |
| duplicate resource/collection identity | `rejected` (`XCOM-PLAN-DUPLICATE`) |
| ambiguous scope (0/>1 System, >1 Deployment/Scenario), multi-destination flow, conflicting/ambiguous endpoint role, undeclared endpoint/route reference, empty activationOrder | `rejected` (`XCOM-PLAN-IDENTITY`) |
| illegal/unknown Profile payload, form/kind mismatch, illegal attachment, duplicate payload for one identity | `rejected` (`XCOM-PLAN-PROFILE`) |
| interface policy that cannot yield a valid contract | `rejected` (`XCOM-PLAN-CONTRACT`) |
| `serviceEmulation: true` without `permitPolicyRef`, invalid stimulation identifier | `rejected` (`XCOM-PLAN-POLICY`) |
| bound exceeded | `failed` (`XCOM-PLAN-BOUND`) |
| unknown compilation step / digest self-check failure | `failed` (`XCOM-PLAN-UNKNOWN`) |
| an unresolved identity/schema/capability/time/ownership/policy input | plan emitted with `status = "inspectable"` |
| every family resolved | plan emitted with `status = "activatable"` |

No unknown outcome is reported as success; a rejected/failed call returns no plan value. `XcomPlanError`
carries the stable `code` and a bounded message; it never includes credentials, addresses, or absolute host
paths.

## 12. Cross-language contract at the boundary

The compiler and the C++ decoder interact **only** through the T017 plan schema and the T017 digest rule. T018
adds no contract statement and changes no T017 schema: the compiler's derivation mapping (§5–§9) is
implementation design owned by `PLAN_DOCS`. T019 must independently reproduce the canonicalization and digest
rules in C++ and reject a version/digest/capability mismatch; T018 does not implement that decoder.

## 13. Unit and artifact trace

| Requirement | Design unit | Artifact | Design section |
| --- | --- | --- | --- |
| T018-SR-001 | `T018-U-01` | `COMPILER` | §4 |
| T018-SR-002 | `T018-U-02` | `COMPILER` | §5 |
| T018-SR-003 | `T018-U-03` | `COMPILER` | §6 |
| T018-SR-004 | `T018-U-04` | `COMPILER` | §7 |
| T018-SR-005 | `T018-U-05`, `T018-U-07` | `COMPILER` | §9.1, §10 |
| T018-SR-006 | `T018-U-05` | `COMPILER` | §9.2 |
| T018-SR-007 | `T018-U-06`, `T018-U-07` | `COMPILER` | §8, §10 |
| T018-SR-008 | `T018-U-08` | `COMPILER` | §11 |
| T018-SR-009 | `T018-U-10` | `COMPILER_TESTS` | `verification-plan.md` §7 |
| T018-SR-010 | `T018-U-09` | `PLAN_DOCS` | `verification-plan.md` §2 |
