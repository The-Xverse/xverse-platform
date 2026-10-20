# AFFA and surviving broker unit contract — before implementation

DRAFT engineering controls. Implement the whole selected M1 path and controller
survival contract; do not credit only a local gate, cooperative latch, cached ACK,
registry copied from durable metadata or new wrapper around per-unit cancellation.

Inputs are original XDL-derived admission, exactly pinned native images and private
sealed configuration, original C1/boundary descriptions, actual durable intent and
mirror/flush acknowledgements, same-authority immutable ticket identities and finite
host deadlines. Validate all sets and caps before any workload effect. Reject bool/
NaN/infinity, unknown classes/fields, duplicated units/sequences, stale epoch/session,
forged/cross-run/cross-generation handles and extra/missing file descriptions.

One original authority owns every unit's registry. No disposable operation/controller
worker can create/thaw workload boundaries. Stage is frozen, registered and epoch-
checked; actual original pidfd ownership precedes handle publication. Original C1
exists before Stage. Missing birth/handle acknowledgement remains unknown; never
recover it by PID, path or cgroup-name discovery.

Release consumes one current-epoch ticket in the authority's exclusive transition.
Cancel, timeout and lease loss close unused tickets for the whole run. For Cancel
ordered before Release, no workload marker/instruction is allowed. Prior committed
Release may run once and is later cleaned. Duplicate tickets never release twice.
An authority resumed after fallback cleanup must be incapable of creating/thawing any
resource in a certified released scope. Observe actual original death/freeze/release;
a local flag, sent signal or empty exported registry is insufficient.

Native and Python boundary contracts must be versioned and independently parsed.
Credential checks bind exact original peers. Received rights are closed on rejection.
A forged/malformed/late response never commits normal state or freshness. Bound
request/reply byte lengths, tables, polls and original absolute ends. Cancellation
and external native lease service remain independent of normal request locks.

Controller crash leaves the original issuer, storage owner and C1 holder alive.
Replacement uses a newly registered owned controller child, new private channel and
new host clock session. Retire the old channel. Reconciliation queries the exact
surviving issuer plus durable consumption/handles; all old positive freshness is
invalid. No start is implicit in reconciliation. Controller-local timeouts and the original
broker absolute-end leases remain separate; new sessions never extend old ends or
subtract their host readings from a prior session. A replacement authority rejects
old-resource adoption. Explicit restart requires new authority scope and permits
after prior transitive-dependent release.

Verify at least: two-unit cross-gate cancellation; both native orderings; duplicate/
stale/foreign tickets; cancelled/expired Stage; real stopped authority and resumed
late operation; issuer death before/after child acknowledgement; actual C1 cleanup;
replacement controller process with surviving issuer; old controller/session/fork
rejection; replacement issuer rejection; storage stall/failure independent cleanup;
source/wheel native parity; exact owned waits and removed boundaries. Preserve
unknown direct-child waits and normal-record gaps. Expected observations must be
written before implementation, not derived from candidate routines.

The complete seven P3 tasks and nine runtime acceptance cases remain open until
assembled evidence establishes them. Separate read-only findings precede repairs.
Commit only verified stable increments; no acceptance/main merge is implicit.
