The repair is complete and verified. Summary of what was done:

**R6 fix (generation-bound commit):**
- `TimeAuthority` now assigns a fresh, never-reused monotonic **declaration generation** to every successful `declare_clock`; `ClockEntry` carries it.
- `now_impl`/`convert_impl` return the declaration generation alongside the observed reading (and destination reading) during the non-mutating peek.
- `advance_baseline(id, reading, declaration)` now refuses to mutate unless the domain still carries the exact generation that produced the observation, so a re-declaration landing between a transition's peek and its deferred commit can never seed the replacement declaration's baseline.
- `SessionManager::transition` captures the generations and passes them at commit; every rejection/`AlreadyApplied`/terminal repeat still returns before any mutation, preserving the rejection-side-effect guarantee.

**Deterministic tests added** (all discovered by CTest, 144 total, up from 141):
- `BUG_R6_ConcurrentRedeclaration`, `BUG_R6_MappedRedeclaration` — a documented, production-inert test interleaving probe places the re-declaration precisely between observation and commit. Confirmed against a throwaway pre-fix build: these two fail there and pass with the fix.
- `BUG_R6_PublicReadAfterRedeclare` — ordinary public reads after re-declaration.
- The four existing `BUG_R6_` regressions are unchanged.

**Docs:** `engineering/design.md` (rev 4), `engineering/implementation-notes.md` (rev 5), and a rewritten `engineering/bugfix-disposition.md`.

**Evidence:** `clang-format --dry-run --Werror` clean; clean build with `-Wall -Wextra -Wpedantic -Werror`; `ctest -R BUG_R6_ -j 4` → 8/8; full `ctest -j 4` → 144/144. The checkpoint `verify` gate passed and wrote `reports/bugfix-check.json` (`R6` fixed, `R5_status: pending_terminal`). R5 closure is not claimed.

```json
{"outcome":"succeeded","context_updates":{"stage":"repair"}}
```