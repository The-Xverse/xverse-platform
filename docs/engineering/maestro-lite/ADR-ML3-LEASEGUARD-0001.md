# Native freeze-only lease guard

Revision: ML3-LEASEGUARD5-2026-10-18-v1. Status: implementation candidate.
Parent: de6be649b8a633b8f92972b249b03271d11810ea. Same capability 024,
U3/U4; ML-SR-010/012/013/024 remain partial. No main acceptance is implied.

Implement a separate native process that watches one original supervisor pidfd,
one private Unix SOCK_SEQPACKET connection and an absolute monotonic lease. On
lease expiration, supervisor death, control loss, malformed input or explicit
Cancel, it irreversibly requests freeze on its retained original cgroup and
observes cgroup.events frozen=1. It never thaws, spawns, signals, kills, deletes,
discovers or adopts a workload. C1 remains in the original external holder.

C11 is selected for the small fixed-buffer Linux syscall loop: no interpreter,
provider callback, tick, storage/journal call or allocation is needed in the
watch loop. Python remains the control plane; X-COM C++ is unchanged. This is a
language allocation based on isolation and inspectability, not a measured speed
comparison. The wheel carries source, not a host binary. Build explicitly with
the recorded compiler; do not compile or start helpers on import or installation.

The original bootstrap owner supplies only an already retained cgroup directory
FD, a connected private socket, a 32-byte scope digest, fixed generation deadline,
initial lease and freeze budget. The socket peer must be the actual original
parent and same UID/GID. Open its pidfd and recheck parent identity. SO_PASSCRED
requires every command's actual sender to match that parent; inherited sockets
cannot authorize forked senders. This authenticates the local bootstrap channel,
not an operator approval, M3 receipt, Argus flush, supervisor Stage acknowledgement
or run admission. Same-user debugger/root compromise is outside this component.

Use CLOCK_MONOTONIC absolute nanoseconds; initial/renewed leases <=5 s and leave
the explicit <=1 s freeze reserve within the immutable <=394 s generation lease.
Renewal requires contiguous sequence, exact scope, a strictly increased absolute
deadline, a still-live original supervisor and a lease not yet expired. Queued late
messages never revive an expired lease. Check time before each message, including
under a flood. Invalid messages irreversibly close renewal and freeze. Reject
ancillary FDs, close delivered descriptors, and never use them as authority.

No lock is shared with Python. The guard's finite poll loop is independent of
provider, broker and storage stalls. Kernel I/O and scheduling can still stall.
A stopped/crashed guard, host failure or blocked kernel write is NOT a proven
bounded fail-closed lease. There is no atomic Release/cancel ordering here: a
future launcher must share an enforceable authority with the guard, and must
prevent a stale thaw after freeze. Until that integration and original-owner
loss handling exist, process readiness remains false and full M1 is open.

The helper only observes frozen state. It cannot certify empty membership,
termination, teardown, facility release or lifecycle success. Loss of a boundary
or failure to confirm freeze yields UNRESOLVED. No replacement path is opened.
The original holder must monitor helper death and retain exact C1 for cleanup.

Implementation and verification derive from D3/D4 and the descriptor C1 contract.
Run owned kernel component tests, source-excluded installed-wheel checks, strict
native compilation, full platform regression, and a separate recorded read-only
review before stable-increment commit. No nine-case ML3 execution is claimed.

Primary API references checked for this implementation: Linux
[Unix sockets/SCM_CREDENTIALS](https://man7.org/linux/man-pages/man7/unix.7.html),
[pidfd pollable identity](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
and [cgroup v2 freeze completion](https://www.kernel.org/doc/html/v6.8/admin-guide/cgroup-v2.html).
These document API semantics; actual component observations are in the local bundle.
