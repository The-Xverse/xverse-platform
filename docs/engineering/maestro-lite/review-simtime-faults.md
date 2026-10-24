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
