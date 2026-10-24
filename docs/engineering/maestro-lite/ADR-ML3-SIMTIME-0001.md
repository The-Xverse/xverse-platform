# Simulation-time fault triggers, a remote relay at the clock-source unit, and the step-hold handshake

ML3-SIMTIME-2026-10-24-v1; parent `b40acce49`. It is recorded before product code (`review-simtime-faults.md`
finding 1).
- **Basis:** thesis `specs/002-assured-aeb/design/wp10-fault-relay.md` §4, and the "WP-10 fault relay" row of
  `decisions.md`. Option A was decided there under the author's delegation of 2026-10-24 and flagged for the
  author's review.
- **Maturity:** an engineering candidate. It is not M1, not AEB evidence, and accepts or authorizes no run.
- **Amends:** `faults-lite/detailed-design.md` (amendment ST-1), `ADR-ML3-SCHEDULER-0001.md` (note ST-1) and
  `ADR-ML3-PERSISTENCE-0001.md` (note ST-1).

## Context

- A fault declared in simulator time is refused (L-8). The compiler keeps it exactly in nanoseconds, but
  `xverse.faults.resolve` reads that value as a Maestro tick.
- Message faults in a Maestro run act on in-process fixtures with no traffic.
- No unit can report simulator time to Maestro.
- Maestro ticks are not simulator time (GA-34, L-6), and PAIR-1 needs equal onsets in simulator time.

## Decision

1. **Declaration: a binding on the preparation, not XDL.**
   - `prepare_lifecycle(..., fault_clock=SimulationClock(...))` declares the clock-sourced simulation domain.
     The binding's fields:

     | Field | Rule |
     | --- | --- |
     | `domain` | equals the single admitted simulation domain (L-1) |
     | `source_unit` | the component instance id of the clock-source unit (U2), which must be a deployed unit |
     | `step_ns` | integer in 1..10^10 |
     | `horizon_ns` | integer in `step_ns`..3.6·10^12 |
     | `max_step_host_s`, `handshake_s`, `hold_bound_s` | each `None` (unmeasured, D-4c) or finite, in (0, 5] |

   - The binding is part of the canonical bytes and the lifecycle digest only when it is present. Plans without
     it are byte-identical to rc.1.
   - With a binding, every fault entry is simulator-timed. Its trigger is `time` in `ns`, `us`, `ms` or `s` in the
     bound domain, and its duration is in one of those units. A `tick` unit or a `declared-order` trigger is
     refused (`XVERSE-FAULT-SIMTIME-TRIGGER`).
2. **Resolution (`xverse.faults.simtime`).**
   - `at_ns` and `duration_ns` are the compiled exact values.
   - `onset_step = ceil(at_ns / step_ns)`, and `clear_step = onset_step + ceil(duration_ns / step_ns)`. The
     relay and the hold act at the first step boundary at or after the declared time (AD-30).
   - **Horizon.** `clear_step · step_ns ≤ horizon_ns`, else `XVERSE-FAULT-HORIZON`.
   - **Overlap.** Two entries on one target with overlapping step windows are refused (`XVERSE-FAULT-OVERLAP`).
     The arbitration parameter is refused in this mode.
   - **Kinds** (anything else is `XVERSE-FAULT-SIMTIME-KIND`):

     | Kind | Target | Mode | Parameters |
     | --- | --- | --- | --- |
     | `delay` | `flows` | `relay` | `delay-ns`, an integer in 1..6·10^10 (`delay-ticks` is refused here, and `delay-ns` in tick mode) |
     | `loss` | `flows` | `relay` | `every` or `loss-ratio` |
     | `stale` | `flows` | `relay` | none |
     | `assurance.proposal-unsafe`, `assurance.proposal-mistimed`, `assurance.evidence-loss` | `flows` | `relay` | none; executable at this boundary only (K-13) |
     | `freeze` | `componentInstances` | `hold` | none; not on `source_unit` (`XVERSE-FAULT-SIMTIME-SOURCE`) |

3. **Admission (`admit_schedule`).**
   - **Unmeasured values.** If a `hold` entry exists and any of `max_step_host_s`, `handshake_s` or
     `hold_bound_s` is `None`, the schedule is refused (`ML-SCHEDULE-FAULT-SIMTIME-UNMEASURED`).
   - **Hold bound.** `handshake_s > hold_bound_s` is refused (`ML-SCHEDULE-FAULT-SIMTIME-HOLD`).
   - **Thaw bound.** For each hold entry, `(clear_step − onset_step) · max_step_host_s + 2 · handshake_s` must not
     exceed `thaw_bound_s`, else `ML-SCHEDULE-FAULT-SIMTIME-THAW`. Here `thaw_bound_s = min(cadence) − health_scan_seconds`
     of the same admission.
   - **Message-only schedules** need no D-4c value, because no step is held.
   - **Rederivation.** The schedule bytes are unchanged; `decode_schedule` re-runs the same checks.
4. **The channel (`HubChannel`, supplied by the trusted caller).**
   - **Socket.** AF_UNIX `SOCK_SEQPACKET`, either connected or listening. A listening socket accepts exactly one
     peer, and that peer's `SO_PEERCRED` uid must equal Maestro's. A second peer is refused.
   - **Frames.** Canonical UTF-8 JSON (sorted keys, no whitespace), at most 4 096 bytes, with
     `{"v": 1, "kind", "seq"}` and closed key sets.
   - **Sequence.** `seq` starts at 1 and rises by 1 in each direction.
   - **Hub clock.** `simNs == step · step_ns`, and the hub's `step` never decreases.
   - **Maestro to hub:**
     - `arm`: `entry`, `fault`, `faultKind`, `mode`, `collection`, `element`, `atNs`, `durationNs`, `onsetStep`,
       `clearStep`, `parameters`, `seed` and `stepNs`. One frame is sent per entry, after the source unit is bound
       and live.
     - `ack`: `entry`, `phase` (`apply` or `clear`), `step` and `outcome` (`applied`, `cleared` or `refused`).
     - `close`: `reason`.
   - **Hub to Maestro:**
     - `armed` (`entry`), one per `arm`;
     - `time` (`step`, `simNs`);
     - `hold` (`entry`, `phase`, `step`, `simNs`);
     - `applied` and `cleared` (`entry`, `step`, `simNs`, `items`);
     - `failed` (`entry`, `phase`, `step`, `simNs`, `reason`).
   - **Protocol failure.** Maestro reads at most 64 frames per poll and never blocks. Each of the following ends
     the run (`XVERSE-FAULT-SIMTIME-PROTOCOL`), and Maestro then sends `close`:
     - a frame outside this contract;
     - an unknown entry;
     - a phase out of order;
     - a hold or report at a step other than the entry's `onsetStep` or `clearStep`;
     - any hub frame at a step beyond a pending hold or report point.
5. **The step-hold handshake: Maestro decides.**
   - **Apply.** At `onsetStep` the hub holds the simulator and sends `hold(apply)`. Maestro checks the entry and
     the step. It applies the freeze through the unchanged `ProcessBoundary` and the owned launcher `freeze`, then
     sends `ack`, with `outcome: refused` if the apply failed. The hub resumes only on `ack`.
   - **Clear.** At `clearStep` the same exchange runs with `thaw`.
   - **Relay entries.** The hub applies and clears them at their steps, and reports both. Maestro validates each
     report and records it.
   - **No role unit.** The schedule never reaches a role unit (FR-028). Only the clock-source unit receives
     descriptors.
6. **Evidence with two clocks.** Each decision is one worker `fault` statement, under the unchanged worker
   rules.
   - Its `detail` carries `simulatorNs`, `simulatorStep` and `hostNs` (Maestro's monotonic ns) beside the Maestro
     tick.
   - The intent carries `atNs`, `durationNs`, `onsetStep`, `clearStep`, `stepNs` and the boundary mode
     (`remote-relay` or `step-hold`).
7. **Run time.**
   - **Keyword.** `FiniteDispatcher(..., fault_clock_channel=None)`, and `_OriginalRuntimeRun(...,
     fault_clock_channel=None)` passes it through.
   - **Missing channel.** A binding with simulator-timed faults and no `HubChannel` is refused at begin
     (`ML-SCHEDULE-FAULT-CLOCK`).
   - **Scheduler.** `SimTimeFaultScheduler` keeps the `FaultScheduler` interface (`start`, `advance(tick)`,
     `cancel`, `finish`, `outcomes`, `run_failed`, `incomplete`, `decisions`), so the dispatcher's tick loop is
     unchanged.
   - **At `finish`:**
     - a freeze still applied is thawed and ends `cancelled` (`XVERSE-FAULT-SIMTIME-NOT-REACHED`);
     - a relay entry applied and not reported cleared ends `incomplete-clearing`, and the run is incomplete;
     - an entry never applied ends `cancelled` (`XVERSE-FAULT-NEVER-DUE`).
   - **On `cancel`.** Active freezes are thawed first, then every entry gets one final outcome, then `close` is
     sent.
8. **Persistence.** The binding travels as an optional `fault_clock` configuration key, present only when
   declared. Every rederivation passes it: the worker, `encode_configuration` and `admission._verify_prepared`.

9. **Public capability contract.**
   - `xverse.faults.SIMULATION_TIME_TRIGGERS` is a module-level `bool`. It is `True` only when every requirement
     of option A is implemented in this package:
     - onset and duration in exact simulator ns (decisions 1 and 2);
     - the horizon check against `horizon_ns` (decision 2);
     - the remote relay boundary at the clock-source unit (decisions 4 and 5);
     - the step-hold freeze handshake (decision 5).
   - It is absent at rc.1. The blueprints admission path (WP-10 #1, candidate `f0ecf6e`,
     `automotive/assured-aeb/admission.py`) probes `getattr(xverse.faults, "SIMULATION_TIME_TRIGGERS", False) is
     True`, and refuses every fault schedule while the probe fails.
   - The flag states only that the code exists. It does not state that the D-4c values are measured, that the hub
     (compat #4) exists, or that any run is admitted. Admission still refuses while those are missing (decision 3).
   - A test pins the name, the type and the value.

## Unchanged

- The tick mode: `FaultScheduler`, the in-process relays, Phase 6 amendment A1, and the tick-mode rules for
  every plan without a binding.
- The native fault operations, the worker statement schema, the request and event accounting (5 statements per
  entry), XDL and the compiler.

## Open (not claimed)

- The D-4c values.
- The hub side (compat #4) and the harness wiring (blueprints #5).
- Authentication of the channel peer as the U2 process. Only the uid is checked here.
- The assurance proposal variants (AD-11, AD-27).
- PAIR-1 conformance of any run.
- Live behaviour.

## Verification before acceptance

- Offline unit tests: resolution, the binding, admission, the channel codec, and the scheduler against a fake hub.
- A composed native dispatcher run with a fake hub thread: a step-hold freeze and a relay `loss`.
- The Phase 5 fault suites, unchanged.
- The full installed-wheel run, DV12 and a CAPA step.
