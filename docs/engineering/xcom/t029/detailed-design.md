# T029 Detailed Design — Owned Fixture, Matrix Behaviour, Expected Values, and Planned Cases

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Stage / role | plan → detailed design |
| Revision | 1 (complete T-STIM cross-cutting verification matrix) |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed accepted units | `XCOM-DU-014` (time authority), `XCOM-DU-015` (permit/session), `XCOM-DU-016` (journal), `XCOM-DU-017` (guard), `XCOM-DU-018` (actions/lease) |
| Classification | Public-safe engineering work product |

## 2. Design principles

1. **Test-only.** T029 adds tests and a fixture header only; it changes no production byte and no existing test.
2. **Owned fixture.** Every case constructs its own bounded fixture; the fixture composes accepted public surfaces
   and re-implements no accepted check (`T29-XB-2`).
3. **Fail-closed observation.** Every decline is asserted as an explicit status with zero emitter calls, zero
   durable append in the declined dimension, and no operational mutation (`T29-XB-3`).
4. **Explicit evidence.** Every assertion names the expected value; no case asserts "no crash".
5. **Bounded determinism.** Threads, operations, queues, leases, lineage, quota, and injected faults are finite and
   declared; no case depends on wall-clock timing (`T29-XB-7`, `T29-XB-8`).
6. **Accepted anchors only.** Identities, digests, vocabularies, and statuses are reused from the accepted
   T025/T026/T027/T028/T-CORE/T-OBS headers, never redefined (`T029-SR-002`).

## 3. Fixture types and vocabulary

The fixture is test-local (`tests/xcom/stimulation_matrix/test_support.hpp`); it defines no production vocabulary
and redefines no accepted type.

### 3.1 Fixture components

| Type | Role | Bounds |
| --- | --- | --- |
| `MatrixFixture` | owns the permit/session values, policy, journal storage, journal, registry, emitter, action path, and snapshots for one case | one permit, one policy, one action path, ≤ 64 operations |
| `FaultStorage` | bounded `StimulationJournal::Storage` with a declared byte buffer and injectable append/sync/read/truncate failures | ≤ 16 KiB durable bytes; ≤ 4 declared fault points |
| `RecordingEmitter` | bounded `ActionEmitter` counting calls, capturing the last `SyntheticStimulationItem`, and returning a declared `EmissionStatus` | ≤ 64 calls; captures ≤ 1 descriptor |
| `ObservationBridge` | builds a `CommunicationItem` classified `OriginKind::validation_tool` from the emitted descriptor and binds a bounded `ObservationHub` + `ObservationTapSpec` + `SyntheticObservationSink` | ≤ 1 item per case; payload-free |

### 3.2 Declared identity projection (bounded, test-local)

The bridge encodes the accepted T026 numeric identity onto the accepted T-CORE string identity with a fixed,
declared, bounded encoding (zero-padded decimal, no free-form text, no payload). This projection is a test-local
convention recorded as `T029-GAP-02`; no canonical production projection is claimed.

| Intent field | Item field | Encoding |
| --- | --- | --- |
| `request_id` | `correlation_id` | bounded decimal |
| `causation_id` | `causation_id` | bounded decimal |
| `tool` | `provider_id` (via format) | declared tag text reused |
| `session_id` | `endpoint_id` (via format) | bounded decimal |

### 3.3 Fixture builders

| Helper | Purpose |
| --- | --- |
| `make_permit()` | valid accepted `Permit` bound to one session, plan digest, validity domain `[0, 100)`, interface/target tags, and one quota |
| `make_policy(quota)` | accepted `StimulationPolicy` allowing all four actions/interactions/directions with the declared quota, loop window, and service owner |
| `make_config()` | bounded `ActionPathConfig` (pending 4/8, lineage 2/4/8, drain 4/8, payload bound, tool tag) |
| `make_request(id, action)` | accepted `StimulationRequest` with the action/interaction/direction/schema pairing from the accepted T027 closed table |
| `in_window()`, `out_of_window()`, `unmapped()` | caller-resolved `ResolvedTime` values (`Ok`, `PermitExpired`/out of window, `UnknownClock`/`MissingMapping`/`ToleranceExceeded`) |
| `bridge_item(descriptor)` | bounded `CommunicationItem` classified `OriginKind::validation_tool` from the emitted descriptor |

## 4. Behaviour

### 4.1 `MatrixFixture` construction

The constructor builds a valid permit, policy, fault-injectable storage, journal (opened over the storage), lease
registry, action path, and recording emitter. `open()` is explicit; a case that requires a closed path does not
open it. Construction and `open()` mutate no accepted global state.

### 4.2 Mismatch-matrix evaluation

For each row the case overwrites exactly one request field (or the session state / resolved time / quota / loop
window), submits once, and asserts the declared status and reason. The accepted guard is evaluated exactly once
per submitted request; the recording emitter observes zero calls; the durable journal byte count is unchanged.

### 4.3 Journal fault injection

A case selects one declared fault point on `FaultStorage` and submits one authorized immediate action, then asserts
the declared status, the emitter call count, and the durable record count. The failure is removed before the next
row.

### 4.4 Restart and recovery

A case emits an authorized action, then discards the journal object and constructs a fresh accepted
`StimulationJournal` over the same `FaultStorage` bytes, runs `open`/`recover`, and asserts the recovered
`RecoveryReport` and the recovered intent identity against the emitted descriptor.

### 4.5 Provenance bridge

A case captures the emitted descriptor, builds the bridge item, attaches the accepted observation tap, submits the
item through the accepted provider route (`ProviderComposition::submit`) with the observation hub enabled, polls
the accepted tap, and asserts the retained `ObservationRecord` origin and identity.

### 4.6 Lease and completion

A case exercises `ServiceEmulationRegistry` directly and through the action path: acquisition, same-generation
conflict, foreign identity, supersession, release, quarantine, expiry, and capacity; then exercises `drain`,
`close`, `revoke`, `expire`, and `mark_evidence_incomplete` with a bounded pending queue and held lease.

### 4.7 Concurrency

A case starts ≤ 4 threads over a finite declared operation count and joins them all before asserting. The accepted
components serialize their own state; the fixture invokes no callback under a lock.

## 5. Expected-value tables

### 5.1 Permit/action mismatch matrix (through the accepted action path)

| Row | Injected mismatch | Guard reason | `ActionStatus` | Emitter calls | Durable appends |
| --- | --- | --- | --- | --- | --- |
| M-01 | malformed request / zero request id / over-bound payload | `RejectedConfiguration` | `RejectedConfiguration` (precondition) | 0 | 0 |
| M-02 | foreign permit identity | `PermitMismatch` | `Rejected` | 0 | 0 |
| M-03 | undeclared schema | `SchemaMismatch` | `Rejected` | 0 | 0 |
| M-04 | inconsistent direction | `DirectionMismatch` | `Rejected` | 0 | 0 |
| M-05 | inconsistent interaction | `InteractionMismatch` | `Rejected` | 0 | 0 |
| M-06 | foreign target tag | `TargetMismatch` | `Rejected` | 0 | 0 |
| M-07 | action not allowed by policy | `ActionMismatch` | `Rejected` | 0 | 0 |
| M-08 | missing/ambiguous service owner | `OwnershipConflict` | `Rejected` | 0 | 0 |
| M-09 | declared quota exhausted | `QuotaExhausted` | `Rejected` | 0 | 0 |
| M-10 | causal parent already in the loop/lineage window | `LoopBound` | `Rejected` | 0 | 0 |
| M-11 | resolution outside the validity window | `TimeOutOfWindow` | `Rejected` | 0 | 0 |
| M-12 | absent/unmapped/out-of-tolerance resolution | `TimeUnmapped` | `Failed` | 0 | 0 |
| M-13 | `revoked` session state | — (action-path precondition) | `NotActive` | 0 | 0 |
| M-14 | `expired` session state | — (action-path precondition) | `NotActive` | 0 | 0 |
| M-15 | `declared`/`armed`/`closing` session state | — (action-path precondition) | `NotActive` | 0 | 0 |
| M-16 | closed accepted guard evaluated directly | `NotOpen` | `Failed` at the guard level | 0 | 0 |

### 5.2 Quota decision

| Row | Declared budget | Submitted | Expected |
| --- | --- | --- | --- |
| Q-01 | per-session = per-window = `n` | `n` authorized then `n+1` | the first `n` are `Emitted`/`Queued`; the `n+1`-th is `Rejected`/`QuotaExhausted`, zero emission |
| Q-02 | per-window < per-session | window exhausted before session | `Rejected`/`QuotaExhausted` until the window advances |
| Q-03 | budget `n` with 4 threads × bounded operations | ≤ `n` authorized total | the emitter/queue count never exceeds `n`; repeated runs identical |

### 5.3 Loop and lineage decision

| Row | Injected | Expected |
| --- | --- | --- |
| L-01 | `causation_id` equals an emitted request id | `Rejected`/`LoopBound`, zero emission, zero append |
| L-02 | `causation_id == 0` | never a loop rejection |
| L-03 | `max_lineage_entries` reached | the window retains at most the bound and evicts the oldest; a new emission succeeds |
| L-04 | guard `loop_window` reached | `Rejected`/`LoopBound` or declared bound behavior with zero emission |

### 5.4 Clock decision

| Row | Resolved time | Expected |
| --- | --- | --- |
| C-01 | `domain == validity_domain`, `value` in `[from, until)`, `Ok` | proceeds (positive control) |
| C-02 | `resolution == UnknownClock` | `Failed`/`TimeUnmapped`, zero emission, zero append |
| C-03 | `resolution == MissingMapping` | `Failed`/`TimeUnmapped` |
| C-04 | `resolution == ToleranceExceeded` | `Failed`/`TimeUnmapped` |
| C-05 | `value >= until` | `Rejected`/`TimeOutOfWindow` |
| C-06 | lease/registry value in a foreign domain | never compared or ordered; `expire_elapsed` touches only the declared domain |
| C-07 | any row | no `TimeAuthority` call and no authority mutation |

### 5.5 Journal decision

| Row | Injected | Expected status | Emitter calls | Durable appends |
| --- | --- | --- | --- | --- |
| J-01 | nominal intent + delivered outcome, each action kind | `Emitted` | 1 (after durable intent) | intent + outcome |
| J-02 | host returns `Rejected` with a durable outcome | `EmissionRejected` | 1 | intent + outcome |
| J-03 | host returns `Unavailable` with a durable outcome | `EmissionUnavailable` | 1 | intent + outcome |
| J-04 | intent append fails (`WriteFailed`) | `JournalFailed` | 0 | 0 |
| J-05 | intent sync fails / short append (`PartialWrite`) | `JournalFailed` | 0 | 0 |
| J-06 | outcome append fails after a durable intent (`WriteFailed`) | `EvidenceIncomplete` | 1 | intent only |
| J-07 | journal bound exceeded (`CapacityExhausted`) | `CapacityExhausted` | 0 | 0 |
| J-08 | restart over J-06 bytes | recovery reports one orphan; identity equals the emitted descriptor | — | — |
| J-09 | `close`/`mark_evidence_incomplete` with the J-06 orphan | `EvidenceIncomplete`, never `Closed`, orphan reported once | 0 | — |

### 5.6 Zero-emission decline families

| Row | Decline family | Emitter calls | Durable byte delta | Snapshot delta |
| --- | --- | --- | --- | --- |
| Z-01 | closed path | 0 | 0 | counters only |
| Z-02 | malformed request | 0 | 0 | counters only |
| Z-03 | over-bound payload | 0 | 0 | counters only |
| Z-04 | loop/lineage rejection | 0 | 0 | counters only |
| Z-05 | pending-queue capacity | 0 | 0 | counters only |
| Z-06 | emulation-lease conflict | 0 | 0 | counters only |
| Z-07 | non-active session | 0 | 0 | counters only |
| Z-08 | guard rejection/failure | 0 | 0 | counters only |
| Z-09 | quota exhaustion | 0 | 0 | counters only |
| Z-10 | late rejection/discard | 0 | 0 | counters only |
| Z-11 | unmapped/out-of-tolerance time | 0 | 0 | counters only |

### 5.7 Provenance decision

| Row | Stage | Expected |
| --- | --- | --- |
| P-01 | emitted descriptor, each action kind | `origin == OriginKind::validation_tool`; exact tool/permit/session/plan/request/correlation/causation identity |
| P-02 | bridged item submitted via the accepted provider route | provider accepts; no relabelling |
| P-03 | retained `ObservationRecord` | `origin == validation_tool`; exact correlation/causation identity |
| P-04 | `ObservationFilter` constrained to `validation_tool` | matches every retained synthetic record; an item of another origin does not match |
| P-05 | journal restart | recovered intent identity equals the emitted descriptor identity; synthetic classification unchanged |

### 5.8 Lease decision

| Row | Injected | Expected |
| --- | --- | --- |
| L-01 | second acquire for one endpoint generation | `Conflict`; no second owner; second request `LeaseConflict`, zero emission |
| L-02 | foreign `session` | `SessionMismatch`; no mutation |
| L-03 | foreign/superseded `generation` | `GenerationMismatch`; superseded generation neither authorizes nor blocks |
| L-04 | foreign `plan_digest` | `PlanMismatch`; no mutation |
| L-05 | exact-owner release | `Ok`; lease inactive; re-acquire succeeds |
| L-06 | non-owner/unknown release | `NotHeld`/`NotFound`; no mutation |
| L-07 | quarantine | `Ok`; `LeaseState::Quarantined`; no longer blocks |
| L-08 | `expire_key`/`expire_elapsed` in the declared domain | `Ok`; `LeaseState::Expired`; foreign-domain values untouched |
| L-09 | active-lease capacity | `CapacityExhausted`; no mutation |
| L-10 | ≤ 4-thread race for one generation | exactly one `Ok`, the rest `Conflict` |

### 5.9 Completion decision

| Row | Operation / state | Expected outcome | Effects |
| --- | --- | --- | --- |
| D-01 | `drain(active)`, due queue | `Drained` when the queue empties; else `None`; ≤ `max_drain_steps` | due actions emitted in declared order |
| D-02 | `drain(declared/armed)` | `None`, never `Drained` | every pending action cancelled, zero emission |
| D-03 | `close(active)` | `Closed` after draining and releasing every lease | no held lease remains |
| D-04 | `close(closed)` with an orphan intent | `EvidenceIncomplete`, never `Closed` | orphan reported |
| D-05 | `revoke` | `Revoked` | every pending action cancelled; held leases released |
| D-06 | `expire` | `Expired` | every pending action cancelled; held leases expired |
| D-07 | `mark_evidence_incomplete` | `EvidenceIncomplete` | orphan reported; never success |
| D-08 | late action, `RejectLate`/`DiscardLate` | cancelled/expired/discarded | zero emission |
| D-09 | due action whose drain-time intent append fails | `EvidenceIncomplete`, `failed >= 1` | never a clean `Drained`/`Closed` |

### 5.10 Concurrency decision

| Row | Configuration | Expected |
| --- | --- | --- |
| K-01 | 4 threads × ≤ 16 bounded submissions, quota 7 | exactly 7 authorized; 3 runs identical; no callback under a lock |
| K-02 | 4 threads racing one endpoint generation | exactly one winner; deterministic final snapshot |
| K-03 | concurrent execute vs completion | deterministic total order; bounds never exceeded; identical repeated runs |

## 6. Failure semantics

A case fails when any expected value in §5 is not observed. Every decline asserts **zero** emitter calls, an
unchanged durable byte count in the declined dimension, and an unchanged operational snapshot apart from declared
counters. A case never asserts "no crash"; it asserts the exact closed status, reason, outcome, state, or count.
A test failure is a candidate failure and never weakens an accepted requirement.

### 6.1 Negative-case mapping

| Negative case | Realized by |
| --- | --- |
| NEG-01 | changed-path/diff inspection; a production or later-task path fails the boundary |
| NEG-02 | include/link inspection; a redefined accepted type or new dependency fails |
| NEG-03 | fixture header inspection; a payload-retaining member or re-implemented check fails |
| NEG-04/M-01 | malformed request reaches the emitter or journal |
| NEG-05/M-02…M-08 | a declaration mismatch emits or journals |
| NEG-06/M-13…M-16 | a lifecycle precondition or closed guard emits |
| NEG-07/Q-01 | a quota-exhausted request is authorized |
| NEG-08/Q-03/K-01 | a concurrent run exceeds the declared quota |
| NEG-09/L-01 | a retained causal parent is authorized |
| NEG-10/L-03 | the lineage window exceeds its declared bound |
| NEG-11/C-02…C-05 | an unmapped/out-of-tolerance time is emitted |
| NEG-12/C-06 | two raw mismatched clock domains are compared |
| NEG-13/J-01 | emission precedes the durable intent |
| NEG-14/J-04 | an intent append failure emits |
| NEG-15/J-05 | an intent sync failure emits |
| NEG-16/J-06 | an incomplete outcome is reported as `Emitted` |
| NEG-17/J-09, D-04 | an incomplete outcome is reported as `Closed` |
| NEG-18/Z-05 | a full queue emits |
| NEG-19/Z-06 | a lease conflict emits |
| NEG-20/Z-04, Z-10 | a loop or late rejection emits |
| NEG-21/P-01 | a non-synthetic descriptor is emitted |
| NEG-22/P-02, P-03 | provenance is relabelled or dropped through route/observation |
| NEG-23/P-04, P-05 | a filter matches a foreign origin or restart identity differs |
| NEG-24/L-01…L-04, L-10 | a second owner or foreign identity acquires/emits |
| NEG-25/L-05…L-08 | a released/quarantined/expired lease remains active or blocking |
| NEG-26/L-08 | a foreign-domain lease value is compared |
| NEG-27/D-01 | more than `max_drain_steps` complete per call |
| NEG-28/D-08 | a late action emits |
| NEG-29/D-02, D-05, D-06 | a completion leaves a pending action or held lease unresolved |
| NEG-30/D-09 | a dropped due action is reported as a clean `Drained`/`Closed` |
| NEG-31/K-01…K-03 | repeated runs differ |
| NEG-32/K-02 | a lease race has two winners |
| NEG-33/K-01 | a callback is invoked under a lock |
| NEG-34 | forbidden-API scan; a network/ambient/secret/process/legacy access fails |
| NEG-35 | public-safety scan; an absolute path/credential/real payload fails |
| NEG-36 | register validators; a weakened requirement/test or promoted REF-002 fails |
| NEG-37 | deterministic gate; a missing work product, unchecked box at the plan stage, or non-`tests/` change fails |

## 7. Bounds and resource design

| Resource | Bound | Cases |
| --- | --- | --- |
| Threads | ≤ 4 | TS-019, TS-020 |
| Operations per case | ≤ 64 | all |
| Pending queue | 4, 8 | TS-018, TS-019 |
| Drain budget | 4, 8 | TS-018, TS-019 |
| Lineage window | 2, 4, 8 | TS-004 |
| Active leases | 1, 2 | TS-016, TS-020 |
| Guard quota | 1 … 8 | TS-003, TS-019 |
| Mismatch rows | ≤ 16 | TS-001, TS-002 |
| Decline families | ≤ 11 | TS-011 |
| Durable bytes | ≤ 16 KiB | TS-006…TS-010 |
| Injected fault points | ≤ 4 | TS-007, TS-008 |
| Restart attempts | 1 per restart case | TS-009 |
| Wall-clock | none | all |

## 8. Build wiring design

`src/xverse/xcom/CMakeLists.txt` gains one additive `foreach` block that, for each `matrix_kind` in
`permit_action_matrix`, `journal_recovery`, `zero_emission`, `provenance`, `lease_drain`, and `concurrency`:

- adds one executable `xverse_xcom_stimulation_matrix_<kind>_tests` from
  `tests/xcom/stimulation_matrix/<kind>_tests.cpp`;
- links `xverse::xcom_stimulation_actions`, `xverse::xcom_observation`, and
  `xverse::xcom_provider_loopback` read-only, plus `GTest::gtest_main`, `GTest::gmock`, and `Threads::Threads`;
- adds `tests/xcom/stimulation_matrix` as a private include directory for `test_support.hpp`;
- passes the committed T028 header/source and the T-OBS/provider headers as build-time read-only compile
  definitions for the bounded declaration inspection;
- applies the inherited warning-as-error rule and registers with `gtest_discover_tests(...
  PROPERTIES LABELS "t029-<kind>")`, where the underscore in `matrix_kind` is replaced by a hyphen (the
  CMake 3.22 single-label workaround), yielding `t029-permit-action-matrix`, `t029-journal-recovery`,
  `t029-zero-emission`, `t029-provenance`, `t029-lease-drain`, and `t029-concurrency`.

The `XVERSE_XCOM_RUNTIME_TARGETS` inventory is unchanged; the `xcom_build_contract` verifier is unchanged.

## 9. Doxygen plan

The fixture header and each test source carry a file block with `\file`, `\brief`, `\ownership`, `\lifetime`,
`\thread_safety`, `\bounds`, and `\failure`, mirroring the accepted T028 test convention. Public test-local
helpers carry `\brief`/`\param`/`\return`. Strict declaration-level Doxygen execution remains `DOX-GAP-01`
(T011/T037); T029 supplies the declarations only.

## 10. Case inventory (planned tests)

### 10.1 `tests/xcom/stimulation_matrix/permit_action_matrix_tests.cpp` (label `t029-permit-action-matrix`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-001` | `MismatchMatrixEveryGuardReason` | rows M-02…M-12 of §5.1: declared status and reason, one guard evaluation, zero emission, zero append |
| `T29-TS-002` | `MismatchMatrixLifecycleAndClosedGuard` | rows M-13…M-16: `NotActive` preconditions and the direct closed-guard `Failed`/`NotOpen`, zero emission |
| `T29-TS-003` | `MismatchMatrixQuotaExhaustion` | §5.2 Q-01/Q-02: exact budget commit, `Rejected`/`QuotaExhausted`, zero emission |
| `T29-TS-004` | `MismatchMatrixLoopBoundAndLineage` | §5.3 L-01…L-04: loop rejection, `causation_id == 0`, lineage eviction under the declared bound |
| `T29-TS-005` | `MismatchMatrixUnmappedAndOutOfToleranceClock` | §5.4 C-01…C-07: fail-closed resolution, out-of-window rejection, no raw cross-domain compare, no authority call |

### 10.2 `tests/xcom/stimulation_matrix/journal_recovery_tests.cpp` (label `t029-journal-recovery`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-006` | `JournalIntentPrecedesSingleEmission` | §5.5 J-01…J-03: durable intent before the single call for each action kind; durable non-delivery maps to `EmissionRejected`/`EmissionUnavailable` |
| `T29-TS-007` | `JournalIntentAppendFailureEmitsNothing` | §5.5 J-04/J-05: injected intent append (`WriteFailed`) and sync/partial-write (`PartialWrite`) failure both return `JournalFailed`, zero emission, zero durable records |
| `T29-TS-008` | `JournalOutcomeFailureIsEvidenceIncomplete` | §5.5 J-06: injected outcome failure returns `EvidenceIncomplete`, never `Emitted`; exactly one durable intent |
| `T29-TS-009` | `JournalRestartRecoversExactIdentity` | §5.5 J-08: reopen over the same bytes, recovered orphan identity equals the emitted descriptor identity |
| `T29-TS-010` | `JournalCapacityExhaustionFailsClosed` | §5.5 J-07: over-capacity append returns `CapacityExhausted`, zero emission, no over-bound record |

### 10.3 `tests/xcom/stimulation_matrix/zero_emission_tests.cpp` (label `t029-zero-emission`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-011` | `ZeroEmissionAcrossEveryRejectionFamily` | §5.6 Z-01…Z-11: zero emitter calls, zero durable byte delta, operational snapshot unchanged apart from declared counters |

### 10.4 `tests/xcom/stimulation_matrix/provenance_tests.cpp` (label `t029-provenance`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-012` | `ProvenanceDescriptorCarriesSyntheticIdentity` | §5.7 P-01: classification and exact identity for each action kind |
| `T29-TS-013` | `ProvenanceSurvivesRoutingAndObservation` | §5.7 P-02/P-03/P-04: provider route and observation tap preserve origin and identity; the `validation_tool` filter matches only synthetic records |
| `T29-TS-014` | `ProvenanceSurvivesJournalRestart` | §5.7 P-05: recovered intent identity equals the emitted descriptor identity |
| `T29-TS-015` | `ProvenanceNeverRelabelled` | §5.7 P-01…P-05 negative side: no path emits/observes a foreign origin and no provenance is dropped |

### 10.5 `tests/xcom/stimulation_matrix/lease_drain_tests.cpp` (label `t029-lease-drain`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-016` | `LeaseConflictMatrixEndToEnd` | §5.8 L-01…L-09: conflict, identity mismatch, supersession, release, quarantine, expiry, capacity, no mutation, zero second-owner emission |
| `T29-TS-017` | `DrainTerminalLifecycleMatrix` | §5.9 D-01…D-07: declared outcomes, pending cancellation, lease release/quarantine/expiry, evidence-incomplete never `Closed` |
| `T29-TS-018` | `DrainOrderingLatePolicyAndImmediateLabel` | §5.9 D-01/D-02/D-08/D-09: ordered drain within budget, both late policies emit nothing, a dropped due action surfaces `failed`, immediate labeling |

### 10.6 `tests/xcom/stimulation_matrix/concurrency_tests.cpp` (label `t029-concurrency`)

| Unit | Case function | Asserts |
| --- | --- | --- |
| `T29-TS-019` | `ConcurrentQuotaEmissionDeterminism` | §5.10 K-01/K-03: 4 threads never exceed the declared quota; no callback under a lock; 3 runs identical |
| `T29-TS-020` | `ConcurrentLeaseSingleWinnerAndCompletion` | §5.10 K-02/K-03: exactly one lease winner; deterministic completion snapshot across repeated runs |

## 11. Traceability

| Unit | T029 requirements | Accepted software req | Spec anchor | Design unit |
| --- | --- | --- | --- | --- |
| `T29-TS-001` | T029-SR-004 | `XCOM-SW-STIM-005` | FR-018, FR-019 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-002` | T029-SR-005 | `XCOM-SW-STIM-009` | FR-018, SC-007 | `XCOM-DU-015`, `XCOM-DU-018` |
| `T29-TS-003` | T029-SR-006 | `XCOM-SW-STIM-006` | FR-019, FR-020 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-004` | T029-SR-007 | `XCOM-SW-STIM-005` | FR-019 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-005` | T029-SR-008 | `XCOM-SW-STIM-006` | FR-020, FR-033 | `XCOM-DU-014`, `XCOM-DU-018` |
| `T29-TS-006` | T029-SR-009 | `XCOM-SW-STIM-007` (consumed) | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-007` | T029-SR-010 | `XCOM-SW-STIM-007`, `-009` | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-008` | T029-SR-011 | `XCOM-SW-STIM-007`, `-009` | FR-021, SC-007 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-009` | T029-SR-011, T029-SR-015 | `XCOM-SW-STIM-003`, `-009` | FR-017, FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-010` | T029-SR-010 | `XCOM-SW-STIM-007`, `-009` | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-011` | T029-SR-012 | `XCOM-SW-STIM-005`, `-008` | FR-019, FR-034 | `XCOM-DU-018` |
| `T29-TS-012` | T029-SR-013 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-018` |
| `T29-TS-013` | T029-SR-014 | `XCOM-SW-STIM-003` | FR-017, SC-006 | `XCOM-DU-018` |
| `T29-TS-014` | T029-SR-015 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-015` | T029-SR-013, T029-SR-014 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-018` |
| `T29-TS-016` | T029-SR-016, T029-SR-017 | `XCOM-SW-STIM-008` | FR-033, FR-034 | `XCOM-DU-018` |
| `T29-TS-017` | T029-SR-019 | `XCOM-SW-STIM-009` | SC-007 | `XCOM-DU-018` |
| `T29-TS-018` | T029-SR-018, T029-SR-019 | `XCOM-SW-STIM-006`, `-009` | FR-020, SC-007 | `XCOM-DU-018` |
| `T29-TS-019` | T029-SR-020, T029-SR-021 | `XCOM-SW-STIM-008`, `-009` | FR-007, FR-014 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-020` | T029-SR-016, T029-SR-020 | `XCOM-SW-STIM-008` | FR-014, FR-034 | `XCOM-DU-018` |

## 12. Traceability to accepted `XCOM-DU-014`…`-018` design

| Accepted unit | T029 contribution |
| --- | --- |
| `XCOM-DU-014` time authority | unmapped/out-of-tolerance fail-closed and no-authority-call cases (TS-005) |
| `XCOM-DU-015` permit/session lifecycle | lifecycle-state preconditions and completion-state cases (TS-002, TS-017) |
| `XCOM-DU-016` journal | ordering, intent/outcome failure, restart recovery, capacity cases (TS-006…TS-010, TS-014) |
| `XCOM-DU-017` guard | complete mismatch, quota, and loop-window cases (TS-001, TS-003, TS-004) |
| `XCOM-DU-018` actions/lease | end-to-end action, lease, provenance, drain/terminal, and concurrency cases (TS-005, TS-011…TS-020) |

## 13. Open design items handled outside this artifact

- `T029-GAP-02` — test-local identity projection; no canonical production projection is claimed (T032/T033).
- `T029-GAP-03` — clean-boundary restart, not a crash-consistency test (T026 own matrix).
- `T029-GAP-05` — T029-local fixture, not the T033 reusable contract suite.
- `T029-OPEN-01` — inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` digest refresh
  after the shared `src/xverse/xcom/CMakeLists.txt` change (implementation stage).
