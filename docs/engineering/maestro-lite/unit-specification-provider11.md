# Process readiness unit contract

Before product code: frozen acceptance cases in provider-expected.json.
Inputs: original ReleaseOwner backed by the actual isolated PersistenceClient; one finite policy per prepared process unit; exact
original registered CatalogLauncher plus its full OwnedResourceHandle; original
HostDeadline. No PID/path/handle-name reconstruction or externally supplied probe
result is accepted. Generation, execution and action identity follow original recipe.
Outputs: immutable observation with exact handle digest, unit, generation, catalog
observe action ID, host session/time, sequence, running-condition result. No normal
M3 outcome, Argus closure, cleanup or full run-ready claim.

Each policy: 0 < cadence <= freshness <= 5 seconds; 0 < timeout <= 5 seconds;
attempts integer 1..3. Reject bool, NaN/infinity, duplicate/missing/unknown policies.
The actual Query deadline is the minimum original deadline and now+policy timeout.
A later deadline never extends an original start. Pending exec can consume the
remaining readiness queries; exited/error/unknown closes starts. Checks before
Release must reprobe prerequisites, reject unreleased or stale/wrong-generation
resources, and validate the entire observation set after the last query.

State: staged -> one Release -> bounded running-condition observation. Any failed
readiness/health/ownership check invalidates readiness and cancels further starts.
Cancellation never waits on the normal nonblocking mutation lock. Repeat start
rejects; no implicit restart, replayed ready cache or success from a sent signal.
Health is sampled only when check_health is invoked; next_health_deadline exposes
the earliest required cadence. A caller that stops polling has no health guarantee.

Verify with real two-unit process XDL, M3/Argus intent and original bootstrap/C1/
launcher/RG06 composition. Markers must prove prerequisite execution and zero
blocked-dependent execution. Include stopped issuer, dead workload, stale result,
wrong handle/session/copy, unsupported condition, original deadline, nonblocking
conflicts, cancellation, and public bootstrap-session replacement. Full source and
installed-wheel regression plus owned-root/helper reaping audit are required.
