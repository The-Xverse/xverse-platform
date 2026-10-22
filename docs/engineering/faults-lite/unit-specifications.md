# Unit specifications: Phase 5 fault injection

IDs map to thesis verification cases V01–V12. Tests live in `tests/thesis_lite/faults/`.

## `xverse.faults.vocabulary` / `resolve` (V01, V02, V04, V11)

| ID | Test | Expect |
| --- | --- | --- |
| U-FLT-01 | six-kind Scenario resolves | six `ResolvedEntry`; boundary classes process/message/observation; `executable` true; no side effect |
| U-FLT-02 | unknown kind | `XVERSE-FAULT-KIND` |
| U-FLT-03 | target in an unsupported collection / outside the selection | `XVERSE-FAULT-TARGET` |
| U-FLT-04 | overlapping windows on one target without `arbitration` | `XVERSE-FAULT-OVERLAP`; with `reject` → same; with `serialize`/`supersede` → resolved with the policy recorded |
| U-FLT-05 | due tick beyond the last planned tick | `XVERSE-FAULT-HORIZON` |
| U-FLT-06 | due tick between planned ticks | `effectiveTick` = first planned tick ≥ due; both recorded |
| U-FLT-07 | tie at one tick | order `(declaredOrder or inf, faultId)` |
| U-FLT-08 | declared-only hook | `executable` false, parameters validated, `declared-not-executed` later |
| U-FLT-09 | parameter schema | `delay-ticks` < 1, `loss-ratio` ∉ (0,1], `every` < 1, unknown parameter → `XVERSE-FAULT-PARAMETER` |
| U-FLT-10 | durations exact | `durationTicks` == compiled `duration.ticks`; no rounding field |

## `xverse.faults.scheduler` (V03, V04, V05, V11, V12)

| ID | Test | Expect |
| --- | --- | --- |
| U-SCH-01 | same plan/seed twice on relays | identical decision sequences |
| U-SCH-02 | boundary refusal | `failed-to-apply`; run ends as documented failure unless `on-apply-failure: continue` |
| U-SCH-03 | clearing failure | `incomplete-clearing`; `incomplete` true; later entries on the target → not applied, outcome `cancelled` with diagnostic |
| U-SCH-04 | `serialize` | later entry applies at the first planned tick after the earlier clears |
| U-SCH-05 | `supersede` | earlier entry cleared with outcome `cancelled`; later applies at its tick |
| U-SCH-06 | cancellation mid-window | outcome `cancelled`; clearing attempted; evidence emitted |
| U-SCH-07 | foreign/revoked handle | `failed-to-apply` / `clear-failed`; nothing else touched |
| U-SCH-08 | bounded retry | one apply-failed/applied pair per attempt; one final outcome |
| U-SCH-09 | seeded loss | `loss-ratio` decisions identical for equal seeds, different for different seeds; counter-based (no `random` state) |

## `xverse.faults.boundary` relays (V07)

| ID | Test | Expect |
| --- | --- | --- |
| U-BND-01 | delay | items delivered `delay-ticks` later; order preserved; clearing delivers held items |
| U-BND-02 | loss `every` / `loss-ratio` | exact dropped count / seeded pattern; counters frozen after clearing |
| U-BND-03 | stale | last delivered item replayed; fresh items resume after clearing |
| U-BND-04 | sensorDropout | observations suppressed in the window; resume after |
| U-BND-05 | handle binding | handle of another run/entry refused |

## Owned process operations (V06, V12)

| ID | Test | Expect |
| --- | --- | --- |
| U-PRC-01 | `kill` through the native launcher | child reaped (observe reports exited by SIGKILL); helper alive; no other pid signalled |
| U-PRC-02 | `freeze` then `thaw` | `cgroup.events frozen` 1 then 0 observed through the owned cgroup |
| U-PRC-03 | forged token / wrong pid | helper refuses (reply 21 reason 6 or connection closed per existing rules); nothing happens |
| U-PRC-04 | `kill` after the child exited | refused, `failed-to-apply` |

## `xverse.faults.evidence` (V08)

| ID | Test | Expect |
| --- | --- | --- |
| U-EVD-01 | four-event chain | intent → applied → cleared with causation ids; extension fields complete |
| U-EVD-02 | failure chains | intent → apply-failed; intent → applied → clear-failed |
| U-EVD-03 | obligations | `causal-closure` per applied entry; missing closure → run incomplete |

## Maestro admission (V09, V10)

| ID | Test | Expect |
| --- | --- | --- |
| U-ADM-01 | resolvable schedule admitted | `prepare` succeeds; `PreparedLifecycle.faults` populated; digest differs from the fault-less plan |
| U-ADM-02 | unresolvable schedule | `ML-UNSUPPORTED` with the fault code |
| U-ADM-03 | existing fault-less plans | canonical bytes and digests unchanged (Phase 3 suite green) |
| U-ADM-04 | full installed-wheel run | clean on a quiet host; DV12 gate accepted |
