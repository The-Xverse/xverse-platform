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
