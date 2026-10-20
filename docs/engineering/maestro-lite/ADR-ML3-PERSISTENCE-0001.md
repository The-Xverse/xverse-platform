# Single original persistence process and bounded supervisor RPC

ML3-PERSISTENCE8-2026-10-18-v1. Parent 4d3aab41465a02998cc5f0f0082a3254cf9af82e.
Capability 024, partial U2/U3/U7, no new scientific or execution approval.

Use Python for the single M3/Argus persistence owner and supervisor control plane;
retain native RG06 for workload Release. M3 and Argus objects must be created inside
their actual owning persistence process, never fork-copied, pickled, reopened or
reconstructed from receipts. The supervisor retains original C1, Stage and native
Release authority. The persistence child receives neither containment/gate FDs nor
provider handles and cannot dispatch workloads. One coordinated writer remains the
only Argus writer. A stalled original writer is killed/retained unresolved, not
replaced by another writer for that root.

A sealed private memfd contains bounded, versioned bootstrap input: original XDL
resource declarations, exact preparation/plan pins, provider descriptors, private
permit/approval facts, explicit host session/generation deadline and isolated store
paths. Revalidate/compile XDL and all permits inside the child before opening stores.
This is private IPC, not a second configuration language or public evidence. No
pickle, arbitrary executable/callback/RPC, discovery, or public nonce serialization.

The original supervisor holds an actual child Popen, pidfd and AF_UNIX SEQPACKET
channel with per-message credentials. It initializes the service only after
registration; bounded Init/RegisterIntent/RevalidateIntent/Abort requests bind the
private input scope, exact operation, sequence and original host deadline. Replies
must come from that original child and match exactly. Private registered receipt
objects, not copied fields or supplied digest strings, connect actual persistence
ACKs to ReleaseOwner. Source hashes cover M3's real public projection. Original
operation deadlines survive every revalidation and cannot be extended.

Caller-side polling, cancellation and drain perform no storage I/O. Timeout/error
closes starts, revokes native Release and terminates/reaps only the original child
through its retained pidfd under a fixed teardown deadline; blocked kernel tasks
remain explicit unresolved retained ownership. Healthy idle cancellation may still
permit an Abort request; it does not grant further start authority. A late writer
result cannot revive a private claim. Abort reports the actual failed writer state,
not lifecycle coverage/completion or fabricated normal M3 outcomes.

Reuse the same durable intent implementation for local and isolated owners. Extend
ReleaseOwner additively with an exact PersistenceClient factory; retain existing
local API behavior for comparison and regression. No local M3/Argus I/O is allowed
on the isolated path, including at-use journal revalidation. Frozen Stage and native
Release stay in the original supervisor process.

Trusted bootstrap still supplies actual helper creation, executable/FD pins and
exclusive wait ownership before these constructors. Full bounded helper creation,
actual catalog child launcher, admitted native FD-to-C1 binding, original-owner loss,
ordinary handles/readiness/restart, complete U7/U8 and nine runtime cases remain
open. Python/OS scheduling and arbitrary kernel stalls are not hard bounded. This
increment exercises actual interruptible storage stalls with finite in-memory
failure observations; it is not a complete lifecycle or acceptance gate closure.

Mechanism references (engineering API behavior only, no thesis evidence/citation):
[Linux memfd sealing](https://www.man7.org/linux/man-pages/man2/memfd_create.2.html)
and [parent-death signal semantics](https://www.man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html).
The latter follows the creating parent thread and has initialization/credential
caveats; it is not equated with hard process-owner-loss containment.
