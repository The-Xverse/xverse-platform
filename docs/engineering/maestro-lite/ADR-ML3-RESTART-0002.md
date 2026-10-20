# ADR-ML3-RESTART-0002 — Separately admitted explicit restart operation

2026-10-19. Selected before successor implementation. Refines RESTART-0001 after
actual evidence and D3 contract review; does not change historical admissions.

The external DRAFT D3 defines operation timeouts <=5 seconds with an immutable end
min(run_active_end, dispatch_time + timeout). A whole explicit restart is a distinct
operation from one scheduled lifecycle phase. Current code has no separately
admitted restart timeout and applies the scheduled phase0.5s to preparation,
ADVANCE, Stage, final durable revalidation and both live probes together. Actual
recorded durable costs show this accidental coupling exhausts the end. Do not
repair it by retrying a failed operation, extending its end or changing prior pins.

Add optional restart_operation_seconds to pure ScheduleAdmission. Its canonical
version3 body and digest include this finite positive <=5s field, also <= active
seconds and the conservative health service period. Worker rederives every field.
Without it, versions1/2 retain identical serialized bytes and restart opt-in rejects.
The existing phase operation_seconds, active end, terminal reserve, per-unit cleanup,
probe timeouts, freshness and lease budgets remain unchanged.

After old stop and cleanup under their original phase caps, new generation
preparation through actual release/fresh probes receives exactly one end from the
separately admitted restart timeout, clipped by original caller/active/health/lease
ends. A native ACK/permit receipt cannot extend it. Each provider probe still has
its original own timeout. Ticket submission cannot select or enlarge this cap.

For the owned new-admission fixture choose restart1.0s, phase0.5s and active4.8s,
all frozen before execution. These are engineering fixture parameters, not scientific
protocol thresholds or physical timing guarantees. Preserve all a–d failures as
evidence for their exact old0.5s admissions. This does not close deferred initial-
startup timing, teardown135, complete full17, independent review or M1 gates.
