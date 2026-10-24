# Review log: X-Verse increment WP-10 #3, simulation-time fault triggers (option A)

Candidate: `candidate/lite-simtime-faults-20261024`, base main `b40acce49`. Basis (read-only):
- thesis `specs/002-assured-aeb/design/wp10-fault-relay.md` §4 (the six platform requirements and the step-hold
  handshake);
- the "WP-10 fault relay" row of `specs/002-assured-aeb/decisions.md` (option A decided under the author's
  delegation of 2026-10-24, flagged for the author's review).

Findings are recorded before repairs. The maturity is an engineering candidate: not M1, not AEB evidence, not a
scientific result. No CARLA and no live run is used. Every value the design needs from D-4c is a declared input,
and admission refuses while it is unknown.

## Findings

1. **L-8: a simulator-time fault cannot be admitted, and the platform has no path from a fault to traffic or
   to the simulator clock. The design of option A and the affected ADRs (written at 12:17:49 2026-10-24).**
   - **The problem, reproduced offline.** I used the installed C1 wheel, the Maestro fixture with a sensor, and
     a `freeze` on `sink-instance` declared `at: 1.5 s` with a duration of `0.5 s`.
     - It compiles to `trigger.atTicks = 1500000000` and `duration.ticks = 500000000`, with `declaredUnit: s`.
     - `prepare_lifecycle` then refuses it: `ML-UNSUPPORTED: fault schedule not admissible:
       XVERSE-FAULT-HORIZON`.
   - **Where it arises.**
     - **Compilation is already exact in nanoseconds.** `experiment_plan.py:92`,
       `TIME_UNIT_TICKS = {"tick": 1, "ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000}`. `_ticks`
       (`:837-870`) multiplies exactly with `Fraction` and keeps `declaredAt` and `declaredUnit` beside the
       product (`_fault_section`, `:1626-1665`). The canonical tick of the compiler is therefore one nanosecond
       for a physical unit, and the onset and duration in ns are already in the compiled plan without loss.
     - **The refusal is in resolution.** `resolve.py:110-119` reads `atTicks` as a Maestro tick index and looks
       for the first planned tick at or after it. `validate_static` (`resolve.py:149-171`) does the same over the
       dense ticks `0..horizon_ticks` (at most 10 000, `projection.py` `Limits`), so 1.5e9 is beyond the
       horizon.
     - **Tick and ns share the compiled field.** A "3 tick" trigger and a "3 ns" trigger compile to the same
       `atTicks`. Only `declaredUnit` distinguishes them.
     - **One domain (L-1).** `prepare_lifecycle` admits exactly one time domain, of clock class `simulation`
       (`projection.py:274-276`). Steps in that domain are tick-keyed (`projection.py:411-419`).
     - **No traffic and no clock.** The dispatcher builds its boundaries in-process (`dispatcher.py:1289-1333`).
       A `flows` target becomes `MessageRelayBoundary`, recorded as `owned-relay-fixture-no-traffic`, so no
       platform path reaches traffic in another process (P-2). There is no channel through which a unit reports
       simulator time. `FaultScheduler.advance(tick)` is driven by Maestro ticks only (`scheduler.py`).
     - **Assurance kinds.** The three assurance kinds are declared and not executable (`vocabulary.py:75-77`).
       They end as `declared-not-executed`.
   - **Design of option A (proposed; the ADR follows before code).**
     - **(1) Declaration: a simulation-clock binding on the Maestro preparation.**
       - `prepare_lifecycle(..., fault_clock=SimulationClock(...))` declares that the admitted simulation domain
         is clock-sourced:
         - `domain`, which must equal the one admitted domain (L-1);
         - `source_unit`, the component instance of U2, which must be a unit of the deployment;
         - `step_ns` and `horizon_ns`, integers;
         - the D-4c values `max_step_host_s`, `handshake_s` and `hold_bound_s`, each `None` while unmeasured.
       - The binding enters the canonical bytes and the digest only when it is present, so every existing plan
         keeps its bytes and digest (U-ADM-03).
       - XDL is unchanged. The system schema's `timeDomain` is closed (`system.schema.json`), and the compiled
         plan already carries exact ns.
       - With a binding, every fault entry must be simulator-timed: a `time` trigger in a physical unit
         (`ns`, `us`, `ms` or `s`) in the bound domain, and a duration in a physical unit. A `tick` unit or a
         `declared-order` trigger is refused. Without a binding, behaviour is unchanged, L-8 included.
     - **(2) Resolution and horizon (new `xverse.faults.simtime`).**
       - Each entry keeps `at_ns` and `duration_ns` exactly as compiled. Its step grid is
         `onset_step = ceil(at_ns / step_ns)` and `clear_step = onset_step + ceil(duration_ns / step_ns)`,
         following the AD-30 rule "at or after".
       - `clear_step · step_ns` must not exceed `horizon_ns`; otherwise the code is `XVERSE-FAULT-HORIZON`.
         No planned tick is involved.
       - Two entries on one target whose step windows overlap are refused (`XVERSE-FAULT-OVERLAP`). No
         arbitration is admitted in this mode.
       - Admitted kinds:
         - message `delay` (with `delay-ns`, not `delay-ticks`), `loss` (`every` or `loss-ratio`) and `stale` on
           `flows`, through the remote relay;
         - the three assurance kinds on `flows`, executable at the remote relay only (K-13);
         - `freeze` on `componentInstances`, through the step hold.
       - `crash`, `sensorDropout`, `duplicate` and `reorder` are refused (`XVERSE-FAULT-SIMTIME-KIND`).
       - A freeze of the clock-source unit is refused (`XVERSE-FAULT-SIMTIME-SOURCE`), because frozen time
         could not resume.
     - **(3) A remote relay boundary bound to the clock-source unit.**
       - The trusted caller supplies a `HubChannel`: an AF_UNIX `SOCK_SEQPACKET` socket, either connected or
         listening. A listening socket accepts exactly one peer, whose uid must equal Maestro's.
       - Frames are canonical JSON of at most 4 096 B. Each kind has a closed key set, and each direction has a
         strictly increasing sequence.
       - Maestro arms the hub only after the source unit is bound and live, with each entry's minimum
         descriptor (entry, fault, kind, target, mode, `atNs`, `durationNs`, steps and parameters) and the run
         seed. The hub answers `armed` with the exact entry ids.
       - The hub reports `applied`, `cleared` or `failed` at the exact grid step.
       - No role unit receives a descriptor. The schedule stays in the dispatcher (FR-028).
     - **(4) The step-hold handshake, with Maestro as the decision maker.**
       - For a `freeze`, the hub holds the simulator step at `onset_step` and reports `hold(apply)`.
       - On its next poll, Maestro checks the entry, the phase and the exact step. It applies the freeze through
         the unchanged `ProcessBoundary` and the owned launcher operation, then sends `ack`. The hub resumes.
       - The same exchange runs at `clear_step` for the thaw.
       - Any of the following is a protocol failure that ends the run (`XVERSE-FAULT-SIMTIME-PROTOCOL`), and
         Maestro then sends `close`:
         - a hold or report at a different step;
         - a report that passes a pending hold step;
         - a sequence gap;
         - an unknown entry.
     - **(5) Evidence with two clocks.** Every decision travels through the existing worker `fault` statement
       (`schedule_evidence.py:665-679`, detail of at most 512 B). Its detail carries `simulatorNs`,
       `simulatorStep` and the Maestro host time `hostNs`, beside the Maestro tick of the statement. The intent
       detail carries the declared and grid values and the boundary mode (`remote-relay` or `step-hold`).
     - **(6) Admission, in this order:**
       1. preparation (2);
       2. `admit_schedule`, which refuses a schedule with a `freeze` entry
          (`ML-SCHEDULE-FAULT-SIMTIME-UNMEASURED`) while any of `max_step_host_s`, `handshake_s` or
          `hold_bound_s` is unknown;
       3. `admit_schedule` then checks, for each freeze,
          `(clear_step − onset_step) · max_step_host_s + 2 · handshake_s ≤ thaw_bound_s`, with
          `thaw_bound_s = cadence − health_scan_seconds` of this admission. A failure is
          `ML-SCHEDULE-FAULT-SIMTIME-THAW`. A `handshake_s` above `hold_bound_s` is
          `ML-SCHEDULE-FAULT-SIMTIME-HOLD`.

       `step_ns` is mandatory in the binding. A message-only schedule does not need the D-4c values, because no
       step is held for it.
     - **Run time.** `FiniteDispatcher(..., fault_clock_channel=...)` and the same keyword on
       `_OriginalRuntimeRun`. A prepared binding with simulator-timed faults and no channel is refused at begin
       (`ML-SCHEDULE-FAULT-CLOCK`). The new `SimTimeFaultScheduler` keeps the interface of `FaultScheduler`
       (`start`, `advance`, `cancel`, `finish`, `outcomes`, `run_failed`, `incomplete`), so the dispatcher's tick
       loop is unchanged.
       - Each `advance(tick)` reads every available frame without blocking.
       - At `finish`, a freeze still applied is thawed and ends `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`).
         A relay entry applied and never reported cleared is `incomplete-clearing`, so the run is incomplete.
     - **Persistence.** The binding travels in the sealed configuration as an optional `fault_clock` key, present
       only when declared. The worker, `encode_configuration` and `admission._verify_prepared` rederive the
       preparation with it.
   - **ADRs and records affected.**
     - New `ADR-ML3-SIMTIME-0001.md`, the decision record of (1)–(6).
     - Amended `docs/engineering/faults-lite/detailed-design.md` (the Phase 5 fault design). Its resolution,
       boundary and evidence rules gain a simulator-time mode, and the tick mode is unchanged.
     - Amended `ADR-ML3-SCHEDULER-0001.md`, for the dispatcher input (the channel) and the polled scheduler.
     - A note in `ADR-ML3-PERSISTENCE-0001.md`, for the optional configuration key.
     - Unchanged:
       - the Phase 6 relay amendment A1 (`review-flows-lite.md` 62), whose in-process relays stay as they are
         for tick mode;
       - the native launcher fault operations (kill, freeze and thaw);
       - the X-COM records.
   - **Not in this increment (for the record).**
     - The hub side (compat #4) and the harness wiring (blueprints #5).
     - The D-4c values.
     - The proposal variants of the assurance kinds (AD-11, AD-27). Their descriptors carry no variant, and the
       hub takes it from its frozen protocol record.
     - Authentication of the channel peer as the U2 process (cgroup membership). This increment checks the uid
       only.
   - **Planned tests.**
     - Resolution and horizon, including kinds, the source freeze, overlaps and units.
     - The binding's validation, and digest equality for plans without a binding.
     - The admission refusals and the thaw check.
     - The channel codec and its protocol violations, against a fake hub over a socketpair.
     - The scheduler against a fake hub: the hold, apply, ack, clear and ack sequence, relay reports, a skipped
       hold, a wrong step, a protocol failure, `finish` and `cancel`.
     - A composed dispatcher run on the native fixture with a fake hub thread: a step-hold freeze and a remote
       relay `loss`, with Argus chains closed and both clocks in the detail.
     - The Phase 5 suites, unchanged.

2. **Implementation and installed-wheel verification of option A (written at 15:29:01 2026-10-24).**
   - **Commits.**
     - `5b011644a`: finding 1.
     - `321df989e`: `ADR-ML3-SIMTIME-0001` and amendments ST-1.
     - `d7c33172c`: ADR decision 9, the capability contract, added on the coordinator's input before the flag was
       coded.
     - `92fc2643b`: the code and tests. The source diff from `b40acce49` is 11 files, +842/−11.
   - **Capability flag.** `xverse.faults.SIMULATION_TIME_TRIGGERS = True`, the exact name and shape that the
     blueprints probe (WP-10 #1, `f0ecf6e`). No different name was needed. It is pinned by
     `test_capability_flag_is_pinned` (identity `is True`, and listed in `__all__`).
   - **What was built, against the six requirements of `wp10-fault-relay.md` §4.**
     1. **XDL and compilation.** These are unchanged, because the compiler already keeps exact ns (finding 1).
        - `prepare_lifecycle(fault_clock=SimulationClock(...))` names the clock-sourced domain and the source
          unit. `faultClock` enters the canonical bytes only when declared.
        - `delay-ns` is the simulator-time delay parameter. Tick mode refuses it, and simulator-time mode refuses
          `delay-ticks`.
     2. **Resolution and horizon.** `resolve_simtime` keeps `at_ns` and `duration_ns`, places `onset_step` and
        `clear_step` on the step grid ("at or after"), and checks `clear_step · step_ns ≤ horizon_ns`. It also
        enforces the admitted kinds, the source-freeze refusal and the overlap refusal.
     3. **Remote relay boundary.**
        - `HubChannel` uses an AF_UNIX `SOCK_SEQPACKET` socket, connected or listening. A listening socket admits
          one peer of the same uid.
        - Frames are closed, canonical and at most 4 KiB, with a sequence per direction.
        - The relay entries and the assurance kinds are armed at the hub only after the source unit is bound and
          live. Their reports are validated to the exact step.
     4. **Clock source and step hold.** On `hold`, Maestro checks the entry, the phase and the step, applies or
        clears through the unchanged `ProcessBoundary` and launcher operation, and acknowledges (`applied`,
        `cleared` or `refused`).
        - A wrong step, a skipped point, an off-grid clock, a rewind, a sequence gap or an unknown entry ends the
          run (`XVERSE-FAULT-SIMTIME-PROTOCOL`, dispatcher code `ML-SCHEDULE-FAULT-CLOCK`). Maestro then sends
          `close`.
     5. **Evidence.** Each apply and clear detail carries `simulatorNs`, `simulatorStep`, `hostNs` and the mode,
        beside the Maestro tick. The intent carries the declared ns, the steps, `stepNs` and the boundary mode.
        The worker's statement schema is unchanged.
     6. **Single-domain admission.** The binding must name the one admitted domain (L-1).
        - `admit_schedule` refuses a held freeze while any D-4c value is unknown, and checks the thaw bound
          (`(clear − onset) · max_step_host_s + 2 · handshake_s ≤ cadence − health_scan_seconds`) and the hold
          bound.
        - The binding is rederived in the worker, `encode_configuration` and `_verify_prepared`.
   - **Tests.** `tests/thesis_lite/faults/test_simtime.py` has 55 cases:
     - the flag;
     - the binding's validation (9 cases);
     - the L-8 reproduction without a binding and admission with one;
     - unchanged bytes without a binding;
     - the domain and source checks;
     - exact ns and grid rounding;
     - the simulator horizon;
     - 9 refused entry shapes;
     - overlap and disjoint windows;
     - `delay-ns` and the assurance kinds;
     - `delay-ns` refused in tick mode;
     - the D-4c refusal (3 partial bindings), the thaw and hold refusals, and the `decode_schedule` round trip;
     - message-only admission;
     - the frame codec (8 malformed frames and an oversized encode);
     - the stream-socket refusal and a sequence gap;
     - the listening channel's single peer;
     - the scheduler against a fake hub:
       - arming waits for the live source;
       - the full hold, apply, ack, clear and ack sequence, with relay reports and both clocks;
       - 9 protocol violations;
       - a report before arming;
       - a refused freeze;
       - `finish` thawing a freeze that was not reached;
       - `finish` marking an uncleared relay incomplete;
       - `cancel`;
       - never-due entries;
     - the worker's decoding of the binding;
     - the dispatcher's channel type check;
     - **two composed native runs.** On the real persistence worker, broker, launcher and children (pauses 40),
       with a fake hub thread:
       - the step-hold freeze of `sink-instance` (steps 30 and 40) and a remote-relay `loss` (steps 20 and 25)
         both end `cleared`;
       - the acks are exactly `[(apply, applied, 30), (clear, cleared, 40)]`, and the hub receives `close`;
       - the Argus intent modes are `step-hold` and `remote-relay`, and the apply steps are 30 and 20;
       - the closure report is complete and the unit's health is resumed;
       - the missing-channel run ends `ML-SCHEDULE-FAULT-CLOCK`.

     The composed freeze run passed 6 of 6 repetitions, at load about 4.5–5.4.
   - **Mutation controls (run, then reverted; the rebuilt wheel was byte-identical).**
     - Without the exact-step check, the wrong-step case fails.
     - With `thaw_check` disabled, both admission cases fail.
   - **Installed-wheel runs.** The wheel is `d0eabe60a7e4e632c21b9fc200a048a296ff9bff088bebb1d1141daf858eaa7e`, built
     from the worktree with `src/` equal to `92fc2643b`. One pytest process per batch:
     - **Batch 1 (19 files): 403 passed**, 0 failed, 0 skipped, in 237 s at load 5.1–6.3. The files are:
       - faults `simtime` 55, `resolve` 13, `scheduler` 23, `relay_kinds` 4, `process_ops` 4 and `maestro_run` 11
         (U-ADM-03b equal to main);
       - maestro `preparation` 23, `preparation_rejections` 21, `projection_discriminating` 2, `schedule_plan` 48,
         `admission` 73, `persistence` 29, `persistence_config_bound` 12, `dispatcher` 18, `shared_dispatcher` 3,
         `lazy_dispatcher` 13, `runtime_entry` 8, `runtime_admission` 40 and `permit_release_path` 3.
     - **Batch 2 (9 files): 234 passed**, 0 failed, 0 skipped, in 231 s at load 6.2–8.5. The files are flows
       `harness_faults` 15, and maestro `collection_plan` 24, `coverage` 48, `launcher` 22, `schedule_worker` 15,
       `stabilization_s1b_broker` 26, `stabilization_stack_load_failures` 22, `coverage_producers` 33 and
       `bootstrap` 29.

     The logs are in `evidence/simtime/`. The full installed-wheel regression, DV12 and CAPA are not run here;
     the coordinator arranges them with the independent review.
   - **Residuals (open).**
     - **R1. No real hub.** The hub side (compat #4) and the harness wiring (blueprints #5) do not exist. The
       channel contract is exercised only against fake hubs, one in a test thread.
     - **R2. D-4c is unmeasured.** `max_step_host_s`, `handshake_s` and `hold_bound_s` are unknown, so every
       schedule with a freeze is refused at admission, as intended. Message-only schedules are admitted.
     - **R3. Peer authentication.** The channel checks only the peer's uid. Binding the peer to the U2 process or
       cgroup is open.
     - **R4. Handshake latency.** Maestro polls the channel once per dispatcher cycle, so the handshake is at least
       one cycle (at least the 0.05 s poll plus statement time). The simulator is held for that time. D-4c must
       measure it under load.
     - **R5. Tick horizon.** The Maestro tick horizon bounds the simulator-time window.
       - An entry whose step is not reached before the last tick ends `cancelled`: `XVERSE-FAULT-NEVER-DUE`, or
         `XVERSE-FAULT-SIMTIME-NOT-REACHED` for a freeze, which is then thawed.
       - The run can still succeed in that case. The harness must check the fault outcomes for PAIR-1.
     - **R6. A hub that never connects or arms.** Its entries end never-due, and Maestro sets no arming
       deadline. A deadline (fail-closed) is a candidate for the review.
     - **R7. Relay semantics are hub-side.** Loss selection, stale replay, delay rounding and `items` are
       recorded by Maestro but not verified.
     - **R8. Assurance variants.** The proposal variants are not carried in descriptors (AD-11, AD-27).
     - **R9. Hub contract constraint.** The hub may not send `time` before every entry is armed.
     - **R10. Error text.** A `delay` with neither delay parameter now reports "exactly one of", not "lacks
       required parameter". The code is unchanged (`XVERSE-FAULT-PARAMETER`).
     - **R11. Still to do.** The independent review, the full run, DV12 and the CAPA step.

3. **Independent review of findings 1 and 2 (written at 15:36:30 2026-10-24).** Reviewer: an independent Claude
   agent that did not write the increment. Scope: `5b011644a`, `321df989e`, `d7c33172c`, `92fc2643b` and `920f7e6e6`
   on `b40acce49`. **Verdict: PASS WITH NOTES.**
   - **Nothing blocks the decisive full run.** With no hub and with the D-4c values unknown, no live fault run is
     possible, and the tick mode is byte-identical.
   - **M1, M2 and M3 must be repaired, or explicitly accepted by the author, before the first live run with
     simulator-timed faults** (the compat #4 and blueprints #5 integration). Message-only schedules are admissible
     today, so M1 and M3 apply as soon as a hub exists.
   - **What was checked, and the result.**
     - **Installed wheel.** `sha256sum` of the cache wheel gives
       `d0eabe60a7e4e632c21b9fc200a048a296ff9bff088bebb1d1141daf858eaa7e`. The installed `xverse` tree equals `src/`
       at `920f7e6e6` (`diff -rq`). `src/` is unchanged since `92fc2643b`, and the only difference is the unpackaged
       `xcom`.
     - **Rerun.** One pytest process on the installed wheel, over faults `simtime`, `resolve`, `scheduler` and
       `maestro_run`, and maestro `schedule_plan` and `preparation`: **173 passed** in 81 s, load 6.0–6.8.
     - **Root cause (question 1). Confirmed.** The compiler keeps exact ns. `resolve.py` gains only the `delay-ns`
       refusal, and XDL and the compiler are unchanged in the diff. The L-8 reproduction test passes.
     - **Byte identity without a binding (question 1). Confirmed independently, and wider than the suite shows.**
       - **Method.** I exported `b40acce49` and `920f7e6e6` (`src`, `tests`, `xdl`) and prepared four plans under
         each, with the installed interpreter and each tree's own sources.
       - **Result.** The lifecycle digest and the canonical-byte hash are **identical** for a fault-less plan
         (`952c6b93…`) and for **three tick-mode plans with faults**: stale plus crash, freeze, and `delay-ticks`.
       - **The suite tests less than this.** `test_plans_without_binding_keep_their_bytes`
         (`test_simtime.py:87-92`) checks only that `faultClock` is absent. `U-ADM-03b` (`test_maestro_run.py:170-188`)
         compares only a fault-less plan, and against a sibling checkout at whatever revision that checkout is (L4).
     - **Resolution (question 2).**
       - `onset = ceil(at/step)` and `clear = onset + ceil(duration/step)`, and `clear·step_ns ≤ horizon_ns`
         (`simtime.py:180-183`).
       - The kind and collection pairs are closed, and a freeze of `source_unit` is refused.
       - Arbitration and `delay-ticks` are refused, and so are repeated ids.
       - Overlap is refused per target, including windows that only touch (`second.onset ≤ first.clear`). That is
         conservative and acceptable, and the ADR could say so.
       - A zero-duration freeze works, with two handshakes at one step (probe P5).
     - **Channel (question 3).**
       - The frame types and key sets are closed, and the JSON must be canonical, at most 4 096 B, with no NaN.
       - The sequence must rise by exactly 1, starting at 1.
       - `simNs == step·step_ns`, and the step never goes back. A report must come at the exact pending step.
       - Arming waits for `source_live()` and a connected peer, and no report is accepted before every entry is
         armed.
       - Every violation sets `run_failed` with an `XVERSE-FAULT-SIMTIME-*` diagnostic, which the dispatcher maps to
         `ML-SCHEDULE-FAULT-CLOCK` (`dispatcher.py` `_advance_faults`).
     - **Admission (question 5).**
       - A held freeze is refused while any D-4c value is `None`.
       - The checks are `handshake_s > hold_bound_s` → HOLD, and
         `held_steps·max_step_host_s + 2·handshake_s ≤ min(cadence) − n·operation_seconds` → THAW
         (`schedule_plan.py:172-183`).
       - Message-only schedules need no D-4c value. This matches the "WP-10 fault relay" row's inequality.
     - **Evidence (question 6).** Apply and clear decisions carry `simulatorNs`, `simulatorStep`, `hostNs` and the
       mode, and relay decisions also carry `items`. The intent carries `atNs`, `durationNs`, `onsetStep`,
       `clearStep`, `stepNs` and `boundaryMode`. The worker statement schema is unchanged.
     - **Capability flag (question 7).** It is a static `True`, pinned by a test. The name and shape match the
       blueprints probe at `18201fe` (`admission.py:121`, `getattr(platform, "SIMULATION_TIME_TRIGGERS", False) is
       True`). It honestly claims only that the code exists.
     - **Mutation claims (question 8).** I did not rerun them, because the worktree is read-only to me. They are
       plausible from the tests. The test gaps are given under M1 to M3.
   - **Issues.**
     - **M1 (MEDIUM; does not block the decisive full run; repair before the first live fault run): the channel's
       EOF fails the run even after every entry is final.**
       - **The cause.** `receive` turns an empty read into `XVERSE-FAULT-SIMTIME-CHANNEL` (`simtime.py:370`).
         `advance` keeps reading on every tick (`:619`), and so does `finish` (`:671`), whatever the entry state.
       - **Probe.** A relay `loss` is applied and cleared, so every entry is `cleared`. The hub then closes its
         socket, as U2 does when its stop step ends the process inside the tick loop. The next `advance` sets
         `run_failed` (`XVERSE-FAULT-SIMTIME-PROTOCOL: XVERSE-FAULT-SIMTIME-CHANNEL`), and the dispatcher would end a
         successful run with `ML-SCHEDULE-FAULT-CLOCK`.
       - **Why the tests miss it.** The composed test's hub thread keeps its socket open until Maestro sends `close`
         (`test_simtime.py:542`). A real Maestro unit cannot.
       - **Effect.** It fails closed, but every live fault run would fail at teardown.
       - **Repair.**
         - Define the channel's lifetime in the ADR: EOF is benign once every entry is final, or once the source
           unit's stop step has begun. EOF with an entry still pending stays a failure.
         - Stop reading once every entry is final.
         - Add a test in which the hub exits after its last report.
     - **M2 (MEDIUM; not reachable until D-4c is measured; repair or accept before the first live freeze): Maestro
       cannot see whether the hub actually held the step (PAIR-1).**
       - **The gap.** ADR decision 5 says "the hub resumes only on `ack`", but Maestro accepts frames the hub sent
         before it could have received the ack.
       - **Probe P1.** `hold(apply, 30)`, then `time(31)` and `time(35)`, all queued at once. Maestro freezes, acks,
         and accepts both `time` frames.
       - **Probe P2.** `hold(apply, 30)` then `hold(clear, 40)`, back to back. Maestro freezes, thaws, and records
         `cleared`. A hub that never held, or that runs ahead, therefore passes undetected. Under it, the freeze
         onset is no longer equal across the paired runs in simulator time.
       - **Repair.** Any of these would detect it:
         - refuse every hub frame that was already queued when the ack was sent: everything read after a `hold` in
           the same `receive` batch, and any further frame read before the ack's send completes;
         - or require a `resumed` frame, or an `ackSeq` echo, before any frame with a later step.

         Add tests for P1 and P2.
     - **M3 (MEDIUM; R5 and R6; repair or accept before the first live fault run, message-only included): a
       declared fault that never happens leaves a successful run.**
       - **Probes.** In P3 the hub connects and never arms, and in P4 it arms but never reaches a step. In both,
         `finish` gives `cancelled` for every entry, with `run_failed=False` and `incomplete=False`.
       - **The weak behaviour is pinned.** `test_never_applied_entries_end_cancelled_never_due`
         (`test_simtime.py:422-425`) asserts `not incomplete`.
       - **Why this is weaker than tick mode.** Tick mode refuses unreachable entries statically (horizon). In
         simulator time, reachability depends on the hub and on the Maestro tick horizon (R5), and R6 sets no
         arming deadline.
       - **Effect.** A paired fault run whose faults never fired, because a hub was missing, disconnected or slow,
         is indistinguishable from a successful one at the platform level. It relies on the harness reading every
         outcome.
       - **Repair.** Make an armed or declared entry that is unreached at `finish` (`_end`, `simtime.py:629-650`)
         mark the run incomplete, or a declared invalid-run code. Add an arming deadline in Maestro ticks or host
         time, past which the run fails closed. If the author prefers the harness to own this, record that as a
         decision, and pin the harness check in blueprints #5.
     - **L1 (LOW; R3).** Peer authentication is by uid only, and every Maestro unit runs under that uid. **Before a
       live run:** prefer the connected form, a socketpair whose peer end is passed only to U2 at spawn, so there is
       no listening path. Otherwise check the peer's `SO_PEERCRED` pid against the source unit's cgroup, which
       Maestro holds. An accidental extra peer already fails closed (single-peer rule).
     - **L2 (LOW): `horizon_ns` is only as good as the caller's value.** It is supplied by the caller. Nothing
       derives it from the scenario (wp10 §4 asks for the scenario horizon, AD-25) or checks it against the Maestro
       tick horizon (R5). Record that blueprints #5 must derive it from the frozen scenario, and consider refusing a
       binding whose `horizon_ns` exceeds what the Maestro plan's active ticks can cover.
     - **L3 (LOW): two thaw bounds that could disagree.** The blueprints admission (`18201fe`) checks the
       inequality against a declared `FreezeBound.thaw_bound_s`. The platform uses `min(cadence) − n·operation_seconds`.
       Both must pass, so this is fail-closed, but the two bounds can disagree. Align the definitions in #5, or
       record which one governs.
     - **L4 (LOW): the byte-identity tests are weaker than the claim.** Pin the lifecycle digest of at least one
       **tick-mode plan with faults** as a literal from base `b40acce49`. Make `U-ADM-03b` pin its reference
       revision rather than read a sibling checkout's current HEAD.
   - **Residuals R1 to R11 (question 9).**
     - **R1, R2, R4 and R7 to R11** are honest.
     - **R3** stands, with the wiring constraint in L1.
     - **R5 and R6** are understated as residuals. They are M3, and need a fail-closed rule or an explicit author
       decision.
     - **Proposed additions:**
       - **R12.** Channel lifetime at teardown (M1).
       - **R13.** Hold verification (M2).

4. **Dispositions of finding 3, recorded before any repair (written at 15:43:13 2026-10-24).**
   - **Basis.** Thesis `specs/002-assured-aeb/decisions.md`, rows "WP-10 #3 review dispositions" (15:38) and
     "WP-10 #4 relay alignment" (15:42, R-1 and R-2). Both were decided by the coordinator under the author's
     delegation of 2026-10-24 and are flagged for the author's review. This finding records them; it accepts no
     run and no evidence.
   - **Order.** This finding, then ADR amendment ST-2 (decisions 4, 5 and 7, residuals R12 and R13), then code,
     then finding 5 (implementation and installed-wheel verification).
   - **Repaired in this increment.**
     - **M1, channel lifetime.** A hub end-of-file once every entry is final and no hold, report or `resumed` is
       pending is a benign `hub-closed` event, recorded in the run's fault evidence. It is not a protocol failure.
       An end-of-file with anything pending stays `XVERSE-FAULT-SIMTIME-PROTOCOL`. Sending `close` to a hub that
       has already closed must not fail the run. A composed native test has the fake hub exit at its stop step, the
       case the review reproduced at `simtime.py:370`, `:619` and `:671`.
     - **M2, hold verification.** A new hub-to-Maestro frame `resumed`, with the closed keys `entry`, `phase`,
       `step` and `ackSeq` (beside `v`, `kind` and `seq`). After every hold `ack` that Maestro sends, the next hub
       frame must be `resumed`, echoing that ack's `seq` and the same entry, phase and step. Any other frame first
       is a protocol failure. The reviewer's probes become tests: P1, `hold(apply, 30)` then `time(31)` and
       `time(35)` with no `resumed`, is refused; P2, `hold(apply)` then `hold(clear)` back to back, is refused.
     - **M3, structural reachability (no new numeric bound).**
       - The hub must send `armed` for an entry before it reports any step at or after that entry's `onsetStep`,
         else a protocol failure.
       - At `finish`, an entry never armed, or not applied although the hub reported its onset step, is a protocol
         failure.
       - An entry whose onset step the hub never reached ends `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`) and
         sets `incomplete=True`: the treatment never happened.
       - `test_never_applied_entries_end_cancelled_never_due` (`test_simtime.py:422-425`), which pins the old
         behaviour, is replaced.
     - **R-1 (WP-10 #4), arming completeness.** The Maestro-to-hub `arm` frame gains two closed keys: `count`, the
       number of entries in the arming batch (equal in every `arm` frame), and `index`, 1-based and rising by 1.
       Tests cover a wrong count, an index gap and a duplicate.
     - **L4, byte identity.** The lifecycle digests of tick-mode plans with faults, and of the fault-less plan, are
       pinned as literals computed from base `b40acce49` (a clean export of the base, not the candidate).
   - **Not repaired here; residuals and obligations of WP-10 #5 (wiring), recorded in the ADR.**
     - **L1.** Before any live run, the peer is given a connected socketpair end at spawn, or its cgroup is
       checked.
     - **L2.** The caller derives `horizon_ns` from the scenario duration and checks it against the tick horizon.
     - **L3.** The blueprints admission computes the thaw bound by the platform definition (decision 3).
     - **R-2 (WP-10 #4).** The platform keeps one time domain per Maestro form. WP-10 #5 maps the blueprints
       domain `carla-simulation` onto `experiment-time`.
   - **Residuals adopted.** R12 (channel lifetime) and R13 (hold verification), as the review proposed.
   - **Implementation reading, stated before code so that review can check it.**
     - **R9 is superseded by M3.** Finding 2 required every entry to be armed before any other hub frame (R9). M3
       states the rule per entry: `armed` must precede any step at or after that entry's `onsetStep`. Keeping R9
       would make that rule vacuous, and would refuse a conforming hub that sends `time` frames while it arms. So
       a `time` frame below every unarmed entry's onset is accepted. The hub now learns that arming is complete
       from `count` and `index` (R-1).
     - **`hub-closed` evidence.** It is one worker `fault` statement, phase `outcome`, outcome `hub-closed`, on the
       chain of the first entry in listing order, after that entry's final outcome. The worker statement schema is
       unchanged. In simulator-time mode an entry takes at most four statements (arbitration is refused there), so
       the admitted budget of five per entry still covers this one extra statement.
     - **Finish with a protocol failure.** If `finish` detects a protocol failure (M3), the remaining entries end
       `cancelled` (`XVERSE-FAULT-CANCELLED`), and the dispatcher ends the run `ML-SCHEDULE-FAULT-CLOCK`, mapped
       as `_advance_faults` maps it. Before this, `_finish_faults` checked only `incomplete`.
     - **Unchanged.** A freeze that was applied, but whose clear step was not reached before `finish`, is still
       thawed by Maestro and ends `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`) without `incomplete`: its onset
       happened, and Maestro cleared it itself. A `resumed` still outstanding at `finish` or `cancel` is not
       checked (R13).

5. **Implementation of amendment ST-2 and installed-wheel verification (written at 15:50:47 2026-10-24).**
   - **Commits.**
     - `88379942c`: finding 4, the dispositions, before any code.
     - `ce62b8fbc`: ADR amendment ST-2, before any code.
     - `c3aadc745`: the code and tests. The source diff from `b40acce49` is now 11 files, +922/−11. ST-2 itself changes
       `simtime.py`, `faults/__init__.py` (the flag comment only) and `dispatcher.py` (`_finish_faults`).
   - **What changed.**
     - **M1.**
       - `HubChannel.receive` no longer raises on an end-of-file. It sets `peer_closed` and reads nothing after it.
       - `SimTimeFaultScheduler._hub_eof` decides the end-of-file. When every entry is final and no `resumed` is
         pending, it records `hub_closed` and one `outcome`/`hub-closed` statement on the first entry in listing
         order. Otherwise it is a protocol failure ("the hub closed the channel with … pending").
       - `close` sends nothing after the hub's end-of-file and never raises.
     - **M2.**
       - `resumed` is in `HUB_FRAMES`, and `ackSeq` is an integer of at least 1.
       - Each hold `ack` is sent through `_ack`, which records `(entry, phase, step, seq)`.
       - The next frame must be the matching `resumed`. Any other frame, or a `resumed` with no ack pending, is a
         protocol failure.
     - **M3.**
       - In `_handle`, a step at or after the onset of an unarmed, non-final entry is a protocol failure. This
         replaces R9's rule, "every entry armed before any other frame".
       - In `finish`, an entry never armed, or one not applied although the hub reported its onset step, is a
         protocol failure. Its remaining entries end `cancelled` (`XVERSE-FAULT-CANCELLED`).
       - An unreached onset ends `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`) and sets `incomplete`.
       - `FiniteDispatcher._finish_faults` maps a simulator-time `run_failed` at `finish` to `ML-SCHEDULE-FAULT-CLOCK`
         (or `-APPLY`), before the `incomplete` check. This is restricted to `SimTimeFaultScheduler`, so tick mode is
         unchanged.
     - **R-1.**
       - `arm` carries `count` and `index`.
       - `check_arm_batch` (exported) refuses a wrong or unequal count, an index gap or an index that does not start
         at 1, a duplicate index or entry, and a truncated batch.
       - Maestro checks its own batch before it sends.
     - **L4.** `BASE_DIGESTS` pins five plans: the fault-less plan, the fault-less plan with the sensor, stale plus
       crash, freeze, and `delay-ticks`. For each it pins the lifecycle digest and the sha256 of the canonical bytes.
       - **Method.** The literals were computed from `git archive b40acce49 src tests xdl` with the cache venv
         interpreter (`-I`, the export's own sources first on `sys.path`, asserted).
       - **Result.** An export of the candidate gives identical values.
       - **Cross-check.** The fault-less plan with the sensor is `952c6b93…`, the value finding 3 reported.
       - **Records.** The script and its output are in `evidence/simtime/l4-base-digests.py` and
         `l4-base-digests-b40acce49.json`.
       - **Not changed.** `U-ADM-03b` still reads the sibling checkout. The literals now pin the fault-less plan
         independently.
     - **`SIMULATION_TIME_TRIGGERS`** stays `True`, and only its comment changed. Every requirement of option A
       still holds.
   - **Tests.** `test_simtime.py` now has 78 cases, up from 55.
     - **Added.**
       - 5 L4 literal cases.
       - The arm-batch refusals (7 shapes in one case).
       - Per-entry arming, two cases: a step below the onset is accepted and the onset is refused; a report for an
         unarmed entry is refused.
       - The unreached onset, giving `cancelled` NOT-REACHED and `incomplete`.
       - 4 finish refusals: source never live; never confirmed armed; a reached onset without apply, for a freeze
         and for a relay.
       - The reviewer's probes P1 and P2.
       - 4 `resumed` echo cases (wrong `ackSeq`, `step` or `phase`, and no ack pending) and the `resumed` codec.
       - Benign end-of-file, including no `close` sent to a closed hub.
       - 3 pending end-of-file cases: a report, a `resumed`, and a clear hold.
       - The composed native run, now parametrized. The fake hub arms until `index == count`, answers every ack
         with `resumed`, and in the new case **exits at its stop step**. That run succeeds with both entries
         `cleared`, records one `hub-closed` statement at simulator step 40 on the first listed entry, and leaves
         the closure report complete.
     - **Replaced.** `test_never_applied_entries_end_cancelled_never_due`, which pinned the old behaviour, and
       `test_report_before_arming_completes_is_a_protocol_failure`, which pinned R9.
   - **Mutation controls (run, then reverted; the rebuilt wheel was byte-identical).**
     - **No `resumed` check:** P1, P2, 3 echo cases, the benign end-of-file, the pending-hold end-of-file and the
       composed exit run fail. That is 8 cases.
     - **Every end-of-file a failure:** the benign end-of-file and the composed exit run fail.
     - **No finish reachability check:** the 4 finish refusals fail.
   - **Installed-wheel run.**
     - **Wheel.** `5e91e36c2b7d6a325133dfb9c8eed718c17058cafff9d2e65c072e98f6d16013`, built by `s1a3-venv.sh build`
       from `src/` at `c3aadc745`.
     - **Tree check.** `diff -rq` of the installed `xverse` against `git archive c3aadc745 src` differs only in the
       unpackaged `xcom`. The installed `xverse_xdl` adds only its `profiles` and `schemas` data.
     - **Result.** One pytest process over faults `simtime`, `resolve`, `scheduler` and `maestro_run`, and maestro
       `schedule_plan` and `preparation`: **196 passed**, 0 failed, 0 skipped, in 81 s at load 4.6–4.8. The log is
       `evidence/simtime/related-suites-st2-c3aadc745.log`. Finding 3's rerun of the same files gave 173, and the 23
       new cases account for the difference. Another agent's compat test process ran on the host at the same time.
     - **Not run here.** The decisive full regression (`run-z-quiet-loop.sh`), DV12 and CAPA are left to the
       coordinator, after re-review.
   - **Residuals.**
     - R12, R13 and the WP-10 #5 obligations (L1, L2, L3 and R-2) are recorded in ADR ST-2.
     - R5 and R6 are closed structurally by M3. An unreached entry now makes the run incomplete, and an entry never
       armed fails it, with no deadline.
     - R9 is superseded (finding 4).
     - R1–R4, R7, R8, R10 and R11 stand.
     - **Hub dependency.** The compat hub relay (WP-10 #4) must implement `resumed`, `count`/`index`,
       arm-before-onset and the benign close exactly as in ST-2. Until it does, the frame contract is exercised only
       against fake hubs.

6. **Focused re-review of amendment ST-2 (written at 15:55:52 2026-10-24).** Reviewer: the same independent Claude agent
   as finding 3. Scope: `88379942c..00bd41ba2` (`88379942c`, `ce62b8fbc`, `c3aadc745` and `00bd41ba2`).
   **Verdict: PASS WITH NOTES.**
   - **Nothing blocks the decisive full run.**
   - **N1 should be decided by the author before the first live freeze run**: repaired, or accepted as recorded.
     That run cannot happen while D-4c is unknown.
   - **Installed wheel.** `sha256sum` of the cache wheel gives
     `5e91e36c2b7d6a325133dfb9c8eed718c17058cafff9d2e65c072e98f6d16013`. The installed tree equals `src/` at
     `00bd41ba2` (`diff -rq`; only `xcom` differs).
   - **Rerun.** One process, faults `simtime`, `scheduler` and `maestro_run`: **112 passed** in 64 s, at load about
     8. An unrelated project's pytest was running at the same time.
   - **The finding 3 probes, re-run on the installed ST-2 wheel.**

     | Probe | Before ST-2 (finding 3) | Now |
     | --- | --- | --- |
     | P1: `hold(apply,30)` then `time(31)`, queued before the ack | accepted | **protocol failure**: "hub sent time before resumed for ack 2" |
     | P2: `hold(apply)` then `hold(clear)`, back to back | accepted, ended `cleared` | **protocol failure**: "hub sent hold before resumed" |
     | M1: hub EOF after every entry is `cleared` | run failed (CHANNEL) | **benign**: `run_failed=False`, `hub_closed` recorded, `finish` cleared and not incomplete |
     | EOF while an entry is still pending | — | protocol failure ("closed the channel with entry … pending") |
     | P3: connected, never armed | cancelled, run succeeded | **protocol failure**: "fault:f-frz was never armed" |
     | P4: armed, onset never reached | cancelled, run succeeded | `cancelled`, **`incomplete=True`** |

     M1, M2 and M3 of finding 3 are repaired as the "WP-10 #3 review dispositions" row specifies. Arming now carries
     `count` and `index` (`check_arm_batch`), as in the "WP-10 #4 relay alignment" row R-1.
   - **The implementer's judgment calls.**
     - **(a) R9 replaced by the per-entry M3 rule.**
       - **What it guarantees.** Each frame with a step is checked: no step at or after an unarmed entry's onset
         (`simtime.py:589-592`). An entry never armed by `finish` fails the run.
       - **What is lost.** Only that the platform no longer insists that the whole batch is armed before any frame.
         The batch-level rules (CC-1, one seed) are hub-side re-checks in any case, and the compat relay is
         stricter: it sends every `armed` before its first tick.
       - **Conclusion.** Nothing needed for safety or PAIR-1 is lost, and the compat relay is compatible with the
         rule.
     - **(b) `hub-closed` on the first entry's chain.** **LOW, documented** (ADR ST-2, decision 4).
       - **Probe.** The first entry's chain is `[apply applied, clear cleared, final cleared, outcome hub-closed]`.
         The worker maps `final` to phase `outcome`, so that entry carries **two** `outcome` events, and the last
         one is `hub-closed`.
       - **Who is affected.** `closure_report` and `Chain.status` are unaffected, because they read the apply and
         clear phases, and `scheduler.outcomes` is right. A reader that takes the last `outcome` event per entry
         as final (a blueprints oracle or a PAIR-1 checker) would misreport entry 1 in **every** benign run.
       - **Fix.** Either carry the event as the final outcome's detail, or give readers a stated rule: an entry's
         final outcome is the first `outcome` whose value is in `FINAL_OUTCOMES`. If the rule is chosen, add it
         to the WP-10 #5 obligations and test it.
     - **(c) The `_finish_faults` mapping in simulator-time mode only. Confirmed.**
       - The new branch is guarded by `type(self._faults) is SimTimeFaultScheduler` (`dispatcher.py:1421-1426`),
         so the tick-mode finish path is unchanged.
       - **Plans.** A clean export of `00bd41ba2` gives the same lifecycle digests and canonical-byte hashes as
         base `b40acce49` for my four plans (fault-less, stale+crash, freeze, delay-ticks; the values are in
         finding 3). The pinned L4 literal for stale+crash, `3e2bd8af…`, equals the value I computed independently.
     - **(d) Ends at `finish`.**
       - **N1 (MEDIUM; not reachable before D-4c; decide before the first live freeze): a freeze cut short leaves a
         successful run.**
         - **Probe d1.** A freeze is applied at step 30 and its clear step (40) is never reached. `finish` thaws it,
           ends it `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`), and sets **no** `incomplete`. ST-2 states
           this.
         - **Why it matters.** The treatment then lasted less than declared, so PAIR-1 needs equal freeze windows
           and this run is not one of them. It is also asymmetric with a relay entry applied and not cleared, which
           is `incomplete-clearing`.
         - **Recommendation.** Set `incomplete` for a freeze applied but not cleared at `finish`. Otherwise the
           author should record why a truncated freeze is an acceptable treatment.
       - **N2 (LOW; R13, documented).** A `resumed` still outstanding at `finish` is unchecked.
         - **Probe d2.** The clear hold is acked, the hub never sends `resumed`, and `finish` gives `cleared` and
           a successful run.
         - Failing on it would race the last tick, so do not fail. Record a `resumed-outstanding` detail on the
           entry's final statement so that the evidence shows the unconfirmed handshake.
   - **Residuals.**
     - R12 and R13 are honest.
     - R13's "not proof against an adversarial peer" is correct, and stays tied to L1 (the connected socketpair or
       the cgroup check) in WP-10 #5.
     - The L1–L3 obligations are recorded for WP-10 #5 as the dispositions row requires.

7. **Dispositions of finding 6, recorded before any repair (written at 15:59:43 2026-10-24).**
   - **Basis.** The thesis `specs/002-assured-aeb/decisions.md` row "WP-10 #3/#4 re-review notes" (15:58). The
     coordinator decided it under the author's delegation of 2026-10-24, and it is flagged for the author's review.
     The compat items of that row (compat N1 and N2) belong to the hub relay and are not part of this repository.
   - **Order.** This finding comes first. Next is one ADR commit, which updates the ST-2 text (decisions 4 and 7,
     R13) and adds a short amendment note ST-2a. The code follows, and finding 8 records the verification.
   - **Repaired.**
     - **N1, a freeze cut short.** A freeze applied whose clear step is never reached by `finish` is thawed and ends
       `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`). It also sets `incomplete=True`, as a relay entry
       applied and not cleared does. A shortened freeze is a different treatment under PAIR-1.
     - **(b), the placement of `hub-closed`.** It moves into the detail of the final outcome event of the first
       entry in listing order. There is no second `outcome` event, and each entry has exactly one final outcome.
       The statement budget is unchanged.
     - **N2, an outstanding `resumed`.** A `resumed` still outstanding at `finish` or `cancel` is recorded in
       the evidence, in the final outcome detail of the entry whose ack is unconfirmed. It does not fail the run,
       because failing would race the last tick (R13).
   - **Implementation reading, stated before code.**
     - **Final statements are deferred.** In simulator-time mode, an entry's final outcome is still decided when it
       happens (`outcomes` changes at once). Its one `final` statement is emitted when the scheduler ends, at
       `finish` or `cancel`, in compiled listing order. Only then are the benign end-of-file and an outstanding
       `resumed` known. The `apply` and `clear` statements keep their own ticks. Each entry still takes at most
       four statements: intent, apply, clear and final.
     - **Detail keys.** The keys are `hubClosed` (`simulatorStep`, `hostNs`) and `resumedOutstanding`
       (`phase`, `step`, `ackSeq`), inside the 512-byte detail bound.
     - **A consequence on failing runs.** On a failing run, the final statements are now sent on the dispatcher's
       best-effort cancel path. A final that cannot be sent leaves the chain without its `outcome` event. The
       apply and clear phases, which `closure_report` reads, are unaffected.
   - **Tests.**
     - N1: a truncated freeze sets `incomplete`.
     - `hub-closed` sits in the first entry's final detail, with exactly one final per entry, both in a unit case
       and in the composed native run where the hub exits.
     - N2: an outstanding `resumed` is recorded at `finish` and at `cancel`, and the run does not fail.
     - The L4 literals are re-verified unchanged (tick mode).

8. **Implementation of note ST-2a and installed-wheel verification (written at 16:08:34 2026-10-24).**
   - **Commits.**
     - `e5fc3425f`: finding 7.
     - `41684db51`: the ADR ST-2 text and note ST-2a.
     - `691e6f8bb`: an ST-2a addendum, recorded before the code commit (see "Deviation" below).
     - `0d84b6f9a`: the code and tests. The source diff from `b40acce49` is now 14 files, +949/−12.
   - **What changed.**
     - **N1.** In `finish`, any entry not yet final sets `incomplete` before `_end`. This covers an unreached onset
       and a freeze applied but not cleared, which is thawed and ends `cancelled` (NOT-REACHED).
     - **Final statements.** `_finalize` only decides the outcome. `_emit_finals`, called from `_end`, emits each
       entry's one `final` statement in compiled listing order:
       - `hubClosed` (`simulatorStep`, `hostNs`) goes on the first entry;
       - `resumedOutstanding` (`phase`, `step`, `ackSeq`) goes on the entry whose hold ack is unconfirmed;
       - a statement is never re-sent, even when the scheduler ends twice.

       The benign end-of-file no longer writes a statement of its own.
     - **N2.** An outstanding `resumed` at `finish` or `cancel` is recorded and does not fail the run.
   - **Deviation (recorded in ADR addendum `691e6f8bb` before the code commit).**
     - **The failure.** With finals deferred to `finish`, both composed native runs ended
       `ML-SCHEDULE-COLLECTION-INCOMPLETE`.
     - **The cause.** A temporary worker trace, reverted and never committed, showed `ML-COLLECTION-EVENT-ACK` in
       `collection_runtime._record_collect`. Its "previous ordinal + 1" check ignores fault events, so a fault
       event cannot be the last event before collection. That is a latent constraint of every mode.
     - **The repair.** The outcome journal keeps `fault_ordinal` (`lifecycle_evidence.py`, set in
       `schedule_evidence._append_fault`), and `_record_collect` includes it.
     - **For re-review.** This touches the collection path, which is outside the dispositions row.
   - **Tests.** `test_simtime.py` has 81 cases, up from 78.
     - **Changed.**
       - `test_finish_thaws_a_freeze_whose_clear_step_was_not_reached` now asserts `incomplete` (N1).
       - The benign end-of-file case asserts that no final statement is emitted at the end-of-file. After `finish`
         there is exactly one final per entry, both `cleared`, and `hubClosed` only on the first listed entry.
       - The composed native runs, both parametrizations, assert exactly one `outcome`-phase event per entry, and
         `hubClosed` (step 40) only in the exit case.
     - **Added.**
       - An outstanding `resumed` at `finish`: `cleared`, the run is not failed, and `resumedOutstanding` is
         recorded.
       - An outstanding `resumed` at `cancel`: recorded on the frozen entry only.
       - Exactly one final per entry when `finish` is followed by `cancel`.
     - **Control.** Without the collection repair, the two composed runs fail, as observed above.
   - **L4.** The five literals are unchanged. A clean export of `0d84b6f9a` gives values identical to
     `l4-base-digests-b40acce49.json` (`evidence/simtime/l4-digests-0d84b6f9a.json`), and the five L4 cases pass.
   - **Installed-wheel run.**
     - **Wheel.** `02efbb2c154a4ae503a0b8725c03b788baca6e6e72cecccea079419d52fd7d8a`, from `src/` at `0d84b6f9a`.
     - **Tree check.** `diff -rq` of the installed tree against `git archive 0d84b6f9a src` differs only in the
       unpackaged `xcom`, plus the `xverse_xdl` data.
     - **The six suites, in one process** (faults `simtime`, `resolve`, `scheduler` and `maestro_run`; maestro
       `schedule_plan` and `preparation`): **199 passed**, 0 failed, 0 skipped, in 82 s at load 5.3. The log is
       `related-suites-st2a-0d84b6f9a.log`.
     - **Collection, afterwards in a second process.** Because the collection path changed, maestro
       `collection_runtime` and `lazy_dispatcher` gave **35 passed** in 41 s. The log is
       `collection-suites-st2a-0d84b6f9a.log`.
     - **Host load.** Another agent's compat pytest was running on the host during both runs.
     - **Not run.** The decisive full regression, DV12 and CAPA are left to the coordinator.
   - **Residuals.**
     - N1 is closed.
     - R13 now records an outstanding `resumed` instead of leaving it unchecked.
     - The adversarial-peer limit stays tied to L1.
     - The other residuals are unchanged.

9. **Independent focused Codex re-review of ST-2a (2026-10-24), PASS for entry to full regression.**
   - Input: `dfc39081e` (product `0d84b6f9a`), findings 6 to 8 and ADR ST-2a/addendum. Reviewed the changed
     finish/cancel/final-emission paths, their new tests, and the collection-continuity change outside the original
     dispositions row. No product repair was made.
   - A truncated applied freeze is thawed and marked incomplete; final statements are deferred and emitted at most
     once in listing order; benign hub closure and an outstanding resumed ACK are details of that final, not new
     outcomes. An unconfirmed resumed frame at end is recorded rather than turned into a last-tick race failure.
   - The collection change preserves exact original-writer ordinal continuity: the fault ordinal is updated only
     after the fault event is flushed, and collection takes the maximum of fault, lifecycle and retained-intent
     ordinals. It does not count a fault event as lifecycle coverage or create a new writer/ownership claim.
   - The previously recorded 199 related installed-wheel and 35 collection tests remain evidence of product
     `0d84b6f9a`; this re-review has not re-run them or the full suite. The full clean installed-wheel run, DV12,
     CAPA step 17 and delegated acceptance remain mandatory. No acceptance or platform merge is claimed.
   - Carried: L1 peer/cgroup validation, L2 horizon derivation, L3 thaw-bound derivation belong to WP-10 #5;
     other finding 8 residuals, the declared load envelope and CAPA limits remain unchanged.
   - Run scheduling must preserve the rc.1 soak at 00:00 on 2026-10-25: one heavy test process at a time and no new
     full-run admission too late to accommodate the driver's existing outer and preparation deadlines before 23:00.

10. **Independent full-regression finding and successor test design (Codex, 2026-10-24).**
    - Candidate `12dfb21e1b6bfdd8533b2b2058ddba184fa88c8b` failed the installed-wheel full run:
      3037 passed, 1 failed, 1 skipped, 39 subtests passed in 2791.75 s. Maximum sampled load was 6.15;
      this is a decisive failure, not a load-discarded attempt. Receipt and full nested traceback are retained in
      `evidence/affa19/stabilization-s1a3/platform-regression-20261024i-codex-1/`. No DV12/CAPA/acceptance follows.
    - The sole outer failure is the existing Argus assembled-regression test. Its child suite fails
      `test_listening_channel_accepts_exactly_one_peer` before exercising the channel: `listener.bind(path)`
      raises `OSError: AF_UNIX path too long`. The child's inherited pytest temp hierarchy makes the pathname
      exceed the platform socket limit. The child otherwise reports 2742 passed, 1 skipped, 39 subtests passed.
    - Repair design, recorded before code: only this listener test will use an explicitly short, unique
      `tempfile.TemporaryDirectory` under `/tmp` for its socket. Keep the genuine pathname-bound Unix
      SOCK_SEQPACKET listener, both real peers and all existing assertions. Use context/finally cleanup for
      sockets/channel and directory. Remove the unused tmp_path fixture dependency. No product or protocol change.
    - Verification: independently review the successor diff; repeat the focused case with a deliberately long
      pytest base directory, then repeat the complete installed-wheel regression. Preserve the failed run and
      the existing DV12/CAPA step-17 gates. The lane-admission skip is the dedicated-driver gate, not evidence
      of lane admission. No acceptance or merge is claimed.

11. **Independent Codex read-only review of short-path test repair (2026-10-24), PASS for repeated verification.**
    - Reviewed exact test-only candidate `088046f40c49d721a814d2bfbbbd493fdb970b86`, its design checkpoint
      `e2d3dafd1be5757c9e6f9d3b522b66ed9d11f6d2`, finding 10 and the exercised `HubChannel.connected/close` paths.
      The reviewer did not author the repair and made no product or test modification.
    - The test now creates a unique short directory explicitly below `/tmp`, independently of pytest's inherited
      base directory or `TMPDIR`. It retains a genuine pathname-bound `AF_UNIX/SOCK_SEQPACKET` listener, both real
      peer connections, the initial disconnected/first-connected assertions and the second-peer `FaultError`
      assertion. No production path constraint or channel behavior is weakened to make the test pass.
    - Directory and listener contexts, nested peer contexts and `finally: channel.close()` preserve cleanup after
      success or assertion failure. Re-closing the listener is harmless; after the peer contexts close, the channel's
      best-effort close handles the refused send and releases its accepted socket/listener. The unused `tmp_path`
      fixture is removed. No protocol, source package or installed wheel content changes in this repair.
    - Performed only source/diff inspection, an in-memory syntax check and AST checks for the removed fixture
      dependency and explicit short temporary-directory parent; `git diff --check` passes. No pytest, socket
      exchange, wheel build or framework import was run by this reviewer. The coordinator's deliberately long-base
      focused execution and complete installed-wheel regression remain required on this successor; the failed
      3037-pass run cannot support acceptance. DV12, CAPA step 17, delegated acceptance and rc.1 soak scheduling
      gates remain as recorded in findings 9–10. No merge or acceptance is claimed.
    - **Coordinator-run evidence, reported after this source review:** the exact repaired listener test passed
      **1 passed in 0.67 s** with base directory
      `/dev/shm/codex-deliberately-long-nested-pytest-base-20261024/one-more-directory-for-the-parent-and-child-hierarchy`,
      using the original installed-wheel venv (product unchanged), no `PYTHONPATH` and plugin autoload disabled.
      This was run by the coordinator, not the independent reviewer. It resolves the focused long-path reproduction;
      the complete successor regression and downstream gates remain pending.


12. **Decisive successor evidence and delegated acceptance (Codex, 2026-10-24; flagged for author review).**
    - Actual installed-wheel attemptj at4bedba9:3038passed,1 dedicated-lane skip,39subtests in3086.69s,
      3039collected,exit0,no outer timeout/unknown descendant cleanup. Installed/frozen source equality and source
      archive binding are recorded. Maximum sampled load11.99 is retained explicitly; this passing functional
      regression is not a new timing-performance guarantee beyond the existing declared load envelope. Failed
      attempti at6.15 and its nested socket-path failure remain retained, not relabelled or discarded.
    - Official code-scope DV12 genuinely executed and accepted this exact run/candidate with no blockers, unchanged
      six input hashes, matching run/candidate code identity45a5960c8b30c4655be4e4a526c1b41ec5da48573817e0c334da1daac53d5268,
      actual exit0 and clean owned completion. GateSHA9705d8471ea415b01b1d06c98dbc69a3d63ea544126b194a007f740a4ba33c6c.
      Capture/builder source defects were independently found and repaired before their genuine execution;
      originals, designs/reviews, exact tools and actual execution receipts are retained under affa19.
    - CAPA17 actual registerSHA0d6f40f28635ccb1c801fa00552f0fe8e0b3f04008c91c65338d5324b1da3b07 has57records/784bindings,
      exact parentbf39b087 (56records/757bindings). Official schema/evidence verification and parent preservation
      both exit0. Independent actual source/JSON review PASS verifies all prior rows/plans/bindings unchanged and
      all27additions/exact tested-source association. New collection-continuity observation stays TRIAGED/HYPOTHESIS;
      no cause verification, reproducer/effectiveness window or sustained effectiveness is invented. Historical
      approvals remain historical; generated child root accepted/merged flags stayfalse.
    - **Accept implementation under the standing author's delegation of2026-10-24, flagged for author review.**
      Acceptance is only WP10#3/ST2a plus the independently reviewed test-only socket repair. Evidence and actual
      CAPA review are in affa19/codex-capa17-execution-20261024, with delegated-acceptance.json. Final delivery still
      requires isolated main assembly, whole-tree/test-scope equivalence check and merge/push; this finding alone
      is not a delivered-main claim.
    - L1 UID-only peer authentication, L2/L3 derivation and D4c/live wiring remain successor gates. No new source-
      process identity, adversarial hold, M1/principal/scientific/live result is claimed. No rc.1 soak input/tag
      changes, protocol value, CAPA promotion or automatic canonical-note update is authorized by this acceptance.
