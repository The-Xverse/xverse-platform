# T025 Maintenance — Component Boundaries, API Use, Build, Invariants, Extension Points, Limitations

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | review (documentation owner) |
| Revision | 3 (independent replay of the reviewed terminal candidate) |
| Classification | SANITIZED |
| Source | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`, `src/xverse/xcom/src/validation_session.cpp` |
| Tests | `tests/validation_session_{tests,integration_tests,validation_tests}.cpp` |
| Companion document | `engineering/internal-review.md` |

### 1.1 Authority statement

This is internal, source-free maintenance guidance for the standalone worker candidate. It is not
accepted delivery and does not assert predecessor regression, source compatibility, protected
verification, or production readiness.

## 2. Component boundaries

All public types live in namespace `xverse::xcom::validation` and use only the C++20 standard
library; no predecessor header is included or recreated. The single header/source pair realises
seven logical components (each with an architecture record and a unit specification):

| Component | Public types | Unit spec |
| --- | --- | --- |
| `validation_types` | `Timestamp`, `Tolerance`, `SignedOffset`, `ClockDomainId`, `Generation`, `Nonce`, `ControllerId`, `SessionId`, `PermitId`, `PlanDigest`, `ActionMask`, `ClockKind`, `Action`, `LifecycleState`, `QuotaKind`, `Quota`, `Result`, `FieldLocator`, `TransitionOutcome`, `Tag`, `ManagerScope` | `T025-U-TYPES` |
| `validation_diagnostic` | `Diagnostic` (bounded ordered code sequence + optional locator) | `T025-U-DIAGNOSTIC` |
| `validation_time_authority` | `TimeAuthority` | `T025-U-TIME` |
| `validation_permit` | `Permit`, `PermitBuilder`, `SessionContext` | `T025-U-PERMIT` |
| `validation_permit_registry` | `PermitRegistry` | `T025-U-REGISTRY` |
| `validation_session` | `ValidationSession`, `SessionHandle`, `SessionSnapshot` | `T025-U-SESSION` |
| `validation_session_manager` | `SessionManager`, `ManagerConfig`, `ManagerSnapshot` | `T025-U-MANAGER` |

## 3. Public API use

- **`TimeAuthority`** (non-copyable/non-movable, one internal mutex): `declare_clock(id, source,
  kind, min, max)`, `declare_mapping(src, dst, offset, tolerance)`, `now(id, out)`,
  `convert(src, dst, value, out)`, `baseline(id)`, `domain_count()`, `mapping_count()`.
  `ClockSource` is `std::function<std::optional<Timestamp>()>`.
- **`PermitBuilder` → `Permit`**: setters for every bound field
  (`set_session_id`, `set_plan_digest`, `set_scenario/deployment/environment/tool/interface/target`,
  `set_nonce`, `set_validity`, `add_allowed_action`, `add_quota`) then `build()`. A built `Permit`
  is immutable with const accessors only and an FNV-1a 128-bit `permit_id()` (the content digest
  excludes the session identity, which is bound and tracked separately).
- **`PermitRegistry`** (non-copyable/non-movable): atomic `try_consume(controller, permit_id,
  session_id)` (check order session → permit → capacity); `is_consumed_permit`/`is_consumed_session`;
  `capacity`/`size`/`session_size`.
- **`SessionManager`** (non-copyable/non-movable; owns `TimeAuthority` + `PermitRegistry`):
  `register_controller(id, name)`, `advance_generation(controller)`,
  `consume(controller, permit, context, handle&)`,
  `transition(handle, action, now_domain, now_value, diagnostic&)`,
  `state`, `session_snapshot`, `last_diagnostic`, `manager_snapshot`, `capacity`,
  `emission_count` (always `0`), `time_authority()`.
- **`ValidationSession`**: `apply`, `state`, `is_terminal`, `remaining_quota`, `snapshot`,
  `permit_id`, `session_id`, `controller`, `generation`, `quota_index`.
- All result-returning public methods are `[[nodiscard]]`. Rejections are non-mutating and
  produce ordered, payload-free `Diagnostic` codes (capacity 8) following the declared
  `Result` precedence.

## 4. Build commands

From `/workspace` (toolchain: CMake ≥ 3.20, Ninja, GCC 12 / Clang, GoogleTest via the provided
`FabroGoogleTest.cmake` helper):

```
cmake -S . -B build/fabro -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/fabro --parallel 4
ctest --test-dir build/fabro -L unit -j4          # 129 tests
ctest --test-dir build/fabro -L integration -j4   #   4 tests
ctest --test-dir build/fabro -L validation -j4    #   3 tests
```

This reviewer independently reproduced the configure/build/test steps in `build/review-check`:
136 tests discovered, `100% tests passed, 0 tests failed` (unit 129 / integration 4 / validation 3).

Quality/static gates (as recorded in `engineering/quality-evidence.json`,
`engineering/doxygen-evidence.json`, and `engineering/validation.md` §3):

```
clang-format --dry-run --Werror <header> <cpp> <three test files>
clang-tidy -p build/fabro-static -checks=<8 enabled rules> --warnings-as-errors=* \
    src/xverse/xcom/src/validation_session.cpp
gcovr --root . --filter src/ --json-summary-pretty --output reports/coverage-summary.json
nm -C -g --defined-only build/fabro/libxverse_validation.a   # zero-emission symbol audit
doxygen reports/doxygen/Doxyfile                              # WARN_AS_ERROR=YES
```

The library target is `xverse_validation`; warnings are errors (`-Wall -Wextra -Wpedantic
-Werror`). Test executables are labelled `unit`, `integration`, and `validation` for CTest.

## 5. Invariants (do not break)

1. **Single time authority.** No code path compares raw timestamps from different domains;
   every time decision goes through `now`/`convert`/declared mapping.
2. **Distinct time outcomes.** `UnknownClock`, `ClockSourceFailure`, `ClockOutOfBounds`,
   `ClockRegression`, `ClockOverflow`, `MissingMapping`, `ToleranceExceeded` are distinct.
3. **Non-copyable owners.** `TimeAuthority`, `PermitRegistry`, `SessionManager` delete copy and
   move (asserted by `static_assert`). Destroy before any using thread exits.
4. **Exactly-once, controller-scoped consumption.** `try_consume` is one atomic check-then-insert
   critical section (session key → permit key → capacity); replay (including changed nonce) is
   rejected.
5. **Replay precedes live-session capacity (F-IMP-01).** In `SessionManager::consume`, the read-only
   replay probes (`is_consumed_session` then `is_consumed_permit`) run before slot allocation, and
   the atomic `try_consume` runs only after a slot is available, so a replay on a full table reports
   `SessionAlreadyConsumed`/`PermitAlreadyConsumed` (not `CapacityExhausted`) and an unconsumed permit
   on a full table is rejected transactionally without persisting any consumed identity.
6. **Validation before mutation.** Handle → context → time → action → quota all precede any state
   change; every rejection leaves session state, consumed sets, quota counters, and authority
   baselines byte-identical.
7. **Lifecycle table.** `declared→armed→active→closing→closed` plus terminal
   `expired`/`revoked`/`evidence_incomplete`; the constexpr transition table is exhaustive;
   terminal states admit no outgoing transition; safe repeats return `AlreadyApplied`.
8. **Payload-free diagnostics.** `Diagnostic` holds only enumerable codes + a numeric locator
   (asserted at compile time); no string/payload content.
9. **Zero normal-route emission.** No emission/transport/journal/persistence entry point;
   `emission_count()` is always `0`; nominal paths do no file/socket/env I/O.
10. **Bounded resources.** Every table/set/counter is finite and host-configured via
    `ManagerConfig`/constructor capacities, with explicit `CapacityExhausted`/`QuotaExhausted`.
11. **`@unitspec` ownership (F-IMP-02).** `precedence_rank(Result)`/`compare(Result, Result)` belong
    to `T025-U-DIAGNOSTIC`, not `T025-U-TYPES`; the ActionMask vocabulary helpers belong to
    `T025-U-TYPES`. Regenerating Doxygen must keep the per-symbol audit clean.

## 6. Extension points

- **New clock domains / mappings**: declare via `time_authority()` with additional capacities in
  `ManagerConfig.max_domains` / `max_mappings`.
- **New action bits**: extend `Action` within `kDefinedActionMask`; keep each enumerator a single
  atomic bit; update the `producing_action`/transition table and the PERMIT/LIF test matrix.
- **New quota kinds**: extend the closed `QuotaKind` set (currently `Operations`, `Evidence`);
  update `ValidationSession::quota_index` and the QUO cases.
- **Capacity tuning**: `ManagerConfig` fields (`max_sessions`, `max_domains`, `max_mappings`,
  `max_consumed_permits`, `max_consumed_sessions`, `max_superseded`, `max_controllers`).
- **New diagnostic precedence**: edit the `precedence_rank` mapping; keep the `Result` enum closed.

## 7. Limitations

- Standalone only: includes only the C++20 standard library; repository integration and source
  compatibility with the accepted predecessor are protected host steps.
- `PermitId` is FNV-1a 128-bit bookkeeping identity (not cryptographic); handle authenticity is
  opaque issuance against the manager table.
- Concurrency is proven by deterministic stress under a coarse-grained mutex, not by a race
  detector: ThreadSanitizer (`STC-TIME-04`), CodeQL, and ASan/UBSan are pending/not executed in
  this sandbox.
- Predecessor regression, FR-015–FR-020/FR-033 allocation confirmation, and the authoritative
  traceability matrix remain protected steps; the worker matrix is internal only
  (`pending_external`).
- Trace links pin code targets to exact file SHA-256; any edit to `validation_session.hpp`/`.cpp`
  invalidates the affected links and evidence hashes until regenerated.
- Line coverage is 92.4% of 846 lines (branch 71.3%); no reliability/availability/real-time target
  is asserted.
