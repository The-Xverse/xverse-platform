# T024 Architecture — Observation Acceptance Matrix: Structure, Boundaries, and Interfaces

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | plan → architecture |
| Revision | 1 (observation acceptance matrix) |
| Repair revision | 3 — terminal review R-01 governance repair (see §11) |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Repair baseline | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` |
| Affected source paths | `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/integration_tests.cpp` (test fixtures only); no production source and no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-008` observation boundary, `XCOM-CMP-011` synthetic sink and tools, `XCOM-CMP-006` provider composition); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-012` declared observation layer, `XCOM-DU-013` bounded observer queue/counters/synthetic sink); `docs/engineering/xcom/t021/architecture.md` (declared observation layer); `docs/engineering/xcom/t022/architecture.md` (retention and validity layer); `docs/engineering/xcom/t023/architecture.md` (consumer sink layer); `specs/007-xcom-core/contracts/observation.md`; ADR-0019 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T024 is the **consolidated acceptance-matrix layer** of the observation boundary. It adds no production
behaviour: it exercises the accepted observation surface (`ObservationHub`, `ObservationTapSpec`,
`ObservationRecord`, `ObservationSnapshot`, `SyntheticObservationSink`) plus the accepted owned loopback
composition, and it proves the accepted success criteria `SC-003`, `SC-004`, and `SC-005` across the
metadata-only, controlled-payload, ordering, saturation, degraded-validity, safe-detach, and
normalized-record dimensions in one auditable matrix.

T024 closes the handoff recorded by the predecessors: `T021-GAP-04`, `T022-GAP-03`, and `T023-GAP-01` —
"broad metadata-only, controlled-payload, redaction/truncation, ordering, saturation, degraded-validity,
safe-detach matrix" — allocated to T024. `disabled-tap-performance` remains T036.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013 core types → T015 provider composition
   → T019 bounded activation-plan decode → T021 declared observation layer
   → T022 bounded retention + applied validity effect
   → T023 synthetic sink, failure/disconnect isolation, visible counters
   → T024 observation acceptance matrix (this document)
   → { T-XDL consumed, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T024 is a **test-only** slice: the deterministic gate requires at least one changed `tests/` path, satisfied
by the two edited observation fixtures. No production unit, build file, XDL schema, contract, provider,
plan, or later-slice interface changes.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ────────┐
   │  observation-policy: payloadAccess · bounds · validityEffect                            │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ declared vocabulary (no competing language)
   ┌──────────────── accepted observation boundary under test (src/xverse/xcom) ────────────┐
   │  observation.hpp/cpp                                                                    │
   │    declaration  ObservationTapSpec · ObservationFilter · ObservationTapHandle            │
   │    retention    drop_newest · coalesce_latest · lossless_validation                       │
   │    validity     ObservationValidityState + applied declared effect                        │
   │    reporting    ObservationSnapshot counters + validity_state                             │
   │    payload      metadata_only · bounded_prefix · redacted (PayloadViewState/undecoded)    │
   │    consumer     SyntheticObservationSink · SyntheticSinkCounters                           │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ public API consumed read-only by the matrix
   ┌────────────────────────────────────▼──────────────────────────────────────────────────┐
   │  T024 acceptance matrix (this slice, tests/xcom/observation)                              │
   │    core/unit_tests.cpp        7 new matrix cases (hub-level)                              │
   │    integration/integration_tests.cpp  2 new route-level matrix cases                       │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
                                        │ asserts SC-003 / SC-004 / SC-005 and FR-023
                                        ▼
                       T035–T038 evidence consumption · T039 review · T041 acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T24-XB-1` Test vs production | the committed fixture source and its assertions | the accepted `src/xverse/xcom` production units | The matrix observes and asserts only; no production header, source, signature, enumerator, or accepted value is changed. |
| `T24-XB-2` Payload exposure vs metadata | the policy-bounded visible payload bytes and view state | the full source payload and any schema/decoder meaning | Metadata-only/redacted expose zero bytes; bounded-prefix exposes only the declared prefix; schema state stays `undecoded`; no decode success is invented. |
| `T24-XB-3` Tap retention vs declared bound | the fixed per-tap record slots and their counters | an unbounded queue | Every queue stays within its declared capacity (1–16); every drop/coalesce is counted; lossless rejection occurs before provider mutation. |
| `T24-XB-4` Declared validity effect vs realized status | the applied `ObservationValidityEffect` → realized `ObservationValidityState` | an inferred, defaulted, or strengthened status | The realized status is derived only from the declared effect and an actual matching loss; it is never lowered except by acknowledgement or detach/recreation. |
| `T24-XB-5` Observer vs normal route | the observer tap, its retained records, and the consumer sink counters | the normal provider queue, ordering, and delivery outcome | Removing, blocking, disconnecting, or failing a best-effort observer never changes the route item count, FIFO order, or delivery outcome (SC-005). |
| `T24-XB-6` Exact handle vs declared identity | the exact generation-bound `ObservationTapHandle` | declared tap/route/filter identity | Only an exact current handle authenticates; a stale/foreign/closed handle is rejected with the stable outcome and mutates nothing. |
| `T24-XB-7` X-COM vs export/storage | the in-process normalized record and snapshot | Argus, OpenTelemetry, files, dashboards, databases, adapters, the tool gateway | X-COM owns no rendering, storage, query, or presentation; the matrix asserts no such primitive exists (ADR-0019). |
| `T24-XB-8` Repository vs environment | committed test source and work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, process, dynamic-load, or legacy access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No production source change, build-file change, new CTest target/test/label, TCP listener, external network
peer, discovery, package manager/registry, filesystem access, process execution, legacy repository/binary
access, dynamic plugin discovery, domain-specific primitive, new admitted dependency, competing
configuration language, unbounded resource, consumer callback under an X-COM lock, or
export/dashboard/storage/query behavior. No new `ObservationOutcome`, `ObservationOverflowPolicy`,
`ObservationValidityEffect`, `ObservationValidityState`, or `PayloadViewState` value. These inherit the
T007 global prohibitions, the T011 envelope, the T012 build contract, ADR-0019, and the constitution.

## 4. Components

Each component maps to a case group in `unit-specifications.md`. `T24-TS-*` names are local to this
document; the accepted `XCOM-DU-*`/`XCOM-CMP-*` identifiers are the authorized units/components.

### 4.1 New test components (design units `XCOM-DU-012`/`XCOM-DU-013`, components `XCOM-CMP-008`/`XCOM-CMP-011`)

- **`T24-TS-001` Metadata/controlled-payload matrix** (`core/unit_tests.cpp`, new case):
  `metadata_only` family/size completeness and `bounded_prefix` boundary table plus `redacted`, with
  no-decode assertions. Owns the `metadata-only-zero-payload` and `controlled-payload-view` evidence names.
- **`T24-TS-002` Ordering matrix** (`core/unit_tests.cpp`, new case): per-tap FIFO under drop/coalesce,
  multi-tap independence, strictly increasing pulled sequence.
- **`T24-TS-003` Saturation bound matrix** (`core/unit_tests.cpp`, new case): `drop_newest` at minimum and
  maximum capacity, `coalesce_latest` key selection, `lossless_validation` rejection/recovery, and the
  bounded deterministic concurrency sub-check (≤ 4 competing publisher threads over one lossless tap).
- **`T24-TS-004` Degraded-validity matrix** (`core/unit_tests.cpp`, new case): effect × loss-mode table,
  at-least-degraded rule, monotonicity, acknowledgement, discard on detach/recreation.
- **`T24-TS-005` Safe-detach matrix** (`core/unit_tests.cpp`, new case): detach/ownership semantics
  (`tap_busy`, `tap_closed`, foreign, stale, recreation, own-records-only discard).
- **`T24-TS-006` Normalized-record matrix** (`core/unit_tests.cpp`, new case): family × origin × outcome
  record completeness and value ownership (`XCOM-SW-OBS-005`).
- **`T24-TS-007` Record self-description and edge-value matrix** (`core/unit_tests.cpp`, new case):
  boundary values for empty/optional sequence, clock domains, provider outcomes, and payload-view states
  across families.
- **`T24-TS-008` Route ordering/neutrality matrix** (`integration/integration_tests.cpp`, new case): all
  four families over the owned loopback, route FIFO invariance while an observer is blocked/removed/failed.
- **`T24-TS-009` Route saturation/safe-detach matrix** (`integration/integration_tests.cpp`, new case):
  route-level saturation loss counters and degraded validity visible while the route still delivers;
  detached tap's records discarded and stale handle rejected without changing the route.

### 4.2 Preserved components (read-only for T024)

- **`T24-CMP-HUB`** (`XCOM-CMP-008`, `XCOM-DU-013`) — `ObservationHub` attach/reserve/commit/cancel/poll/
  snapshot/acknowledge/detach, the mutex serialization, and the exact-handle authentication: **re-verified
  unchanged**.
- **`T24-CMP-DECLARATION`** (`XCOM-DU-012`, T021) — filter matching, declared tap/route identity, the
  immutable record/counter projection, and the payload view policy: **re-verified unchanged**.
- **`T24-CMP-RETENTION`** (`XCOM-DU-013`, T022) — the accepted `drop_newest`/`coalesce_latest`/
  `lossless_validation` rules and the applied declared validity effect: **re-verified unchanged**.
- **`T24-CMP-SINK`** (`XCOM-CMP-011`, T023) — `SyntheticObservationSink` and `SyntheticSinkCounters`:
  consumed read-only where a consumer view is needed; its behavior is re-verified unchanged.
- **`T24-CMP-ROUTE`** (`XCOM-CMP-006`, T015) — provider composition and the owned loopback provider:
  consumed read-only by the integration cases.

### 4.3 Work-product components

- **`T24-WP`** — the T024 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t024-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-002` X-COM Profile/schema, `XCOM-CMP-003` activation plan, and `XCOM-CMP-004` core value types are
matched or consumed but neither implemented nor altered by T024.

## 5. Data flow (ordered)

1. **Build the hub and policy** — a case constructs an `ObservationTapSpec` through
   `ObservationTapSpec::create` with an explicit payload mode, bound, capacity, overflow policy, and
   validity effect, and attaches it; the hub issues an exact handle (T021, unchanged).
2. **Publish** — a case reserves, commits an explicit provider outcome, and (for the lossless mode) checks
   a pre-provider rejection; the hub retains a normalized record or applies the declared loss rule
   (T022, unchanged).
3. **Pull and assert payload** — the case polls the exact handle and asserts the visible payload
   bytes/view state, schema state, source size, and every normalized identity for the source size and
   payload mode under test (metadata/prefix/redacted table).
4. **Assert ordering** — the case polls a sequence of retained records and asserts FIFO order, coalesce
   replacement position, and independence across two taps on one hub.
5. **Assert saturation** — the case fills the tap to its declared capacity, checks that the queue never
   exceeds the bound, and asserts the exact `accepted`/`dropped`/`coalesced`/`backpressure_rejections`
   counters and the realized validity projection on `ObservationSnapshot`.
6. **Assert validity** — the case reads `ObservationSnapshot::validity_state` and
   `experiment_validity_degraded`, acknowledges, and re-reads; a detach/recreate case re-creates the slot
   and asserts a fresh `valid` interval.
7. **Assert detach** — the case detaches, re-polls, snapshots, re-detaches, detaches while a claim is held,
   and uses a foreign/stale handle, asserting the stable outcome and no mutation of unrelated taps.
8. **Assert route neutrality** — the integration cases submit over the owned loopback, drive an observer
   through connected/blocked/removed/failed states, and assert the route item count, `per_route_fifo`
   receive order, and every provider outcome are unchanged (SC-005).

## 6. Interfaces

T024 consumes the accepted in-process C++20 observation API only (no transport, no external ABI, no new
interface).

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `ObservationTapSpec::create(const ObservationTapSpecInput&)` | validates and owns a bounded payload/retention/validity policy. |
| `ObservationHub::attach/ reserve/ commit/ cancel` | attaches a tap; claims lossless capacity before provider mutation; commits an explicit provider outcome. |
| `ObservationHub::poll(const ObservationTapHandle&)` | returns a value-owned record, `no_record`, or `invalid_tap_handle`. |
| `ObservationHub::snapshot(const ObservationTapHandle&) const` | returns counters, the declared identity/effect, the realized `validity_state`, and the `experiment_validity_degraded` projection for an authenticated handle. |
| `ObservationHub::acknowledge(const ObservationTapHandle&)` | closes a `degraded` interval; an `invalid` status persists. |
| `ObservationHub::detach(const ObservationTapHandle&)` | closes one exact handle, discarding only its records; `tap_busy`/`tap_closed`/`invalid_tap_handle` otherwise. |
| `ObservationRecord` accessors | the complete normalized, value-owned record and its retention-time counter projection. |
| `SyntheticObservationSink` / `SyntheticSinkCounters` | the accepted pull-only consumer and its visible counters (T023), used read-only where a consumer view is asserted. |
| `ProviderComposition` / `LoopbackProvider` | the owned loopback route used by the integration cases (T015), consumed read-only. |

## 7. Concurrency and resource bounds

| Aspect | T024 decision |
| --- | --- |
| Threads | at most four test threads in the `T24-TS-003` concurrency sub-check; no case spawns an unbounded number. |
| Iterations | finite, declared loop counts (e.g. 64 bounded submit/pull iterations); no unbounded loop or retry. |
| Taps per hub | at most `kMaximumObservationTaps` (8); most cases use one or two. |
| Records per tap | at most `kMaximumObservationRecordsPerTap` (16); the bound matrix exercises the minimum (1) and maximum (16). |
| Payload bytes | fixture payloads are synthetic and ≤ 4 bytes; the prefix boundary uses the declared bound, never a real payload. |
| Wall-clock | no case depends on wall-clock timing for its verdict; the `T24-TS-003` concurrency sub-check uses bounded repeated runs and atomic flags. |
| Serialization | publication and pull serialize through the hub mutex; the matrix asserts consistency, not a formal race proof. |
| Callbacks | none; the observation boundary is pull-only and the matrix installs no callback. |
| Production footprint | zero; the candidate changes no production unit, adds no dependency, and allocates only ordinary test-local values. |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Metadata safety | metadata-only/redacted expose zero payload bytes; bounded-prefix exposes only the declared prefix; no decode claim | T024-SR-003, T024-SR-005, T024-SR-006; CHK-05, CHK-06 |
| Bounded retention | every queue stays within its declared capacity with exact loss counters and accounting identity | T024-SR-008, T024-SR-009, T024-SR-010; CHK-09, CHK-10 |
| Declared validity fidelity | the realized status derives only from the declared effect and an actual loss; at least `degraded` for lossless | T024-SR-011, T024-SR-012; CHK-11, CHK-12 |
| Deterministic ordering | per-tap FIFO under drop/coalesce; independent multi-tap order; route FIFO invariance | T024-SR-007, T024-SR-014; CHK-08, CHK-14 |
| Fail-closed detach | stale/foreign/closed/claimed handles are rejected with stable outcomes and no mutation | T024-SR-013; CHK-13 |
| Normalized records | complete, self-describing, value-owned records for every family/origin/outcome | T024-SR-015; CHK-16 |
| Argus boundary | no rendering, storage, query, presentation, or export primitive | T024-SR-016; CHK-17 |
| Determinism | bounded threads/iterations; repeated runs produce the same outcome | T024-SR-017, T024-SR-018; CHK-18, CHK-19 |
| Offline safety | standard-library plus admitted test dependencies only; no network/ambient/filesystem/process access | T024-SR-019; CHK-21 |
| Public safety | committed files carry no secret, private address, real payload, or host path | T024-SR-020; CHK-22 |
| Additivity | no existing case, target, label, value, production unit, or build file is changed | T024-SR-021; CHK-02, CHK-20 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged; T024 checkbox only at implementation | T024-SR-023, T024-SR-024; CHK-24, CHK-25 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T024 consumes the accepted observation and provider surfaces; it
  introduces no dependency on a later slice and no adapter, storage, or dashboard element.
- **Domain neutrality preserved.** The matrix uses only generic observation vocabulary (payload modes,
  overflow policies, validity effects, interaction families); no automotive or product primitive and no
  configuration language is introduced.
- **XDL centrality preserved.** T024 neither parses nor authors XDL and mirrors the accepted declaration
  only indirectly through the consumed tap policy.
- **Logical/physical separation preserved.** The matrix asserts logical identities, clock domains, and
  counters only; no address, provider transport, or environment identity enters a record.
- **Argus boundary preserved.** The matrix exercises the in-process normalized record and snapshot only;
  X-COM owns no rendering, storage, query, or presentation (`T24-XB-7`, ADR-0019).
- **Ownership preserved.** Only T024-owned observation test paths, the T024 work products, and the T024
  checkbox change; the accepted T021/T022/T023 behavior is re-verified unchanged and no prior declaration
  is weakened.
- **Maturity preserved.** The observation boundary stays a bounded prototype; executed sanitizer/static/
  Doxygen evidence, benchmarks, integration, and acceptance remain with T035–T041.

## 10. Traceability

| Architecture element | T024 requirements |
| --- | --- |
| `T24-XB-1`, `T24-WP` | T024-STK-001, T024-STK-005, T024-SR-001, T024-SR-021, T024-SR-022, T024-SR-023 |
| `T24-XB-2`, `T24-TS-001` | T024-STK-002, T024-SR-003, T024-SR-005, T024-SR-006 |
| `T24-XB-3`, `T24-TS-003` | T024-STK-002, T024-SR-004, T024-SR-008, T024-SR-009, T024-SR-010, T024-SR-018 |
| `T24-XB-4`, `T24-TS-004` | T024-STK-002, T024-SR-011, T024-SR-012 |
| `T24-XB-5`, `T24-TS-008`, `T24-TS-009` | T024-STK-002, T024-SR-014 |
| `T24-XB-6`, `T24-TS-005` | T024-STK-002, T024-SR-013 |
| `T24-XB-7`, `T24-TS-006` | T024-STK-003, T024-SR-015, T024-SR-016 |
| `T24-XB-8` | T024-STK-004, T024-SR-017, T024-SR-018, T024-SR-019, T024-SR-020 |
| `T24-TS-002` | T024-SR-007 |
| `T24-TS-007` | T024-SR-002, T024-SR-015 |
| `T24-CMP-HUB`, `T24-CMP-DECLARATION`, `T24-CMP-RETENTION`, `T24-CMP-SINK`, `T24-CMP-ROUTE` | T024-SR-001, T024-SR-021, T024-SR-024 (re-verified unchanged) |

## 11. Revision 3 — Terminal review R-01 governance-repair architecture

### 11.1 Position in the delivery graph

Revision 3 is a **governance-record repair**, not a runtime component. It closes finding R-01 on the
accumulated T011–T016/T021–T024 candidate at baseline
`d50bb48f45e422b8a7018710b1ac50cdadbcf8ed`. It changes the authoritative T007 ownership register and the
capability analysis record so that the recorded reconciliation state matches the delivered task state,
while keeping the external-acceptance gate explicitly open. It adds no observation, communication,
stimulation, or gateway component, and it does not alter the Revision 1 observation acceptance matrix.

```text
terminal review R-01
   → T024-R01 requirements (this repair) → T024-R01 detailed design → T024-R01 unit specs → T024-R01 verification
   → T007 ownership register reconciliation (`delivered` + exact revision + pending acceptance)
   → capability analysis A12 successor note
   → affected validators (task-ownership, requirements-traceability)
   → deterministic gate → external Codex review (deferred) → explicit user acceptance (deferred)
```

### 11.2 Boundary and trust boundaries

- **Write boundary.** Only the paths in `requirements.md` §11.5 are writable by this repair.
- **Read-only accepted evidence.** `docs/engineering/xcom/t008/requirements-register.{json,md}`,
  `docs/engineering/xcom/t009/architecture-model.{json,md}`, `docs/engineering/xcom/t010/unit-design.{json,md}`,
  the `t007-t020-acceptance-decision.md` record, and the ADRs are consumed read-only. Their historical
  open-checkbox language is disposed by a dated successor note, not rewritten.
- **Acceptance boundary.** The repair never writes an acceptance decision. Candidate delivery is recorded;
  external review and user acceptance remain a separate, later gate (ADR-0020; Constitution §Capability
  acceptance gates).

### 11.3 Components and interfaces

No new software component. The only structural change is to the reconciliation vocabulary of the T007
register (`accepted`/`unreconciled`/`allocated`/`deferred` extended with `delivered`) and the projection
that renders it. The register schema version stays `1` because the reconciliation value is a free string
constrained by the repository-owned validator, not by the JSON schema object; the validator's
`RECON_STATUSES` is the normative vocabulary.

| Interface | Producer | Consumer | Contract |
| --- | --- | --- | --- |
| `reconciliation[task] = {status, revision, reason}` | `task-ownership.json` author | `validate_xcom_task_ownership.py`, `validate_xcom_requirements_traceability.py`, `validate_xcom_architecture_contracts.py`, `validate_xcom_unit_design.py` | `delivered` requires a 40-hex lowercase revision and a non-empty reason; the exact-delivered set T012–T016/T021–T024 is pinned by the validator |
| `task-ownership.md` | deterministic projection | human review | byte-identical to `project_markdown(json)` |
| analysis A12 | `analysis.md` author | review | records `delivered` plus pending acceptance; supersedes the checkbox-open wording |

### 11.4 Prohibited elements

- No change to maturity vocabulary, maturity values, REF-002 dispositions, ADRs, contracts, or schemas.
- No acceptance, no promotion to `implemented`, no legacy or external-network interaction.
- No edit to accepted predecessor bytes; no edit to `src/`, any existing `tests/` file, `xdl/`, `cmake/`, or `CMakeLists.txt`. The only `tests/` addition is the new governance regression test required by the T024 deterministic gate.

### 11.5 Concurrency and resource bounds

The repair is single-threaded, offline, and deterministic. The register validator bounds its inputs to
1 MiB per file and 4 MiB total; it opens no network peer, subprocess, or listener. There is no shared
mutable state, so no concurrency bound applies.

### 11.6 Quality attributes

| Attribute | Realization |
| --- | --- |
| Traceability | exact candidate revision per `delivered` task; stable `T024-R01-SR-###` links to checks |
| Auditability | git-diff-visible one-line reason edits; regenerated deterministic projection |
| Reproducibility | byte-stable JSON serialization and projection; offline validators |
| Public safety | no absolute host path, credential, private address, or sensitive value |
| Compatibility | no API, protocol, contract, or schema change; README/governance semantics preserved |

### 11.7 Traceability (repair view)

| Architectural element | Requirements |
| --- | --- |
| Register reconciliation (`delivered`) | `T024-R01-SR-001`, `T024-R01-SR-004` |
| Analysis A12 successor note | `T024-R01-SR-002`, `T024-R01-SR-003` |
| Validator enforcement | `T024-R01-SR-004`, `T024-R01-SR-006` |
| Governance regression test | `T024-R01-SR-009` |
| Acceptance boundary | `T024-R01-SR-005` |
| Path boundary / public safety | `T024-R01-SR-007`, `T024-R01-SR-008` |
