# T029 Implementation Record — Complete Stimulation Verification Matrix and Owned Fixtures

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Stage / role | implementation |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Candidate identity | uncommitted working tree on the baseline; content-addressed by the per-file SHA-256 in §4 |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Classification | Public-safe engineering work product |

Authority: capability 007 accepted design and bounded implementation authorization; ADR-0016 (naming),
ADR-0018 (platform-first), ADR-0019 (observation/stimulation ownership), ADR-0020 (repository-owned work
products and exact-candidate evidence). T029 is a **test-only** slice: it authors no production behaviour
and changes no accepted production header, source, runtime target, existing test, target, label, command,
or expected value. This record is a repository-owned work product; it does not accept or integrate the
candidate, and external Codex review and user acceptance remain deferred until the ordered backlog
`xcom-t026-t029-20260928` completes.

## 2. Scope delivered

1. One bounded, payload-free owned fixture header (`tests/xcom/stimulation_matrix/test_support.hpp`)
   composing the accepted T025 permit/session, T026 fault-injectable journal storage, T027 policy, T028
   action path and exclusive lease registry, a recording emitter, and a bounded bridge into the accepted
   provider/observation boundary.
2. Six additive GoogleTest executables under `tests/xcom/stimulation_matrix/` with 20 case functions
   (`T29-TS-001`…`T29-TS-020`) covering the complete permit/action mismatch matrix, quotas, loop bounds,
   unmapped clocks, journal-before-emission and journal failure/recovery, zero emission after every
   rejection, persistent synthetic provenance, lease conflicts, drain/terminal behaviour, and bounded
   deterministic concurrency.
3. Additive CTest registration in `src/xverse/xcom/CMakeLists.txt` with six `t029-<kind>` labels; no
   runtime-target inventory change.
4. The inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` provenance refresh
   required by the shared `src/xverse/xcom/CMakeLists.txt` digest change.
5. The T029 capability task checkbox and this implementation record.

## 3. Changed artifacts and symbols

| Path | Change | Symbols / notes |
| --- | --- | --- |
| `tests/xcom/stimulation_matrix/test_support.hpp` | add | `MatrixFixture`, `FaultStorage`, `RecordingEmitter`, `ObservationBridge`, `to_decimal`, `session_decimal`, `make_permit`, `make_policy`, `make_config`, `make_request`, `in_window`, `out_of_window`, `unmapped`; test-local, bounded, payload-free |
| `tests/xcom/stimulation_matrix/permit_action_matrix_tests.cpp` | add | `XcomStimulationMatrixPermitAction.{MismatchMatrixEveryGuardReason,MismatchMatrixLifecycleAndClosedGuard,MismatchMatrixQuotaExhaustion,MismatchMatrixLoopBoundAndLineage,MismatchMatrixUnmappedAndOutOfToleranceClock}` |
| `tests/xcom/stimulation_matrix/journal_recovery_tests.cpp` | add | `XcomStimulationMatrixJournalRecovery.{JournalIntentPrecedesSingleEmission,JournalIntentAppendFailureEmitsNothing,JournalOutcomeFailureIsEvidenceIncomplete,JournalRestartRecoversExactIdentity,JournalCapacityExhaustionFailsClosed}` |
| `tests/xcom/stimulation_matrix/zero_emission_tests.cpp` | add | `XcomStimulationMatrixZeroEmission.ZeroEmissionAcrossEveryRejectionFamily` |
| `tests/xcom/stimulation_matrix/provenance_tests.cpp` | add | `XcomStimulationMatrixProvenance.{ProvenanceDescriptorCarriesSyntheticIdentity,ProvenanceSurvivesRoutingAndObservation,ProvenanceSurvivesJournalRestart,ProvenanceNeverRelabelled}` |
| `tests/xcom/stimulation_matrix/lease_drain_tests.cpp` | add | `XcomStimulationMatrixLeaseDrain.{LeaseConflictMatrixEndToEnd,DrainTerminalLifecycleMatrix,DrainOrderingLatePolicyAndImmediateLabel}` |
| `tests/xcom/stimulation_matrix/concurrency_tests.cpp` | add | `XcomStimulationMatrixConcurrency.{ConcurrentQuotaEmissionDeterminism,ConcurrentLeaseSingleWinnerAndCompletion}` |
| `src/xverse/xcom/CMakeLists.txt` | edit | one additive `foreach` block registering `xverse_xcom_stimulation_matrix_<kind>_tests` with labels `t029-permit-action-matrix`, `t029-journal-recovery`, `t029-zero-emission`, `t029-provenance`, `t029-lease-drain`, `t029-concurrency`; `XVERSE_XCOM_RUNTIME_TARGETS` unchanged |
| `engineering/trace/links.json` | edit | `T020-L-046` `implemented_by` target digest refreshed to the new `src/xverse/xcom/CMakeLists.txt` digest |
| `engineering/stage-results/implementation.json` | edit | `src/xverse/xcom/CMakeLists.txt` artifact digest refreshed |
| `engineering/stage-results/{documentation,integration,internal-review}.json` | edit | `engineering/trace/links.json` artifact digest refreshed |
| `specs/007-xcom-core/tasks.md` | edit | one-line T029 checkbox marked complete (**implementation stage only**) |
| `docs/engineering/xcom/t029/implementation.md` | add | this record |

Consumed read-only and unchanged: `stimulation_actions.hpp`/`.cpp`, `stimulation_guard.hpp`/`.cpp`,
`stimulation_journal.hpp`/`.cpp`, `validation_session.hpp`/`.cpp`, the accepted T-CORE/T-OBS/provider
public headers and all existing tests, `engineering/`, `xdl/`, `proto/`, `cmake/*.cmake`, and the root
`CMakeLists.txt`.

## 4. Candidate file digests (SHA-256)

| Path | SHA-256 |
| --- | --- |
| `tests/xcom/stimulation_matrix/test_support.hpp` | `9f770a19b56ddbf5d9ce613b1caf43204c74c63aecbada538f2ba8111311812c` |
| `tests/xcom/stimulation_matrix/permit_action_matrix_tests.cpp` | `4475c4e24bed2cc78fac19223882fe41255b5fa4f624e951493c728f8915f487` |
| `tests/xcom/stimulation_matrix/journal_recovery_tests.cpp` | `7fc5d8115736ba7c07d87c504b0a52b983d7883a793cdde78facff3d80284d7f` |
| `tests/xcom/stimulation_matrix/zero_emission_tests.cpp` | `dc2424736f79360475b6e02d7572b19177d26209f308da167eabad2d94972bb8` |
| `tests/xcom/stimulation_matrix/provenance_tests.cpp` | `e78111ad7ff500e4a47929dba60af5a14979ae8b625a5b094f2870e87fa0a96a` |
| `tests/xcom/stimulation_matrix/lease_drain_tests.cpp` | `490dc061377adc507603fcb9240cda9b48f29687dfac3bd47bf2627e23da3729` |
| `tests/xcom/stimulation_matrix/concurrency_tests.cpp` | `a1691cbe297a4196d8e10c52928793f520c6ddaa489c83df3c72718e87cfe5e9` |
| `src/xverse/xcom/CMakeLists.txt` | `cbf5db33d8c53ed2107a406840bdf0a3d6344b1ac273f37ec0aca44bfbc552d1` |
| `engineering/trace/links.json` | `bdd285e873f87dbbaef06ac43663bd2d8f43673fe840c43d72ee9fb3f845bb1c` |
| `engineering/stage-results/documentation.json` | `a5ec8a1bdc79abf2f239bb960f5ef24d9295a14568db2d2c1e29de8d9c5b9322` |
| `engineering/stage-results/implementation.json` | `b1bb05a81450d562ffe2c4fd9fd4ccbd8d50ea856f6e200ae4cac94659fccdad` |
| `engineering/stage-results/integration.json` | `6340ea42cc2991ae83c3fadf802cd25e9609d169e663ed59c2211a3cb3292510` |
| `engineering/stage-results/internal-review.json` | `30817c3e43a02bd336205dff3037757c33997d3a234746b4103dd5b327692a5e` |
| `specs/007-xcom-core/tasks.md` | `b8376cd657a71ff4787daae9ab7f7930111733c14725b6689088b33d76b52129` |

Work-product digests (`requirements.md` `ce370f17…`, `architecture.md` `bbd0ae3f…`,
`detailed-design.md` `ea1b32f4…`, `unit-specifications.md` `e0132a61…`, `verification-plan.md`
`1ccb1403…`) are recorded by the package stage.

## 5. Build and test wiring

The six executables are registered additively under the inherited T012 warning-as-error rule and link
`xverse::xcom_stimulation_actions`, `xverse::xcom_observation`, `xverse::xcom_provider_loopback`,
`GTest::gtest_main`, `GTest::gmock`, and `Threads::Threads`. `tests/xcom/stimulation_matrix` is a private
include directory for `test_support.hpp`. No third-party dependency is added and no
`XVERSE_XCOM_RUNTIME_TARGETS` entry changes.

## 6. Commands and observed results

All commands run from the repository root at the candidate working tree.

| ID | Command | Observed result |
| --- | --- | --- |
| B-1 | `cmake -S . -B build/fabro-t029 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (A-1 cache-seeded configure) | configure exit 0 |
| B-2 | `cmake --build build/fabro-t029 --parallel 4` | build exit 0; every target, including the six new ones, compiled under `-Werror` |
| B-3 | `ctest --test-dir build/fabro-t029 -N` | `Total Tests: 387` (baseline `build/fabro-t028 -N`: `Total Tests: 367`; +20 additive T029 cases) |
| B-4 | `ctest --test-dir build/fabro-t029 -L t029 --output-on-failure` | `100% tests passed, 0 tests failed out of 20` |
| B-5 | `ctest --test-dir build/fabro-t029 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 387` |
| B-6 | `ctest --test-dir build/fabro-t029 -L "t02[6789]" --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 81` (T026–T029, unchanged preservation) |
| B-7 | `python3 scripts/validate_xcom_task_ownership.py --verify` / `--check-human` | `X-COM task-ownership validation passed` |
| B-8 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | `X-COM requirements/traceability validation passed` |
| B-9 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | `X-COM architecture/contracts validation passed` |
| B-10 | `python3 scripts/validate_xcom_unit_design.py --verify` | `X-COM unit-design validation passed` |
| B-11 | `git diff --check 4d3985855ef7a62b68aa4c66d3b7df032b29f5e9 --` | clean |
| B-12 | `git diff --name-only <baseline> --` | only `src/xverse/xcom/CMakeLists.txt` (tracked); all other candidate paths are new |
| B-13 | `git ls-files --others --exclude-standard` | the six new suites, the fixture header, and the six `docs/engineering/xcom/t029/*.md` work products |
| B-14 | forbidden-API source scan of `tests/xcom/stimulation_matrix/` | clean: no network/socket/resolver/TLS, ambient/secret lookup, dynamic load, subprocess, production filesystem, wall-clock, or legacy access |

The A-1 environment prerequisite is inherited: the admitted offline inputs are read from the previously
admitted cache values (`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`,
`XVERSE_XCOM_T025_TEST_TOOLCHAIN`) by name only; the hash-verified preflight is unchanged and no ambient
path or network resolution is introduced. Host-specific paths are omitted from this public record.

## 7. Check and negative-case coverage

| Check | Realizing unit(s) | Result |
| --- | --- | --- |
| CHK-04, CHK-06, CHK-15 | `T29-TS-001`, `T29-TS-002` | pass (M-01…M-16 rows; one guard evaluation per call exercised directly) |
| CHK-07, CHK-16 | `T29-TS-003`, `T29-TS-019` | pass (Q-01/Q-02; bounded concurrent quota) |
| CHK-08 | `T29-TS-004`, `T29-TS-016` | pass (L-01…L-04; lease conflict/identity/supersession) |
| CHK-09 | `T29-TS-005`, `T29-TS-016` | pass (C-01…C-06; declared-domain lease expiry) |
| CHK-10 | `T29-TS-006` | pass (durable intent before the single call for four action kinds; J-02/J-03) |
| CHK-11 | `T29-TS-007`…`T29-TS-010` | pass (J-04…J-08; capacity fail-closed) |
| CHK-12 | `T29-TS-011` | pass (Z-01…Z-11 with zero emitter calls and zero durable delta) |
| CHK-13 | `T29-TS-012`…`T29-TS-015` | pass (P-01…P-05; descriptor, routed/observed, restart) |
| CHK-14, CHK-17, CHK-18 | `T29-TS-016`…`T29-TS-018` | pass (D-01…D-09; ordering, budget, late policy, terminal outcomes) |
| CHK-16, CHK-19, CHK-20, CHK-21 | inspection + `T29-TS-019`, `T29-TS-020` | pass (bounded determinism, offline, payload-free, public-safe) |
| CHK-23 | register validators (B-7…B-10) | pass; REF-002 `unchanged`, nothing promoted |
| CHK-24 | deterministic gate + `git diff --check` (B-11) | pass (see the separate gate run recorded by the internal review) |

Negative cases realized: NEG-04…NEG-11, NEG-13…NEG-17, NEG-18…NEG-23, NEG-24…NEG-33 by the executable
cases above; NEG-01/NEG-02/NEG-03/NEG-12/NEG-34/NEG-35 by the changed-path, include/link, fixture
declaration, and forbidden-API inspections (B-12…B-14); NEG-36 by the register validators; NEG-37 by the
stage rule (checkbox marked only in this implementation record; ≥ 1 changed `tests/` path). No accepted
requirement, test, ADR, contract, register, or production byte is weakened.

## 8. Maturity and REF-002 disposition

- `XCOM-SW-STIM-009` — **implemented by T029**: the complete owned-fixture action-conformance and
  lifecycle-completion matrix.
- `XCOM-SW-STIM-003` — **implemented by the T029 projection**: descriptor classification and identity,
  routed and observed preservation, and restart identity persistence (`T029-GAP-02` records that the
  fixture identity projection is test-local; a canonical projection and the gateway/IPC proof remain
  T032/T033).
- `XCOM-SW-STIM-005`/`-006`/`-008` remain **implemented** (T028); T029 supplies the cross-cutting evidence
  without changing their disposition.
- REF-002: `disposition` stays `unchanged` with an empty `promoted` list; no allocated, deferred,
  architectural-target, or superseded SADS requirement is reported implemented.

## 9. Limitations and gaps

- `T029-GAP-01` test-only boundary: no runtime, transport, gateway, compatibility, parity, or
  production-readiness claim.
- `T029-GAP-02` test-local identity projection onto the accepted T-CORE string identity vocabulary
  (zero-padded decimal); no canonical production projection is claimed.
- `T029-GAP-03` clean-boundary restart only; crash consistency and torn-write media atomicity remain
  T026's own failure matrix.
- `T029-GAP-04` single-process, single-writer.
- `T029-GAP-05` T029-local fixture, not the T033 reusable contract suite.
- `T029-GAP-06` bounded counts and deterministic outcomes only; no latency, throughput, or real-time
  claim (T036).
- `T029-OPEN-03` the routed/observed provenance case links the accepted observation/provider targets
  read-only; it authors no observation or provider behaviour.

## 10. Provenance refresh (T029-OPEN-01)

Editing `src/xverse/xcom/CMakeLists.txt` invalidated the inherited `T020-L-046` `implemented_by` target
digest and the declared `links.json`/`CMakeLists.txt` digests. Following the T026/T027/T028 precedent, and
without changing any requirement, link identity, relation, or stage result:

- `engineering/trace/links.json` `T020-L-046.target_revision` → new `src/xverse/xcom/CMakeLists.txt`
  digest `cbf5db33…`;
- `engineering/stage-results/implementation.json` `src/xverse/xcom/CMakeLists.txt` → `cbf5db33…`;
- `engineering/stage-results/{documentation,integration,internal-review}.json`
  `engineering/trace/links.json` → new links digest `bdd285e8…`.

Historical T027/T028 package and review records retain their own candidate digests as exact-revision
evidence and are not rewritten.

## 11. Traceability

- Requirements: T029-STK-001…-005; T029-SR-001…-025 (see `requirements.md` §5 and `verification-plan.md`
  §8).
- Design units verified: `XCOM-DU-014` (time authority), `-015` (permit/session), `-016` (journal),
  `-017` (guard), `-018` (actions/lease); component `XCOM-CMP-009`; contract `XCOM-XLC-006`; boundary
  `XCOM-XB-007`; invariants `XCOM-INV-03/04/05/07/09/10`.
- Accepted software requirements closed or evidenced: `XCOM-SW-STIM-003`, `-005`, `-006`, `-008`,
  `-009`.
- Capability slice evidence names (`T007` register): `permit-action-mismatch-matrix`, `quotas`,
  `loop-bounds`, `unmapped-clocks`, `journal-before-emission`, `journal-failure-recovery`,
  `zero-emission-after-rejection`, `synthetic-provenance`, `lease-conflicts`, `drain-terminal`,
  `deterministic-concurrency`.

## 12. Review status

This record is the implementation-stage product. A **separate** read-only DeepSeek internal review is
performed and recorded after this pass in `internal-review.json`; it does not constitute external Codex
review or user acceptance, which remain deferred (T039/T041).
