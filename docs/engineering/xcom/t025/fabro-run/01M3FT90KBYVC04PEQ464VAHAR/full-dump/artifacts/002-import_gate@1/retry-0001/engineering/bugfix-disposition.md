# T025 Focused Bug-Fix Disposition — R6 (and R5 handoff status)

- Review authority: `/opt/xcom-bugfix/terminal-review.json`
  (`review_id` `T025-CODEX-01M3FCEP6JMWSGDSN265K94DKD`, review round 2, verdict
  `changes_requested`).
- Repaired finding: **R6 only** — implementation, severity high, priority P1, blocking.
- Finding R5 (terminal export completeness) is an **artifact-handoff** defect of the host terminal
  collector and is **not** repairable or closable in the worker workspace; see §5.
- Classification: SANITIZED internal worker evidence. This is **not** accepted delivery, protected
  verification, or integration sign-off, and it does not refresh any requirement or protected
  evidence.

## 1. R6 root cause

`TimeAuthority` keeps a per-domain retained regression baseline and rejects a monotonic reading
below it with `Result::ClockRegression`. Public `now`/`convert` commit that baseline, but
`SessionManager::transition` resolved every time decision through the **non-mutating peek** paths
(`now_impl(..., commit_baseline=false)` and `convert_impl(..., commit_baseline=false)`) and never
advanced a baseline afterwards.

Observed (reproduced before the fix): `Arm` succeeded at `1500` and left the monotonic baseline
unset; a following `Activate` whose source read `1400` therefore saw no regression, succeeded,
became `active`, and consumed a second quota unit. The same held with a seeded baseline and through
a declared mapping.

## 2. Exact R6 fix

Two coordinated changes, in the allowed source/header only.

1. `TimeAuthority` (`validation_session.hpp`, `validation_session.cpp`)
   - New friend-accessible `advance_baseline(ClockDomainId id, Timestamp reading)`: acquires the
     authority mutex, finds the declared entry, and sets `baseline = reading` **only when**
     `!baseline.has_value() || reading >= *baseline`. It therefore never lowers a retained baseline
     and serializes with concurrent public `now`/`convert` calls. An undeclared (or re-declared)
     domain is ignored. Marked `@unitspec{T025-U-TIME}`.
   - `convert_impl` gained an optional out-parameter `Timestamp *destination_reading` that receives
     the destination-domain host reading used for the tolerance cross-check, so a mapped transition
     can advance the same destination baseline that public `convert` would.
   - Documentation of `now_impl`, `read_clock_locked`, `convert_impl`, the `SessionManager` friend
     grant, and the class notes updated to the new transaction contract.
2. `SessionManager::transition` (`validation_session.cpp`)
   - Resolution is unchanged and still non-mutating (peek), and it now captures
     `mapped_reading` for the mapped destination domain.
   - **After** every check passes and `ValidationSession::apply` returns `Result::Ok`, the manager
     calls `authority_.advance_baseline(now_domain, auth_now)` and, for a mapped resolution,
     `authority_.advance_baseline(validity_domain, mapped_reading)`.
   - Every rejection, `AlreadyApplied`, and terminal-state repeat returns before this point, so no
     baseline, session state, quota, or output changes.

Net contract: a successful lifecycle transition establishes or advances the retained monotonic
baseline(s) of the domain(s) it observed, so a later backward reading is
`Result::ClockRegression`; every rejected transition preserves authority baselines, session state,
quota, and diagnostic output.

## 3. Changed files

| File | Change |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` | `advance_baseline` declaration; `convert_impl` destination-reading out-parameter; updated time/manager contracts |
| `src/xverse/xcom/src/validation_session.cpp` | `advance_baseline` implementation; `convert_impl` captures destination reading; `transition` advances baselines only on `Result::Ok` |
| `tests/validation_session_tests.cpp` | Five focused R6 regression tests |
| `engineering/design.md` | Revision 3: §4.2, §7.5, §9.1 R6 transaction/concurrency contract |
| `engineering/implementation-notes.md` | Revision 4: §2.1 correction and new §2.5 R6 record |
| `engineering/bugfix-disposition.md` | This disposition (new) |

No public API entry point was added: both changes touch private members (`advance_baseline` is a
private method and `convert_impl` is a private method), so the public API surface and the
zero-emission boundary are unchanged. `CMakeLists.txt`, requirements, requirements JSON, ReqIF,
architecture component records, inspection reports, and all protected-evidence artifacts are
untouched.

## 4. Focused regression tests (GoogleTest; discovered by CTest)

Added to `tests/validation_session_tests.cpp`:

- `SessionManagerUnit.BUG_R6_UnseededSameDomain` — no prior baseline; a successful `Arm` at `1500`
  sets the baseline to `1500`; `Activate` at `1400` is `ClockRegression` with baselines, session
  snapshot, and quota byte-identical, while a later `Activate` at `1600` is accepted.
- `SessionManagerUnit.BUG_R6_SeededSameDomain` — the baseline is seeded to `1500` through public
  `now`; a successful `Arm` at `1600` advances it to `1600`; `Activate` at `1500` is
  `ClockRegression` with no state change.
- `SessionManagerUnit.BUG_R6_MappedDomain` — a mapped (`kWall -> kMono`) successful `Arm` advances
  **both** the source and destination baselines to `1500`; a backward source read and a backward
  destination read are each `ClockRegression` with no state change.
- `SessionManagerUnit.BUG_R6_RejectionPreservesState` — after a successful baseline-establishing
  `Arm`, time (`ClockRegression`), validity (`PermitExpired`), action (`ActionNotAllowed`,
  `UndefinedAction`), state (`InvalidTransition`), and quota (`QuotaExhausted`) rejections each
  leave manager snapshot, session snapshot, and both baselines unchanged; state stays `armed` and
  remaining operations stay `0`.
- `SessionManagerUnit.BUG_R6_ConcurrentAuthorityAccess` — eight public `now` readers run
  concurrently with the successful transition's deferred advance; all reads succeed, the retained
  baseline stays `1500` (never lowered), and the subsequent backward reading is `ClockRegression`.

## 5. R5 status (terminal collector — not closed here)

R5 concerns the host terminal collector contract
(`/home/jefferson/x-verse_fabric/pilots/xcom-t025/collect_terminal.py`, present read-only as
`/opt/xcom-input/collect_terminal.py`). It cannot be repaired or verified in the worker workspace;
this disposition makes **no** claim that R5 is closed. The worker package is kept complete so the
terminal collector can capture and verify it: all changed source/header/tests and both design notes
are present and hash-addressable, and `engineering/bugfix-disposition.md` is included. R5 closes only
after a fresh terminal capture verifies a complete final manifest with matching hashes and fails
visibly on any missing source, manifest, or required evidence.

## 6. Commands and results

All runs in `/workspace`, bounded to four jobs.

- `clang-format --dry-run --Werror` over the changed header, source, and test file: **clean**.
- `cmake -S . -B build/bugfix -G Ninja -DCMAKE_BUILD_TYPE=Debug` and
  `cmake --build build/bugfix -j 4`: **build succeeded** (`-Wall -Wextra -Wpedantic -Werror`).
- `ctest --test-dir build/bugfix -N`: **141 discovered** tests, including
  `SessionManagerUnit.BUG_R6_{UnseededSameDomain,SeededSameDomain,MappedDomain,RejectionPreservesState}`
  and `SessionManagerUnit.BUG_R6_ConcurrentAuthorityAccess`.
- `ctest --test-dir build/bugfix --output-on-failure -j 4 -R BUG_R6_`: **5/5 passed**.
- `ctest --test-dir build/bugfix --output-on-failure -j 4`: **141/141 passed** (unit 134,
  integration 4, validation 3).

Machine-readable evidence for this run is written by the checkpoint verifier to
`reports/bugfix-check.json`.

## 7. Remaining limitations

- Standalone sanitized candidate only: no protected predecessor source, integration, credentials, or
  network access.
- R5 remains **open / pending the host terminal collector**; no worker run can close it.
- ASan/UBSan, ThreadSanitizer, CodeQL, and protected regression were **not** executed here and are
  not claimed. The concurrency evidence is a functional multi-threaded unit stress test, not a
  sanitizer result.
- The concurrency guarantee is by construction (single authority mutex plus a never-lowering
  advance); no lock-free or lock-graph proof is offered.
- Requirements and unrelated earlier evidence remain historical and were not refreshed; no protected
  acceptance is claimed.
