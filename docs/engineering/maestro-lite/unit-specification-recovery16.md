# Surviving issuer reconciliation unit contract — before product code

Inputs: exact original root/owner, exact per-unit ProbePolicy tuple, positive finite
operation budget <=5 seconds; exact same-session active and reserved cleanup ends
within the original generation. At most 16 units, finite RPC capacity and bounded
view inventory. Reject copied/replaced holders, unknown units, changed repeats and
normal lock conflicts before any mutation. Never clear a cancellation latch.

The original owner retains readiness-view identities. Recovery acquires existing
view/owner locks without blocking, reserves its original owner thread, advances the
view epoch and closes all future claim/Stage/Release paths. Previous observations
are unusable even if their age would otherwise be fresh. Cancel bypasses these locks.

Snapshot RPC executes only in the original storage process. Require exact original
claim operation, consumed permit/nonce and intact ordered journal/mirrors. A matching
full handle with a normal original start outcome permits ordinary reconciliation;
missing/unacknowledged outcome or handle permits cleanup-only. Return closed factual
rows/source hashes and actual global last sample sequence, never a new permit/handle.
Native Query/revalidation both before and after the snapshot binds it to the live
original issuing registry; changed/dead/foreign issuer or malformed reply fails.

New recovered ProcessReadiness starts empty, has no start capability and uses a
strictly later normal sample sequence. Fresh positive observations require actual
new Query and normal original M3/Argus append/flush. No new started outcome is
fabricated. Normal reverse teardown remains available with original ownership.
On failure, latch cancellation and bounded original run closure proceed independently
of journal usability. Result separates recovered ownership, freshness, cleanup and
incomplete lifecycle status. Matching repeat returns retained facts without mutation.

Verify actual started two-unit recovery, original view invalidation, fresh health
sequence/public hashes, normal owned teardown, staged-only and missing durable
history, expired/changed-session/copy/foreign issuer, real Query/storage stalls,
malformed ACK, mutation conflicts, independent cancellation and same-scope repeats.
Source/wheel/native identity, actual removal/reaping and separate read-only review
remain required. All seven full P3 tasks remain unchecked. Process-restart and new
host-session recovery remain inadmissible, not silently mapped to this same-supervisor
primitive. All requirement and experimental boundaries remain unchanged.

Finding8 successor contract, before repair: explicit scheduled observe is scoped
to its exact admitted unit and original handle. One unit's operation end must not
be shared by an unrelated unit's extra probe. Add exact-unit health with unchanged
normal lock, original-holder, freshness, durable sample and independent cancellation
rules. Invalid units and normal lock conflicts reject before observation/cancellation.
Periodic host health continues to scan all released units under its admitted scan
budget. Keep all timing limits and conservative request/event bounds unchanged.
Verify actual two-unit explicit observation scope plus invalid-unit/conflict behavior.
