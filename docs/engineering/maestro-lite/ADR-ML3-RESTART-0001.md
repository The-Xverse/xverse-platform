# ADR-ML3-RESTART-0001 — Explicit restart during a blocking finite lifecycle

2026-10-19. Selected engineering refinement for implementation. The author answered
the lifecycle choice with “propose something and go”; choose active-run requests.
This does not promote the external ML-DESIGN-2026-10-03-v2 DRAFT or accept full17.

`FiniteDispatcher.run` remains blocking through original terminal publication and
writer closure. Add opt-in `allow_restarts=True` before execution, requiring original
v6 collection/native broker/controller and sealed future contexts. Derive finite
extra request/event/controller capacity before any effects; never enlarge frozen
limits, active end, health freshness, operation caps or terminal reserve.

`restart(run_id, unit_id, *, permit, generation, deadline)` submits control intent
only, returning an original retained ticket. Require the exact original sealed
future permit object, next generation, issued/live current unit and fixed caller
end <= original active end. One queued/in-progress request globally; conflicts and
unknown/unadmitted inputs reject without consuming a permit. Exact repeats return
the retained ticket; changed repeat ends reject. `restart_result(ticket)` is inert.

Only the original run thread performs mutation, at safe points after complete
phases with no unfinished step for the unit. Before mutation, revalidate normal
transitive-dependent release; never auto-stop a live dependent to satisfy a parent
request. Expired requests and failed preconditions receive rejected results. Once
old stop begins, failure is conservative: fail result, close start authority and
perform original cleanup. Never roll back permit consumption or replay an uncertain
generation operation. Close the mailbox before terminal cleanup and reject pending
work; terminal/result retrieval cannot reopen the writer.

Use normal old stop/cleanup, fresh frozen original C1, original prepare/ADVANCE,
Stage/bind/start and genuine fresh dependency probes. Preparation/ADVANCE/Stage/start
share one original operation end; each preceding normal stop/cleanup retains its
own original cap and the caller/active end. Add optional caller deadline bounding
to existing C1 creation, preserving default behavior and rejecting unknown options.

After authentic transition, dispatcher updates its binding pin and creates a new
teardown view for the current generation; old view and all receipts remain retained.
Carry unaffected-unit caches forward unchanged. Worker independently rejects a
generation transition during an unfinished logical step; only successful original
generation preparation retires the old schedule-handle pin. Actual new scheduled
facts still require an original worker-issued handle. One scheduled start remains.

Original coverage includes every sealed future context, every actual generation and
unused future rows. Fixture declares source artifacts as generation1 and restarted
leaf artifacts as current generation2 before execution. No old-generation artifact
claim is inferred from a reused marker filename. Productive controller replacement
is a subsequent composition task, not simulated by swapping the current controller.

Expected controls: genuine leaf generation2 and closed independent report; unchanged
single scheduled start; foreign permit/unknown ticket/expired/conflicting requests;
live-dependent parent reject without stop/permit use; original ends and cleanup for
every issued generation; authentic old/new handles retained; no writer replay.
