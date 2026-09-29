# X-COM Unit Design — Capability 007

> Deterministic projection of `unit-design.json` (schema version 1).
> Do not edit by hand; regenerate from the model and re-run
> `scripts/validate_xcom_unit_design.py --check-human`.

## Model identity

| Field | Value |
| --- | --- |
| Task | T010 |
| Capability | 007-xcom-core |
| Schema version | 1 |
| Baseline revision | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Candidate revision rule | Every candidate records its own exact revision and the exact accepted predecessor revision it derives from; acceptance is per candidate and is never inherited from a sibling or inferred from source presence. |
| Units | 30 |
| Invariants | 14 |

## REF-002 disposition

- Disposition: `unchanged`
- Promoted: none
- Source: `specs/007-xcom-core/reference-traceability.md`

## Coverage

Component exemptions:

- none

Requirement exemptions:

- none

## Declared counts

| Family | Units |
| --- | ---: |
| CORE | 8 |
| ENB | 5 |
| GW | 3 |
| INTG | 4 |
| OBS | 2 |
| STIM | 5 |
| XDL | 3 |
| **units** | **30** |
| **invariants** | **14** |

## Doxygen plan (DOX-01)

| Field | Value |
| --- | --- |
| Configuration | `Doxyfile` |
| Warning-as-error | True |
| Mandatory file block | `file`, `brief`, `ingroup` |
| Mandatory public tags | `brief`, `ownership`, `lifetime`, `thread_safety`, `failure` |
| Conditional public tags | `param`, `return`, `retval`, `note`, `pre`, `post` |
| Coverage rule | Every public declaration in a C++ unit header is documented; every unit header carries the mandatory file block; the ownership, lifetime, thread-safety, and failure aliases are present on every public declaration. |

Groups:

- `CORE` -> `xcom_core`
- `ENB` -> `xcom_enb`
- `GW` -> `xcom_gw`
- `INTG` -> `xcom_intg`
- `OBS` -> `xcom_obs`
- `STIM` -> `xcom_stim`
- `XDL` -> `xcom_xdl`

Known gaps (recorded, never reported as closed):

| Gap | Description | Owning tasks | Status |
| --- | --- | --- | --- |
| `DOX-GAP-01` | Doxyfile sets WARN_IF_UNDOCUMENTED = NO and WARN_NO_PARAMDOC = NO; the strict C++ configuration is not yet admitted. | T011, T037 | `allocated` |
| `DOX-GAP-02` | Generated protobuf C++ provenance and documentation policy are admitted by T011. | T011 | `allocated` |
| `DOX-GAP-03` | System and third-party headers are out of documentation scope; the allowed exclusion list is admitted by T011. | T011, T037 | `allocated` |

## Units

### XCOM-DU-001 — Value and payload view

**Responsibility.** Typed value and bounded payload view with a metadata-only default and an explicit bounded view lifetime.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T013 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline value and payload source is present under T013 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/value.hpp` (established)
- `src/xverse/xcom/src/value.cpp` (established)
- `tests/xcom/core_types/` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — Values are constructed by the caller and owned by the caller; the unit retains no shared state.
- Lifetime: `invocation-scoped` — A value is valid for the callback or invocation scope and is not retained beyond it.
- Exposes view: True; view lifetime: bounded to the owning item or callback scope; the view is not retained after the callback returns

**Thread-safety.**

- Model: `immutable-value` — Values are immutable after construction and are copied on hand-off.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| payload view size | `bytes` | True | None | unit configuration |
| value elements | `capacity` | True | None | unit configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| declared bound exceeded | `failed` |
| outcome unknown for the payload view | `failed` |
| malformed value or payload view | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-CORE-002`, `XCOM-SW-CORE-004`

**Component refs:** `XCOM-CMP-004`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-04`, `CHK-05`, `CHK-06`, `CHK-07`, `NEG-12`, `NEG-15`, `NEG-20`

### XCOM-DU-002 — Contract and logical identity

**Responsibility.** Versioned contract descriptor and logical-identity record separating logical identity from realization.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T012 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline contract and identity source is present under T012 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/contract.hpp` (established)
- `src/xverse/xcom/src/contract.cpp` (established)

**Ownership / lifetime.**

- Ownership: `platform-owns-shared` — The contract descriptor is published once by the platform and read by many consumers.
- Lifetime: `plan-scoped` — The descriptor is valid for the activation-plan scope and is replaced only by a new plan.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `immutable-value` — The descriptor is immutable after publication and copies are independent.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| descriptor size | `bytes` | True | None | unit configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| internal descriptor defect | `failed` |
| incompatible contract version or logical identity | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 4 / public 4

**Requirement links:** `XCOM-SW-CORE-001`, `XCOM-SW-CORE-003`

**Component refs:** `XCOM-CMP-004`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-04`, `NEG-07`, `NEG-12`, `NEG-13`

### XCOM-DU-003 — Item identity, origin, time, and correlation

**Responsibility.** Item identity, origin, timestamps, and correlation and causation references carried without interpretation.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T013 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline item source is present under T013 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/item.hpp` (established)
- `src/xverse/xcom/src/item.cpp` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — Items are constructed by the caller and owned by the caller; the unit keeps no registry.
- Lifetime: `invocation-scoped` — An item is valid for the routing invocation scope and is not retained by this unit.
- Exposes view: True; view lifetime: bounded to the item lifetime; a payload view is never retained beyond the owning item

**Thread-safety.**

- Model: `immutable-value` — Items are immutable after construction and copied or moved on hand-off.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| item record size | `bytes` | True | None | unit configuration |
| identifier elements | `capacity` | True | None | unit configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| declared bound exceeded | `failed` |
| outcome unknown for item provenance | `failed` |
| malformed item identity or origin | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-CORE-002`, `XCOM-SW-CORE-003`, `XCOM-SW-CORE-010`

**Component refs:** `XCOM-CMP-004`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-04`, `NEG-08`, `NEG-09`

### XCOM-DU-004 — Diagnostics and deterministic ordering

**Responsibility.** Stable diagnostic codes with severity, phase, reason, and correction, ordered deterministically.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T013 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline diagnostic source is present under T013 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp` (established)
- `src/xverse/xcom/src/diagnostic.cpp` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — Diagnostics are values produced for the caller and owned by the caller.
- Lifetime: `invocation-scoped` — A diagnostic is valid for the reporting invocation and is not retained.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `immutable-value` — Diagnostics are immutable after construction and ordered by a stable key.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| diagnostic record size | `bytes` | True | None | unit configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| internal diagnostic defect | `failed` |
| incompatible severity, phase, or reason mapping | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 4 / public 4

**Requirement links:** `XCOM-SW-CORE-006`, `XCOM-SW-CORE-010`

**Component refs:** `XCOM-CMP-004`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-05`, `CHK-06`

### XCOM-DU-005 — Result, outcome, and core type aggregate

**Responsibility.** Result and outcome value type plus the aggregate core type header, with honest unknown handling.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T013 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline result and core-type aggregate is present under T013 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/core_types.hpp` (established)
- `src/xverse/xcom/include/xverse/xcom/result.hpp` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — Result values are produced for the caller and owned by the caller.
- Lifetime: `invocation-scoped` — A result is valid for the calling invocation scope and is not retained.
- Exposes view: True; view lifetime: bounded to the owning result; a payload view is not retained after the result is consumed

**Thread-safety.**

- Model: `immutable-value` — Results are immutable after construction and copied on hand-off.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| payload view size | `bytes` | True | None | unit configuration |
| value elements | `capacity` | True | None | unit configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| declared bound exceeded | `failed` |
| outcome unknown for the result | `failed` |
| malformed result variant | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 4 / public 4

**Requirement links:** `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`

**Component refs:** `XCOM-CMP-004`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-04`, `CHK-07`, `NEG-25`, `NEG-26`

### XCOM-DU-006 — Endpoint and route lifecycle with generation handles

**Responsibility.** Bounded endpoint and route lifecycle in which only the exact issued generation-bound handle mutates or closes a resource.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T014 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline endpoint/route lifecycle source is present under T014 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp` (established)
- `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` (established)
- `tests/xcom/endpoint_route_lifecycle/` (established)

**Ownership / lifetime.**

- Ownership: `provider-issued-handle` — A provider issues the only handle that may mutate or close an endpoint or route; a stale or foreign handle is rejected.
- Lifetime: `endpoint-generation` — A handle is valid only for the endpoint generation that issued it; restart reconciliation never infers ownership from a name or address.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — Concurrent lifecycle transitions share a per-provider handle table and generation counters.
- Shared state: `generation counters`, `per-provider endpoint and route handle table`
- Synchronization: per-provider mutex held only for the state transition; no lock is held across a provider callback

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| active endpoints and routes | `capacity` | True | None | activation plan |
| retry count | `retry` | True | 0 | activation plan |

Overflow policies: `reject`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| outcome unknown for a lifecycle transition | `failed` |
| provider lifecycle failure | `failed` |
| stale, foreign, or duplicate handle | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 7 / public 7

**Requirement links:** `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`, `XCOM-SW-CORE-005`

**Component refs:** `XCOM-CMP-005`

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-04`, `CHK-05`, `CHK-06`, `NEG-15`, `NEG-18`, `NEG-19`, `NEG-24`

### XCOM-DU-007 — Provider boundary and composition

**Responsibility.** Explicit provider boundary and one-time composition with capability and version negotiation.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T015 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline provider boundary source is present under T015 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/provider.hpp` (established)
- `src/xverse/xcom/src/provider.cpp` (established)

**Ownership / lifetime.**

- Ownership: `provider-issued-handle` — The provider issues the handle that owns its realization; composition never adopts a handle from an address or name.
- Lifetime: `process-scoped` — A registered provider is valid for the process lifetime and is removed only through its handle.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `externally-synchronized` — Composition happens once before activation; the registered-provider table is read-only afterwards.
- Shared state: `registered provider table`
- Synchronization: caller composes providers before activation and performs no concurrent registration afterwards

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| registered providers | `capacity` | True | None | explicit composition input |
| retry count | `retry` | True | 0 | explicit composition input |

Overflow policies: `reject`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| outcome unknown for a provider registration | `failed` |
| provider composition failure | `failed` |
| incompatible provider capability or version | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-CORE-005`, `XCOM-SW-CORE-007`, `XCOM-SW-CORE-008`

**Component refs:** `XCOM-CMP-006`

**Contract refs:** `XCOM-XLC-004`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-05`, `CHK-09`, `NEG-17`

### XCOM-DU-008 — Owned loopback provider

**Responsibility.** Owned loopback provider that exercises the first proof deterministically without a legacy asset or external peer.

| Field | Value |
| --- | --- |
| Family | `CORE` |
| Kind | `test-fixture` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T015, T016 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline loopback provider source is present under T015/T016 but the tasks are not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp` (established)
- `src/xverse/xcom/src/loopback_provider.cpp` (established)
- `tests/xcom/provider_loopback/` (established)

**Ownership / lifetime.**

- Ownership: `provider-issued-handle` — The loopback provider issues the handle for its own route; a foreign handle is rejected.
- Lifetime: `process-scoped` — The test-owned loopback provider is valid for the process lifetime of the fixture.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `single-thread-owner` — The owning test thread drives the loopback route and exclusively owns its per-route in-flight queue; there is no cross-thread hand-off in the first proof.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| per-route in-flight queue depth | `capacity` | True | None | activation plan |
| retry count | `retry` | True | 0 | activation plan |

Overflow policies: `reject`, `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| loopback delivery failure | `failed` |
| outcome unknown for a loopback emission | `failed` |
| loopback policy violation | `rejected` |

**Doxygen obligation.**

- Group: `xcom_core`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-CORE-007`, `XCOM-SW-CORE-009`

**Component refs:** `XCOM-CMP-007`

**Contract refs:** `XCOM-XLC-004`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-05`, `CHK-06`

### XCOM-DU-009 — XDL Profile and activation-plan compiler

**Responsibility.** Deterministic Profile-aware activation-plan compilation from the normalized XDL input, offline and bounded.

| Field | Value |
| --- | --- |
| Family | `XDL` |
| Kind | `build-time` |
| Language | `python` |
| Scope | `first-proof` |
| Owning slice | `T-XDL` |
| Owning tasks | T017, T018 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse_xdl/xcom_plan.py` (established)
- `tests/test_xcom_plan.py` (established)
- `xdl/profiles/xcom-v0.1.schema.json` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — The compiler returns a new plan value to its caller and owns no shared runtime state.
- Lifetime: `process-scoped` — The compiler runs as a bounded build-time process and retains no state after it exits.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Build-time compiler: one process, one thread, offline.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| graph input size | `bytes` | True | None | XDL input |
| compiled nodes and edges | `capacity` | True | None | unit configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| declared bound exceeded | `failed` |
| outcome unknown for a compilation step | `failed` |
| invalid or malformed graph input | `rejected` |

**Doxygen obligation.**

- Required: false — Python build-time tooling; module and function docstrings are covered by scripts/check_doxygen.py.

**Requirement links:** `XCOM-SW-XDL-001`, `XCOM-SW-XDL-002`

**Component refs:** `XCOM-CMP-001`, `XCOM-CMP-002`

**Contract refs:** `XCOM-XLC-005`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-09`, `CHK-10`, `NEG-37`, `NEG-39`

### XCOM-DU-010 — Activation-plan v1 schema

**Responsibility.** Canonical activation-plan v1 schema and digest contract that the C++ decoder validates independently.

| Field | Value |
| --- | --- |
| Family | `XDL` |
| Kind | `derived-artifact` |
| Language | `json` |
| Scope | `first-proof` |
| Owning slice | `T-XDL` |
| Owning tasks | T017 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The schema is a versioned build artifact owned by its authoring task.
- Lifetime: `static-immutable` — The schema is immutable once published and superseded additively by a new version.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `read-only-static` — Immutable schema artifact read concurrently without synchronization.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| schema artifact size | `bytes` | True | None | static artifact |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| schema or digest defect | `rejected` |

**Doxygen obligation.**

- Required: false — JSON schema artifact; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-XDL-001`

**Component refs:** `XCOM-CMP-003`

**Contract refs:** `XCOM-XLC-001`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-09`, `NEG-42`, `NEG-43`

### XCOM-DU-011 — Bounded activation-plan decode

**Responsibility.** Bounded activation-plan decode with independent version and digest checks that fails closed on malformed or drifted input.

| Field | Value |
| --- | --- |
| Family | `XDL` |
| Kind | `data-plane` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-XDL` |
| Owning tasks | T019, T020 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` (established)
- `src/xverse/xcom/src/activation_plan.cpp` (established)
- `tests/xcom/activation_plan/` (established)

**Ownership / lifetime.**

- Ownership: `caller-owns-value` — The decoded plan is returned to the caller, which owns it; the unit retains no decoded state.
- Lifetime: `plan-scoped` — The decoded plan is valid for the activation-plan scope and is immutable after decode.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `immutable-value` — The decoded plan is immutable after a bounded decode and shared read-only.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| plan bytes | `bytes` | True | None | activation plan |
| decoded entities | `capacity` | True | None | activation plan |
| nested structure depth | `depth` | True | None | activation plan |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| declared bound exceeded | `failed` |
| outcome unknown for a decode step | `failed` |
| malformed plan bytes or version or digest mismatch | `rejected` |

**Doxygen obligation.**

- Group: `xcom_xdl`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-XDL-003`, `XCOM-SW-CORE-003`

**Component refs:** `XCOM-CMP-003`

**Contract refs:** `XCOM-XLC-001`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-06`, `CHK-09`, `NEG-21`, `NEG-22`, `NEG-23`

### XCOM-DU-012 — Observation record and payload-view policy

**Responsibility.** Immutable observation record and payload-view policy with metadata-only as the default.

| Field | Value |
| --- | --- |
| Family | `OBS` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-OBS` |
| Owning tasks | T021 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline observation record source is present under T021 but the task is not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/observation.hpp` (established)
- `src/xverse/xcom/src/observation.cpp` (established)

**Ownership / lifetime.**

- Ownership: `platform-owns-shared` — The platform owns the observation record and publishes it read-only to observers.
- Lifetime: `route-scoped` — A record is valid for the route scope in which it was produced.
- Exposes view: True; view lifetime: bounded to the observation record and route scope; metadata-only is the default and a payload view is not retained

**Thread-safety.**

- Model: `immutable-value` — Observation records are immutable projections once built.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| payload view size | `bytes` | True | None | unit configuration |
| record elements | `capacity` | True | None | unit configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| outcome unknown for a record projection | `failed` |
| payload policy absent or payload view beyond the declared bound | `rejected` |

**Doxygen obligation.**

- Group: `xcom_obs`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-OBS-001`, `XCOM-SW-OBS-002`, `XCOM-SW-OBS-005`

**Component refs:** `XCOM-CMP-008`

**Contract refs:** `XCOM-XLC-003`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-04`, `CHK-05`, `CHK-09`

### XCOM-DU-013 — Bounded observer queue, counters, and synthetic sink

**Responsibility.** Bounded observer queue with drop and coalesce counters and a synthetic sink, isolating observer failure from the route.

| Field | Value |
| --- | --- |
| Family | `OBS` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-OBS` |
| Owning tasks | T022, T023 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Baseline observer queue source is present under T022/T023 but the tasks are not user-accepted; coverage stays partial per analysis A12. |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/observation.hpp` (established)
- `src/xverse/xcom/src/observation.cpp` (established)
- `tests/xcom/observation/` (established)

**Ownership / lifetime.**

- Ownership: `platform-owns-shared` — The platform owns the bounded queue and counters shared between the route thread and the observer.
- Lifetime: `route-scoped` — A tap queue is valid for the route scope and is drained or released with the route.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `message-passing` — Producers enqueue records on the route thread and the observer drains them on its own thread through a bounded queue.
- Shared state: `drop and coalesce counters`, `per-tap bounded record queue`
- Synchronization: producer enqueues under the tap mutex and the observer drains on its own thread; counters are atomic

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| per-tap queue depth | `capacity` | True | None | tap policy |
| coalesce window per tap | `quota` | True | None | tap policy |
| retry count | `retry` | True | 0 | tap policy |

Overflow policies: `drop-newest`, `coalesce`, `lossless-backpressure`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| observer detached or failing, isolated from the normal route | `failed` |
| outcome unknown for delivery to the synthetic sink | `failed` |
| queue saturated at the declared bound under the drop-newest tap policy | `rejected` |

**Doxygen obligation.**

- Group: `xcom_obs`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-OBS-003`, `XCOM-SW-OBS-004`

**Component refs:** `XCOM-CMP-008`, `XCOM-CMP-011`

**Contract refs:** `XCOM-XLC-003`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-05`, `CHK-06`, `NEG-18`, `NEG-19`, `NEG-45`

### XCOM-DU-014 — Time authority

**Responsibility.** Explicit time authority with clock-domain mapping and a declared tolerance, rejecting unmapped domains before emission.

| Field | Value |
| --- | --- |
| Family | `STIM` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-STIM` |
| Owning tasks | T025 |
| Maturity | `implemented` |
| Accepted revision | 4b01586b438a8587d231ee8828d896c206c06a96 |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` (established)
- `src/xverse/xcom/src/validation_session.cpp` (established)
- `tests/xcom/validation_session/` (established)

**Ownership / lifetime.**

- Ownership: `platform-owns-shared` — The platform owns the host-implemented time authority for the session lifetime.
- Lifetime: `session-scoped` — The time authority is valid for the validation-session scope.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `externally-synchronized` — The host-implemented time authority is read by the session's single active thread.
- Shared state: none
- Synchronization: caller invokes the time authority from the session's single active thread; the authority holds no internally synchronized state

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| clock-domain mapping tolerance | `deadline` | True | None | session time-authority policy |
| bounded clock read | `timeout` | True | None | session time-authority policy |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| elapsed validity interval | `expired` |
| outcome unknown for a clock read | `failed` |
| unmapped or out-of-tolerance clock domain before emission | `rejected` |

**Doxygen obligation.**

- Group: `xcom_stim`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-STIM-006`

**Component refs:** `XCOM-CMP-009`

**Contract refs:** `XCOM-XLC-006`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-03`, `CHK-06`, `CHK-11`

### XCOM-DU-015 — Validation permit and session lifecycle

**Responsibility.** Exclusive validation permit and bounded session lifecycle guarding arming, consumption, and quota.

| Field | Value |
| --- | --- |
| Family | `STIM` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-STIM` |
| Owning tasks | T025 |
| Maturity | `implemented` |
| Accepted revision | 4b01586b438a8587d231ee8828d896c206c06a96 |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` (established)
- `src/xverse/xcom/src/validation_session.cpp` (established)
- `tests/xcom/validation_session/` (established)

**Ownership / lifetime.**

- Ownership: `session-issued-handle` — Only the handle issued for an armed session may consume its permit or close it.
- Lifetime: `session-scoped` — A permit handle is valid only for its session scope and is consumed exactly once.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — Session transitions and quota consumption share a per-session state machine.
- Shared state: `consumed-permit record`, `quota counters`, `session state machine`
- Synchronization: per-session mutex guarding transitions and quota consumption

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| armed sessions | `capacity` | True | None | validation permit |
| permit validity interval | `deadline` | True | None | validation permit |
| actions per session | `quota` | True | None | validation permit |
| requests per interval | `rate` | True | None | validation permit |

Overflow policies: `reject`, `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| permit validity interval elapsed | `expired` |
| outcome unknown after an injection attempt | `failed` |
| missing, consumed, or mismatched permit | `rejected` |
| quota exceeded | `rejected` |

**Doxygen obligation.**

- Group: `xcom_stim`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-STIM-001`, `XCOM-SW-STIM-002`

**Component refs:** `XCOM-CMP-009`

**Contract refs:** `XCOM-XLC-006`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-04`, `CHK-05`, `CHK-06`

### XCOM-DU-016 — Durable stimulation intent and outcome journal

**Responsibility.** Durable stimulation intent and outcome journal that records intent before emission and reports evidence-incomplete on a lost outcome.

| Field | Value |
| --- | --- |
| Family | `STIM` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-STIM` |
| Owning tasks | T026 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp` (established)
- `src/xverse/xcom/src/stimulation_journal.cpp` (established)
- `tests/xcom/stimulation_journal/` (established)

**Ownership / lifetime.**

- Ownership: `platform-owns-shared` — The platform owns the journal handle and index for the session lifetime.
- Lifetime: `session-scoped` — Journal records are valid for the session scope and retained up to the declared bound.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — The append-only journal handle and index are shared by the single writer.
- Shared state: `append-only journal file handle`, `journal index`
- Synchronization: per-journal mutex with a single writer; the intent is persisted before emission

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| journal record size | `bytes` | True | None | journal configuration |
| retained journal records | `capacity` | True | None | journal configuration |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| intent recorded without an outcome | `evidence-incomplete` |
| journal write or fsync failure or disk full | `evidence-incomplete` |
| outcome unknown after a journal write | `evidence-incomplete` |
| journal configuration rejected | `rejected` |

**Doxygen obligation.**

- Group: `xcom_stim`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-STIM-007`

**Component refs:** `XCOM-CMP-009`

**Contract refs:** `XCOM-XLC-006`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-07`, `NEG-27`

### XCOM-DU-017 — Fail-closed pre-emission guard

**Responsibility.** Fail-closed pre-emission guard that rejects every schema, target, direction, action, time, quota, loop, or ownership mismatch with zero emission.

| Field | Value |
| --- | --- |
| Family | `STIM` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-STIM` |
| Owning tasks | T027 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` (established)
- `src/xverse/xcom/src/stimulation_guard.cpp` (established)
- `tests/xcom/stimulation_guard/` (established)

**Ownership / lifetime.**

- Ownership: `session-issued-handle` — Only the session-issued handle may evaluate and reject an action; a rejection mutates no owned state.
- Lifetime: `session-scoped` — The guard is valid for the session scope and retains only the declared action tally.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — The action tally and loop-detection window are shared per session.
- Shared state: `loop-detection window`, `per-session action tally`
- Synchronization: per-session mutex; a rejection performs no state mutation

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| loop-detection window | `depth` | True | None | validation permit |
| actions per session | `quota` | True | None | validation permit |
| actions per interval | `rate` | True | None | validation permit |

Overflow policies: `reject`, `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| outcome unknown after a guard evaluation | `failed` |
| schema, target, direction, action, time, quota, loop, or ownership mismatch | `rejected` |

**Doxygen obligation.**

- Group: `xcom_stim`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-STIM-004`, `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`

**Component refs:** `XCOM-CMP-009`

**Contract refs:** `XCOM-XLC-006`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-07`, `CHK-11`

### XCOM-DU-018 — Guarded injection and exclusive service-emulation lease

**Responsibility.** Guarded injection and exclusive service-emulation lease with synthetic provenance, release, or quarantine on expiry, revocation, or disconnect.

| Field | Value |
| --- | --- |
| Family | `STIM` |
| Kind | `boundary` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-STIM` |
| Owning tasks | T028 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` (established)
- `src/xverse/xcom/src/stimulation_actions.cpp` (established)
- `tests/xcom/stimulation_actions/` (established)

**Ownership / lifetime.**

- Ownership: `session-issued-handle` — Only the session-issued handle may acquire or release the exclusive lease for an endpoint generation.
- Lifetime: `endpoint-generation` — A lease is valid only for the endpoint generation under which it was acquired.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — The exclusive lease table and drain state are shared by concurrent session actions.
- Shared state: `drain state`, `exclusive lease table keyed by endpoint and generation`
- Synchronization: atomic lease acquisition under a per-session mutex; release or quarantine on expiry, revocation, or disconnect

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| active leases | `capacity` | True | None | activation plan |
| drain deadline | `deadline` | True | None | validation permit |
| drain queue depth | `depth` | True | None | validation permit |

Overflow policies: `fail-closed`, `reject`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| lease revoked, expired, or disconnected | `cancelled` |
| emission without a recorded outcome | `evidence-incomplete` |
| outcome unknown after emission | `evidence-incomplete` |
| lease validity elapsed | `expired` |
| lease conflict or unauthorized action | `rejected` |

**Doxygen obligation.**

- Group: `xcom_stim`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 6 / public 6

**Requirement links:** `XCOM-SW-STIM-001`, `XCOM-SW-STIM-003`, `XCOM-SW-STIM-008`, `XCOM-SW-STIM-009`

**Component refs:** `XCOM-CMP-009`

**Contract refs:** `XCOM-XLC-006`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0019`, `ADR-0020`

**Planned evidence:** `CHK-05`, `CHK-07`

### XCOM-DU-019 — Tool gateway Protocol Buffers API

**Responsibility.** Versioned Protocol Buffers tool API with additive evolution and explicit rejection of an unknown field or service version.

| Field | Value |
| --- | --- |
| Family | `GW` |
| Kind | `edge` |
| Language | `proto` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T030 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `proto/xverse/xcom/v1/tool_gateway.proto` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The service definition is a versioned artifact owned by its authoring task.
- Lifetime: `static-immutable` — The service definition is immutable once published and evolved additively.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `read-only-static` — The immutable service definition and generated types are read concurrently.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| message and stream size | `bytes` | True | None | tool API schema |
| concurrent streams | `capacity` | True | None | tool API schema |

Overflow policies: `fail-closed`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| outcome unknown for a gateway call | `failed` |
| unknown field or unsupported service version | `rejected` |

**Doxygen obligation.**

- Required: false — Protocol Buffers definition; the generated C++ documentation policy is gap DOX-GAP-02 owned by T011.

**Requirement links:** `XCOM-SW-GW-001`

**Component refs:** `XCOM-CMP-010`

**Contract refs:** `XCOM-XLC-002`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-09`, `NEG-28`

### XCOM-DU-020 — Local-IPC-only gateway session

**Responsibility.** Local-IPC-only gateway session with per-request deadlines, flow control, and no TCP listener.

| Field | Value |
| --- | --- |
| Family | `GW` |
| Kind | `edge` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T031 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` (established)
- `src/xverse/xcom/src/tool_gateway.cpp` (established)
- `tests/xcom/tool_gateway/` (established)

**Ownership / lifetime.**

- Ownership: `gateway-issued-handle` — The gateway issues the only handle that owns an accepted peer session and its flow-control window.
- Lifetime: `session-scoped` — A gateway session handle is valid for its session scope and is closed on disconnect or expiry.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `internally-synchronized` — Accepted peer sessions and their per-session flow-control windows are shared.
- Shared state: `accepted local IPC peer sessions`, `per-session deadlines and flow-control windows`
- Synchronization: per-session mutex plus a bounded request queue; local IPC only, no TCP listener

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| message size | `bytes` | True | None | gateway configuration |
| concurrent sessions and streams | `capacity` | True | None | gateway configuration |
| per-request deadline | `deadline` | True | None | gateway configuration |
| requests per interval | `rate` | True | None | gateway configuration |
| session idle timeout | `timeout` | True | None | gateway configuration |

Overflow policies: `fail-closed`, `reject`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| disconnected after an intent | `evidence-incomplete` |
| expired session | `expired` |
| outcome unknown after a request | `failed` |
| transport or peer failure | `failed` |
| unauthorized session | `rejected` |

**Doxygen obligation.**

- Group: `xcom_gw`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 7 / public 7

**Requirement links:** `XCOM-SW-GW-001`, `XCOM-SW-GW-002`

**Component refs:** `XCOM-CMP-010`

**Contract refs:** `XCOM-XLC-002`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-05`, `CHK-06`, `CHK-11`

### XCOM-DU-021 — Separate-process synthetic tool client

**Responsibility.** Separate-process synthetic tool client that exercises the gateway contract without an external or legacy peer.

| Field | Value |
| --- | --- |
| Family | `GW` |
| Kind | `test-fixture` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-CORE` |
| Owning tasks | T032, T033 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `src/xverse/xcom/fixtures/synthetic_tool.cpp` (established)
- `tests/xcom/tool_gateway/` (established)

**Ownership / lifetime.**

- Ownership: `gateway-issued-handle` — The client holds the gateway-issued session handle and owns its in-flight request table.
- Lifetime: `process-scoped` — The synthetic client is valid for the process lifetime of its own test process.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `externally-synchronized` — The client issues one request or stream at a time per session.
- Shared state: `in-flight request table`
- Synchronization: caller issues one request or stream at a time per client session

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| message size | `bytes` | True | None | tool client configuration |
| request deadline | `deadline` | True | None | tool client configuration |
| transport timeout | `timeout` | True | None | tool client configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| disconnected after an intent | `evidence-incomplete` |
| session expired | `expired` |
| transport or peer failure | `failed` |

**Doxygen obligation.**

- Group: `xcom_gw`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 5 / public 5

**Requirement links:** `XCOM-SW-GW-002`, `XCOM-SW-GW-003`

**Component refs:** `XCOM-CMP-011`

**Contract refs:** `XCOM-XLC-002`

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-05`, `CHK-09`

### XCOM-DU-022 — Doxygen documentation and warning gate

**Responsibility.** Doxygen documentation, alias support, and the warning gate over the changed units.

| Field | Value |
| --- | --- |
| Family | `INTG` |
| Kind | `documentation` |
| Language | `python` |
| Scope | `first-proof` |
| Owning slice | `T-INTG` |
| Owning tasks | T037 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Admitted Doxygen configuration and check_doxygen.py exist, but the strict C++ configuration and warning-free generation are allocated to T011/T037; coverage stays partial. |

**Artifact paths:**

- `Doxyfile` (established)
- `docs/xcom/` (established)
- `scripts/check_doxygen.py` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The documentation configuration and generated output are owned by the documentation task.
- Lifetime: `document-scoped` — A generated documentation set is valid for its exact source revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline documentation tooling: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| missing docstring or Doxygen warning | `failed` |
| unavailable documentation tool | `failed` |

**Doxygen obligation.**

- Required: false — Python documentation tooling; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-INTG-002`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-08`, `NEG-29`

### XCOM-DU-023 — Requirements traceability validation

**Responsibility.** Offline requirements and traceability validation across the register, architecture, design, and tests.

| Field | Value |
| --- | --- |
| Family | `INTG` |
| Kind | `documentation` |
| Language | `python` |
| Scope | `first-proof` |
| Owning slice | `T-INTG` |
| Owning tasks | T038 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Requirements traceability validation exists, but full Spec Kit and REF-002 closure is allocated to T038; coverage stays partial. |

**Artifact paths:**

- `docs/engineering/xcom/t008/` (established)
- `scripts/validate_xcom_requirements_traceability.py` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The traceability tooling and its evidence are owned by the validation task.
- Lifetime: `document-scoped` — A traceability result is valid for its exact candidate revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline traceability tooling: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| dangling traceability link | `failed` |
| unavailable requirement register | `failed` |

**Doxygen obligation.**

- Required: false — Python offline validator; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-INTG-002`, `XCOM-SW-ENB-001`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-10`, `NEG-39`

### XCOM-DU-024 — Public-safe evidence bundle and manifests

**Responsibility.** Public-safe evidence bundle and per-task manifests bound to the exact candidate revision.

| Field | Value |
| --- | --- |
| Family | `INTG` |
| Kind | `evidence` |
| Language | `markdown` |
| Scope | `first-proof` |
| Owning slice | `T-INTG` |
| Owning tasks | T035, T040 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | The queue manifest directory exists, but the full evidence bundle is allocated to T035/T040; coverage stays partial. |

**Artifact paths:**

- `docs/engineering/xcom/t035/` (established)
- `docs/engineering/xcom/t036/` (planned)
- `docs/engineering/xcom/t038/` (planned)
- `docs/engineering/xcom/t040/` (planned)
- `reports/xcom-queue/` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The evidence bundle is owned by the integration task that produced it.
- Lifetime: `document-scoped` — An evidence bundle is valid for its exact candidate revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline evidence assembly: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| absent required evidence | `failed` |
| prohibited content in evidence | `failed` |

**Doxygen obligation.**

- Required: false — Markdown evidence documents; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-INTG-001`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-14`, `NEG-41`

### XCOM-DU-025 — Controlled disabled-tap benchmark evidence

**Responsibility.** Controlled disabled-tap benchmark evidence recording environment identity and measurement uncertainty.

| Field | Value |
| --- | --- |
| Family | `INTG` |
| Kind | `evidence` |
| Language | `cpp` |
| Scope | `first-proof` |
| Owning slice | `T-INTG` |
| Owning tasks | T036 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | The disabled-tap benchmark harness exists, but the controlled benchmark run and its uncertainty record are allocated to T036; coverage stays partial. |

**Artifact paths:**

- `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` (established)
- `tests/xcom/performance/` (planned)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The benchmark evidence is owned by the integration task that produced it.
- Lifetime: `document-scoped` — A benchmark result is valid for the environment identity it records.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline benchmark harness: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| benchmark input size | `bytes` | True | None | offline tooling configuration |
| benchmark run deadline | `deadline` | True | None | offline tooling configuration |
| benchmark timeout | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| benchmark harness failure | `failed` |
| environment identity or uncertainty missing | `failed` |

**Doxygen obligation.**

- Group: `xcom_intg`
- File block: `file`, `brief`, `ingroup`
- Public tags: `brief`, `ownership`, `lifetime`, `thread_safety`, `failure`
- Elements: documented 4 / public 4

**Requirement links:** `XCOM-SW-INTG-003`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-08`, `NEG-30`

### XCOM-DU-026 — Requirement register and REF-002 model

**Responsibility.** Requirement register and REF-002 disposition model that every unit design resolves against.

| Field | Value |
| --- | --- |
| Family | `ENB` |
| Kind | `documentation` |
| Language | `json` |
| Scope | `first-proof` |
| Owning slice | `T-ENABLER` |
| Owning tasks | T008 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | The T008 register is reviewed but not user-accepted; coverage stays partial per ADR-0020. |

**Artifact paths:**

- `docs/engineering/xcom/t008/requirements-register.json` (established)
- `docs/engineering/xcom/t008/traceability-matrix.json` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The register is a repository-owned work product of the enabler task.
- Lifetime: `document-scoped` — A register revision is valid for its exact candidate revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline register validation: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| REF-002 promotion defect | `failed` |
| register schema defect | `failed` |

**Doxygen obligation.**

- Required: false — JSON work product; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-10`, `NEG-32`

### XCOM-DU-027 — Architecture and contract model

**Responsibility.** Component, boundary, contract, diagram, and invariant model that the unit design resolves against.

| Field | Value |
| --- | --- |
| Family | `ENB` |
| Kind | `documentation` |
| Language | `json` |
| Scope | `first-proof` |
| Owning slice | `T-ENABLER` |
| Owning tasks | T009 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | The T009 architecture model is reviewed but not user-accepted; coverage stays partial per ADR-0020. |

**Artifact paths:**

- `docs/engineering/xcom/t009/architecture-model.json` (established)
- `docs/engineering/xcom/t009/architecture-model.md` (established)
- `scripts/validate_xcom_architecture_contracts.py` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The architecture model is a repository-owned work product of the enabler task.
- Lifetime: `document-scoped` — An architecture-model revision is valid for its exact candidate revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline architecture validation: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| architecture model schema defect | `failed` |
| unresolved component or contract reference | `failed` |

**Doxygen obligation.**

- Required: false — JSON work product; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-ENB-001`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-09`, `NEG-38`

### XCOM-DU-028 — Unit-design model and Doxygen plan

**Responsibility.** Canonical unit-design model, its deterministic projection, and the Doxygen plan for every public interface.

| Field | Value |
| --- | --- |
| Family | `ENB` |
| Kind | `documentation` |
| Language | `json` |
| Scope | `first-proof` |
| Owning slice | `T-ENABLER` |
| Owning tasks | T010 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `docs/engineering/xcom/t010/design-units.md` (established)
- `docs/engineering/xcom/t010/unit-design.json` (established)
- `scripts/validate_xcom_unit_design.py` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The unit-design model is a repository-owned work product of this task.
- Lifetime: `document-scoped` — A unit-design revision is valid for its exact candidate revision.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline unit-design validation: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| coverage or cross-resolution defect | `failed` |
| unit-design schema defect | `rejected` |

**Doxygen obligation.**

- Required: false — JSON work product produced by this unit; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-ENB-001`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-01`, `CHK-16`, `NEG-33`

### XCOM-DU-029 — Dependency admission and build lock

**Responsibility.** Compiler, dependency, license, hash, and generated-code provenance admission with an offline preflight.

| Field | Value |
| --- | --- |
| Family | `ENB` |
| Kind | `documentation` |
| Language | `markdown` |
| Scope | `first-proof` |
| Owning slice | `T-ENABLER` |
| Owning tasks | T011 |
| Maturity | `partial` |
| Accepted revision | None |
| Reconciliation | Dependency admission documents and the offline preflight exist, but T011 is not user-accepted; coverage stays partial. |

**Artifact paths:**

- `cmake/XComOfflineDependencies.cmake` (established)
- `docs/engineering/xcom/build-environment.md` (established)
- `docs/engineering/xcom/dependency-lock.md` (established)
- `scripts/xcom_dependency_preflight.py` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The admission records are repository-owned work products of the enabler task.
- Lifetime: `document-scoped` — An admission record is valid for its exact candidate revision and dependency set.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline dependency preflight: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| unadmitted dependency version, hash, or license | `failed` |
| unavailable dependency metadata | `failed` |

**Doxygen obligation.**

- Required: false — Markdown admission documents; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-ENB-004`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-12`, `NEG-35`

### XCOM-DU-030 — Independent review and acceptance record

**Responsibility.** Independent read-only review record and the explicit user-acceptance record kept separate from implementation.

| Field | Value |
| --- | --- |
| Family | `ENB` |
| Kind | `documentation` |
| Language | `markdown` |
| Scope | `first-proof` |
| Owning slice | `T-REVIEW` |
| Owning tasks | T039, T041 |
| Maturity | `allocated` |
| Accepted revision | None |
| Reconciliation |  |

**Artifact paths:**

- `docs/engineering/xcom/t039/` (planned)
- `docs/reviews/` (established)

**Ownership / lifetime.**

- Ownership: `task-owns-artifact` — The review and acceptance records are repository-owned work products of the review task.
- Lifetime: `document-scoped` — A review record is valid for the exact candidate revision it inspected.
- Exposes view: False; view lifetime: None

**Thread-safety.**

- Model: `offline-single-threaded` — Offline review record: one process, one thread.
- Shared state: none
- Synchronization: None

**Bounds:**

| Resource | Kind | Configured | Value | Declared in |
| --- | --- | --- | --- | --- |
| artifact size | `bytes` | True | None | offline tooling configuration |
| worker threads | `thread-count` | True | 1 | offline tooling configuration |
| validation runtime | `timeout` | True | None | offline tooling configuration |

Overflow policies: `n/a`

**Failure semantics:**

| Condition | Outcome |
| --- | --- |
| absent review record | `failed` |
| unresolved blocker or major review finding | `failed` |

**Doxygen obligation.**

- Required: false — Markdown review records; not a hand-written C/C++ interface.

**Requirement links:** `XCOM-SW-ENB-003`

**Component refs:** none

**Contract refs:** none

**Governing ADRs:** `ADR-0016`, `ADR-0018`, `ADR-0020`

**Planned evidence:** `CHK-18`, `NEG-46`

## Invariants

| Id | Kind | Statement | Enforcing check |
| --- | --- | --- | --- |
| `XCOM-UDI-01` | `ownership` | Every unit has exactly one owning slice and a task set consistent with the T007 register. | CHK-03, CHK-11 |
| `XCOM-UDI-02` | `ownership` | Only an exact issued handle mutates, closes, or replaces an active resource. | CHK-04 |
| `XCOM-UDI-03` | `lifetime` | Immutable values and static artifacts are shared without synchronization. | CHK-05 |
| `XCOM-UDI-04` | `thread-safety` | Every shared mutable state is protected by a declared synchronization mechanism or boundary. | CHK-05 |
| `XCOM-UDI-05` | `bounds` | Every queue, quota, depth, rate, byte, and retry bound is finite and declared with its source. | CHK-06 |
| `XCOM-UDI-06` | `bounds` | No unit silently retries or silently upgrades delivery guarantees. | CHK-06 |
| `XCOM-UDI-07` | `failure` | An unknown or incomplete outcome is never reported as success. | CHK-07 |
| `XCOM-UDI-08` | `doxygen` | Every public C/C++ interface documents its ownership, lifetime, thread-safety, and failure contract. | CHK-08 |
| `XCOM-UDI-09` | `lifetime` | Payload views have an explicit bounded lifetime and metadata-only is the observation default. | CHK-04, CHK-05 |
| `XCOM-UDI-10` | `failure` | Synthetic provenance survives routing, observation, and restart classification. | CHK-07 |
| `XCOM-UDI-11` | `dependency` | Dependencies flow one-way blueprints to profiles to XDL/platform to runtime; subsystem naming is preserved. | CHK-11 |
| `XCOM-UDI-12` | `neutrality` | No core unit embeds a domain-specific primitive (ECU, CAN, SOME/IP, Zenoh, or a product name). | CHK-11 |
| `XCOM-UDI-13` | `safety` | The first proof executes no legacy workload, contacts no external peer, and exposes no TCP listener except the host-protected local tool gateway. | CHK-11 |
| `XCOM-UDI-14` | `documentation` | Every unit declares explicit, classified failure semantics and planned evidence. | CHK-07, CHK-10 |
