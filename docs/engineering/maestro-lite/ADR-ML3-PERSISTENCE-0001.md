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

## Amendment S1a-1: in-flight cancellation (2026-10-23, thesis specs/029-lite-stabilization FR-005, S-D2)

Recorded before implementation, under the author's decision S-D2 of 2026-10-23. Before this amendment, only
*idle* cancellation left a healthy owner: a cancel observed while an ordinary request was about to be sent,
or was in flight, went through the fail-closed path (`_fail()`). That terminated the child, so the terminal
records and the Abort could no longer reach the owner (S1a findings 5–6).

Amended rule:
- **Cancel before send.** A cancel observed before an ordinary request is sent refuses that request with
  `PersistenceCancelled` (code `ML-PERSIST-CLOSED`). The owner stays healthy, and no RPC failure is
  recorded.
- **Cancel in flight.** A request already sent when the cancel is observed may still receive its exact
  reply within a fixed grace (`CANCEL_REPLY_GRACE_NS`, 0.5 s). The grace stays inside the admitted
  cancellation drain of at most 2 s. Without a reply in that grace, the call fails closed exactly as
  before.
- **Grace expiry, and the recovery path (thesis DR-1, S1a findings 11–12).** Expiry fails closed with its own
  code, `ML-PERSIST-CANCEL-GRACE`, through the ordinary RPC failure path: the failure is recorded,
  `_fail()` runs, and the child is terminated. `reconcile_snapshot` re-raises a before-send cancel refusal
  instead of failing storage.
- **Unchanged.** Caller-side polling, cancellation and drain still perform no storage I/O. A cancelled run
  still gains no further start authority: ordinary requests are refused, and only the terminal kinds, the
  abort and the closure proceed. Timeouts, protocol errors, identity changes and child loss still close
  starts, revoke native Release and terminate the child.

### Note: S1a-1 revision (RB1) (2026-10-24, written at 01:13:20; before implementation; thesis DR-15)

- **Context.** S1b review-log findings 21–22 (B), reproduced in `test_stabilization_stack_load_failures.py`.
  `_live` reads the cancel latch more than once. A cancel that lands after its first read was refused by the
  final check as a plain `PersistenceError("ML-PERSIST-CLOSED")`, or one call earlier by the child check, whose
  root check refuses a cancelled run (`ML-BOOT-CLOSED`). `_rpc` then recorded an RPC failure at `validation`
  and called `_fail()`, so no terminal record reached the writer although the native CANCEL was confirmed.
- **Revised rule.** A cancel observed by `_live` at its child check or at its final check, while storage has not
  failed, on a call that neither allows a cancel nor is in flight, raises `PersistenceCancelled`
  (`ML-PERSIST-CLOSED`), as a cancel at the first read already did. It is never a recorded RPC failure and never
  calls `_fail()`.
  - **Child check.** If the ordinary (`live=True`) child check is refused while the latch is cancelled and
    storage has not failed, the child is checked as the terminal kinds check it (`live=False`: the holder and
    capability checks only). The checks that follow still run.
  - **The in-flight call.** The same window exists for a request already sent: a cancel that lands between the
    in-flight read of the latch and the child check is checked the same way and then continues under the
    unchanged in-flight grace. It does not raise `PersistenceCancelled`, because a cancel refusal is only raised
    before send.
- **Unchanged, and checked first.** The order of the failure checks is kept. A real child exit, a pid or socket
  identity change, a failed holder or capability check, and `_failed` still raise `PersistenceError` and fail
  closed. A child-check refusal while the latch is not cancelled still fails closed. Grace expiry is unchanged.
- **Verification.** `test_stabilization_stack_load_failures.py` (B) must pass in every window, with the control
  unchanged; the persistence, cancel and closure suites must stay unchanged.

### Note: S1a-1 revision (RB1) residual L1 (2026-10-24, written at 01:48:16; before implementation; thesis DR-16)

- **Context.** S1b review-log finding 24, LOW-1 and MEDIUM-3; thesis DR-16. The RB1 rule does not change.
- **Residual L1 (declared): root-level faults that coincide with a cancel are reported one call late.**
  - With the latch cancelled, the RB1 re-check (`live=False`) does not consult the bootstrap root. A root lease
    expiry, a root exit, a closed root and a terminal-mode mismatch are therefore not refused at this call.
  - A storage worker that the root has just killed may not yet be visible to the pidfd check. The call can then
    raise `PersistenceCancelled`, and the next terminal call, which checks the child and the root, reports the
    fault.
  - This is the same shape as the S1a-1 first read and the terminal kinds. It adds no new class.
- **Residual L1 (declared): the latch reason is not consulted.** A latch cancelled with `bootstrap-uncertain` or
  `bootstrap-helper-failed` is taken as a cancel at this call. That is safe: no further start authority is
  gained, ordinary requests are refused, and the helper or root fault is reported by the root and the closure.
- **Fail-closed side (MEDIUM-3), now pinned by tests.** With the latch cancelled, each of the following still raises
  a plain `PersistenceError`, recorded as the RPC failure, followed by `_fail()`:
  - a killed storage worker (`ML-PERSIST-CHILD`);
  - `_failed` set (`ML-PERSIST-CLOSED`);
  - a replaced socket identity (`ML-PERSIST-CHILD`).

  A root refusal without a cancel also still fails closed (the root's code). Tests:
  `test_stabilization_stack_load_failures.py`.

## Note: amendment C1 of ADR-ML3-BOOTSTRAP-0001 (2026-10-24)

On the bootstrap path, the sealed persistence configuration is now bounded at 262 144 bytes
(`bootstrap.MAX_PERSISTENCE_INPUT`, native `MAX_STORAGE_INPUT`). It was bounded at 65 536 before, by the generic
role-input seal. The input form, the 1 MiB outer bound (`MAX_CONFIG`) and this ADR's rules are unchanged
(`review-c1.md` finding 1).

## Note ST-1: the simulation-clock binding (2026-10-24, ADR-ML3-SIMTIME-0001)

The sealed configuration gains an optional `fault_clock` key, present only when the prepared lifecycle
declares a `SimulationClock`. The worker passes it to `prepare_lifecycle`, so the rederived lifecycle digest
includes it. Configurations without it are unchanged.
