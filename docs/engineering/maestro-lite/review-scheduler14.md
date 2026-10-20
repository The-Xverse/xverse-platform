# Scheduler read-only integration findings

18 October 2026. Same-agent separate inspection, not independent full-candidate review.
Record findings before the successor edits that address them.

1. MAJOR composition finding: OutcomeJournal numbers its producer from len(events),
   but that shared retained-mirror register also contains teardown and future step
   producer events. A later probe after a scoped stop/step record would jump its
   producer sequence and fail the client's exact next-sequence check. Retain the
   shared mirror register but give the outcomes producer its own counter. Exercise
   actual interleaved step/tick/stop and health records in full dispatcher tests.
2. ADVISORY scope: already-issued unit composition does not establish initial
   bootstrap/environment admission, full helper closure, restart/recovery, U7/U8,
   global M1, nine runtime cases or independent full review/acceptance. Preserve all
   open full P3 tasks and downstream phases 4–9.
3. MINOR initial expected fixture: 20 active seconds in the two-unit fixture still
   fits 128 calls (100 worst-case calls); the test wrongly expects rejection.
   Use 40 seconds for the over-cap control and retain exact independent counts.
4. MAJOR pure-admission inspection: individually finite, tiny positive cadence
   values can make active_seconds/period overflow to infinity before ceil().
   Reject nonfinite or over-cap derived slot counts explicitly with ScheduleError
   before constructing health obligations. Do not loosen any cadence or limit.
5. MINOR test inspection: the renewal-positive test immediately infers running
   from a Release ACK plus one Query. ACK only proves unfreeze; exec may still be
   pending. Verify through the actual bounded readiness facade before asserting
   running. This changes no product timeout or application-readiness claim.
6. MAJOR admission integration: a missing Query needs a normal factual failure
   record in addition to the unit terminal disposition when storage remains usable.
   Reserve at most one such diagnostic per admitted unit before any Release and
   enforce that one-use limit in the forthcoming schedule journal. It cannot mint
   a successful probe or replace a missing normal outcome.
7. MAJOR verification harness: composition-v1 reused an installed wheel built before
   the failure-diagnostic admission reserve changed. Its worker independently rejects
   the changed schedule bytes, so six scheduled cases fail at Init as expected for
   that mismatch. Do not count the mixed-source run as current verification. Rebuild
   and reinstall the actual wheel after product changes, record module identity,
   and repeat the affected composition checks. Preserve the raw failed run.
8. MAJOR actual scoped-composition counterexample: after a dependent's confirmed
   cleanup, _jobs still compares its retained launcher recipe with a missing live
   descriptor, rejecting later phases/final teardown. Skip exactly the original
   controller's already-confirmed cleaned units in the live-job snapshot; preserve
   their cached historical facts in final reverse order. Do not skip unknown or
   unconfirmed resources or adopt a replacement descriptor.
9. MINOR read-only scoped-health inspection: next_health_deadline now filters out
   stopped units, but a just-released first unit can precede its first observation.
   The current nonempty released set then leaves min() with an empty iterator.
   Return no sampled-health deadline until an actual released-unit observation
   exists, retaining the operation's own finite readiness deadline. Exercise the
   property immediately before the genuine first Query; do not invent readiness.
10. MAJOR full-dispatch admission inspection: CatalogLauncher.stage invokes
    ReleaseOwner._stage_claim, which performs one additional persistence
    revalidation per unit. The draft counts claims and the two Release checks but
    misses staging. Include this call and the full active-through-teardown health
    horizon, dispatcher begin, phase AND terminal-disposition annotations, and
    normal terminal/abort reserve before any Release. Keep exact independent
    count fixtures and both-side canonical rederivation; do not hide exhaustion.
11. MAJOR dispatcher integration inspection: a health-scan reserve alone does not
    account for root plus individual-gate renewal RPCs. Health and lease service
    must share a finite deadline margin and admission must count the shorter
    resulting health spacing. Service health before renewal when due, cap renewal
    operations by health and original lease ends, and fail closed if both cannot
    fit. Preserve separate root/gate scopes; never infer cadence after a slow RPC.
12. MINOR measured fixture budget: dispatcher-v1-observed shows a whole start
    operation reaches ML-PERSIST-TIMEOUT at 0.15048 s. That includes all admitted
    prerequisite probes, durable writes, revalidations and Release, not one Query.
    Admit a 0.5 s whole-operation budget and a 5 s cadence/freshness for the new
    full-dispatch fixture; keep product maxima and all inherited stale/timeout
    controls unchanged. This is host fixture calibration, not a scientific bound.
13. MAJOR read-only error-path inspection: dispatcher catches only selected
    exception classes, allowing an unexpected coordinator/decoder exception to
    bypass its cleanup/result path. Catch ordinary Exception around execution and
    cleanup/report attempts, preserving independent cancellation and bounded C1.
    Test an unexpected owned callback-body failure with no product fault switch.
    Also pin the original persistence BootstrapChild to the same root as the gates
    and launchers; do not rely only on a matching manager/digest.
14. MAJOR failure-provenance inspection: the draft turns every dispatcher error
    into a unit health-loss/unknown observation, even for a tick-window or prepare
    error, and may name a dependent when its prerequisite Query failed. Retain an
    exact private failed-probe context at the original facade; record unknown
    health only for that actual attempted unit. Other errors receive factual
    validation failure in their actual phase/run scope, never a fabricated probe.
15. MAJOR remaining-budget inspection: an original caller can legitimately perform
    extra revalidation RPCs before begin. Recheck actual remaining capacity against
    the full admitted future budget on both client and worker before any Release;
    an originally sufficient total cap is not proof that enough remains now.
16. MAJOR cleanup-path inspection: if normal terminal health/lease service throws,
    _cleanup currently exits before calling the independent reverse fallback.
    Always attempt that original fallback within the existing reserve after
    cancelling normal service. Do not renew a caller deadline or report missing
    normal records as complete. Exercise failure before implicit final cleanup.
17. MINOR cancellation/eligibility inspection: explicit operator cancellation is
    distinct from a failed health sample and needs cancelled dispositions. Runtime
    stop/cleanup eligibility must also reflect actual dependent cleanup and stopped
    state, beyond static compiler windows. Preserve the prepared ordering among
    actions that are actually admissible and handle implicit horizon stop normally.
18. MINOR verification inspection: the remaining-budget test directly changes a
    client counter, proving only that local comparison. Replace it with genuine
    original-session revalidation calls under a 128-call admission, then verify
    both the front door and independent worker Begin reject before any Release.
    Retain actual public schema/M3-hash snapshots for all dispatcher branches.
19. MAJOR implicit-cleanup inspection: a cleanup step without an explicit stop
    implicitly stops its unit at the horizon. Its runtime eligibility must require
    actual dependent cleanup before dispatching that implicit stop, even when its
    compiler rank comes first. Apply the same independent condition in the worker
    and dispatcher, preserving deterministic order among admissible work. Exercise
    the discriminating reverse-rank cleanup-only fixture.
20. MINOR discriminating fixture: changing cleanup IDs does not change the
    compiler's declaration-index tie order. The first implicit-cleanup red run
    fails its fixture precondition (sink still ranks first), not the product.
    Reverse the two independent cleanup declarations and rerun the actual control
    before repairing finding 19; retain the original failed fixture separately.
21. MAJOR bounded-phase inspection: when the explicit caller window is shorter
    than the configured per-unit cap, normal stop/cleanup can consume the entire
    caller window, leaving no promised emergency reserve. Split the actual
    remaining window (including a shortened final run window) into 60/40, not the
    larger configured cap. Exercise a genuine M3 lock with a short scoped stop;
    C1 release must still be attempted before that same original caller end.


Final separate read-only inspection, after finding 21 repair: reviewed independent
budget rederivation and actual remaining-capacity checks, original holder/root/
handle pins, typed active statement one-use checks, runtime dependent cleanup,
phase/duration/tick completion, health/lease deadline reserves, worker ACK/M3/Argus
validation, failure provenance, independent cancellation and terminal fallback.
No additional component finding identified. This is same-agent component review;
independent full-candidate review remains open. Findings 1, 4, 6, 8–11, 13–17,
19 and 21 have product repairs; 3, 5, 7, 12, 18 and 20 concern fixture/evidence
corrections. Finding 2 retains the full integration boundary. Current verification
must use the rebuilt installed wheel and frozen successor inputs. Historical failed
runs and pre-repair archives are retained; they are not current passing receipts.
