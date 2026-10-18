# Native one-use Release gate

Revision ML3-RELEASEGATE6-2026-10-18-v1. Implementation candidate, partial U3/U4.
Parent d40ab1a6612dccec86fcc0b9cf09c44d0e48e47e; accepted main c2997c0 unchanged.
ML-SR-010/012/013/024 and all remaining requirements retain their full scope.

Continue the native guard as a distinct compile-time build variant. The default
LG05 build remains freeze-only and rejects Release commands. Explicit
`-DMAESTRO_RELEASE_GATE=1` selects RG06, an incompatible 256-byte private protocol
and additional creation-epoch argument. Both variants share one syscall loop and
kernel/sender checks, avoiding duplicated security-sensitive parsers. Verify both
binaries and pin the build mode, source and executable. C11 remains appropriate
for fixed buffers and isolation from Python/provider/tick/storage work; Python
supplies a strict inert wire codec. This is not a measured performance allocation.
No compilation, bootstrap or workload execution occurs on package import/install.

For one exact original boundary/generation, the native process owns the current
epoch, one-use ticket slot and actual unfreeze operation. Arm requires a live lease,
original sender, exact creation epoch/scope, operation identity and three nonzero
receipt digests: durable M3 intent, public Argus append+flush, supervisor Stage ACK.
The trusted original admission owner must verify and bind those facts before Arm.
The native primitive checks their identities but cannot authenticate their truth;
caller digests alone do not establish run admission or satisfy those upstream gates.
No worker receives this private channel. A 256-bit nonce issued by getrandom binds
Release to the original slot, peer, operation, receipts, epoch and fixed ticket TTL.
It is not transferable authority and cannot reconstruct a helper/registry after loss.

A single native event loop validates and consumes that ticket once, records local
Release linearization and writes zero to the original retained cgroup.freeze FD
without interleaving another command. Cancel/expiry/control/owner/protocol failure
advances the epoch once, burns the ticket, requests freeze and terminates the gate.
A successfully acknowledged Release is an observed unfreeze, never readiness,
M3 outcome, cleanup or complete lifecycle success. Stage child creation, full handles
and independent owner/C1/broker integration remain separate work.

Kernel scheduling/I/O can stall between checks and mutation. This single-process
ordering is not a hard kernel lease and does not bound queued Cancel latency during
such a stall. Release can linearize before an external Cancel request is processed;
external request timestamps are not the native linearization. A future independent
owner must use exact original C1 for emergency cleanup when the gate stalls/dies.
After confirmed kernel removal of the original cgroup, its retained freeze FD must
reject unfreeze, and a resumed gate cannot adopt a replacement name. Verify that
kernel predicate and delayed production Release explicitly. Freeze without actual
removal is insufficient to prevent a stale separate writer from thawing. No full
M1/host-loss or stopped/killed-helper proof is claimed by these component cases.

Keep C1 cleanup-only, non-transferable and registered before any external Stage
insertion. No C1 grants Arm/Release. The gate cannot create children, kill, delete,
adopt a path/PID, mint provider handles, renew the original generation deadline or
report lifecycle success. Public process readiness remains false until full
admission, trusted acknowledgements, launcher, whole supervisor integration and
nine full-runtime cases are verified. All source-parent and acceptance gates stay open.

Primary API basis: [cgroup v2](https://www.kernel.org/doc/html/v6.8/admin-guide/cgroup-v2.html)
for frozen/dying-group semantics, [getrandom](https://man7.org/linux/man-pages/man2/getrandom.2.html)
for nonblocking nonce generation, and [Unix credentials](https://man7.org/linux/man-pages/man7/unix.7.html)
for original local sender checks. Old-freeze-FD rejection is additionally tested on
the actual owned kernel; no general real-time guarantee follows from these APIs.
