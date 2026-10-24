# X-Verse Lite 1.0 release record: `xverse-platform`

**Status: release candidate rc.1, recorded 2026-10-24.** The step from rc.1 to the final release depends on the
S1d soak (section 9), which is pending and runs on the tagged revisions.

| Item | Value |
| --- | --- |
| Repository | `/home/jefferson/xverse-platform` |
| Code revision | main `a9db0ac39a858c0b2d341149042a8a97b7dcf393` (equal to `origin/main` on 2026-10-24) |
| Release commit | the commit on `release/xverse-lite-1.0-rc.1` that adds this record; its parent is `a9db0ac39`, and it changes documentation only (this record and `docs/engineering/maestro-lite/README.md`) |
| Tag | `xverse-lite-v1.0.0-rc.1`, naming the release commit (created and pushed separately, not by this commit) |
| Package | `xverse-xdl` 0.4.0 (`pyproject.toml`); console scripts `xdl`, `xverse-argus` |
| Companion records | `docs/releases/xverse-lite-1.0.md` in `xverse-compat` and in `xverse-blueprints` |

## 1. What X-Verse Lite 1.0 is

X-Verse Lite 1.0 is the first engineering-integration baseline of X-Verse Lite across three repositories:
`xverse-platform`, `xverse-compat` and `xverse-blueprints`. It declares an experiment in XDL Lite, runs owned
units and one unchanged legacy unit under Maestro Lite with deterministic fault injection and flow-level
communication evidence, records the run in Argus Lite, and drives a bounded live CARLA 0.9.15 closed loop
through the compatibility adapters and the Lite blueprint. It is engineering integration only. It is not
AEB validation, not M1 (Phase 8 records a declared non-M1 limit, AD-21), not X-Verse fitness for purpose
(that remains the Phase 8 P8-T06 review), and not a scientific result. `RF-2026-08-30-v6` and
`AEB-EXPERIMENT-2026-08-30-v2` are unchanged by it.

## 2. Components in this repository

| Component | Phase | Location and entry points |
| --- | --- | --- |
| XDL Lite | 1 | `src/xverse_xdl/`. CLI `xdl validate`, `xdl normalize`, `xdl experiment compile`, `xdl version` (`cli.py`). API `compile_experiment_plan`, `compile_experiment_sources`, `compile_experiment_files` (`experiment_plan.py`); `validate_sources` (`validate.py`); `ExecutionPermit` (`lifecycle.py`). Schemas and profiles under `xdl/schemas`, `xdl/profiles` |
| Argus Lite | 2 | `src/xverse/argus/`. Read-only CLI `xverse-argus {verify\|export} <run-root> [--format json\|jsonl]`. API `read_run`, `read_records` (the verified-prefix reader added in S1a) |
| Maestro Lite | 3, S1 | `src/xverse/maestro/`. Lifecycle projection `prepare_lifecycle` (`projection.py`); admission of schedule, coverage and collection (`schedule_plan.admit_schedule`, `coverage.admit_coverage`, `collection_plan.admit_collection`); the trusted-host run path `_OriginalRuntimeRun` (`runtime_entry.py`). The readiness-reviewed `RuntimeService` path (`runtime_service.py`) stays closed to the blueprint (thesis DLG-7) |
| Maestro native helpers | 3, S1b | `src/xverse/maestro/native/`: `bootstrap.c`, `run_authority.c` (AF17 run authority, including TERM and the nonce-marker QUERY from S1b), `lease_guard.c`, `catalog_launcher.c` (LC09, tests only; refuses the S1b declarations, DR-8) |
| Persistence | 3, S1a | `persistence.py`, `persistence_worker.py`: the sealed persistence worker with the verified-prefix cache for the Argus mirror and the M3 journal (S1a) |
| Coverage | 3, S1a-6 | `coverage.py`: lifecycle coverage assessment, including the DR-20 Stop-bracket discharge |
| Closure | 3, S1a | `run_closure.py`, `terminal_runtime.py`, `evidence.py` (bounded per-element encoding, S1a-3) |
| Fault injection | 5 | `src/xverse/faults/` (`scheduler.py`, `resolve.py`, `vocabulary.py`, `evidence.py`, `boundary.py`) |
| Flow runtime | 6 | `src/xverse/flows/` (`binding.py`, `clock.py`, `receiver.py`, `run.py`, `timebase.py`); mirrors the C++ X-COM loopback rules and does not activate the core |

Engineering records: `docs/engineering/maestro-lite/` (ADRs `ADR-ML3-*`, review logs `review-*.md`, evidence
under `evidence/`), `docs/engineering/xdl-lite/`, `docs/engineering/argus-lite/`, `docs/engineering/faults-lite/`.

## 3. Phase and increment history

Dates are WEST. Merge revisions are `main` first-parent commits. Acceptance records are in the thesis
repository unless a platform path is given.

| Step | Repository: merge | Merged | Accepted | Acceptance record |
| --- | --- | --- | --- | --- |
| Phase 1 XDL Lite | platform: candidate `0d7ebdde4`, acceptance record `c1fd213cd` | 2026-10-01 | 2026-10-01, author ("i accept") | `specs/021-thesis-lite-program/fabro/admission/runs/01M3VYDPRZTZKBZ2S0616VAHQ6/acceptance-decision.json`; platform `docs/engineering/xdl-lite/acceptance-decision.md` |
| Phase 2 Argus Lite | platform: `c2997c0f8` (fast-forward; pushed 2026-10-03) | 2026-10-02 | 2026-10-02, author ("go") | `specs/023-argus-lite-evidence/review/closure-assessment-20261022.md` (ledger reconciliation) |
| Phase 3 Maestro Lite, increments 17 and 18 | platform: `e65965a95`, record `557619e0c` | 2026-10-20 | 2026-10-20, author (findings 392, 411) | platform `docs/engineering/maestro-lite/README.md`; canonical note, Note 23 |
| Phase 3 Maestro Lite, increment 19 | platform: `63f5cb8c7`; documentation `0a498bb7e`, `744b66f9c` | 2026-10-22 | 2026-10-22, under the author's delegation (E3, E4; finding 476) | `specs/024-maestro-lite-lifecycle/review/t07-acceptance-package-20261022.md` |
| Phase 4 compatibility descriptors | compat: `ee9db2a` | 2026-10-22 | 2026-10-22, author's goal (bounded partial delivery) | `specs/003-thesis-lite-artifact-adapters/review/t07-acceptance-package-20261022.md` |
| Phase 5 fault injection | platform: `2d556ff24` | 2026-10-22 | 2026-10-22, delegation (DLG-3, DLG-4) | `specs/026-lite-fault-schedules/review/acceptance-package-20261022.md` |
| Phase 6 communication | platform: `8b3d8c8e8`; compat: `39ae980` | 2026-10-22 | 2026-10-22, delegation (DLG-5, DLG-6) | `specs/027-lite-flow-runtime/review/acceptance-package-20261022.md` |
| Phase 4b CARLA client adapters | compat: `6271ac2` | 2026-10-22 | 2026-10-22, delegation (DLG-1, DLG-2) | `specs/028-lite-carla-client-adapters/review/acceptance-package-20261022.md` |
| Phase 7 live smoke check | blueprints: `e7a6ebc`; compat: `39d31fa` | 2026-10-23 | 2026-10-23 about 07:39, author (AD-01) | `specs/001-thesis-lite-compatibility-smoke/review/acceptance-package-20261023.md` |
| S1a persistence scaling, cancel closure | platform: `b28a2aacf` | 2026-10-23 | 2026-10-23 about 16:15, author ("i accept") | `specs/029-lite-stabilization/review/acceptance-package-s1a-20261023.md` |
| S1c-1 | compat: `25e4e1f`; blueprints: `126a80b` | 2026-10-23 | 2026-10-23 about 16:15, author | `acceptance-package-s1c1-20261023.md` |
| S1c-2a blueprint horizons | compat: `bb07492`; blueprints: `6ac7703` | 2026-10-23 | 2026-10-23 about 18:40, author ("I accept all") | `acceptance-package-s1c2a-20261023.md` |
| S1a-2 cancel on a busy connection | platform: `5aadd358c` | 2026-10-24 04:31 | 2026-10-24 about 04:14, author | `acceptance-package-s1a2-20261023.md` |
| S1b graceful stop, private stderr, nonce-marker readiness | platform: `a6cc0c9f8` | 2026-10-24 04:31 | 2026-10-24 about 04:14, author | `acceptance-package-s1b-20261023.md` |
| S1a-3 bounded terminal encoding, with S1a-5 (cancel past the lease, DR-13) and the stack load repairs DR-15 to DR-17 | platform: `ee91697a4` | 2026-10-24 04:31 | 2026-10-24 about 04:14, author | `acceptance-package-s1a3-20261023.md` |
| S1a-6 Stop-bracket health slot (DR-20) | platform: `a9db0ac39` | 2026-10-24 06:52 | repair successor under the author's acceptance of 2026-10-24 | `acceptance-package-s1a6-s1d-20261024.md` |
| S1c-2 live harness after S1b, soak tooling | compat: `e05d467`; blueprints: `aceb5ae` | 2026-10-24 07:14 | under the author's acceptance of 2026-10-24 | `acceptance-package-s1c2-20261024.md` |
| S1d soak health-check repair (DR-21) | compat: `f0f31f9`; blueprints: `9b21d5b` | 2026-10-24 08:09 | repair successor under the author's acceptance | `acceptance-package-s1a6-s1d-20261024.md`; compat `review-s1c.md` findings 57–59 |
| S1d2 operator-signal stop (finding 60) | compat: `30446f6`; blueprints: `5fa8bcb` | 2026-10-24 08:48 | repair successor under the author's acceptance | `acceptance-package-s1a6-s1d-20261024.md`; compat `review-s1c.md` findings 60–62 |

The "S1a-n" identifiers of the ADR amendments are per ADR and do not map one-to-one to increments: amendment
S1a-4 (ADR-ML3-EVIDENCE-0001) belongs to increment S1a-3, and "S1a-6" names both an ADR-ML3-AFFA-0001 note of the
stack load repairs (DR-15, DR-16) and the ADR-ML3-EVIDENCE-0001 amendment of increment S1a-6 (DR-20).

## 4. Cross-repository compatibility set

| Element | Value |
| --- | --- |
| Platform main | `a9db0ac39a858c0b2d341149042a8a97b7dcf393` |
| Compat main | `30446f6c7f234ec600398ba5db6c57846210c772` (the last change to compat `src/`, `tests/` or `xdl/` is in `e05d467`) |
| Blueprints main | `5fa8bcba3545e5675e512baf5baa5738bac42599` |
| Release commits | one documentation-only commit on `release/xverse-lite-1.0-rc.1` in each repository, on top of these mains; each is named by the tag `xverse-lite-v1.0.0-rc.1` |
| Platform-API lock (`xverse-compat/platform-api.lock.json`) | `platformRevision` `a9db0ac39a858c0b2d341149042a8a97b7dcf393`; surface `treeSha256` `ce779e57d888b61b2a40fa7b4a05999ad900a33e48fc71e340a082b902fb43cd` (26 files: `pyproject.toml`, `src/xverse_xdl`, `xdl/profiles`, `xdl/schemas`); `xverse-xdl` 0.4.0 |
| Pinned live environment | `xverse-lite-live-20261022` on loop10, rebuilt from `a9db0ac39`; wheel `xverse_xdl-0.4.0-py3-none-any.whl` SHA-256 `cea5ced404c277157df9496086fd4a0a8f011c58e01c8e7d659fc2fb5b53cddf` (compat `review-s1c.md` finding 55). The same digest is recorded for the S1a-6 decisive run (`configuration.json` of `platform-regression-20261024g-1`) and in platform S1b-log finding 33 |
| CARLA | server 0.9.15 (binary `sha256:1da989e4…`); client wheel `carla-0.9.15-cp310` `sha256:61449e33…4ad6` on system CPython 3.10.12 (DLG-1) |

## 5. Verification and evidence

### 5.1 Decisive full installed-wheel runs and DV12 verdicts

Every run is under `docs/engineering/maestro-lite/evidence/affa19/`, with `dv12-gate-verdict.json`,
`configuration.json`, `load-samples.jsonl` and `SHA256SUMS`. DV12 is `scripts/validate_maestro_acceptance_evidence.py
--scope code`. All verdicts read `accepted_as_evidence: true` with no blockers. The one skip is the lane-admission
test (`MAESTRO_LANE_PROPOSAL` unset).

| Step | Run | Tested head | Passed / skipped | Max sampled load | DV12 code SHA-256 | Wheel SHA-256 | CAPA step |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 3 (inc. 19) | `platform-regression-20261022a-1` | `af9bd3c72` | 2250 / 1 | 8.29 | `f25a295d…` | `94fe115e…` | 5, 6 |
| Phase 5 | `faults-lite/platform-regression-20261022g-2` | `476ed1f3f` | 2297 / 1 | 8.51 | `80a43a3a…` | `eaeb095b…` | 7 |
| Phase 6 | `flows-lite/platform-regression-20261022h-1` | `74db77112` | 2397 / 1 | 5.49 | `8a3e6740…` | `3bbd2b1b…` | 8 |
| S1a | `stabilization-s1a/platform-regression-20261023a-1` | `d04bc7937` | 2417 / 1 | 7.94 | `2a337467…` | `6ff39689…` | 9 |
| S1a-2 | `stabilization-s1a2/platform-regression-20261023b-1` | `d8b44719c` | 2423 / 1 | 8.07 | `33b2d1fd…` | `b253356a…` | 10 |
| S1b | `stabilization-s1b/platform-regression-20261023c-1` | `78ed2f0e6` | 2524 / 1 | 6.31 | `2d17c186…` | `d38bc527…` | 11 |
| S1a-3 | `stabilization-s1a3/platform-regression-20261023d-1` | `2497b5a4d` | 2886 / 1 | 5.11 | `868a21b6…` | `d0fed3d1…` | 12 |
| S1a-5 | `stabilization-s1a3/platform-regression-20261024e-1` | `5ae2a3da3` | 2890 / 1 | 5.29 | `a970c8d5…` | `2efbd893…` | 13 |
| Stack load (DR-15 to DR-17) | `stabilization-s1a3/platform-regression-20261024f-1` | `c6dad58d8` | 2920 / 1 | 5.55 | `998b51af…` | `a54844d3…` | 14 |
| S1a-6 (release head) | `stabilization-s1a3/platform-regression-20261024g-1` | `2fc20ef12` | 2945 / 1 (2946 collected; 2632 s) | 6.69 | `69118482…` | `cea5ced4…` | 15 |

Phases 1 and 2 were verified before this driver existed: Phase 1 by 147 feature tests and 295 integration tests
(acceptance decision), Phase 2 by 579 platform tests and 284 installed-wheel owned tests (closure assessment).
Runs judged under the increment-19 ruling (finding 469): a run that fails only while sampled load exceeds 10 is an
observation, not a regression signal.

### 5.2 CAPA register steps

Registers are under `evidence/affa19/capa-*/`, verified by `verify-capa-register-20261023.py` with parent
preservation checked by `affa17/check-capa-parent-preservation-20261019.py`. Mode `OBSERVE_ONLY`. Every step
records `effectiveness_demonstrated: false` and `independent_cause_confirmation: false`.

| Step | Directory | Register SHA-256 | Records / bindings |
| --- | --- | --- | --- |
| 6 | `capa-20261022-affa19-step6` | `fb8d70588223c284…` | 56 / 647 |
| 7 | `capa-20261022-faults-step7` | `76a60c17b3304646…` | 56 / 654 |
| 8 | `capa-20261022-flows-step8` | `49f25e7488667b61…` | 56 / 665 |
| 9 | `capa-20261023-stabilization-s1a-step9` | `34c742da89529601…` | 56 / 681 |
| 10 | `capa-20261023-stabilization-s1a2-step10` | `4b04cb4aee387323…` | 56 / 687 |
| 11 | `capa-20261023-stabilization-s1b-step11` | `3eb39cda32a0376e…` | 56 / 712 |
| 12 | `capa-20261023-stabilization-s1a3-step12` | `d095ac0769944532…` | 56 / 718 |
| 13 | `capa-20261024-stabilization-s1a5-step13` | `cdbb1506b6557088…` | 56 / 724 |
| 14 | `capa-20261024-stabilization-stack-load-step14` | `fb5eb4598266e1cd…` | 56 / 741 |
| 15 | `capa-20261024-stabilization-s1a6-step15` | `6be1a184fc226166…` | 56 / 749 |

State at step 15: 43 FIX_CANDIDATE, 8 UNRESOLVED, 4 TRIAGED, 1 REJECTED; root-cause status 48 HYPOTHESIS and 8
UNKNOWN. No record has a verified cause. ML-CAPA-418 is FIX_CANDIDATE; ML-CAPA-359 and ML-CAPA-337 are TRIAGED
with a HYPOTHESIS cause; ML-CAPA-286 is UNRESOLVED with an UNKNOWN cause. Steps 9 to 15 opened no record.

### 5.3 Compatibility suite and live evidence

- **Compat suite:** 244 passed and 39 subtests against the installed platform wheel (compat
  `docs/engineering/thesis-lite-stabilization/verification-20261024-s1c2-f.log`; admission record
  `xdl/selection/aeb-sim-admission.json`, which still records `executionAuthority: absent`). See the compat record.
- **Live sets** on loop10 under
  `/media/jefferson/11c42dee-73a3-4c2b-ab42-a0440011d9e0/.x-verse-build/runs/lite-stabilization-s1/`:
  `s1c2-part2-dev3-20261024` to `s1c2-part2-dev8-20261024` (diagnoses and repairs; dev8 is the final set, 10 of
  10 as designed, 666 sealed files) and `vs09-20261024` (VS-09 MET on platform `a9db0ac39`, compat `e05d467`,
  blueprints `aceb5ae`; 144 sealed files). See the blueprints record.
- **Native checks:** the Phase 6 FR-024 boundary gtest passed 3/3 on the reconstructed loop10 toolchain. S1b
  needed no gtest because no C++ boundary changed (S1b package).
- **Soak (S1d, S1-T16): PENDING.** See section 9.

## 6. Engineering decisions

Source: `specs/029-lite-stabilization/review/author-decisions-20261023.md`, SHA-256
`38a6fc23888727a1f4904601d824d3c2af49604fd1864c10e0676179d35169e4` (thesis repository; untracked file, so the hash
is the only identity). "Delegated" means adopted under the author's "propose something and go" pattern;
"flagged" means it is marked there for the author's attention.

| ID | Summary | Status |
| --- | --- | --- |
| S-D1 | Capacity targets; long-run revised under delegation to 600 ticks, 4 units, 55 s active window, 4 MiB retained cap (S1a package) | approved 2026-10-23; revision delegated |
| S-D2 | Frozen as-built limits and ADRs (FR-012) may be amended, each recorded before implementation | approved 2026-10-23 |
| S-D3 | Challenge (nonce) marker readiness probe | approved 2026-10-23 |
| S-D4 | Soak protocol of plan rev 4a (P1–P8, validity rules) | approved 2026-10-23 |
| S-D5 | S1a and S1b as separate candidates | engineer proposal stands |
| S-D6 | Live execution for VS-09 and the S1d soak, within the Phase 7 constraints | approved 2026-10-23 |
| S-D7 | Verified-prefix cache keeping byte-level checks | engineer proposal stands |
| S-D8 | Weaker per-operation check only if S1-T01 required it | conditional; not triggered (S1a keeps byte-level prefix re-hashing) |
| S-D9 | Long-run terminal report against the 2 s bound | resolved by path (a), platform S1a-3; pending live confirmation in soak P6 |
| DR-1 | In-flight request grace 0.5 s, then `ML-PERSIST-CANCEL-GRACE` | delegated; accepted with S1a |
| DR-2 | After a cancel the writer ends `closed` or `failed`, consistent with the stream | delegated; accepted with S1a |
| DR-3 | RunClosure STOP/RETIRE only if evidence shows unattested facts | delegated; accepted with S1a |
| DR-4 | Argus-level differential check plus same-size tamper variants | delegated; accepted with S1a |
| DR-5 | Closure budget for the admitted maximum of 5 units | delegated; accepted with S1a |
| DR-6 | P3/P4 Argus conditions: Maestro root; WRITER-STATE allowed only for `failed`; killed-unit flow roots reported | approved by the author 2026-10-23 |
| DR-7 | Graceful stop for scenario and restart stops; terminal-fence stops stay forced | delegated, flagged; signed off 2026-10-24 04:14 |
| DR-8 | S1b features on the AF17 path only; LC09 refuses them | delegated, flagged; signed off 2026-10-24 |
| DR-9 | stderr private and retained, never collected | delegated, flagged; signed off 2026-10-24 |
| DR-10 | TERM is a separate AF17 request; grace waited with the lock free | delegated, flagged; signed off 2026-10-24 |
| DR-11 | No-carla runs in the four server-stopped gaps; server-failure counting | delegated, flagged; signed off 2026-10-24 |
| DR-12 | INVALID only for a server reason; a restore failure is FAIL | delegated, flagged; signed off 2026-10-24; made stricter by DR-21 |
| DR-13 | K.CANCEL accepted past the open lease (ADR-ML3-AFFA-0001 S1a-5) | delegated, flagged; signed off 2026-10-24 |
| DR-14 | No-carla diagnostic may be `ML-PROBE-NOT-READY` or `ML-RUN-CHILD-EXIT` | delegated, flagged; signed off 2026-10-24 |
| DR-15 | Load repairs RB1, RA1, RA4; harness H1, H3; H2 considered | delegated, flagged; signed off 2026-10-24 |
| DR-16 | RA2 with RA1; RA5 reserve; RB1 negative tests; LOW residuals | delegated, flagged; signed off 2026-10-24 |
| DR-17 | Failure-statement deadline cap (revised 02:41 to L_root − 0.25 s on the readiness and start paths); H1 = 1.7 s | delegated, flagged; signed off 2026-10-24 |
| DR-18 | H1 = 1.95 s and one soak warm-up per server start | delegated, flagged; signed off 2026-10-24; (1) superseded by DR-19 |
| DR-19 | H1 back to 1.7 s; warm-up excuses only a clean readiness failure; H2 tmpfs staging; post-run `SHA256SUMS` | delegated under the 2026-10-24 acceptance, flagged |
| DR-20 | A valid sample discharges a health slot due inside the Stop bracket (S1a-6) | delegated under the 2026-10-24 acceptance, flagged |
| DR-21 | Soak health check on a fresh synchronous server; synchronous after-check is FAIL; erratum 08:09 | delegated under the 2026-10-24 acceptance, flagged |

DR-19 to DR-21 were made after the author's acceptance of 2026-10-24 04:14 and have not been individually signed
off. The author may revoke any delegated decision.

## 7. Declared limits and residuals

- **Not claimed:** AEB validation, M1 (AD-21: declared non-M1 limit), X-Verse fitness for purpose, scientific
  results, standards compliance. Lane activation, M1 admission and factory runs remain author decisions.
- **Host:** a single development host. Timing outcomes are claimed only up to a sampled host load of 10.
- **Source parents:** G4 waived; all 18 REF-002 parents of Phase 3 remain allocation-only. Phases 1, 2 and 4
  keep their parents bounded_partial.
- **CAPA:** no verified cause and no demonstrated effectiveness (section 5.2).
- **Capacity:** the 64 KiB persistence configuration caps a run at 5 units, and a run must close within 90 s of
  entry, so the active window is about 55–60 s (S1a package). Retained public inputs grow about 1.7 KB per event.
  Admission does not check that the horizon fits the active window.
- **Readiness:** owned units use the nonce-marker probe. The unchanged legacy VCU stays liveness-only. Health
  stays liveness-only. The adapter's first run after a CARLA server start needs 1.27 s to more than 1.70 s to
  become ready, against the owned window of 1.7 s; about half of the soak warm-ups are expected to fail cleanly
  and be excused, and the soak results describe a warmed-up server (S1c-2 package; DR-18, DR-19).
- **Stops:** post-cancel and terminal-fence stops stay forced (DR-7); `stop_mode` is not persisted by the platform.
  A cancel during the TERM grace makes that stop an emergency result.
- **Cancel and lease residuals** (ADR-ML3-PROBE-0001, ADR-ML3-AFFA-0001, ADR-ML3-PERSISTENCE-0001; all fail-closed):
  - once the lease has actually expired, the authority closes itself and the run's closure is not guaranteed (S1a-5);
  - expired cap: if the cancel overran the reserve so that `L_root − 0.25 s` has passed, the failure statement is
    refused before sending and the failure event is missing;
  - sub-round-trip cap: a cap still in the future but shorter than one round trip is still sent, times out, and
    loses later terminal records;
  - L2: W′ = 0 for marker restarts and generation-limited starts; RA4 covers only an undeadlined cancel;
  - L3: admission does not compare W with the start budget or the health cadence; cuts are diagnosed
    (`ML-PROBE-WINDOW-CUT`);
  - L1 (persistence): root faults coinciding with a cancel are reported one call late;
  - L6: the readiness-window record is not in Argus or the writer's integrity chain.
- **Coverage (S1a-6):** a pre-S1a-6 report that hit the bracket re-verifies as `conflicting` with a later wheel
  (LOW-4); slot windows are closed at both ends (LOW-5); `ready` rows stay `unverifiable` in no-carla and start-up
  failures.
- **Evidence durability (H2):** unit run directories are staged on tmpfs and copied to loop10 at cleanup;
  durability is that of the copy after the run.
- **Live scope:** no steering ownership (blueprint README: "No steering; the reverse gear is not carried"); `brakeStatus` and
  `wheelSpeedEscStatus` blocked (G2); a command echo is not braking evidence; no parity with the legacy loop.

## 8. How to verify a checkout

The commands below are those recorded in the logs. They need host paths of the development machine; where a step
needs loop10 or CARLA, that is stated.

1. **Identity.** `git -C <checkout> rev-parse HEAD` must equal `a9db0ac39a858c0b2d341149042a8a97b7dcf393`.
2. **Full installed-wheel run.** From a clean checkout that contains the driver:
   `docs/engineering/maestro-lite/evidence/affa19/run-z-quiet-loop.sh <prefix>`, which waits for a quiet host and
   runs `verify-platform-regression-20261021t.py <out-dir>` (driver SHA-256 `3d7b285a…`; it freezes HEAD as a git
   archive, builds the wheel, installs it into a fresh venv and runs `python -m pytest tests -q -ra` on tmpfs). The
   driver hard-codes the build interpreter `/tmp/maestro-lite-platform-regression-target-20261020h/bin/python`,
   which exists only on the development host. Expected on the release head: 2945 passed, 1 skipped.
3. **DV12 gate.** `scripts/validate_maestro_acceptance_evidence.py <run-dir> --candidate <sha>
   --g4 acceptance-inputs/g4.json --allowlist acceptance-inputs/allowlist.json --scope code`
   (inputs under `evidence/affa19/acceptance-inputs/`). Expected: `accepted_as_evidence: true`, code `69118482…`.
4. **CAPA register.** From `docs/engineering/maestro-lite/evidence/affa19/`, with a Python that has `jsonschema`
   (the recorded checks used the decisive-run target interpreter, Python 3.13.13 with `jsonschema` 4.26.0):
   `<python> verify-capa-register-20261023.py capa-20261024-stabilization-s1a6-step15 <output.json>`.
   The argument is the register directory name. Without the second argument the verifier writes
   `<register>/verification-recheck.json` and refuses if that file exists, so a re-verification names an output
   file outside the tree. It needs a checkout that includes `evidence/` and the git history, because it checks the
   committed blobs of earlier bindings. Expected: rc 0, register `6be1a184…`, 56 records, 749 bindings (re-run
   2026-10-24 with that result).
5. **Compat suite, live cases and soak dry run:** see the compat and blueprints records. The live cases need
   loop10 and a CARLA 0.9.15 server.

## 9. Open items

- **S1d soak (S1-T16): PENDING.** Attempt 1 (2026-10-24 07:20) was stopped by the soak's own health check and led
  to DR-21. Attempt 2 (08:10) was stopped by the operator at the author's request and led to S1d2. Per compat
  finding 60 the soak restarts from zero at 00:00 on 2026-10-25, from clean detached worktrees of the tagged rc.1
  revisions. The rc.1 to final step depends on its report against P1 and P3–P8. GA-09, GA-10, GA-11 and GA-30 stay open until it
  reports; S-D9 closes only if P6 passes.
- **Ledgers (S1-T17):** `specs/021-thesis-lite-program/tasks.md`, `backlog.json` and the Phase 8 E8-2 list still
  show the state of 2026-10-23; a canonical-note entry for Phase 7 and S1 is to be recommended, not applied.
- **Phase 8 Assured AEB** (`specs/002-assured-aeb`): planning rev 3a. Decided: AD-01 (Phase 7 contract accepted),
  AD-21 (declared non-M1 limit), AD-23 (role vocabulary), AD-29 (Note 21 baseline), AD-30 (modelled latency in
  simulator time), AD-33 (no proposer-initiated degradation in the MLOC arm), AD-34 (arm table confirmed; C-13
  open). All other AD items, the protocol freeze (AD-27) and live authorization (AD-22) are open.
- **Phase 9 campaign runner:** planned, not started.

## Sources

Thesis repository `/home/jefferson/distributed_safety_critical_thesis`. These files are untracked or locally
modified there, so the SHA-256 below, computed at 2026-10-24 09:15 WEST, is their identity for this record.

| File | SHA-256 |
| --- | --- |
| `notes/dynamic_thesis_notes.md` | `8228de0729816330b25b296715cf921400c809ef732b248759b9ae6d50e07ddb` |
| `specs/021-thesis-lite-program/tasks.md` | `bee0c284b1a4f3a49c79ea4b547f543ce79416fdb3b5fd31669ddbda7cbd7b94` |
| `specs/021-thesis-lite-program/backlog.json` | `07d391ed1aea946df65d607139b61b7ee958178222bbc72074c7a2652dab5f8b` |
| `specs/021-thesis-lite-program/review/delegated-decisions-20261022.md` | `480397328a423cb868a0535b36583b2f0a1e4be4f4350f49fdf0a94389dcbd25` |
| `specs/021-thesis-lite-program/fabro/admission/runs/01M3VYDPRZTZKBZ2S0616VAHQ6/acceptance-decision.json` | `4fc8f685ce0b00922c8439d62b8e396dceffbfbf2588f8f3b376271f4f5e9fab` |
| `specs/023-argus-lite-evidence/review/closure-assessment-20261022.md` | `c8da44b8130457a5f3a4a5424fd89ecbd0e59a1b4224eaddf353ba538c1c09d4` |
| `specs/024-maestro-lite-lifecycle/review/t07-acceptance-package-20261022.md` | `44bc1a2e4e4708375d4bd7b30099f76cea70a763752b8c2f267c1e0348b0c34f` |
| `specs/003-thesis-lite-artifact-adapters/review/t07-acceptance-package-20261022.md` | `470527fce49100edde06f82d17bff5ca260a1f4f0d9e123596de083d619f440a` |
| `specs/026-lite-fault-schedules/review/acceptance-package-20261022.md` | `e2fcb4ccbeaf3dd7b589d55ac524c0427ed91a59965a600ef14476d2f6d9ad8c` |
| `specs/027-lite-flow-runtime/review/acceptance-package-20261022.md` | `e688de94a73b95f20988a1768b093e77d994328568fb32543485c3411506c547` |
| `specs/028-lite-carla-client-adapters/review/acceptance-package-20261022.md` | `ff6fe275be4c3199b562ed0ece571b42559f1ec4e9aa1b4a160291fd0ad79cb5` |
| `specs/001-thesis-lite-compatibility-smoke/review/acceptance-package-20261023.md` | `566f555901a00c0caaec9713c903b75135d14245b90d8d56f08cc1528df5e72c` |
| `specs/002-assured-aeb/decisions.md` | `6fca544cb06bf1bc9375af1053ed0723ca0e8498c6a7d23df6435ca9cc55d03d` |
| `specs/029-lite-stabilization/spec.md` | `a8d6ee4eaeeef19f69794743d366a7875459f93957d2016f4c47c22825cedcbf` |
| `specs/029-lite-stabilization/plan.md` | `386c50d0199a40080d9bede3ad0e940d54a884f70a8f63a07215da73ba406852` |
| `specs/029-lite-stabilization/tasks.md` | `03e439bfc9aaef9898bbafd914af156a9448329c6d840e8f462318f329557919` |
| `specs/029-lite-stabilization/review/acceptance-package-s1a-20261023.md` | `8d5677fddf1f47d035f0d9fa8097bc9de3e39fcbd997a30c88e9d722133c468b` |
| `specs/029-lite-stabilization/review/acceptance-package-s1a2-20261023.md` | `1fd198453c40de406a3fbf40d96d4b71131835b68bae8fee4171bfa382c708ab` |
| `specs/029-lite-stabilization/review/acceptance-package-s1b-20261023.md` | `b8178ace2e8c299ca218b2be2dbfab9840c1df8158c1ba55b8d800d6a38593b0` |
| `specs/029-lite-stabilization/review/acceptance-package-s1a3-20261023.md` | `f4bc1ebbab550ede36fa7644d965af6b4f75cd9399615195ce66575351866b0a` |
| `specs/029-lite-stabilization/review/acceptance-package-s1c1-20261023.md` | `7f1e07fa10096c28f55e15c92d470ba711ea9b45010b68f31146dd3b42d0c342` |
| `specs/029-lite-stabilization/review/acceptance-package-s1c2a-20261023.md` | `5f9e6ae7f40b8ce70a410524e18819309b9597fb3ed6143b619f9af8f8116276` |
| `specs/029-lite-stabilization/review/acceptance-package-s1c2-20261024.md` | `deab3886875592e0a08d0866154bb7b22d8a01828cf4a24d7a9bade039c0412a` |
| `specs/029-lite-stabilization/review/vs09-20261024.md` | `32f3698a4ba6b325d7615096e8e39191b93412e0500e7d4fb7f16ad638e95b73` |
| `specs/029-lite-stabilization/review/vs09-s1c2a-20261023.md` | `ff3660f3f0517e9d5b99c167f8dd68670094909ce485ec9ccf96e5bb9f78dc1d` |
| `specs/029-lite-stabilization/review/author-decisions-20261023.md` | `38a6fc23888727a1f4904601d824d3c2af49604fd1864c10e0676179d35169e4` |
| `specs/029-lite-stabilization/review/acceptance-package-s1a6-s1d-20261024.md` | `ed579593a869427ac4b3d9261f3ea1aca15561cbc6d2c791432246ab2ea94814` |
