# Separate read-only review of provider v1 (before repairs)

18 October 2026; same-agent component review, not independent full-candidate review.
Candidate source is uncommitted successor of a31d093. Read-only pass inspected
providers.py, owner.release changes, bootstrap._holder and real-process tests.

1. MINOR test contract: copy.copy raises the existing original-authority TypeError;
   the new negative test expects only ValueError. Preserve rejection, correct test.
2. MINOR observation exposure: external cancellation can leave historical cached
   ready values exposed by observations/observation until another operation. Make
   returned snapshots conservative when the original latch is closed; historical
   immutable values are observations, never transferable execution authority.
3. MINOR numeric validation: enormous integer policy values may raise OverflowError
   from math.isfinite instead of the stable diagnostic. Add explicit conversion
   rejection and exercise timeout/cadence/attempt bounds, including bool.
4. ADVISORY packaging/full integration: source Query-based running probes are
   existence-only and caller-driven. Initial helper admission, durable bootstrap
   permit authentication/consumption, normal M3 outcomes, autonomous finite cadence,
   reverse lifecycle, restart/recovery, U7/U8 and full M1/runtime gates remain open.
   Do not describe this as a full LifecycleProvider implementation or application
   readiness. Exact compiled graph is consumed; no competing ordering is permitted.
5. ADVISORY verification scope: add a discriminating step-dependency graph case,
   readiness-query exhaustion, and a guard argument substitution rejection. Real
   failure at final guard must leave dependent marker absent. Full regression and
   installed-wheel identity/reaping audit still required.

Findings are recorded before successor repairs. Existing bootstrap finding 14 has
an explicit comparison repair; its no-dispatch control must pass. No acceptance,
merge, principal experiment or independent review is claimed.

6. MINOR fixture validity (v2 focused result): removing the original flow leaves
   an Experiment observation referring to sample-flow. The XDL validator correctly
   rejects before any bootstrap starts. Retarget that observer to the original source-instance while removing the flow,
   so no inter-unit flow edge exists and only the original step dependency can
   block the dependent. Preserve the failed focused log.

7. MAJOR bounded-call admission (read-only v3 pass, before repair): the facade
   accepts a legacy ReleaseOwner backed by synchronous coordinator M3/Argus I/O.
   Its release revalidation can therefore block inside storage. Require the actual
   original isolated PersistenceClient before exposing this facade; preserve the
   legacy primitive API separately. Add a genuine local-owner rejection control.
   This does not close external bootstrap/kernel-stall bounds.

## Read-only successor pass after repairs

Final v4 focused verification: 35 passed. Findings 1, 2, 3, 5, 6 and 7 have
successor repairs or discriminating controls; finding 4 remains an explicit full
integration limitation. Full source/installed regressions still required at this
pass. No new source repair requested by this pass. Parent bootstrap finding 14 is
covered by a changed-alias rejection with unchanged native request sequence.

The exact final guard is typed and bound to the original owner, target, deadline
and active facade operation. It invokes real original Query RPCs; neither supplied
observations nor callbacks authorize Release. Flow and step-only dependencies have
separate real compiled-XDL controls. SIGSTOP issuer loss is deliberately resumed
for the original helper's bounded drain; it is not reclassified as crash recovery.
The API accepts already staged resources, supports running existence only and
requires caller-driven sampling. This is neither full provider admission nor
normal lifecycle evidence closure. Independent full-candidate review remains open.
