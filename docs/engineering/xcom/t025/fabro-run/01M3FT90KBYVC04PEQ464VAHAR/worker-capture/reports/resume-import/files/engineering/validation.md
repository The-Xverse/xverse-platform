# T025 Validation — Observed Internal Checks, Scenarios, and Limitations

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | validation |
| Revision | 1 |
| Classification | SANITIZED |
| Design authority | `engineering/design.md` (rev 1) |
| Requirements authority | `engineering/requirements.md` (rev 1) |
| Verification plan | `engineering/verification-plan.md` (rev 1) |
| Source under test | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` (SHA-256 `ec0bc335…b8384c5`), `src/xverse/xcom/src/validation_session.cpp` (SHA-256 `ac6b7018…81daa71`) |
| Tests under test | `tests/validation_session_tests.cpp` (`3df3acdb…d7e3b7c`), `tests/validation_session_integration_tests.cpp` (`d952d0de…eed8e88`), `tests/validation_session_validation_tests.cpp` (`6d0ffeec…81daf5b`) |
| Material identity | `1c1d1a0b59612a00ee8a1ba3bc161f3dee9bde021bdf574afa155dfbdb9667c0` |

### 1.1 Authority statement

Everything in this document is **internal worker evidence from an isolated Docker sandbox**. It is
*not* protected verification and *not* accepted delivery. Internal tests do not establish
predecessor regression, source compatibility, repository integration, human acceptance, or
production readiness. CodeQL and ThreadSanitizer were **not** executed here and are recorded as
pending; nothing in this document may be read as claiming they passed.

## 2. Resume provenance — hash-bound checkpoint verified

This validation stage resumes the failed run `01M3ESNGNTE2KZDV6BM5ACT981` (route
`implementation_repair`). The staged checkpoint was re-hashed during validation:

| Checkpoint control | Observed SHA-256 | Matches |
| --- | --- | --- |
| `manifest.json` | `47cde6f75d9fd4d70dfee2fc7a317b00361bc2650751be8352192399dec6c572` | `engineering/resume-provenance.json` `manifest_sha256` |
| `checkpoint-evidence.json` | `903cdc2c2897929ffcf1a47fdbdffcba2d4102d3ca9e0601b91e16773842f948` | `manifest.checkpoint_evidence_sha256` |
| `inspection-failure.json` | `909a320bc383dd018564bdbef8c584a5d7571290a8209d7418e85d78ef7d48fa` | `resume-provenance.json` `inspection_failure_sha256` |

The failed independent implementation inspection (conclusion `fail`) carried exactly two findings:
**F-01** — a rejected cross-domain transition mutated the time-authority destination baseline; and
**F-02** — the transition-path time/action rejection branches had no executable evidence. The
checkpoint manifest lists 65 files; every listed path was present and every recorded SHA-256
matched the staged draft bytes. The requirements and design inspections both concluded `pass`, and
the unit specifications are validated, so those reviewed inputs were preserved unchanged (their
hashes still match `engineering/resume-provenance.json` `reviewed_artifacts_sha256`).

The **draft** implementation bytes are deliberately *not* the current bytes: the draft header
`67a0a598…` and draft source `2618150c…` were repaired. The current, reviewed implementation is
bound to `ec0bc335…` / `ac6b7018…`, which is what every trace link and measure in this stage
addresses. F-01 and F-02 are treated as repaired, and the repair is independently re-inspected by
the later implementation-inspection gate, not by this validation stage.

## 3. Observed internal commands and results

All commands were run from `/workspace`. The `unit`, `integration`, and `validation` CTest runs
below were re-executed during this validation stage against the current build directory
`build/fabro`; the build/quality/Doxygen records were produced by the preceding controlled gates
and are re-checked here only by hash and material identity.

| # | Command (exact) | Observed result |
| --- | --- | --- |
| B1 | `cmake -S . -B build/fabro -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` | configure succeeded |
| B2 | `cmake --build build/fabro --parallel 4` | build succeeded; `libxverse_validation.a` and three test executables produced |
| T1 | `ctest --test-dir build/fabro -N -L unit` | `Total Tests: 107` |
| T2 | `ctest --test-dir build/fabro -N -L integration` | `Total Tests: 4` |
| T3 | `ctest --test-dir build/fabro -N -L validation` | `Total Tests: 3` |
| T4 | `ctest --test-dir build/fabro -L unit -j4` | `100% tests passed, 0 tests failed out of 107` |
| T5 | `ctest --test-dir build/fabro -L integration -j4` | `100% tests passed, 0 tests failed out of 4` |
| T6 | `ctest --test-dir build/fabro -L validation -j4` | `100% tests passed, 0 tests failed out of 3` |
| Q1 | `clang-format --dry-run --Werror` over the five current source/test files | clean (no diff) |
| Q2 | `clang-tidy -p build/fabro-static -checks=<8 enabled rules> --warnings-as-errors=* src/xverse/xcom/src/validation_session.cpp` | clean (no diagnostic) |
| Q3 | `gcovr --root . --filter src/ --json-summary-pretty --output reports/coverage-summary.json` | `line_percent 92.0`, `line_total 800` |
| Q4 | `nm -C -g --defined-only build/fabro/libxverse_validation.a` | enumerated; only `xverse::xcom::validation` and standard-library weak symbols |
| D1 | Doxygen build of `reports/doxygen/Doxyfile` with `WARN_AS_ERROR=YES` | 390 symbols, 0 audit issues, HTML/XML generated |

Internal evidence records (hash-bound to the current material identity `1c1d1a0b…`):

- `engineering/build-evidence.json` — `status: passed`, unit 107 / integration 4 / validation 3.
- `engineering/quality-evidence.json` — `status: passed`, clang-format, 8 clang-tidy rules, gcovr 92.0%.
- `engineering/doxygen-evidence.json` — `status: passed`, 390 symbols, source hashes `ec0bc335…` / `ac6b7018…`.
- `engineering/unit-static-evidence.json` — 38 unit-spec static checks dispositioned; status
  `worker_checks_complete_protected_checks_pending`.

No test-observation is reported as protected evidence: T1–T6 are worker-controlled runs, and
Q1–Q4/D1 are worker-controlled tool records. The 107 unit tests realise every unit-spec case ID
(TYP/DIA/PRM/REG/CLK/LIF/QUO/NOM/MIS/RP/HND/CON/ZEM/NOMUT) plus the seven F-02 transition cases;
the discovery gate confirms no unit case is absent from CTest.

## 4. Intended-use scenarios

The eight intended-use scenarios are canonical records under
`engineering/validation/scenarios/*.json`; each links to the stakeholder requirement it
demonstrates, and each is exercised by the named tests. Every canonical record now states,
in addition to its expected result, its **setup** (fixtures), its **observed** internal
worker test result with precise case/test IDs and counts, and its **limitation**; the table
below summarises the intended use and the exercising tests.

| Scenario | Intended use | Exercised by |
| --- | --- | --- |
| `T025-VS-001` | Nominal declared→armed→active→closing→closed session with zero emissions | `Validation.EndToEndNominalScenario`, NOM-01/02, LIF-01..04, ZEM-02 |
| `T025-VS-002` | Cross-domain validity resolved only through a declared mapping | NOM-03/04, CLK-06/07/08, `Integration.MappedValidityCrossDomainLifecycle` |
| `T025-VS-003` | Exactly-once, controller-scoped consumption incl. changed nonce | RP-01..05 |
| `T025-VS-004` | Controller-bound handle ownership and recreation isolation | HND-01..07, `Integration.GenerationRotationInvalidatesLiveHandle` |
| `T025-VS-005` | Zero normal-route emission and no nominal-path I/O | `Validation.ZEM_01`, `Validation.ZEM_03`, ZEM-02 |
| `T025-VS-006` | Finite quota/capacity boundaries with explicit exhaustion | QUO-01..06, `Integration.QuotaExhaustionThroughTransitionPath` |
| `T025-VS-007` | Non-mutating rejection and payload-free ordered diagnostics | NOMUT-01..06, DIA-01/05 |
| `T025-VS-008` | Deterministic concurrency and exactly-once mutation | CON-01..05, `Integration.IndependentControllerScopes` |

Per-scenario setup, observed result, and limitation are recorded in each canonical JSON
record (`engineering/validation/scenarios/T025-VS-00N.json`, fields `setup`, `observed`,
`limitation`). The observed results are the internal worker CTest run T1–T6 in §3 — 107/107
unit, 4/4 integration, and 3/3 validation tests passed, 0 failed — with each scenario's
exercising case/test IDs stated precisely in its record. These are internal worker
observations only; they are distinguished from the protected predecessor regression,
ThreadSanitizer/CodeQL, and intended-use acceptance steps, which remain pending and are
listed in §6 and §9.

## 5. Negative cases, including the F-01/F-02 repair evidence

Every negative case asserts state is unchanged, and the F-01/F-02 repair added executable evidence
for the previously unverified transition rejection branches:

- **Permit field mismatch matrix** — MIS-01..MIS-13 change exactly one bound field each and assert
  `PermitMismatch` with the specific `FieldLocator`; NOMUT-01/02 assert snapshot equality.
- **Replay / changed nonce** — RP-01..RP-05 assert exactly one success and deterministic
  `SessionAlreadyConsumed` / `PermitAlreadyConsumed` for repeats, including a changed nonce.
- **Clock failures** — CLK-02/03/04/05/07/08/09/11 assert `UnknownClock`, `ClockSourceFailure`,
  `ClockOutOfBounds`, `ClockRegression`, `MissingMapping`, `ToleranceExceeded`, and `ClockOverflow`
  distinctly; NOMUT-03 asserts authority state unchanged.
- **Handle failures** — HND-02..HND-06 assert `StaleHandle`, `ForeignHandle`, `RecreatedController`,
  `InvalidHandle`, and `SessionNotFound`; HND-07 asserts other sessions are untouched.
- **Lifecycle failures** — LIF-08..LIF-15 assert `TerminalState`, `InvalidTransition`, and
  `AlreadyApplied`; NOMUT-04 asserts state equality on each invalid repeat.
- **Exhaustion** — QUO-01..QUO-06 assert `QuotaExhausted` / `CapacityExhausted` with no partial
  application.
- **Transition rejection (F-02)** — seven executable tests through the real `SessionManager::transition`
  path: `TransitionRejectsPermitNotYetValidInDomain`, `TransitionRejectsPermitExpiredInDomain`,
  `TransitionRejectsPermitNotYetValidCrossDomain`, `TransitionRejectsPermitExpiredCrossDomain`,
  `TransitionRejectsActionNotAllowed`, `TransitionRejectsUndefinedAction`, and
  `TransitionExpiredWithUndefinedActionReportsPermitExpired`. Each asserts the **exact** primary
  `Result` and `diagnostic.size() == 1`, then compares a full before/after snapshot
  (`TransitionFixtureSnapshot`) covering the `ManagerSnapshot`, the addressed `SessionSnapshot`,
  and the monotonic and wall authority regression baselines. This is the executable proof that a
  rejected transition — including the cross-domain path of F-01 — leaves manager, session,
  consumed-permit/session sets, quota counters, live-session count, and **both authority baselines**
  byte-identical. The last case also proves the design §8.3 precedence that time validation precedes
  action validation.

The F-01 mechanics are also visible in the current source: the transition path resolves cross-domain
time through the documented non-mutating `TimeAuthority::convert_impl(..., commit_baseline=false)`
peek, while public `now()` / `convert()` keep their baseline-committing semantics; no public
signature changed.

## 6. Unavailable or not-executed checks

| Check | Status | Reason |
| --- | --- | --- |
| ThreadSanitizer (`STC-TIME-04`, `T025-M-SA-TSAN`) | **pending_protected_sanitizer_verification** | a sanitizer run could not be started in this Docker sandbox; not claimed as passed |
| CodeQL | **pending_protected_security_verification** | no CodeQL control ref or verifier is available to the worker; not claimed as passed |
| ASan/UBSan (`STC-06`) | not executed | no sanitizer execution in this environment |
| Predecessor regression in substantive mode (`--all` and every predecessor X-COM validator) | not executed | the restricted predecessor checkout is explicitly unavailable; no predecessor source exists in this sandbox |
| Protected/human acceptance, repository integration, source compatibility | not performed | protected host steps after Codex review |

## 7. Integration gaps

1. **No predecessor source.** The candidate is a standalone `xverse::xcom::validation` library that
   includes only the C++20 standard library. It neither includes nor recreates predecessor headers.
   How the new public types slot into the accepted repository is a protected host decision.
2. **FR anchor allocation unverified.** `FR-015`–`FR-020` and `FR-033` are preserved as trace
   anchors only. Their authoritative statements and per-requirement allocation are referred to
   protected review (see `engineering/trace.md` §8).
3. **REF-002 scope is partial.** `XVE-SYS-0144` (channel identity/access), the hard-real-time part of
   `XVE-SYS-0147`, `XVE-SYS-0152` (stimulation/Maestro triggers), and the durable part of
   `XVE-SYS-0154` are deferred; only the bounded local foundation is present.
4. **Concurrency is proven by deterministic stress, not by a race detector.** CON-01..CON-05 assert
   exact success counts and no corruption under a coarse-grained mutex, but thread-safety under a
   race detector remains a protected check.
5. **CMake integration is standalone.** The root `CMakeLists.txt` uses a provided GoogleTest helper
   and builds three labelled test executables; it is not the accepted repository build.

## 8. Exact limitations

- All checks here are **internal worker checks** in an isolated sandbox; they are not protected
  evidence and do not establish accepted X-COM delivery.
- Line coverage is 92.0% of 800 lines; the uncovered remainder is not analysed here as a defect.
- The only numeric figures reported are the observed test counts (107/4/3 = 114), the coverage
  percentage, and the Doxygen symbol count (390). No reliability, availability, or real-time target
  is asserted; none is derivable from the admitted packet.
- The permit identity is an FNV-1a 128-bit bookkeeping digest and handle authenticity is opaque
  issuance, not cryptography; no security claim is made.
- Normal-route emission count is asserted to be zero (ZEM-01/02/03) within this candidate only.
- The trace graph binds code targets to the exact current file SHA-256; any later source edit
  invalidates the affected links until regenerated.

## 9. Internal versus protected evidence

| Layer | Produced here | Authority |
| --- | --- | --- |
| Unit/integration/validation tests (T1–T6) | yes | internal worker observation only |
| Format/tidy/coverage (Q1–Q4), Doxygen (D1) | yes (preceding gates, hash-bound) | internal worker records only |
| Trace graph, measures, scenarios | yes | internal candidate artifacts |
| ThreadSanitizer, CodeQL, ASan/UBSan | **no** | protected verification, pending |
| Predecessor regression, repository integration, acceptance | **no** | protected host steps, not claimed |
