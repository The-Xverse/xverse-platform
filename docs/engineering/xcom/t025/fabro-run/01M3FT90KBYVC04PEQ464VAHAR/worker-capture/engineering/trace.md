# T025 Trace — Reciprocal Requirement, Design, Code, Test, and Measure Links

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | validation |
| Revision | 1 |
| Classification | SANITIZED |
| Requirement authority | `engineering/requirements.md` (rev 1); `engineering/requirements/*.json` |
| Design authority | `engineering/design.md` (rev 1); `engineering/architecture/components/*.json` |
| Unit authority | `engineering/unit-specifications/*.json` |
| Verification plan | `engineering/verification-plan.md` (rev 1, reviewed) |
| Machine-readable graph | `engineering/trace/links.json` (schema_version 1, project_id `xcom-t025-sanitized`) |
| Measure records | `engineering/verification/measures/*.json` |
| Validation scenarios | `engineering/validation/scenarios/*.json` |
| Source under test | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` (SHA-256 `a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20`) and `src/xverse/xcom/src/validation_session.cpp` (SHA-256 `c3a62ab4c807b5df263ab8412d5c31201a84eebe70ae41e0aa93fb0928eec08f`) |

### 1.1 Authority statement

This is an internal, source-free worker trace candidate. It does **not** establish accepted X-COM
delivery, does not claim predecessor regression, source compatibility, repository integration,
protected verification, or production readiness. Code targets below are pinned to the exact
SHA-256 of the current candidate file, so any later source edit invalidates the link by
construction. Internal worker evidence is kept distinct from protected verification.

### 1.2 Repair provenance of the current bytes

This stage resumes failed run `01M3F969J5X7JHNK5C3JC9B4NP` from its hash-bound implementation-repair
checkpoint (`engineering/resume-provenance.json`, `kind: terminal-inspection-resume`). The failed
implementation inspection carried exactly two findings, both repaired before this validation stage
(`engineering/implementation-repair.md`):

- **F-IMP-01 (minor, IMP-01)** — `SessionManager::consume` reserved a live-session slot before the
  registry's check-then-insert, so a replay on a full table reported `CapacityExhausted` instead of
  `SessionAlreadyConsumed`/`PermitAlreadyConsumed`. Repaired so the read-only replay probes precede
  capacity, and the atomic `try_consume` runs only after a slot is available.
- **F-IMP-02 (minor, IMP-12)** — `precedence_rank(Result)` and `compare(Result, Result)` were tagged
  `@unitspec{T025-U-TYPES}` while `T025-U-DIAGNOSTIC.json` owns them. Repaired by re-tagging both to
  `@unitspec{T025-U-DIAGNOSTIC}`; the reviewed unit specification was not modified.

The independently reviewed requirements and design and the validated unit specifications are
preserved byte-for-byte from the checkpoint; the repaired implementation was re-inspected by a fresh
independent implementation inspection that recorded `findings: []`, `conclusion: pass` against the
current header/source/test hashes. The reviewed/validated provenance is unchanged.

## 2. Link vocabulary and direction (reciprocal)

`engineering/trace/links.json` is the single machine-readable graph; every table in this
document is a projection of it. Each link is `{id, relation, source, source_revision, target,
target_revision}`. Relations and their legal direction:

| Relation | Source type | Target type | Reciprocal meaning |
| --- | --- | --- | --- |
| `refines` | software requirement | stakeholder requirement | the software requirement narrows the stakeholder intent |
| `allocated_to` | software requirement | architecture component | the component is responsible for the requirement |
| `decomposes_to` | architecture component | unit specification | the unit is part of the component |
| `implemented_by` | requirement / component / unit | code `path::symbol` | the code element realises the source |
| `verified_by` | requirement / component / unit | measure (kind unit/integration/validation) | the measure exercises the source |
| `analyzed_by` | unit specification | measure (kind `static_analysis`) | a static check constrains the unit |
| `validates` | validation scenario | requirement | the intended-use scenario demonstrates the requirement |

Reciprocity is enforced: every accepted software requirement has `allocated_to`, `implemented_by`, and
`verified_by`; every component reaches its units through `decomposes_to`; every unit has
`implemented_by`, `verified_by`, and `analyzed_by`; every validation scenario has at least one
`validates` link. The deterministic trace gate re-checks all of this and the current graph contains
**148 links over 68 canonical artifacts** (all revisions current).

## 3. Stakeholder to software requirement coverage

| Stakeholder requirement | Title | Refining software requirements | Validation scenarios |
| --- | --- | --- | --- |
| `T025-STK-001` | Explicit time authority governs all time-dependent decisions | `T025-SR-001`, `T025-SR-002`, `T025-SR-003`, `T025-SR-004`, `T025-SR-005` | `T025-VS-002` |
| `T025-STK-002` | Local validation permit is exactly-once and exactly-bound | `T025-SR-007`, `T025-SR-008`, `T025-SR-009`, `T025-SR-010` | `T025-VS-003`, `T025-VS-006` |
| `T025-STK-003` | Bounded session lifecycle with controller-bound handles | `T025-SR-011`, `T025-SR-012`, `T025-SR-013` | `T025-VS-001`, `T025-VS-004` |
| `T025-STK-004` | Rejection is non-mutating; diagnostics are stable and payload-free | `T025-SR-015`, `T025-SR-016` | `T025-VS-007` |
| `T025-STK-005` | Zero normal-route emissions | `T025-SR-018` | `T025-VS-001`, `T025-VS-005` |
| `T025-STK-006` | Bounded, concurrency-safe resources | `T025-SR-006`, `T025-SR-014`, `T025-SR-017` | `T025-VS-006`, `T025-VS-008` |

## 4. Software requirement to design, code, test, and measure

Code targets are `path::symbol` with the current file SHA-256 as `target_revision`. Test evidence is
the exact discovered CTest test names inside the named measures (see
`engineering/verification/measures/*.json` for the full case lists and `engineering/validation.md`
for the observed run).

| Requirement | Refines | Allocated component(s) | Code symbol(s) | Verifying measure(s) |
| --- | --- | --- | --- | --- |
| `T025-SR-001` Declare and identify clock domains | `T025-STK-001` | `validation_time_authority` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TimeAuthority` | `T025-M-U-TIME` |
| `T025-SR-002` Bounded current-time acquisition | `T025-STK-001` | `validation_time_authority` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TimeAuthority`, `src/xverse/xcom/src/validation_session.cpp::TimeAuthority` | `T025-M-U-TIME` |
| `T025-SR-003` Declared source-to-destination mapping with tolerance | `T025-STK-001` | `validation_time_authority` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TimeAuthority` | `T025-M-U-TIME`, `T025-M-I-CROSSDOMAIN` |
| `T025-SR-004` Regression and overflow are distinct failures | `T025-STK-001` | `validation_time_authority` | `src/xverse/xcom/src/validation_session.cpp::TimeAuthority` | `T025-M-U-TIME` |
| `T025-SR-005` Validity and lifecycle decisions use the authority only | `T025-STK-001` | `validation_time_authority`, `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager`, `src/xverse/xcom/src/validation_session.cpp::SessionManager` | `T025-M-U-TIME`, `T025-M-I-CROSSDOMAIN` |
| `T025-SR-006` Authority lifetime and synchronisation contract | `T025-STK-006` | `validation_time_authority` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TimeAuthority` | `T025-M-U-TIME`, `T025-M-SA-COMPILE` |
| `T025-SR-007` Immutable permit binds the exact session envelope | `T025-STK-002` | `validation_permit`, `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::Permit`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitBuilder` | `T025-M-U-PERMIT` |
| `T025-SR-008` Undefined actions and composite values are rejected | `T025-STK-002` | `validation_permit` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitBuilder` | `T025-M-U-PERMIT`, `T025-M-U-TRANSITION-REJECT` |
| `T025-SR-009` Exactly-once consumption with explicit replay scope | `T025-STK-002` | `validation_permit_registry` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitRegistry`, `src/xverse/xcom/src/validation_session.cpp::PermitRegistry` | `T025-M-U-REGISTRY`, `T025-M-U-TRANSITION-REJECT` |
| `T025-SR-010` Quota and capacity exhaustion is explicit | `T025-STK-002` | `validation_permit_registry`, `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitRegistry`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::ManagerConfig` | `T025-M-U-REGISTRY`, `T025-M-U-MANAGER`, `T025-M-I-QUOTA` |
| `T025-SR-011` Handles bind controller identity and generation | `T025-STK-003` | `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionHandle`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager` | `T025-M-U-MANAGER`, `T025-M-I-GENERATION` |
| `T025-SR-012` All lifecycle and terminal states are defined and reachable | `T025-STK-003` | `validation_session` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::ValidationSession`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TransitionOutcome` | `T025-M-U-SESSION` |
| `T025-SR-013` Validation precedes mutation; safe idempotency only | `T025-STK-003` | `validation_session` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::ValidationSession` | `T025-M-U-SESSION`, `T025-M-U-MANAGER` |
| `T025-SR-014` Bounded session capacity and lifecycle bookkeeping | `T025-STK-006` | `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::ManagerConfig` | `T025-M-U-MANAGER` |
| `T025-SR-015` Rejection leaves state unchanged | `T025-STK-004` | `validation_session`, `validation_session_manager` | `src/xverse/xcom/src/validation_session.cpp::SessionManager` | `T025-M-U-MANAGER`, `T025-M-U-TRANSITION-REJECT` |
| `T025-SR-016` Ordered, payload-free diagnostics | `T025-STK-004` | `validation_diagnostic` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::Diagnostic` | `T025-M-U-DIAGNOSTIC` |
| `T025-SR-017` Deterministic concurrency for consumption and mutation | `T025-STK-006` | `validation_permit_registry`, `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitRegistry`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager` | `T025-M-U-MANAGER`, `T025-M-I-CONTROLLER` |
| `T025-SR-018` Zero normal-route emissions | `T025-STK-005` | `validation_session_manager` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::emission_count`, `src/xverse/xcom/src/validation_session.cpp::emission_count` | `T025-M-V-ZEM`, `T025-M-SA-SYMBOL` |

## 5. Component to unit decomposition and unit evidence

| Component | Unit specification | Code symbol(s) | Unit measure | Static-analysis measure(s) |
| --- | --- | --- | --- | --- |
| `validation_diagnostic` | `T025-U-DIAGNOSTIC` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::Diagnostic` | `T025-M-U-DIAGNOSTIC` | `T025-M-SA-COMPILE`, `T025-M-SA-CLANGTIDY` |
| `validation_permit` | `T025-U-PERMIT` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::Permit`, `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitBuilder` | `T025-M-U-PERMIT` | `T025-M-SA-COMPILE`, `T025-M-SA-CLANGTIDY` |
| `validation_permit_registry` | `T025-U-REGISTRY` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::PermitRegistry` | `T025-M-U-REGISTRY` | `T025-M-SA-COMPILE`, `T025-M-SA-CLANGTIDY` |
| `validation_session` | `T025-U-SESSION` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::ValidationSession` | `T025-M-U-SESSION` | `T025-M-SA-COMPILE`, `T025-M-SA-CLANGTIDY` |
| `validation_session_manager` | `T025-U-MANAGER` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::SessionManager`, `src/xverse/xcom/src/validation_session.cpp::SessionManager` | `T025-M-U-MANAGER`, `T025-M-U-TRANSITION-REJECT` | `T025-M-SA-COMPILE`, `T025-M-SA-SYMBOL` |
| `validation_time_authority` | `T025-U-TIME` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp::TimeAuthority`, `src/xverse/xcom/src/validation_session.cpp::TimeAuthority` | `T025-M-U-TIME` | `T025-M-SA-COMPILE`, `T025-M-SA-RAWCLOCK`, `T025-M-SA-TSAN` |
| `validation_types` | `T025-U-TYPES` | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` | `T025-M-U-TYPES` | `T025-M-SA-COMPILE`, `T025-M-SA-CLANGTIDY`, `T025-M-SA-DOXYGEN` |

The reviewed unit specifications declare **119** unit cases in total; the implementation adds **10**
executable repair-regression tests (7 transition-path rejection tests and 3 replay/transactional
tests), so the CTest `unit` label discovers **129** tests. Per-measure case counts are: TYPES 6,
DIAGNOSTIC 6, TIME 20, PERMIT 9, REGISTRY 6, SESSION 18, MANAGER 54, TRANSITION-REJECT 10; plus
integration 4 and validation 3. No reviewed unit case is absent from the executable suite.

## 6. Validation scenarios to stakeholder requirements

| Scenario | Intended use | Validates | Nominal case IDs |
| --- | --- | --- | --- |
| `T025-VS-001` | Nominal, intended-use validation session lifecycle. | `T025-STK-003`, `T025-STK-005` | `NOM-01`, `NOM-02`, `LIF-01`, `LIF-02`, `LIF-03`, `LIF-04`, `ZEM-02` |
| `T025-VS-002` | Cross-domain permit validity must use the explicit time authority. | `T025-STK-001` | `NOM-03`, `NOM-04`, `CLK-06`, `CLK-07`, `CLK-08` |
| `T025-VS-003` | Exactly-once, controller-scoped permit consumption and replay rejection. | `T025-STK-002` | `RP-01`, `RP-02`, `RP-03`, `RP-04`, `RP-05` |
| `T025-VS-004` | Controller-bound handle ownership and recreated-controller isolation. | `T025-STK-003` | `HND-01`, `HND-02`, `HND-03`, `HND-04`, `HND-05`, `HND-06`, `HND-07` |
| `T025-VS-005` | Zero normal-route emissions in the intended-use path. | `T025-STK-005` | `ZEM-01`, `ZEM-02`, `ZEM-03` |
| `T025-VS-006` | Finite quota and capacity boundaries with explicit exhaustion. | `T025-STK-002`, `T025-STK-006` | `QUO-01`, `QUO-02`, `QUO-03`, `QUO-04`, `QUO-05`, `QUO-06` |
| `T025-VS-007` | Rejection is non-mutating and diagnostics are stable and payload-free. | `T025-STK-004` | `NOMUT-01`..`NOMUT-07`, `DIA-01`, `DIA-05` |
| `T025-VS-008` | Deterministic concurrency for consumption and lifecycle mutation. | `T025-STK-006` | `CON-01`, `CON-02`, `CON-03`, `CON-04`, `CON-05` |

## 7. REF-002 dispositions (preserved from the interface bridge)

| REF-002 ID | Disposition in this slice | Basis | Trace anchor |
| --- | --- | --- | --- |
| `XVE-SYS-0144` | **partial**; general channel identity/access **deferred** to Security | T025 implements only a bounded local validation permit; general channel identity and access remain Security scope. | `T025-SR-007`, `T025-SR-011`, `T025-STK-003` |
| `XVE-SYS-0147` | **partial** clock-domain interface; hard real-time proof **deferred** to protected verification | Clock domains, mappings, tolerance, regression, and overflow are implemented and unit-measured; hard real-time proof remains deferred. | `T025-SR-001`..`T025-SR-005`, `T025-STK-001` |
| `XVE-SYS-0152` | **partial** permit and session foundations; stimulation **deferred** | Permit and session primitives only; actual stimulation and Maestro triggers are later tasks. | `T025-SR-007`..`T025-SR-014`, `T025-STK-002` |
| `XVE-SYS-0154` | **partial** payload-free diagnostics; durable intent/outcome **deferred** | Ordered payload-free diagnostics are delivered; durable provenance remains deferred. | `T025-SR-016`, `T025-STK-004` |

Conflicting: none identified within the admitted inputs. Needing clarification: none for REF-002
itself; the FR anchor allocation below is the sole item referred to protected review.

## 8. Preserved accepted requirement anchors

The admitted packet requires preservation of `FR-015`–`FR-020` and `FR-033`. Their authoritative
statements live in the restricted predecessor checkout, which is unavailable to the worker, so the IDs
are preserved as **trace anchors only** — never restated, renumbered, or reinterpreted.

| Anchor | Preserved on | Limitation |
| --- | --- | --- |
| `FR-015` | `T025-SR-001`..`T025-SR-005` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-016` | `T025-SR-007`, `T025-SR-008` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-017` | `T025-SR-009`, `T025-SR-010` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-018` | `T025-SR-011`, `T025-SR-012` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-019` | `T025-SR-013`, `T025-SR-015` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-020` | `T025-SR-016`, `T025-SR-018` | anchor-preserved, allocation unverified; predecessor text unavailable |
| `FR-033` | `T025-SR-005`, `T025-SR-017` | anchor-preserved, allocation unverified; predecessor text unavailable |

Exact allocation of these anchors is a protected-review decision: *confirm the authoritative statement
and allocation of FR-015–FR-020 and FR-033, or return the corrected anchor-to-requirement mapping.*

## 9. Protected boundary and unverified links

- Code revisions are the current file SHA-256; the trace gate rejects any stale endpoint.
- All measure records are **internal worker evidence**; they are not protected verification.
- `XVE-SYS-0147` hard real-time proof, `XVE-SYS-0144` channel identity/access, `XVE-SYS-0152`
  stimulation, and `XVE-SYS-0154` durable provenance are recorded as deferred/allocated and must not
  be read as satisfied by this candidate.
- ThreadSanitizer (`STC-TIME-04`, measure `T025-M-SA-TSAN`) and CodeQL are **pending**, not passed;
  predecessor regression and repository integration are protected host steps.
