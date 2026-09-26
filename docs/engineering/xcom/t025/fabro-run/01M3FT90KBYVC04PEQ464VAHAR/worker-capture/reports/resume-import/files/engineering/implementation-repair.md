# T025 Implementation Repair Record

- Source run: `01M3EYZ3203P78PJKG8HXCX6T3`
- Source candidate identity SHA-256: `bde5d11c16cb577882d118f3913b10bee0f0b7325b2f1c763f0223dd8e6c6a57`
- Terminal review SHA-256: `3aad4d719ef7ac46c7d7dc7171539406b55bd80968c4e1d6067579a1ad78b82b`
- Disposition repaired: `changes required; do not accept or integrate this candidate` (R1–R4).

## Repaired findings

| Finding | Requirement | Code change | Regression tests |
| --- | --- | --- | --- |
| R1 same-domain transitions bypass the time authority | T025-SR-005 | `transition` resolves every time decision through `now_impl`/`convert_impl`; claim is cross-checked against the authoritative reading | ADV-R1a, ADV-R1b, ADV-R1c, ADV-R1d, NOMUT-07, TransitionRejects* |
| R2 independent managers issue identical identities | T025-SR-011 | `ManagerScope` in `ManagerConfig`; `register_controller(ControllerId, name)`; scope-first handle validation; `InvalidController` | HND-08, HND-09, HND-10, HND-11, ADV-R2a, ADV-R2b |
| R3 tolerance arithmetic admits maximally separated timestamps | T025-SR-003 | `unsigned_distance` computed from the signed ordering (exact over the signed 64-bit domain) | CLK-13, CLK-14, CLK-15, ADV-R3 |
| R4 rejected conversion advances the monotonic baseline | T025-SR-015 | destination baseline committed only after every conversion check passes | CLK-16, CLK-17, ADV-R4, NOMUT-07 |

## Public API changes

- Added `using ManagerScope = std::array<std::uint8_t, 16>`; added `Result::InvalidController`
  (design §8.1 rank 25); added `action_mask_name(ActionMask)`.
- `ManagerConfig` gained a `scope` field (zero rejected at construction).
- `SessionHandle` gained a leading `scope` field.
- `SessionManager::register_controller` is now `Result register_controller(const ControllerId &id,
  std::string_view name)`; the per-manager `controller_sequence_` member was removed.

## Verification performed

- Full standalone build and all three CTest labels pass (`pilot_check.py build`).
- clang-format, clang-tidy, and gcovr pass (`pilot_check.py quality`).
- Doxygen (`WARN_AS_ERROR=YES`) and unit-specification links pass (`pilot_check.py doxygen`).
- Regression cases are added to `tests/validation_session_tests.cpp` and pass; the imported
  implementation fails these cases before the repair is applied (R1–R4 reproduce on the
  unmodified source).
