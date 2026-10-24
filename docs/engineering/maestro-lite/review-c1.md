# Review log: Maestro Lite increment C1 (persistence-configuration bound)

Candidate: `candidate/lite-c1-config-bound-20261024`, base main `64ff9d3eb` (tag `xverse-lite-v1.0.0-rc.1`).
Basis: thesis repository `specs/002-assured-aeb/design/wp11-unit-allocation.md` (WP-11, option C1, D-4a) and
`specs/002-assured-aeb/decisions.md` §J ("C1: a platform increment raises the persistence-configuration limit
enough for at least 7 units"; under the author's delegation of 2026-10-24, flagged for the author's review).
S1a finding 3 (`review-stabilization-s1a.md` 66–82) first recorded the bound and proposed raising it.
Findings are recorded before repairs. The maturity is an engineering candidate: not M1, not AEB evidence, not a
scientific result. No CARLA and no live run is used; every size below is an offline dry run.

## Findings

1. **The 64 KiB bound on the sealed persistence configuration: where it is enforced, why, what grows per unit,
   and the proposed bound (written at 10:56:26 2026-10-24).**
   - **Where it is enforced (two places, one Python and one native).**
     - **Python.** `src/xverse/maestro/bootstrap.py:1110-1118`, `BootstrapSession.persistence`: a
       `PersistenceInput` whose `private_bytes` are not `0 < len <= 65536` is refused with `ML-BOOT-PERSISTENCE`.
       The refusal comes before `_context` and before any native request, so the supervisor sequence is unchanged
       (pinned by `tests/thesis_lite/maestro/test_coverage_producers.py:169-172`).
     - **Native.** `src/xverse/maestro/native/bootstrap.c:226-227`, `birth()`: `sealed(fds[3],65536,&input_size)`.
       It applies to the sealed input of **every** helper role (1 to 5), in both builds (the legacy supervisor and
       `-DRUN_BOOTSTRAP`). The native side never reads a role-3 input: it checks the seals, the regular-file type
       and the size, then clears `FD_CLOEXEC` and passes the fd across exec. A refusal makes the request invalid,
       and the main loop then runs `cleanup()` and the supervisor exits.
   - **Bounds that look alike but do not apply to the persistence input (unchanged by C1).**
     - `bootstrap.c:129` (`initialize`) bounds the supervisor's own BC10/BC17 input at 65 536 and `malloc`s it.
       `bootstrap.py:205` (`ML-BOOT-INPUT-LIMIT`) and `runtime_admission.py:175` mirror it.
     - `catalog_launcher.c:179` and `launcher.py:261,281` bound the LC09 launch recipe.
     - `run_authority.c:298` and `affa_protocol.py:346,358` bound the AC17 authority recipe.
     - `controller.py:23,31` bounds the role-5 controller input (`MAX_PACKET`).
     - The outer persistence bound is `persistence.py:37`, `MAX_CONFIG = 1 << 20`. It is applied at encode
       (`persistence.py:269`), at `sealed_input_fd` (290), in the worker's `_read_input` (309) and at run
       admission (`runtime_admission.py:174`).
     - The persistence channel frames (`persistence.py:38`, `MAX_PACKET = 1 << 16`). The configuration never
       crosses that channel: it travels only as the sealed memfd, and the client keeps only its SHA-256 scope.
   - **Why the bound exists.**
     - The native seal dates from ML3-BOOTSTRAP10 (`a31d09367`; `ADR-ML3-BOOTSTRAP-0001.md`;
       `unit-specification-bootstrap10.md`). One generic size check covers the "sealed role input" of every
       helper birth. The role inputs were then the LC09 recipe (capped at 64 KiB, `unit-specification-launcher9.md:5`),
       the 64-byte gate input and the persistence configuration ("Helper input is unchanged LC09 sealed recipe or
       persistence configuration", `unit-specification-bootstrap10.md:19`).
     - The value equals the LC09 recipe cap and the BC10 "maximum private input 64 KiB". No record derives it for
       the persistence configuration. That configuration's own contract caps it at 1 MiB
       (`unit-specification-persistence8.md:5`).
     - The Python mirror came with increment 17 (`1e081a1ba`), after `review-affa17.md` finding 264: "Bound
       original private byte inputs before JSON/hashing". Its purpose is a stable refusal before any native
       mutation.
     - **Consequence.** On the bootstrap path, the effective bound on the persistence configuration is the generic
       64 KiB role-input seal. It is 16 times tighter than the persistence contract's own 1 MiB, and it was never
       sized for a unit count.
   - **What grows per unit: offline dry run at rc.1.**
     - **Method.** `tests/thesis_lite/maestro/test_persistence_config_bound.py::configuration` builds the encoded
       configuration through the admissions a run uses: validation, experiment plan, `prepare_lifecycle`,
       permits and approvals, `admit_schedule`, `admit_coverage`, `admit_collection` and the broker artifact. It
       starts no process. It was run with the rc.1 wheel installed (sha256 `cea5ced4…`) from this worktree:
       `evidence/c1/measure-sizes.py` and `measure-sizes-large.py` (results in `offline-sizes-rc1.json` and
       `offline-sizes-large-rc1.json`).
     - **Two shapes.**
       - `bench`: the S1a size-probe builder (`tools/bench/persistence_scaling`), for comparison with S1a.
       - `phase8`: a conservative Phase 8 stand-in modelled on the rc.1 Phase 7 live blueprint. Every unit
         declares the S1b controls (TERM grace 0.6 s, private stderr of 256 KiB, `nonce-marker`), the Phase 7
         action budgets, three environment names and the argument vector of the CARLA adapter, the longest
         Phase 7 unit. The run declares two concurrent freezes (CC-1), the retained-inputs artifact and a
         600-tick horizon. Unit names follow the WP-11 allocation.
     - **Calibration against the real Phase 7 shape.** `evidence/c1/phase7-calibrate.py` imports the rc.1 blueprint
       read-only (`xverse-blueprints` `99df3a4`) and encodes its 4-unit configuration offline:
       - 54 690 B for the nominal case at h400;
       - 55 354 B for `freeze-vcu` at h400;
       - 56 155 B for `freeze-vcu` at h600.

       The stand-in at 4 units and h600 is 57 256 B, 1 101 B (2.0 %) above the real shape, so it is conservative.

     | Units | `bench` h300 (B) | `bench` h100 (B) | S1a live probe (B) | `phase8` h600 (B) | `phase8` h300 (B) | Fits 65 536? (`phase8` h600) |
     | --- | --- | --- | --- | --- | --- | --- |
     | 4 | 49 577 | 48 767 | 49 805 | 57 256 | 56 055 | yes |
     | 5 | 59 633 | 58 819 | 59 075 | 68 751 | 67 550 | **no** |
     | 6 | 69 784 | 68 967 | 69 250 | 80 280 | 79 080 | no |
     | 7 | 80 012 | 79 193 | — | 91 959 | 90 758 | no |
     | 8 | 90 279 | — | 90 617 | 103 668 | — | no |
     | 10 | 111 109 | — | — | 127 376 | — | no |
     | 12 | 132 392 | — | — | 151 441 | — | no |
     | 16 | 175 888 | — | — | 200 635 | — | no |

     (4–7 units at op 0.2 s for `bench` and 0.25 s for `phase8`; 8–16 units at op 0.1 s, which B1 needs.)
     - **Per unit.** `bench` grows by 10 145 B per unit. Its base is about 9.0 KB, and the figures agree with the S1a
       live probes to within 1 %. The `phase8` stand-in grows by 11 568 B per unit, with a base of about 11.0 KB.
     - **Breakdown of the `phase8` per-unit growth.** XDL resources 6 488 B (instance, node, binding and five
       steps), coverage 2 224 B, approvals 965 B, bindings 915 B, schedule 709 B and collection 267 B. The coverage
       increment rises slowly with n (2 139, 2 214, 2 319 B), so the total is slightly super-linear.
     - **Consequence at rc.1.** The Phase 8 shape admits **at most 4 units**, not 5, which confirms the WP-11
       caveat "possibly 4 after S1b". The bench shape admits 5.
   - **Proposed bound: 262 144 B (256 KiB, `1 << 18`), for the persistence configuration (role 3) only.**
     - **Requirement (thesis §J).** At least 7 units of the Phase 8 shape, plus a margin. The stand-in needs
       91 959 B at 7 units and h600.
     - **Margin.** At 7 units, 262 144 B leaves 170 185 B (2.85 times the stand-in): about 14 more units at the
       stand-in increment. At 6 units it is 3.27 times.
     - **Unmodelled content.** The margin covers what the stand-in does not model: the WP-12 XDL system content
       (flows, endpoints, sensors, interfaces and the GA-28 relay declarations), longer Phase 8 names and
       arguments, and more faults per run. None of these is designed yet (WP-12).
     - **Structural maximum.** The platform admits at most 16 units, through the controller input
       (`controller.py:43`) and the AC17 authority input (`affa-bootstrap-v2.md`). The stand-in at 16 units is
       200 635 B, which fits with 61 509 B to spare. 256 KiB is the smallest power of two above it. With C1,
       this bound therefore no longer limits the unit count below the platform's structural maximum for this
       shape. B1 (the operation budget) and the other admission bounds limit it instead.
     - **Rejected: 131 072 B (128 KiB).** It leaves 39 113 B at 7 units, about 3.4 stand-in units. Unmeasured
       WP-12 content could exhaust that and force a second increment.
     - **Rejected: 1 MiB (the outer persistence bound).** No measured need supports it. It would also remove the
       defence-in-depth gap between the bootstrap seal and the worker's outer read bound.
     - **Other role inputs stay at 65 536 (roles 1, 2, 4 and 5).** So does the supervisor's own input. The native
       change is therefore role-specific, not a raise of the generic seal.
   - **Properties the bound protects, and how 262 144 B preserves them.**
     - **Native memory and DoS.** The native supervisor does not allocate, map or read a role-3 input, so the value
       changes no native allocation. The only native input it allocates is its own (`initialize`, at most 65 536),
       and that is unchanged.
     - **Worker memory.** `_read_input` preads `st_size + 1` bytes, bounded by `MAX_CONFIG` (1 MiB), and parses
       them with the strict JSON decoder. The new bound keeps the input at a quarter of that outer bound. The
       parent already holds the encoded bytes, which `encode_configuration` bounds by `MAX_CONFIG`.
     - **Time** (corrected per finding 4, L5). The worker's work grows with size, in two stages:
       - the strict parse and the configuration checks run before hello (`persistence_worker.py:246-270`), and
         only the caller's start-up deadline bounds them (`persistence.py:609`);
       - only `_load` runs inside the Init request, which is bounded at 5 s.

       Both still fail closed when late, within the bootstrap lease. The bound itself does not change the size of a
       real run, which is about 92 KB at 7 units.
     - **Fd passing and integrity.**
       - The configuration stays a sealed memfd (`F_SEAL_WRITE|GROW|SHRINK|SEAL`), passed as the fourth
         `SCM_RIGHTS` fd of the birth request.
       - The seal checks are unchanged, both native (`sealed()`) and in the worker (`_read_input`).
       - The fd count per birth stays 4.
       - The BS packet (128 B) and the 64 KiB persistence frames are unchanged, because the configuration never
         crosses a channel.
       - The SHA-256 scope still covers every byte.
     - **Fail-closed order.** The Python refusal still precedes `_context` and every native request. The native
       refusal still ends the supervisor through `cleanup()`. Both now use the same named value.
   - **ADRs and contracts affected.**
     - `ADR-ML3-BOOTSTRAP-0001.md` holds the generic role-input seal and is **amended** (amendment C1), before
       code.
     - `ADR-ML3-PERSISTENCE-0001.md`: its sealed-memfd input and its 1 MiB outer cap (`unit-specification-persistence8.md`)
       are unchanged. It gets a cross-reference note to amendment C1.
     - Unchanged and not amended, because their bounds are not the persistence input:
       - `unit-specification-bootstrap10.md` and `affa-bootstrap-v2.md` (the supervisor's own input);
       - `unit-specification-launcher9.md` (the LC09 recipe);
       - `ADR-ML3-SCHEDULER-0001.md` (64 KiB framing).
     - The rc.1 release record (`docs/releases/xverse-lite-1.0.md:201`, "caps a run at 5 units") is a frozen tag
       record and is not edited. The next release record must restate the capacity.
   - **Test consequences.**
     - `test_coverage_producers.py:171` sends `65537` bytes to show the Python refusal. Above the new bound that
       size would reach the native birth, so it moves to the bound plus one byte.
     - `test_coverage_producers.py:67` (`<= 65536`) moves to the named bound.
     - New cases cover:
       - the 6- and 7-unit stand-ins encoding below the bound;
       - the Python refusal at the bound plus one byte;
       - both native builds accepting a role-3 input of exactly the bound and refusing one byte more;
       - a non-storage role input still refused above 65 536.

2. **Implementation and installed-wheel verification of amendment C1 (written at 11:04:11 2026-10-24).**
   - **Commits.**
     - `cee23ae5a`: finding 1 and the offline builder.
     - `21b057271`: the ADR amendment, committed before `src/` was touched.
     - `bdfc20779`: the code and tests.
   - **Change (10 source lines).**
     - `bootstrap.py`: `MAX_PERSISTENCE_INPUT = 1 << 18`, which `BootstrapSession.persistence` now uses in
       place of `65536`.
     - `native/bootstrap.c`: `MAX_ROLE_INPUT 65536` and `MAX_STORAGE_INPUT 262144`. `birth()` seals
       `fds[3]` at `role==3 ? MAX_STORAGE_INPUT : MAX_ROLE_INPUT`.
     - Unchanged: the supervisor's own input (`initialize`, literal 65 536), `encode_bootstrap`, the launcher,
       authority and controller bounds, `MAX_CONFIG`, `MAX_PACKET` and `runtime_admission`.
     - Both native builds compile with `-Wall -Wextra -Werror -Wconversion -Wshadow`.
   - **Tests.** `test_persistence_config_bound.py`, 11 cases:
     - the named bound is equal on both sides, and the native file has one role-specific birth seal;
     - the 6- and 7-unit Phase 8 stand-ins (h600, op 0.25 s) are each above 65 536 and within half the bound;
     - the Python check refuses sizes 0 and bound + 1 with `ML-BOOT-PERSISTENCE`, with the sequence unchanged,
       no slot issued and no cancel;
     - the legacy and `RUN_BOOTSTRAP` supervisors each accept a role-3 input of exactly 262 144 B (born, not
       activated, reaped by drain, and the helper sent nothing);
     - each supervisor refuses 262 145 B: no child, cancelled, and the supervisor ends;
     - role 5 is accepted at 65 536 and refused at 65 537.

     `test_coverage_producers.py` now names the bound (lines 67 and 171).
   - **Mutation controls (not committed).**
     - With the native seal reverted to `MAX_ROLE_INPUT` for every role, both accept cases fail, and the legacy
       fixture's teardown reports the unacknowledged birth.
     - With `MAX_STORAGE_INPUT` for every role, the role-5 refusal case fails.
     - The source was restored, and the rebuilt wheel is byte-identical (`d4db5d74…`).
   - **Installed-wheel run.** One pytest process, wheel `d4db5d740fc1a45404b8612897eec15ad3322d1bb100ac0a318081b907ad52d2`
     built from `bdfc20779`, load 5.1–5.6. **311 passed, 0 failed, 0 skipped** in 145 s
     (`evidence/c1/related-suites-bdfc20779.log`).

     | File | Passed |
     | --- | --- |
     | `test_persistence_config_bound` | 11 |
     | `test_bootstrap` | 29 |
     | `test_bootstrap_late_birth` | 4 |
     | `test_bootstrap_launcher` | 19 |
     | `test_bootstrap_launch_unknown` | 3 |
     | `test_bootstrap_startup_ownership` | 5 |
     | `test_persistence` | 29 |
     | `test_composed_persistence_termination` | 6 |
     | `test_native_storage_faults` | 6 |
     | `test_run_bootstrap` | 9 |
     | `test_run_bootstrap_values` | 10 |
     | `test_boundary` | 52 |
     | `test_offline_boundary` | 4 |
     | `test_affa_native` | 17 |
     | `test_stabilization_s1b_native` | 34 |
     | `test_coverage_producers` | 33 |
     | `test_runtime_admission` | 40 |

     The full installed-wheel regression was not run here; the coordinator runs it.
   - **Sizes on the candidate.** `evidence/c1/offline-sizes-c1-bdfc20779.json` gives the same figures as at rc.1,
     within ±2 B of timestamp encoding. For `phase8` at h600: 57 257, 68 751, 80 280 and 91 959 B for 4 to 7
     units. The encoding is unchanged, so only the bound moved. 7 units now fit with 170 185 B to spare.
   - **Residuals (open, for the coordinator and the author).**
     - **R1. Live evidence.** No run with 6 or 7 units has been made. Whether such a run fits B1, the 8 192 request
       and event limits, the 90 s closure and the persistence frames that grow with the unit count (the 64 KiB
       `MAX_PACKET` replies and inventories) is untested. It belongs to D-4a, D-4b and the first such run.
     - **R2. Worker Init time.** The worker's Init (strict parse and XDL revalidation) at about 80–92 KB is
       unmeasured. The whole offline encode took 0.8–1.0 s at 6–7 units, at load about 4.8. This is an
       indicator, not the worker's time.
     - **R3. The stand-in is not the WP-12 plan.** WP-12 adds flows, endpoints, sensors and the relay. The
       stand-in does not model them, and the 2.85-times margin is sized for them, not measured against them.
       D-4a must re-measure the WP-12 candidate plan.
       - **Calibration** (extended per finding 4, L2). It has one point: the Phase 7 blueprint at 4 units
         (`phase7-calibration-rc1.json`). That point confirms the total (+2.0 %), not the per-unit slope that the
         7- and 16-unit figures extrapolate. D-4a must measure the slope as well.
       - **Superseded by the WP-12 re-measurement** (finding 5). The real Phase 8 configuration, measured with the
         platform builder, replaces the stand-in as the sizing basis.
     - **R4. Run admission is still looser.** `runtime_admission.validate_run_admission` still checks the
       persistence input against `MAX_CONFIG` (1 MiB). A configuration between 256 KiB and 1 MiB is therefore
       refused at bootstrap (`ML-BOOT-PERSISTENCE`), not at admission. This is unchanged from rc.1, where the gap
       began at 64 KiB, and it fails closed.
     - **R5. Release record.** The rc.1 release record still states a 5-unit cap. The next release record must
       state the new bound. For the Phase 8 shape the cap at rc.1 was really 4 units (finding 1).
     - **R6. Test coupling.** The size cases import the bench builder from `tools/bench/persistence_scaling`, so
       they run only from a checkout root, as the regression harness does.
       - **Host paths** (extended per finding 4, L3). The stand-in also uses host-specific absolute paths as
         byte-length proxies, and touches no file under them:
         - `PY`, the real `python3.13` under `sys.base_prefix`;
         - `CACHE`, the loop10 `.x-verse-build/cache` path;
         - `COMPAT` and `RUN_DIR`, synthetic paths.

         On another host the sizes shift by the length differences only.
     - **R7. Still to do for the increment.** Thesis §J asks for a full run, DV12 and a CAPA step. None is done
       here.

3. **Independent review of amendment C1 (written at 11:09:26 2026-10-24).** Reviewer: an independent Claude
   agent that did not write the increment. Scope: `cee23ae5a`, `21b057271`, `bdfc20779` and `27255b07d` on
   `64ff9d3eb`. **Verdict: PASS WITH NOTES.** No issue blocks the decisive full run.
   - **What was checked, and the result.**
     - **Installed wheel.** `sha256sum` of the cache wheel gives `d4db5d740fc1a45404b8612897eec15ad3322d1bb100ac0a318081b907ad52d2`.
       The installed `xverse/maestro` tree is byte-identical to `src/xverse/maestro` at `27255b07d` (`diff -rq`;
       `src/` is unchanged since `bdfc20779`). The only difference is `src/xverse/xcom`, which the wheel does not
       package (`pyproject.toml:36-45`).
     - **Rerun.** One pytest process on the installed wheel, `test_persistence_config_bound.py` and
       `test_coverage_producers.py`: **44 passed** in 29.7 s, load 3.6–5.0.
     - **Compile.** Both builds compile in a scratch copy with `-Wall -Wextra -Werror -Wconversion -Wshadow`, and
       also with `-Wsign-conversion` added. `role==3?MAX_STORAGE_INPUT:MAX_ROLE_INPUT` is an `int` widened to the
       `off_t` parameter of `sealed()`, and `role` is compared with a non-negative constant, so no conversion is
       narrowing or sign-changing.
     - **Call sites.** `birth()` has one caller (`native/bootstrap.c:338`), so the role-specific seal at
       `bootstrap.c:231` covers every helper birth in both builds. The remaining `sealed(…,65536,…)` calls are the
       supervisor's own input (`bootstrap.c:133`) and the AC17 recipe (`run_authority.c:298`). Neither is a role-3
       input.
   - **Properties the old bound protected (question 1): all preserved.**
     - **Native side.** For role 3 it only checks the seals, the regular-file type and the size
       (`bootstrap.c:61-65`, `231`), then passes the fd number as argv (`bootstrap.c:252`). Only roles 2 (exactly
       64 B, `bootstrap.c:245`) and 4 (at most 2 688 B, `bootstrap.c:205`) are read natively. The value
       therefore changes no native allocation, read or loop.
     - **Worker side.** `_read_input` (`persistence.py:307-316`) checks `st_size <= MAX_CONFIG` (1 MiB) and the
       seals before one `pread`.
     - **Transfer.** The memfd is written from exactly `private_bytes` and sealed (`persistence.py:288-304`), so
       the Python `len()` and the native `st_size` are the same quantity. Both checks are `0 < size <= 262 144`,
       and I found no Python/native disagreement.
     - **Channel.** `MAX_PACKET` (`persistence.py:38`), the 128-byte BS packet and the fd count per birth are
       untouched.
     - **Other role inputs.** They keep 65 536 or tighter: `launcher.py:261,281`, `catalog_launcher.c:179`,
       `affa_protocol.py:358`, `run_authority.c:298`, `controller.py:23`, `bootstrap.c:133`.
     - **Proportional work.** The only work that grows with the input is the worker's strict parse and `_load`,
       and the parent's re-parse in `PersistenceClient.__init__` (`persistence.py:481`). Both are linear and run
       on supervisor-authored bytes, so I found no DoS amplification.
   - **Measurement method (question 3): sound, with one limit (L2).**
     - **Builder.** The offline builder runs the same admissions the run uses and encodes through the production
       `encode_configuration`. The stand-in errs long on paths (the `COMPAT` path is longer than the real
       `/home/jefferson/xverse-compat`) and on per-unit controls.
     - **Weight of the XDL resources.** The per-part breakdown (`offline-sizes-c1-bdfc20779.json`) shows that the
       XDL `resources` are 57 % of the configuration at 7 units (52 572 of 91 959 B). WP-12 shape S-A adds about
       19 inter-unit flows with endpoints, the unbound element instances and their extensions
       (thesis `design/wp12-xdl-topology.md` §3.2 and the flow table). That content lands in `resources` and can
       plausibly add tens of KB.
     - **Choice of bound.** This supports rejecting 128 KiB, which leaves 39 KB at 7 units, and choosing 256 KiB.
       Rejecting 1 MiB on defence-in-depth grounds is reasonable. The "16 units fit" claim is stated for the
       stand-in shape only, and should stay that way.
   - **Issues.**
     - **M1 (MEDIUM, does not block the decisive full run): the accept side of the Python bound, and the composed
       role-3 path above 64 KiB, are untested.**
       - **The accept cases bypass the Python check.** They call `session.birth` directly
         (`test_persistence_config_bound.py:231-238`), with `b"x"` bytes that never reach the worker. The
         Python cases test only refusal (`:220-226`, sizes 0 and bound + 1). `test_coverage_producers.py:67,171`
         passes with any Python limit at or below the bound.
       - **A surviving mutant.** A mutant that keeps `<= 65536` in `BootstrapSession.persistence`
         (`bootstrap.py:1120`) while `MAX_PERSISTENCE_INPUT` stays `1 << 18` passes all 11 C1 cases. I did not run
         it, because the worktree is read-only to me; the conclusion follows from the test structure. The code as
         written is correct, because I read the line itself.
       - **What no test exercises.** `BootstrapSession.persistence` → `_spawn_role(3)` → native birth → worker
         `_read_input`, strict parse, `_load`, hello and Init with a real configuration above 65 536 B. The
         S1a/C1 evidence never runs the worker on more than 64 KiB.
       - **Proposed closure.** One composed installed-wheel case that drives `session.persistence()` through Init
         with a real configuration of about 70–92 KB, and records it as residual R8 until then. This should be
         done before D-4b or the first run with five or more units, not before the full regression.
     - **L1 (LOW, does not block): the ADR names the wrong role in its verification list.**
       - `ADR-ML3-BOOTSTRAP-0001.md:126` says "a role-4 input above 65 536 is still refused natively". The test
         uses role 5 (`test_persistence_config_bound.py:289-297`), as finding 2 says.
       - Role 5 is the right choice. A role-4 case would not discriminate, because `authority_input` refuses any
         size above 2 688 (`bootstrap.c:205`). The ADR line should say role 5.
     - **L2 (LOW, does not block): the calibration has a single point.** `phase7-calibration-rc1.json` checks the
       stand-in against the real Phase 7 blueprint at 4 units only. It confirms the total (+2.0 %), not the
       per-unit slope that the 7- and 16-unit figures extrapolate. The margin absorbs any plausible slope error,
       and R3 already requires D-4a to re-measure. R3 should name the slope explicitly.
     - **L3 (LOW, does not block): the size cases hard-code host paths.**
       - `test_persistence_config_bound.py:65,72-74` hard-codes host-specific absolute paths: `python3.13` under
         `sys.base_prefix`, the `/media/…/.x-verse-build/cache` path and a developer worktree path. They are used
         only as byte-length proxies, and no file under them is touched.
       - The cases also import `tools.bench` (R6). R6 should mention the paths too, or the paths should become
         fixed synthetic strings of the same length.
     - **L4 (LOW, does not block): no legacy-build case shows that role 1 stays at 64 KiB.**
       - Only the `RUN_BOOTSTRAP` build is checked for a non-storage role (role 5). Both builds share the one
         conditional at `bootstrap.c:231`, so a build-specific divergence would need an `#ifdef` mutant.
       - The LC09 launcher re-checks 65 536 after exec (`catalog_launcher.c:179`). No action is needed beyond
         noting it.
     - **L5 (LOW, does not block, editorial): the record overstates the 5 s bound.**
       - `review-c1.md` finding 1 ("Time") and `ADR-ML3-BOOTSTRAP-0001.md:119` attribute the worker's parse time
         to "the Init request deadline (at most 5 s)". The strict parse and the configuration checks run before
         the hello (`persistence_worker.py:246-270`), and only the caller's startup deadline bounds them
         (`persistence.py:609`). Only `_load` runs inside the Init request, which is at most 5 s
         (`persistence_worker.py:302,363-366`).
       - It still fails closed. Only the wording is imprecise.
   - **Residuals (question 5).**
     - **R1 to R7** are honest and correctly scoped. R4 is accurate: admission uses `MAX_CONFIG`, so a
       configuration between 256 KiB and 1 MiB fails closed at bootstrap.
     - **Missing:**
       - **R8.** The composed role-3 path above 64 KiB is untested (M1).
       - **The calibration slope.** It is unvalidated (L2), and could be folded into R3.
     - **Tests (question 4).** The native boundary cases discriminate as claimed: at the bound and the bound + 1
       for role 3 in both builds, and at 65 536 and 65 537 for role 5. The two stated native mutants would each
       fail at least one case. The Python boundary is discriminating only on the refusal side (M1).

4. **Coordinator disposition of finding 3 (written at 11:10:53 2026-10-24), recorded before any change.** It was made
   under the author's delegation of 2026-10-24, and it accepts nothing.
   - **M1: repair now.** Add a composed installed-wheel case. It drives `BootstrapSession.persistence()` through
     the native birth and the real worker's `_read_input`, strict parse, `_load` and Init, with a real 6- or
     7-unit stand-in configuration above 65 536 B. A mutant that keeps `<= 65536` in
     `BootstrapSession.persistence` must fail it. The mutant is run and then reverted.
   - **L1.** `ADR-ML3-BOOTSTRAP-0001.md` amendment C1 should name role 5, not role 4, in its verification list.
   - **L2.** R3 is extended: the calibration has one point, at 4 units. It confirms the total, not the per-unit
     slope.
   - **L3.** R6 is extended with the host-specific paths used as byte-length proxies
     (`test_persistence_config_bound.py` `PY`, `CACHE`, `COMPAT` and `RUN_DIR`).
   - **L4.** It is noted. No change.
   - **L5.** The time wording in finding 1 and in the ADR amendment is corrected:
     - the caller's start-up deadline bounds the worker's strict parse and configuration checks, which run
       before hello;
     - only `_load` runs inside the Init request, which is bounded at 5 s.
   - **Then.** Rebuild, run the C1 files and the bootstrap and persistence suites (one process), and record the
     result as finding 5.

5. **Repair of M1, and corrections L1, L2, L3 and L5 (written at 11:15:37 2026-10-24).**
   - **M1 repaired.** `test_persistence_config_bound.py::test_python_path_starts_the_worker_with_a_7_unit_configuration_above_64_kib`
     adds the `stand_in_stack` fixture, modelled on `test_bootstrap.boot_stack`: the legacy native supervisor,
     admitted for the stand-in's lifecycle digest, with a 100 s generation.
     - `BootstrapSession.persistence()` runs with the 7-unit `phase8` stand-in, 91 959 B (between 65 536 and the
       bound). It goes through the Python check, `_spawn_role(3)`, native birth and activation, and the real worker's
       `_read_input`, strict parse, `_load`, hello and Init.
     - The client is ready and `open`, with no cancel. Its scope is the SHA-256 of the full configuration, and its
       units are the stand-in's 7.
     - Teardown aborts and reaps the worker, then the supervisor. Every boundary is released, and stderr is empty.
   - **Mutant, run and reverted.** I set `bootstrap.py` to `<= 65536` while `MAX_PERSISTENCE_INPUT` stayed
     `1 << 18`, and rebuilt the wheel. The new case failed with `ML-BOOT-PERSISTENCE`, and the other 11 C1 cases
     passed, which confirms the reviewer's survival analysis. The source was restored (`git checkout`) and rebuilt.
   - **Corrections.**
     - **L1.** The ADR amendment's verification list now names role 5 (65 536 accepted, 65 537 refused) and the
       composed case.
     - **L2.** R3 now names the single calibration point and the unvalidated slope.
     - **L3.** R6 now names the host-path proxies `PY`, `CACHE`, `COMPAT` and `RUN_DIR`.
     - **L5.** The time wording is corrected in finding 1 and in the ADR: the start-up deadline bounds the parse
       and checks before hello, and the 5 s Init request bounds only `_load`.
     - **L4.** Noted. No change.
   - **Build and run.** The wheel was rebuilt from the worktree with `src/` unchanged since `bdfc20779`:
     sha256 `d4db5d740fc1a45404b8612897eec15ad3322d1bb100ac0a318081b907ad52d2`, byte-identical to finding 2.
     - **Run.** One pytest process over the same 17 files as finding 2, at load 4.2–4.8: **312 passed, 0 failed,
       0 skipped** in 150 s (`evidence/c1/related-suites-finding5.log`). That is the 311 of finding 2 plus the new
       composed case, so `test_persistence_config_bound` now has 12 cases.
     - The full installed-wheel regression is not run here.
   - **WP-12 re-measurement, supplied by the coordinator and checked read-only.**
     - **Source.** `xverse-blueprints` candidate `58d5726`, `automotive/assured-aeb/docs/review-wp12.md`
       finding 2 (the admission dry-run table), and `automotive/assured-aeb/docs/evidence/wp12-check-3aed505.json`
       (blob sha256 `a20fd449…`). I read the figures from the table at that commit.
     - **Full Maestro form** (every XDL document embedded):
       - 5 units: 146 458 B at op 0.29 s;
       - 6 units: 170 503 B at op 0.29 s;
       - 7 units: 182 302 B at op 0.20 s, or 182 273 B at op 0.25 s.
     - **Slim alternative:** 65 951, 75 605 and 87 866 B for 5, 6 and 7 units.
     - **Comparison.** The real full form is about twice the stand-in: 182 302 against 91 959 B at 7 units. Its
       increment from 6 to 7 units is 11.8 KB, close to the stand-in's 11.6 KB slope. The jump is in the base,
       through the WP-12 system documents, as R3 anticipated.
     - **The coordinator's decision, under the delegation:** the full form.
     - **Margin.** At 7 units, 262 144 B leaves 79 842 B, 1.44 times the full form. **The bound stands.** The
       2.85-times stand-in margin is superseded. The "16 units fit" figure of finding 1 holds for the stand-in shape
       only, not for the WP-12 full form.
   - **Residuals.**
     - R1, R2, R4, R5 and R7 are unchanged.
     - R3 is superseded by the WP-12 re-measurement above.
     - R6 is extended (L3).
     - **R8 (M1) is closed** by the composed case.
     - **R9 (new): later growth must be re-measured against the 256 KiB bound.** This applies to growth beyond 7
       units, or to documents added to the full form, such as more flows, faults or instances.
       - At the 6→7 increment of about 11.8 KB, the remaining 79 842 B is about 6 more units of WP-12 shape. Any
         added document consumes the same margin.
       - Any such change must re-run the platform-builder dry run and compare it with `MAX_PERSISTENCE_INPUT`
         before a run.
