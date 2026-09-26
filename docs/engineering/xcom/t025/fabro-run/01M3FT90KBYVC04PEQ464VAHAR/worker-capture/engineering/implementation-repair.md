# T025 Implementation Repair Record

- Source run (R1–R4 design repair): `01M3EYZ3203P78PJKG8HXCX6T3`
- Source run (implementation inspection repair): `01M3F969J5X7JHNK5C3JC9B4NP`
- Source candidate identity SHA-256: `bde5d11c16cb577882d118f3913b10bee0f0b7325b2f1c763f0223dd8e6c6a57`
- Terminal review SHA-256: `3aad4d719ef7ac46c7d7dc7171539406b55bd80968c4e1d6067579a1ad78b82b`
- Disposition repaired: `changes required; do not accept or integrate this candidate` (R1–R4), then
  `F-IMP-01`/`F-IMP-02` from the failed implementation inspection.

## Repaired findings (R1–R4, historical)

| Finding | Requirement | Code change | Regression tests |
| --- | --- | --- | --- |
| R1 same-domain transitions bypass the time authority | T025-SR-005 | `transition` resolves every time decision through `now_impl`/`convert_impl`; claim is cross-checked against the authoritative reading | ADV-R1a, ADV-R1b, ADV-R1c, ADV-R1d, NOMUT-07, TransitionRejects* |
| R2 independent managers issue identical identities | T025-SR-011 | `ManagerScope` in `ManagerConfig`; `register_controller(ControllerId, name)`; scope-first handle validation; `InvalidController` | HND-08, HND-09, HND-10, HND-11, ADV-R2a, ADV-R2b |
| R3 tolerance arithmetic admits maximally separated timestamps | T025-SR-003 | `unsigned_distance` computed from the signed ordering (exact over the signed 64-bit domain) | CLK-13, CLK-14, CLK-15, ADV-R3 |
| R4 rejected conversion advances the monotonic baseline | T025-SR-015 | destination baseline committed only after every conversion check passes | CLK-16, CLK-17, ADV-R4, NOMUT-07 |

## Public API changes (R1–R4)

- Added `using ManagerScope = std::array<std::uint8_t, 16>`; added `Result::InvalidController`
  (design §8.1 rank 25); added `action_mask_name(ActionMask)`.
- `ManagerConfig` gained a `scope` field (zero rejected at construction).
- `SessionHandle` gained a leading `scope` field.
- `SessionManager::register_controller` is now `Result register_controller(const ControllerId &id,
  std::string_view name)`; the per-manager `controller_sequence_` member was removed.

## Implementation inspection repair (F-IMP-01, F-IMP-02)

### F-IMP-01 — replay precedence over live-session capacity, transactional rejection

`SessionManager::consume` previously reserved a live-session slot (`allocate_slot_locked`) before
`PermitRegistry::try_consume`, so a replayed permit presented while the live-session table was full
reported `CapacityExhausted` (rank 24) instead of `SessionAlreadyConsumed`/`PermitAlreadyConsumed`
(ranks 21/22). The repaired order is:

1. permit/context field-by-field comparison (unchanged),
2. read-only replay probes — `is_consumed_session` then `is_consumed_permit` — so replay precedes
   capacity,
3. live-session slot allocation — full table reports `CapacityExhausted`,
4. atomic `PermitRegistry::try_consume` (the authoritative check-then-insert) only after a slot is
   available, then the bind.

Because the probes are read-only and the atomic insert runs only after a slot is available, an
unconsumed permit rejected on a full table is never persisted and both consumed sets stay
unchanged. The registry's own invariant ("no partial insertion on any failure") is unchanged.

### F-IMP-02 — `@unitspec` ownership of `precedence_rank`/`compare`

`precedence_rank(Result)` and `compare(Result, Result)` were tagged `@unitspec{T025-U-TYPES}` while
`engineering/unit-specifications/T025-U-DIAGNOSTIC.json` declares both among its interfaces and
`T025-U-TYPES.json` does not. Both symbols are re-tagged `@unitspec{T025-U-DIAGNOSTIC}`; the reviewed
unit-specification files are unchanged. Doxygen is regenerated and the per-symbol mapping is
re-verified (`symbol-audit.json` issues `[]`; both symbols list `T025-U-DIAGNOSTIC`).

## Regression coverage added (tests/validation_session_tests.cpp)

- `SessionManagerUnit.ReplayOnFullTableReportsSessionAlreadyConsumed` — full table, replayed
  session identity → `SessionAlreadyConsumed` (not `CapacityExhausted`), manager snapshot unchanged.
- `SessionManagerUnit.ReplayOnFullTableReportsPermitAlreadyConsumed` — full table, fresh session id
  carrying an already-consumed `PermitId` → `PermitAlreadyConsumed`, manager snapshot unchanged.
- `SessionManagerUnit.UnconsumedPermitOnFullTableRejectedTransactionally` — full table, unconsumed
  permit → `CapacityExhausted`; live sessions, consumed permits, and consumed sessions byte-identical
  before and after (no consumed identity is persisted).

## Verification performed (fresh re-run after repair)

- `python3 /opt/xcom-input/pilot_check.py build` (FABRO_CTEST_JOBS=4): passed — unit 129,
  integration 4, validation 3 discovered tests.
- `python3 /opt/xcom-input/pilot_check.py doxygen-scan`: passed — 395 symbols, `symbol-audit.json`
  issues `[]`, `precedence_rank`/`compare` map to `T025-U-DIAGNOSTIC`.
- `python3 /opt/xcom-input/pilot_check.py quality` (FABRO_CTEST_JOBS=4): passed — clang-format
  clean over the header, source, and all three test files; clang-tidy clean over the source with
  the eight declared rules; gcovr line coverage 92.4% (846 lines); `nm` symbol enumeration
  regenerated (`reports/public-symbols.txt` sha256
  `86c193ca570d7eb0dae2639b475eacf101ea5e0076f89f612e7038ece78f0e7b`).
