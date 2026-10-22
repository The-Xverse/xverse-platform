# Review log: Thesis Lite Phase 6 (communication integration, `xverse.flows`)

Candidate: `candidate/flows-lite-20261022` from platform main `2d556ff24` (Phase 5 accepted).

Authoritative specification (thesis repository, `specs/027-lite-flow-runtime`):
- planning rev 8b;
- detailed design rev 3a, READY FOR IMPLEMENTATION after detailed-design reviews 1–3.

Delegated decisions: DLG-5 (D6-11) and DLG-6 (D6-4, D6-5, D6-8). This log is under the gate-excluded
path `docs/engineering/maestro-lite/review-*`. Findings are recorded before repairs, and every log
edit is committed at once, because the frozen-run driver refuses a dirty worktree (faults-lite
finding 15).

1. Opening (2026-10-22). Planned work in design order:
   - `xverse.flows` modules `codes`, `timebase`, `clock`, `provider`, `convert`, `binding`,
     `receiver`, `evidence` and `run`;
   - the owned fixtures `tests/thesis_lite/flows/fixtures/{uniform,distinct,refusals}`;
   - the tests V01–V10.

   **Phase 5 successor change**, recorded here before any code (design §9; 026 amendment to follow
   in the thesis repository):
   - (9a) `duplicate` and `reorder` become executable, with a relay outbox, `take_outbox` and
     `held_count`. The side effects are: resolve-time target-boundary refusals, overlap
     arbitration covering both kinds, the dispatcher `boundaryMode` change, and Maestro arming
     them.
   - (9b) The `XVERSE-FAULT-RECOVERY` message wording follows DLG-3.

   The Phase 5 tests asserting the declared-only behaviour change with it.

   **Open question:** does `xcom_plan.compile_plan` need the X-COM Profile resource
   (`io.xverse.xcom`) in its graph, given that this resource is not an experiment-plan provenance
   contributor? If it does, that is a finding and a design amendment (convert §3). It is settled
   by the first binding test.

2. Two clarifications found during implementation (2026-10-22); neither is a design defect.
   (a) The open question of finding 1 is settled: `compile_plan` accepts the converted System,
       Deployment, Scenario and Component entries without the X-COM Profile resource. That
       Profile is needed only by XDL validation, which runs before `bind`. On the unchanged
       `tests/thesis_lite/xdl/fixtures` set, stage 0 gives exactly
       `XCOM-PLAN-CAPABILITY-UNRESOLVED`, `-POLICY-UNRESOLVED` and `-SCHEMA-UNRESOLVED`, as the
       design (W1) expects.
   (b) The data model does not say what happens to an out-of-order item on an `unordered` route
       while the buffer is full. The precedence rule keeps the verdict `out-of-order`, so the
       item is withheld with diagnostic `queue-full` (receiver).

3. Implementation finding (2026-10-22). The experiment plan normalizes a Scenario mapping tolerance
   to `{value, unit, ticks}` (`experiment_plan._quantity`). The binder's quantity parser accepts
   exactly `{value, unit}`, so the first owned fixture refused the camera flow with
   `MAPPING-UNSUPPORTED`. Repair: the binder parses `{value, unit}` and requires the plan's
   `ticks` to equal the parsed nanoseconds (1 tick = 1 ns); a disagreement is
   `MAPPING-UNSUPPORTED`. With the repair the owned `uniform` set compiles to an `activatable`
   `xcom_plan` with no diagnostics, and the `distinct` set compiles to an `inspectable` plan with
   only `XCOM-PLAN-POLICY-CONFLICT`, as FR-013 requires.

4. Implementation complete for P6-T01–T03, T05 and T06 (platform side), 2026-10-22.

   **Product.**
   - `src/xverse/flows/`: `codes`, `timebase`, `clock`, `provider` (mirror digest
     `0e38ed80…` over the four provider/loopback files), `convert`, `binding`, `receiver`,
     `evidence`, `run`.
   - `pyproject` force-includes `src/xverse/flows`.
   - The Phase 5 successor change (amendment A1, thesis 026 `spec.md` `1ea98c16…`):
     - `vocabulary.py`: `duplicate` and `reorder` executable;
     - `boundary.py`: the two relay kinds, the outbox, `take_outbox` and `held_count`;
     - `resolve.py`: the DLG-3 message wording.

   **Tests.**
   - `tests/thesis_lite/flows/`: `support.py` builder plus the committed `fixtures/{uniform,distinct}`,
     and the test modules `test_binding`, `test_timebase`, `test_receiver`, `test_harness_faults`,
     `test_mirror` and `test_fixtures`.
   - `test_mirror` checks that the FR-024 core headers keep digest `67dd25ce…`.
   - `tests/thesis_lite/faults/test_resolve.py`: `u_flt_08` now asserts A1, and the new
     `u_flt_08b` asserts the overlap side effect.

   **Test-expectation correction (not a product defect).** A reorder window cannot clear after the
   last planned tick, because resolution gives `XVERSE-FAULT-HORIZON`. The end-of-run test
   therefore clears the partial block exactly at the last tick (40) and asserts that it is
   received.

   **Results.**
   - From source: 73 flows tests passed.
   - Installed-wheel venv `/dev/shm/p6-venv`: 121 passed across `tests/thesis_lite/faults` and
     `tests/thesis_lite/flows`.
   - Four Maestro-run fault tests failed when run from source with `PYTHONPATH`. They need one
     installed version, as already recorded for Phase 5, and all pass installed.

   **Pending.**
   - P6-T04: the `xverse-compat` adapter.
   - V10's named `fault_boundary_tests` gtest run.
   - Independent implementation review.
   - Full installed-wheel run and DV12 gate.

5. V10 gtest run not performed (2026-10-22). The X-COM C++ toolchain prefixes in `~/.cache`
   (`xverse-xcom-grpc-prefix`, `xverse-xcom-t025-gtest-prefix` and their package caches) are
   dangling symlinks. They point to `/media/jefferson/11c42dee-…/.x-verse-build/cache`, which no
   longer exists on the mounted image; only `repository/` and `runs/` remain. Reprovisioning
   requires the controlled online staging of the 12 pinned packages
   (`docs/engineering/xcom/build-environment.md`), which this phase does not perform.

   Substitute evidence, stated as a limit, not as equivalence:
   - `git diff 2d556ff24 -- src/xverse/xcom tests/xcom` is empty: Phase 6 changes no C++ source,
     header or C++ test.
   - `test_mirror::test_v10_core_headers_byte_identical_to_the_phase_6_base` pins the 10 FR-024
     core headers (`67dd25ce…`).
   - The FR-024 gtest was accepted on exactly these bytes with platform main.

   The named gtest run stays an open V10 item, to be executed when the toolchain is reprovisioned.

6. Cross-repository finding (2026-10-22), recorded with `xverse-compat` candidate
   `candidate/phase6-bridge-route-20261022` (its finding 2). The `xverse-compat` content lock
   includes the platform `pyproject.toml`, which the Phase 5 merge changed. `xverse-compat` main
   has therefore failed `test_platform_dependency_source_matches_content_lock` against platform
   main since `2d556ff24`; Phase 5's acceptance did not run that suite.

   This candidate changes `pyproject.toml` again (`xverse.flows`). The re-pin follows the platform
   Phase 6 merge. **Process repair:** from now on, an acceptance that changes the platform
   `pyproject.toml` or the locked roots also runs the `xverse-compat` suite against the candidate
   before the merge, and records the expected re-pin.

7. V10 gtest run performed (2026-10-22, author instruction "install again the c++ toolchain, but
   on loop10"). This supersedes the open item of finding 5.

   **Toolchain.** The X-COM toolchain was reconstructed on the loop10 image
   (`/media/jefferson/11c42dee-…/.x-verse-build/cache/`). The existing `~/.cache` symlinks resolve
   again.
   - The 13 locked Jammy packages (`dependency-lock.md`) were downloaded from the recorded Ubuntu
     pool coordinates into `xverse-xcom-grpc-packages/`, and each size and SHA-256 equals the lock.
     The `package-manifest.json` has 13 records. They were extracted with `dpkg-deb -x` only (no
     install, no maintainer scripts) into the new prefix `xverse-xcom-grpc-prefix/` (80 MB).
   - The 3 googletest 1.11.0-3 packages (`t025/test-dependency-admission.md`) were handled the
     same way, into `xverse-xcom-t025-gtest-packages/` and `-prefix/`.

   **Admission.**
   - `scripts/check_xcom_t025_test_dependencies.py` gives `XCOM-T025-DEP-I000`.
   - `scripts/xcom_dependency_preflight.py --verify-toolchain` gives `XCOM-BLD-I000` ("exact
     offline dependency set admitted"), with the documented environment (`PATH`,
     `LD_LIBRARY_PATH`, `PKG_CONFIG_*`, `CMAKE_PREFIX_PATH`) and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`.
   - The first two attempts failed, and the failures are recorded: without `LD_LIBRARY_PATH` the
     `protoc` version probe failed (E039); without the T025 prefix the CMake configure probe failed
     (E061).

   **Run.** The candidate tree was configured in `/dev/shm/xcom-build-p6` (Debug, testing on). Only
   `xverse_xcom_core_matrix_fault_boundary_tests` was built (`ninja -j4`), and
   `ctest -L t016-fault-boundary` passed: 100%, 3/3. One of the three is
   `CoreMatrixFaultBoundary.CoreSurface_HasNoUncontrolledMutationEntryPoint`. The evidence is
   in `evidence/affa19/flows-lite/v10-gtest-20261022/` (admission JSON, filtered ctest log,
   SHA256SUMS). V10 is complete.

8. Independent implementation review 1 (2026-10-22, on `dd76a8a32` plus compat `f2a5577`): **FAIL**,
   with no HIGH findings and five MEDIUM ones (recorded here before any repair). The reviewer
   confirmed that the core logic conforms:
   - binding steps 0–9, attribution, selection, mask, limits, cross-check and serialization;
   - receiver precedence, state table, deadline formula and queue;
   - harness order, outbox and determinism;
   - A1 semantics.

   It re-ran 121 installed tests and 15 compat tests (both passed), and probed two uncovered paths
   (`refuse_clear` gives `incomplete` with heldAtEnd 15; an exception drains the outbox), both of
   which behave correctly.

   | # | Sev | Finding | Planned repair |
   | --- | --- | --- | --- |
   | M1 | MEDIUM | `reconstruct_flows` only compares the withheld, gap and deadline event counts with the summary. It does not re-derive verdicts or check the other summary fields, it drops foreign flows silently, it raises `KeyError` on an unknown verdict, and it misses duplicate summaries. | Re-derive each recorded event's verdict from its payload and the binding: age, tolerance, stale, out-of-order. Compare every summary field that can be derived. Flag foreign flows, unknown verdicts and duplicate summaries. Add tamper tests. Stated limit: delivered items are counted, not recorded, so their verdicts are checked only by count. |
   | M2 | MEDIUM | V06 is incomplete: there is no `bridge-recorder-monotonic` domain in the fixtures, no hand-computed ages, and no receiver-in-loop test. | Add the domain to the fixture System. Add a compat V06 test that feeds the adapter's items through the platform `FlowReceiver` (the compat test environment gets the candidate platform wheel), with hand-computed ages, a deadline check and a final poll. |
   | M3 | MEDIUM | A1 side-effect tests are missing: the resolve target mismatch, the dispatcher `boundaryMode`, Maestro arming, and relay-level duplicate/reorder. | Add a resolve-refusal test, relay unit tests, and a Maestro-run assertion on the intent `boundaryMode` and the outcomes of a duplicate and a reorder entry. |
   | M4 | MEDIUM | There is no test of `heldAtEnd > 0` or of the cancel-path outbox drain. | Add a `refuse_clear` test and an exception-with-held-items test. |
   | M5 | MEDIUM | Missing binding tests: `POLICY-MISSING`, Deployment fallback, Scenario `ignoredPayloads`, provider ambiguity and `networkId` narrowing, the stage-0 `XcomPlanError` path, and multi-defect cases for step precedence. | Extend the builder with payload overrides and add these tests. |

   Repairs for the LOW findings:
   - **L1:** emit summaries once; record a cleanup failure in `failure`.
   - **L2:** separate the deadline anchor from the regression baseline.
   - **L3:** set the top-level `flowId` on cross-check refusals.
   - **L4:** the data model is amended in the thesis repository (unordered out-of-order with a full
     buffer keeps verdict `out-of-order`, withheld, with diagnostic `queue-full`), under the
     author's delegation.
   - **L5:** fix the vocabulary docstring and add `held_buffer()`.
   - **L6:** replace the hard-coded pins with a real cross-test against the platform function (made
     possible by M2's environment).

9. Repairs for implementation review 1 (2026-10-22). Each finding was recorded in finding 8 before
   its repair.

   | # | Repair |
   | --- | --- |
   | M1 | `reconstruct_flows` re-derives each recorded event's verdict from its payload and the binding (age through the mapping, tolerance, freshness, regression). It compares `withheldCount`, `gapCount`, `deadlineMissedCount`, `queueFullCount`, every withheld verdict count, the out-of-order count (withheld plus delivered), `filledGapCount`, `deliveredCount` and `heldAtEnd`. It flags foreign flows, unknown verdicts and events, and duplicate summaries. The stated limit remains: delivered in-order items are counted, not recorded. New tamper tests cover a relabelled verdict, an inconsistent age, an unknown verdict, a duplicate summary, a foreign flow and a wrong `deliveredCount`. |
   | M2 | The fixture System declares `bridge-recorder-monotonic`, with a test. Compat test `test_v06_adapter_items_through_the_platform_receiver_with_hand_computed_ages` feeds adapter items through `xverse.flows.FlowReceiver`: ages of 5, 5 and 70 ms, the third stale against a 60 ms freshness bound; three deadline events at the 80 ms deadline, one at reception and two at the final poll. |
   | M3 | New tests: `test_relay_kinds.py` (duplicate, reorder, the outbox from a delay or reorder clear, `release` keeping held items counted); `test_u_flt_08c` (a duplicate on a process target gives `XVERSE-FAULT-TARGET`); `test_fault_run_arms_duplicate_and_reorder_on_no_traffic_relays[duplicate|reorder]` (a Maestro run per kind: outcome `cleared`, intent `boundaryMode` `owned-relay-fixture-no-traffic`, closure complete). The Maestro fixture's short horizon admits one message fault at tick 1, so each kind runs on its own. |
   | M4 | `test_v08_failed_clear_leaves_items_held_and_the_run_incomplete`, and `test_v08_exception_cancels_and_drains_held_items_to_the_receiver` (held sequences 5–9 reach the receiver through the cancel-path outbox; summaries emitted once; no cleanup failure). |
   | M5 | Tests for `POLICY-MISSING`, the Deployment fallback, Scenario `ignoredPayloads`, two-provider ambiguity, `networkId` narrowing (unit level), the stage-0 `XcomPlanError` path, and five two-defect step-precedence cases. The builder gains `omit_camera_policy`, `deployment_policy`, `scenario_policy` and `second_provider`; the committed fixtures are regenerated. |
   | L1 | Summaries are emitted once. A cleanup failure is recorded in `FlowRunHarness.cleanup_failure` and does not mask the original error. |
   | L2 | Activation sets only the deadline anchor; the regression baseline is the previous reception, with a test. |
   | L3 | A cross-check refusal carries the top-level `flowId`. |
   | L4 | The thesis data model is amended (unordered out-of-order with a full buffer). |
   | L5 | The vocabulary docstring now says eight executable kinds, and `FlowReceiver.held_buffer()` is added. |
   | L6 | The compat pins are compared live with `xverse.flows.seconds_to_ns`. |

   **Results.** The wheel was rebuilt; the flows and faults suites give 144 passed. Compat, in the
   clean venv `/dev/shm/compat-p6-venv` with the candidate platform wheel, gives 16/16 for
   `test_bridge_route.py`. The full compat suite gives 90 passed and 1 failed: the known
   content-lock drift, re-pinned after the platform merge (finding 6).

10. Independent implementation review 2 (2026-10-22, on `4d43f93c3` plus compat `932f251`): **PASS**.
    M1–M5, L1, L2 and L4–L6 are resolved; L3 is partial. The reviewer's checks:
    - re-ran 144 platform tests and 16 compat tests (both passed);
    - fuzzed 20 000 legitimate receiver runs through `reconstruct_flows` with zero false positives;
    - confirmed the M3 test reads `boundaryMode` from the Argus intent payloads.

    It raised four new LOW findings, recorded here before their dispositions:

    | # | Finding | Disposition |
    | --- | --- | --- |
    | N1 | The L3 repair (top-level `flowId` on `XCOM-CROSSCHECK`) contradicts design §2 ("`flowId` null"), and no test covers it. | Keep the repair and amend design §2 under the author's delegation (a per-flow refusal names its flow); add a record-level test. |
    | N2 | `_expected_verdict` skips `queue-full` labels although stale ranks above them; the regression diagnostic is not checked against reception order. | Re-derive stale for `queue-full` labels. Regression ordering cannot be checked from recorded events alone, because delivered in-order receptions are not recorded; stated limit. |
    | N3 | The "recorded X, derived Y" branch has no test. | Add a self-consistent relabel-to-`delivered` tamper test. |
    | N4 | A cleanup failure inside `_final` can lose outbox items already taken, `cleanup_failure` is untested, and it is not written to evidence. | Add a test that sets `cleanup_failure`. Stated limit: this arises only in runs that already re-raise; the failure is kept on the harness, not in Argus. |

11. Review 2 LOW findings dispositioned (2026-10-22):
    - **N1:** thesis detailed design §2 amended (a cross-check refusal carries its binding's
      `flowId`); `test_v01_crosscheck_refusal_names_its_flow`.
    - **N2:** `_expected_verdict` re-derives stale for `queue-full` labels; the regression-ordering
      limit is stated.
    - **N3:** `test_rule_13_relabel_to_delivered_hits_the_derivation_branch`, which covers relabels
      to `queue-full` and to `delivered`.
    - **N4:** `test_cleanup_failure_is_recorded_without_masking_the_original_error`; the limit is
      stated.

    Wheel rebuilt; the flows and faults suites give 147 passed. Next: the full installed-wheel run
    on a quiet host (loop `flows-lite/platform-regression-20261022h`).

12. Decisive full installed-wheel run (2026-10-22): `flows-lite/platform-regression-20261022h-1`,
    head `74db77112`, started 20:35Z at load 3.43. It was the first attempt.
    - Result: **clean**, 2397 passed, 1 skipped, 0 failed in 2746 s.
    - Load: sampled about 90 times, maximum 5.49. The loop reported `decisive: clean`.
    - DV12 gate (`--scope code`, G4 and allowlist inputs): `accepted_as_evidence: true`, no
      blockers. The run and candidate code SHA-256 match (`8a3e67405939c6ae…`).
    - Evidence: `dv12-gate-verdict.json` and `SHA256SUMS` (13 files) in the run directory;
      receipts archived.

13. CAPA tooling finding (2026-10-22). The first build of CAPA step 8 failed
    `verify-capa-register-20261020.py` on the inherited binding `E-FAULTS-REVIEW-LOG` (CAPA step
    7). Step 7 bound `review-faults-lite.md` as it stood with findings 1–17
    (SHA-256 `6558cc6fd8cfdda5…`). Findings 18–19 were then appended, and only that later version
    was committed (`45daf1c53`). The bound bytes therefore never entered git history.

    Step 7 verified at Phase 5 time because the file on disk still matched. Once the file changed,
    the verifier's committed-blob fallback (finding 391) found no blob with that hash.

    The bound version reconstructs exactly: the committed log cut before "18. CAPA successor
    step 7", plus a newline, hashes to the bound value.

    **Repair**, documentation-only and in the gate-excluded path, so the code hash is unchanged:
    two commits on this candidate. The first sets `review-faults-lite.md` to the reconstructed
    bytes; the second restores its current content (net change zero). The bound blob is then in
    history at its path. The partial step-8 build was discarded and is rebuilt after this log is
    committed.

    **Process repair:** commit the review log before building any CAPA step, so every bound log
    version is a committed blob. Phase 5's acceptance is unaffected: its CAPA verified at the time,
    and the bound content is recovered exactly.

14. CAPA successor step 8 (`evidence/affa19/capa-20261022-flows-step8/`), built by
    `build-capa-20261022-flows-step8.py` after the log was committed (finding 13's process
    repair). It is additive over step 7 (`76a60c17…`), and no record was opened, changed or
    closed: every Phase 6 defect was a defect of this unaccepted candidate (findings 2–11),
    repaired before acceptance.
    - Register `49f25e7488667b61c6b8e9e82c5f2d58d4b97f8e00b5f0a8664077a72fd16f84`: 56 records and
      665 bindings, which add the review log, the run's SHA256SUMS and gate verdict, the V10
      SHA256SUMS and the Phase 6 test modules.
    - `verify-capa-register-20261020.py` passes (rc 0).
    - Parent preservation passes: 654 parent bindings, none changed or lost.
    - No cause is verified and no effectiveness is claimed.

15. **Acceptance decision, Phase 6 (communication integration), recorded before merge**
    (2026-10-22).

    **Basis.** The author's goal of 2026-10-22, plus the delegation "propose something and go"
    (thesis `specs/021-thesis-lite-program/review/delegated-decisions-20261022.md`: DLG-5 for
    D6-11 and DLG-6 for D6-4, D6-5 and D6-8). Specification: thesis `specs/027-lite-flow-runtime`
    (planning rev 8b, detailed design rev 3a with the N1 amendment, data model with the L4
    addition) and the 026 amendment A1.

    **Evidence.**
    - Implementation review 1 FAIL (finding 8), repaired (9); review 2 PASS (10); LOWs
      dispositioned (11).
    - V10 FR-024 gtest 3/3 on the reconstructed toolchain (7).
    - Decisive clean run h-1 with the DV12 gate accepted (12).
    - CAPA step 8 valid (14).
    - The `xverse-compat` suite was run against the candidate wheel before the merge (finding 6's
      process repair): 90 passed; the 1 failure is the content lock, re-pinned after this merge.

    **Decision.** Accept `candidate/flows-lite-20261022` and merge it `--no-ff` into platform main,
    then push. The delivery identity check is the gate against the merge commit, which must give
    the run's code SHA-256 `8a3e6740…`. Then re-pin the `xverse-compat` lock to the new main, run
    its suite, review, and merge it.

    **Limits carried.**
    - The flow layer mirrors the C++ loopback rules and opens no X-COM route (D6-7). Only
      ordered/best-effort flows bind.
    - Policy-distinct flows cannot activate the C++ core (D6-10).
    - Maestro-driven flow traffic is not exercised; verification uses the tick-driven harness, and
      the assembled system is carried to Phase 7 (D6-11).
    - The bridge age excludes publication latency (D6-3).
    - The time and capability conventions live in `quality` and in strings, not in the schema
      (D6-4, D6-5, D6-8).
    - Offline reconstruction checks delivered in-order items by count only.
    - A harness cleanup failure is kept on the harness, not in Argus.
    - Live camera, radar and bridge paths are gated by Phase 4b and Phase 7, and G3 and G6 stay
      open.
    - Timing outcomes are claimed only up to a sampled host load of 10.
    - The 18 REF-002 parents get bounded partial contributions only.
    - No scientific claim, M1, lane activation or factory run.
