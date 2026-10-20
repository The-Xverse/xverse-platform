# Durable start/probe outcome unit specification

Inputs: genuine original facade/current observation, exact issued full handle,
original private claim, original HostDeadline; no caller-provided public payload.
Client validates identity before dispatch; changed/duplicate sample arguments reject.
Worker validates closed request fields, claim continuity, action/provider/execution,
original handle continuity, session, finite sample time/freshness, increasing sample
sequence and original combined-graph dependency receipts. A new successful start
outcome is emitted once per generation only. Running is existence-only.

Order: actual Query -> exact client validation -> worker M3 append+fsync -> exact
public M3 projection -> Argus append -> public flush acknowledgement -> returned
immutable public receipt -> readiness/dependent use. No append-only ready credit.
First successful sample emits started + probe + ready; later successful sample emits
health. Failed initial samples emit probe failed without started/ready. Repeated
false after start emits health and health-loss. Public event causation follows the
original intent and acknowledged predecessor/event references. Host/UTC domains
remain separate; source timestamps are not reconstructed/backdated from durable ACK.
All public annotation payloads must validate against the unchanged external v2.0
schema and accepted Argus reader. Complete lifecycle coverage remains incomplete.

Use real original bootstrap/storage/catalog/C1/gate composition and read actual M3
and Argus bytes. Verify positive two-unit sequencing, source-ref hashes, exact
schema, sanitized fields, normal start once, health records, copied/forged/stale/
duplicate/foreign-session rejection, zero pending-exec ready credit, journal loss,
Argus flush failure, blocked actual storage locks and cancellation. Storage failure
must prevent dependent marker execution while C1 remains available. Record findings
before repairs. Full source and isolated installed-wheel regressions, exact hashes,
native builds and actual owned cleanup/reaping audit are required.
