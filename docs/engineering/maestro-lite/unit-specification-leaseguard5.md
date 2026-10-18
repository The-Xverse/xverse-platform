# Lease guard unit and wire contract

Revision: ML3-LEASEGUARD5-2026-10-18-v1. Partial U3/U4 component, ready=false.

Native entry: `lease-guard CGFD SOCKETFD GENERATION_NS LEASE_NS FREEZE_NS SCOPE_HEX`.
Strict unsigned decimal values and exactly 64 lowercase hexadecimal scope digits.
CGFD is an existing exclusive original boundary; SOCKETFD is its connected private
AF_UNIX SOCK_SEQPACKET control endpoint. Bootstrap must use close_fds and pass only
those FDs, fixed standard streams and an admitted executable; no runtime launcher
or bootstrap facade is supplied by this increment. The helper opens an original
parent pidfd, validates cgroup v2/domain/no descendants/initially frozen, and emits
READY. Before READY, input/identity failure exits 64; no successful admission is
invented. An initially running boundary is an admission rejection.

Every packet is exactly 64 bytes, network byte order:

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 4 | ASCII LG05 |
| 4 | 4 | kind |
| 8 | 8 | contiguous command sequence; READY is 0 |
| 16 | 8 | absolute CLOCK_MONOTONIC lease deadline |
| 24 | 32 | original scope digest |
| 56 | 8 | reason, zero on commands |

Commands: RENEW=1, CANCEL=2. Responses: READY=16, RENEWED=17, FROZEN=18,
UNRESOLVED=19. Reason: none=0, lease=1, supervisor_loss=2, control_loss=3,
protocol=4, cancel=5, freeze_failure=6, authority_expired=7. Cancellation
must echo the current lease. FROZEN is a terminal observation only; it grants
no cleanup or Release rights. UNRESOLVED is terminal failure. Exit codes:
0 observed frozen, 64 admission rejection, 70 freeze/authority unresolved.
ACK delivery is nonblocking: failure cannot delay freeze; terminal state may be
observed only through the original owner's direct kernel check and helper exit.
Even a successful local send does not acknowledge receiver delivery; unread queued
commands can reset the connection at exit. A missing terminal packet stays unknown.

| Unit invariant | Required checks |
| --- | --- |
| Fixed retained kernel scope | Real cgroup frozen on lease, Cancel, control loss and parent death; sentinel unaffected; deleted FD unresolved |
| Original local sender | Forked sender, wrong scope/sequence/magic/kind/length/reason and passed FDs cause freeze; no adoption |
| Fixed temporal authority | <=5 s leases, <=1 s freeze reserve, <=394 s immutable generation; stale and late renewal cannot reopen; flood cannot starve expiration |
| Independent loop | Python/provider pause does not stop expiry; test actual native process and frozen event |
| One terminal transition | No renewal after cancellation/expiry; no thaw method or child creation |
| Observability | READY/renew ACK reflect exact scope/sequence/deadline; terminal failure never reports freeze/cleanup success |
| Packaging | Build packaged exact native source with strict C11 warnings; source excluded installed-wheel regression |

Measure real host intervals with explicit generous test allowances; do not promote
observations to real-time guarantees. Keep all 24 ML-SR and 18 unvalidated REF-002
parents from containment4. Full AFFA/U3/U4, M3/Argus integration, helper-loss fencing,
all nine runtime cases and independent full-candidate review remain required.
