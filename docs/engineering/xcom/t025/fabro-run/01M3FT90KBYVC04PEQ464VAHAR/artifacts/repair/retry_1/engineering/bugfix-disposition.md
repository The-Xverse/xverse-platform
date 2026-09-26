# T025 Focused Bug-Fix Disposition — R6 (and R5 handoff status)

- Review authority: `/opt/xcom-bugfix/terminal-review.json`
  (`review_id` `T025-CODEX-01M3FR5F7TGWQ043HZ7KYXW7HB`, review round 3, verdict
  `changes_requested`).
- Repaired finding: **R6 only** — implementation, severity high, priority P1, blocking,
  finding *"Concurrent re-declaration can cause a successful transition to commit the old clock
  reading into the replacement clock's baseline."*
- Finding R5 (terminal export completeness) is an **artifact-handoff** defect of the host terminal
  collector and is **not** repairable or closable in the worker workspace; see §5.
- Classification: SANITIZED internal worker evidence. This is **not** accepted delivery, protected
  verification, or integration sign-off, and it does not refresh any requirement or protected
  evidence. R6 is reported as **fixed in the candidate**, not accepted.

## 1. R6 root cause

Revision 4 made a successful `SessionManager::transition` commit the observations it relied on
(`TimeAuthority::advance_baseline` for the `now` domain and, for a mapped resolution, the validity
domain). Resolution is a non-mutating peek, and the commit is a **separate** authority critical
section, so a concurrent `declare_clock` of the same domain could land between them:

1. the transition peeks domain `D` and observes reading `R` under declaration `G`;
2. another thread re-declares `D` (`declare_clock` resets `D.baseline` and installs a replacement
   source, declaration `G'`);
3. the transition commits `(D, R)` through `advance_baseline(D, R)`, which only checked that the
   domain existed and did not lower its baseline — so it wrote the **old** declaration's reading
   `R` into the **replacement** declaration's baseline.

The observed failure mode is a stale reading committed across a declaration boundary. The
generation of the observation was available at peek time but was discarded, so the deferred commit
could not tell that its domain had been replaced.

## 2. Exact R6 fix

The deferred commit is **generation-bound** (the second option in the finding's requested action).

1. `TimeAuthority` (`validation_session.hpp`, `validation_session.cpp`)
   - `ClockEntry` gained `std::uint64_t declaration{0}`, and `TimeAuthority` gained a monotonic,
     never-reused `declaration_counter_`. Every successful `declare_clock` sets
     `entry->declaration = ++declaration_counter_` (a rejected declaration is unchanged and consumes
     no generation).
   - `now_impl` gained an optional out-parameter `std::uint64_t *declaration`; on `Result::Ok` it
     returns the reading domain's declaration generation. The read and the capture share one
     critical section.
   - `convert_impl` gained an optional out-parameter `std::uint64_t *destination_declaration`
     alongside the existing `destination_reading`; the destination declaration is captured from the
     same destination read used for the tolerance cross-check.
   - `advance_baseline(id, reading)` became
     `advance_baseline(id, reading, std::uint64_t declaration)`. It acquires the authority mutex and
     returns without mutating when the domain is undeclared **or** `entry->declaration !=
     declaration`; otherwise it applies the existing never-lower rule
     (`!baseline.has_value() || reading >= *baseline`). It is private and called only by
     `SessionManager::transition`.
2. `SessionManager::transition` (`validation_session.cpp`)
   - The non-mutating resolution now captures `now_declaration` for the `now` domain and
     `mapped_declaration` for the mapped validity domain.
   - After every check passes and `ValidationSession::apply` returns `Result::Ok`, the manager calls
     `authority_.advance_baseline(now_domain, auth_now, now_declaration)` and, for a mapped
     resolution, `authority_.advance_baseline(mapped_domain, mapped_reading, mapped_declaration)`.
   - Every rejection, `AlreadyApplied`, and terminal-state repeat returns before this point, so no
     baseline, session state, quota, or output changes on a rejected transition.
   - Between the observation and the commit, the success path invokes `before_commit_probe_` if it
     is set. It is an empty test-only interleaving probe, reachable only through the
     test-translation-unit friend `SessionManagerProbe`; production managers never set it, so the
     public surface, runtime behaviour, and zero-emission boundary are unchanged.

Net contract: a lifecycle transition commits an observation **only to the same clock declaration
that produced it**. A `declare_clock` that interleaves between the peek and the commit changes the
generation, so the stale advance is refused and the replacement declaration keeps its own baseline
(initially empty); it can only be established or advanced by an observation of the replacement.
Re-declaration also resets the retained baseline, and ordinary public `now`/`convert` after a
re-declaration are measured against the replacement's own baseline.

The declaration generation is orthogonal to the existing per-controller handle generation; no public
API entry point was added, and `CMakeLists.txt`, requirements, requirement JSON, ReqIF, architecture
component records, inspection reports, and protected-evidence artifacts are untouched. The test seam
is a private member plus one friend declaration inside the implementation header; it is documented
as test-only and has no production effect.

## 3. Changed files

| File | Change |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` | `ClockEntry::declaration`; `declaration_counter_`; `now_impl`/`convert_impl` declaration out-parameters; generation-checked `advance_baseline`; test-only `before_commit_probe_` + `SessionManagerProbe` friend; updated time/manager contracts and docs |
| `src/xverse/xcom/src/validation_session.cpp` | fresh generation on successful `declare_clock`; capture declaration in `now_impl`/`convert_impl`; generation check in `advance_baseline`; `transition` captures and passes the generations; invokes the empty test probe before the commit |
| `tests/validation_session_tests.cpp` | `SessionManagerProbe` test accessor and three new deterministic R6 regressions |
| `engineering/design.md` | Revision 4: declaration-generation binding in §4.2, §4.3, §7.5, §9.1 |
| `engineering/implementation-notes.md` | Revision 5: §2.1 correction and rewritten §2.5 R6 record |
| `engineering/bugfix-disposition.md` | This disposition (rewritten) |

## 4. Focused regression tests (GoogleTest; discovered by CTest)

Four R6 regressions from revision 4 are kept unchanged, and three deterministic cases are added to
`tests/validation_session_tests.cpp`:

- `SessionManagerUnit.BUG_R6_UnseededSameDomain` — a successful `Arm` at `1500` sets an empty
  baseline; `Activate` at `1400` is `ClockRegression` with baselines, session snapshot, and quota
  byte-identical; a later `Activate` at `1600` is accepted.
- `SessionManagerUnit.BUG_R6_SeededSameDomain` — a public-`now`-seeded baseline of `1500` is advanced
  to `1600` by a successful `Arm`; `Activate` at `1500` is `ClockRegression` with no state change.
- `SessionManagerUnit.BUG_R6_MappedDomain` — a mapped (`kWall -> kMono`) successful `Arm` advances
  **both** baselines to `1500`; a backward source read and a backward destination read are each
  `ClockRegression` with no state change.
- `SessionManagerUnit.BUG_R6_RejectionPreservesState` — time, validity, action, state, and quota
  rejections each leave manager snapshot, session snapshot, and both baselines unchanged.
- `SessionManagerUnit.BUG_R6_ConcurrentRedeclaration` — deterministic interleaving: the probe
  re-declares `kMono` after the transition's peek and before its deferred commit. The stale commit
  is refused (`baseline(kMono)` is empty), and ordinary public reads then serve the replacement
  (reading `1400` succeeds and seeds `1400`; `1300` is `ClockRegression`).
- `SessionManagerUnit.BUG_R6_MappedRedeclaration` — deterministic interleaving: the probe
  re-declares the mapped destination `kMono` after the tolerance read and before the deferred
  commit. The replacement destination baseline stays empty while the untouched source baseline
  (`kWall`) retains `1500`; the replacement then serves a public read of `1400`.
- `SessionManagerUnit.BUG_R6_PublicReadAfterRedeclare` — re-declaration clears the retained
  baseline, a public `now` of a lower reading (`1400`) succeeds and seeds the replacement, `1300`
  regresses against it, and a later successful transition commits to the replacement (`1450`; a
  subsequent `1440` is `ClockRegression`).

The two re-declaration cases were confirmed to be genuine regression guards: rebuilt against the
pre-fix `advance_baseline` (declaration check removed) they fail with
`baseline(kMono).has_value() == true` where the replacement declaration must be empty, and pass with
the fix. The check was performed in a throwaway copy outside the workspace; the workspace sources
were not modified for the experiment.

## 5. R5 status (terminal collector — not closed here)

R5 concerns the host terminal collector contract, supplied read-only at
`/opt/xcom-input/collect_terminal.py`. It cannot be repaired or verified from inside the worker, and
this disposition makes **no** claim that R5 is closed. The worker package is kept complete so the
terminal collector can capture and verify it: every changed source/header/test and both design notes
are present and hash-addressable, and `engineering/bugfix-disposition.md` is included. R5 closes
only after a fresh terminal capture verifies a complete final manifest with matching hashes and fails
visibly on a manifest that omits any independently required candidate or evidence path.
`reports/bugfix-check.json` records `R5_status: pending_terminal`.

## 6. Commands and results

All runs in `/workspace`, bounded to four jobs.

- `clang-format --dry-run --Werror` over the changed header, source, and test file: **clean**.
- `cmake -S . -B build/bugfix -G Ninja -DCMAKE_BUILD_TYPE=Debug` and
  `cmake --build build/bugfix -j 4`: **build succeeded** (`-Wall -Wextra -Wpedantic -Werror`).
- `ctest --test-dir build/bugfix -N`: **144 discovered** tests, including all seven
  `SessionManagerUnit.BUG_R6_*` cases.
- `ctest --test-dir build/bugfix --output-on-failure -j 4 -R BUG_R6_`: **8/8 passed**.
- `ctest --test-dir build/bugfix --output-on-failure -j 4`: **144/144 passed**
  (unit 137, integration 4, validation 3).
- Pre-fix control (throwaway copy): with the declaration check removed, `-R BUG_R6_` is
  **6/8 passed**, failing exactly `BUG_R6_ConcurrentRedeclaration` and
  `BUG_R6_MappedRedeclaration`; the fix restores 8/8.

Machine-readable evidence for the accepted run is written by the checkpoint verifier to
`reports/bugfix-check.json`.

## 7. Remaining limitations

- Standalone sanitized candidate only: no protected predecessor source, integration, credentials, or
  network access.
- The declaration generation is per-`TimeAuthority` and monotonic by construction; no formal proof
  of counter non-reuse or a lock-graph proof is offered (both are by construction under the single
  authority mutex).
- R5 remains **open / pending the host terminal collector**; no worker run can close it.
- ASan/UBSan, ThreadSanitizer, CodeQL, and protected regression were **not** executed here and are
  not claimed. The concurrency evidence is a deterministic interleaving plus a functional
  multi-threaded unit stress test, not a sanitizer result.
- Requirements and unrelated earlier evidence remain historical and were not refreshed; no protected
  acceptance is claimed.
