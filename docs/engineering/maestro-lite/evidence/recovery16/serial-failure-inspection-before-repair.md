# Finding8 — separate read-only inspection before successor repair

The still-running serialized full run has one reported failure. Collection order
locates it at test_full_dispatcher_result_precedes_full_helper_closure; both outer
and nested paused-tick snapshots now have successful terminal records. Await the
actual terminal traceback before treating that location as the final failure set.

The failing outer closure/dispatcher snapshot has an observe-source dispatch at
18:14:36.238944, then two normal observation records at 18:14:36.295589 and
18:14:36.782217, followed by no completed step. The dispatcher passes one 0.5-second
operation end to ProcessReadiness.check_health, which queries every released unit.
Thus an explicit source-targeted observe performs a second, sink-targeted durable
probe under the same single-unit operation end. The schedule separately admits
health_scan_seconds=number_of_units*operation_seconds for all-unit host service.

Source inspection confirms _effect(observe) uses the all-unit API despite the
step's exact unit binding; the independent worker only requires the target unit's
fresh sample. This is a scope/budget defect, not evidence that recovery needs
larger operation limits or that host-load serialization alone fixes the suite.

Proposed successor: add an exact original-unit health operation with the same
nonblocking original facade/owner and cancellation rules; dispatch explicit observe
through it. Preserve all-unit periodic service, conservative admitted scan/event
bounds, every operation/lease/fixture timeout and all failure controls. Add a real
two-unit regression that proves explicit observe queries only the declared unit.
Record a versioned unit-contract addendum and freeze successor inputs before
source/wheel regression. Preserve both failed full runs and pre-repair source.
No candidate source, test or frozen review file has been changed by this inspection.
