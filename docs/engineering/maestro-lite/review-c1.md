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
     - **Time.** Parsing and the XDL revalidation in the worker's Init grow with size. The Init request deadline
       (at most 5 s) and the bootstrap lease still bound them, and a slow Init still fails closed. The bound itself
       does not change the size of a real run, which is about 92 KB at 7 units.
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
