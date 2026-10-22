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
