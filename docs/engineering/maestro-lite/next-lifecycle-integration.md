# Next full lifecycle integration — read-only implementation constraints

18 October 2026, DRAFT engineering handoff, not a new acceptance or runtime gate.
External authority remains thesis capability 024 and its full seven P3 tasks.
This follows OUTCOMES12; it does not narrow the requested Lite program.

- `prbc.py::force_cleanup` currently terminates, observes empty and removes C1
  in one operation. A normal stop/cleanup sequence needs distinct bounded
  terminate-and-retain and empty-boundary-release operations. Writing a cleanup
  intent after force_cleanup has already removed C1 would reverse cause/effect.
  Preserve the existing emergency force_cleanup API and its explicit unresolved
  returns. Do not infer direct-child reaping from C1 empty/release.
- `launcher.py::cancel` closes the shared latch; it is an emergency/global path.
  A planned reverse unit teardown needs an original scoped stop observation and
  the issuer's actual wait result while other units retain ownership. Use the
  complete original handle/registry and retained C1; no PID/path discovery.
- `persistence.py::_rpc` bounds a synchronous coordinator wait, but a new automatic
  scheduler cannot claim health cadence merely by polling after a slow start or
  durable write returns. Budget all intervening operation deadlines or supply
  independent admitted health-loss/watchdog supervision. Sampling remains finite;
  continuous/atomic multi-unit health is not established by a polling loop.
- Bootstrap and gate leases are finite and independent. Long runs need original
  scoped renewal before each expiry and within the original generation; a root
  renewal alone cannot silently renew all gates. Cancelled/expired generations
  cannot regain start authority. Full original-owner/guard-loss/M1 stays open.
- The private persistence protocol retains a 128-request cap. Scheduling admission
  must derive its worst-case query/renewal/record/stop/cleanup budget from units,
  prerequisite probes, cadence, attempts and horizon. Do not discover exhaustion
  after partial startup or silently enlarge the cap without an explicit contract.
- Reuse `PreparedLifecycle` combined graph, phase links, windows and deterministic
  ordering. Every declared step, including prepare/observe/stop/cleanup, needs its
  normal record or an honest disposition. No second configuration language or
  start-only scheduler may substitute for the full declared lifecycle.
- Simulation ticks remain separate from host and UTC clocks. Use only an admitted
  tick source; a host delay is not an inferred simulation rate. Blocked tick work
  must not prevent host cancellation/health deadlines. No arbitrary coordinator
  callback may acquire workload authority.
- Extend the original storage worker with closed typed stop/cleanup intent and
  observed outcome records. Failed persistence must leave exact emergency C1
  available, with normal-record gaps retained. OUTCOMES12 only covers actual
  start/probe observations; absent Query/issuer failures still need failure and
  terminal disposition records. No synthetic stopped/cleaned success from signals.
- Keep execution status, issuer/direct-child wait, C1 termination/empty/release,
  Argus in-memory usability/last durable manifest, and U7 lifecycle coverage
  separate in the eventual RunResult. Missing normal records cannot be satisfied
  by later emergency cleanup. Implement both provisional and offline assessment
  against original obligations, then U8 confined collection/results.

Next implement and verify this composition with real owned process fixtures,
finite paused ticks, failed health/readiness, partial-start rollback, reverse
teardown, storage hangs and cancellation. Then finish explicit restart/recovery,
full runtime/M1/admission/source gates, independent full review and acceptance.
All 24 ML-SR, 18 unvalidated source parents, 30 scenario pairs, 90 declared
endpoints and nine runtime cases remain binding. No dissertation experiment is
admitted by this handoff. Keep the complete phases 4–9 backlog downstream.
