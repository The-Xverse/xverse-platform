# T025 Validation — Observed Internal Checks, Scenarios, and Limitations

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | validation |
| Revision | 1 |
| Classification | SANITIZED |
| Requirements authority | `engineering/requirements.md` (rev 1) |
| Design authority | `engineering/design.md` (rev 1) |
| Verification plan | `engineering/verification-plan.md` (rev 1, reviewed) |
| Source under test | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` (SHA-256 `a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20`), `src/xverse/xcom/src/validation_session.cpp` (SHA-256 `c3a62ab4c807b5df263ab8412d5c31201a84eebe70ae41e0aa93fb0928eec08f`) |
| Tests under test | `tests/validation_session_tests.cpp` (`eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb`), `tests/validation_session_integration_tests.cpp` (`547b9d0feb8b08b8c05495dbc4a2bbeb773e9897a2fa83301c68701b20052ce4`), `tests/validation_session_validation_tests.cpp` (`5ed87a0f82e6686f2bdcb606d72d53d077599bc5c904643de5c54f89671f2eb9`) |
| Internal material identity | `44efb24efc4f29756a247da9615c2a3caf7af8749d11fee2450398ea87845818` (recorded identically by build, quality, Doxygen, and unit-static evidence) |

### 1.1 Authority statement

Everything in this document is **internal worker evidence from an isolated Docker sandbox**. It is
*not* protected verification and *not* accepted delivery. Internal tests do not establish predecessor
regression, source compatibility, repository integration, human acceptance, or production readiness.
CodeQL and ThreadSanitizer were **not** executed here and are recorded as pending; nothing in this
document may be read as claiming they passed. No predecessor `--all` run, sanitizer run, or external
static-analysis service was executed in this sandbox.

## 2. Resume provenance — hash-bound implementation-repair checkpoint

This validation stage resumes failed run `01M3F969J5X7JHNK5C3JC9B4NP` from its hash-bound
implementation-repair checkpoint (`engineering/resume-provenance.json`,
`kind: terminal-inspection-resume`). The staged checkpoint was re-hashed during validation:

| Checkpoint control | Observed SHA-256 | Matches |
| --- | --- | --- |
| checkpoint manifest | `b2c7860d0e97f920715f3be371adaf014e9f3ad6e85bd8ce2ce5d2af3bcc6001` | `resume-provenance.json` `manifest_sha256` |
| checkpoint evidence | `39323d8eef571c267b22be32805644eef45bed7a67f043b7fc6116bdbd1f1b35` | `/opt/xcom-resume/checkpoint-evidence.json` |
| failed inspection report | `641c3ee35064b375deb8d25d0f1a22a07e37d5f7dce4f56b50921b27227864cd` | `resume-provenance.json` `invalid_inspection_sha256` |

The failed independent implementation inspection carried exactly two findings, both **minor** and both
**repaired before this stage** (`engineering/implementation-repair.md`):

- **F-IMP-01** (item IMP-01) — `SessionManager::consume` allocated a live-session slot before the
  registry's check-then-insert, so a replayed permit presented while the live-session table was full
  reported `CapacityExhausted` instead of `SessionAlreadyConsumed`/`PermitAlreadyConsumed`. Repaired so
  the read-only replay probes precede capacity and the atomic `try_consume` runs only after a slot is
  available. Three regression tests were added.
- **F-IMP-02** (item IMP-12) — `precedence_rank(Result)` and `compare(Result, Result)` carried
  `@unitspec{T025-U-TYPES}` while `T025-U-DIAGNOSTIC.json` owns them. Repaired by re-tagging both to
  `@unitspec{T025-U-DIAGNOSTIC}`; the reviewed unit-specification files were left unchanged.

The independently reviewed requirements and design and the validated unit specifications were
preserved byte-for-byte; a fresh independent implementation inspection then recorded `findings: []`
and `conclusion: pass` bound to the current header, source, and test hashes
(`engineering/inspections/implementation.json`). This validation stage therefore runs against the
post-repair bytes, and every trace link and measure addresses those hashes.

## 3. Observed internal commands and results

All commands were run from `/workspace`. The `unit`, `integration`, and `validation` CTest runs below
were re-executed during this validation stage against `build/fabro`; the build/quality/Doxygen records
were produced by the preceding controlled gates and are re-checked here by hash and material identity.

| # | Command (exact) | Observed result |
| --- | --- | --- |
| B1 | `cmake -S . -B build/fabro -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` | configure succeeded |
| B2 | `cmake --build build/fabro --parallel 4` | build succeeded; `libxverse_validation.a` and three test executables produced |
| T1 | `ctest --test-dir build/fabro -N -L unit` | `Total Tests: 129` |
| T2 | `ctest --test-dir build/fabro -N -L integration` | `Total Tests: 4` |
| T3 | `ctest --test-dir build/fabro -N -L validation` | `Total Tests: 3` |
| T4 | `ctest --test-dir build/fabro -L unit -j4` | `100% tests passed, 0 tests failed out of 129` |
| T5 | `ctest --test-dir build/fabro -L integration -j4` | `100% tests passed, 0 tests failed out of 4` |
| T6 | `ctest --test-dir build/fabro -L validation -j4` | `100% tests passed, 0 tests failed out of 3` |
| Q1 | `clang-format --dry-run --Werror` over the header, source, and all three test files | clean (no diff) |
| Q2 | `clang-tidy -p build/fabro-static -checks=<8 enabled rules> --warnings-as-errors=* src/xverse/xcom/src/validation_session.cpp` | clean (no diagnostic) |
| Q3 | `gcovr --root . --filter src/ --json-summary-pretty --output reports/coverage-summary.json` | `line_percent 92.4`, `line_total 846`, `branch_percent 71.3` |
| Q4 | `nm -C -g --defined-only build/fabro/libxverse_validation.a` | enumerated to `reports/public-symbols.txt`; only `xverse::xcom::validation` and standard-library symbols |
| D1 | Doxygen build of `reports/doxygen/Doxyfile` with `WARN_AS_ERROR=YES` | 395 symbols, symbol-audit issues `[]`, HTML/XML generated |

Internal evidence records (bound to the current material identity
`44efb24e…87845818` and the current source/test hashes):

- `engineering/build-evidence.json` — `status: passed`; discovered tests unit 129 / integration 4 / validation 3.
- `engineering/quality-evidence.json` — `status: passed`; clang-format over five files, 8 clang-tidy
  rules over `validation_session.cpp`, gcovr 92.4% of 846 lines; `reports/public-symbols.txt`
  `86c193ca570d7eb0dae2639b475eacf101ea5e0076f89f612e7038ece78f0e7b`.
- `engineering/doxygen-evidence.json` — `status: passed`; 395 symbols; source hashes
  `a8bbfb14…` / `c3a62ab4…`; `symbol-audit.json` `f6895430…` with issues `[]`.
- `engineering/unit-static-evidence.json` — 38 unit-specification static checks dispositioned; status
  `worker_checks_complete_protected_checks_pending`.

No test observation is reported as protected evidence: T1–T6 are worker-controlled runs, and
Q1–Q4/D1 are worker-controlled tool records. The 129 unit tests realise every reviewed unit case ID
(TYP/DIA/PRM/REG/CLK/LIF/QUO/NOM/MIS/RP/HND/CON/ZEM/NOMUT/ADV) plus the ten repair-regression tests;
no reviewed unit case is absent from CTest.

## 4. Intended-use scenarios

The eight intended-use scenarios are canonical records under
`engineering/validation/scenarios/*.json`; each links to the stakeholder requirement(s) it
demonstrates and to the exact unit/integration/validation tests that exercise it. Every canonical
record states its `setup`, its `observed` internal worker result with precise case/test IDs, and its
`limitation` in addition to `expected`.

| Scenario | Intended use | Exercised by |
| --- | --- | --- |
| `T025-VS-001` | Nominal declared→armed→active→closing→closed session with zero emissions | `Validation.EndToEndNominalScenario`, NOM-01/02, LIF-01..04, ZEM-02 |
| `T025-VS-002` | Cross-domain validity resolved only through a declared mapping | NOM-03/04, CLK-06/07/08, `Integration.MappedValidityCrossDomainLifecycle` |
| `T025-VS-003` | Exactly-once, controller-scoped consumption incl. changed nonce | RP-01..05 |
| `T025-VS-004` | Controller-bound handle ownership and recreation isolation | HND-01..07, `Integration.GenerationRotationInvalidatesLiveHandle` |
| `T025-VS-005` | Zero normal-route emission and no nominal-path I/O | `Validation.ZEM_01`, `Validation.ZEM_03`, ZEM-02 |
| `T025-VS-006` | Finite quota/capacity boundaries with explicit exhaustion | QUO-01..06, `Integration.QuotaExhaustionThroughTransitionPath` |
| `T025-VS-007` | Non-mutating rejection and payload-free ordered diagnostics | NOMUT-01..07, DIA-01/05 |
| `T025-VS-008` | Deterministic concurrency and exactly-once mutation | CON-01..05, `Integration.IndependentControllerScopes` |

The observed results are the internal worker CTest runs T4–T6 in §3 — **129/129 unit, 4/4 integration,
3/3 validation** tests passed with 0 failures — with each scenario's exercising case/test IDs stated
precisely in its record. These are internal worker observations only; they are distinguished from the
protected predecessor regression, ThreadSanitizer/CodeQL, and intended-use acceptance steps, which
remain pending and are listed in §6 and §8.

## 5. Negative cases, including the F-IMP-01/F-IMP-02 repair evidence

Every negative case asserts state is unchanged, and the repair added executable evidence for the two
failed inspection findings:

- **Permit field mismatch matrix** — MIS-01..MIS-13 change exactly one bound field each and assert
  `PermitMismatch` with the specific `FieldLocator`; NOMUT-01/02 assert snapshot equality.
- **Replay / changed nonce** — RP-01..RP-05 assert exactly one success and deterministic
  `SessionAlreadyConsumed` / `PermitAlreadyConsumed` for repeats, including a changed nonce.
- **Replay precedence over capacity (F-IMP-01)** — `ReplayOnFullTableReportsSessionAlreadyConsumed`
  and `ReplayOnFullTableReportsPermitAlreadyConsumed` fill the live-session table, present a replay,
  and assert `SessionAlreadyConsumed`/`PermitAlreadyConsumed` (not `CapacityExhausted`) with an
  unchanged manager snapshot; `UnconsumedPermitOnFullTableRejectedTransactionally` asserts a fresh
  permit on a full table yields `CapacityExhausted` with live sessions, consumed permits, and consumed
  sessions byte-identical (no consumed identity persisted).
- **Clock failures** — CLK-02/03/04/05/07/08/09/11 assert `UnknownClock`, `ClockSourceFailure`,
  `ClockOutOfBounds`, `ClockRegression`, `MissingMapping`, `ToleranceExceeded`, and `ClockOverflow`
  distinctly; CLK-16/17 and NOMUT-03 assert the authority baseline/state is unchanged on rejection.
- **Handle failures** — HND-02..HND-06 assert `StaleHandle`, `ForeignHandle`, `RecreatedController`,
  `InvalidHandle`, and `SessionNotFound`; HND-07 asserts other sessions are untouched; HND-08/09 cover
  cross-manager scope and recreated-controller isolation.
- **Lifecycle failures** — LIF-08..LIF-15 assert `TerminalState`, `InvalidTransition`, and
  `AlreadyApplied`; NOMUT-04 asserts state equality on each invalid repeat.
- **Exhaustion** — QUO-01..QUO-06 assert `QuotaExhausted` / `CapacityExhausted` with no partial
  application.
- **Transition rejection through the real manager path** — seven executable tests through
  `SessionManager::transition`: `TransitionRejectsPermitNotYetValidInDomain`,
  `TransitionRejectsPermitExpiredInDomain`, `TransitionRejectsPermitNotYetValidCrossDomain`,
  `TransitionRejectsPermitExpiredCrossDomain`, `TransitionRejectsActionNotAllowed`,
  `TransitionRejectsUndefinedAction`, and
  `TransitionExpiredWithUndefinedActionReportsPermitExpired`. Each asserts the **exact** primary
  `Result` and `diagnostic.size() == 1`, then compares a full before/after snapshot
  (`TransitionFixtureSnapshot`) covering the `ManagerSnapshot`, the addressed `SessionSnapshot`, and
  the monotonic and wall authority regression baselines.
- **Unit-specification ownership (F-IMP-02)** — `precedence_rank`/`compare` are now tagged
  `@unitspec{T025-U-DIAGNOSTIC}`; the Doxygen symbol audit maps both symbols to `T025-U-DIAGNOSTIC`
  and reports issues `[]` (`reports/doxygen/symbol-audit.json`). The reviewed unit specification was
  not changed.

## 6. Unavailable or not-executed checks

| Check | Status | Reason |
| --- | --- | --- |
| ThreadSanitizer (`STC-TIME-04`, `T025-M-SA-TSAN`) | **pending_protected_sanitizer_verification** | no sanitizer execution was performed in this Docker sandbox; not claimed as passed |
| CodeQL | **pending_protected_security_verification** | no CodeQL control ref or verifier is available to the worker; not claimed as passed |
| ASan/UBSan | not executed | no sanitizer execution in this environment |
| Predecessor regression in substantive mode (`--all` and every predecessor X-COM validator) | not executed | the restricted predecessor checkout is explicitly unavailable; no predecessor source exists in this sandbox |
| Protected/human acceptance, repository integration, source compatibility | not performed | protected host steps after Codex review |

## 7. Integration gaps

1. **No predecessor source.** The candidate is a standalone `xverse::xcom::validation` library that
   includes only the C++20 standard library. It neither includes nor recreates predecessor headers.
   How the new public types slot into the accepted repository is a protected host decision.
2. **FR anchor allocation unverified.** `FR-015`–`FR-020` and `FR-033` are preserved as trace anchors
   only. Their authoritative statements and per-requirement allocation are referred to protected review
   (see `engineering/trace.md` §8).
3. **REF-002 scope is partial.** `XVE-SYS-0144` (channel identity/access), the hard-real-time part of
   `XVE-SYS-0147`, `XVE-SYS-0152` (stimulation/Maestro triggers), and the durable part of
   `XVE-SYS-0154` are deferred; only the bounded local foundation is present.
4. **Concurrency is proven by deterministic stress, not by a race detector.** CON-01..CON-05 assert
   exact success counts and no corruption under a coarse-grained mutex, but thread-safety under a race
   detector remains a protected check.
5. **CMake integration is standalone.** The root `CMakeLists.txt` uses a provided GoogleTest helper and
   builds three labelled test executables; it is not the accepted repository build.

## 8. Exact limitations

- All checks here are **internal worker checks** in an isolated sandbox; they are not protected
  evidence and do not establish accepted X-COM delivery.
- Observed line coverage is 92.4% of 846 lines (branch 71.3%); the uncovered remainder is not analysed
  here as a defect, and no coverage threshold is asserted by the admitted packet.
- The only numeric figures reported are the observed test counts (129/4/3 = 136), the coverage
  percentages, and the Doxygen symbol count (395). No reliability, availability, or real-time target is
  asserted; none is derivable from the admitted packet.
- The permit identity is an FNV-1a 128-bit bookkeeping digest and handle authenticity is opaque
  issuance, not cryptography; no security claim is made.
- Normal-route emission count is asserted to be zero (ZEM-01/02/03) within this candidate only.
- The trace graph binds code targets to the exact current file SHA-256; any later source edit
  invalidates the affected links until regenerated.

## 9. Internal versus protected evidence

| Layer | Produced here | Authority |
| --- | --- | --- |
| Unit/integration/validation tests (T1–T6) | yes | internal worker observation only |
| Format/tidy/coverage (Q1–Q4), Doxygen (D1) | yes (controlled gates, hash-bound) | internal worker records only |
| Trace graph, measures, scenarios | yes | internal candidate artifacts |
| ThreadSanitizer, CodeQL, ASan/UBSan | **no** | protected verification, pending |
| Predecessor regression, repository integration, acceptance | **no** | protected host steps, not claimed |
