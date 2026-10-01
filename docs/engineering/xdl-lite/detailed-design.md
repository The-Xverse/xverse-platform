# XDL Lite Phase 1 Detailed Design — frozen Profile fields, plan shape, identity, diagnostics, bounds, order, API/CLI

## 1. Document control

| Field | Value |
| --- | --- |
| Feature | XDL1 (XDL Lite Phase 1 — offline declared experiment intent compilation) |
| Stage / role | architecture (pre-code detailed design) |
| Revision | 1 |
| Date | 2026-10-01 |
| Admitted platform baseline revision | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Component records | `engineering/architecture/components/XDL1-SR-001-CMP.json` … `XDL1-SR-019-CMP.json` |
| Consumed accepted anchors | `src/xverse_xdl/{models,loader,diagnostics,schema,semantics,normalize,validate,catalog,xcom_plan,cli}.py`, `xdl/schemas/v1alpha1/{common,component,deployment,profile,scenario,system}.schema.json`, ADR-0007/0008/0010/0011/0012, Constitution 2.1.0 |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Design only, written **before** implementation. Every constant, field, bound, ordering rule, diagnostic code, and expected behaviour below is a verification contract: implementation must realize it, and weakening any of it requires a reviewed successor candidate. |
| Revision status | **Successor revision.** Supersedes the rejected XDL1 attempt-1 detailed design (frozen candidate under run `01M3VCR5S2TCDGQGA7R1JYH6DA`, independently reviewed read-only with `verdict: rework`, predecessor `review/internal-review.json` SHA-256 `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4`). It closes `XDL1-RVW-001` (total compiled-parameter bound scope), `XDL1-RVW-002` (declared System core-parameter destination), and `XDL1-RVW-003` (missing count-bound negative evidence). The predecessor is retained only as failed external review evidence; see §16.2. |

This design **freezes** what the admitted planning inputs deliberately left open: "Exact payload field names,
stable diagnostic codes and finite bounds are design tasks before implementation"
(`specs/022-xdl-lite-experiment-plan/research.md`) and "All exact JSON field shapes and compatibility conversions
must be reviewed and frozen before implementation" (`.../contracts/experiment-plan.md`).

## 2. Design decisions

| ID | Decision | Rationale | Requirements |
| --- | --- | --- | --- |
| `XDL1-DD-01` | Add one admitted neutral Profile payload schema `xdl/profiles/experiment-lite-v0.1.schema.json` with namespace `io.xverse.experiment`, payload `schemaVersion` `0.1`, Profile `metadata.version` `0.1.0`, and `$id` `https://xverse.io/profiles/experiment-lite/v0.1/schema.json` | A single versioned neutral extension, admitted through the accepted explicit Profile registry; no second language and no generic extension bag | `XDL1-SR-017`, `XDL1-SR-016` |
| `XDL1-DD-02` | The payload has exactly four closed `kind` forms (`scenario-intent`, `step-intent`, `fault-intent`, `realization-intent`) attached at existing extension points only (`Scenario/extensions`, `spec.steps[i]/extensions`, `spec.faults[i]/extensions`, `spec.bindings[i]/extensions`) | The accepted `EXTENSION_COLLECTIONS` set is the only legal attachment surface; adding containers would modify the accepted core | `XDL1-SR-017`, `XDL1-SR-002` |
| `XDL1-DD-03` | Every other requested concept maps to an existing v1alpha1 field (§5); the typed extension is used only for the three real gaps: explicit seed+parameters, fault trigger/duration/typed parameters, and step phase/dependencies/typed parameters plus realization delivery/retry/protocol intent | "Detailed design must identify the exact reused schema field for each concept and add a typed extension only where the accepted core has no equivalent representation" | `XDL1-SR-002`, `XDL1-SR-005` |
| `XDL1-DD-04` | Compiler entry points accept XDL byte sources/files (through the accepted loader, schema registry, semantics, normalizer) or already-normalized resources; the compiler core consumes only immutable normalized resources and performs no I/O | Pure function; the real loader/schema path is exercised, not mocked | `XDL1-SR-014`, `XDL1-SR-016` |
| `XDL1-DD-05` | Semantic identity is computed over canonical JSON of the normalized declared content, excluding source-map locations, byte hashes, run identifiers, wall-clock time, and file names; byte hashes live only in the volatile run envelope | Equivalent YAML/JSON and permuted inputs must not acquire different semantic identities; run/wall-clock must not affect the plan digest | `XDL1-SR-011`, `XDL1-SR-018` |
| `XDL1-DD-06` | Time is expressed in a closed unit vocabulary (`tick`, `ns`, `us`, `ms`, `s`) with exact rational scaling to integer ticks; unknown, ambiguous, negative, non-finite, overflowing, or imprecise values reject; no wall clock is read | Deterministic ordering with no invented conversion and no silent unit assumption | `XDL1-SR-019`, `XDL1-SR-018` |
| `XDL1-DD-07` | Ordering is fully specified: dependency order over System component instances and Scenario steps; schedule/observation order per declared time domain with explicit tie-breaks; cycles and duplicate `declared-order` triggers reject | Deterministic, replayable, ambiguity-free intent order | `XDL1-SR-003`, `XDL1-SR-007`, `XDL1-SR-013`, `XDL1-SR-018` |
| `XDL1-DD-08` | Every declared defect returns stable structured diagnostics and `plan = None`; no partial, best-effort, or executable plan is ever exposed | Fail-closed rejection with no side effect | `XDL1-SR-014`, `XDL1-SR-015` |
| `XDL1-DD-09` | The plan carries a compiler-emitted non-readiness statement and the declared fidelity limitations; it makes no availability, fitness, readiness, compatibility, parity, or certification claim | Intent validation only; declaration-only readiness is labelled as such | `XDL1-SR-012` |
| `XDL1-DD-10` | The compiler never embeds, defaults, or narrows a scientific protocol value; seed, parameters, durations, tolerances, and bounds remain caller inputs, and only platform library bounds are enforced | No invented thesis protocol value | `XDL1-SR-005`, `XDL1-SR-019` |
| `XDL1-DD-11` | Physical realization is explicitly unsupported in Phase 1 and rejects; declared simulated/virtual/hybrid bindings are recorded as references only | Phase 1 holds no device or artifact-admission authority and executes nothing | `XDL1-SR-015`, `XDL1-SR-010` |
| `XDL1-DD-12` | Exposure is additive only: a new module, new exports, and one new `xdl experiment compile` subcommand; existing commands, formats, exit codes, schemas, and diagnostics are preserved byte-for-byte for existing inputs | Compatibility, no accepted change (ADR-0018/ADR-0020; ADR-THESIS-LITE-0001) | `XDL1-SR-016` |
| `XDL1-DD-13` | `ExperimentLimits.max_parameters` is enforced over **three explicit scopes**: (a) each declared extension `parameterList` (per-payload), (b) the **total compiled parameter count** over the whole emitted plan, and (c) each declared core `Component.spec.parameters[]`/`System.spec.parameters[]` list projected into `components[].declaredParameters`. All three reuse `XDL1-PLAN-BOUND-EXCEEDED`; the exact counting rule is frozen in §10.3. Resolves `XDL1-RVW-001`. | The predecessor declared "per payload and total compiled parameters" but enforced only per-list; a resolved plan could carry more compiled parameters than the declared bound. The successor makes the total scope an explicit, deterministic count over the finished sections | `XDL1-SR-019`, `XDL1-SR-014`, `XDL1-SR-012` |
| `XDL1-DD-14` | Declared core parameters have **two deterministic destinations**, both under the frozen `components[].declaredParameters` surface: `Component.spec.parameters[]` → the `declaredParameters` of that Component's own `components[]` entry (`scope = "component-instance"`); `System.spec.parameters[]` → the `declaredParameters` of exactly one System-scope `components[]` entry (`scope = "system"`, emitted first, always present). No System parameter is duplicated across component entries and none is dropped. Resolves `XDL1-RVW-002`. | The predecessor mapping row listed both sources against `components[].declaredParameters` but the projection read only the Component resource; the System-scope entry gives a deterministic, non-duplicating destination for the System's own declared core parameters and models | `XDL1-SR-002`, `XDL1-SR-011` |

## 3. Frozen Profile identity and admission

### 3.1 Frozen identities

| Constant | Frozen value |
| --- | --- |
| Profile payload schema file | `xdl/profiles/experiment-lite-v0.1.schema.json` |
| Payload `$id` (= `spec.schemaRef`) | `https://xverse.io/profiles/experiment-lite/v0.1/schema.json` |
| Payload `schemaVersion` | `0.1` (JSON Schema `const`) |
| Extension namespace (`spec.extensionNamespace`) | `io.xverse.experiment` |
| Profile resource `metadata.version` | `0.1.0` (exact) |
| Profile `spec.compatibleApiVersions` | exactly `["xverse.io/xdl/v1alpha1"]` |
| Profile `spec.conflictPolicy` | `reject` |
| Profile `spec.documentationRef` | `https://xverse.io/profiles/experiment-lite/v0.1/README.md` |
| Plan version | `1` |
| Plan generator | `{"task": "XDL1", "version": "0.1.0"}` |

### 3.2 Admission checks (in order)

The accepted gates run first and unchanged: parse → core schema → Profile schema catalog → closed-set reference
resolution → kind semantics → normalization. The compiler then requires, over the normalized resources:

1. exactly one `Profile` resource whose `spec.extensionNamespace` is `io.xverse.experiment` (`XDL1-PLAN-PROFILE-ABSENT`
   / `XDL1-PLAN-PROFILE-DUPLICATE`; the accepted gate already rejects a duplicate namespace owner);
2. that Profile's `metadata.version` is exactly `0.1.0` and `compatibleApiVersions` contains
   `xverse.io/xdl/v1alpha1` (`XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED`);
3. that Profile's `schemaRef` is exactly the frozen `$id` (`XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED`);
4. at most one payload per attachment pointer (`XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE`), each payload `kind` matching
   its attachment point (`XDL1-PLAN-PROFILE-PAYLOAD-KIND`) and each payload `target` equal to the owning
   resource/element identity (`XDL1-PLAN-PROFILE-TARGET-MISMATCH`);
5. the selected `Scenario` carries exactly one `scenario-intent` payload (`XDL1-PLAN-PROFILE-PAYLOAD-ABSENT`).
   Step, fault, and binding payloads are optional per attachment point.

Payload schema validation itself is performed by the accepted `ProfileSchemaCatalog`; therefore unknown namespaces
(`XDL-SEMANTIC-PROFILE-MISSING`), unknown fields and closed-enum violations (`XDL-SEMANTIC-EXTENSION-SCHEMA`), missing
Profile schemas (`XDL-SEMANTIC-PROFILE-SCHEMA-MISSING`), and incompatible Profiles
(`XDL-SEMANTIC-PROFILE-INCOMPATIBLE`) fail closed **before** the compiler's own checks and produce no plan.

## 4. Frozen Profile payload — exact fields

Common rules for every payload form: `additionalProperties: false` at every level; `schemaVersion` `const` `0.1`;
`kind` a closed `const` per attachment; `target` an exact identity reference to the attachment owner.

### 4.1 Shared definitions

| Definition | Frozen shape |
| --- | --- |
| `identifier` | string, `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, length 1–63 (matches `common.schema.json#/$defs/identifier`) |
| `text` | string, length 1–200 |
| `unitSemantics` | string, length 1–64 (opaque declared unit label; never converted) |
| `timeUnit` | `enum ["tick", "ns", "us", "ms", "s"]` |
| `timeQuantity` | `{"value": number ≥ 0, "unit": timeUnit}`, `additionalProperties: false` |
| `parameter` | `{"id": identifier, "valueType": enum["boolean","integer","number","string"], "value": <typed>, "unitSemantics": unitSemantics, "mutability": enum["constant","configuration","scenario"] (optional), "limitations": array of text, ≤ 8, unique (optional)}` with `allOf` conditionals binding `valueType` to the exact JSON type and finite bounds: boolean; integer −9007199254740991…9007199254740991; number with magnitude ≤ 1e15; string length 1–200 |
| `parameterList` | array of `parameter`, ≤ 256, duplicate `id` rejected by the compiler |
| `seed` | `{"value": integer 0…9007199254740991, "unitSemantics": unitSemantics}` |
| `fidelityLimitations` | array of `text`, ≤ 64, `uniqueItems: true` |
| `scenarioTarget` | `{"apiVersion": const, "kind": const "Scenario", "namespace", "name"}` |
| `deploymentElementTarget` | `{"apiVersion": const, "kind": const "Deployment", "namespace", "name", "element": identifier}` |
| `scenarioElementTarget` | `{"apiVersion": const, "kind": const "Scenario", "namespace", "name", "element": identifier}` |

### 4.2 `scenario-intent` — attached at `Scenario /extensions/io.xverse.experiment`

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `schemaVersion` | `const "0.1"` | yes | — |
| `kind` | `const "scenario-intent"` | yes | — |
| `target` | `scenarioTarget` | yes | must equal the owning Scenario identity |
| `seed` | `seed` | yes | explicit; never defaulted |
| `parameters` | `parameterList` | yes (may be `[]`) | declared experiment parameters; no default is invented |
| `fidelityLimitations` | `fidelityLimitations` | no | merged into the plan `limitations` |

### 4.3 `step-intent` — attached at `Scenario /spec/steps[i]/extensions/io.xverse.experiment`

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `schemaVersion` / `kind` | `const "0.1"` / `const "step-intent"` | yes | — |
| `target` | `scenarioElementTarget` | yes | `element` must equal the owning step `id` |
| `phase` | `enum ["prepare","start","observe","stop","cleanup"]` | yes | total order `prepare < start < observe < stop < cleanup` |
| `dependsOn` | array of `identifier`, ≤ 64, unique | no | every entry must name another declared step of the same Scenario; self-reference rejects |
| `duration` | `timeQuantity` | no | converted to integer ticks; recorded |
| `parameters` | `parameterList` | no | typed step parameters |

### 4.4 `fault-intent` — attached at `Scenario /spec/faults[i]/extensions/io.xverse.experiment`

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `schemaVersion` / `kind` | `const "0.1"` / `const "fault-intent"` | yes | — |
| `target` | `scenarioElementTarget` | yes | `element` must equal the owning fault `id` |
| `trigger` | `{"kind":"time","at":number ≥0,"unit":timeUnit}` or `{"kind":"declared-order","order":integer 0…1048575}` | yes | exactly one form |
| `timeDomainId` | `identifier` | required when `trigger.kind = "time"`; forbidden otherwise | must resolve to a declared `System.spec.timeDomains[].id` |
| `duration` | `timeQuantity` | yes | `0` means instantaneous; converted to integer ticks |
| `parameters` | `parameterList` | no | typed fault parameters |

### 4.5 `realization-intent` — attached at `Deployment /spec/bindings[i]/extensions/io.xverse.experiment`

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `schemaVersion` / `kind` | `const "0.1"` / `const "realization-intent"` | yes | — |
| `target` | `deploymentElementTarget` | yes | `element` must equal the owning binding `id` |
| `delivery` | `enum ["in-place","staged","none"]` | no | `in-place`/`staged` require ≥ 1 pinned artifact on the binding; `none` forbids the `retry` field |
| `retry` | `{"policy": enum["none","bounded"], "maxAttempts": integer 1…64}` | no | `maxAttempts` required iff `policy = "bounded"` (`allOf`), forbidden otherwise |
| `protocolBinding` | `{"standardRef": uri-reference, "bindingKind": identifier, "compatibility": enum["exact","backward","converter"], "limitations": array of text ≤ 16}` | no | declared standard/binding reference only; nothing is resolved |

`SUPPORTED_REALIZATION_CLASSES = ("simulated", "virtual", "hybrid")` (§2 `XDL1-DD-11`). A binding whose
`realizationClass`, or whose target's `targetClass`, is declared as `physical` rejects with
`XDL1-PLAN-REALIZATION-UNSUPPORTED`; every other accepted core value is recorded verbatim as a declaration.
Values outside the accepted core enums never reach the compiler because the accepted core schema rejects them
(`XDL-SCHEMA-INVALID`). No delivery, retry, or realization default is applied when a payload omits those fields:
the corresponding plan field is `null`.

## 5. Concept-to-existing-field mapping (frozen)

Every requested concept maps to an existing v1alpha1 field or to the frozen extension gap. "Extension" means the
`io.xverse.experiment` payload; no other new representation exists.

| Requested concept | Exact existing representation | Plan location |
| --- | --- | --- |
| System | `kind: System` resource identity + `spec` | `selection.system` |
| Node | `System.spec.nodes[].id` | `components[].nodeId`, `dependencyOrder[].kind = "node"` |
| Component | `kind: Component` resource | `components[].componentRef` |
| Component instance | `System.spec.componentInstances[].id` + `componentRef` | `components[].instanceId` |
| Component parameter (core) | `Component.spec.parameters[]` (`common.schema.json#/$defs/parameter`) | `components[scope="component-instance"].declaredParameters` (the entry whose `componentRef` is that Component) |
| System parameter (core) | `System.spec.parameters[]` (`common.schema.json#/$defs/parameter`) | `components[scope="system"].declaredParameters` (exactly one System-scope entry, emitted first; never duplicated into component entries and never dropped) |
| Interface | `System.spec.interfaces[]` / `Component.spec.interfaces[]` (`#/$defs/interface`) | `flows[].interfaceId` |
| Endpoint | `System.spec.endpoints[]` / `Component.spec.endpoints[]` (`#/$defs/endpoint`) | `flows[].sourceEndpointId` / `destinationEndpointIds` |
| Flow | `System.spec.flows[]` (`sourceEndpointId`, `destinationEndpointIds`, `interfaceId`, `deliveryIntent`, `networkId?`, `timeDomainId?`) | `flows[]` |
| Network | `System.spec.networks[]` | `flows[].networkId` |
| Time domain | `System.spec.timeDomains[]` (`id`, `clockClass`, `epoch`, `rate`, `monotonic`) | `timeDomains[]` |
| Time mapping | `Scenario.spec.timeMappings[]` (`sourceTimeDomainId`, `targetTimeDomainId`, `mapping`, `tolerance`) | `timeMappings[]` |
| Execution target | `Deployment.spec.targets[]` (`id`, `targetClass`, `capabilities`, `externalAssetRef?`, `profileRefs?`) | `bindings[].targetId` / `targetClass` |
| Realization | `Deployment.spec.bindings[]` (`logicalRef`, `realizationClass`, `targetId`, `artifactIds`, `resourceIds`, `lifecycle`) | `bindings[]` |
| Protocol binding | `Deployment.spec.targets[].profileRefs[]` + extension `protocolBinding` (§4.5) | `bindings[].protocolBinding` |
| Deployment realization readiness | accepted declaration-only `StaticReadiness` from `SemanticsGraph.readiness` | `selection.staticReadiness` (labelled declaration-only) |
| Model/artifact binding | `Deployment.spec.bindings[].artifactIds[]` → `Deployment.spec.artifacts[]` (`id`, `artifactKind`, `version`, `digest`, `sourceRef`, `maturity`, `limitations`) | `bindings[].artifactRefs[]` |
| Component model reference | `Component.spec.models[]` (`externalRef`, `maturity`, `limitations`) | `components[scope="component-instance"].modelRefs[]` |
| System model reference | `System.spec.models[]` (`externalRef`, `maturity`, `limitations`) | `components[scope="system"].modelRefs[]` |
| Scenario | `kind: Scenario` resource | `selection.scenario` |
| Scenario initial conditions | `Scenario.spec.initialConditions` (open declared object) | `initialConditions` (verbatim declared content) |
| Acceptance intent | `Scenario.spec.acceptanceIntent?` | `acceptanceIntent` |
| Parameter (experiment) | **extension gap** — `scenario-intent.parameters` (§4.2); core `Component/System.spec.parameters[]` recorded separately | `parameters[]` |
| Seed | **extension gap** — `scenario-intent.seed` (§4.2) | `seed` |
| Lifecycle intent | `Scenario.spec.steps[]` (`actionKind`, `targetRef`, `timeDomainId`, `schedule`, `action`) + `step-intent` phase/dependsOn/duration/parameters | `lifecycleIntent[]` |
| Fault | `Scenario.spec.faults[]` (`id`, `targetRef`, `faultKind`, `activation`, `recovery`, `maturity`) + `fault-intent` trigger/timeDomainId/duration/parameters | `faultSchedule[]` |
| Fault class | `Scenario.spec.faults[].faultKind` (recorded verbatim; no vocabulary is invented) | `faultSchedule[].faultKind` |
| Observer | `Scenario.spec.observers[]` (`id`, `targetRef`, `timeDomainId`, `samplingIntent`, `payloadSchema`, `unitSemantics`, `evidenceSinkRef`) | `observers[]` |
| Metric | `Scenario.spec.metrics[]` (`id`, `observerIds`, `calculationRef`, `unitSemantics`, `acceptance`) | `metrics[]` |
| Observer payload policy | `Scenario.spec.observers[].payloadSchema` + `samplingIntent` | `observers[].payloadPolicy` |
| Fidelity limitation | `metadata.provenance.limitations` (all contributing resources) + `scenario-intent.fidelityLimitations` | `limitations[]` |
| Non-readiness statement | **compiler-emitted constant** (never caller input) | `nonReadiness` |
| Deployment delivery / retry | **extension gap** — `realization-intent.delivery` / `.retry` (§4.5) | `bindings[].delivery` / `.retry` |

No new top-level XDL resource kind is introduced; `ProtocolBinding` and `Realization` are represented by reviewed
`Deployment`/`Profile` relationships only, as required by the admitted specification.

## 6. Compiler pipeline (ordered, fail-closed)

| Stage | Check | Codes | Owner |
| --- | --- | --- | --- |
| S1 parse | bounded JSON/YAML 1.2 parse, duplicates, non-string keys, finite numbers | `XDL-PARSE-*` | accepted loader |
| S2 core schema | v1alpha1 kind schemas `additionalProperties: false` | `XDL-SCHEMA-*` | accepted registry |
| S3 Profile schema catalog | explicit local schemas only | `XDL-POLICY-*` | accepted registry |
| S4 reference | closed-set resource/element resolution | `XDL-REFERENCE-*` | accepted semantics |
| S5 kind semantics + extension payload validation | membership, ownership, flow direction, bindings, time mappings, Profile ownership, payload schema | `XDL-SEMANTIC-*`, `XDL-BINDING-ARTIFACT-INTEGRITY` | accepted semantics |
| S6 normalize | immutable `NormalizedResource` set, deterministic identity order | — | accepted normalizer |
| S7 Profile admission | §3.2 | `XDL1-PLAN-PROFILE-*` | `XDL1-ARCH-02` |
| S8 selection | §7.1 | `XDL1-PLAN-SYSTEM-*`, `-SCENARIO-*`, `-DEPLOYMENT-*` | `XDL1-ARCH-03` |
| S9 quantities/units | §10 | `XDL1-PLAN-SEED-*`, `-PARAMETER-*`, `-QUANTITY-*`, `-TIME-*` | `XDL1-ARCH-04` |
| S10 order | §11 | `XDL1-PLAN-DEPENDENCY-*`, `-SCHEDULE-AMBIGUOUS`, `-BOUND-EXCEEDED` | `XDL1-ARCH-05` |
| S11 compile intent | §7.2 | `XDL1-PLAN-ARTIFACT-*`, `-REALIZATION-*`, `-DELIVERY-*`, `-RETRY-*`, `-METRIC-*`, `-OBSERVER-*`, `-SECRET-*` | `XDL1-ARCH-06` |
| S12 identity | §8 | `XDL1-PLAN-INPUT-MUTATED`, `XDL1-PLAN-DIGEST-SELFCHECK` | `XDL1-ARCH-07` |

Stages S7–S12 are skipped entirely when any stage S1–S6 returns an error diagnostic. Diagnostics are accumulated
within one stage, sorted by the accepted `Diagnostic.sort_key`, and returned with `plan = None` whenever any
error-severity diagnostic exists.

Before the S12 identity stage finalizes a plan, the compiler performs the **total compiled-parameter count check**
of §10.3 over the fully compiled parameter-bearing sections (`parameters`, `lifecycleIntent[].parameters`,
`faultSchedule[].parameters`). A total count greater than `limits.max_parameters` emits
`XDL1-PLAN-BOUND-EXCEEDED` and returns no plan. The check is deterministic, independent of stage order, and is the
single place where the total-parameter scope is enforced; the per-payload scope (§10.3) is enforced where each
declared parameter list is read.

### 6.1 Selection rules (S8, frozen)

1. Exactly one `System` resource must be present (`XDL1-PLAN-SYSTEM-MISSING`, `XDL1-PLAN-SYSTEM-AMBIGUOUS`).
2. Exactly one `Scenario` in the closed set must reference that System (`XDL1-PLAN-SCENARIO-MISSING`,
   `XDL1-PLAN-SCENARIO-AMBIGUOUS`). Zero or two or more resolvable Scenarios reject.
3. At most one `Deployment` must reference that System (`XDL1-PLAN-DEPLOYMENT-AMBIGUOUS`). When exactly one exists,
   the selected Scenario must declare `deploymentRef` to it (`XDL1-PLAN-DEPLOYMENT-UNBOUND`).
4. When no Deployment exists, the phase-1 plan still compiles: bindings and realization sections are empty and the
   plan records `deployment: null`. This is the only permitted case of an absent Deployment.
5. The selected Scenario must carry exactly one `scenario-intent` payload (§3.2).

## 7. Resolved experiment plan v1 — frozen shape

Canonical serialization: `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)`
with every finite mathematically integral float emitted as an integer (accepted `xcom_plan` numeric convention).
Arrays are emitted in the frozen order of §11; mappings are key-sorted by canonical JSON.

```json
{
  "planVersion": "1",
  "generator": {"task": "XDL1", "version": "0.1.0"},
  "profile": {
    "namespace": "io.xverse.experiment", "schemaVersion": "0.1",
    "schemaRef": "https://xverse.io/profiles/experiment-lite/v0.1/schema.json",
    "resource": {"apiVersion": "xverse.io/xdl/v1alpha1", "kind": "Profile", "namespace": "<ns>",
                 "name": "<name>", "version": "0.1.0", "uri": "xdl://<ns>/profile/<name>"},
    "resourceDigest": {"algorithm": "sha256", "value": "<64 hex>"}
  },
  "selection": {
    "system": {"apiVersion": "...", "kind": "System", "namespace": "...", "name": "...",
               "uri": "xdl://...", "version": "<semver>", "semanticDigest": {"algorithm": "sha256", "value": "..."}},
    "deployment": {"...": "same shape, or null"},
    "scenario": {"...": "same shape"},
    "staticReadiness": {"<deployment uri>": "Ready|NotReady|NotEvaluated"}
  },
  "seed": {"value": 0, "unitSemantics": "<label>"},
  "parameters": [{"id": "<id>", "valueType": "integer", "value": 1, "unitSemantics": "<label>", "mutability": "configuration"}],
  "components": [{"scope": "system", "instanceId": null, "componentRef": null, "nodeId": null,
                  "declaredParameters": [{"id": "<id>", "valueType": "integer",
                                          "unitSemantics": "<label>", "mutability": "constant"}],
                  "modelRefs": []},
                 {"scope": "component-instance", "instanceId": "<id>", "componentRef": {"...": "identity"},
                  "nodeId": null, "declaredParameters": [], "modelRefs": []}],
  "timeDomains": [{"id": "<id>", "clockClass": "simulation", "epoch": "<declared>", "rate": "<declared>",
                   "monotonic": true, "canonicalUnit": "tick",
                   "usedBy": ["step:<id>", "observer:<id>", "flow:<id>", "fault:<id>"]}],
  "timeMappings": [{"declaredIndex": 0, "sourceTimeDomainId": "<id>", "targetTimeDomainId": "<id>",
                    "mapping": "<declared>", "tolerance": {"value": 1, "unit": "ms", "ticks": 1000000}}],
  "dependencyOrder": [{"rank": 0, "kind": "component-instance", "id": "<id>", "owner": "system"}],
  "flows": [{"id": "<id>", "sourceEndpointId": "<id>", "destinationEndpointIds": ["<id>"],
             "interfaceId": "<id>", "deliveryIntent": "ordered", "networkId": null, "timeDomainId": null}],
  "bindings": [{"id": "<id>", "logicalRef": {"...": "elementRef"}, "collection": "componentInstances",
                "realizationClass": "simulated", "targetId": "<id>", "targetClass": "model-unit",
                "artifactRefs": [{"id": "<id>", "artifactKind": "<declared>", "version": "<declared>",
                                  "digest": "<declared>", "sourceRef": "<declared uri-reference>",
                                  "maturity": "prototype"}],
                "resourceIds": [], "delivery": "in-place", "retry": null,
                "protocolBinding": {"standardRef": "<declared>", "bindingKind": "<id>",
                                    "compatibility": "exact", "limitations": []}}],
  "lifecycleIntent": [{"stepId": "<id>", "actionKind": "<declared>", "targetRef": {"...": "elementRef"},
                       "timeDomainId": "<id>", "phase": "start",
                       "schedule": {"declaredAt": 0, "declaredUnit": "ms", "atTicks": 0,
                                    "tolerance": {"value": 0, "unit": "ms", "ticks": 0}},
                       "dependsOn": [], "duration": null, "parameters": []}],
  "faultSchedule": [{"entryId": "fault:<id>", "entryKind": "fault", "faultId": "<id>", "faultKind": "<declared>",
                     "targetRef": {"...": "elementRef"}, "collection": "<owning collection>",
                     "activation": "<declared>", "recovery": "<declared>", "maturity": "prototype",
                     "timeDomainId": "<id>", "trigger": {"kind": "time", "declaredAt": 0, "declaredUnit": "ms",
                                                         "atTicks": 0},
                     "duration": {"declaredValue": 1, "declaredUnit": "ms", "ticks": 1000000},
                     "parameters": []}],
  "observers": [{"observerId": "<id>", "targetRef": {"...": "elementRef"}, "collection": "<owning collection>",
                 "timeDomainId": "<id>", "samplingIntent": "<declared>",
                 "payloadPolicy": {"payloadSchema": "<declared>", "unitSemantics": "<declared>"},
                 "evidenceSinkRef": "<declared>"}],
  "metrics": [{"metricId": "<id>", "observerIds": ["<id>"], "calculationRef": "<declared>",
               "unitSemantics": "<declared>", "acceptance": "<declared>",
               "timeDomainIds": ["<id>"], "status": "reference-only"}],
  "initialConditions": {"...": "declared content, verbatim"},
  "acceptanceIntent": "<declared>|null",
  "limitations": ["<declared limitation>"],
  "nonReadiness": {
    "statement": "This resolved plan records declared intent validation only; it is not evidence of executable artifact availability, runtime fitness, live readiness, compatibility, parity, certification, or execution.",
    "claim": "declared-intent-validation-only",
    "executableArtifactAvailability": false,
    "runtimeFitness": false,
    "liveReadiness": false,
    "compatibilityOrParity": false
  },
  "provenance": {
    "inputSemanticDigest": {"algorithm": "sha256", "value": "<64 hex>"},
    "resources": [{"apiVersion": "...", "kind": "System", "namespace": "...", "name": "...",
                   "uri": "xdl://...", "version": "<semver>",
                   "semanticDigest": {"algorithm": "sha256", "value": "<64 hex>"}}]
  },
  "status": "resolved",
  "digest": {"algorithm": "sha256", "value": "<64 hex>"}
}
```

Frozen field rules:

* `provenance.resources` contains exactly the contributing resources: the selected System, the selected Deployment
  (when present), the selected Scenario, the admitted Profile, every distinct Component referenced by
  `System.spec.componentInstances[].componentRef`, and every distinct `Component`/`System` resource supplying a
  declared core parameter or model reference used above. Ordered by `(apiVersion, kind, namespace, name, version)`.
* `provenance.inputSemanticDigest` is computed over exactly that contributing set, so an unrelated extra valid
  resource in the closed input set changes nothing in the plan.
* `components[]` always contains exactly one `scope = "system"` entry first, followed by exactly one
  `scope = "component-instance"` entry per declared `System.spec.componentInstances[]` in declared order. The
  System entry carries `instanceId = null`, `componentRef = null`, `nodeId = null`,
  `declaredParameters` = the projection of `System.spec.parameters[]`, and `modelRefs` = the projection of
  `System.spec.models[]`; it is emitted even when both are empty, so the plan shape is stable. Each
  component-instance entry carries `declaredParameters` = the projection of that referenced Component's
  `spec.parameters[]` and `modelRefs` = that Component's `spec.models[]`. No declared core parameter is ever
  copied from the System scope into a component-instance entry, and no declared core parameter is dropped.
* Declared core parameters are projected as `{id, valueType, unitSemantics, mutability}` (declared-content
  references only, no value or `default`); each declaring list (System and each referenced Component) is
  independently bounded by `max_parameters` (§10.3).
* `status` is always `resolved` for an emitted plan: a rejected compile returns no plan at all.
* `seed` is present if and only if a `scenario-intent` payload is present, which is mandatory in this phase.
* `metrics[].status` is the constant `reference-only`; no metric is computed.
* `observers[].payloadPolicy` and `metrics[].unitSemantics` are declared labels; nothing is converted or evaluated.
* Every array element is emitted with exactly the keys shown; no optional key is emitted as an empty placeholder
  except where the table above fixes `null` or `[]`.

### 7.1 Volatile run envelope (never part of the plan or its digest)

| Field | Content |
| --- | --- |
| `runId` | caller-supplied identifier (≤ 128 chars, `[A-Za-z0-9][A-Za-z0-9_.-]*`) or `null` |
| `generatedAt` | caller-supplied RFC 3339 date-time, or `1970-01-01T00:00:00Z` when omitted; never read from the clock |
| `sourceByteDigests` | `{declared resource key: sha256 of the exact input bytes}` for the sources/file entry points only |
| `planDigest` | the emitted `digest.value`, or `null` on rejection |
| `status` | `resolved` or `rejected` |
| `compilerVersion` | `0.1.0` |

## 8. Canonical semantic identity vs byte provenance (frozen)

* **Resource domain separator** `b"xverse.xdl.experiment-resource.v1\x00"`; **input domain separator**
  `b"xverse.xdl.experiment-input.v1\x00"`; **plan domain separator** `b"xverse.xdl.experiment-plan.v1\x00"`.
* `resourceSemanticDigest(r) = sha256(RESOURCE_DOMAIN_SEPARATOR + canonical_json(r))` where `canonical_json` is the
  accepted `normalize.canonical_json` with `include_source_map = False` and integral floats emitted as integers.
  Included: `identity`, `revision`, `provenance`, `labels`, `elements`, `references`, `extensions`, `content`.
  Excluded: `sourceMap` (authored locations), file name, source format, YAML anchors/comments/key order.
* `inputSemanticDigest = sha256(INPUT_DOMAIN_SEPARATOR + canonical_json(contributing_resources_ordered))`.
* `planDigest = sha256(PLAN_DOMAIN_SEPARATOR + canonical_plan_bytes(plan_without_digest))`, recomputed and
  self-checked after assembly (`XDL1-PLAN-DIGEST-SELFCHECK` if it does not match).
* Volatile data (`runId`, `generatedAt`, `sourceByteDigests`, process handles, observed outcomes) is **never** inside
  the plan body and therefore never affects `planDigest`.
* Late-mutation detection: `compile_experiment_plan` recomputes every resource semantic digest and the input semantic
  digest immediately before finalizing; if any value differs from the value computed at entry, or differs from a
  caller-supplied `expected_input_semantic_digests` entry, it returns `XDL1-PLAN-INPUT-MUTATED` and no plan.

## 9. Diagnostics catalogue (closed, frozen)

Codes are stable, uppercase, hyphenated, and prefixed `XDL1-PLAN-`. Every entry is an `error` with a stable JSON
pointer and a remediation string; the accepted `Diagnostic` value type, `ValidationGate` set, `Severity` set,
`diagnostic_to_data` serialization, ordering, and text rendering are reused unchanged. "Path" records which entry
point can reach the code: **L** = loader/file or source entry point (through the accepted gates), **N** = normalized
API entry point, **B** = both.

| Code | Gate | Path | Rejection meaning |
| --- | --- | --- | --- |
| `XDL1-PLAN-PROFILE-ABSENT` | policy | B | no `io.xverse.experiment` Profile resource is supplied |
| `XDL1-PLAN-PROFILE-DUPLICATE` | policy | B | more than one admitted Profile owner at one attachment surface |
| `XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED` | policy | B | Profile `metadata.version` or `compatibleApiVersions` is not admitted |
| `XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED` | policy | B | Profile `schemaRef` is not the admitted payload `$id` |
| `XDL1-PLAN-PROFILE-PAYLOAD-ABSENT` | policy | B | the Scenario carries no `scenario-intent` payload |
| `XDL1-PLAN-PROFILE-PAYLOAD-KIND` | binding | B | a payload `kind` does not match its attachment point |
| `XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE` | policy | B | more than one payload at one attachment pointer |
| `XDL1-PLAN-PROFILE-TARGET-MISMATCH` | binding | B | a payload `target` differs from its owning resource/element |
| `XDL1-PLAN-SYSTEM-MISSING` | policy | B | no System resource is present |
| `XDL1-PLAN-SYSTEM-AMBIGUOUS` | policy | B | more than one System resource is present |
| `XDL1-PLAN-SCENARIO-MISSING` | policy | B | no Scenario references the selected System |
| `XDL1-PLAN-SCENARIO-AMBIGUOUS` | policy | B | more than one Scenario references the selected System |
| `XDL1-PLAN-DEPLOYMENT-AMBIGUOUS` | policy | B | more than one Deployment references the selected System |
| `XDL1-PLAN-DEPLOYMENT-UNBOUND` | binding | B | a Deployment is present but the Scenario does not reference it |
| `XDL1-PLAN-SEED-MISSING` | semantic | N | the admitted payload omits the explicit seed |
| `XDL1-PLAN-SEED-RANGE` | semantic | B | the seed is outside `0 … 9007199254740991` |
| `XDL1-PLAN-PARAMETER-DUPLICATE` | semantic | B | a declared parameter `id` appears twice |
| `XDL1-PLAN-PARAMETER-VALUE-TYPE` | semantic | N | a parameter value does not match its declared `valueType` |
| `XDL1-PLAN-PARAMETER-BOUND` | semantic | B | a parameter value exceeds the finite library bound |
| `XDL1-PLAN-QUANTITY-NONFINITE` | semantic | N | a declared numeric quantity is not finite |
| `XDL1-PLAN-QUANTITY-NEGATIVE` | semantic | B | a declared quantity that must be non-negative is negative |
| `XDL1-PLAN-QUANTITY-OVERFLOW` | semantic | B | a declared quantity exceeds `max_ticks` or the numeric bound |
| `XDL1-PLAN-TIME-UNIT-UNKNOWN` | semantic | B | a declared time unit is not in the closed vocabulary |
| `XDL1-PLAN-TIME-PRECISION` | semantic | B | a declared time value does not land on an exact integer tick |
| `XDL1-PLAN-TIME-DOMAIN-UNRESOLVED` | semantic | N | a declared time domain reference does not resolve to a System time domain |
| `XDL1-PLAN-TIME-MAPPING-MISSING` | binding | N | a used pair of time domains has no declared mapping |
| `XDL1-PLAN-FAULT-TRIGGER-MISSING` | semantic | N | a fault carries no resolvable trigger |
| `XDL1-PLAN-FAULT-DURATION-INVALID` | semantic | B | a fault duration is absent, negative, non-finite, or unresolvable |
| `XDL1-PLAN-DEPENDENCY-MISSING` | semantic | N | `dependsOn` names a step that is not declared in the Scenario |
| `XDL1-PLAN-DEPENDENCY-CYCLE` | semantic | B | the declared dependency graph contains a cycle |
| `XDL1-PLAN-SCHEDULE-AMBIGUOUS` | semantic | B | two faults declare the same `declared-order` trigger |
| `XDL1-PLAN-BOUND-EXCEEDED` | policy | B | a declared entity count, or one of the three `max_parameters` scopes of §10.3 (per-payload / total compiled / declared core), exceeds the finite library bound |
| `XDL1-PLAN-ARTIFACT-PIN-MISSING` | binding | B | an in-scope binding references an artifact without an immutable digest |
| `XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED` | binding | N | a binding artifact reference does not resolve to a declared artifact |
| `XDL1-PLAN-REALIZATION-UNSUPPORTED` | policy | B | a `physical` binding/target realization is declared (Phase 1 unsupported) |
| `XDL1-PLAN-DELIVERY-UNSUPPORTED` | binding | B | declared `in-place`/`staged` delivery with no pinned artifact |
| `XDL1-PLAN-RETRY-UNSUPPORTED` | binding | B | a retry policy is declared together with `delivery = "none"` |
| `XDL1-PLAN-METRIC-LINK-INCOMPLETE` | binding | B | a metric has no resolving observer/time/unit linkage |
| `XDL1-PLAN-OBSERVER-UNRESOLVED` | binding | N | an observer target or time domain does not resolve |
| `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT` | policy | B | an emitted plan leaf matches a credential/private-key/userinfo pattern |
| `XDL1-PLAN-INPUT-MUTATED` | policy | B | a re-hashed input digest differs from its already-hashed value |
| `XDL1-PLAN-DIGEST-SELFCHECK` | policy | B | the recomputed plan digest does not match the emitted digest |

Credential/secret scan (matched against emitted plan leaf strings, case-insensitive): credential-like assignment
(a credential keyword such as `password`, `passwd`, `secret`, `token`, or `api_key` followed by `:` or `=`),
a private-key marker line, and URI userinfo (an authority that carries a user-information component before `@`).
A match rejects the compile; the offending value is never echoed into the diagnostic message.

## 10. Quantities, units, and finite library bounds (frozen)

### 10.1 Time

`TIME_UNIT_TICKS = {"tick": 1, "ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000}` — the canonical unit is the
`tick` (1 tick = 1 ns). Conversion uses `fractions.Fraction(value) * TIME_UNIT_TICKS[unit]`; the result must be an
exact non-negative integer `≤ max_ticks`, otherwise the compile rejects with the code from §9. A declared
`unitSemantics` label is recorded verbatim elsewhere and is never used for conversion. Untyped/absent units are never
assumed: scheduling, durations, and tolerances always carry an explicit closed-vocabulary unit.

### 10.2 `ExperimentLimits` (defaults, all positive; non-positive values raise `ValueError`)

| Field | Default | Applies to |
| --- | --- | --- |
| `max_resources` | 1 000 | closed input set (mirrors accepted `LoadLimits`) |
| `max_bytes_per_file` | 5 242 880 (5 MiB) | each input source (mirrors accepted `LoadLimits`) |
| `max_parameters` | 256 | three explicit scopes (§10.3): each declared extension `parameterList`; the total compiled-parameter count; each declared core `Component`/`System`.`spec.parameters[]` list |
| `max_steps` | 256 | declared Scenario steps |
| `max_faults` | 256 | declared Scenario faults |
| `max_observers` | 256 | declared Scenario observers |
| `max_metrics` | 256 | declared Scenario metrics |
| `max_dependencies_per_step` | 64 | `dependsOn` entries per step |
| `max_flows` | 1 024 | declared System flows |
| `max_bindings` | 512 | declared Deployment bindings |
| `max_ticks` | 9 007 199 254 740 991 (2⁵³−1) | any canonical tick value |
| `max_seed` | 9 007 199 254 740 991 | seed value |
| `max_number_magnitude` | 1e15 | declared numeric parameter magnitude |
| `max_text_length` | 200 | declared text/limitation strings |
| `max_limitations` | 64 | merged plan limitations |
| `max_diagnostics` | 256 | returned diagnostics before the compile fails closed |

These are platform **library** limits. They are not thesis safety thresholds, tolerances, deadlines, or protocol
values, and none of them is derived from a scientific protocol.

### 10.3 Parameter-count semantics and scopes (frozen; resolves `XDL1-RVW-001`)

`ExperimentLimits.max_parameters` (default `256`) is enforced over **three** explicitly named scopes. All three
violations reuse the single stable code `XDL1-PLAN-BOUND-EXCEEDED` (gate `policy`); each diagnostic names the
scope and the observed and bound counts, and every violation returns `plan = None`.

1. **Per-payload scope.** For every declared extension `parameterList` — `scenario-intent.parameters`, each
   `step-intent.parameters`, and each `fault-intent.parameters` — the declared list length must satisfy
   `len(list) ≤ max_parameters`. Checked where the list is read; the diagnostic pointer is that payload's
   parameter pointer.
2. **Total compiled-parameter scope.** Let

   ```text
   C_total = len(plan["parameters"])
           + Σ over entry in plan["lifecycleIntent"] of len(entry["parameters"])
           + Σ over entry in plan["faultSchedule"]  of len(entry["parameters"])
   ```

   `C_total` must satisfy `C_total ≤ max_parameters`. This is the total number of *compiled* experiment
   parameters emitted anywhere in the plan. It counts every parameter compiled from an extension `parameterList`
   form (§4.2–§4.4); it **excludes** `components[].declaredParameters`, which are declared core parameter
   *projections* (scope 3), not compiled payload parameters, and excludes the `seed`, which is a single scalar.
   Checked once over the fully compiled sections immediately before §8 identity finalization (§6). On the success
   path each declared parameter produces exactly one emitted entry, so an equivalent statement is
   `Σ len(declared payload parameterList) ≤ max_parameters`.
3. **Declared core-parameter scope.** For every declaring core list projected into `components[].declaredParameters`
   — `System.spec.parameters[]` and the `spec.parameters[]` of each referenced `Component` — the declared list
   length must satisfy `len(list) ≤ max_parameters`. Checked during `components[]` projection; the diagnostic
   pointer identifies the declaring resource's `spec.parameters`.

Scope 3 is added by this successor so that the declared-core-parameter surface introduced by `XDL1-DD-14` is
bounded as well and has no unbounded analogous gap; it does not change scopes 1–2 of the predecessor table, it
makes the previously implicit total scope explicit.

**Negative-evidence obligation (resolves `XDL1-RVW-003`).** Every scope above must be exercised by at least one
independent negative case that exceeds the bound and observes `XDL1-PLAN-BOUND-EXCEEDED` with no plan, bound into
the XDL1-UNIT and XDL1-VALIDATION measures by the verification-design stage. In particular the **total
compiled-parameter** case must supply declarable per-payload lists each within the per-payload bound whose sum
exceeds `max_parameters`, and must observe the total-scope diagnostic. `XDL1-PLAN-BOUND-EXCEEDED` may not remain
the only frozen diagnostic code with zero negative coverage. A declared bound without such negative evidence is
incomplete, not satisfied.

## 11. Dependency and schedule order (frozen)

### 11.1 Dependency graph and order

* Nodes: every `System.spec.componentInstances[].id` plus every declared Scenario step `id`. Supporting node entries
  (`System.spec.nodes[].id`, `System.spec.devices[].id`) are emitted as `dependencyOrder` entries derived from the
  owning `componentInstances`/`devices` `nodeId`, not as independent graph nodes.
* Edges:
  * component-instance edges from `System.spec.flows[]`: for each flow, the endpoint owner of
    `sourceEndpointId` (resolved through `System.spec.endpoints[].ownerId`) precedes the owner of each of
    `destinationEndpointIds`; edges are kept only when both owners are distinct component instances; self-edges and
    flow cycles therefore surface as a graph cycle;
  * step edges from `step-intent.dependsOn`.
* Order: Kahn topological sort. The ready set is drained in ascending key
  `(kindRank, declaredIndex, id)` with `kindRank = {"node": 0, "component-instance": 1, "step": 2}`. Equivalent
  declared inputs always yield the same `dependencyOrder`; permuting the input resource or payload order does not
  change it.
* Cycle or unsatisfiable ordering → `XDL1-PLAN-DEPENDENCY-CYCLE` with the offending node ids in `related`; an
  unresolved `dependsOn` → `XDL1-PLAN-DEPENDENCY-MISSING`. No partial order is emitted.

### 11.2 Schedule and observation order

* `lifecycleIntent` order key: `(timeDomainId, atTicks, phaseRank, stepId)` with
  `phaseRank = {"prepare":0,"start":1,"observe":2,"stop":3,"cleanup":4}`; `atTicks` comes from the step's declared
  `schedule` through §10.1.
* `faultSchedule` order key: `(triggerKindRank, timeDomainKey, tickOrOrder, faultId)` with
  `triggerKindRank = {"time":0,"declared-order":1}`; for time triggers `timeDomainKey = timeDomainId` and
  `tickOrOrder = atTicks`, for declared-order triggers `timeDomainKey = ""` and `tickOrOrder = order`.
* `observers` order key: `(timeDomainId, observerId)`; `metrics` order key: `(metricId)` with `observerIds` and
  `timeDomainIds` sorted.
* Cross-time-domain comparison is never inferred: the declared `mapping` string is recorded, not executed, and a used
  pair without a declared mapping is rejected (`XDL1-PLAN-TIME-MAPPING-MISSING`; the accepted gate emits
  `XDL-SEMANTIC-TIME-MAPPING` on the loader path first). Ordering across domains is therefore per-domain and stable.
* Competing declared order: two faults sharing a `declared-order` value → `XDL1-PLAN-SCHEDULE-AMBIGUOUS`. Equal
  time-trigger ticks are **not** ambiguous; they are tie-broken by `faultId`.

## 12. No-side-effect contract (frozen)

The compiler core (`compile_experiment_plan`) and the canonicalization/digest helpers:

* open no file, create no directory, write no byte, and discover no path (`compile_experiment_files` reads only the
  explicitly supplied paths, through the accepted loader — it performs no discovery);
* start no process, thread, or coroutine and import no `subprocess`, `socket`, `threading`, `multiprocessing`, or
  `urllib.request`/`http` capability;
* perform no registry, catalog, DNS, or network access (the accepted catalog/C++ X-COM activation-plan modules are
  not invoked at all by Phase 1);
* read no ambient clock, locale, environment variable, hostname, user, or CWD in the plan body — the only time value
  is explicit or the fixed sentinel;
* mutate no input: normalized resources are immutable frozen values, and inputs are never written back;
* emit the plan as a fresh plain `dict` tree owned by the caller;
* return no plan of any kind on rejection (no partial plan, no placeholder, no executable handle).

The CLI writes only to an explicitly requested `-o PATH` (or stdout) and refuses to overwrite an input path, mirroring
the accepted `normalize` guard.

## 13. Additive API and CLI exposure (frozen)

### 13.1 Module `src/xverse_xdl/experiment_plan.py`

```text
PROFILE_NAMESPACE, PROFILE_RESOURCE_VERSION, PROFILE_SCHEMA_VERSION, PROFILE_SCHEMA_ID,
PLAN_VERSION, GENERATOR_TASK, GENERATOR_VERSION, DEFAULT_GENERATED_AT,
PLAN_DOMAIN_SEPARATOR, RESOURCE_DOMAIN_SEPARATOR, INPUT_DOMAIN_SEPARATOR,
TIME_UNIT_TICKS, PHASE_ORDER, TRIGGER_KIND_ORDER, SUPPORTED_REALIZATION_CLASSES,
DIAGNOSTIC_CODES, PAYLOAD_KINDS, PLAN_STATUS

@dataclass(frozen=True) class ExperimentLimits            # §10.2
@dataclass(frozen=True) class ExperimentPlanResult:
    diagnostics: tuple[Diagnostic, ...]
    plan: dict[str, Any] | None
    run: FrozenMap
    @property def is_valid(self) -> bool                  # no error diagnostic and plan is not None

def compile_experiment_plan(resources, *, static_readiness=None, run_id=None, generated_at=None,
                            expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
def compile_experiment_sources(sources, *, profile_schema_paths=(), run_id=None, generated_at=None,
                               expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
def compile_experiment_files(paths, *, profile_schema_paths=(), run_id=None, generated_at=None,
                             expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
def resource_semantic_digest(resource) -> str
def canonical_plan_bytes(plan) -> bytes
def compute_plan_digest(plan) -> str
def plan_matches_digest(plan) -> bool
def experiment_plan_status(plan) -> str
def plan_public_data(result) -> dict
```

`compile_experiment_sources`/`_files` call the accepted `validate_sources`/`validate_files` with the supplied
`profile_schema_paths`, then `compile_experiment_plan` with `ValidationResult.resources` and
`ValidationResult.readiness`. No signature, default, return shape, or diagnostic of `validate_sources`,
`validate_files`, `validate_mappings`, `canonical_json`, `derive_catalog`, `build_lifecycle_plan`,
`catalog_entry_public_data`, or the C++ X-COM activation-plan contract changes.

### 13.2 CLI (`src/xverse_xdl/cli.py`, additive subcommand)

```text
xdl experiment compile [--profile-schema PATH]... [--run-id ID] [--generated-at RFC3339]
                       [--expect-input-digest NAME=SHA256]... [--format text|json]
                       [-o PLAN.json] RESOURCE...
```

| Behaviour | Contract |
| --- | --- |
| exit `0` | a plan was emitted; stdout carries the text summary or the JSON envelope; `-o` receives canonical plan JSON |
| exit `1` | rejected; diagnostics on stdout (`--format json`) or stderr (text); no `-o` file is created or overwritten; `plan = null` |
| exit `2` | invocation/internal failure (bad `--expect-input-digest`, `-o` equal to an input path, runtime error), matching the accepted CLI convention |
| `--format text` (default) | one line per diagnostic (`SEVERITY CODE [gate] location/pointer: message` + `correction`) or `resolved plan <digest> (<n> sections)` |
| `--format json` | `{"reportVersion":"1","toolVersion":…,"valid":…,"plan":<plan or null>,"run":{…},"diagnostics":[…]}` |
| `xdl validate`, `xdl normalize`, `xdl version` | byte-identical behaviour, output, and exit codes for existing inputs |

`src/xverse_xdl/__init__.py` gains `experiment_plan` exports (`ExperimentLimits`, `ExperimentPlanResult`,
`compile_experiment_plan`, `compile_experiment_sources`, `compile_experiment_files`, `canonical_plan_bytes`,
`compute_plan_digest`, `plan_matches_digest`, `experiment_plan_status`) and adds no removal to `__all__`.

## 14. Invariants (frozen, verification targets)

| ID | Invariant |
| --- | --- |
| `XDL1-INV-01` | Any error diagnostic implies `plan is None`; no partial or executable plan is ever returned |
| `XDL1-INV-02` | Compilation performs no filesystem, network, registry, process, clock, locale, or environment access |
| `XDL1-INV-03` | An emitted plan satisfies `plan_matches_digest(plan)` and `status == "resolved"` |
| `XDL1-INV-04` | Equal declared content (any encoding, any input permutation) yields equal canonical plan bytes and equal plan digest |
| `XDL1-INV-05` | No scientific value is defaulted, invented, or narrowed; only platform library bounds are enforced |
| `XDL1-INV-06` | `runId`/`generatedAt`/`sourceByteDigests` never appear in the plan body and never affect `planDigest` |
| `XDL1-INV-07` | Existing public APIs, schemas, diagnostics, and CLI behaviour for existing inputs are unchanged |
| `XDL1-INV-08` | The plan's `nonReadiness` statement and declared `limitations` are present and truthful |
| `XDL1-INV-09` | Only generic platform vocabulary appears; no automotive, thesis, or domain-specific primitive |
| `XDL1-INV-10` | Every emitted array is in the frozen §11 order and every declared quantity is within `ExperimentLimits` |
| `XDL1-INV-11` | A plan is emitted only when all three §10.3 `max_parameters` scopes hold; a violation yields `plan is None` and `XDL1-PLAN-BOUND-EXCEEDED` |
| `XDL1-INV-12` | An emitted plan always carries exactly one `components[scope="system"]` entry whose `declaredParameters` projects every declared `System.spec.parameters[]` entry, and no System parameter appears in a component-instance entry |

## 15. Failure semantics

| Condition | Outcome | Code / exit |
| --- | --- | --- |
| accepted gate rejects (parse/schema/reference/semantic/profile) | diagnostics, no plan, plan stage skipped | accepted `XDL-*`; CLI exit `1` |
| admitted Profile absent / wrong version / wrong `schemaRef` | diagnostics, no plan | `XDL1-PLAN-PROFILE-*`; exit `1` |
| no, or more than one, System / Scenario / Deployment selection | diagnostics, no plan | `XDL1-PLAN-*-MISSING` / `-AMBIGUOUS` / `-UNBOUND`; exit `1` |
| seed/parameter missing, mistyped, duplicated, or out of bound | diagnostics, no plan | `XDL1-PLAN-SEED-*` / `-PARAMETER-*`; exit `1` |
| unknown unit, imprecise/negative/non-finite/overflow quantity | diagnostics, no plan | `XDL1-PLAN-TIME-*` / `-QUANTITY-*`; exit `1` |
| dependency cycle, unresolved dependency, competing declared order | diagnostics, no plan | `XDL1-PLAN-DEPENDENCY-*` / `-SCHEDULE-AMBIGUOUS`; exit `1` |
| unpinned referenced artifact, unsupported realization/delivery/retry | diagnostics, no plan | `XDL1-PLAN-ARTIFACT-*` / `-REALIZATION-*` / `-DELIVERY-*` / `-RETRY-*`; exit `1` |
| metric without a resolving observer/time/unit link | diagnostics, no plan | `XDL1-PLAN-METRIC-LINK-INCOMPLETE`; exit `1` |
| credential-like value in an emitted leaf | diagnostics, no plan, value not echoed | `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT`; exit `1` |
| input re-hash differs after hashing | diagnostics, no plan | `XDL1-PLAN-INPUT-MUTATED`; exit `1` |
| entity/quantity bound exceeded, or a §10.3 parameter-count scope violated (per-payload, total compiled, or declared core) | diagnostics, no plan | `XDL1-PLAN-BOUND-EXCEEDED`; exit `1` |
| plan digest self-check fails | diagnostics, no plan | `XDL1-PLAN-DIGEST-SELFCHECK`; exit `2` |
| bad CLI argument or `-o` collision with an input | no plan, no file written | CLI message; exit `2` |

## 16. Compatibility and preserved boundaries

* **Accepted schemas unchanged.** `xdl/schemas/v1alpha1/**` is not modified; the new payload schema is a separate
  Profile artifact referenced through `spec.schemaRef`, as the accepted extension mechanism requires.
* **Accepted public API unchanged.** Every existing function, default, dataclass field, enum, exported name,
  diagnostic code, and serialization stays byte-compatible; XDL1 only adds.
* **Accepted C++ X-COM boundary unchanged.** `proto/xverse/xcom/v1/**`, `src/xverse/xcom/**`,
  `src/xverse/xcom/contracts/**`, and `xdl/profiles/xcom-v0.1.schema.json` are not touched, imported, or invoked.
* **M3 catalog/lifecycle unchanged and not invoked.** `derive_catalog`, `build_lifecycle_plan`, and the lifecycle
  controller keep their accepted semantics; Phase 1 starts nothing.
* **Dependency set unchanged.** Only the standard library plus the already-admitted `jsonschema`, `referencing`,
  and `ruamel.yaml` are used; `pyproject.toml` already ships `xdl/profiles` in the wheel, so no packaging change is
  authorized or required.
* **Traceability.** `allocated_to` links (`XDL1-L-101`…`XDL1-L-119`) are added by this stage; `decomposes_to`,
  `implemented_by`, `verified_by`, `analyzed_by`, and `validates` links are owned by the unit-specification,
  implementation, verification-design, and validation stages respectively. `implemented_by` endpoints use the
  candidate source-file SHA-256 as the code revision, per the admitted workflow.
* **Known scheduled refresh (not this stage).** 21 pre-existing `implemented_by` links target
  `engineering/project.json` with its previous hash; after the requirements-stage current-pointer update those code
  endpoint revisions are stale and `validate_trace` cannot pass until the validation stage refreshes exactly those
  mutable links. This stage records the condition instead of performing an unassigned repair (see the stage result
  `findings`).

### 16.1 Requirement coverage of this design

| Requirement | Frozen element of this design |
| --- | --- |
| `XDL1-SR-001` | §6.1 selection rules; plan `selection`; codes `XDL1-PLAN-SYSTEM-*`, `-SCENARIO-*`, `-DEPLOYMENT-*` |
| `XDL1-SR-002` | §5 concept mapping; §7 `components`/`flows`; `XDL1-DD-03`; no new kind |
| `XDL1-SR-003` | §4.3 `step-intent`; §7 `lifecycleIntent`; §11.2 order; no lifecycle execution |
| `XDL1-SR-004` | §5 realization/binding mapping; §7 `bindings`, `selection.staticReadiness`; §4.5 `realization-intent`; `XDL1-DD-11` |
| `XDL1-SR-005` | §4.2 `seed`/`parameters`; §9 seed/parameter codes; `XDL1-DD-10` |
| `XDL1-SR-006` | §5 time-domain/time-mapping mapping; §7 `timeDomains`/`timeMappings`; §11.2; `XDL1-PLAN-TIME-DOMAIN-UNRESOLVED`, `-TIME-MAPPING-MISSING` |
| `XDL1-SR-007` | §4.4 `fault-intent`; §7 `faultSchedule`; §11.2 tie-break and competing-order rule; no fault execution |
| `XDL1-SR-008` | §5 observer mapping; §7 `observers`; §11.2 order; no observer invocation |
| `XDL1-SR-009` | §5 metric mapping; §7 `metrics`; `XDL1-PLAN-METRIC-LINK-INCOMPLETE`; `status = reference-only` |
| `XDL1-SR-010` | §5 artifact/model mapping; §7 `bindings[].artifactRefs`; `XDL1-PLAN-ARTIFACT-PIN-MISSING` |
| `XDL1-SR-011` | §7 `provenance`; §8 identity rules; independent version dimensions; `XDL1-DD-05` |
| `XDL1-SR-012` | §7 `limitations`, `nonReadiness`; `XDL1-DD-09` |
| `XDL1-SR-013` | §11.1 dependency graph, order, cycle rejection; `XDL1-DD-07` |
| `XDL1-SR-014` | §12 no-side-effect contract; §6 stage order; `XDL1-INV-01`, `XDL1-INV-02` |
| `XDL1-SR-015` | §4.5 `delivery`/`retry`; §9 `-REALIZATION-*`, `-DELIVERY-*`, `-RETRY-*`; `XDL1-DD-11` |
| `XDL1-SR-016` | §3.1 frozen identities; §13 additive API/CLI; §16 preserved boundaries; `XDL1-DD-12` |
| `XDL1-SR-017` | §4 payload schema; §3.2 admission; §9 `-PROFILE-*`; `XDL1-DD-01`, `XDL1-DD-02` |
| `XDL1-SR-018` | §7 `faultSchedule`/`lifecycleIntent` order; §8 canonical identity; `XDL1-INV-04`, `XDL1-INV-06` |
| `XDL1-SR-019` | §4 shared time definitions; §10 units and `ExperimentLimits`; §9 quantity/time codes; `XDL1-DD-06`, `XDL1-DD-10`, `XDL1-DD-13` |

### 16.2 Predecessor review resolution (frozen contract for the successor chain)

The successor requirement baseline (`requirements.md` `XDL1-SR-002`, `XDL1-SR-012`, `XDL1-SR-014`,
`XDL1-SR-019`) already amends its acceptance criteria for the rejected predecessor findings; this design freezes
the concrete behaviour those criteria require. Findings are recorded, not repaired, in the predecessor; the
successor realizes them here.

| Finding | Predecessor defect | Frozen resolution in this design |
| --- | --- | --- |
| `XDL1-RVW-001` | `ExperimentLimits.max_parameters` declared as "per payload and total compiled parameters" but only individual lists were checked; a plan carrying more compiled parameters than the bound was emitted as resolved with no diagnostic. | `XDL1-DD-13` and §10.3 freeze three scopes, including the deterministic `C_total` rule, and §6 places the total-scope check before identity finalization. Any scope violation emits `XDL1-PLAN-BOUND-EXCEEDED` and returns no plan (`XDL1-SR-014`, `XDL1-SR-019`). |
| `XDL1-RVW-002` | `System.spec.parameters` was mapped to `declaredParameters` by the design but silently omitted from every plan section; only `Component.spec.parameters` was projected. | `XDL1-DD-14`, the §5 mapping rows, and the §7 field rules freeze the always-present System-scope `components[]` entry as the deterministic destination for `System.spec.parameters` (and `System.spec.models`), with no duplication into component entries and no drop (`XDL1-SR-002`, `XDL1-SR-011`). |
| `XDL1-RVW-003` | `XDL1-PLAN-BOUND-EXCEEDED` was the only one of the frozen diagnostic codes with no test; no count-based bound had a negative case. | §10.3 adds the negative-evidence obligation: one independent negative case per declared bound scope, including the total compiled-parameter scope, bound into XDL1-UNIT and XDL1-VALIDATION by the verification-design stage (`XDL1-SR-019`, `XDL1-SR-012`). |

Repeating these resolutions by inspection is not proof: satisfaction requires the successor's own code and
executed measures, owned by later stages. No code, schema, fixture, or test is written by this architecture stage.

## 17. Hand-off to the unit-specification stage

The next stage must, against this design only and without code: define unit interfaces, state/concurrency,
inputs/outputs/errors/invariants, planned source paths, independent table-driven expected outcomes (including the
"reject" and "no plan" rows above), adversarial and metamorphic cases, exact pytest-discoverable test identifiers,
and static checks. The required negative surface is fixed here: unknown Profile/version/`schemaRef`/kind/field,
absent/ambiguous selection, missing reference/pin/time mapping/seed, non-finite/negative/overflow/imprecise
quantity, unknown unit, unknown fault/action, dependency cycle, competing declared order, unsupported
realization/delivery/retry, incomplete metric linkage, secret-bearing leaf, reordered/permuted inputs, equal
YAML/JSON semantics, volatile-only differences, and post-hash mutation. In addition, the successor must carry the
resolution-negative surface introduced by `XDL1-RVW-001/002/003`: a positive case proving a declared System core
parameter (for example the fixture's `loop-count`) appears at `components[scope="system"].declaredParameters` and
is not duplicated into any component-instance entry, and an independent negative case for **each** declared
count-based bound scope in §10.3 — including the **total** compiled-parameter scope whose per-payload lists are
each individually within `max_parameters` — asserting `XDL1-PLAN-BOUND-EXCEEDED`, `plan is None`, and no side
effect. Scientific protocol numbers remain caller inputs and must not appear in any unit expectation.

## 18. Next step and model recommendation

Next stage: **unit_specification**. Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning
remains the most cost-effective and only authorized route, because this is deterministic transcription of the frozen
contracts above into unit cases and expected values; no stronger-reasoning tier is needed and there is no new
Terra/Luna/Sol/Astra engineering route, no fallback, and no model switch. Blocker: none at this stage; implementation
cannot start until the four design stages complete and the precode gate passes.
